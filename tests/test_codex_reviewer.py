import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from savetax.adapters.codex import CodexReviewer


class Process:
    def __init__(self, events, stderr=b'', code=0):
        self.stdin = io.BytesIO()
        self.stdout = io.BytesIO(events)
        self.stderr = io.BytesIO(stderr)
        self.code = code
        self.killed = False

    def wait(self, timeout=None):
        return self.code

    def kill(self):
        self.killed = True


def events(decision, *, metadata=True):
    rows = [{'type': 'thread.started', 'thread_id': 'thread-1'}]
    if metadata:
        rows.append({'type': 'session_meta', 'payload': {
            'model': 'configured-codex-model', 'model_provider': 'openai'}})
    rows += [{'type': 'item.completed', 'item': {'type': 'agent_message',
              'text': json.dumps(decision)}}, {'type': 'turn.completed', 'usage': {'input_tokens': 1}}]
    return ('\n'.join(json.dumps(row) for row in rows) + '\n').encode()


class CodexReviewerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.package = self.root / 'package'
        self.package.mkdir()
        (self.package / 'manifest.json').write_text('{}')
        self.manifest = {'package_hash': 'a' * 64}
        self.decision = {'schema_version': '1', 'decision': 'needs_evidence',
                         'blocking': ['가격 미확인'], 'accepted_limitations': [],
                         'notes': '추가 근거 필요', 'source_assessments': []}

    def test_uses_ordinary_readonly_exec_and_scrubs_vendor_credentials(self):
        process = Process(events(self.decision))
        with patch('savetax.adapters.codex.subprocess.Popen', return_value=process) as spawn, \
                patch.dict('os.environ', {'PARALLEL_API_KEY': 'secret', 'SAVETAX_TOKEN': 'pat',
                                         'TYPESAFE_API_KEY': 'secret', 'OPENAI_API_KEY': 'secret'}):
            reviewer = CodexReviewer(executable='codex-test', timeout=5, model='configured-codex-model')
            result = reviewer.review(self.package, self.manifest)
        command = spawn.call_args.args[0]
        self.assertIn('exec', command)
        self.assertNotIn('review', command)
        self.assertEqual(command[command.index('--sandbox') + 1], 'read-only')
        self.assertIn('--ephemeral', command)
        self.assertIn('--output-schema', command)
        self.assertFalse(spawn.call_args.kwargs.get('shell', False))
        self.assertNotEqual(Path(spawn.call_args.kwargs['cwd']), self.package)
        self.assertFalse(Path(spawn.call_args.kwargs['cwd']).is_relative_to(self.root))
        self.assertFalse(any(k.endswith('_API_KEY') or k.startswith('SAVETAX_')
                             for k in spawn.call_args.kwargs['env']))
        self.assertEqual(result, self.decision)
        self.assertEqual(reviewer.last_execution['model'], 'configured-codex-model')
        self.assertEqual(reviewer.last_execution['metadata_source'], 'jsonl')

    def test_missing_observed_metadata_is_honestly_bound_to_explicit_configuration(self):
        process = Process(events(self.decision, metadata=False))
        with patch('savetax.adapters.codex.subprocess.Popen', return_value=process):
            reviewer = CodexReviewer(executable='codex-test', model='configured-codex-model')
            self.assertEqual(reviewer.review(self.package, self.manifest), self.decision)
        self.assertIsNone(reviewer.last_execution['model_observed'])
        self.assertEqual(reviewer.last_execution['requested_model'], 'configured-codex-model')
        self.assertEqual(reviewer.last_execution['metadata_source'], 'configured-execution')

    def test_timeout_and_external_errors_are_sanitized(self):
        process = Process(b'', stderr=b'secret-key-value', code=1)
        with patch('savetax.adapters.codex.subprocess.Popen', return_value=process):
            with self.assertRaises(RuntimeError) as caught:
                CodexReviewer(executable='codex-test', model='configured-codex-model').review(self.package, self.manifest)
        self.assertNotIn('secret-key-value', str(caught.exception))
        process = Process(b'')
        process.wait = lambda timeout=None: (_ for _ in ()).throw(subprocess.TimeoutExpired('x', 1))
        with patch('savetax.adapters.codex.subprocess.Popen', return_value=process):
            with self.assertRaisesRegex(RuntimeError, 'timeout'):
                CodexReviewer(executable='codex-test', timeout=1, model='configured-codex-model').review(self.package, self.manifest)
        self.assertTrue(process.killed)

    def test_oversize_output_malformed_json_and_local_provider_fail_closed(self):
        for raw in (b'x' * 10000, b'not-json', events(self.decision).replace(b'openai', b'ollama')):
            with self.subTest(raw=raw[:20]):
                with patch('savetax.adapters.codex.subprocess.Popen', return_value=Process(raw)):
                    with self.assertRaises(RuntimeError):
                        CodexReviewer(executable='codex-test', max_output_bytes=4096, model='configured-codex-model').review(
                            self.package, self.manifest)
