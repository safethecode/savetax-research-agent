import json
import io
import tempfile
import subprocess
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from savetax.browser import BrowserRuntime


class BrowserTests(unittest.TestCase):
    def test_user_authorized_search_exception_does_not_allow_account_or_api(self):
        BrowserRuntime._validate_url('https://savetax.now/search')
        BrowserRuntime._validate_url('https://savetax.now/search?q=software')
        for url in ('https://savetax.now/account', 'https://savetax.now/search/else',
                    'https://api.savetax.now/search', 'https://hackathon.savetax.now/search',
                    'http://savetax.now/search', 'https://u:p@savetax.now/search'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                BrowserRuntime._validate_url(url)

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

    def test_read_preserves_existing_blank_tab_and_closes_only_owned_tab(self):
        # Harness new_tab(url) can reuse an attached blank tab; read must own
        # its target even when reading the page raises before returning JSON.
        for read_fails in (False, True):
            with self.subTest(read_fails=read_fails), tempfile.TemporaryDirectory() as folder:
                runtime = BrowserRuntime(folder)
                pages = {'existing': 'about:blank'}
                current = ['existing']
                closed = []
                url = 'https://shop.example/a?q=quoted%22'

                def create_target(method, **params):
                    self.assertEqual(method, 'Target.createTarget')
                    pages['owned'] = params['url']
                    return {'targetId': 'owned'}

                def read_page(_expression):
                    if read_fails:
                        raise RuntimeError('page read failed')
                    return json.dumps({'url': pages[current[0]], 'text': 'price'})

                def close_page(target):
                    closed.append(target)
                    pages.pop(target)

                def reuse_blank_page(address):
                    pages[current[0]] = address
                    return current[0]

                def execute_harness_script(code):
                    output = io.StringIO()
                    helpers = {
                        'new_tab': reuse_blank_page,
                        'cdp': create_target,
                        'switch_tab': lambda target: current.__setitem__(0, target),
                        'goto_url': lambda address: pages.__setitem__(current[0], address),
                        'wait_for_load': lambda: None,
                        'js': read_page,
                        'close_tab': close_page,
                    }
                    with redirect_stdout(output):
                        exec(compile(code, '<browser-read>', 'exec'), helpers)
                    return json.loads(output.getvalue().strip().splitlines()[-1])

                with patch.object(runtime, '_run', side_effect=execute_harness_script):
                    if read_fails:
                        with self.assertRaisesRegex(RuntimeError, 'page read failed'):
                            runtime.read(url)
                    else:
                        result = runtime.read(url)
                        self.assertEqual(result['url'], url)
                        self.assertEqual(result['text'], 'price')
                self.assertEqual(pages, {'existing': 'about:blank'})
                self.assertEqual(closed, ['owned'])

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

    def test_cleanup_failure_does_not_hide_primary_timeout(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder)
            runtime.python.parent.mkdir(parents=True)
            runtime.python.touch()
            with patch.object(runtime, 'prepare_env', return_value={}), \
                    patch.object(runtime, '_page_targets', side_effect=[{'A'*32}, {'A'*32, 'B'*32}]), \
                    patch('savetax.browser.subprocess.run', side_effect=[
                        subprocess.TimeoutExpired('test', 55),
                        subprocess.CompletedProcess('cleanup', 1, '', 'external-secret-detail')]):
                with self.assertRaisesRegex(RuntimeError, '55초') as failure:
                    runtime._run('test')
            self.assertIn('정리', str(failure.exception))
            self.assertNotIn('external-secret-detail', str(failure.exception))
            self.assertFalse((runtime.work/'browser-operation.lock').exists())

    def test_cleanup_failure_does_not_hide_invalid_model_result(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder)
            runtime.python.parent.mkdir(parents=True)
            runtime.python.touch()
            with patch.object(runtime, 'prepare_env', return_value={}), \
                    patch.object(runtime, '_page_targets', side_effect=[set(), {'B'*32}]), \
                    patch('savetax.browser.subprocess.run', side_effect=[
                        subprocess.CompletedProcess('model', 0, 'not-json', ''),
                        subprocess.CompletedProcess('cleanup', 1, '', 'external-secret-detail')]):
                with self.assertRaisesRegex(RuntimeError, 'JSON') as failure:
                    runtime._run('test', model=True)
            self.assertIn('정리', str(failure.exception))
            self.assertNotIn('external-secret-detail', str(failure.exception))
            self.assertFalse((runtime.work/'browser-operation.lock').exists())

    def test_cleanup_decode_errors_do_not_hide_primary_timeout(self):
        errors = [json.JSONDecodeError('external-secret-detail', '', 0),
                  UnicodeDecodeError('utf-8', b'\xff', 0, 1, 'external-secret-detail')]
        for error in errors:
            with self.subTest(error=type(error).__name__), tempfile.TemporaryDirectory() as folder:
                runtime = BrowserRuntime(folder)
                runtime.python.parent.mkdir(parents=True)
                runtime.python.touch()
                with patch.object(runtime, 'prepare_env', return_value={}), \
                        patch.object(runtime, '_page_targets', return_value=set()), \
                        patch.object(runtime, '_cleanup_new_tabs', side_effect=error), \
                        patch('savetax.browser.subprocess.run', side_effect=subprocess.TimeoutExpired('test', 55)):
                    with self.assertRaisesRegex(RuntimeError, '55초') as failure:
                        runtime._run('test')
                self.assertIn('정리', str(failure.exception))
                self.assertNotIn('external-secret-detail', str(failure.exception))
                self.assertFalse((runtime.work/'browser-operation.lock').exists())

    def test_valid_result_with_cleanup_decode_error_is_not_success(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder)
            runtime.python.parent.mkdir(parents=True)
            runtime.python.touch()
            with patch.object(runtime, 'prepare_env', return_value={}), \
                    patch.object(runtime, '_page_targets', return_value=set()), \
                    patch.object(runtime, '_cleanup_new_tabs', side_effect=json.JSONDecodeError('external-secret-detail', '', 0)), \
                    patch('savetax.browser.subprocess.run', return_value=subprocess.CompletedProcess('model', 0, '{"ok": true}', '')):
                with self.assertRaisesRegex(RuntimeError, '결과는 생성됐지만') as failure:
                    runtime._run('test', model=True)
            self.assertNotIn('external-secret-detail', str(failure.exception))
            self.assertFalse((runtime.work/'browser-operation.lock').exists())


class JevGuardTest(unittest.TestCase):
    def test_guard_blocks_purchase_and_login_labels(self):
        import re
        from savetax.browser import JEV_GUARD_PATTERN
        guard = re.compile(JEV_GUARD_PATTERN, re.I)
        for label in ('바로구매', '장바구니 담기', '결제하기', '로그인', '회원가입', 'Add to Cart', 'Checkout', 'Sign in'):
            self.assertTrue(guard.search(label), label)
        for label in ('판넬두께 150T', '코일두께 0.5T x 0.6T', '수량 증가', '상품 상세정보'):
            self.assertFalse(guard.search(label), label)

    def test_run_jev_rejects_bad_steps(self):
        from savetax.browser import BrowserRuntime
        with self.assertRaises(ValueError):
            BrowserRuntime().run_jev('https://example.com/p', '가격 확인', max_steps=0)
