# SaveTax Research Harness Implementation Plan

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans. 사용자가 병렬 구현과 조사, 커밋·푸시를 요청했다.

**Goal:** 조달 원본과 국내 판매가를 연결하는 재현 가능한 조사 도구를 만들고 실제 후보를 검증한다.

**Architecture:** GET 전용 클라이언트, DuckDB 표본 탐색, JSON DSL과 증거 평가를 Python CLI로 연결한다. 원본·인증은 로컬에 남기고 분석과 코드만 공개한다.

**Tech Stack:** Python 3.11+, requests, DuckDB, unittest.

**Spec:** `docs/superpowers/specs/2026-10-16-research-harness-design.md`

## Global Constraints

- 목표는 60,000,000,000원. 실현액과 추정액을 구별한다.
- 토큰은 허용된 HTTPS Authorization에만 사용한다.
- 원본 ZIP·Parquet와 개인 인증 지침은 재배포하지 않는다.
- 국내 우선, 모델·단위·VAT·설치·배송 조건을 확인한다.
- 외부 등록·제보는 실행하지 않는다.

## Review Focus

- 같은 납품요구를 공유하는 등재는 중복 합산하지 않는다.
- 모델·팩수량·배송 조건이 빠진 가격은 검증 완료로 처리하지 않는다.
- 납품요구 금액을 지급 완료 금액으로 설명하지 않는다.
- 서버 장애와 DNS·TCP/TLS·HTTP 실패를 구분한다.
- 재실행 때 완료 묶음과 후보를 조용히 건너뛰지 않는다.

## Task 1: API와 데이터 취득

- [ ] `tests/test_client.py`에 허용 URL·redirect·비밀 비노출 실패 테스트 작성 및 실행.
- [ ] `savetax/client.py`의 `SaveTaxClient.get_json`, `download_dataset` 구현.
- [ ] 네트워크 없는 테스트와 실제 인증 GET·ZIP 다운로드 확인.
- [ ] 인증 파일 추적 제외와 클라이언트를 커밋.

## Task 2: DSL·증거 평가

- [ ] `tests/test_rules.py`, `tests/test_evidence.py`에 코드 주입·결측·중복·가격조건·산식 테스트 작성 및 실패 확인.
- [ ] `apply_rules`, `deterministic_batches`, `learn_from_feedback`, `evaluate_candidate` 구현.
- [ ] 테스트 통과 후 DSL·평가기를 별도 커밋.

## Task 3: Parquet 탐색·CLI

- [ ] `tests/test_analysis.py`, `tests/test_cli.py`에 작은 실제 Parquet와 재개 상태 테스트 작성 및 실패 확인.
- [ ] `analysis.py`의 물품별 dlv_key 중복 제거와 고정 묶음 탐색 구현.
- [ ] `cli.py`의 후보 수집·fact 조회·평가·상태 재개·한국어 보고서 구현.
- [ ] 실데이터 실행 결과 검증 후 커밋.

## Task 4: 국내 가격 조사·스킬·인계

- [ ] 실제 후보의 국내 판매 페이지를 직접 확인하고 미확인 조건을 기록.
- [ ] 실제 조사에 필요한 스킬을 `.agents/skills`에 작성하고 사례 검증.
- [ ] 전체 unittest, CLI 실행, secret·raw artifact 점검.
- [ ] 결과·README 커밋 후 원격 푸시와 HEAD 일치 확인.
