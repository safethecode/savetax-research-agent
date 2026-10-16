"""Named sessions must not reuse another task's Chrome, daemon state or lock."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from savetax.browser import BrowserRuntime
from savetax.cli import main


class BrowserSessionTests(unittest.TestCase):
    def test_invalid_session_names_are_rejected_before_creating_paths(self):
        names = ('', '.', '..', '../root', r'..\root', '/tmp/browser',
                 r'C:\browser', 'two words', 'upperCase', 'a/b', 'a:b',
                 'a' * 33, 'con', 'nul', 'com1', 'lpt9')
        with tempfile.TemporaryDirectory() as folder:
            for name in names:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    BrowserRuntime(folder, session_name=name)
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_default_state_and_named_states_do_not_overlap(self):
        with tempfile.TemporaryDirectory() as folder:
            default = BrowserRuntime(folder)
            industrial = BrowserRuntime(folder, session_name='industrial')
            hardware = BrowserRuntime(folder, session_name='hardware-2')
            with patch('savetax.browser.environment', return_value={}):
                self.assertEqual(default._env()['BH_HOME'], str(Path(folder)/'work/browser-state'))
                self.assertEqual(industrial._env()['BH_HOME'], str(Path(folder)/'work/browser-sessions/industrial/browser-state'))
                self.assertEqual(hardware._env()['BH_HOME'], str(Path(folder)/'work/browser-sessions/hardware-2/browser-state'))
            self.assertEqual(default.python, industrial.python)

    def test_named_session_reads_its_own_active_port(self):
        with tempfile.TemporaryDirectory() as folder:
            work = Path(folder)/'work'
            for path, port in ((work/'browser-chrome', 1111),
                               (work/'browser-sessions/industrial/browser-chrome', 2222)):
                path.mkdir(parents=True)
                (path/'DevToolsActivePort').write_text(str(port)+'\n/browser', encoding='utf-8')
            runtime = BrowserRuntime(folder, session_name='industrial')
            urls = []
            class Opener:
                def open(self, url, timeout):
                    urls.append(url)
                    return io.StringIO('{"webSocketDebuggerUrl":"ws://127.0.0.1:2222/browser"}')
            with patch('savetax.browser.build_opener', return_value=Opener()):
                self.assertEqual(runtime._endpoint(), 'http://127.0.0.1:2222')
            self.assertEqual(urls, ['http://127.0.0.1:2222/json/version'])

    def test_named_session_without_active_port_does_not_inherit_other_browser(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder, session_name='industrial')
            inherited = {'BU_CDP_URL':'http://127.0.0.1:1111',
                         'BU_CDP_WS':'ws://127.0.0.1:1111/browser', 'BU_NAME':'shared',
                         'BU_BROWSER_ID':'foreign-cloud-browser'}
            with patch('savetax.browser.environment', return_value=inherited):
                env = runtime.prepare_env()
            self.assertFalse(any(key in env for key in ('BU_CDP_URL','BU_CDP_WS','BU_NAME','BU_BROWSER_ID')))

    def test_named_session_overrides_inherited_harness_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder, session_name='industrial')
            inherited = {key:str(Path(folder)/'shared') for key in
                         ('BH_RUNTIME_DIR','BH_TMP_DIR','BH_CONFIG_DIR','BH_AGENT_WORKSPACE')}
            with patch('savetax.browser.environment', return_value=inherited):
                env = runtime._env()
            home = Path(folder)/'work/browser-sessions/industrial/browser-state'
            self.assertEqual(env['BH_RUNTIME_DIR'], str(home/'runtime'))
            self.assertEqual(env['BH_TMP_DIR'], str(home/'tmp'))
            self.assertEqual(env['BH_CONFIG_DIR'], str(home))
            self.assertEqual(env['BH_AGENT_WORKSPACE'], str(home/'agent-workspace'))

    def test_named_start_isolates_profile_pid_and_chrome_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            chrome = Path(folder)/'chrome.exe'
            chrome.touch()
            runtime = BrowserRuntime(folder, session_name='industrial')
            env = {'SAVETAX_TOKEN':'procurement-secret', 'TYPESAFE_API_KEY':'model-secret',
                   'PARALLEL_API_KEY':'search-secret'}
            with patch('savetax.browser.environment', return_value=env), \
                    patch('savetax.browser.shutil.which', return_value=str(chrome)), \
                    patch.object(runtime, '_endpoint', side_effect=[None, 'http://127.0.0.1:2222']), \
                    patch('savetax.browser.subprocess.Popen') as spawn:
                spawn.return_value.pid = 4321
                result = runtime.prepare_env(start=True)
            base = Path(folder)/'work/browser-sessions/industrial'
            self.assertIn('--user-data-dir='+str(base/'browser-chrome'), spawn.call_args.args[0])
            self.assertEqual(json.loads((base/'browser-chrome-process.json').read_text())['pid'], 4321)
            self.assertFalse((Path(folder)/'work/browser-chrome-process.json').exists())
            child_env = spawn.call_args.kwargs['env']
            self.assertFalse(any(k.startswith('SAVETAX_') or k.endswith('_API_KEY') for k in child_env))
            self.assertEqual(result['BU_CDP_URL'], 'http://127.0.0.1:2222')

    def test_locks_allow_different_sessions_but_reject_same_session(self):
        with tempfile.TemporaryDirectory() as folder:
            default = BrowserRuntime(folder)
            industrial = BrowserRuntime(folder, session_name='industrial')
            same = BrowserRuntime(folder, session_name='industrial')
            with default._operation(), industrial._operation():
                with self.assertRaises(RuntimeError):
                    with same._operation():
                        self.fail('same session acquired its existing lock')
                self.assertTrue((Path(folder)/'work/browser-operation.lock').exists())
                self.assertTrue((Path(folder)/'work/browser-sessions/industrial/browser-operation.lock').exists())
            self.assertFalse(list(Path(folder).rglob('*.lock')))

    def test_cli_commands_apply_session_to_real_runtime(self):
        def result(runtime, *args):
            return {'home':runtime._env()['BH_HOME']}
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'read.json'
            for command, argv in (
                    ('browser-status', []),
                    ('browser-read', ['--url','https://shop.example/item','--output',str(output)]),
                    ('browser-plan', ['--url','https://shop.example/item','--goal','가격 읽기','--output',str(output)])):
                with self.subTest(command=command), \
                        patch('savetax.browser.environment', return_value={}), \
                        patch.object(BrowserRuntime, 'status', result), \
                        patch.object(BrowserRuntime, 'read', result), \
                        patch.object(BrowserRuntime, 'plan', result), \
                        contextlib.redirect_stdout(io.StringIO()) as stdout:
                    self.assertEqual(main([command,'--session','industrial',*argv]), 0)
                    saved = json.loads(stdout.getvalue()) if command == 'browser-status' else json.loads(output.read_text(encoding='utf-8'))
                    self.assertEqual(saved['home'], str(Path.cwd()/'work/browser-sessions/industrial/browser-state'))

    def test_named_timeout_keeps_existing_tabs_and_releases_own_lock(self):
        with tempfile.TemporaryDirectory() as folder:
            runtime = BrowserRuntime(folder, session_name='industrial')
            runtime.python.parent.mkdir(parents=True)
            runtime.python.touch()
            existing, new = 'A'*32, 'B'*32
            with patch.object(runtime, 'prepare_env', return_value={}), \
                    patch.object(runtime, '_page_targets', side_effect=[{existing}, {existing,new}]), \
                    patch('savetax.browser.subprocess.run', side_effect=[
                        subprocess.TimeoutExpired('read',55), subprocess.CompletedProcess('cleanup',0,'','')]) as run:
                with self.assertRaisesRegex(RuntimeError, '55초'):
                    runtime._run('fixed-read')
            self.assertIn(new, run.call_args.kwargs['input'])
            self.assertNotIn(existing, run.call_args.kwargs['input'])
            self.assertFalse(list(Path(folder).rglob('*.lock')))
