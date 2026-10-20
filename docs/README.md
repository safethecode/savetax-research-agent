# 문서 색인

## 현재 구조와 로컬 조사 전환

[로컬 조사·Codex 근거 리뷰 아키텍처](superpowers/specs/2026-10-20-local-research-codex-review-design.md)가 새 구조의 정본이다. `qwen3.5:9b` 조사, Jev·Parallel API, Python 계산, Codex 리뷰와 접수 경계를 다룬다. **검토용 설계이며 실행기 구현 완료를 뜻하지 않는다.**

| 읽을 내용 | 위치 |
|---|---|
| 현재 구현과 설계의 차이 | [2절](superpowers/specs/2026-10-20-local-research-codex-review-design.md#2-현재-확인한-상태) |
| 역할·의존 방향·아키텍처 그림 | [4절](superpowers/specs/2026-10-20-local-research-codex-review-design.md#4-책임과-의존-방향) |
| 목표 파일 트리와 현재 모듈 대응표 | [5절](superpowers/specs/2026-10-20-local-research-codex-review-design.md#5-목표-파일-구조와-이전-대응표) |
| 실행 데이터·정책·비밀의 저장 위치 | [6절](superpowers/specs/2026-10-20-local-research-codex-review-design.md#6-실행-설정과-데이터-경계) |
| 근거 묶음·모델 제안·리뷰 계약 | [7절](superpowers/specs/2026-10-20-local-research-codex-review-design.md#7-입력출력-계약) |
| 재개·리뷰·접수·멱등 복구 | [8절](superpowers/specs/2026-10-20-local-research-codex-review-design.md#8-상태재시도리뷰제출) |
| 단계별 이전과 검증·커밋 경계 | [10절](superpowers/specs/2026-10-20-local-research-codex-review-design.md#10-단계별-이전과-검증-기준) |

## 지금 실행할 수 있는 기능

- [CLI 사용법](usage.md): 설치·후보 선별·증거 평가·점수·영수증·대기열.
- [Browser Harness·Jev](integrations/browser.md): 별도 런타임·세션·관측과 한계.
- [Parallel 검색](integrations/parallel.md): Search API 계약·출처·오류.
- [상품검색 MCP](integrations/market-mcp.md): 연결별 과거 검증 결과와 차이.
- [규격서 추출](integrations/documents.md): HWP/HWPX·추출·변경추적·미검증 상태.

연동 문서의 날짜가 적힌 성공·실패·가격·응답시간은 그 시점의 관측이다. 현재 연결 상태나 제품 가격의 확인을 대신하지 않는다.

## 파일 배치 원칙

현재 문서의 탐색 시작점은 이 색인과 루트 README다. 사용 명령은 `usage.md`, 서비스별 연결은 `integrations/`, 검토한 아키텍처와 과거 계획은 `superpowers/`에 둔다. 공개 조사 기록은 [research](../research/README.md), 원본 자료·실행 상태·개인 자료는 Git에서 제외한 `work/`에 둔다.

기존 `browser-research.md`, `document-reading.md`, `mcp-connections.md`, `parallel-search.md`는 옛 링크와 조사 스킬의 호환 경로다. 새 설명은 `integrations/`에서 관리한다. 기존 `.agents` 절차와 과거 공개 조사 파일을 이 문서 정리 때문에 이동하거나 다시 쓰지 않는다.

## 과거 설계

- [2026-10-16 초기 설계](superpowers/specs/2026-10-16-research-harness-design.md)
- [2026-10-16 초기 구현 계획](superpowers/plans/2026-10-16-research-harness.md)

두 문서는 작성 시점의 범위를 보존한다. 현재 구현·사용자 권한·최신 금액 정책은 해당 날짜의 문구만으로 결정하지 않는다.

- [로컬 Qwen 조사와 Codex 근거 리뷰 실행](local-research.md)
