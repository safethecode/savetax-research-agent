import tempfile
import unittest
from pathlib import Path

import duckdb

from scripts.build_full_index import build_index


class FullIndexTests(unittest.TestCase):
    def test_all_items_have_one_owner_and_delivery_duplicates_are_removed(self):
        with tempfile.TemporaryDirectory() as folder:
            source, output = Path(folder)/'source.parquet', Path(folder)/'index.parquet'
            con = duckdb.connect()
            con.execute("""CREATE TABLE sample AS SELECT
                lpad(i::VARCHAR,8,'0') item_id, '상품' AS name, 'M'||i model,
                '제조사' manufacturer, '품명' detail_category, '개' unit,
                200 price, 'D'||i dlv_key, 100 dlv_amount, 3 dlv_qty
                FROM range(2003) t(i)""")
            con.execute("INSERT INTO sample SELECT * FROM sample WHERE item_id='00000000'")
            con.table('sample').write_parquet(str(source))
            result = build_index(source,output)
            self.assertEqual(result['items'],2003)
            self.assertEqual(result['owners'],[(0,503),(1,500),(2,500),(3,500)])
            con.read_parquet(str(output)).create_view('catalog')
            self.assertEqual(con.execute('SELECT count(DISTINCT item_id),count(DISTINCT md5_rank) FROM catalog').fetchone(),(2003,2003))
            self.assertEqual(con.execute('SELECT count(*) FROM catalog WHERE owner_slot<>md5_batch%4').fetchone()[0],0)
            self.assertEqual(con.execute("SELECT local_amount_krw,local_quantity,listing_count FROM catalog WHERE item_id='00000000'").fetchone(),(100,3,2))
            expected = con.execute("SELECT item_id FROM sample GROUP BY item_id ORDER BY md5('삼손:20261010-r5:'||item_id),item_id LIMIT 1").fetchone()[0]
            self.assertEqual(con.execute('SELECT item_id FROM catalog WHERE md5_rank=0').fetchone()[0],expected)
            con.close()
