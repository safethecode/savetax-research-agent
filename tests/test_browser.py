import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from savetax.browser import BrowserRuntime


class BrowserTests(unittest.TestCase):
    def test_invalid_or_authenticated_url_never_launches(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder)
            with patch.object(runtime, '_run') as run:
                for url in ('http://shop.test/a', 'https://u:p@shop.test/a', 'https://hackathon.savetax.now/v1/me'):
                    with self.assertRaises(ValueError):
                        runtime.read(url)
                run.assert_not_called()

    def test_missing_typesafe_key_precedes_browser_start(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder)
            with patch('savetax.browser.environment', return_value={}), patch.object(runtime, '_run') as run:
                with self.assertRaisesRegex(ValueError, 'TYPESAFE_API_KEY'):
                    runtime.plan('https://shop.example/a', '제품 가격 확인')
                run.assert_not_called()

    def test_read_script_is_fixed_and_url_is_data(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder)
            with patch.object(runtime, '_run', return_value={'text':'price'}) as run:
                result = runtime.read('https://shop.example/a?q=quoted%22')
            self.assertEqual(result['text'], 'price')
            code = run.call_args.args[0]
            self.assertIn('finally:', code)
            self.assertIn('close_tab', code)
            self.assertNotIn('type_text(', code)
            self.assertNotIn('click_at_xy(', code)
