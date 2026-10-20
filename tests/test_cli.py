import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from savetax.cli import main, normalize_fact, write_json


class CliTests(unittest.TestCase):
    def test_fact_keeps_official_basis_and_uncertain_installation(self):
        item = {'item_id': '001', 'snapshot': {'model': 'ABC'}, 'facts': []}
        fact = {'fact_id': 'F1', 'unit': '대', 'tax_basis': 'vat_included',
                'basis_id': 'basis:대:vat_included', 'unit_price_krw': '100',
                'quantity': '3', 'comparable_amount_krw': '299', 'scorable': True}
        out = normalize_fact(item, fact)
        self.assertEqual(out['comparison_basis_id'], fact['basis_id'])
        self.assertEqual(out['comparable_amount_krw'], '299')
        self.assertIsNone(out['installation_required'])

    def test_evaluate_missing_offer_does_not_invent_savings(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/'evidence.json', Path(folder)/'result.json'
            write_json(source, {'candidates': [{'fact': {
                'item_id': '001', 'model': 'ABC', 'unit': '대', 'delivered_unit_price': '100',
                'quantity': '10', 'vat_included': True, 'installation_required': False}, 'offers': []}]})
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(['evaluate', '--input', str(source), '--output', str(output)])
            self.assertEqual(code, 0)
            result = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(result['verified_potential_savings_krw'], '0')
            self.assertEqual(result['target_krw'], '60000000000')
            self.assertIsNone(result['realized_savings_krw'])
            self.assertTrue(output.with_suffix('.md').exists())

    def test_resume_bound_to_handle_dataset_and_strategy(self):
        with tempfile.TemporaryDirectory() as folder:
            state, output, strategy = [Path(folder)/p for p in ('state.json','out.json','strategy.json')]
            write_json(state, {'handle': 'other', 'dataset_version': 'v1', 'next_offset': 500})
            write_json(strategy, {'version': 1, 'name': 'x', 'filters': [], 'order_by': [], 'batch_size': 500})
            with patch('savetax.cli.mine_batch') as mining:
                with contextlib.redirect_stderr(io.StringIO()):
                    code = main(['mine', '--parquet', 'unused', '--handle', 'public', '--dataset-version', 'v1',
                                 '--strategy', str(strategy), '--state', str(state), '--output', str(output)])
            self.assertEqual(code, 2)
            mining.assert_not_called()

    def test_hydrate_claimed_item_remains_available_for_general_report(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/'input.json', Path(folder)/'facts.json'
            write_json(source, {'candidates': [{'item_id': '001'}]})
            with patch('savetax.adapters.catalog.SaveTaxClient') as factory, patch('savetax.cli.time.sleep'):
                factory.return_value.get_json.side_effect = [
                    {'items': [{'item_id': '001', 'state': 'claimed'}]},
                    {'item_id': '001', 'facts': [], 'availability': {'state': 'claimed'}}]
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['hydrate','--input',str(source),'--output',str(output)]),0)
            self.assertEqual(len(json.loads(output.read_text(encoding='utf-8'))['items']),1)

    def test_reports_reads_rejected_review_status_history(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'status.json'
            with patch('savetax.adapters.catalog.SaveTaxClient') as factory:
                factory.return_value.get_json.side_effect = [
                    {'reports': [{'report_id': 'r1', 'review_status': 'rejected'}]},
                    {'history': [{'review_code': 'MODEL_MISMATCH'}]}]
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['reports', '--output', str(output)]),0)
            self.assertIn('r1', json.loads(output.read_text(encoding='utf-8'))['rejected_histories'])

    def test_report_replay_preserves_receipt_and_never_resends_success(self):
        with tempfile.TemporaryDirectory() as folder:
            source, receipt = Path(folder)/'report.json', Path(folder)/'receipt.json'
            body = {'product_id': '001', 'product_name': '상품',
                    'reason': '같은 모델의 현재 판매 페이지를 직접 확인했으며 조건 확인이 필요합니다.',
                    'source_url': 'https://example.com/item'}
            write_json(source, body)
            with patch('savetax.adapters.catalog.SaveTaxClient'), patch('savetax.adapters.reports.ReportClient') as reports:
                reports.return_value.submit.return_value = {'report_id': 'R-123', 'review_status': 'submitted'}
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['report', '--input', str(source), '--receipt', str(receipt), '--send']),0)
                    self.assertEqual(main(['report', '--input', str(source), '--receipt', str(receipt)]),0)
                    self.assertEqual(main(['report', '--input', str(source), '--receipt', str(receipt), '--send']),0)
            saved = json.loads(receipt.read_text(encoding='utf-8'))
            self.assertEqual(saved['response']['report_id'], 'R-123')
            self.assertEqual(saved['state'], 'submitted')
            reports.return_value.submit.assert_called_once()

    def test_hydrate_failure_records_actual_http_status_url_and_time(self):
        from savetax.client import SaveTaxError
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/'input.json', Path(folder)/'facts.json'
            write_json(source, {'candidates': [{'item_id': '001'}]})
            with patch('savetax.adapters.catalog.SaveTaxClient') as factory, patch('savetax.cli.time.sleep'):
                factory.return_value.get_json.side_effect = SaveTaxError('HTTP',status=401,code='invalid_token',stage='http')
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['hydrate','--input',str(source),'--output',str(output)]),0)
            row = json.loads(output.read_text(encoding='utf-8'))['failures'][0]
            self.assertEqual(row['http_status'],401)
            self.assertEqual(row['host'],'hackathon.savetax.now')
            self.assertIn('/items/lookup',row['url'])
            self.assertIn('+00:00',row['observed_at'])


if __name__ == '__main__':
    unittest.main()
