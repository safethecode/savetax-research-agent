# 기존 도구를 쓸 때

스킬은 판단·자료 읽기·본문 작성을 담당한다. 기존 Python은 공식 API·계산·원문 보존·전송/복구에 사용한다. 이미 저장된 자료를 검토하는 요청에 Ollama·브라우저·모든 테스트를 일괄 실행할 필요는 없다.

이 스킬의 저장소 정본은 `<repo>/.agents/skills/savetax/`다. 개인 skills 폴더의 정션으로 설치했다면 실제 대상 경로의 저장소를 사용한다. 실행 디렉터리의 `pyproject.toml` 이름이 `savetax-research-agent`인지 확인하고 Python 3.11 이상으로 아래 명령을 실행한다. 기존 가상환경·번들 Python을 재사용한다.

## 저장된 입력으로 본문 만들기

`python -m savetax build-score --input work/verified-offer.json --output work/score-body.json`

입력은 `{item, offer, event}`이며 item/event는 공식 snapshot, offer는 실제 판매 관측이다. 세금·팩·fact별 B·대체품 필드는 저장소 `docs/usage.md`가 정본이다. 새 필드를 추측해 채우지 않는다.

## 선택: 로컬 모델 조사

Ollama가 실제 실행 중이고 선택 모델이 설치됐는지 먼저 확인한다. 모델을 호출하지 않고 로컬 모델 실행 성공이라고 보고하지 않는다. 기존 모델은 `qwen3.5:9b`이며 현재 사용자가 바꾸면 설정을 따른다. 원격 모델 전환·다운로드·자동 예약은 만들지 않는다.

```powershell
python -m savetax research --input <공식-snapshot.json> --policy <현재-policy.json> --profile config/local-profile.json --run-dir work/runs/<고유-run>
```

외부 검색·Jev 읽기가 필요하면 명시된 도구 예산과 `--tools`를 사용한다. 같은 입력·정책·설정과 run이면 완료 job을 재사용한다. 세부 설정은 저장소 `docs/local-research.md`에서 필요한 항목만 읽는다. 합성 예제의 실행 성공을 실제 가격 검증으로 세지 않는다.

## 리뷰와 신규 전송

기존 research가 만든 `package_dir` 또는 `savetax.application.review.create_package`로 고정한 근거 묶음을 사용한다. 후자의 필수 인자는 item/event/policy/proposal/sources/calculation/body이며 입력 계약은 구현/`docs/local-research.md`를 확인한다. 저장 파일 형식을 복제한 새 리뷰 시스템을 만들지 않는다.

```powershell
python -m savetax review --package <package_dir>
python -m savetax score --input <package_dir>/body.json --package <package_dir> --review <review.json> --receipt work/<item>-receipt.json --min-saving <현재-기준> --send
```

`approved`인 실제 Codex 리뷰와 현재 근거·본문·정책 해시가 일치해야 한다. 같은 승인 파일은 다시 호출하지 않고 사용한다. Python의 `ScoreClient.submit/revise`도 이 gate를 유지한다. 접수 결과가 불명확하면 [submission.md](submission.md)의 복구를 수행한다. 이의제기는 신규 score 명령과 별개이며 [appeals.md](appeals.md)를 사용한다.

## 파일과 확인 범위

| 위치 | 용도 |
|---|---|
| `.agents/skills/savetax/` | 재사용 절차의 정본 |
| `savetax/`, `tests/` | 작동하는 도구와 그 회귀 테스트 |
| `records/` | 현재 접수 원장과 결과 요약만 보존 |
| `work/` | 비공개 원문·실행 상태·실제 첨부·영수증 |
| `work/archive/`와 Git 이력 | 과거 조사·설계·일회성 도구. 일반 실행 때 로드하지 않음 |

자료/문서 변경은 연결·입력·결과를 해당 범위에서 확인한다. 코드 변경 때만 관련 테스트를 실행하며, 반복 실패·새 원인·공통 경계 변경이 없다면 같은 검사를 늘리지 않는다. 독립 리뷰나 전수 재감사는 요청되거나 실제 불일치가 있을 때 수행한다.
