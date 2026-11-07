# 로컬 조사와 Codex 리뷰 실행

로컬 조사 모델은 설치된 Ollama `qwen3.5:9b`다. Python이 작업 단계·도구 예산·원문 보존·공식 fact 계산을 담당하고, Qwen은 출처가 있는 미검토 제안을 만든다. Codex가 고정한 원문·계산·최종 본문을 별도로 검토한다. 명령을 실행할 때만 작업하며 예약은 만들지 않는다.

## 바로 실행하기

저장소 root에서 Python 3.11 이상과 실행 중인 Ollama가 필요하다. 선택한 모델은 미리 설치되어 있어야 한다. 프로그램은 모델을 내려받거나 원격 모델로 자동 전환하지 않는다.

```powershell
python -m pip install -e .
python -m savetax research --input work/input.json --policy config/policies/local-research.json --profile config/local-profile.json --run-dir work/runs/research-001
```

`work/input.json`에는 실제 공식 snapshot과 저장한 판매 원문의 경로를 넣는다. 입력 구조는 아래의 item/event/sources 설명을 따른다. `awaiting_review`는 근거 검증이나 접수 성공을 뜻하지 않는다.

실제 조사에는 공식 snapshot JSON을 `--input`으로 주거나 공식 API 조회를 사용한다. 후자는 개인 가이드의 기존 인증과 브라우저 별도 런타임이 필요하다.

```powershell
python -m savetax research --item-id 12345678 --policy config/policies/local-research.json --run-dir work/runs/research-001 --tools --root .
```

물품 번호는 실제 조사 대상으로 바꾼다. `--tools`는 Parallel 검색과 기존 Jev 실행 루프를 허용하므로 외부 API 비용이 발생한다. `.env.txt`의 키는 각 서비스에만 전달한다. 검색 발췌와 실제 브라우저 관측을 별도로 저장하며, 모델은 실제 발견한 URL만 읽을 수 있다. 구매·장바구니·로그인·연락 기능은 제공하지 않는다.

여러 snapshot은 `{"jobs":[{"item":...,"event":...,"sources":[...]}]}` 형식이다. 기본 최대 20후보를 한 run에서 순서대로 처리하고 GPU 추론은 한 번에 하나만 실행한다. 각 source의 `path`는 입력 JSON 위치를 기준으로 해석한다. `kind`는 retailer/manufacturer/search 등이며 검색 자료만으로 가격 본문을 만들 수 없다.

## 리뷰와 전송

출력된 `package_dir`에는 변경할 수 없는 manifest·원문 사본·본문·계산이 들어 있다. 다음 명령은 일반 `codex exec`를 read-only 모드로 호출한다. 완전한 manifest와 텍스트 원문을 크기 한도 안에서 전달하며, 일부를 조용히 생략하지 않는다.

```powershell
python -m savetax review --package <package_dir>
```

결과는 `approved`, `needs_evidence`, `rejected`와 리뷰 파일 경로로 출력된다. JSON 형식만 맞는 로컬 응답은 Codex 리뷰를 대신하지 않는다. Codex가 실제 resolved 모델명을 보고하지 않으면 요청한 모델과 그 관측 한계를 실행 영수증에 구분해 기록한다. 합성 예제는 실제 근거가 없으므로 승인 대상으로 해석하면 안 된다.

기존 `build-score`와 `score`의 preview는 유지한다. **새 전송과 revision에는 원문·정책·본문과 일치하는 Codex 승인 파일이 필수**다. 기존 직접 `ScoreClient.submit/revise` 호출도 `package_dir`, `review_path`를 전달해야 한다.

```powershell
python -m savetax score --input <package_dir>/body.json --package <package_dir> --review <review.json> --receipt work/score-receipt.json --min-saving 1000000000 --send
```

예시 정책은 `allow_submit=false`, `allow_revise=false`다. 실제 실행 정책에는 현재 위임 범위를 명시해 근거와 함께 고정한다. 과거 채팅의 제출 권한이나 금액을 자동 적용하지 않는다. 원문·본문·정책 변경 후에는 새 근거 묶음과 리뷰가 필요하다. 불명확한 POST는 기존 영수증과 멱등 키로 먼저 조회하며, 이미 접수됐거나 pending인 요청의 복구에 새 리뷰 파일을 요구하지 않는다.

## 현재 지원 범위와 재개

자동 초안은 동일 모델·같은 공식 단위·신품 완제품·일반 구매가·포함 배송비와 세금 근거가 갖춰진 경우를 지원한다. 팩 끝수는 공식 fact별로 따로 올림한다. 대체품, 미확인 환산, 별도 배송비와 필수 설치 비용은 제안과 원문을 보존하고 `body=null`로 남긴다. 기존 수동 builder의 대체품·VAT·fact별 단가 지원은 유지된다. 설치·보증 여부를 모든 품목의 추가 필수 조건으로 만들지는 않는다.

동일 명령을 다시 실행하면 완료한 후보는 모델을 다시 호출하지 않는다. 오류는 원문을 남기고 정책의 시도·검색·읽기·전체 동작 예산 안에서 재개한다. 429의 Retry-After는 상태에 저장하고 기한 전 API 재호출을 막으며 프로세스를 긴 sleep으로 붙들지 않는다. 공식 조회 실패는 해당 후보만 기록하고 다음 후보를 처리한다. 입력 파일 바이트·정책·모델 설정이 바뀌면 새 run 경로를 사용한다. `needs_evidence` 이후 추가 자료도 새 run에서 조사한다. 강제 프로세스 종료로 잠금 파일이 남으면 파일에 기록된 PID의 실행 여부를 확인한 뒤 해당 잠금만 수동으로 정리한다.

```text
work/runs/<run>/
  run.json, effective-policy.json
  jobs/<item>/
    job.json
    official/snapshot.json
    search/, sources/, proposals/, calculations/
    packages/<package_hash>/manifest.json, body.json, sources/
    packages/reviews/<review_id>.json
    packages/reviews/executions/<review_id>.json
```

공식 fact 전체·포괄 범위·관련 번호는 모델 컨텍스트와 별개로 보존한다. 제한된 공식 fact snapshot을 전체 물품 합계로 표시하지 않는다. preview 예상액·리뷰 결과·심사 인정액·실제 예산 절감액도 구분한다.

## 코드 경계와 검증

`commands`는 CLI 인수, `application`은 조사·리뷰·출판 흐름, `domain`은 순수 계산과 규칙, `adapters`는 공식 API·검색·브라우저·모델 연동, `runtime`은 저장·설정·잠금을 맡는다. 기존 평면 모듈은 이전 import 경로를 위한 facade다. 프롬프트와 JSON Schema는 `savetax/prompts`, `savetax/schemas`의 wheel 리소스다. 자격증명·모델 파일·원본·실행 로그·리뷰 묶음은 Git에서 제외한다.

```powershell
python -m unittest discover -s tests
python -m pip wheel . --no-deps -w work/wheels
```

구조화 출력은 스키마를 API의 format과 프롬프트에 함께 전달하고 추출 생성 설정을 고정한다. JSON 형식 성공과 값의 사실성은 별도로 검증한다. [Ollama의 구조화 출력 설명](https://docs.ollama.com/capabilities/structured-outputs)을 참고한다.

2026-10-20 검증에서는 unittest 257개 중 255개가 통과했고 2개는 Windows의 symlink 생성 권한 때문에 생략됐다. wheel을 별도 경로에 설치해 계층 import와 네 가지 프롬프트·스키마 리소스도 확인했다. 실제 Qwen 합성 자료 한 건은 약 8.2초에 초안·계산·묶음을 만들었으며, 재실행은 같은 job을 재사용했다. 실제 Codex 리뷰는 계산을 확인하고 합성 판매처·불충분한 원규격을 근거로 `needs_evidence`를 반환했다. 실제 판매 조사의 정확도나 대회 접수 성공률을 측정한 결과는 아니다.

실제 후보를 대상으로 한 후속 시험은 [2026-10-20 로컬 모델 시험](https://github.com/safethecode/savetax-research-agent/blob/0ad6f980630563cfdc6af01bf01c5ffe1c435e46/research/local-model-trial-20261020.md)에 있다. live 작업에서 판매 관측이 없으면 검색·발견 URL 읽기를 먼저 수행하고, Jev의 StalePage는 기존 단계 예산 안에서 다시 판단한다. 실제 가격 검증의 성공과 모델 실행 성공을 구분한다.
