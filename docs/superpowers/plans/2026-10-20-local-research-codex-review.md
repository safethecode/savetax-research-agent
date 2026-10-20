# 로컬 조사 실행기 구현 계획

승인된 설계: `../specs/2026-10-20-local-research-codex-review-design.md`.
사용자의 2026-10-20 «구현해야지» 지시에 따라 현재 세션에서 실행한다.

## 실행 단위

1. **runtime와 로컬 추론**: 안전한 상대경로·정규화 JSON 해시·원자적 저장·동시 실행 잠금, 명시적 로컬 프로필, loopback 전용 Ollama JSON 추론. 실패·timeout·응답 초과·잘못된 JSON을 먼저 테스트한다.
2. **고정 근거 묶음과 리뷰**: 원천 바이트를 복사하고 해시를 고정한 package, 정확한 body/policy 연결, Codex read-only subprocess와 JSON Schema 응답, tamper 및 blocking 검증. 스키마·프롬프트는 wheel에 포함되는 패키지 리소스로 둔다.
3. **조사 workflow**: 공식 snapshot 입력 또는 공식 GET, 제한된 search/read/finish 제안 루프, Parallel 발견과 Jev 관측 분리, 재개 시 입력·정책 일치 확인, 도구 예산과 실패 보존. 모델의 관측 제안은 승인 boolean으로 바꾸지 않는다.
4. **초안과 계산**: 기존 수동 builder의 검증과 순수 본문 조립을 분리한다. 새 draft는 명시적인 미검토 상태로만 생성하며 필수 원문·비용·모델·단위 입력이 없으면 body=null. 공식 fact별 C/Q와 관련 번호를 보존한다.
5. **공통 출판 gate**: ScoreClient.submit/revise와 CLI --send에 package/review 검증을 연결한다. 기존 영수증 재생과 불명확 POST의 동일 키 복구는 먼저 수행한다. 새 전송에는 새 gate가 필수다.
6. **검증·정리**: 의미 있는 경계 테스트, 전체 unittest 회귀, wheel 리소스 확인, 실제 qwen3.5:9b 추론 smoke, 독립 코드 리뷰. 실제 접수·예약 생성 없이 문서와 실행 예시를 갱신한다.

각 단위에서 RED를 확인하고 구현·GREEN 후 작은 명시적 파일 집합을 커밋·푸시한다. 기존 공개 조사 기록·원본 work 경로·영수증을 일괄 이동하지 않는다. 기존 모듈은 호환 진입점으로 보존하면서 새 코드의 의존 방향을 application → domain/adapters/runtime로 분리한다. 범용 셸 실행·자동 cloud fallback·모델 다운로드·자동 접수 daemon은 추가하지 않는다.

## 공유 인터페이스

- `runtime.artifacts`: `canonical_hash(value)`, `atomic_json(path,value)`, `safe_path(root,relative)`, `exclusive_lock(path)` context manager.
- `runtime.config.LocalProfile`: model/base_url/timeout/num_ctx/num_predict/think, `as_dict()`.
- `adapters.ollama.OllamaClient(profile).generate(prompt, schema) -> dict` (JSON 객체), `last_metadata` (실제 실행 메타데이터).
- `application.review.create_package(destination, *, item, event, policy, proposal, sources, calculation, body) -> Path`: sources에는 source_id/path/url/kind가 있으며 실제 파일을 package 내부로 복사한다.
- `application.review.review_package(package_dir, reviewer) -> Path`: reviewer는 `review(package_dir, manifest) -> dict`; broker가 실제 실행 receipt와 해시를 붙인다.
- `application.review.require_approved(body, package_dir, review_path) -> dict`: 원천·package·body·정책·규칙·fact 범위와 리뷰 결정을 재검증한다.
- `adapters.codex.CodexReviewer.review(package_dir, manifest) -> dict`: ordinary `codex exec`, read-only/ephemeral/output-schema, package를 신뢰할 수 없는 증거 데이터로 취급한다.

모델 응답은 제안이며 승인 권한을 갖지 않는다. 연구 CLI는 `research --input <snapshot.json> --policy <policy.json> --run-dir <dir>`와 `--item-id` 공식 조회 경로를 제공한다. 리뷰 CLI는 `review --package <dir>`다. `score --send`는 `--package`와 `--review`를 요구한다.

## 완료 기록 — 2026-10-20

- [x] runtime·로컬 추론, 실제 설치된 qwen3.5:9b 호출 확인
- [x] 제한된 search/read/finish 조사, 재개·원문 보존·fact 계산
- [x] 고정 근거 묶음·Codex stdin 원문 리뷰·공통 출판 gate
- [x] 기존 접수 영수증 재생·모호한 POST의 멱등 복구 유지
- [x] 12개 구현 모듈의 실제 계층 이동·이전 import 호환·의존 방향 검사
- [x] 257개 unittest 실행: 255통과, OS 권한으로 2생략
- [x] 별도 경로 wheel 설치와 포함 리소스 검사
- [x] 독립 리뷰의 두 P2(429 Retry-After, 후보별 조회 실패 격리) 재현·수정·재검증

현재 자동 초안 지원 범위와 실행 명령은 [로컬 조사 사용법](../../local-research.md)에 있다. 원문·계산·본문·정책을 바꾸면 새 리뷰가 필요하다. 검증 과정에서 대회 접수나 예약을 생성하지 않았다.
