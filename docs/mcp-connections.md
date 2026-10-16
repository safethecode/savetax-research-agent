# 국내 상품검색 MCP 연결 현황

브라우저 연동 추가: `browser_harness` 0.1.13을 별도 환경에 설치하고 네이티브 MCP `browser_page_info` 실제 호출을 확인했다. 작업 전용 Chrome 연결·Jev·키 사용 상태는 [브라우저 조사 문서](browser-research.md)를 참고한다.

확인 기준: **2026-10-16 10:49 KST**. 공식 운영 문서와 제작자 GitHub 저장소를 확인했으며, 설정 등록·MCP 기동·실제 상품 반환을 구분했다. 공개되어 있는 모든 국내 MCP의 전수 목록을 보장하지는 않는다.

## 실제 검색 가능한 연결

| Codex 서버명 | 연결/범위 | 검증 결과 | 증거 |
| --- | --- | --- | --- |
| `daiso` | `https://mcp.aka.page`, 인증 없는 공개 Streamable HTTP | `daiso_search_products` 실제 HTTP 200. `복사용지` 검색으로 28개 중 3개 상품·가격 반환. 증거파일 기록 10:36 KST | `work/data/mcp-daiso-search.json`, `work/data/mcp-daiso-verified.json` |
| `kr_pc_deals` | 로컬 STDIO, `kr-pc-deals-mcp@1.0.7`; 다나와·컴퓨존 PC 부품/모니터 검색 | **10:43:21 KST** initialize, 도구 11개 목록, `search_parts` 호출 성공. `LS22C312`, `monitor`, `all`, `limit=3` 요청에 실제 상품 2개 반환 | `work/mcp-discovery/kr_pc_deals-probe.json` |

`kr_pc_deals` 첫 검색 결과는 삼성전자 S22C312 170,000원([다나와 상품](https://prod.danawa.com/info/?pcode=73428074))과 삼성 모니터 LS22C312EAKXKR 169,000원([다나와 판매상품](https://prod.danawa.com/info/?pcode=TTC21C_9536641708))이었다. 이는 연결 검증 당시 응답이며 배송비·할인·최종 결제가는 별도로 확인한다.

이어 **10:49 KST에 현재 채팅의 실제 MCP 도구** `mcp__kr_pc_deals__search_parts`로 `로지텍 B100`, `source=compuzone`, `limit=3`을 호출해 상품 2개를 받았다. 그중 정확한 B100 본품은 7,600원([컴퓨존 상품 1079859](https://www.compuzone.co.kr/product/product_detail.htm?ProductNo=1079859))이었다. 검색 결과에 다른 키보드/마우스 합본도 포함되므로 결과 전체를 동일 모델로 간주하지 않는다. 이 호출로 컴퓨존 상품 반환과 현재 채팅에서의 MCP 도구 사용도 확인했다. 응답: `work/mcp-discovery/kr-pc-live-compuzone.json`.

다이소 서버 제작자는 다이소 외에 올리브영·편의점 등의 조회도 안내한다. 서비스별 지원은 [제작자 README](https://github.com/hmmhmmhm/daiso-mcp)와 [서비스 안내](https://mcp.aka.page/prompt)를 따른다. 위 성공 판정은 **다이소 상품검색 호출**에 대한 것으로, 모든 서비스가 같은 시각에 검증된 것은 아니다. 별도 서비스마다 같은 URL을 중복 등록할 필요는 없다.

## 등록했으나 사용 조건이 남은 연결

| Codex 서버명 | 상태 | 확인한 내용 / 남은 조건 |
| --- | --- | --- |
| `danawa` | **설정 등록 완료, 연결 HTTP 403** | `https://mcp.ai.cowave.kr/mcp` initialize 요청이 10:36 KST에 403. 공식 [접속 문서](https://mcp.ai.cowave.kr/docs)는 IP 허용 목록을 명시한다. 계정 로그인/OAuth 문제가 아니다. 서버 설정은 보존했으며 동일 요청을 반복하지 않았다. 현재 호스트 직접 접속을 사용하려면 운영자의 IP 허용이 필요하다. 문의를 발송하거나 IP를 외부에 전달하지 않았다. |
| `coupang_browser` | **설치·설정·MCP 기동 검증 완료, 상품검색 미검증, 비활성화** | `coupang-browser-mcp@0.2.3` initialize 및 도구 9개 목록 성공(10:43:48 KST). 실제 상품검색에는 Chrome CDP가 필요하다. 이 세션의 브라우저 조작은 승인된 CUA 경로로만 수행해야 하므로 CDP 호출·Chrome 시작·사용자 Chrome 종료를 하지 않았다. `enabled=false`로 보존했다. |
| `naver_low_price` | **설치·설정·MCP 기동 검증 완료, 상품검색 HTTP 418, 비활성화** | [woogi8/my_naver_shop_low_price_MCP](https://github.com/woogi8/my_naver_shop_low_price_MCP)의 공개 HTML 조회 방식. 종료된 쇼핑 API를 쓰지 않는다. 10:47:35 KST initialize/도구 목록은 성공했으나 `로지텍 B100` 단일 조회에 `HTTP 418: I'm a teapot`을 반환했다. 재시도하거나 차단을 우회하지 않고 `enabled=false`, `enabled_tools=["search_naver_shopping"]`로 보존했다. |

쿠팡 브라우저 서버는 제품 검색·상세·리뷰 외에 주문·장바구니 변경 도구도 포함한다. 현재 설정의 도구 허용 목록은 `search_products`, `get_product_detail`, `get_product_reviews` 세 개이며, 주문·장바구니 도구는 허용하지 않았다. 현재 환경에서 이 MCP를 통한 직접 CDP 브라우저 조작을 실행한 것으로 보고해서는 안 된다. [제작자 설명과 도구 목록](https://github.com/hanjoonchoe/coupang-browser-mcp)

다나와 공식 MCP의 403과 `kr_pc_deals`의 성공은 서로 다른 연결에 대한 결과다. `kr_pc_deals`는 다나와/컴퓨존 공개 상품 페이지를 읽는 별도의 커뮤니티 서버다. 다나와 공식 MCP 연결이 복구되었다고 해석하지 않는다. [다나와 공식 문서](https://mcp.ai.cowave.kr/docs), [커뮤니티 서버 소스](https://github.com/edward-kim-dev/kr-pc-deals-mcp)

## 추가 조사했으나 등록하지 않은 후보

| 후보 | 판정 | 근거/조건 |
| --- | --- | --- |
| [zeikar/kimcp](https://github.com/zeikar/kimcp), [isnow890/naver-search-mcp](https://github.com/isnow890/naver-search-mcp), [uju777/mcp-server-naver-search](https://github.com/uju777/mcp-server-naver-search) | **기존 네이버 쇼핑 API 종료** | 기존 Client ID/Secret 방식. 네이버 공식 공지는 쇼핑 검색 API가 **2026-07-31 종료**, 기존 발급 키로도 호출 불가, API HUB 대체도 없다고 명시한다. 키만 발급하면 쇼핑검색이 복구되는 상태가 아니다. 일반 뉴스·블로그 API와 구별한다. |
| [insung8150/AgentWebSearch-MCP](https://github.com/insung8150/AgentWebSearch-MCP) | 브라우저 준비 필요, 미설치 | Chrome CDP를 이용하는 일반 웹검색 서버. 현재 CUA 브라우저 제어 경로와 별도로 운용해야 하므로 상품검색 연결로 검증하지 않았다. |
| [uju777/coupang-mcp](https://github.com/uju777/coupang-mcp) | **운영자 점검 공지, 미등록** | 제작자 README에 서비스 일시 중단·API HTTP 503 공지가 있다. 정상 연결로 표시하지 않았다. 로컬로 실행하더라도 기본 upstream이 운영자 서비스라 별도 정상화 확인이 필요하다. 실제 503 재호출 검사는 하지 않았다. |
| [space-cap/mcp-coupang-server](https://github.com/space-cap/mcp-coupang-server) | **인증 필요, 미설치** | 쿠팡 파트너스 Access Key/Secret/Partner ID 필요. 현재 프로세스에 키가 없다. 계정 가입·키 발급을 진행하지 않았다. |
| [item-base](https://item-base.com/) | **유료 계정/mid 필요, 미등록** | 연결 URL `https://api.item-base.com/mcp/server?mid={mid}`. 운영 사이트는 유료 요금제를 안내한다. `mid`를 만들거나 임의 값으로 접속하지 않았다. |
| [tenacl/aladin-mcpserver](https://github.com/tenacl/aladin-mcpserver), [rubatoyd/aladin-book-mcp](https://github.com/rubatoyd/aladin-book-mcp) | **알라딘 TTB 키 필요, 미설치** | 도서·중고도서 가격조회 가능. 현재 프로세스에 `ALADIN_TTB_KEY`가 없다. 계정 가입·키 발급을 진행하지 않았다. |
| [korea-ecommerce-integrated-channel-mcp](https://github.com/minwoo19930301/korea-ecommerce-integrated-channel-mcp) | 상품검색 목적과 달라 제외 | 네이버·쿠팡·11번가·G마켓/옥션 판매자용 등록·수정·삭제 서버다. 소비자 상품검색 연결로 추가하지 않았다. |

네이버 종료 근거: [네이버 개발자센터 내 검색 '쇼핑/책/전문자료' API 서비스 종료 안내 (2026년 7월 31일 예정)](https://developers.naver.com/notice/article/32564), [[중요] Search API, Search Trend, Shopping Insight 서비스 종료 및 NAVER API HUB 이관 안내](https://developers.naver.com/notice/article/32530). 확인일 2026-10-16. 일반 검색 MCP의 오래된 README에 쇼핑 도구가 남아 있는 것과 현재 upstream 사용 가능 여부는 다르다.

## 로컬 설치와 도구 정책

이번 추가 설치 위치는 `work/mcp-discovery/runtime/`다. 전역 npm 설치와 사용자 Chrome 설정 변경 없이 다음 버전을 설치했다.

```powershell
npm install --prefix work/mcp-discovery/runtime --ignore-scripts --no-audit --no-fund --save-exact kr-pc-deals-mcp@1.0.7 coupang-browser-mcp@0.2.3
```

설치 전 제작자 소스와 npm 배포본을 확인했다. 배포 패키지·의존성은 `runtime/package-lock.json`에 고정되어 있다. Node.js는 현재 호스트의 `C:\Users\컴퓨터\AppData\Local\Programs\LocalAI\node-v24.19.0-win-x64\node.exe`를 절대 경로로 등록했다. 두 서버의 실행 파일 역시 설치 위치의 절대 경로를 사용한다. 이 `work` 폴더를 지우면 등록된 로컬 서버가 실행되지 않으므로 보존하거나 설정 경로를 함께 변경해야 한다.

`kr_pc_deals`는 다음 읽기 도구 6개만 활성화했다.

```toml
enabled_tools = ["search_parts", "get_product_detail", "get_price_history", "compare_prices", "find_lowest_price", "list_by_category"]
startup_timeout_sec = 20
tool_timeout_sec = 60
```

`build_add`, `build_remove` 등 견적 상태 변경 도구는 허용하지 않았다. `ZYTE_API_KEY`는 빈 값으로 설정해 유료 프록시가 사용되지 않게 했다. 기존 사용자 설정의 다른 서버·키를 수정하지 않았다. `coupang_browser`는 상품 조회 3개 도구 허용 목록을 저장했지만 서버 전체를 비활성화했다.

설정은 이 호스트의 `~/.codex/config.toml`에 등록되어 있다. [OpenAI 공식 MCP 문서](https://developers.openai.com/codex/mcp)의 전역 설정·STDIO·Streamable HTTP·`enabled_tools` 지침에 따라 등록했고, `codex mcp list`와 `codex mcp get`으로 저장값을 확인했다. 이 채팅에서는 `mcp__daiso`, `mcp__kr_pc_deals` 도구가 자동으로 추가되었고 `kr_pc_deals` 실제 도구 호출도 성공했다. 다른 채팅/클라이언트에서 도구가 보이지 않으면 연결을 갱신/재시작한 뒤 확인한다.

`naver_low_price`는 제작자 commit `d2868c87147026b082b681df7cedd8ccccb83508`의 `src/index.js`, `package.json`, `package-lock.json`, README를 `work/mcp-discovery/naver-low-price/`에 저장하고 `npm ci --ignore-scripts --no-audit --no-fund`로 격리 설치했다. 네트워크 호출은 `node-fetch`를 이용한 상품 HTML 조회이며 브라우저를 제어하지 않는다. 상품조회 실패 응답이 `isError=true` 대신 일반 텍스트로 반환되므로 JSON-RPC가 성공했다는 이유만으로 정상 검색으로 판정하면 안 된다. 검증 응답은 `work/mcp-discovery/naver_low_price-probe.json`에 있다.

재현용 연결 검사(브라우저 검사 스크립트는 목록만 조회하며 Chrome을 제어하지 않는다):

```powershell
node work/mcp-discovery/probe-stdio.mjs kr_pc_deals
node work/mcp-discovery/probe-stdio.mjs coupang_browser
codex mcp get kr_pc_deals --json
codex mcp get coupang_browser --json
codex mcp get naver_low_price --json
```

설치된 npm 패키지는 1.0.7이지만 `kr-pc-deals-mcp`가 initialize에서 보고한 버전 문자열은 1.0.0이다. 검증 파일에 둘을 구분해 저장했다. 또한 npm 배포본에는 제작자 저장소 main에서 확인한 것보다 파일이 더 있어 실제 배포본의 진입점·도구 등록·네트워크 동작도 확인했다. 계정·키·토큰의 실제 값은 문서나 검증 출력에 저장하지 않았다.
