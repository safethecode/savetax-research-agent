"""점수 CLI의 파일 상태와 HTTP 경계를 검증한다. 모든 네트워크는 모의 응답이다."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

from savetax.cli import main, write_json
from savetax.client import SaveTaxClient


def response(status, payload=None, *, decode_error=False):
    value = Mock(status_code=status,headers={})
    if decode_error:
        value.json.side_effect = ValueError('invalid external JSON')
    else:
        value.json.return_value = payload
    return value


class ScoreCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name)/'body.json'
        self.receipt = Path(self.temp.name)/'receipt.json'
        self.body = {'canonical_product_id':'001','lines':[{'fact_id':'F1'}]}
        write_json(self.source,self.body)
        self.client = SaveTaxClient(token='savetax_'+'x'*32)
        self.events = []

    def run_score(self, *, amount='200000000', preview=None, submit=None, recovery=None, state='available', extra=(), send=True):
        preview = preview if preview is not None else {'ok':True,'next_action':'submit','total_amount_krw':amount}

        def post(url, **kwargs):
            if url.endswith('/preview'):
                self.events.append(('preview',None))
                return response(200,preview)
            self.events.append(('submit',kwargs['headers']['Idempotency-Key']))
            if isinstance(submit,Exception):
                raise submit
            return submit if submit is not None else response(201,{'submission_id':'S1','amount_krw':amount})

        def get(url, **kwargs):
            if '/submission-requests/' in url:
                self.events.append(('recover',url.rsplit('/',1)[1]))
                if recovery is None:
                    raise AssertionError('unexpected recovery GET')
                return recovery
            self.events.append(('lookup',kwargs.get('params',{}).get('ids')))
            return response(200,{'items':[{'item_id':'001','state':state}]})

        with patch('savetax.client.SaveTaxClient',return_value=self.client), \
                patch('savetax.submissions.requests.post',side_effect=post), \
                patch('savetax.client.requests.get',side_effect=get), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return main(['score','--input',str(self.source),'--receipt',str(self.receipt),
                         *(['--send'] if send else []),*extra])

    def saved(self):
        return json.loads(self.receipt.read_text(encoding='utf-8'))

    def test_submitted_receipt_replay_never_previews_or_submits_again(self):
        self.assertEqual(self.run_score(),0)
        original = self.receipt.read_bytes()
        self.assertEqual(self.saved()['response']['submission_id'],'S1')
        self.assertEqual(self.events[0][0],'preview')
        self.assertEqual(self.events[1],('lookup','001'))
        self.assertEqual(self.events[2][0],'submit')
        self.events.clear()
        self.assertEqual(self.run_score(),0)
        self.assertEqual(self.events,[])
        self.assertEqual(self.receipt.read_bytes(),original)

    def test_verified_small_amount_can_submit_by_default(self):
        self.assertEqual(self.run_score(amount='1992000'),0)
        self.assertEqual(self.saved()['state'],'submitted')
        self.assertEqual([e[0] for e in self.events],['preview','lookup','submit'])

    def test_less_than_100m_is_deferred_without_submission(self):
        self.assertEqual(self.run_score(amount='99999999',extra=('--min-saving','100000000')),0)
        self.assertEqual(self.saved()['state'],'deferred_lower_amount')
        self.assertEqual(self.events,[('preview',None)])

    def test_preview_only_does_not_send_even_when_amount_qualifies(self):
        self.assertEqual(self.run_score(send=False),0)
        self.assertEqual(self.saved()['state'],'previewed')
        self.assertEqual(self.events,[('preview',None)])

    def test_deferred_rerun_keeps_same_key_without_submitting(self):
        self.assertEqual(self.run_score(amount='99999999',extra=('--min-saving','100000000')),0)
        key = self.saved()['idempotency_key']
        self.events.clear()
        self.assertEqual(self.run_score(amount='99999999',extra=('--min-saving','100000000')),0)
        self.assertEqual(self.saved()['state'],'deferred_lower_amount')
        self.assertEqual(self.saved()['idempotency_key'],key)
        self.assertEqual(self.events,[('preview',None)])

    def test_exactly_100m_can_submit_after_fresh_availability_lookup(self):
        self.assertEqual(self.run_score(amount='100000000'),0)
        self.assertEqual(self.saved()['state'],'submitted')
        self.assertEqual([e[0] for e in self.events],['preview','lookup','submit'])

    def test_failed_or_non_submit_preview_never_sends_submission(self):
        for preview in ({'ok':False,'next_action':'submit','total_amount_krw':'200000000'},
                        {'ok':True,'next_action':'revise_existing','total_amount_krw':'200000000'}):
            with self.subTest(preview=preview):
                self.events.clear()
                self.assertEqual(self.run_score(preview=preview),2)
                self.assertEqual(self.events,[('preview',None)])

    def test_every_non_available_state_blocks_final_post(self):
        for state in ('claimed','claimed_by_me','reform_found','on_hold'):
            with self.subTest(state=state):
                self.receipt.unlink(missing_ok=True)
                self.events.clear()
                self.assertEqual(self.run_score(state=state),2)
                self.assertEqual([e[0] for e in self.events],['preview','lookup'])
                self.assertNotEqual(self.saved()['state'],'submitted')

    def test_bad_success_json_and_pending_recovery_never_become_submitted(self):
        self.assertEqual(self.run_score(submit=response(201,decode_error=True)),2)
        key = self.saved()['idempotency_key']
        self.assertEqual(self.saved()['state'],'sending')
        self.events.clear()
        self.assertEqual(self.run_score(recovery=response(202,{'state':'pending'})),0)
        self.assertEqual(self.saved()['state'],'sending')
        self.assertEqual(self.events,[('recover',key)])
        self.events.clear()
        self.assertEqual(self.run_score(recovery=response(200,{'submission_id':'S1'})),0)
        self.assertEqual(self.saved()['state'],'submitted')
        self.assertEqual(self.saved()['response']['submission_id'],'S1')
        self.assertEqual(self.events,[('recover',key)])

    def test_malformed_recovery_preserves_unresolved_request_and_never_posts(self):
        self.assertEqual(self.run_score(submit=requests.Timeout()),2)
        key = self.saved()['idempotency_key']
        self.events.clear()
        self.assertEqual(self.run_score(recovery=response(200,{'state':'pending'})),2)
        self.assertEqual(self.saved()['state'],'sending')
        self.assertEqual(self.events,[('recover',key)])

    def test_legacy_submitted_state_without_receipt_id_is_reconciled(self):
        self.assertEqual(self.run_score(),0)
        saved = self.saved()
        key = saved['idempotency_key']
        saved['response'] = {}
        write_json(self.receipt,saved)
        self.events.clear()
        self.assertEqual(self.run_score(recovery=response(202,{'state':'pending'})),0)
        self.assertEqual(self.saved()['state'],'sending')
        self.assertEqual(self.saved()['idempotency_key'],key)
        self.assertEqual(self.events,[('recover',key)])

    def test_404_recovery_retries_only_same_idempotency_key(self):
        self.assertEqual(self.run_score(submit=requests.Timeout()),2)
        key = self.saved()['idempotency_key']
        self.events.clear()
        self.assertEqual(self.run_score(recovery=response(404,{'code':'NOT_FOUND'})),0)
        self.assertEqual(self.saved()['idempotency_key'],key)
        self.assertEqual(self.saved()['state'],'submitted')
        self.assertEqual(self.events,[('recover',key),('preview',None),('lookup','001'),('submit',key)])

    def test_changed_body_cannot_reuse_receipt_or_send_new_request(self):
        self.assertEqual(self.run_score(),0)
        original = self.receipt.read_bytes()
        write_json(self.source,{**self.body,'title':'changed'})
        self.events.clear()
        self.assertEqual(self.run_score(),2)
        self.assertEqual(self.events,[])
        self.assertEqual(self.receipt.read_bytes(),original)

    def test_invalid_preview_amount_never_submits(self):
        for amount in ('NaN','Infinity','-Infinity','not-money','-1',None,[],{},True,False,2640750.0,-1):
            with self.subTest(amount=amount):
                self.receipt.unlink(missing_ok=True)
                self.events.clear()
                self.assertEqual(self.run_score(amount=amount),2)
                self.assertEqual(self.events,[('preview',None)])

    def test_live_api_integer_amount_can_submit_with_explicit_minimum(self):
        self.assertEqual(self.run_score(amount=2640750,extra=('--min-saving','0')),0)
        self.assertEqual(self.saved()['state'],'submitted')
        self.assertEqual([e[0] for e in self.events],['preview','lookup','submit'])

    def test_preview_missing_amount_never_submits_or_crashes(self):
        self.assertEqual(self.run_score(preview={'ok':True,'next_action':'submit'}),2)
        self.assertEqual(self.events,[('preview',None)])


if __name__ == '__main__':
    unittest.main()
