import copy
import json
from pathlib import Path
import tempfile
import unittest

from savetax.application.research import run_research
from savetax.domain.scoring import build_draft, calculate_body


def fixture(root):
    text = 'ABC 새상품 완제품 1대 판매가 100000원 부가세 포함 무료배송 구매 가능'
    source = Path(root) / 'source.txt'
    source.write_text(text, encoding='utf-8')
    item = {'item_id':'001', 'snapshot':{'model':'ABC'}, 'availability':{'state':'available'},
            'facts_total':1, 'facts_truncated':False, 'facts':[
                {'fact_id':'F1','contract_no':'C1','request_no':'R1','line_no':'1',
                 'unit':'대','tax_basis':'vat_included','basis_id':'basis:대:vat_included',
                 'period_kind':'none','scorable':True,'quantity':'1000','comparable_amount_krw':'300000000'}]}
    values = {'model':'ABC','unit_price':'100000','vat_included':True,'shipping_included':True,
              'pack_quantity':1,'unit':'대','new':True,'purchase_available':True,'complete_product':True}
    proposal = {'schema_version':'1','comparison_kind':'identical','unknowns':[],
                'claims':[{'field':key,'value':value,'status':'observed','source_id':'S1',
                           'quote':text,'location':'text:1'} for key,value in values.items()]}
    data = {'item':item,'event':{'dataset_release_id':'release','ruleset_version':'rules'},
            'sources':[{'source_id':'S1','path':str(source),'url':'https://shop.example/item',
                        'kind':'retailer','method':'fixture','observed_at':'2026-10-20T00:00:00Z',
                        'truncated':False}]}
    policy = {'schema_version':'1','policy_id':'test-research','allow_submit':False,'allow_revise':False,
              'max_actions':4,'max_searches':1,'max_reads':1,'max_attempts':2,'max_candidates':20,
              'jev_steps':8}
    return data, policy, proposal


class Model:
    def __init__(self, actions):
        self.actions = iter(actions)
        self.calls = 0
        self.last_metadata = {'model':'fixture-only','provider':'test'}

    def generate(self, prompt, schema):
        self.calls += 1
        value = next(self.actions)
        if isinstance(value, Exception):
            raise value
        return value


class LocalResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data, self.policy, self.proposal = fixture(self.root)

    def test_draft_does_not_masquerade_as_verified_manual_offer(self):
        offer = {'model':'ABC','url':'https://shop.example/item','quote':'ABC 100000원',
                 'unit_price':'100000','vat_included':True,'shipping_included':True,
                 'observed_at':'2026-10-20'}
        body = build_draft(self.data['item'], offer, self.data['event'])
        self.assertNotIn('price_verified',offer)
        self.assertEqual(calculate_body(self.data['item'],body)['total_savings_krw'],'200000000')

    def test_finish_builds_immutable_package_and_resume_skips_inference(self):
        model = Model([{'action':'finish','query':None,'url':None,'proposal':self.proposal}])
        state = run_research(self.data,self.policy,self.root/'run',model=model)
        self.assertEqual(state['state'],'awaiting_review')
        package = Path(state['package_dir'])
        manifest = json.loads((package/'manifest.json').read_text(encoding='utf-8'))
        self.assertIsNotNone(manifest['body'])
        self.assertNotIn('price_verified',json.dumps(manifest))
        self.assertEqual(run_research(self.data,self.policy,self.root/'run',model=model),state)
        self.assertEqual(model.calls,1)

    def test_unknown_cost_or_search_snippet_cannot_build_body(self):
        for field in ('shipping_included','vat_included','pack_quantity','model'):
            with self.subTest(field=field):
                proposal = copy.deepcopy(self.proposal)
                next(x for x in proposal['claims'] if x['field']==field)['status']='unknown'
                model = Model([{'action':'finish','query':None,'url':None,'proposal':proposal}])
                state = run_research(self.data,self.policy,self.root/field,model=model)
                manifest = json.loads((Path(state['package_dir'])/'manifest.json').read_text(encoding='utf-8'))
                self.assertIsNone(manifest['body'])
        data = copy.deepcopy(self.data)
        data['sources'][0]['kind']='search'
        state = run_research(data,self.policy,self.root/'snippet',model=Model([
            {'action':'finish','query':None,'url':None,'proposal':self.proposal}]))
        self.assertIsNone(json.loads((Path(state['package_dir'])/'manifest.json').read_text())['body'])

    def test_quote_must_exist_in_source_and_authority_flags_are_rejected(self):
        proposal = copy.deepcopy(self.proposal)
        proposal['claims'][0]['quote']='not in source'
        state = run_research(self.data,self.policy,self.root/'badquote',model=Model([
            {'action':'finish','query':None,'url':None,'proposal':proposal}]))
        self.assertIsNone(json.loads((Path(state['package_dir'])/'manifest.json').read_text())['body'])
        proposal['approved']=True
        with self.assertRaises(ValueError):
            run_research(self.data,self.policy,self.root/'authority',model=Model([
                {'action':'finish','query':None,'url':None,'proposal':proposal}]))

    def test_model_cannot_read_invented_url_or_execute_shell(self):
        for action in ({'action':'read','query':None,'url':'https://invented.example','proposal':None},
                       {'action':'shell','query':'whoami','url':None,'proposal':None}):
            with self.subTest(action=action), self.assertRaises(ValueError):
                run_research(self.data,self.policy,self.root/action['action'],model=Model([action]))

    def test_timeout_preserves_sources_and_bounded_retry(self):
        model = Model([RuntimeError('model unavailable'),RuntimeError('model unavailable')])
        run = self.root/'timeout'
        for status in ('retry_wait','failed'):
            with self.assertRaises(RuntimeError):
                run_research(self.data,self.policy,run,model=model)
            state = json.loads((run/'jobs'/'001'/'job.json').read_text())
            self.assertEqual(state['state'],status)
            self.assertTrue((run/'jobs'/'001'/'sources'/'S1.txt').exists())
        with self.assertRaises(ValueError):
            run_research(self.data,self.policy,run,model=model)
        self.assertEqual(model.calls,2)

    def test_resume_rejects_policy_or_input_change(self):
        run = self.root/'identity'
        run_research(self.data,self.policy,run,model=Model([
            {'action':'finish','query':None,'url':None,'proposal':self.proposal}]))
        with self.assertRaises(ValueError):
            run_research(self.data,{**self.policy,'policy_id':'changed'},run,model=Model([]))

    def test_malformed_field_types_stay_unreviewed_without_crashing_job(self):
        for field,value in (('model',123),('unit_price',True),('pack_quantity',-1),('unit',None)):
            proposal=copy.deepcopy(self.proposal)
            next(c for c in proposal['claims'] if c['field']==field)['value']=value
            with self.subTest(field=field):
                state=run_research(self.data,self.policy,self.root/('type-'+field),model=Model([
                    {'action':'finish','query':None,'url':None,'proposal':proposal}]))
                manifest=json.loads((Path(state['package_dir'])/'manifest.json').read_text())
                self.assertIsNone(manifest['body'])

    def test_resume_detects_original_source_bytes_changed(self):
        run=self.root/'source-identity'
        run_research(self.data,self.policy,run,model=Model([
            {'action':'finish','query':None,'url':None,'proposal':self.proposal}]))
        Path(self.data['sources'][0]['path']).write_text('changed original')
        with self.assertRaises(ValueError):
            run_research(self.data,self.policy,run,model=Model([]))

    def test_twenty_source_backed_cases_have_decimal_calculation(self):
        for i in range(20):
            data = copy.deepcopy(self.data)
            data['item']['facts'][0]['quantity']=str(i+1)
            data['item']['facts'][0]['comparable_amount_krw']=str(300000*(i+1))
            state = run_research(data,self.policy,self.root/f'case-{i}',model=Model([
                {'action':'finish','query':None,'url':None,'proposal':self.proposal}]))
            manifest = json.loads((Path(state['package_dir'])/'manifest.json').read_text())
            self.assertEqual(manifest['calculation']['total_savings_krw'],str(200000*(i+1)))

    def test_search_and_jev_are_separate_and_collision_keeps_original_capture(self):
        data=copy.deepcopy(self.data)
        data['sources'][0]['source_id']='read-1'
        proposal=copy.deepcopy(self.proposal)
        for claim in proposal['claims']:
            claim['source_id']='read-1-capture'
        text=Path(self.data['sources'][0]['path']).read_text(encoding='utf-8')
        class Tools:
            def search(self,query):
                return {'results':[{'source_url':'https://shop.example/item','title':'ABC','excerpt':'단서'}]}
            def read(self,url,steps):
                return {'url':url,'text':text,'observed_at':'2026-10-20T00:00:00Z',
                        'steps':[{'operation':'DONE','label':'complete'}]}
        model=Model([
            {'action':'search','query':'ABC 판매가','url':None,'proposal':None},
            {'action':'read','query':None,'url':'https://shop.example/item','proposal':None},
            {'action':'finish','query':None,'url':None,'proposal':proposal}])
        state=run_research(data,self.policy,self.root/'live-tools',model=model,tools=Tools())
        manifest=json.loads((Path(state['package_dir'])/'manifest.json').read_text())
        self.assertEqual(state['searches'],1)
        self.assertEqual(state['reads'],1)
        self.assertEqual([s['source_id'] for s in manifest['sources']],['read-1','read-1-capture'])
        source=manifest['sources'][1]
        self.assertTrue((Path(state['package_dir'])/source['raw_path']).exists())
        self.assertEqual((self.root/'live-tools/jobs/001/sources/read-1.txt').read_text(encoding='utf-8'),text)

    def test_action_budget_persists_and_oversized_sources_are_rejected(self):
        policy={**self.policy,'max_actions':1}
        class Tools:
            def search(self,query):
                return {'results':[]}
        with self.assertRaises(ValueError):
            run_research(self.data,policy,self.root/'budget',model=Model([
                {'action':'search','query':'ABC','url':None,'proposal':None}]),tools=Tools())
        state=json.loads((self.root/'budget/jobs/001/job.json').read_text())
        self.assertEqual(state['actions'],1)
        self.assertEqual(state['state'],'failed')
        Path(self.data['sources'][0]['path']).write_bytes(b'x'*4_000_001)
        model=Model([])
        with self.assertRaises(ValueError):
            run_research(self.data,self.policy,self.root/'large',model=model)
        self.assertEqual(model.calls,0)

    def test_rate_limit_persists_cooldown_for_this_run_before_retry(self):
        from savetax.adapters.parallel import ParallelError
        class Tools:
            def search(self,query):
                raise ParallelError('rate_limited',status=429,retry_after=600)
        run=self.root/'rate-limit'
        with self.assertRaises(RuntimeError):
            run_research(self.data,self.policy,run,model=Model([
                {'action':'search','query':'ABC','url':None,'proposal':None}]),tools=Tools())
        state=json.loads((run/'jobs/001/job.json').read_text())
        self.assertEqual(state['http_status'],429)
        self.assertEqual(state['retry_after'],600)
        model=Model([])
        with self.assertRaises(RuntimeError):
            run_research(self.data,self.policy,run,model=model,tools=Tools())
        self.assertEqual(model.calls,0)


if __name__=='__main__':
    unittest.main()
