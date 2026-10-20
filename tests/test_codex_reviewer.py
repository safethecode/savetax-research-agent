import io
import hashlib
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
        self.manifest = {'package_hash': 'a' * 64, 'body': None, 'sources': []}
        (self.package / 'manifest.json').write_text(json.dumps(self.manifest))
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

    def test_complete_manifest_body_and_all_text_and_raw_captures_are_inline(self):
        text = 'INLINE-RETAIL: MODEL-A 신품 100원 부가세 포함 무료배송'
        raw = '{"text":"INLINE-RAW: MODEL-A selected option A quantity 1 total 100"}'
        (self.package / 'seller.txt').write_text(text, encoding='utf-8')
        (self.package / 'capture.json').write_text(raw, encoding='utf-8')
        self.manifest.update(body={'title': 'INLINE-BODY-EXACT', 'lines': []},
                             policy={'policy_id': 'INLINE-POLICY'}, sources=[{
            'source_id': 'S1', 'path': 'seller.txt', 'raw_path': 'capture.json',
            'sha256': hashlib.sha256(text.encode()).hexdigest(),
            'raw_sha256': hashlib.sha256(raw.encode()).hexdigest()}])
        delivered = {}
        def execute(command, cwd, prompt):
            delivered['prompt'] = prompt
            return events(self.decision), b''
        with patch.object(CodexReviewer, '_execute', side_effect=execute):
            reviewer = CodexReviewer(executable='codex-test', model='configured-codex-model')
            reviewer.review(self.package, self.manifest)
        prompt = delivered['prompt'].decode('utf-8')
        self.assertIn(text, prompt)
        self.assertIn('INLINE-RAW: MODEL-A selected option A quantity 1 total 100', prompt)
        self.assertIn('INLINE-BODY-EXACT', prompt)
        self.assertIn('INLINE-POLICY', prompt)
        self.assertIn('No file commands or tools are needed', prompt)
        self.assertEqual(reviewer.last_execution['input_bytes'], len(delivered['prompt']))
        self.assertEqual(reviewer.last_execution['input_sha256'], hashlib.sha256(delivered['prompt']).hexdigest())

    def test_actual_full_inline_prompt_overflow_never_launches_codex(self):
        text = 'x' * 262144
        (self.package / 'seller.txt').write_text(text, encoding='utf-8')
        self.manifest['sources'] = [{'source_id': 'S1', 'path': 'seller.txt',
                                     'sha256': hashlib.sha256(text.encode()).hexdigest()}]
        with patch.object(CodexReviewer, '_execute', return_value=(events(self.decision), b'')) as execute:
            with self.assertRaisesRegex(RuntimeError, 'input_limit'):
                CodexReviewer(executable='codex-test', model='configured-codex-model').review(
                    self.package, self.manifest)
        execute.assert_not_called()
