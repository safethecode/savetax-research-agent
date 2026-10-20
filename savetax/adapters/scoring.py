"""Official score transport and optimistic revisions with mandatory review."""
import json
import re

import requests

from .catalog import SaveTaxClient, SaveTaxError, TOKEN_PATTERN, _redact
from ..domain.evidence import is_procurement_price_url
from ..application.publication import require_publication_approval

BASE = 'https://hackathon.savetax.now/v1/events/current'


class ScoreClient:
    def __init__(self, client: SaveTaxClient):
        self.client = client

    @staticmethod
    def _validate_key(key):
        if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,100}',key):
            raise ValueError('안정된 멱등 키가 필요합니다')

    @staticmethod
    def _require_receipt(result):
        submission_id = result.get('submission_id') if isinstance(result,dict) else None
        if (not isinstance(submission_id,str)
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',submission_id)
                or TOKEN_PATTERN.search(submission_id)):
            raise SaveTaxError('점수 접수 영수증 미확인; 같은 멱등 키로 결과를 확인하세요',stage='decode')
        return result

    def recover_request(self, idempotency_key):
        """HTTP 202는 접수 성공이 아니다. 같은 요청의 최종 결과만 복구한다."""
        self._validate_key(idempotency_key)
        try:
            response = self.client._get(BASE+'/submission-requests/'+idempotency_key)
        except SaveTaxError as error:
            if error.status == 404:
                return {'state':'not_found'}
            raise
        error, result = None, None
        try:
            if response.status_code == 202:
                return {'state':'pending'}
            if response.status_code != 200:
                error = SaveTaxError('점수 접수 결과 상태 미확인',status=response.status_code,stage='http')
            else:
                try:
                    result = self._require_receipt(response.json())
                except (ValueError,TypeError):
                    error = SaveTaxError('점수 접수 결과 해석 실패',stage='decode')
        finally:
            response.close()
        if error:
            raise error from None
        return {'state':'submitted','response':_redact(result,self.client._token)}

    def _post(self, suffix, body, key=None, *, revision=None, package_dir=None, review_path=None):
        is_revision = bool(re.fullmatch(r'/submissions/[A-Za-z0-9_-]{1,200}/revisions', suffix)) and not TOKEN_PATTERN.search(suffix)
        if suffix not in ('/submissions/preview','/submissions') and not is_revision:
            raise ValueError('허용되지 않은 점수 경로')
        if is_revision:
            if isinstance(revision, bool) or not isinstance(revision, int) or revision < 1:
                raise ValueError('현재 revision은 양의 정수여야 합니다')
            self._validate_key(key)
        elif revision is not None:
            raise ValueError('수정 요청에만 If-Match를 보낼 수 있습니다')
        if any(is_procurement_price_url(evidence.get('source_url'))
               for line in body.get('lines', [])
               for evidence in line.get('price_evidence', [])):
            raise ValueError('공공조달 견적은 시중 판매가격 근거로 사용할 수 없습니다')
        serialized = json.dumps(body,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        if TOKEN_PATTERN.search(serialized):
            raise ValueError('본문에 비밀 문자열을 넣을 수 없습니다')
        payload = serialized.encode('utf-8')
        if len(payload) > 1048576:
            raise ValueError('점수 전송 본문 1MiB 초과; 명시적 fact 범위 분리가 필요합니다')
        headers = {'Authorization':'Bearer '+self.client._token,'User-Agent':'Mozilla/5.0',
                   'Accept':'application/json','Content-Type':'application/json'}
        if key is not None:
            self._validate_key(key)
            headers['Idempotency-Key'] = key
        elif suffix == '/submissions':
            self._validate_key(key)
        if is_revision:
            headers['If-Match'] = str(revision)
        if suffix == '/submissions' or is_revision:
            # Validate the exact JSON snapshot encoded in payload, even if the
            # caller's mutable body changed after its earlier availability GET.
            require_publication_approval(json.loads(serialized), package_dir, review_path,
                                         operation='revise' if is_revision else 'submit')
        response,error = None,None
        try:
            response = requests.post(BASE+suffix,data=payload,headers=headers,
                timeout=self.client.timeout,allow_redirects=False)
        except requests.RequestException:
            error = SaveTaxError('점수 요청 연결 결과 미확인; 같은 멱등 키로 결과를 확인하세요',stage='transport')
        if error:
            raise error from None
        try:
            try:
                result = response.json()
            except (ValueError,TypeError):
                result = None
            if response.status_code not in (200,201):
                detail = result.get('error',result) if isinstance(result,dict) else {}
                code = detail.get('code','http_error') if isinstance(detail,dict) else 'http_error'
                if not isinstance(code,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}',code) or TOKEN_PATTERN.search(code):
                    code = 'http_error'
                error = SaveTaxError(f'점수 요청 HTTP {response.status_code} ({code})',status=response.status_code,code=code,stage='http')
            elif not isinstance(result,dict):
                error = SaveTaxError('점수 요청 응답 해석 실패; 같은 멱등 키로 결과를 확인하세요',stage='decode')
            elif suffix == '/submissions' or is_revision:
                self._require_receipt(result)
        finally:
            response.close()
        if error:
            raise error from None
        return _redact(result,self.client._token)

    def preview(self, body):
        return self._post('/submissions/preview',body)

    def submit(self, body, idempotency_key, preview, *, package_dir=None, review_path=None):
        self._validate_key(idempotency_key)
        if not isinstance(preview,dict) or preview.get('ok') is not True or preview.get('next_action') != 'submit':
            raise ValueError('점수 제출 가능한 preview 결과가 필요합니다')
        require_publication_approval(body, package_dir, review_path)
        lookup = self.client.get_json(BASE+'/items/lookup',params={'ids':body['canonical_product_id']})
        rows = lookup.get('items',[])
        matching = [row for row in rows if isinstance(row,dict)
                    and row.get('item_id') == body['canonical_product_id']] if isinstance(rows,list) else []
        if len(matching) != 1 or matching[0].get('state') != 'available':
            raise ValueError('물품이 이미 등록되었거나 현재 등록할 수 없습니다')
        return self._post('/submissions',body,idempotency_key,
                          package_dir=package_dir, review_path=review_path)

    def revise(self, submission_id, body, idempotency_key, preview, *, package_dir=None, review_path=None):
        """Revise an existing owned submission using its preview revision.

        The server's If-Match check protects against a change after preview.
        This method never creates a claim or withdraws the existing submission.
        """
        self._validate_key(idempotency_key)
        if (not isinstance(submission_id, str)
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}', submission_id)
                or TOKEN_PATTERN.search(submission_id)):
            raise ValueError('유효한 제출 ID가 필요합니다')
        if (not isinstance(preview, dict) or preview.get('ok') is not True
                or preview.get('next_action') != 'revise_existing'
                or preview.get('claimed_by_me') is not True
                or preview.get('existing_submission_id') != submission_id
                or preview.get('existing_submission_state') != 'accepted'):
            raise ValueError('본인 제출의 수정 가능한 preview 결과가 필요합니다')
        current_revision = preview.get('current_revision')
        require_publication_approval(body, package_dir, review_path, operation='revise')
        return self._post('/submissions/'+submission_id+'/revisions', body,
                          idempotency_key, revision=current_revision,
                          package_dir=package_dir, review_path=review_path)
