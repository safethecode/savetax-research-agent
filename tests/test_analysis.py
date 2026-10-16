import tempfile
import unittest
from pathlib import Path

import duckdb

from savetax.analysis import DatasetError, dataset_summary, mine_batch


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'listings.parquet'
        con = duckdb.connect()
        con.execute('''CREATE TABLE sample(listing_id VARCHAR, item_id VARCHAR, name VARCHAR,
            model VARCHAR, manufacturer VARCHAR, detail_category VARCHAR, unit VARCHAR,
            price DOUBLE, dlv_key VARCHAR, dlv_amount DOUBLE, dlv_qty DOUBLE, dlv_lines INTEGER)''')
        con.executemany('INSERT INTO sample VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', [
            ('L1', '001', '모니터', 'ABC', '제조사', '모니터', '대', 100, 'D1', 1000, 10, 1),
            ('L2', '001', '모니터', 'ABC', '제조사', '모니터', '대', 110, 'D1', 1000, 10, 1),
            ('L3', '002', '모니터', 'DEF', '제조사', '모니터', '대', 50, 'D2', 500, 10, 1),
            ('L4', '003', '기록없음', 'GHI', '제조사', '모니터', '대', 100, None, None, None, None),
        ])
        con.execute('COPY sample TO ? (FORMAT PARQUET)', [str(self.path)])
        con.close()

    def tearDown(self):
        self.temp.cleanup()

    def test_delivery_key_deduplicated_and_missing_preserved(self):
        summary = dataset_summary(self.path)
        self.assertEqual(summary['listing_count'], 4)
        self.assertEqual(summary['item_count'], 3)
        self.assertEqual(summary['delivery_amount_krw'], '1500')
        rows = mine_batch(self.path, 'public', 'v1', 3, 0)
        self.assertEqual(len(rows), 3)
        by_id = {r['item_id']: r for r in rows}
        self.assertEqual(by_id['001']['dlv_amount'], '1000')
        self.assertEqual(by_id['001']['dlv_qty'], '10')
        self.assertIsNone(by_id['003']['dlv_amount'])

    def test_batches_do_not_overlap_and_preserve_leading_zero(self):
        first = mine_batch(self.path, 'public', 'v1', 2, 0)
        second = mine_batch(self.path, 'public', 'v1', 2, 2)
        self.assertFalse({x['item_id'] for x in first} & {x['item_id'] for x in second})
        self.assertEqual({x['item_id'] for x in first + second}, {'001', '002', '003'})
        self.assertEqual(first, mine_batch(self.path, 'public', 'v1', 2, 0))

    def test_missing_schema_rejected_and_parameters_bounded(self):
        with self.assertRaises(ValueError):
            mine_batch(self.path, 'public', 'v1', 0, 0)
        empty = Path(self.temp.name) / 'bad.parquet'
        con = duckdb.connect()
        con.execute('COPY (SELECT 1 AS arbitrary) TO ? (FORMAT PARQUET)', [str(empty)])
        with self.assertRaises(DatasetError):
            dataset_summary(empty)


if __name__ == '__main__':
    unittest.main()
