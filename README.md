# SaveTax

SaveTax 조사·근거 비교·접수·이의제기를 실행하는 스킬과 보조 Python 도구다.

## 스킬로 사용

진입점은 [savetax 스킬](.agents/skills/savetax/SKILL.md) 하나다.

```text
$savetax 저장된 근거를 이어서 검토하고, 위임된 접수까지 진행해 줘.
$savetax 기존 판정의 이유를 읽고 이의제기를 보완해 줘.
```

현재 채팅의 위임·범위와 [AGENTS.md](AGENTS.md)를 따른다. 스킬은 조사/접수/이의/브라우저/도구 실행 중 필요한 참고 문서만 읽는다. 같은 원문·본문·정책의 검토는 재사용하며, 접수 확인은 영수증과 공식 조회로 끝낸다. 외부 작업은 현재 상태와 기한이 허용할 때만 수행한다.

이 PC에서는 개인 skills 폴더의 `savetax`를 저장소 스킬에 정션으로 연결한다. 다른 환경에서는 `.agents/skills/savetax`를 개인 skills 경로에 연결하거나 복사해 설치한다. 정본은 저장소에 하나만 둔다. 기존 `savetax-research`·`savetax-browser` 절차는 이 스킬의 참고 문서에 통합했다.

## 저장 구조

| 위치 | 내용 |
|---|---|
| `.agents/skills/savetax/` | 스킬과 작업별 참고 문서 |
| `savetax/`, `scripts/`, `tests/` | 기존 계산·연동·전송·복구 도구와 회귀 테스트 |
| `docs/` | 필요한 경우 찾아보는 CLI·연동 설명 |
| `research/` | 공개 조사 기록·접수 원장. [최신 결과](research/README.md) |
| `work/` | Git 제외: 원문·데이터·실행 상태·영수증 |
| `docs/archive/`, `docs/superpowers/` | 과거 운영 지시와 설계. 일반 실행에는 읽지 않음 |

선택적으로 [기존 CLI](docs/usage.md)와 [로컬 모델 실행](docs/local-research.md)을 사용할 수 있다. 로컬 모델은 조사 제안, Python은 계산·저장·API, Codex는 근거·본문 판단을 맡는다. 현재 구현은 `commands → application → domain/adapters/runtime`이며 이전 import 경로는 호환 facade다.

Python 3.11 이상에서 `python -m pip install -e .`, `python -m savetax --help`로 도구를 준비한다. 저장 자료만 검토할 때 모델·브라우저를 켤 필요는 없다. 키·개인 지침·원본은 커밋하지 않고 예약은 요청 없이 만들지 않는다.
