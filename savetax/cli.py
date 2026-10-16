"""조달 후보 수집과 근거 평가를 연결하는 읽기 전용 CLI."""
import argparse
import hashlib
import json
import re
import sys
import time
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
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
             '대회 기준으로 동일 상품의 현재 판매가와 납품요구 fact를 대조했다. 가격의 시점 차이는 제외 조건으로 쓰지 않는다.', '',
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
    pending = [r for r in candidates if r['item_id'] not in done
               and (args.retry_failures or r['item_id'] not in failures)][:args.limit]
    for row in pending:
        item_id = row['item_id']
        if not isinstance(item_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',item_id) or 'savetax_' in item_id:
            raise ValueError('물품 식별번호 형식이 올바르지 않습니다')
        request_url = BASE + '/items/lookup'
        try:
            lookup = client.get_json(BASE + '/items/lookup', params={'ids': item_id})
            lookup_row = next(iter(lookup.get('items', [])), {})
            if lookup_row.get('state') not in {'available', 'claimed', 'claimed_by_me', 'reform_found', 'on_hold'}:
                failures[item_id] = {'item_id': item_id, 'stage': 'lookup', 'state': lookup_row.get('state'),
                                     'hold_until': lookup_row.get('hold_until'), 'retryable': True}
            else:
                request_url = BASE + '/items/' + item_id
                item = client.get_json(BASE + '/items/' + item_id)
                existing['items'].append(item)
                failures.pop(item_id, None)
                print(f"{item_id}: fact {len(item.get('facts', []))}개")
        except SaveTaxError as exc:
            failures[item_id] = {'item_id': item_id, 'stage': getattr(exc, 'stage', 'http'),
                                 'code': getattr(exc, 'code', None), 'retryable': True,
                                 'host': 'hackathon.savetax.now', 'url': request_url,
                                 'http_status': getattr(exc, 'status', None),
                                 'retry_after': getattr(exc, 'retry_after', None),
                                 'observed_at': datetime.now(timezone.utc).isoformat()}
            if getattr(exc,'stage',None) == 'transport':
                from .client import diagnose_connection
                failures[item_id]['connection_diagnostic'] = diagnose_connection('hackathon.savetax.now')
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
        event_gap = data.get('event', {}).get('price_gap') if isinstance(data, dict) else None
        result = evaluate_candidate(fact, candidate.get('offers', []), price_gap=event_gap)
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
    hydrate.add_argument('--retry-failures', action='store_true', help='기록한 실패 후보를 다시 확인')
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
    report = sub.add_parser('report', help='일반 제보 검토 또는 명시적으로 접수 (--send)')
    report.add_argument('--input', required=True)
    report.add_argument('--receipt', default='work/report-receipt.json')
    report.add_argument('--guide', default='savetax-agent-guide.md')
    report.add_argument('--send', action='store_true')
    reports = sub.add_parser('reports', help='제보 심사 상태와 반려 이력 확인')
    reports.add_argument('--output', default='work/report-status.json')
    reports.add_argument('--guide', default='savetax-agent-guide.md')
    browser_status = sub.add_parser('browser-status', help='격리 Chrome·하네스·키 준비 상태 확인 (키 값 출력 없음)')
    browser_read = sub.add_parser('browser-read', help='JS 판매 페이지 텍스트와 상세 iframe 주소 수집')
    browser_read.add_argument('--url', required=True)
    browser_read.add_argument('--output', required=True)
    browser_plan = sub.add_parser('browser-plan', help='Jev·TypeSafe의 다음 동작 제안 (실행 전 검토)')
    browser_plan.add_argument('--url', required=True)
    browser_plan.add_argument('--goal', required=True)
    browser_plan.add_argument('--output', required=True)
    parallel = sub.add_parser('parallel-search', help='Parallel API로 국내 판매가 검색 단서 수집')
    parallel.add_argument('--query', required=True)
    parallel.add_argument('--limit', type=int, default=5)
    parallel.add_argument('--output', required=True)
    score_build = sub.add_parser('build-score', help='공식 fact와 확인한 판매가로 점수 본문 생성')
    score_build.add_argument('--input', required=True)
    score_build.add_argument('--output', default='work/score-body.json')
    score = sub.add_parser('score', help='점수 preview 후 억 단위 우선 접수 (--send)')
    score.add_argument('--input', required=True)
    score.add_argument('--receipt', required=True)
    score.add_argument('--guide', default='savetax-agent-guide.md')
    score.add_argument('--min-saving', default='100000000')
    score.add_argument('--send', action='store_true')
    queue = sub.add_parser('queue', help='신규 억 단위 우선·소액 대기 목록 생성')
    queue.add_argument('--input', required=True)
    queue.add_argument('--output', default='work/submission-queue.json')
    queue.add_argument('--remaining', type=int)
    queue.add_argument('--release-deferred', action='store_true')
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
            feedback_data = read_json(args.input)
            if isinstance(feedback_data, dict):
                feedback_data = feedback_data.get('status', feedback_data).get('reports', [])
            write_json(args.output, learn_from_feedback(read_json(args.strategy), feedback_data))
        elif args.command == 'market-search':
            from .market import MarketClient
            write_json(args.output, MarketClient(args.provider).search(args.query, args.limit))
        elif args.command == 'report':
            from .reports import ReportClient, validate_report
            from .client import SaveTaxClient
            body = validate_report(read_json(args.input))
            key = 'research-' + hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            receipt = {'idempotency_key': key, 'body': body, 'state': 'prepared'}
            if Path(args.receipt).exists():
                receipt = read_json(args.receipt)
                if receipt.get('idempotency_key') != key or receipt.get('body') != body:
                    raise ValueError('다른 제보의 영수증입니다. 새 receipt 경로를 사용하세요')
                if receipt.get('state') == 'submitted':
                    print('이미 접수한 영수증을 보존합니다: ' + str(args.receipt))
                    return 0
            else:
                write_json(args.receipt, receipt)
            if args.send:
                receipt['response'] = ReportClient(SaveTaxClient(guide_path=args.guide)).submit(body, key)
                receipt['state'] = 'submitted'
                write_json(args.receipt, receipt)
                print('일반 제보 접수 결과: ' + json.dumps(receipt['response'], ensure_ascii=False))
            else:
                print('일반 제보 검토본 저장: ' + str(args.receipt))
        elif args.command == 'reports':
            from .reports import ReportClient, REPORTS_URL
            from .client import SaveTaxClient
            client = SaveTaxClient(guide_path=args.guide)
            status = ReportClient(client).list_reports()
            rows = status.get('reports', status.get('items', []))
            histories = {}
            for row in rows:
                if row.get('review_status', row.get('status')) == 'rejected' and (report_id := row.get('report_id', row.get('id'))):
                    histories[report_id] = client.get_json(REPORTS_URL + '/' + str(report_id) + '/history')
            write_json(args.output, {'status': status, 'rejected_histories': histories})
            print('일반 제보 상태 저장: ' + str(args.output))
        elif args.command in ('browser-status','browser-read','browser-plan'):
            from .browser import BrowserRuntime
            runtime = BrowserRuntime()
            if args.command == 'browser-status':
                print(json.dumps(runtime.status(),ensure_ascii=False,indent=2))
            else:
                result = runtime.read(args.url) if args.command == 'browser-read' else runtime.plan(args.url,args.goal)
                write_json(args.output,result)
                print('브라우저 조사 결과 저장: '+str(args.output))
        elif args.command == 'parallel-search':
            from .parallel import ParallelClient
            from .secrets import environment
            result = ParallelClient(api_key=environment().get('PARALLEL_API_KEY')).search(args.query,max_results=args.limit)
            write_json(args.output,result)
            print('Parallel 검색 결과 저장: '+str(args.output))
        elif args.command == 'build-score':
            from .submissions import build_submission
            source = read_json(args.input)
            write_json(args.output,build_submission(source['item'],source['offer'],source['event']))
        elif args.command == 'queue':
            from .queue import prioritize
            source = read_json(args.input)
            rows = source['candidates'] if isinstance(source,dict) else source
            write_json(args.output,prioritize(rows,remaining=args.remaining,release_deferred=args.release_deferred))
        elif args.command == 'score':
            from .client import SaveTaxClient
            from .submissions import ScoreClient
            body = read_json(args.input)
            key = 'score-'+hashlib.sha256(json.dumps(body,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            saved = read_json(args.receipt) if Path(args.receipt).exists() else None
            if saved and (saved.get('idempotency_key') != key or saved.get('body') != body):
                raise ValueError('다른 점수 제출의 영수증입니다. 새 경로를 사용하세요')
            if saved and saved.get('state') == 'submitted':
                try:
                    ScoreClient._require_receipt(saved.get('response'))
                except RuntimeError:
                    saved['state'] = 'sending'
                    write_json(args.receipt,saved)
                else:
                    print('이미 점수 접수한 영수증을 보존합니다: '+str(args.receipt))
                    return 0
            minimum = Decimal(args.min_saving)
            if not minimum.is_finite() or minimum < 0:
                raise ValueError('min-saving은 0 이상의 원화 금액이어야 합니다')
            client = SaveTaxClient(guide_path=args.guide)
            scoring = ScoreClient(client)
            receipt = saved or {'idempotency_key':key,'body':body,'state':'prepared'}
            if receipt['state'] == 'sending':
                recovery = scoring.recover_request(key)
                if recovery['state'] == 'submitted':
                    receipt['response'] = recovery['response']
                    receipt['state'] = 'submitted'
                    write_json(args.receipt,receipt)
                    return 0
                if recovery['state'] == 'pending':
                    print('점수 접수가 아직 확정되지 않았습니다. 같은 영수증을 유지합니다')
                    return 0
                if recovery['state'] != 'not_found':
                    raise ValueError('접수 조회 상태를 확인할 수 없습니다')
            preview = scoring.preview(body)
            receipt.update(preview=preview,state='previewed')
            write_json(args.receipt,receipt)
            if preview.get('ok') is not True or preview.get('next_action') != 'submit':
                raise ValueError('점수 preview가 신규 제출을 허용하지 않았습니다')
            amount_raw = preview.get('total_amount_krw')
            if not isinstance(amount_raw,str):
                raise ValueError('점수 preview 금액은 십진 문자열이어야 합니다')
            amount = Decimal(amount_raw)
            if not amount.is_finite() or amount < 0:
                raise ValueError('점수 preview 금액은 유한한 0 이상의 원화여야 합니다')
            if amount < minimum:
                receipt['state'] = 'deferred_lower_amount'
                write_json(args.receipt,receipt)
                print(f'후순위 대기: 예상 {amount:,.0f}원, 우선 기준 {minimum:,.0f}원')
                return 0
            print(f'점수 preview 예상액 {amount:,.0f}원')
            if args.send:
                receipt['state'] = 'sending'
                write_json(args.receipt,receipt)
                receipt['response'] = scoring.submit(body,key,preview)
                receipt['state'] = 'submitted'
                write_json(args.receipt,receipt)
                print('점수 제출 결과: '+json.dumps(receipt['response'],ensure_ascii=False))
    except RuntimeError as exc:
        # SaveTax/market transports expose only sanitized errors.
        print(str(exc), file=sys.stderr)
        return 2
    except InvalidOperation:
        print('원화 금액 형식이 잘못되었습니다', file=sys.stderr)
        return 2
    except (ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0
