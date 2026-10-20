"""전체 데이터에서 물품별 고정 표본과 중복 없는 납품요구 합계를 만든다."""
from decimal import Decimal
from pathlib import Path

import duckdb


class DatasetError(ValueError):
    pass


REQUIRED = {'listing_id', 'item_id', 'name', 'model', 'manufacturer',
            'detail_category', 'unit', 'price', 'dlv_key', 'dlv_amount',
            'dlv_qty', 'dlv_lines'}


def _open(path):
    path = Path(path).resolve(strict=True)
    con = duckdb.connect()
    con.read_parquet(str(path)).create_view('listings')
    columns = {r[0] for r in con.execute('DESCRIBE listings').fetchall()}
    if missing := REQUIRED - columns:
        con.close()
        raise DatasetError('필수 컬럼 누락: ' + ', '.join(sorted(missing)))
    return con


def _number(value):
    if value is None:
        return None
    return format(Decimal(str(value)).normalize(), 'f')


def dataset_summary(path):
    con = _open(path)
    try:
        listings, items = con.execute("SELECT count(*), count(DISTINCT item_id) FROM listings WHERE item_id IS NOT NULL AND item_id <> ''").fetchone()
        amount, qty, keys = con.execute('''SELECT sum(dlv_amount), sum(dlv_qty), count(*) FROM
            (SELECT dlv_key, max(dlv_amount) dlv_amount, max(dlv_qty) dlv_qty FROM listings
             WHERE dlv_key IS NOT NULL AND CAST(dlv_key AS VARCHAR) <> '' GROUP BY dlv_key)''').fetchone()
        return {'listing_count': listings, 'item_count': items,
                'delivery_key_count': keys, 'delivery_amount_krw': _number(amount),
                'delivery_quantity': _number(qty),
                'basis': '최종 차수 납품요구; dlv_key 중복 제거; 지급 완료 아님'}
    finally:
        con.close()


def mine_batch(path, handle, dataset_version, batch_size=500, offset=0):
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or not 1 <= batch_size <= 10000:
        raise ValueError('batch_size는 1~10000 정수여야 합니다')
    if not isinstance(offset, int) or isinstance(offset, bool) or offset < 0:
        raise ValueError('offset은 0 이상의 정수여야 합니다')
    if not handle or not dataset_version or str(handle).startswith('savetax_'):
        raise ValueError('공개 handle과 데이터셋 버전이 필요합니다')
    con = _open(path)
    try:
        cursor = con.execute('''WITH selected AS (
            SELECT DISTINCT item_id FROM listings WHERE item_id IS NOT NULL AND item_id <> ''
            ORDER BY md5(? || ':' || ? || ':' || item_id), item_id LIMIT ? OFFSET ?
        ), products AS (
            SELECT l.item_id, min(l.listing_id) listing_id,
                any_value(l.name) product_name, any_value(l.model) model,
                any_value(l.manufacturer) manufacturer,
                any_value(l.detail_category) detail_category, any_value(l.unit) unit,
                min(CASE WHEN l.price > 1 THEN l.price END) price,
                count(*) listing_count
            FROM listings l JOIN selected s USING (item_id) GROUP BY l.item_id
        ), deliveries AS (
            SELECT l.item_id, l.dlv_key, max(l.dlv_amount) amount,
                max(l.dlv_qty) qty, max(l.dlv_lines) lines
            FROM listings l JOIN selected s USING (item_id)
            WHERE l.dlv_key IS NOT NULL AND CAST(l.dlv_key AS VARCHAR) <> '' GROUP BY l.item_id, l.dlv_key
        ), totals AS (
            SELECT item_id, sum(amount) dlv_amount, sum(qty) dlv_qty, sum(lines) dlv_count
            FROM deliveries GROUP BY item_id
        ) SELECT p.*, t.dlv_amount, t.dlv_qty, t.dlv_count
            FROM products p LEFT JOIN totals t USING(item_id)
            ORDER BY t.dlv_amount DESC NULLS LAST, p.item_id''',
            [str(handle), str(dataset_version), batch_size, offset])
        names = [r[0] for r in cursor.description]
        rows = [dict(zip(names, r)) for r in cursor.fetchall()]
        for row in rows:
            for field in ('price', 'dlv_amount', 'dlv_qty', 'dlv_count'):
                row[field] = _number(row[field])
        return rows
    finally:
        con.close()
