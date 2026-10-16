"""조달 후보 수집과 근거 평가를 연결하는 읽기 전용 CLI."""
import argparse
import hashlib
import json
import sys
import time
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .analysis import dataset_summary, mine_batch

BASE = 'https://hackathon.savetax.now/v1/events/current'
TARGET = '60000000000'


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + '\n', encoding='utf-8')
    temp.replace(path)


def normalize_fact(item, fact):
    tax = fact.get('tax_basis')
    return {
        'item_id': item['item_id'], 'fact_id': fact['fact_id'],
        'model': item.get('snapshot', {}).get('model'), 'unit': fact.get('unit'),
        'comparison_basis_id': fact.get('basis_id'), 'tax_basis': tax,
        'delivered_unit_price': fact.get('unit_price_krw'), 'quantity': fact.get('quantity'),
        'comparable_amount_krw': fact.get('comparable_amount_krw'),
        'scorable': fact.get('scorable'),
        'vat_included': True if tax == 'vat_included' else False if tax == 'vat_excluded' else None,
        'installation_required': None, 'request_date': fact.get('request_date'),
    }


def render_report(result):
    lines = ['# 가격 비교 결과', '',
             f"확인한 비교 조건의 절감 가능액: {Decimal(result['verified_potential_savings_krw']):,.0f}원",
             '목표: 60,000,000,000원(600억 원)',
             '심사 인정액: 미확인 · 실제 예산 절감액: 미확인', '',
             '현재 판매가와 과거 납품요구 기록을 대조한 조사 결과다. 지급·검수 완료나 실제 예산 절감을 뜻하지 않는다.', '',
             '| 물품 | fact | 판정 | 절감 가능액(원) | 확인할 내용 |',
             '|---|---|---|---:|---|']
    for row in result['results']:
        reason = '; '.join(row.get('reasons', [])) or '비교 조건 확인'
        clean = lambda value: str(value).replace('|', '/').replace('\n', ' ')
        lines.append('| ' + ' | '.join(map(clean, [row.get('item_id'), row.get('fact_id', ''),
                     row['status'], row.get('potential_savings_krw') or '미산정', reason])) + ' |')
    lines.append('')
    for row in result['results']:
        offer = row.get('selected_offer')
        if offer:
            lines.extend([f"- {row['item_id']}: {offer.get('url')} ({offer.get('observed_at')})",
                          f"  - 직접 확인한 문구: {offer.get('quote', '')}"])
    return '\n'.join(lines) + '\n'


def _mine(args):
    from .rules import apply_rules, validate_strategy
    strategy = read_json(args.strategy)
    validate_strategy(strategy)
    fingerprint = hashlib.sha256(json.dumps(strategy, sort_keys=True).encode()).hexdigest()
    identity = {'handle': args.handle, 'dataset_version': args.dataset_version,
                'parquet': str(Path(args.parquet).resolve()), 'strategy_sha256': fingerprint}
    state = read_json(args.state) if Path(args.state).exists() else {**identity, 'next_offset': 0}
    if any(state.get(k) != v for k, v in identity.items()):
        raise ValueError('재개 상태의 handle·데이터셋·경로·전략이 다릅니다. 새 state/output 경로를 지정하세요')
    existing = read_json(args.output) if Path(args.output).exists() else {'identity': identity, 'candidates': []}
    if existing.get('identity') != identity:
        raise ValueError('후보 출력 파일이 다른 조사에 속합니다')
    if state['next_offset'] and not Path(args.output).exists():
        raise ValueError('재개할 후보 출력 파일이 없습니다')
    by_id = {x['item_id']: x for x in existing['candidates']}
    batch_size = strategy.get('batch_size', 500)
    for _ in range(args.batches):
        offset = state['next_offset']
        rows = mine_batch(args.parquet, args.handle, args.dataset_version, batch_size, offset)
        if not rows:
            state['exhausted'] = True
            break
        selected = apply_rules(rows, strategy)
        for row in selected:
            row['batch_offset'] = offset
            by_id[row['item_id']] = row
        # 출력 성공 뒤에만 cursor 전진. 중단 시 같은 묶음 재처리는 item_id로 중복 제거한다.
        write_json(args.output, {'identity': identity, 'candidates': list(by_id.values())})
        state['next_offset'] = offset + len(rows)
        state['exhausted'] = len(rows) < batch_size
        write_json(args.state, state)
        print(f"표본 {offset}~{state['next_offset']}: 후보 {len(selected)}개, 누적 {len(by_id)}개")
        if state['exhausted']:
            break
    write_json(args.state, state)


def _hydrate(args):
    from .client import SaveTaxClient, SaveTaxError
    client = SaveTaxClient(guide_path=args.guide)
    data = read_json(args.input)
    candidates = data['candidates'] if isinstance(data, dict) else data
    existing = read_json(args.output) if Path(args.output).exists() else {'items': [], 'failures': []}
    done = {i['item_id'] for i in existing['items']}
    failures = {f['item_id']: f for f in existing.get('failures', [])}
    pending = [r for r in candidates if r['item_id'] not in done][:args.limit]
    for row in pending:
        item_id = row['item_id']
        try:
            lookup = client.get_json(BASE + '/items/lookup', params={'ids': item_id})
            lookup_row = next(iter(lookup.get('items', [])), {})
            if lookup_row.get('state') != 'available':
                failures[item_id] = {'item_id': item_id, 'stage': 'lookup', 'state': lookup_row.get('state'),
                                     'hold_until': lookup_row.get('hold_until'), 'retryable': True}
            else:
                item = client.get_json(BASE + '/items/' + item_id)
                existing['items'].append(item)
                failures.pop(item_id, None)
                print(f"{item_id}: fact {len(item.get('facts', []))}개")
        except SaveTaxError as exc:
            failures[item_id] = {'item_id': item_id, 'stage': getattr(exc, 'stage', 'http'),
                                 'code': getattr(exc, 'code', None), 'retryable': True}
        existing['failures'] = list(failures.values())
        write_json(args.output, existing)
        time.sleep(0.55)


def _evaluate(args):
    from .evidence import evaluate_candidate
    data = read_json(args.input)
    candidates = data['candidates'] if isinstance(data, dict) else data
    results, seen = [], set()
    total = Decimal(0)
    for candidate in candidates:
        fact = candidate['fact']
        result = evaluate_candidate(fact, candidate.get('offers', []))
        result.update({'item_id': fact['item_id'], 'fact_id': fact.get('fact_id')})
        key = fact.get('fact_id')
        if result['status'] == 'verified':
            if not key or key in seen:
                result['status'] = 'needs_review'
                result['reasons'] = result.get('reasons', []) + ['fact_id 누락 또는 중복으로 합산 제외']
            else:
                seen.add(key)
                total += Decimal(result.get('potential_savings_krw') or '0')
        results.append(result)
    output = {'observed_at': datetime.now(timezone.utc).isoformat(), 'target_krw': TARGET,
              'verified_potential_savings_krw': format(total, 'f'),
              'reviewed_amount_krw': None, 'realized_savings_krw': None,
              'remaining_target_krw': format(max(Decimal(TARGET) - total, Decimal(0)), 'f'), 'results': results}
    write_json(args.output, output)
    Path(args.output).with_suffix('.md').write_text(render_report(output), encoding='utf-8')
    print(f"비교 조건 확인 {sum(r['status'] == 'verified' for r in results)}건 · 절감 가능액 {total:,.0f}원")


def _download(args):
    from .client import SaveTaxClient
    destination = Path(args.output)
    archive = SaveTaxClient(guide_path=args.guide).download_dataset(destination)
    target = destination.parent.resolve()
    with zipfile.ZipFile(archive) as bundle:
        if sum(i.file_size for i in bundle.infolist()) > 2_000_000_000:
            raise ValueError('압축 해제 용량 상한 2GB 초과')
        for info in bundle.infolist():
            resolved = (target / info.filename).resolve()
            if not resolved.is_relative_to(target) or info.external_attr >> 16 & 0o170000 == 0o120000:
                raise ValueError('안전하지 않은 ZIP 경로')
        bundle.extractall(target)
    print(f'데이터셋 저장: {archive}')


def main(argv=None):
    parser = argparse.ArgumentParser(description='SaveTax 국내 우선 가격 조사 하네스 (읽기 전용)')
    sub = parser.add_subparsers(dest='command', required=True)
    download = sub.add_parser('download', help='공식 인증 ZIP 다운로드·압축 해제')
    download.add_argument('--output', default='work/data/savetax-products.zip')
    download.add_argument('--guide', default='savetax-agent-guide.md')
    summary = sub.add_parser('summary', help='원본 건수와 중복 제거 납품요구 합계')
    summary.add_argument('--parquet', required=True)
    mine = sub.add_parser('mine', help='고정 무작위 묶음의 후보 선별·재개')
    for name in ('parquet', 'handle', 'dataset-version'):
        mine.add_argument('--' + name, required=True)
    mine.add_argument('--strategy', default='strategies/domestic-first.json')
    mine.add_argument('--state', default='work/state.json')
    mine.add_argument('--output', default='work/candidates.json')
    mine.add_argument('--batches', type=int, default=1)
    hydrate = sub.add_parser('hydrate', help='후보 가용성과 공식 fact 조회')
    hydrate.add_argument('--input', default='work/candidates.json')
    hydrate.add_argument('--output', default='work/facts.json')
    hydrate.add_argument('--guide', default='savetax-agent-guide.md')
    hydrate.add_argument('--limit', type=int, default=10)
    evaluate = sub.add_parser('evaluate', help='판매가 증거 평가·한국어 보고서')
    evaluate.add_argument('--input', required=True)
    evaluate.add_argument('--output', default='work/evaluation.json')
    feedback = sub.add_parser('feedback', help='반려 피드백으로 DSL 개선안 생성')
    feedback.add_argument('--strategy', default='strategies/domestic-first.json')
    feedback.add_argument('--input', required=True)
    feedback.add_argument('--output', default='work/strategy-proposal.json')
    market = sub.add_parser('market-search', help='다이소·다나와 MCP 실제 검색')
    market.add_argument('--provider', required=True, choices=['daiso', 'danawa'])
    market.add_argument('--query', required=True)
    market.add_argument('--limit', type=int, default=5)
    market.add_argument('--output', default='work/market-search.json')
    args = parser.parse_args(argv)
    try:
        if args.command == 'download':
            _download(args)
        elif args.command == 'summary':
            print(json.dumps(dataset_summary(args.parquet), ensure_ascii=False, indent=2))
        elif args.command == 'mine':
            if args.batches < 1:
                raise ValueError('batches는 1 이상이어야 합니다')
            _mine(args)
        elif args.command == 'hydrate':
            if not 1 <= args.limit <= 100:
                raise ValueError('limit은 1~100이어야 합니다')
            _hydrate(args)
        elif args.command == 'evaluate':
            _evaluate(args)
        elif args.command == 'feedback':
            from .rules import learn_from_feedback
            write_json(args.output, learn_from_feedback(read_json(args.strategy), read_json(args.input)))
        elif args.command == 'market-search':
            from .market import MarketClient
            write_json(args.output, MarketClient(args.provider).search(args.query, args.limit))
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0
