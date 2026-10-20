import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

from savetax.adapters.ollama import OllamaClient, OllamaError
from savetax.runtime.artifacts import exclusive_lock
from savetax.runtime.config import LocalProfile


SCHEMA = {'type': 'object', 'properties': {'action': {'type': 'string'}},
          'required': ['action'], 'additionalProperties': False}


def response(payload=None, *, status=200, raw=None):
    result = Mock()
    result.status_code = status
    result.headers = {}
    content = raw if raw is not None else json.dumps(payload or {
        'model': 'qwen3.5:9b', 'created_at': '2026-10-20T00:00:00Z',
        'response': '{"action":"finish"}', 'done': True,
        'total_duration': 120, 'load_duration': 10, 'prompt_eval_count': 30,
        'prompt_eval_duration': 40, 'eval_count': 5, 'eval_duration': 70,
    }).encode()
    result.iter_content.return_value = iter([content])
    return result


class OllamaTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.lock = Path(self.folder.name) / 'inference.lock'

    def test_generate_uses_only_local_schema_request_and_retains_actual_metadata(self):
        reply = response()
        with patch.dict(os.environ, {'HTTP_PROXY': 'http://proxy.invalid',
                                    'SAVETAX_TOKEN': 'private-test',
                                    'PARALLEL_API_KEY': 'secret-test'}), \
                patch('requests.Session.send', return_value=reply) as send:
            client = OllamaClient(LocalProfile(), lock_path=self.lock)
            self.assertEqual(client.generate('Summarize observed facts.', SCHEMA), {'action': 'finish'})
            prepared = send.call_args.args[0]
            self.assertEqual(prepared.url, 'http://127.0.0.1:11434/api/generate')
            self.assertNotIn('Authorization', prepared.headers)
            self.assertNotIn('secret-test', prepared.body.decode())
            self.assertNotIn('private-test', prepared.body.decode())
            self.assertEqual(json.loads(prepared.body), {
                'model': 'qwen3.5:9b', 'prompt': 'Summarize observed facts.',
                'format': SCHEMA, 'stream': False, 'think': False,
                'options': {'num_ctx': 8192, 'num_predict': 1536}})
            self.assertFalse(client.session.trust_env)
            self.assertFalse(send.call_args.kwargs['allow_redirects'])
            self.assertEqual(send.call_args.kwargs['proxies'], {})
            self.assertTrue(send.call_args.kwargs['stream'])
            self.assertEqual(client.last_metadata['model'], 'qwen3.5:9b')
            self.assertEqual(client.last_metadata['eval_count'], 5)
            self.assertNotIn('digest', client.last_metadata)
            self.assertFalse(self.lock.exists())
            reply.close.assert_called_once()

    def test_default_lock_is_shared_across_working_directories(self):
        first = OllamaClient(LocalProfile())
        with patch('pathlib.Path.cwd', return_value=Path(self.folder.name)):
            second = OllamaClient(LocalProfile())
        self.assertEqual(first.lock_path, second.lock_path)

    def test_existing_inference_lock_blocks_request(self):
        client = OllamaClient(LocalProfile(), lock_path=self.lock)
        with exclusive_lock(self.lock), patch('requests.Session.send') as send:
            with self.assertRaises(OllamaError):
                client.generate('Read source.', SCHEMA)
            send.assert_not_called()

    def test_redirect_and_timeout_fail_once_without_raw_error_or_stale_metadata(self):
        client = OllamaClient(LocalProfile(), lock_path=self.lock)
        client.last_metadata = {'model': 'old'}
        for fixture in (response(status=302), requests.Timeout('private-server-detail')):
            with self.subTest(fixture=type(fixture).__name__), \
                    patch('requests.Session.send', side_effect=[fixture]) as send:
                with self.assertRaises(OllamaError) as caught:
                    client.generate('Read source.', SCHEMA)
                self.assertNotIn('private-server-detail', str(caught.exception))
                self.assertEqual(client.last_metadata, {})
                self.assertFalse(self.lock.exists())
                self.assertEqual(send.call_count, 1)

    def test_nonobject_fenced_duplicate_nonfinite_or_truncated_output_is_rejected(self):
        for text in ('[]', '```json\n{"action":"finish"}\n```', '{"action":',
                     '{"action":"finish","action":"search"}', '{"value":NaN}', '{"value":1e999}'):
            fixture = response({'model': 'qwen3.5:9b', 'done': True, 'response': text})
            with self.subTest(text=text), patch('requests.Session.send', return_value=fixture):
                with self.assertRaises(OllamaError):
                    OllamaClient(LocalProfile(), lock_path=self.lock).generate('Read source.', SCHEMA)
                self.assertFalse(self.lock.exists())

    def test_incomplete_or_different_model_response_is_not_success(self):
        for metadata in ({'model': 'other-model', 'done': True},
                         {'model': 'qwen3.5:9b', 'done': False},
                         {'model': 'qwen3.5:9b', 'done': True, 'done_reason': 'length'}):
            fixture = response({**metadata, 'response': '{"action":"finish"}'})
            with self.subTest(metadata=metadata), patch('requests.Session.send', return_value=fixture):
                with self.assertRaises(OllamaError):
                    OllamaClient(LocalProfile(), lock_path=self.lock).generate('Read source.', SCHEMA)

    def test_response_size_and_elapsed_budget_are_checked_before_success(self):
        fixture = response()
        fixture.iter_content.return_value = iter([b' ' * 600_000, b' ' * 600_000])
        with patch('requests.Session.send', return_value=fixture):
            with self.assertRaises(OllamaError):
                OllamaClient(LocalProfile(), lock_path=self.lock).generate('Read source.', SCHEMA)
            fixture.close.assert_called_once()
        with patch('requests.Session.send', return_value=response()), \
                patch('savetax.adapters.ollama.time.monotonic', side_effect=[0, 181, 181]):
            with self.assertRaises(OllamaError):
                OllamaClient(LocalProfile(), lock_path=self.lock).generate('Read source.', SCHEMA)

    def test_invalid_or_oversized_input_makes_no_request(self):
        for prompt, schema in (('', SCHEMA), ('x' * 131_073, SCHEMA), ('read', []),
                               ('read', {'type': float('nan')})):
            with self.subTest(prompt_length=len(prompt)), patch('requests.Session.send') as send:
                with self.assertRaises(OllamaError):
                    OllamaClient(LocalProfile(), lock_path=self.lock).generate(prompt, schema)
                send.assert_not_called()
