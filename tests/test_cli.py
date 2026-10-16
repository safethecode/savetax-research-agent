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


if __name__ == '__main__':
    unittest.main()
