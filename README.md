# SaveTax 리서치 하네스

조달 물품과 국내 실제 판매가를 대조하고, 신규 고액 절감 후보를 점수 제출까지 연결하는 Python 도구다. 최신 목표는 대회 예상액 1,000억 원이며 아직 달성하지 않았다. 신규 건당 최소 10억 원과 최신 조사·제출 기준은 [AGENTS.md](AGENTS.md)에 있다.

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
| 공식 규격서의 HWP/HWPX 형식 판별·원문 해시·본문 추출 | `savetax/documents.py` |
| 점수 본문·계약/납품요구/라인 자동 기록 | `savetax/submissions.py` |
| 억 단위 우선·소액 후순위 대기열 | `savetax/queue.py` |
| 제보·상태·정정과 영수증 보존 | `savetax/reports.py`, `savetax/cli.py` |

다이소와 PC 가격검색 MCP는 실제 호출을 확인했다. 다른 연결의 제약은 [MCP 상태](docs/mcp-connections.md)를 참고한다. 유료 가입이나 사용자의 구매 계정 변경은 하지 않는다.

사용자가 요청한 [Browser Harness·Jev](docs/browser-research.md)와 [Parallel 검색](docs/parallel-search.md)도 연결했다. `.env.txt`의 키는 허용된 이름만 읽어 프로세스 환경변수로 전달하며 출력·커밋하지 않는다.

```powershell
python -m savetax browser-status
python -m savetax parallel-search --query '정확한 모델 국내 판매가' --output work/search.json
python -m savetax parallel-search --query '정확한 모델' --objective '같은 모델의 국내 일반 신품 판매 상세와 실제 가격·포장 구성을 찾는다.' --output work/model-search.json
python -m savetax browser-read --url 'https://판매처/상품' --output work/browser/product.json
```

내려받은 한글 규격서는 `python -m savetax document-read --input work/spec.hwpx --output work/spec-text.json`으로 읽는다. 확장자 대신 실제 파일 형식을 판별하며 표·도면·사양 검증 전 상태를 보존한다. HWP 선택 의존성과 사용 범위는 [규격서 읽기](docs/document-reading.md)에 있다.

## 실행

Python 3.11 이상이 필요하다. Windows에서 `python`이 스토어 연결용 실행 파일이면 실제 설치된 Python의 절대 경로를 사용한다. 이 환경의 번들 Python으로도 검증했다.

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
python -m savetax --help
```

인증은 `SAVETAX_TOKEN` 환경변수를 우선 사용한다. 없으면 기존 `savetax-agent-guide.md`에서 한 개의 토큰만 메모리로 추출한다. 개인 지침은 Git 추적에서 제외되어 있다. 공개 manifest 확인은 활성 에이전트 세션에서 수행하며 이 도구는 별도 폴러를 만들지 않는다.

macOS에서는 `guide.md`와 `.env`도 기존 파일 이름이 없을 때 읽는다. 개인 지침의 마크다운 밑줄 이스케이프는 메모리에서만 정규화한다. 브라우저 런타임은 `work/browser-runtime/bin/`을 사용하며, 길이가 제한된 Unix 소켓만 세션별 `/tmp/savetax-bh-<uid>/`에 둔다. Chrome 프로필·근거·로그·잠금은 계속 `work/`에 보존한다.

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

판매가가 부가세 별도이고 공식 fact가 부가세 포함이면, 원문 가격과 `vat_included: false`를 그대로 둔 채 `benchmark_tax_basis: "vat_included"`, `vat_rate: "0.10"`을 명시한다. 예를 들어 표시가 100,000원은 근거에 그대로 남고 비교 단가 B만 110,000원으로 환산된다. 반대 방향도 같은 방식으로 지원하며 세율은 자동으로 정하지 않는다. 세금 기준이나 세율이 미확인이면 임의로 채우지 않는다. 환산 설명은 가격 근거와 재현 방법에 기록된다. `pack_quantity` 나눗셈과 세금 환산을 모두 마친 뒤 소수 6자리에서 한 번 올림하며, 공통·fact별 비교 단가는 환산한 가격보다 낮출 수 없다. 추가 배송비·설치비는 이 기능이 계산하지 않으므로 같은 세금 기준의 B에 직접 반영하고 근거에 설명한다. 이 옵션은 `build-score`의 본문 생성용이며, 별도의 `evaluate_candidate` 입력은 기존처럼 세금 기준을 맞춘 총비용을 요구한다.

`comparison_kind: equivalent`는 원모델·실제 판매모델·사양 대응·출처·차이 외에 `comparison_assessment`가 필요하다. 핵심 용도와 완제품 구성을 실제 근거로 검토한 뒤 각각 기록한다.

```json
{
  "comparison_assessment": {
    "core_purpose": {
      "status": "verified",
      "basis": "두 제품 모두 40W 실내 조명용이며 사양 출처에서 용도를 확인했다."
    },
    "complete_product": {
      "status": "verified",
      "basis": "선택 가격은 컨버터와 본체를 포함하는 완성 등기구 1개다."
    }
  }
}
```

확인되지 않았으면 `unverified`나 `missing`으로 보존하며 점수 본문을 만들지 않는다. 일반 CCTV 침입 감시를 수위·침수 감시로, 외벽 표면판을 프레임 포함 완성 벽체로, 배낭 하나를 여러 가방의 전체 세트로 바꾸어 계산하지 않기 위한 확인이다. 보증·모든 인증·미세 사양의 완전 일치를 추가 요구하지 않는다. 핵심 용도와 완성 구성이 확인되면 재질·치수·등급 차이를 공개한 대체 비교는 허용한다. 코드는 선언의 형식과 상태를 검사하므로 실제 근거를 읽는 조사자의 판단과 공식 최종 심사를 대신하지 않는다. 기존 대체품 입력도 새 본문 생성 전에 이 두 검토를 보완해야 한다.

구매 포장 때문에 납품 건마다 비용이 달라지면 `offer.benchmark_unit_price_by_fact`에 실제 `scorable` fact_id별 비교 단가를 지정한다. 지정하지 않은 행은 공통 단가를 유지한다. 예를 들어 59,840원인 패널 한 장의 유효면적이 2㎡인데 한 fact에 3㎡가 필요하면, 두 장 119,680원을 구입한 뒤 3㎡로 나눈 단가를 소수 6자리에서 올려 `39893.333334`원/㎡로 기록한다. 다른 납품 건의 남는 면적과 합쳐 구매 장수를 줄이지 않는다. 판매 페이지의 관측가는 계속 한 장 전체의 59,840원이다. `pack_quantity: 2`는 공식 비교 단위 2㎡를 뜻하며 물리 패널 2장이라는 뜻이 아니다. 실제 장수·남는 면적·원문 단위는 조사 근거에 따로 보존한다. 개별 단가는 포장 환산 관측가보다 낮출 수 없으며, 모르는 fact ID나 6자리를 넘는 소수는 거절한다.

판매 경로별 상태를 조사했으면 `offer`에 다음 두 필드를 함께 보존한다. 다이소1072759에서 MCP는 재고 있음으로 반환했지만 실제 택배는 품절이었던 사례를 반영했다.

```json
{
  "purchase_channel": "parcel_delivery",
  "purchase_availability": {
    "channel": "parcel_delivery",
    "status": "available",
    "source_kind": "retail_page",
    "url": "https://shop.example/item",
    "quote": "택배배송 가능, 3만원 이상 무료배송",
    "observed_at": "2026-10-16"
  }
}
```

URL은 해당 `offer.url`과 같아야 하며 채널도 일치해야 한다. `unavailable`·`unverified`, 다른 채널, MCP 검색만을 출처로 쓴 기록, 잘못된 관측일·인용은 본문 생성과 가격 평가에서 보류한다. 유효한 판매 경로 근거는 재현 설명에 남는다. 두 필드를 생략한 기존 입력은 기존의 수동 가격·모델 검토 기준을 따르며, 새 필드는 현재 대량 재고나 납기 확약을 요구하지 않는다. 코드는 기록의 형식과 상태를 검사할 뿐 인용의 진실성이나 실제 주문 가능성을 자동 검증하지 않는다.

```powershell
python -m savetax build-score --input work/verified-offer.json --output work/score-body.json
python -m savetax score --input work/score-body.json --receipt work/score-item.json --min-saving 1000000000
python -m savetax score --input work/score-body.json --receipt work/score-item.json --min-saving 1000000000 --send
```

`score`는 preview의 실제 서버 예상액이 `--min-saving`보다 작으면 접수하지 않고 후순위로 기록한다. 범용 명령의 기본값은 0이며 이 작업의 제출 기준을 뜻하지 않는다. 현재 작업은 `AGENTS.md`와 날짜별 선별 기록의 금액·한도를 따르며, 위 예시는 10억 원 우선 검토다. preview가 신규 등록을 허용해야 하고 제출 직전 중복을 다시 조회한다. 성공한 영수증은 재실행해도 덮어쓰거나 재접수하지 않는다. 접수 결과가 불명확하면 같은 멱등 키로 결과부터 확인한다.

기존 제출의 승인된 근거 보완에는 Python의 `ScoreClient.revise(submission_id, body, idempotency_key, preview)`를 사용한다. 전체 새 본문을 먼저 `preview`하고, 본인 소유의 편집 가능한 제출을 가리키는 `revise_existing` 결과만 전달한다. 클라이언트는 그 결과의 `current_revision`을 `If-Match`로 보내며 신규 등록이나 철회로 우회하지 않는다. 수정 본문·멱등 키·영수증을 보존하고, 응답이 불명확하면 `recover_request`로 같은 요청의 결과를 먼저 확인한다. 매 수정 직전 개인 지침 재확인과 실제 근거 검토는 조사자가 수행한다. preview의 형식·산식 통과는 가격과 대체 적합성의 입증을 대신하지 않는다.

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
