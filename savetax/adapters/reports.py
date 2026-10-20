"""사용자가 위임한 일반 제보만 접수한다. 점수 등록·수정·철회는 없다."""
import re

import requests

from .catalog import SaveTaxClient, SaveTaxError, TOKEN_PATTERN, _redact
from ..domain.evidence import _source_valid

REPORTS_URL = 'https://hackathon.savetax.now/v1/events/current/reports'
LIMITS = {'product_id': 200, 'product_name': 500, 'reason': 4000,
          'category_name': 300, 'supplier_name': 500, 'contract_reference': 300,
          'source_url': 2048, 'details': 8000}


def validate_report(report):
    if not isinstance(report, dict) or set(report) - (set(LIMITS) | {'suspected_price_krw', 'evidence_refs'}):
        raise ValueError('일반 제보 허용 필드가 아닙니다')
    for key in ('product_id', 'product_name', 'reason', 'source_url'):
        if key not in report:
            raise ValueError('제보 필수 필드 누락: ' + key)
    for key, limit in LIMITS.items():
        if key in report:
            value = report[key]
            if not isinstance(value, str) or not value.strip() or len(value) > limit or TOKEN_PATTERN.search(value):
                raise ValueError('제보 필드 길이·형식 오류: ' + key)
    if len(report['reason']) < 20 or not _source_valid(report['source_url']):
        raise ValueError('구체적 사유와 공개 HTTPS 상품 페이지가 필요합니다')
    if report.get('evidence_refs') not in (None, []):
        raise ValueError('실전 제보에는 파일 첨부를 사용하지 않습니다')
    if 'suspected_price_krw' in report and (not isinstance(report['suspected_price_krw'], str)
            or not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?', report['suspected_price_krw'])):
        raise ValueError('단가는 소수 6자리 이하 십진 문자열이어야 합니다')
    return dict(report)


class ReportClient:
    def __init__(self, client: SaveTaxClient):
        self.client = client

    def submit(self, report, idempotency_key):
        body = validate_report(report)
        if not isinstance(idempotency_key, str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,100}', idempotency_key):
            raise ValueError('안정된 멱등 키가 필요합니다')
        response, error = None, None
        try:
            response = requests.post(REPORTS_URL, json=body,
                headers={'Authorization': 'Bearer ' + self.client._token,
                         'Idempotency-Key': idempotency_key, 'Accept': 'application/json',
                         'User-Agent': 'Mozilla/5.0'}, timeout=self.client.timeout, allow_redirects=False)
        except requests.RequestException:
            error = SaveTaxError('일반 제보 연결 결과 미확인; 같은 멱등 키로 접수 상태를 확인하세요', stage='transport')
        if error:
            raise error from None
        try:
            if response.status_code not in (200, 201):
                error = SaveTaxError(f'일반 제보 HTTP {response.status_code}', status=response.status_code, stage='http')
            else:
                try:
                    result = response.json()
                    if not isinstance(result, dict):
                        error = SaveTaxError('일반 제보 응답 형식 오류', stage='decode')
                except ValueError:
                    error = SaveTaxError('일반 제보 응답 해석 실패', stage='decode')
        finally:
            response.close()
        if error:
            raise error from None
        return _redact(result, self.client._token)

    def list_reports(self):
        return self.client.get_json(REPORTS_URL)

    def revise(self, current, report, idempotency_key):
        body = validate_report(report)
        report_id = current.get('report_id','')
        if (current.get('review_status') != 'submitted' or type(current.get('revision')) is not int
                or current['revision'] < 1 or not re.fullmatch(r'[0-9a-fA-F-]{36}',report_id)):
            raise ValueError('접수 대기 중인 제보의 현재 revision만 정정할 수 있습니다')
        if not isinstance(idempotency_key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,100}',idempotency_key):
            raise ValueError('정정 멱등 키가 필요합니다')
        error = None
        try:
            response = requests.patch(REPORTS_URL+'/'+report_id,json=body,
                headers={'Authorization':'Bearer '+self.client._token,'Idempotency-Key':idempotency_key,
                         'If-Match':str(current['revision']),'User-Agent':'Mozilla/5.0'},
                timeout=self.client.timeout,allow_redirects=False)
        except requests.RequestException:
            error = SaveTaxError('제보 정정 연결 결과 미확인',stage='transport')
        if error:
            raise error from None
        try:
            if response.status_code != 200:
                error = SaveTaxError(f'제보 정정 HTTP {response.status_code}',status=response.status_code,stage='http')
            else:
                try:
                    result = response.json()
                    if not isinstance(result,dict):
                        error = SaveTaxError('제보 정정 응답 형식 오류',stage='decode')
                except ValueError:
                    error = SaveTaxError('제보 정정 응답 해석 실패',stage='decode')
        finally:
            response.close()
        if error:
            raise error from None
        return _redact(result,self.client._token)
