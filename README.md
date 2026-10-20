# SaveTax 리서치 하네스

공식 조달 fact와 실제 판매 원문을 연결하고, 비교 근거·계산·제출 영수증을 보존하는 Python 도구다.

현재 사용자 지시·위임 범위와 [AGENTS.md](AGENTS.md)를 함께 확인해 조사 정책을 정한다. 대회 접수 예상액, 심사 인정액, 실제 예산 절감액은 구분한다.

## 시작할 곳

| 목적 | 문서 |
|---|---|
| 로컬 모델·외부 API·Codex 책임과 목표 폴더 구조 | [아키텍처 설계](docs/superpowers/specs/2026-10-20-local-research-codex-review-design.md) |
| 현재 구현된 CLI 명령 | [사용법](docs/usage.md) |
| 문서·연동·과거 설계 탐색 | [문서 색인](docs/README.md) |
| 공개 조사 결과와 기존 상태 원장 | [조사 기록](research/README.md) |

## 현재 구현과 다음 구조

| 담당 | 현재 상태 | 로컬 조사 전환 시 역할 |
|---|---|---|
| Python | 공식 API·Parquet·규칙·증거 입력·수치 계산·접수 복구 구현 | 계산·단계 실행·근거 보존·권한 경계 |
| Jev·Browser Harness | 별도 브라우저 런타임과 세션·작업 잠금 구현 | 공개 원문·실제 옵션 관측 |
| Parallel·판매 MCP | 검색 어댑터 구현 | 실제 판매처 후보 발견 |
| Ollama `qwen3.5:9b` | 제한된 조사 실행기·재개·출처 제안 구현 | 검색 계획·필드 추출·비교 제안·초안 |
| Codex | 고정 근거 리뷰·정확한 본문/정책 해시 gate 구현 | 고정한 원문·계산·최종 본문 리뷰 |

목표 의존 방향은 `CLI → application → domain + adapters + runtime`이다. 모델 제안, 실제 관측, 검토 승인과 공식 접수는 다른 상태로 보존한다. [로컬 조사 실행법](docs/local-research.md)과 [설계](docs/superpowers/specs/2026-10-20-local-research-codex-review-design.md)를 확인한다.

실행 가능한 로컬 예제와 Codex 리뷰는 [로컬 조사 사용법](docs/local-research.md)에 있다. `commands / application / domain / adapters / runtime`으로 구현을 분리했고 기존 평면 모듈은 import 호환 facade다.

## 설치와 검증

Python 3.11 이상을 사용한다. 브라우저는 [별도 런타임](docs/integrations/browser.md)을 사용한다.

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
python -m savetax --help
```

Windows의 `python`이 스토어 연결용 실행 파일이면 실제 설치된 Python의 절대 경로를 사용한다. HWP 선택 의존성은 [문서 추출](docs/integrations/documents.md)에 설명했다.

## 저장 위치

| 위치 | 보관 내용 |
|---|---|
| `savetax/`, `tests/`, `scripts/`, `strategies/` | 실행 코드·검증·선별 규칙 |
| `docs/` | 사용법·연동·현재 설계·과거 변경 기록 |
| `research/` | 검토한 공개 조사 기록·공개 상태 요약 |
| `work/` | Git 제외: 데이터·원문·브라우저·실행 상태·원본 영수증 |
| 개인 가이드·`.env*` | Git 제외: 지침과 자격증명 |

기존 조사 파일·영수증·브라우저 세션 경로는 유지한다. 새 실행의 폴더 계약은 [설계 6절](docs/superpowers/specs/2026-10-20-local-research-codex-review-design.md#6-실행-설정과-데이터-경계)에 있다. 자동 실행 예약은 이 저장소 정리로 생성하지 않는다.
