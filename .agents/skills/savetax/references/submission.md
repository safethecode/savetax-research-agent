# 신규 접수·수정·복구

## 신규/수정

현재 공식 [API](https://hackathon.savetax.now/docs/api.md)·[schema](https://hackathon.savetax.now/docs/submission-schema.md)와 이벤트의 실제 기한·한도를 따른다. `events/current`의 RUNNING/open 문구만으로 접수 기간이 열렸다고 판단하지 않는다.

1. 기존 원장과 `items/lookup`을 확인한다. 신규 점수는 `available`만 사용하고 기등록품을 새 제출로 복제하지 않는다. `on_hold`는 `hold_until` 이후 다시 조회한다.
2. 원문·공식 fact·필수 비용·사양 대응을 반영한 본문을 완성한다. 계약·납품요구·라인 번호는 각 line의 `evidence_refs.fulfillment_evidence`에 넣는다. 줄마다 전체 fact ID가 반복되지 않아도 계약/request/line 성분이 모두 대응하면 된다.
3. 신규 접수·revision **직전마다** 로컬 개인 가이드 전체를 비밀 마스킹 후 읽는다. `savetax-agent-guide.md`가 없으면 기존 `guide.md`를 사용한다. 키와 지침을 외부 리뷰나 패키지에 복사하지 않는다.
4. 저장소 `score --send`와 `ScoreClient.submit/revise`는 고정 근거 묶음·본문·정책에 맞는 Codex 승인 파일이 필요하다. 이미 일치하는 승인 파일이 있으면 재사용한다. 실행은 [runtime.md](runtime.md)를 따른다. gate를 제거하거나 가짜 승인 JSON으로 우회하지 않는다.
5. 공식 preview에서 대상·범위·산식·현재 상태를 확인하고 위임된 접수를 진행한다. preview 통과를 가격 진위나 기술 동등성 인정으로 세지 않는다. 접수 전 멱등 키와 정확한 payload를 저장한다.
6. 영수증과 공식 GET에서 대상·본문·금액을 한 번 대조해 기록한다. 성공한 영수증을 덮어쓰거나 같은 건을 재접수하지 않는다.

revision은 기존 소유 제출에 대한 수정이다. `ScoreClient.revise(submission_id, body, idempotency_key, preview, package_dir=..., review_path=...)`를 사용한다. `revise_existing` preview의 current revision을 If-Match로 보내며 신규·철회로 우회하지 않는다. 판정에 대한 이의는 [appeals.md](appeals.md)의 별도 작업이다.

## 불명확한 점수 POST

네트워크 오류·202는 접수 성공으로 확정하지 않는다. 저장한 키로 `GET /v1/events/current/submission-requests/{idempotency_key}`를 조회한다. 기존 Python에서는 `ScoreClient(client).recover_request(idempotency_key)`다. 토큰을 코드에 직접 넣지 말고 기존 `SaveTaxClient`의 보호된 인증을 사용한다.

| 조회 상태 | 다음 행동 |
|---|---|
| 완료 | 영수증을 복구하고 기존 본문과 대조 |
| pending | 상태를 남기고 API 재시도 조건 이후 조회. 새 키 전송 금지 |
| not_found | 기록·대상 상태를 대조한 뒤, 아직 유효한 동일 요청만 같은 키로 재시도 |
| 401/403 | 인증 실패로 보존하고 반복 중단 |

접수/pending 복구를 위해 같은 근거를 다시 리뷰하지 않는다. 내용이 바뀌면 복구가 아니라 새 검토 작업이며, 이전 불명확 요청의 결과부터 정리한다. 이의제기 응답 복구는 이 점수 전용 endpoint를 쓰지 않는다.
