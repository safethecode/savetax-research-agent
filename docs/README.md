# 기술 문서

일반 작업은 [savetax 스킬](../.agents/skills/savetax/SKILL.md)에서 시작한다. 아래 문서는 해당 도구의 입력·설치·오류를 확인할 때 읽는다.

| 필요한 내용 | 문서 |
|---|---|
| 기존 CLI·가격/단위 입력·preview·복구 | [사용법](usage.md) |
| Ollama 조사·고정 근거 묶음·Codex 승인 | [로컬 조사 실행](local-research.md) |
| Browser Harness·Jev | [브라우저](integrations/browser.md) |
| Parallel 검색 | [검색](integrations/parallel.md) |
| 상품검색 MCP | [MCP](integrations/market-mcp.md) |
| HWP/HWPX 추출 | [문서](integrations/documents.md) |

`records/`는 현재 접수 원장·요약, `work/`는 비공개 원본·영수증이다. 과거 조사·설계·운영 지시는 Git 이력과 `work/archive/legacy-layout-20261107.zip`에 보존했다. 일반 실행에는 로드하지 않는다. 현재 구현 여부는 코드와 CLI를 기준으로 판단한다. 연동 문서의 날짜가 적힌 성공·가격·응답시간은 당시 관측이며 현재 상태를 보장하지 않는다.
