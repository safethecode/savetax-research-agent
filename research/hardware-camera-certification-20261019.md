# 카메라 가격 경로의 세금·구성품·원품 인증 추가 확인

25619100 진명아이앤씨 JHDC-4831AI와 Dahua SD8A840WA-HNF의 비교는 **현재 접수 준비가 되지 않았다. 채택 단가와 검증 예상액은 null**로 유지한다. 아래 702,673,000원은 확인되지 않은 조건을 남긴 하드웨어 산술이며, 접수액·심사 인정액·실제 예산 절감액이 아니다. 컴퓨존 가격 경로는 기존 `root-wide-alternatives`에도 있어 새로운 판매처 발견으로 중복 집계하지 않는다.

[컴퓨존 상품](https://www.compuzone.co.kr/product/product_detail.htm?ProductNo=1051613)의 1대 일반가 1,668,000원을 다시 읽었고, [공식 FAQ](https://m.compuzone.co.kr/cscenter/faq_main.htm)의 모든 상품 가격 부가세 포함 기준을 HTTP 본문에서 확인했다. 배송 안내 팝업은 30만원 이상 구매하면 택배 1박스가 무료라는 내용이다. 대량 전체를 무료로 계산하지 않고 검토 산술에 대당 3,000원을 더했다.

[Dahua 공식 PDF](https://material.dahuasecurity.com/uploads/soft/20201217/DH-SD8A840WA-HNF_20201217(For-Project-Only).pdf) 3페이지를 렌더링해 PFB306W 벽부형 마운트와 DC36V 2.23A 어댑터가 기본 동봉품임을 직접 확인했다. 필수 부품 가격을 임의로 0원 처리한 것은 아니다. 다만 [현재 제조사 HTML](https://www.dahuasecurity.com/products/dedicated-products/project-exclusive/ptz-cameras/sd8a840wa-hnf(for-project-only))은 AC24V 3A를 적는다. 두 세대의 전원 표기를 혼합하지 않았고, 실제 국내 판매 재고의 전원 세대·동봉 구성 대응은 아직 확정하지 않았다. Hi-PoE 지원은 두 문서에 공통이다.

[TTA 공식 인증제품 검색](https://cs.tta.or.kr/tta/notification/ttaCertProductListR.do)에서 원품 JHDC-4831AI의 **TTA-IT-V-25-067, 2025-01-24**를 찾았다. 결과요약서 1페이지를 직접 렌더링했으며, 인증 범위는 보안 항목 선택·성능품질 항목 미선택이다. 원품은 SI-9310IR(TTA-IT-V-24-185)의 보안 동일 소프트웨어 모델이며 펌웨어는 2.23.00_20240619_R24다. 이것으로 카메라의 모든 영상 성능이 인증됐다고 확대하지 않는다.

[원규격](https://shop.g2b.go.kr/link/GMSF001_01/?ctrtItemMngNo=002270134_1220002037) 3.4 선택부품 표의 JHDC-4831AI 행에는 TTA ●가 있다. 각주의 정확한 뜻은 인증 대상 품목이면 인증받은 모델이라는 설명이다. 각주 자체가 모든 대체품에 같은 기관의 인증을 강제하는 법적 문장이라고 확대하지 않는다. 그러나 대안의 보안 적합성을 확인하지 않은 채 광학 줌 증가만으로 원품보다 핵심 성능이 분명히 우수한 완제품이라고 확정하지도 않는다.

TTA 전체 인증 검색의 SD8A840·Dahua·다후아는 각각 0건이었다. TTA가 공개한 2026-10-15 보안기능 확인서 XLSX의 235개 제품 행에서도 관련 모델·제조사를 찾지 못했다. 이는 해당 목록의 관측 결과이며, 다른 시험기관까지 포함한 미인증 확정이 아니다. 컴퓨존의 KC 표시 R-R-DXJ-DHI-LM22-A200도 해당 카메라 모델과의 대응을 확인하지 못했다.

| 계약번호 | 납품요구번호 | 라인 | 수량 | 공식 C | B 1,671,000원의 조건부 차액 |
|---|---|---:|---:|---:|---:|
| 002270134_1 | R25TB01337473 | 31 | 91 | 618,800,000원 | 466,739,000원 |
| 002270134_1 | R26TB01970724 | 1 | 46 | 312,800,000원 | 235,934,000원 |

두 fact의 Q 137대·C 931,600,000원과 관련 번호를 원문 그대로 JSON에 보존했다. 원품은 현장설치도이고, 검토 가격은 현장 설치·배선·지주 시공을 포함하지 않은 하드웨어 취득 범위다. 설치 견적을 모든 후보의 추가 관문으로 만들지는 않되 실제 범위 차이는 남긴다. 가격·사양의 한계를 지운 제출은 하지 않았다. 이번 추가 확인의 preview·접수는 모두 0건이다.

공개 파일에 원문 전체를 복제하지 않고 아래 해시로 원시 자료를 식별한다. 원품 규격 HWP의 변경 이력은 평가하지 않았다.

| 자료 | SHA-256 |
|---|---|
| retailer_VAT_policy | `729d8095b6a8ffb51db83bfa8f5efa2e7adbc7c3deaa2af145dadb96b30bf4ba` |
| retail_observation | `a7c650c6e04ccc6297816e7105156748cff90ba9ef19b16a5ad2549cd2236419` |
| retail_shipping_popup | `72a0785539d6920281a9fdafcd02e108cf8aa1579b49674e55fea4d1c39bd83f` |
| manufacturer_standard_package | `0301ca6f1b70b0241cdd7a0ffec646a6ab5ce68374ff65c403ae0775670c25ce` |
| manufacturer_current_spec | `b9edb1bd4ed693103036f181b656a4c69076466cffc1c77f87eb4e2b488e6c45` |
| original_TTA_certificate | `5e6dc9ddf03a93c70cc41e46c0fe9a81a8cb53798dc215e88c8e6278be121fad` |
| TTA_search_observation | `4be1373991f605f96314d734c33e2b59351bc97820a657fddfa908fedb52240f` |
| TTA_security_function_issued_list | `2e9555d353624dafaf2a3ac9e6ffb9b89a410b5438befdd415f30a51e4742d56` |
| original_spec_extracted | `bcce7000bc5a4c255d2746066e905d2213c7fa8d05b3b9a1b57227db793dc2b1` |
