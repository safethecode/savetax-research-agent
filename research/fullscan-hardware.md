# 전체 목록 담당 구간 조사

2026-10-16 전체 목록에서 owner_slot 2만, md5_batch 200 이후를 500개 묶음 순서대로 확인했다. 500개 전체를 로컬에서 읽어 후보를 고르고 공식 API available부터 확인했다. Parallel은 독립 후보 최대 5개씩 동시에 검색했고, 유사품·무관상품 검색 결과를 판매근거로 채택하지 않았다.

| 구분 | 수량 |
|---|---:|
| local_rows_read | 9500 |
| local_candidates_selected | 141 |
| official_available | 113 |
| official_scorable_candidates | 110 |
| actually_web_searched | 109 |
| investigation_closed_with_reason | 112 |
| direct_price_checks_completed | 11 |
| verified_positive_submission_candidates | 1 |

25666134 여의시스템 SFP-1G20LX-LC의 정확모델 공개 판매가33000원, 개당 배송3500원을 부모Jev+실DOM으로 확인했다. 제주 추가도선료 미확정 주문2개를 제외한 본토6건48개는 비교금액3744000원, 보수적 비교가36500원 기준 절감가능액1992000원으로 접수 accepted(제출ID e4fa9fe2-587f-4db5-a2c7-d5b28cb24cb3). lint는 미조회 상태다. 일반소비자표시가를 VAT포함 비교가로 채택했으며 VAT포함 명시문장을 관측했다고 주장하지 않는다. 소매 원문은 https://www.aesir3.shop/goods/goods_view.php?goodsNo=1000003352 이다. 실제 예산절감 집행은 확인되지 않았다.

별도 SFP 표적조회12개 중6개 available이었다. 미등록 누리아이엔지24361786의 본토21건200개는 검증된 여의 SFP-1G20LX-LC로 핵심광전송사양대응 대체 비교를 준비했다. 같은제품이 아니며, DDM·온도·전기조건·실장비호환 미확인을 명시했다. B36500원 범위의 절감가능액6500000원이며 아직 제출성공으로 집계하지 않는다. 원모델8500원 쿠팡가격은 실제접속차단/검색캐시뿐이므로 채택하지 않았고, MPS 현재정확상품은 전화문의였다.

로컬 읽기·선별 수를 실가격 검증 완료 수로 표현하지 않았다. 공식 API 전체 facts와 500개 묶음 원문은 work 경로에 보관하고, 공개 JSON에는 합계·개별 최고단가·조사결론만 남겼다. 신규 제출·revision은 부모 담당자가 직전 가이드 전체 재독 후 수행한다.
