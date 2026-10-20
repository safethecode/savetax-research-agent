import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from savetax.commands.research import execute
from savetax.adapters.catalog import SaveTaxError
from test_local_research import fixture


class ResearchCliTests(unittest.TestCase):
    def test_hydration_failure_does_not_discard_prior_or_later_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            data,policy,_=fixture(root)
            p=root/'policy.json';p.write_text(json.dumps(policy))
            args=argparse.Namespace(policy=str(p),profile=None,input=None,item_id=['001','002','003'],
                tools=False,root=str(root),env_file='.env.txt',guide=None,run_dir=str(root/'run'))
            client=Mock()
            def get(url,params=None):
                if url.endswith('/current'):
                    return data['event']
                if url.endswith('/lookup'):
                    ident=params['ids']
                    if ident=='002':
                        raise SaveTaxError('mock unavailable',status=503,stage='http')
                    return {'items':[{'item_id':ident,'state':'available'}]}
                return {**copy.deepcopy(data['item']),'item_id':url.rsplit('/',1)[1]}
            client.get_json.side_effect=get
            def research(job,policy,run_dir,**kwargs):
                return {'item_id':job['item']['item_id'],'state':'awaiting_review','package_dir':'fixture-only'}
            with patch('savetax.adapters.catalog.SaveTaxClient',return_value=client), \
                    patch('savetax.commands.research.OllamaClient'), \
                    patch('savetax.commands.research.run_research',side_effect=research) as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(execute(args),2)
            self.assertEqual([c.args[0]['item']['item_id'] for c in run.call_args_list],['001','003'])
            record=json.loads((root/'run/fetch-state.json').read_text())
            self.assertEqual(record['failures'][0]['item_id'],'002')


if __name__=='__main__':
    unittest.main()
