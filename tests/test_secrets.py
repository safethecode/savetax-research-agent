import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from savetax.secrets import activated_environment, environment, load_env_file, redact_keys


class SecretsTests(unittest.TestCase):
    def test_env_fallback_preserves_legacy_precedence_and_allowlist(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'.env.txt'
            path.with_name('.env').write_text('PARALLEL_API_KEY=local-key\nPATH=bad\n')
            self.assertEqual(load_env_file(path), {'PARALLEL_API_KEY':'local-key'})
            path.write_text('TYPESAFE_API_KEY=legacy-key\n')
            self.assertEqual(load_env_file(path), {'TYPESAFE_API_KEY':'legacy-key'})

    def test_only_allowed_assignment_without_shell_evaluation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'keys.txt'
            path.write_text('\ufeffTYPESAFE_API_KEY="test-only"\nexport PARALLEL_API_KEY=literal$(no-exec)\nPATH=bad\nTEXT_MODEL=fast # comment\n', encoding='utf-8')
            self.assertEqual(load_env_file(path), {'TYPESAFE_API_KEY':'test-only', 'PARALLEL_API_KEY':'literal$(no-exec)', 'TEXT_MODEL':'fast'})
            with patch.dict(os.environ, {'TYPESAFE_API_KEY':'existing'}):
                self.assertEqual(environment(path)['TYPESAFE_API_KEY'], 'existing')

    def test_nested_responses_redact_keys(self):
        self.assertEqual(redact_keys({'msg':['prefix-test-value']}, {'PARALLEL_API_KEY':'test-value'}), {'msg':['prefix-[REDACTED]']})

    def test_api_key_is_process_environment_and_restored_after_use(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'keys.txt'
            path.write_text('PARALLEL_API_KEY=test-parallel\nTYPESAFE_API_KEY=test-typesafe\n', encoding='utf-8')
            with patch.dict(os.environ, {'TYPESAFE_API_KEY':'already-set'}, clear=True):
                with self.assertRaises(RuntimeError):
                    with activated_environment(path):
                        self.assertEqual(os.environ['PARALLEL_API_KEY'], 'test-parallel')
                        self.assertEqual(os.environ['TYPESAFE_API_KEY'], 'already-set')
                        raise RuntimeError('test')
                self.assertNotIn('PARALLEL_API_KEY', os.environ)
                self.assertEqual(os.environ['TYPESAFE_API_KEY'], 'already-set')
