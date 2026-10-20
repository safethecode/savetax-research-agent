"""Execute the actual child program against a DOM-change race, without a browser."""
import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from savetax.adapters.browser import BrowserRuntime


class JevStalePageTests(unittest.TestCase):
    def test_changed_page_repredicts_within_the_existing_step_budget(self):
        class StalePage(Exception):
            pass
        class Agent:
            def __init__(self,*args,**kwargs):
                self.actions=0
                self.state={'decisions':[{'model':'fixture-jev'}]}
                self.browser=types.SimpleNamespace(observe=lambda **kwargs:{
                    'url':'https://shop.example/item','title':'ABC','text':'ABC 100000원'})
            def __enter__(self):
                return self
            def __exit__(self,*args):
                return False
            def command(self,name,argument=None):
                if name=='predict':
                    return {'page':{'actions':[],'fingerprint':'observed'},
                            'decision':{'operation':'DONE','choice':'none','confidence':1,'latency_ms':1}}
                self.actions+=1
                if self.actions==1:
                    raise StalePage('page changed before action')
        package=types.ModuleType('jev_ultrafast');package.Agent=Agent
        browser=types.ModuleType('jev_ultrafast.browser');browser.StalePage=StalePage
        model=types.ModuleType('jev_ultrafast.model');model.field_context=lambda *args:None
        def run(code,**kwargs):
            output=io.StringIO()
            with patch.dict(sys.modules,{'jev_ultrafast':package,'jev_ultrafast.browser':browser,
                                        'jev_ultrafast.model':model}),contextlib.redirect_stdout(output):
                exec(compile(code,'jev-child','exec'),{})
            return json.loads(output.getvalue().strip())
        with tempfile.TemporaryDirectory() as root:
            runtime=BrowserRuntime(root=root)
            with patch.object(runtime,'_env',return_value={'TYPESAFE_API_KEY':'test-only'}), \
                    patch.object(runtime,'_run',side_effect=run):
                result=runtime.run_jev('https://shop.example/item','Read product details only',max_steps=2)
        self.assertEqual(result['stopped'],'done')
        self.assertEqual(len(result['steps']),2)
        self.assertTrue(result['steps'][0]['stale_page'])
        self.assertEqual(result['text'],'ABC 100000원')
