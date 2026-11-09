<h1 align="center">SaveTax</h1>

<p align="center">
  조달 가격 비교부터 근거 검토와 이의제기까지.
</p>

<p align="center">
  <a href=".agents/skills/savetax/SKILL.md">에이전트 스킬</a> ·
  <a href="docs/usage.md">CLI 사용법</a> ·
  <a href="docs/local-research.md">로컬 모델</a> ·
  <a href="docs/README.md">문서</a>
</p>

<p align="center">
  <img src="assets/hackathon-award.png" width="340" alt="나랏돈 50조 찾기 해커톤 8위 · 확정 발견금액 5,576,770,830원" />
</p>

SaveTax는 공식 조달 데이터와 실제 판매 원문을 대조하는 **에이전트 스킬과 Python 도구**입니다. 후보 조사, 가격·사양 비교, 근거 정리, 접수와 이의제기를 하나의 작업 흐름으로 연결합니다.

## 주요 기능

- **근거 중심 비교** — 실제 판매 모델·옵션·구성품을 확인하고, 동일품과 대체품의 차이를 기록합니다.
- **공식 데이터 계산** — 공식 fact의 납품금액·수량을 바탕으로 단위·포장 수량·세금 기준을 맞춰 비교합니다.
- **로컬 조사와 Codex 리뷰** — Ollama로 조사 제안을 만들고, 고정한 원문·계산·본문을 Codex가 검토합니다.
- **접수와 이의제기** — preview, 중복 확인, 멱등 키와 영수증을 통해 접수·수정·복구를 이어갑니다.

## 빠른 시작

### 에이전트 스킬

저장소를 Codex에서 열고 [`savetax`](.agents/skills/savetax/SKILL.md) 스킬을 호출합니다.

```text
$savetax 저장된 근거를 이어서 검토하고, 위임된 접수까지 진행해 줘.
$savetax 기존 판정의 이유를 읽고 이의제기를 보완해 줘.
```

스킬은 작업에 필요한 참고 문서만 읽습니다. 현재 채팅의 위임·범위와 [저장소 작업 지침](AGENTS.md)을 따르며, 같은 원문과 본문의 검토 결과는 재사용합니다.

다른 프로젝트에서도 사용하려면 `.agents/skills/savetax`를 개인 skills 경로에 연결하거나 복사합니다. 저장소의 스킬을 정본으로 관리합니다.

### Python CLI

**Python 3.11 이상**이 필요합니다.

```bash
git clone https://github.com/safethecode/savetax-research-agent.git
cd savetax-research-agent
python -m pip install -e .
python -m savetax --help
```

외부 연동을 사용할 때 해당 서비스의 인증을 설정합니다. 공식 API 인증은 `SAVETAX_TOKEN`, 검색·브라우저 설정은 [연동 문서](docs/README.md)를 참고합니다. 저장된 자료만 검토할 때는 모델이나 브라우저를 실행할 필요가 없습니다.

## 작업 흐름

`후보 조사 → 판매 원문 확인 → 공식 fact 계산 → 근거 묶음 → Codex 리뷰 → preview·접수`

| 구성 | 역할 |
|---|---|
| 에이전트 스킬 | 조사·접수·이의제기의 절차와 판단 기준 |
| 로컬 모델 · Ollama | 출처를 바탕으로 조사 제안과 초안 작성 |
| Python | 데이터 조회·계산·근거 보존·API 실행 |
| Codex | 원문·사양·계산·최종 본문 검토 |

새 점수 접수와 revision에는 현재 근거 묶음과 일치하는 Codex 승인이 필요합니다. 검색 결과, 실제 판매 관측, 예상 접수액, 심사 인정액, 실제 예산 절감액은 각각 구분해 기록합니다.

## 문서

| 문서 | 내용 |
|---|---|
| [스킬](.agents/skills/savetax/SKILL.md) | 일반 작업의 시작점 |
| [CLI 사용법](docs/usage.md) | 명령·입력 형식·가격 환산·접수 복구 |
| [로컬 모델 실행](docs/local-research.md) | Ollama 조사·근거 묶음·Codex 리뷰 |
| [브라우저 연동](docs/integrations/browser.md) | Browser Harness·Jev로 판매 원문 확인 |
| [검색 연동](docs/integrations/parallel.md) | Parallel 검색 |
| [상품 검색](docs/integrations/market-mcp.md) | 상품검색 MCP |
| [문서 추출](docs/integrations/documents.md) | HWP·HWPX 처리 |
| [접수·이의제기 기록](records/appeals-20261106.md) | 보완 내역과 결과 요약 |

## 프로젝트 구조

```text
.agents/skills/savetax/  스킬과 작업별 참고 문서
savetax/
  commands/             CLI 명령
  application/          조사·리뷰·접수 흐름
  domain/               계산과 규칙
  adapters/             API·검색·브라우저·모델 연동
  runtime/              설정·저장·잠금
config/                 로컬 실행 설정과 선별 정책
scripts/                보조 실행 도구
tests/                  회귀 테스트
docs/                   사용법과 연동 문서
records/                접수 원장과 결과 요약
assets/                 README 이미지
work/                   비공개 원문·데이터·영수증 · Git 제외
```

## 개발

```bash
python -m pip install -e .
python -m unittest discover -s tests
```

키·개인 지침·원본 자료·실행 로그는 Git에 포함하지 않습니다. 선별 기본값은 `config/policies/candidate-selection.json`에서 관리하며, `--strategy`로 별도 정책을 지정할 수 있습니다.
