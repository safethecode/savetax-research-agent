# SaveTax 리서치 하네스

조달 물품과 국내 실제 판매가를 대조하고, 신규 고액 절감 후보를 점수 제출까지 연결하는 Python 도구다. 목표는 대회 기준 600억 원이며 아직 달성하지 않았다. 최신 조사·제출 기준은 [AGENTS.md](AGENTS.md)에 있다.

## 구성

| 기능 | 구현 |
|---|---|
| 공식 API·인증 ZIP, 토큰 노출 방지 | `savetax/client.py` |
| 물품별 중복 제거·고정 무작위 묶음 | `savetax/analysis.py` |
| 선언형 JSON DSL·반려 피드백 개선 제안 | `savetax/rules.py`, `strategies/` |
| 실측 가격·단위·세금·필수 비용 검증 | `savetax/evidence.py` |
| 다이소·다나와 원격 MCP 검색 | `savetax/market.py` |
| JS 판매 페이지·격리 Chrome·Jev 동작 제안 | `savetax/browser.py`, `scripts/browser_mcp.py` |
| Parallel 판매 페이지 검색 | `savetax/parallel.py` |
| 점수 본문·계약/납품요구/라인 자동 기록 | `savetax/submissions.py` |
| 억 단위 우선·소액 후순위 대기열 | `savetax/queue.py` |
| 제보·상태·정정과 영수증 보존 | `savetax/reports.py`, `savetax/cli.py` |

다이소와 PC 가격검색 MCP는 실제 호출을 확인했다. 다른 연결의 제약은 [MCP 상태](docs/mcp-connections.md)를 참고한다. 유료 가입이나 사용자의 구매 계정 변경은 하지 않는다.

사용자가 요청한 [Browser Harness·Jev](docs/browser-research.md)와 [Parallel 검색](docs/parallel-search.md)도 연결했다. `.env.txt`의 키는 허용된 이름만 읽어 프로세스 환경변수로 전달하며 출력·커밋하지 않는다.

```powershell
python -m savetax browser-status
python -m savetax parallel-search --query '정확한 모델 국내 판매가' --output work/search.json
python -m savetax browser-read --url 'https://판매처/상품' --output work/browser/product.json
```

## 실행

Python 3.11 이상이 필요하다. Windows에서 `python`이 스토어 연결용 실행 파일이면 실제 설치된 Python의 절대 경로를 사용한다. 이 환경의 번들 Python으로도 검증했다.

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
python -m savetax --help
```

인증은 `SAVETAX_TOKEN` 환경변수를 우선 사용한다. 없으면 기존 `savetax-agent-guide.md`에서 한 개의 토큰만 메모리로 추출한다. 개인 지침은 Git 추적에서 제외되어 있다. 공개 manifest 확인은 활성 에이전트 세션에서 수행하며 이 도구는 별도 폴러를 만들지 않는다.

```powershell
python -m savetax download
python -m savetax summary --parquet work/data/savetax-products-20261010-r5/listings.parquet
python -m savetax mine --parquet work/data/savetax-products-20261010-r5/listings.parquet --handle 삼손 --dataset-version 20261010-r5 --batches 10
python -m savetax hydrate --limit 10
python -m savetax market-search --provider daiso --query 복사용지 --limit 5
```

`mine`은 같은 상태·출력 파일로 실행하면 다음 묶음부터 이어간다. handle·버전·경로·전략이 바뀌면 새 파일을 지정한다. 실패 후보는 기록하며 다음 후보를 처리하고, `hydrate --retry-failures`로 재시도한다. 시장 검색 결과는 실제 판매가 검증의 출발점이다.

## 점수와 대기열

점수 본문용 입력 JSON은 `{item, offer, event}`다. `item`과 `event`는 공식 API 응답이며 `offer`에는 실제 확인한 `model`, `url`, `quote`, `unit_price`(정수 문자열), `observed_at`, `vat_included`, `shipping_included`, `price_verified: true`, `model_verified: true`를 넣는다. 이 확인값은 실제 상세·선택 옵션을 검토한 뒤에만 쓴다. 필수 비용을 더한 경우 `benchmark_unit_price_krw`와 비교 범위도 적는다.

```powershell
python -m savetax build-score --input work/verified-offer.json --output work/score-body.json
python -m savetax score --input work/score-body.json --receipt work/score-item.json
python -m savetax score --input work/score-body.json --receipt work/score-item.json --send
```

`score`는 preview의 실제 서버 예상액이 기본 1억 원 미만이면 접수하지 않고 후순위로 기록한다. preview가 신규 등록을 허용해야 하고 제출 직전 중복을 다시 조회한다. 성공한 영수증은 재실행해도 덮어쓰거나 재접수하지 않는다. 접수 결과가 불명확하면 같은 멱등 키로 결과부터 확인한다.

`queue` 입력은 `item_id`, `state`, `verified`, `eligible_for_preview`, `potential_savings_krw`를 가진 물품별 후보 목록이다.

```powershell
python -m savetax queue --input work/verified-candidates.json --remaining 40
python -m savetax queue --input work/verified-candidates.json --remaining 5 --release-deferred
```

큰 신규 물품을 먼저 내고 작은 절감 후보는 한도가 남을 때 해제한다. 이미 등록된 물품은 신규 대기열에서 제외한다. 일반 제보는 점수 제출과 다른 흐름이며 최신 사용자 지시에 따라 추가 중복 제보를 하지 않는다. 기존 접수와 검토 피드백은 다음과 같이 확인한다.

```powershell
python -m savetax reports
python -m savetax feedback --input work/report-status.json
python -m savetax evaluate --input work/manual-evidence.json --output work/evaluation.json
```

## 근거와 조사 기록

`research/`에는 확인한 가격과 제외·보류 이유를 저장한다. 원본 데이터와 대량 fact는 `work/`에만 둔다. 가격 시점 차이는 조사 제외 조건으로 쓰지 않는다. 납품요구와 실제 예산 절감은 구별하며 서버 영수증의 예상액을 임의로 확정 인정액으로 바꾸지 않는다.

중요한 정정 사례는 [동일성 감사](research/identity-audit.md)에 있다. 모니터 상품 제목은 같았지만 상세에 다른 모델 대체 발송이 있었으므로 동일 제품 가격 근거에서 제외했다. 이후 하네스와 스킬은 실제 발송 모델까지 확인하도록 보완했다.
