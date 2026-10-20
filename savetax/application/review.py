"""Immutable evidence packages and a brokered, exact-body review gate.

The broker receipt prevents accidental/model-created approval dictionaries from
being accepted. It is a workflow control, not authentication against the OS user.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR, localcontext
import hashlib
from importlib.resources import files
import json
from pathlib import Path
import re
import shutil
import tempfile
import uuid

from jsonschema import Draft202012Validator, ValidationError

from ..runtime.artifacts import atomic_json, canonical_hash, exclusive_lock, safe_path

_ID = re.compile(r'[A-Za-z0-9_-]{1,100}\Z')
_HASH = re.compile(r'[a-f0-9]{64}\Z')
_REQUIRED = {'model', 'unit_price', 'vat_included', 'shipping_included',
             'pack_quantity', 'unit', 'new', 'purchase_available', 'complete_product'}
_MAX_JSON = 8 * 1024 * 1024
_MAX_SOURCE = 16 * 1024 * 1024
_MAX_TOTAL_SOURCE = 64 * 1024 * 1024


def decision_schema():
    """Return the same packaged schema used by the adapter and the broker."""
    return json.loads(files('savetax').joinpath('schemas/review-decision-v1.json').read_text(encoding='utf-8'))


def validate_decision(value):
    try:
        Draft202012Validator(decision_schema()).validate(value)
    except ValidationError:
        raise ValueError('리뷰 응답이 review-decision-v1 계약과 다릅니다') from None
    if value['decision'] == 'approved' and value['blocking']:
        raise ValueError('blocking 항목이 남은 리뷰는 승인할 수 없습니다')


def _read_json(path):
    try:
        raw = Path(path).read_bytes()
        if len(raw) > _MAX_JSON:
            raise ValueError()
        value = json.loads(raw.decode('utf-8'), parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        # Revalidate encodability, finiteness, and supported JSON types.
        canonical_hash(value)
        return value
    except (OSError, UnicodeError, ValueError, TypeError):
        raise ValueError('근거 또는 리뷰 JSON 파일을 확인할 수 없습니다') from None


def _text(data):
    try:
        text = data.decode('utf-8-sig')
    except UnicodeError:
        return ''
    try:
        value = json.loads(text)
    except ValueError:
        return text
    strings = []
    def collect(value):
        if isinstance(value, str):
            strings.append(value)
        elif isinstance(value, dict):
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect(value)
    return text + '\n' + '\n'.join(strings)


def _quote_exists(quote, source):
    return (isinstance(quote, str) and bool(quote.strip()) and
            (quote in source or ' '.join(quote.split()) in ' '.join(source.split())))


def _decimal(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', value):
        raise ValueError('금액·수량은 유한한 0 이상 Decimal 문자열이어야 합니다')
    try:
        number = Decimal(value)
    except InvalidOperation:
        raise ValueError('잘못된 Decimal 입력입니다') from None
    if not number.is_finite():
        raise ValueError('잘못된 Decimal 입력입니다')
    return number


def _validate_claims(proposal, source_text, *, has_body):
    if not isinstance(proposal, dict) or not isinstance(proposal.get('claims'), list):
        raise ValueError('출처가 있는 proposal.claims가 필요합니다')
    claims = {}
    for claim in proposal['claims']:
        if not isinstance(claim, dict) or not isinstance(claim.get('field'), str):
            raise ValueError('잘못된 claim입니다')
        field = claim['field']
        if field in claims or claim.get('status') not in {'observed', 'inferred', 'unknown', 'disputed'}:
            raise ValueError('중복 필드 또는 잘못된 claim 상태입니다')
        claims[field] = claim
        source = claim.get('source_id')
        if source is not None and has_body:
            if source not in source_text:
                raise ValueError('claim이 존재하지 않는 source를 참조합니다')
            if claim.get('quote') and not _quote_exists(claim['quote'], source_text[source]):
                raise ValueError('claim 인용이 실제 원천에 없습니다')
    if not has_body:
        return
    if proposal.get('unknowns') or proposal.get('comparison_kind') not in {'identical', 'equivalent'}:
        raise ValueError('미확인 항목이 남으면 본문은 null이어야 합니다')
    for field in _REQUIRED:
        claim = claims.get(field, {})
        if (claim.get('status') != 'observed' or claim.get('value') is None
                or claim.get('source_id') not in source_text or not claim.get('location')
                or not _quote_exists(claim.get('quote'), source_text.get(claim.get('source_id'), ''))):
            raise ValueError('필수 입력의 출처가 미확인인 본문은 승인 대상이 아닙니다')
    for field in ('vat_included', 'shipping_included'):
        if type(claims[field]['value']) is not bool:
            raise ValueError('세금·배송 포함 여부는 확인한 boolean이어야 합니다')
    for field in ('new', 'purchase_available', 'complete_product'):
        if claims[field]['value'] is not True:
            raise ValueError('신품·구매 가능·완제품 구성이 미확인입니다')
    # This first draft workflow supports included shipping and no installation.
    # A false flag is not a demonstrated zero-cost allowance.
    if claims['shipping_included']['value'] is not True:
        raise ValueError('배송비가 확인되지 않은 본문은 null이어야 합니다')
    if claims.get('installation_required', {}).get('value') is True:
        raise ValueError('필수 설치 비용의 독립 검증이 필요합니다')


def _scope(item, policy, body):
    facts = item.get('facts')
    if not isinstance(facts, list):
        raise ValueError('공식 fact snapshot이 필요합니다')
    ids = [fact.get('fact_id') for fact in facts if isinstance(fact, dict)]
    if len(ids) != len(facts) or any(not isinstance(fid, str) or not fid for fid in ids) or len(set(ids)) != len(ids):
        raise ValueError('공식 fact ID 누락 또는 중복입니다')
    returned = item.get('returned_count', len(facts))
    total = item.get('facts_total', len(facts))
    truncated = item.get('facts_truncated', False)
    if (type(returned) is not int or returned != len(facts) or type(total) is not int
            or total < returned or type(truncated) is not bool or (total > returned and not truncated)):
        raise ValueError('공식 fact 포괄 범위가 모순됩니다')
    adopted = [] if body is None else [line.get('fact_id') for line in body.get('lines', [])]
    scorable = {fact['fact_id'] for fact in facts if fact.get('scorable') is True}
    if len(set(adopted)) != len(adopted) or any(fid not in scorable for fid in adopted):
        raise ValueError('본문은 반환된 scorable fact만 중복 없이 참조해야 합니다')
    scope = policy.get('fact_scope')
    if truncated and body is not None:
        if (not isinstance(scope, dict) or scope.get('kind') != 'limited'
                or sorted(scope.get('fact_ids', [])) != sorted(adopted)
                or not isinstance(scope.get('reason'), str) or not scope['reason'].strip()):
            raise ValueError('절단된 fact에는 명시적인 제한 범위 정책이 필요합니다')
    return {'facts_total': total, 'returned_count': returned, 'facts_truncated': truncated,
            'returned_fact_ids': ids, 'adopted_fact_ids': adopted,
            'kind': 'limited' if truncated else 'returned',
            'reason': scope.get('reason') if isinstance(scope, dict) else None}


def _validate_calculation(item, calculation, body):
    if body is None:
        return
    if not isinstance(calculation, dict) or not isinstance(calculation.get('rows'), list):
        raise ValueError('Python의 fact별 계산이 필요합니다')
    facts = {fact['fact_id']: fact for fact in item['facts']}
    lines = {line['fact_id']: line for line in body['lines']}
    seen, positive = set(), set()
    total = Decimal(0)
    with localcontext() as context:
        context.prec = 100
        for row in calculation['rows']:
            fid = row.get('fact_id')
            if fid not in facts or fid in seen:
                raise ValueError('계산의 fact 참조가 잘못되었습니다')
            seen.add(fid)
            fact = facts[fid]
            c, q, b = (_decimal(row.get(name)) for name in ('C', 'Q', 'B'))
            if (c != _decimal(fact.get('comparable_amount_krw'))
                    or q != _decimal(fact.get('quantity')) or q <= 0 or b <= 0):
                raise ValueError('계산의 C·Q가 공식 fact와 다릅니다')
            savings = max(c-b*q, Decimal(0)).to_integral_value(rounding=ROUND_FLOOR)
            if _decimal(row.get('savings_krw')) != savings:
                raise ValueError('fact별 계산 결과가 산식과 다릅니다')
            total += savings
            if savings > 0:
                positive.add(fid)
            if fid in lines:
                line = lines[fid]
                if (_decimal(line.get('benchmark_unit_price_krw')) != b
                        or line.get('comparison_basis_id') != fact.get('basis_id')
                        or line.get('unit') != fact.get('unit')
                        or line.get('tax_basis') != fact.get('tax_basis')):
                    raise ValueError('본문의 비교 기준 또는 단가가 검토 계산과 다릅니다')
        if positive != set(lines) or total != _decimal(calculation.get('total_savings_krw')):
            raise ValueError('계산 합계와 제출 fact 범위가 다릅니다')


def _validate_content(manifest, source_text):
    body = manifest['body']
    _validate_claims(manifest['proposal'], source_text, has_body=body is not None)
    expected_scope = _scope(manifest['item'], manifest['policy'], body)
    if manifest['official_scope'] != expected_scope:
        raise ValueError('검토된 공식 fact 범위가 다릅니다')
    if body is not None:
        if (body.get('canonical_product_id') != manifest['item'].get('item_id')
                or body.get('dataset_release_id') != manifest['event'].get('dataset_release_id')
                or body.get('ruleset_version') != manifest['event'].get('ruleset_version')
                or not body.get('lines')):
            raise ValueError('본문의 물품·데이터·규칙·fact 범위가 다릅니다')
        retailer = {source['url']: source_text[source['source_id']]
                    for source in manifest['sources'] if source['kind'] == 'retailer'}
        for line in body['lines']:
            evidence = line.get('price_evidence')
            if not isinstance(evidence, list) or not evidence:
                raise ValueError('각 제출 fact에 실제 판매 근거가 필요합니다')
            for entry in evidence:
                if not _quote_exists(entry.get('quote'), retailer.get(entry.get('source_url'), '')):
                    raise ValueError('본문 가격 인용은 실제 판매 원천에 있어야 합니다')
    _validate_calculation(manifest['item'], manifest['calculation'], body)


def create_package(destination, *, item, event, policy, proposal, sources, calculation, body):
    """Copy allowed job sources, validate references, and freeze a hash-addressed package."""
    destination = Path(destination).absolute()
    allowed_root = destination.parent.resolve()
    if destination.exists() and destination.resolve() != destination:
        raise ValueError('package 저장 경로의 symlink는 허용하지 않습니다')
    records, blobs, texts, total_bytes = [], {}, {}, 0
    if not isinstance(sources, list) or len(sources) > 64:
        raise ValueError('source는 64개 이하의 목록이어야 합니다')
    for source in sources:
        sid = source.get('source_id')
        if not isinstance(sid, str) or not _ID.fullmatch(sid) or sid in texts:
            raise ValueError('잘못되거나 중복된 source_id입니다')
        path = Path(source.get('path', ''))
        try:
            path = path.resolve(strict=True)
            path.relative_to(allowed_root)
            if not path.is_file() or path.stat().st_size > _MAX_SOURCE:
                raise ValueError()
            raw = path.read_bytes()
        except (ValueError, OSError):
            raise ValueError('source는 현재 작업 안의 허용된 원천 파일이어야 합니다') from None
        total_bytes += len(raw)
        if len(raw) > _MAX_SOURCE or total_bytes > _MAX_TOTAL_SOURCE:
            raise ValueError('원천 파일 크기 한도 초과입니다')
        if source.get('kind') not in {'retailer', 'manufacturer', 'search', 'official', 'document'}:
            raise ValueError('source 종류를 확인하세요')
        extension = path.suffix if re.fullmatch(r'\.[A-Za-z0-9]{1,10}', path.suffix) else '.bin'
        relative = f'sources/{sid}{extension}'
        record = {key: deepcopy(source.get(key)) for key in
                  ('source_id', 'url', 'kind', 'observed_at', 'truncated', 'method')}
        record.update({key: deepcopy(source[key]) for key in
                       ('requested_url', 'final_url', 'capture_limit', 'http_status', 'engine')
                       if key in source})
        record.update(path=relative, sha256=hashlib.sha256(raw).hexdigest(), byte_size=len(raw))
        if source.get('raw_path') is not None:
            try:
                raw_path = Path(source['raw_path']).resolve(strict=True)
                raw_path.relative_to(allowed_root)
                if not raw_path.is_file() or raw_path.stat().st_size > _MAX_SOURCE:
                    raise ValueError()
                original = raw_path.read_bytes()
            except (OSError, ValueError):
                raise ValueError('원본 capture는 현재 작업 안의 허용된 파일이어야 합니다') from None
            total_bytes += len(original)
            if len(original) > _MAX_SOURCE or total_bytes > _MAX_TOTAL_SOURCE:
                raise ValueError('원천 파일 크기 한도 초과입니다')
            raw_extension = raw_path.suffix if re.fullmatch(r'\.[A-Za-z0-9]{1,10}', raw_path.suffix) else '.bin'
            raw_relative = f'sources/{sid}.raw{raw_extension}'
            record.update(raw_path=raw_relative, raw_sha256=hashlib.sha256(original).hexdigest(),
                          raw_byte_size=len(original))
            blobs[raw_relative] = original
        records.append(record)
        blobs[relative] = raw
        texts[sid] = _text(raw)
    manifest = {'schema_version': '1', 'item': deepcopy(item), 'event': deepcopy(event),
                'policy': deepcopy(policy), 'proposal': deepcopy(proposal), 'sources': records,
                'calculation': deepcopy(calculation), 'body': deepcopy(body),
                'body_hash': canonical_hash(body) if body is not None else None,
                'policy_hash': canonical_hash(policy), 'official_scope': _scope(item, policy, body)}
    _validate_content(manifest, texts)
    manifest['package_hash'] = canonical_hash(manifest)
    package = destination / manifest['package_hash']
    if package.exists():
        _load_package(package)
        return package
    destination.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.package-', dir=destination))
    try:
        for relative, raw in blobs.items():
            target = safe_path(staging, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        atomic_json(staging / 'body.json', body)
        atomic_json(staging / 'manifest.json', manifest)
        staging.rename(package)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return package


def _load_package(package_dir):
    original = Path(package_dir).absolute()
    # safe_path checks lexical parents before resolve() can hide a link/junction.
    manifest_path = safe_path(original, 'manifest.json')
    package = original.resolve(strict=True)
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict) or manifest.get('schema_version') != '1':
        raise ValueError('지원하지 않는 evidence package입니다')
    expected = manifest.get('package_hash')
    content = {key: value for key, value in manifest.items() if key != 'package_hash'}
    if not isinstance(expected, str) or not _HASH.fullmatch(expected) or canonical_hash(content) != expected:
        raise ValueError('package manifest 해시가 다릅니다')
    if manifest.get('policy_hash') != canonical_hash(manifest['policy']):
        raise ValueError('policy 해시가 다릅니다')
    body = _read_json(safe_path(package, 'body.json'))
    if body != manifest.get('body') or manifest.get('body_hash') != (canonical_hash(body) if body is not None else None):
        raise ValueError('검토 본문 해시가 다릅니다')
    texts = {}
    for source in manifest.get('sources', []):
        path = safe_path(package, source['path'])
        try:
            raw = path.read_bytes()
        except OSError:
            raise ValueError('원천 파일을 확인할 수 없습니다') from None
        if len(raw) != source['byte_size'] or hashlib.sha256(raw).hexdigest() != source['sha256']:
            raise ValueError('원천 바이트 해시가 다릅니다')
        if source.get('raw_path') is not None:
            try:
                original = safe_path(package, source['raw_path']).read_bytes()
            except OSError:
                raise ValueError('원본 capture를 확인할 수 없습니다') from None
            if (len(original) != source['raw_byte_size']
                    or hashlib.sha256(original).hexdigest() != source['raw_sha256']):
                raise ValueError('원본 capture 바이트 해시가 다릅니다')
        if source['source_id'] in texts:
            raise ValueError('중복 source_id입니다')
        texts[source['source_id']] = _text(raw)
    _validate_content(manifest, texts)
    return package, manifest


def _execution_valid(execution, manifest, decision):
    if (not isinstance(execution, dict) or execution.get('kind') != 'codex-exec'
            or execution.get('provider') != 'openai' or execution.get('returncode') != 0
            or execution.get('package_sha256') != manifest['package_hash']
            or execution.get('decision_sha256') != canonical_hash(decision)
            or execution.get('metadata_source') not in {'jsonl', 'configured-execution'}
            or not execution.get('model') or not execution.get('thread_id')):
        raise ValueError('실제 Codex 실행 영수증이 필요합니다')


def review_package(package_dir, reviewer):
    """Run review, validate its response, and store a separate broker execution receipt."""
    package, manifest = _load_package(package_dir)
    decision = reviewer.review(package, deepcopy(manifest))
    validate_decision(decision)
    if decision['decision'] == 'approved' and manifest['body'] is None:
        raise ValueError('필수 입력이 없는 null 본문은 승인할 수 없습니다')
    execution = deepcopy(getattr(reviewer, 'last_execution', None))
    _execution_valid(execution, manifest, decision)
    known_sources = {source['source_id'] for source in manifest['sources']}
    if any(row['source_id'] not in known_sources for row in decision['source_assessments']):
        raise ValueError('리뷰가 존재하지 않는 원천을 참조합니다')
    identifier = uuid.uuid4().hex
    receipt_relative = f'reviews/executions/{identifier}.json'
    receipt_path = safe_path(package.parent, receipt_relative)
    bindings = {'package_hash': manifest['package_hash'], 'body_hash': manifest['body_hash'],
                'policy_hash': manifest['policy_hash'],
                'dataset_release_id': manifest['event'].get('dataset_release_id'),
                'ruleset_version': manifest['event'].get('ruleset_version'),
                'official_scope_hash': canonical_hash(manifest['official_scope'])}
    receipt = {'schema_version': '1', 'broker': 'savetax-review-v1',
               **bindings, 'execution': execution, 'decision': decision}
    atomic_json(receipt_path, receipt)
    record = {'schema_version': '1', 'broker': 'savetax-review-v1', **bindings, **decision,
              'reviewed_at': datetime.now(timezone.utc).isoformat(),
              'execution_receipt': receipt_relative, 'execution_receipt_hash': canonical_hash(receipt)}
    review_path = safe_path(package.parent, f'reviews/{identifier}.json')
    atomic_json(review_path, record)
    # Update only the owning job's currently selected immutable package. A review
    # finishing after an explicit retry must not overwrite the replacement job.
    job_dir = package.parent.parent
    job_path = safe_path(job_dir, 'job.json')
    if job_path.exists():
        lock = (job_dir.parent.parent / '.run.lock' if job_dir.parent.name == 'jobs'
                else job_dir / '.review-job.lock')
        with exclusive_lock(lock):
            state = _read_json(job_path)
            selected = state.get('package_dir') if isinstance(state, dict) else None
            if isinstance(selected, str) and Path(selected).resolve() == package:
                state.update(state=decision['decision'], review_path=str(review_path.resolve()),
                             reviewed_at=record['reviewed_at'])
                atomic_json(job_path, state)
    return review_path


def require_approved(body, package_dir, review_path, *, operation='submit'):
    """Validate a brokered review, exact inputs, all sources and the delegated operation."""
    package, manifest = _load_package(package_dir)
    if operation not in {'submit', 'revise'}:
        raise ValueError('지원하지 않는 출판 작업입니다')
    if manifest['policy'].get('allow_' + operation) is not True:
        raise ValueError('현재 고정 정책에 해당 작업의 위임이 없습니다')
    if body is None or canonical_hash(body) != manifest['body_hash'] or body != manifest['body']:
        raise ValueError('본문이 Codex 검토본과 다릅니다')
    try:
        review_path = Path(review_path).resolve(strict=True)
        relative = review_path.relative_to(package.parent)
    except (ValueError, OSError):
        raise ValueError('리뷰는 package collection 내부의 broker 파일이어야 합니다') from None
    record = _read_json(safe_path(package.parent, relative.as_posix()))
    if not isinstance(record, dict) or record.get('broker') != 'savetax-review-v1':
        raise ValueError('broker가 생성한 Codex 리뷰가 필요합니다')
    receipt = _read_json(safe_path(package.parent, record.get('execution_receipt', '')))
    if (record.get('execution_receipt_hash') != canonical_hash(receipt)
            or receipt.get('broker') != 'savetax-review-v1'):
        raise ValueError('리뷰 실행 영수증이 다릅니다')
    decision = receipt.get('decision')
    validate_decision(decision)
    if decision['decision'] != 'approved' or any(record.get(k) != v for k, v in decision.items()):
        raise ValueError('현재 근거 묶음은 승인되지 않았습니다')
    expected = {'package_hash': manifest['package_hash'], 'body_hash': manifest['body_hash'],
                'policy_hash': manifest['policy_hash'],
                'dataset_release_id': manifest['event'].get('dataset_release_id'),
                'ruleset_version': manifest['event'].get('ruleset_version'),
                'official_scope_hash': canonical_hash(manifest['official_scope'])}
    if any(record.get(k) != value or receipt.get(k) != value for k, value in expected.items()):
        raise ValueError('리뷰와 근거·본문·정책·공식 fact 범위가 다릅니다')
    _execution_valid(receipt.get('execution'), manifest, decision)
    return record
