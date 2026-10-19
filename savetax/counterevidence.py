"""사용자가 위임한 공개 반증만 접수하고 멱등 키로 결과를 복구한다."""
from __future__ import annotations

import json
import re

import requests

from .client import SaveTaxClient, SaveTaxError, TOKEN_PATTERN, _redact


BASE = 'https://hackathon.savetax.now/v1/events/current'


def _identifier(value):
    if (not isinstance(value, str)
            or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}', value)
            or TOKEN_PATTERN.search(value)):
        raise ValueError('유효한 제출 ID가 필요합니다')
    return value


def _key(value):
    if (not isinstance(value, str)
            or not re.fullmatch(r'[A-Za-z0-9_-]{8,100}', value)
            or TOKEN_PATTERN.search(value)):
        raise ValueError('안정된 멱등 키가 필요합니다')
    return value


def validate_counterevidence(body):
    if (not isinstance(body, dict)
            or set(body) != {'revision_no', 'body', 'evidence_refs'}):
        raise ValueError('반증은 revision_no, body, evidence_refs만 사용합니다')
    if type(body['revision_no']) is not int or body['revision_no'] < 1:
        raise ValueError('반증 대상 revision은 양의 정수여야 합니다')
    text = body['body']
    if (not isinstance(text, str) or not text.strip() or len(text) > 4000
            or TOKEN_PATTERN.search(text)):
        raise ValueError('반증 본문은 비밀 없는 4000자 이하 문자열이어야 합니다')
    refs = body['evidence_refs']
    if (not isinstance(refs, list) or len(refs) > 8
            or any(not isinstance(ref, str)
                   or not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', ref)
                   for ref in refs)
            or len({ref.lower() for ref in refs}) != len(refs)):
        raise ValueError('반증 첨부는 중복 없는 자산 UUID 최대 8개입니다. 출처 URL은 본문에 적습니다')
    return {'revision_no': body['revision_no'], 'body': text, 'evidence_refs': list(refs)}


class CounterevidenceClient:
    def __init__(self, client: SaveTaxClient):
        self.client = client

    @staticmethod
    def _receipt(value):
        if (not isinstance(value, dict)
                or not isinstance(value.get('counterevidence_id'), str)
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}', value['counterevidence_id'])
                or TOKEN_PATTERN.search(value['counterevidence_id'])):
            raise SaveTaxError('반증 영수증 미확인; 같은 멱등 키로 결과를 확인하세요', stage='decode')
        return value

    def recover_request(self, idempotency_key):
        key = _key(idempotency_key)
        try:
            response = self.client._get(BASE + '/submission-requests/' + key)
        except SaveTaxError as error:
            if error.status == 404:
                return {'state': 'not_found'}
            raise
        try:
            if response.status_code == 202:
                return {'state': 'pending'}
            if response.status_code != 200:
                raise SaveTaxError('반증 접수 결과 상태 미확인', status=response.status_code, stage='http')
            try:
                result = self._receipt(response.json())
            except (ValueError, TypeError):
                raise SaveTaxError('반증 접수 결과 해석 실패', stage='decode') from None
            return {'state': 'submitted', 'response': _redact(result, self.client._token)}
        finally:
            response.close()

    def submit(self, submission_id, body, idempotency_key):
        sid, key = _identifier(submission_id), _key(idempotency_key)
        body = validate_counterevidence(body)
        payload = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        try:
            response = requests.post(BASE + '/submissions/' + sid + '/counterevidence',
                data=payload,
                headers={'Authorization': 'Bearer ' + self.client._token,
                         'Idempotency-Key': key, 'Content-Type': 'application/json',
                         'Accept': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                timeout=self.client.timeout, allow_redirects=False)
        except requests.RequestException:
            raise SaveTaxError('반증 연결 결과 미확인; 같은 멱등 키로 결과를 확인하세요', stage='transport') from None
        try:
            try:
                result = response.json()
            except (ValueError, TypeError):
                result = None
            if response.status_code not in (200, 201):
                detail = result.get('error', result) if isinstance(result, dict) else {}
                code = detail.get('code') if isinstance(detail, dict) else None
                if (not isinstance(code, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}', code)
                        or TOKEN_PATTERN.search(code)):
                    code = 'http_error'
                retry = response.headers.get('Retry-After', '')
                retry_after = int(retry) if retry.isdecimal() and len(retry) <= 8 else None
                raise SaveTaxError(f'반증 요청 HTTP {response.status_code} ({code})',
                    status=response.status_code, code=code, stage='http', retry_after=retry_after)
            return _redact(self._receipt(result), self.client._token)
        finally:
            response.close()
