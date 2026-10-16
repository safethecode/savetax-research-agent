"""전체 ZIP의 Parquet를 물품별로 집계하고 500개 단위로 담당을 나눈다.

로컬 집계는 탐색용이다. 점수 계산에는 공식 event fact를 다시 읽는다.
"""
import argparse
from pathlib import Path

import duckdb


def build_index(source, output):
    source = Path(source).resolve(strict=True)
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    try:
        con.read_parquet(str(source)).create_view('listings')
        con.execute("""CREATE TEMP TABLE catalog AS
            WITH products AS (
                SELECT item_id, any_value(name) product_name, any_value(model) model,
                    any_value(manufacturer) manufacturer,
                    any_value(detail_category) detail_category, any_value(unit) unit,
                    min(CASE WHEN price > 1 THEN price END) min_list_price,
                    max(CASE WHEN price > 1 THEN price END) max_list_price,
                    count(*) listing_count
                FROM listings WHERE item_id IS NOT NULL AND item_id <> '' GROUP BY item_id
            ), deliveries AS (
                SELECT item_id, dlv_key, max(dlv_amount) amount, max(dlv_qty) quantity
                FROM listings WHERE dlv_key IS NOT NULL AND CAST(dlv_key AS VARCHAR) <> ''
                GROUP BY item_id, dlv_key
            ), totals AS (
                SELECT item_id, sum(amount) local_amount_krw, sum(quantity) local_quantity
                FROM deliveries GROUP BY item_id
            ), ranked AS (
                SELECT p.*, t.local_amount_krw, t.local_quantity,
                    row_number() OVER (ORDER BY md5('삼손:20261010-r5:' || p.item_id),p.item_id)-1 md5_rank
                FROM products p LEFT JOIN totals t USING (item_id)
            ) SELECT *, CAST(floor(md5_rank/500) AS BIGINT) md5_batch,
                CAST(floor(md5_rank/500) AS BIGINT)%4 owner_slot
              FROM ranked ORDER BY md5_rank""")
        # Path is bound by the relation writer rather than interpolated into SQL.
        con.table('catalog').write_parquet(str(output), compression='zstd')
        return {'items':con.execute('SELECT count(*) FROM catalog').fetchone()[0],
                'owners':con.execute('SELECT owner_slot,count(*) FROM catalog GROUP BY owner_slot ORDER BY owner_slot').fetchall(),
                'output':str(output)}
    finally:
        con.close()


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(build_index(args.source,args.output),ensure_ascii=False))
