# 전체 목록 담당 구간 조사

2026-10-16 전체 목록에서 owner_slot 2만, md5_batch 200 이후를 500개 묶음 순서대로 확인했다. 500개 전체를 로컬에서 읽어 후보를 고르고 공식 API available부터 확인했다. Parallel은 독립 후보 최대 5개씩 동시에 검색했고, 유사품·무관상품 검색 결과를 판매근거로 채택하지 않았다.

| 구분 | 수량 |
|---|---:|
| local_rows_read | 1500 |
| local_candidates_selected | 20 |
| official_available | 19 |
| official_scorable_candidates | 18 |
| actually_web_searched | 16 |
| investigation_closed_with_reason | 16 |
| direct_price_checks_completed | 3 |
| verified_positive_submission_candidates | 0 |

현재 새 양수 제출 확정 후보는 0건이다. 직접 원문 가격 확인을 마친 일렉트로룩스 EFP72315S, 코코브루니 콜드브루 바닐라라떼 200mL, 동원 닭강정소스 2.1kg는 일반 판매가가 공식 fact 기준보다 높아 제외했다. exact 상품 페이지가 검색돼도 현재 404인 상품은 보류했다. 로컬 읽기·선별 수를 실가격 검증 완료 수로 표현하지 않았다.

공식 API의 전체 facts와 500개 묶음 원문은 work 경로에 보관하고, 공개 JSON에는 합계·개별 최고단가·조사결론만 남겼다. 신규 제출·revision은 부모 담당자가 직전 가이드 전체 재독 후 수행한다.
