import tempfile
import subprocess
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

    def test_chrome_does_not_receive_procurement_or_model_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            chrome = Path(folder)/'chrome.exe'
            chrome.touch()
            runtime = BrowserRuntime(folder)
            with patch('savetax.browser.environment',return_value={'SAVETAX_TOKEN':'private-test','TYPESAFE_API_KEY':'model-test','PARALLEL_API_KEY':'search-test'}), \
                    patch('savetax.browser.shutil.which',return_value=str(chrome)), \
                    patch.object(runtime,'_endpoint',side_effect=[None,'http://127.0.0.1:1234']), \
                    patch('savetax.browser.subprocess.Popen') as spawn:
                spawn.return_value.pid = 1234
                result = runtime.prepare_env(start=True)
            child_env = spawn.call_args.kwargs.get('env',{})
            self.assertIn('env',spawn.call_args.kwargs)
            self.assertFalse(any(k.startswith('SAVETAX_') or k.endswith('_API_KEY') for k in child_env))
            self.assertEqual(result['TYPESAFE_API_KEY'],'model-test')

    def test_timeout_parent_closes_only_new_task_tabs(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder)
            runtime.python.parent.mkdir(parents=True)
            runtime.python.touch()
            existing, owned = 'A'*32, 'B'*32
            with patch.object(runtime,'prepare_env',return_value={}), \
                    patch.object(runtime,'_page_targets',side_effect=[{existing},{existing,owned}]), \
                    patch('savetax.browser.subprocess.run',side_effect=[subprocess.TimeoutExpired('test',55),subprocess.CompletedProcess('cleanup',0,'','')]) as run:
                with self.assertRaisesRegex(RuntimeError,'55초'):
                    runtime._run('test')
            cleanup_code = run.call_args.kwargs['input']
            self.assertIn(owned,cleanup_code)
            self.assertNotIn(existing,cleanup_code)
            self.assertFalse((runtime.work/'browser-operation.lock').exists())
