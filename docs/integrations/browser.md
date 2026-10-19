# Browser Harness와 Jev

> 현재 연동 구현과 날짜가 적힌 과거 실측 기록이다. 연결 상태·응답 시간·모델/가격 관측을 오늘의 상태로 확대하지 않는다. 전체 구조는 [아키텍처 설계](../superpowers/specs/2026-10-20-local-research-codex-review-design.md), 문서 목록은 [색인](../README.md)을 참고한다.

2026-10-16 사용자 요청으로 `browser-harness[mcp]==0.1.13`, Jev commit `1231850a0bf1a0c0341fe408ef1668dbbfdfac46`을 별도 Python 3.12 환경에 설치했다. 재설치 목록은 `requirements-browser.txt`다.

```powershell
python -m venv work/browser-runtime
work/browser-runtime/Scripts/python.exe -m pip install -r requirements-browser.txt
python -m savetax browser-status
python -m savetax browser-read --url 'https://판매처/상품' --output work/browser/product.json
python -m savetax browser-plan --url 'https://판매처/상품' --goal '모델과 일반 판매가 열람' --output work/browser/plan.json
```

Windows Chrome은 headless로 실행한다. `--session`을 생략하면 기존 프로필 `work/browser-chrome`, 하네스 상태 `work/browser-state`와 잠금 경로를 그대로 사용한다. 기존 작업 CDP를 재사용하며 사용자 기본 프로필에 원격 디버깅을 켤 필요가 없다. 공용 MCP 브라우저는 root 담당이며 직렬로 조작한다.

독립 CLI 조사에는 세 명령 모두 `--session industrial`처럼 이름을 지정할 수 있다.

```powershell
python -m savetax browser-status --session industrial
python -m savetax browser-read --session industrial --url 'https://판매처/상품' --output work/browser/industrial-product.json
python -m savetax browser-plan --session industrial --url 'https://판매처/상품' --goal '모델과 일반 판매가 열람' --output work/browser/industrial-plan.json
```

이름 있는 세션은 `work/browser-sessions/<이름>/` 아래 Chrome 프로필·`DevToolsActivePort`·Chrome PID 파일·작업 잠금과 `browser-state`의 하네스 설정·daemon PID/port·임시 파일을 분리한다. 하네스 실행 파일과 Python 환경은 공유한다. 이름은 1~32자의 영문 소문자·숫자·하이픈·밑줄이며 첫 글자는 영문 소문자나 숫자다. Windows 장치명, 경로 구분자, 공백, 절대경로는 거절한다. 다른 세션의 CDP 선택자나 하네스 경로 환경변수를 물려받지 않는다.

서로 다른 CLI 세션의 공개 페이지 읽기는 병렬로 가능하다. 같은 이름의 CLI 작업은 잠금으로 직렬 처리하며, 기본 세션과 공용 MCP는 계속 root와 순서를 조율한다. 이름을 바꿔 공용 MCP 탭을 조작하거나 로그인·캡차를 우회하지 않는다. CLI는 기존 고정 읽기와 다음 동작 제안만 제공하며 구매·장바구니·문의·자동 제출은 추가하지 않았다. 세션 분리는 경로와 작업 충돌을 줄이기 위한 기능이며 전체 조사 속도의 개선 수치는 측정하지 않았다.

일반 상품의 옵션·수량 확인도 본인의 독립 세션에서 기존 Browser Harness CLI로 조사할 수 있다. 연구용 코드는 공개 HTTPS 주소를 검사하고 `BrowserRuntime._run`의 환경 분리·잠금·임시 탭 정리를 재사용한다. 실제로 관측한 선택지만 바꾸고 비동기 갱신 뒤 합계를 다시 읽는다. 선택 전후의 원문과 옵션·수량·합계 및 기존 탭 보존 여부를 `work/`에 남긴다. 웹 문서의 코드를 복사해 실행하거나 구매·장바구니·문의·로그인 동작을 수행하지 않는다. 공개 `savetax` CLI에 범용 스크립트 실행 명령을 추가한 것은 아니다.

MCP `browser_harness`는 Codex에 등록했다. 실행 파일은 `work/browser-runtime/Scripts/python.exe`, 인자는 `scripts/browser_mcp.py`의 절대 경로다. 스크립트가 작업 CDP를 설정하고 공식 MCP 진입점을 호출한다. `work/browser-runtime`을 지우면 재설치가 필요하다.

## 키 처리

`.env.txt`는 `.gitignore`의 `.env.*`로 제외한다. 허용된 이름만 셸 평가 없이 읽고 프로세스 환경변수로 전달한다. 기존 환경변수가 우선한다. 레지스트리·셸 프로필·MCP 설정에 키 값을 복사하지 않는다. 상태 출력은 존재 여부만 표시하며 수집 결과에서는 받은 키 값을 제거한다. SaveTax 인증 환경변수는 브라우저 자식 프로세스에 전달하지 않는다.

TypeSafe는 Jev의 동작 선택에 사용한다. `TEXT_MODEL_API_KEY`가 없어 upstream Jev의 자유 입력 생성은 준비되지 않았다. `browser-plan`은 실제 페이지를 읽고 TypeSafe에 다음 동작을 묻는다. 동작은 검토 후 MCP로 실행한다. Parallel 검색은 별도 클라이언트로 연결한다. 현재 Parallel 공식 Chat 문서는 Responses API로 이동하므로 Chat Completions 전용 입력 생성기에 임의 연결하지 않는다.

## 실제 검증

| 항목 | 결과 |
|---|---|
| doctor | 0.1.13, daemon alive, browser_ready=true |
| Chrome 이동 | IANA 공개 페이지 제목·URL 읽기 성공 |
| 네이티브 MCP | `browser_page_info`로 같은 작업 탭 확인 성공 |
| Jev + TypeSafe | F19WDLPR 다나와 페이지 읽기·다음 동작 판단 성공. 모델 `jev-1.13.0`, 모델 응답 258ms (1회) |
| G마켓 EWI | headless 접근은 '잠시만 기다리십시오…' 챌린지. 이 수집물을 가격 검증으로 채택하지 않음 |
| 독립 CLI 세션 | `--session industrial`로 디자인템 D8013 판매 페이지의 제목·모델·12,900원 표시·배송 문구·FREE/XL 치수 목록을 1회 수집했다. 별도 Chrome ActivePort/PID·하네스 daemon port가 생성됐고 작업 잠금이 해제됐다. 옵션을 선택하지 않은 `unreviewed` 수집물이며 발송 옵션·사양·대회 자격 검증을 뜻하지 않는다. |
| 독립 세션의 병렬 읽기 | `root-check-1`과 `root-check-2`로 공개 판매 페이지를 동시에 읽었다. 서로 다른 Chrome CDP 포트와 상태 경로를 썼고 잠금은 해제됐다. 작업 전후 공용 브라우저의 129개 탭은 같았다. 전체 147개 테스트도 통과했다. 독립 리뷰에서 발견한 원격 브라우저 식별자 `BU_BROWSER_ID` 상속은 차단하고 회귀 테스트로 확인했다. |
| 독립 세션의 옵션 확인 | 산업 에이전트가 MC-2200의 블랙·100(XL)·수량 1을 선택해 29,700원 합계를 읽었다. 실제 본문에 배송비 3,500원·20만원 이상 무료·부가세 10% 포함이 있었다. 기존 페이지 목록은 전후 같았고 임시 탭은 정리됐다. 기술 동등성은 이 결과로 판단하지 않았다. |

258ms는 한 번의 모델 응답 시간이며 전체 조사 속도를 뜻하지 않는다. 수집 JSON의 `evidence_status=unreviewed`는 조사자가 모델·옵션·가격을 대조하기 전까지 유지한다. Jev의 DONE은 제출 자격 판정이 아니다. 공개 HTTP와 검색으로 읽을 수 있는 페이지는 그 경로도 계속 쓴다.

케이토목 보강토블록 B형의 수량별 합계도 직접 확인했다. 초기 상품가 2,900원에 운임 예상 510원만 더한 초안은 팔레트 비용을 빠뜨렸다. 수량 1에서는 팔레트 15,000원을 더한 17,900원, 수량 585에서는 팔레트 13개 195,000원을 더한 1,891,500원이 표시됐다. 두 합계 모두 페이지의 VAT·운임 별도 조건을 그대로 따른다. 25톤 운임 예상 300,000원까지 더한 만차 기준은 VAT 포함 개당 약 4,120.77원이며, 납품 사실별 끝수와 지역에 따라 달라진다. 이 관측을 바탕으로 조사 스킬에 수량 입력 후 추가 비용과 숨겨진 배송 필드의 표시 여부를 확인하는 절차를 추가했다.

[Browser Harness](https://github.com/browser-use/browser-harness), [Jev](https://github.com/browser-use/jev-ultrafast), [Parallel Responses](https://docs.parallel.ai/responses-api/responses-quickstart)의 공식 문서를 확인했다. 재사용 절차는 `.agents/skills/savetax-browser/SKILL.md`다.

## 오류 원인과 탭 정리 결과

브라우저 작업이 시간 제한을 넘거나 JSON을 반환하지 못한 뒤 임시 탭 정리까지 실패하면, 정리 오류가 앞선 작업 오류를 덮는 문제가 있었다. 이제 원래 작업 오류를 먼저 보존하고 탭 정리 실패를 덧붙인다. 결과가 생성됐더라도 정리에 실패하면 성공으로 반환하지 않는다. 외부 오류 원문과 키는 출력하지 않는다.

시간 초과·잘못된 JSON과 정리 실패를 함께 재현하는 회귀 테스트 두 개를 추가했다. 이는 오류 진단을 보완한 변경이며, 간헐적인 탭 정리 실패 자체를 해결했다는 뜻은 아니다. 실제 재시도 한 번에서는 Jev 응답과 정리가 모두 성공했다. Jev의 `DONE`은 그 페이지에서 다음 동작이 없다는 판단이므로, 선택 옵션의 가격·수량과 사양 검토는 별도로 수행한다.
