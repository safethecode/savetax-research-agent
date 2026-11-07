# 판정 이의제기

기존 제출·비교 상품·가격을 고정하고 판정의 오독·계산 오류·규칙 적용을 보완한다. 새 상품·새 판매처·새 비교가격으로 교체하거나 실제 사양 열위를 부정하지 않는다. 마감 전에 공개된 같은 비교품의 문서를 확보하고, 현재 재열람 시각과 당시 공개 증거를 구분한다.

## 판정 읽기

현재 공식 [API](https://hackathon.savetax.now/docs/api.md), [rules](https://hackathon.savetax.now/docs/rules.md), 제출 상세 UI의 이의 안내를 확인한다. 아래 계약은 재사용 출발점이며 현재 응답이 우선한다.

`GET https://hackathon.savetax.now/v1/events/current/submissions/{sid}/verdict`

- 소유자 인증으로 `viewer_is_owner`, `appeal_open`, `appeals_remaining`, `appeal_deadline`, `report.report_id`를 확인한다. 기한은 현재 한국시간과 대조한다. 과거 원장에 남은 횟수가 있어도 마감이 지났으면 보내지 않는다.
- `lines_next_cursor`가 있으면 `lines_cursor`로 끝까지 읽어 `lines_total`과 고유 fact ID 수를 맞춘다. 이미 같은 report 전체가 저장됐으면 재사용하고 접수 직전에는 현재 report·창구만 확인한다.
- 판정 미공개·대상 밖·마감은 대기로 구분한다. `unresolved`를 불인정으로, 동결 상한을 인정액으로 바꾸지 않는다.

## 본문과 접수

한 본문은 **판정이 한 말 → 같은 원제출/비교품의 원문과 출처 → 오류·단위·조건 대조 → 남는 실제 차이 → 요청하는 정정** 순서로 쓴다. 부분 정정만 입증되면 그 범위만 요청한다. 감액/부분 인정 가능성은 공식 규칙과 구체 근거에 맞춰 설명하고 새 권리로 단정하지 않는다.

```text
POST https://hackathon.savetax.now/v1/events/current/submissions/{sid}/appeals
Authorization: Bearer <프로세스 메모리의 자격값>
Idempotency-Key: <저장한 동일 요청 키>
Content-Type: application/json

{"report_id":"현재 report_id","body":"최종 본문","evidence_refs":[]}
```

기존 API 계약은 본문 20~4000자, 첨부 최대 8개, 판정당 최대 2회였다. 실제 제한·잔여량은 현재 문서/응답으로 확인한다. 이의 endpoint에 revision의 If-Match를 가져오거나 존재하지 않는 appeal preview를 만들지 않는다. 초안 검토가 끝나고 접수가 위임됐으면 바로 접수한다. 리뷰가 같은 해시를 승인했다면 추가 리뷰를 쌓지 않는다.

전송 전에 sid·report_id·본문 해시·정확한 payload·멱등 키를 저장한다. 영수증을 받은 뒤 verdict GET의 `appeals`에서 appeal ID·본문·report_id·첨부 ID를 한 번 대조하고 완료로 기록한다. **접수 성공과 재심 인정은 별개**다.

불명확한 응답은 verdict의 `appeals`에서 기존 키/본문/판정에 해당하는 접수부터 찾는다. 저장 키는 보존한다. 공식 문서가 결과를 확정하지 못하면 불명확 상태로 남기고, 새 키나 점수 전용 `submission-requests`로 중복 이의를 보내지 않는다. `REPORT_VERSION_CHANGED`는 새 판정을 읽어 기존 초안의 적용 가능성부터 다시 확인한다.

## 첨부가 필요할 때

`POST /v1/events/current/uploads`로 파일명·MIME·크기를 예약하고, 공식 반환 upload URL에만 바이트를 전송한 뒤 `POST /v1/uploads/{asset_id}/complete`로 고정한다. 실제 파일 바이트와 완료 응답 SHA-256을 대조한다. 응답의 `sha256:` 접두사는 표현 형식이므로 제거한 hex끼리 비교한다.

완료한 파일은 수정하지 않는다. 로컬 표시 문서가 달라지면 별도로 저장하고 실제 접수본과 섞지 않는다. 누적 용량 제한에 걸리면 반복 업로드하지 말고 이미 고정한 근거를 재사용하거나 출처와 핵심 원문을 담은 작은 발췌로 준비한다. 전문·해시는 로컬 원본 묶음에 보존하며, 발췌와 전문을 구분해 표시한다.

원장에는 sid·report_id·appeal_id·본문 해시·실제 첨부 해시·접수 시각·남은 횟수·공식 확인 결과를 적는다. 동결 예상액, 현재 인정액, 확정 회복액, 실제 예산 절감액을 별도 필드로 둔다.
