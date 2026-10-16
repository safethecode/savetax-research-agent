import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from savetax.secrets import environment, load_env_file, redact_keys


class SecretsTests(unittest.TestCase):
    def test_only_allowed_assignment_without_shell_evaluation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'keys.txt'
            path.write_text('\ufeffTYPESAFE_API_KEY="test-only"\nexport PARALLEL_API_KEY=literal$(no-exec)\nPATH=bad\nTEXT_MODEL=fast # comment\n', encoding='utf-8')
            self.assertEqual(load_env_file(path), {'TYPESAFE_API_KEY':'test-only', 'PARALLEL_API_KEY':'literal$(no-exec)', 'TEXT_MODEL':'fast'})
            with patch.dict(os.environ, {'TYPESAFE_API_KEY':'existing'}):
                self.assertEqual(environment(path)['TYPESAFE_API_KEY'], 'existing')

    def test_nested_responses_redact_keys(self):
        self.assertEqual(redact_keys({'msg':['prefix-test-value']}, {'PARALLEL_API_KEY':'test-value'}), {'msg':['prefix-[REDACTED]']})
