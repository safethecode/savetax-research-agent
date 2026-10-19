# 세 참가자의 공개 제출 검토와 반증 등록

확인 시각: 2026-10-19T18:06:58.707126+09:00

공개 제출 249건을 전수 검토했다. 현재 근거를 유지한 공개 반증은 126개 제품이며, 별도 2개 제품의 앞선 반증은 공개 정정문으로 관련 주장을 철회했다. 초기 반증 128건과 정정 2건, 총 130건의 접수 및 공개 재조회를 확인했다.

| 참가자 | 전체 검토 | 활성 제출 | 반증 유지 | 정정·주장 철회 | 활성 중 미등록 | 철회 |
|---|---:|---:|---:|---:|---:|---:|
| KiNa_키나 | 88 | 86 | 20 | 0 | 66 | 2 |
| shine | 61 | 60 | 52 | 0 | 8 | 1 |
| WISP | 100 | 100 | 54 | 2 | 44 | 0 |

미등록 건은 새 반증이 입증되지 않았거나 원문·조건 확인에 한계가 남은 건이다. 모든 제출이 잘못됐다고 전제하지 않았다. 철회 3건에는 반증을 달 수 없다.

## 적용한 대회 기준

- [대회 규칙 1·3·4·5·6절](https://hackathon.savetax.now/docs/rules.md): 같은 비교 범위의 근거, 공식 C·Q와 B의 계산, 예상액과 최종 인정의 구분, 공개 반증.
- [대회 참가 지침의 점수 제출 전 필수 검증 3·4·5·7항](https://hackathon.savetax.now/docs/AGENTS.md): 동일 모델과 대체품의 구분, 실제 판매 원문, 핵심 사양·부속품·설치·세금·라이선스·수량 조건, 재현 가능한 비교 단가.
- [제출 스키마 3·4절](https://hackathon.savetax.now/docs/submission-schema.md): 입증한 비교 단가 B, 페이지에서 직접 본 상품과 관측가·인용·VAT·배송 표시.
- [반증 API 7절](https://hackathon.savetax.now/docs/api.md): 정확한 대상 차수, 4000자 이내 본문, 멱등 키와 접수 결과 확인. 일반 사이트 method를 대회 규정 전체로 확대하지 않았다.

## 확인한 주요 쟁점

- shine: CPU 단품가를 완제품 PC의 비교 단가로 쓴 30건, 외장 그래픽카드 누락, 전광판 크기·해상도 차이, 실제 품목과 다른 링크, 소프트웨어 갱신 조건·VAT, 산출 도착가와 원문 관측가의 혼동 등을 구분했다.
- KiNa_키나: 오븐에 포함된 훈연·제어 기능과 설치 범위, 정수 판매 단위의 끝수 비용, 야자매트의 실제 롤별 배송비를 확인했다. 포장 차이는 작은 조정 예시로 한정했고 매트의 재계산은 공개 일반 운임 조건을 적용한 예시라고 명시했다.
- WISP: 원품의 OPS·카메라·마이크와 비교품 기본 구성, 모니터 터치·밝기·명암비·주사율, 노트북 LAN·Windows 구성, 조명의 정격 광출력·효율 차이를 제조사·원규격·실제 판매 상세와 대조했다.

활성 246건의 공개 C·Q·B를 줄별로 재계산한 결과 서버 예상액과 모두 일치했다. 반증의 핵심은 산식 자체보다 B를 뒷받침하는 상품·구성·판매 조건이다. 관련 fact 식별자 9,426개 라인과 원제출에 있는 납품 근거는 구조화 결과에 보존했다.

## 공개 정정한 2건

엔어스 FLCC-15057-002(25543237)·FLDF-15057-001(25543302)는 개별 원규격 대조가 끝나기 전에 공통 카탈로그의 효율·온도 안내로 반증을 등록했다. 추가로 읽은 개별 제원표와 충돌해, 앞선 관련 주장을 철회하는 공개 정정문을 각각 등록했다. 이 2건을 유지한 반증 건수나 입증한 감액에 포함하지 않는다. 원래 접수 기록과 정정문을 함께 보존한다.

## 품목별 처리 결과

| 참가자 | 물품·모델 | 처리 | 확인한 쟁점 또는 추가 검토 사유 |
|---|---|---|---|
| KiNa_키나 | [25584763 PIS-H015TP](https://hackathon.savetax.now/#/submission/e90df355-56fd-4a10-ad95-1f66022c01d8) | 새 반증 미입증·미등록 | 판매처의 DS-QAZ1325G1T-E와 572,000원을 확인했다. 인터엠 제조사 사양도 읽었다. 한국어 TTS 지원이 확인되는 다른 suffix의 문서를 이 판매품에 적용하지 않았으며, 미확인 언어를 기능 부재로 단정하지 않았다. |
| KiNa_키나 | [23402850 DWIP-9021](https://hackathon.savetax.now/#/submission/01eb2093-bfb0-4c73-a9a5-3c61b141eb1b) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [25516615 TECHPIA 3K-TC](https://hackathon.savetax.now/#/submission/b0a0d459-d678-4161-968c-2b52c8e88294) | 새 반증 미입증·미등록 | 컴퓨존의 ABB 3,000VA/2,700W와 일반가 990,000원을 확인했다. 원제출은 내장 배터리가 있는 대체품임을 밝혔다. 원품 모델명 TC의 추가 조건을 확인하지 못해 오류로 단정하지 않았다. |
| KiNa_키나 | [23319421 DBO-202ESD](https://hackathon.savetax.now/#/submission/a3698cbb-5d44-49f5-bbc3-c5e52d90daa1) | 새 반증 미입증·미등록 | RCO-400CE의 22,200,000원과 설치 제외 옵션, 린나이 공식 전원·배선 사양을 읽었다. 원품의 추가 문·세척·제어 기능을 원제출이 공개했다. 별도 원규격의 독립 검증은 미완료라 코스티모 두 건 외 추가 반증은 확정하지 않았다. |
| KiNa_키나 | [24719684 SKK-GP1500](https://hackathon.savetax.now/#/submission/25994bc4-5c94-484e-97d1-efc0fb887b19) | 새 반증 미입증·미등록 | 이오인덕션 공식몰의 1개 합계 4,200,000원과 구매하기 표시를 실제 브라우저에서 확인했다. 정적 HTML에 숨은 SOLD OUT 문구는 품절 증거로 사용하지 않았다. 원제출은 깊이 50mm 차이를 밝혔다. |
| KiNa_키나 | [24695537 HS-SU-76P1](https://hackathon.savetax.now/#/submission/d9a14bdf-b27f-4598-9e07-495a4b329dbb) | 새 반증 미입증·미등록 | 폴 본체 244,200원, 앙카베이스 43,000원과 각도기 25,000원을 읽었다. 경동화물 착불과 주문제작 조건도 확인했다. 판매처의 SUS 표기만으로 강종이 STS304보다 낮다고 단정하지 않았다. |
| KiNa_키나 | [25212793 NMO-202E](https://hackathon.savetax.now/#/submission/cd4af16e-18c5-4cfb-be2e-4ff9a18e2c24) | 새 반증 미입증·미등록 | RCO-400CE의 22,200,000원과 설치 제외 옵션, 린나이 공식 전원·배선 사양을 읽었다. 원품의 추가 문·세척·제어 기능을 원제출이 공개했다. 별도 원규격의 독립 검증은 미완료라 코스티모 두 건 외 추가 반증은 확정하지 않았다. |
| KiNa_키나 | [24505671 HKS-EBV5GB](https://hackathon.savetax.now/#/submission/74e66bce-7d0a-4504-8658-0c46ff7cd8d8) | 새 반증 미입증·미등록 | 비상벨 구성품의 판매 원문과 보조통화장치 누락에 관한 기존 반증을 읽었다. 이미 mooner1022가 실제 구성 차이를 구체적으로 제기했다. 이 조사에서는 새로운 보조통화장치 가격이나 완성 구성 근거를 확보하지 못했다. |
| KiNa_키나 | [24100065 HSO-202E4](https://hackathon.savetax.now/#/submission/309065f4-0828-49d9-a636-9ab3c4c911e2) | 반증 유지 | 제조사 원문으로 확인한 조리·제어 기능 및 필수 설치 범위 차이 |
| KiNa_키나 | [24100063 HSO-122E4](https://hackathon.savetax.now/#/submission/c8848991-5eaa-4933-bbf5-0c7651b120a8) | 반증 유지 | 제조사 원문으로 확인한 조리·제어 기능 및 필수 설치 범위 차이 |
| KiNa_키나 | [24210821 (CN)C3300-24TS](https://hackathon.savetax.now/#/submission/667e18db-57a3-46bd-ba24-c0acc99d3bff) | 새 반증 미입증·미등록 | Router-switch의 두 상품 주소는 직접 GET에서 HTTP 403 챌린지가 나타났다. 접근 차단을 원제출의 가격 오류로 판단하지 않았다. 본문이 해외 비용과 설치, 확장 슬롯 차이를 밝혔음을 확인했다. |
| KiNa_키나 | [24603742 DBF-202EA](https://hackathon.savetax.now/#/submission/47e8e192-d2e5-4deb-a4dd-ee2dbee7bab1) | 새 반증 미입증·미등록 | RCO-400CE의 22,200,000원과 설치 제외 옵션, 린나이 공식 전원·배선 사양을 읽었다. 원품의 추가 문·세척·제어 기능을 원제출이 공개했다. 별도 원규격의 독립 검증은 미완료라 코스티모 두 건 외 추가 반증은 확정하지 않았다. |
| KiNa_키나 | [25064603 DSSRCGW-600AN](https://hackathon.savetax.now/#/submission/4866ba7a-b7d0-4898-a1fb-4b7c8fec880b) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [25784938 SKK-PRO5105SM](https://hackathon.savetax.now/#/submission/b3326de4-92dc-409b-abc9-87bae53f0a75) | 새 반증 미입증·미등록 | 웰치몰의 17,500,000원과 직접배송·설치 무료 조건을 읽었다. 원제출은 자동교반 500인용 대체품의 치수와 소비전력 차이를 밝혔다. 소비전력이 높다는 사실 자체를 성능 우수의 증거로 채택하지는 않았다. |
| KiNa_키나 | [24020216 ACTVISION P6](https://hackathon.savetax.now/#/submission/c7f181eb-0c31-40a4-829b-d7bbddcc5745) | 새 반증 미입증·미등록 | HC P5 키트 1,629.95 USD와 TB40 Plus, 전원·수신 카드 포함 표시를 읽었다. DDP 배송 조건에는 국가별 예외가 있다. 실제 납품 형상과 국내 인증 적합성은 확인되지 않았다. |
| KiNa_키나 | [24687307 NF Board PLUS 140mm](https://hackathon.savetax.now/#/submission/84081e72-1793-4901-b383-86ffb2314892) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24687311 NF Board PLUS 90mm](https://hackathon.savetax.now/#/submission/f6509691-b027-4996-b656-a4d5741fde78) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24656870 NF Board PLUS 100mm](https://hackathon.savetax.now/#/submission/4c760812-e595-43b5-85cf-88d6b78ab690) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24687306 NF Board PLUS 150mm](https://hackathon.savetax.now/#/submission/ce02ff0b-a217-4bab-a67e-c3535dad5b68) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24687309 NF Board PLUS 120mm](https://hackathon.savetax.now/#/submission/aaebaabe-5919-4ba8-92e5-c15c89fc0c88) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24687308 NF Board PLUS 130mm](https://hackathon.savetax.now/#/submission/eb48d445-39be-418e-bd0b-d27b2a64a473) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [25234422 PES-M01](https://hackathon.savetax.now/#/submission/4f31590b-afd5-41b6-bf3f-b77429c590fc) | 새 반증 미입증·미등록 | 실제 판매 가격과 송수신기 구성, 채널 및 주파수 대역에 관한 대조를 읽었다. 같은 주파수 대역만으로 원품의 기존 송신기와 호환된다고 추정하지 않았다. 추가 호환성 검증이 필요하다. |
| KiNa_키나 | [25368043 CGAN-01](https://hackathon.savetax.now/#/submission/819b169d-c23f-4e44-a0af-37ea77fc3b2d) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [24126640 BYTS AM100](https://hackathon.savetax.now/#/submission/4f846b07-08c6-49dc-be1a-856d2869f17e) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [22898595 SID-H-Acoustic-12T](https://hackathon.savetax.now/#/submission/11a6a221-3772-4bb7-b94f-92d41b9f750f) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [22934485 RP MDF PERFORATED BOARD-C2MD](https://hackathon.savetax.now/#/submission/4f79a692-3601-4521-acc7-288d8945c208) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24747746 PP-VL-TW34](https://hackathon.savetax.now/#/submission/dfc7751a-77ee-4ded-a8fd-b6df1a297c6d) | 새 반증 미입증·미등록 | 판매처의 표시 가격과 등·좌판, 팔걸이, 캐스터 및 접이식 구성에 관한 원제출의 대조를 읽었다. 치수 차이는 공개되어 있으며 미확인 세부 성능을 오류로 단정하지 않았다. |
| KiNa_키나 | [24776811 PWM-R092RT](https://hackathon.savetax.now/#/submission/54358afd-5a26-4745-aef2-be0a862a1b14) | 새 반증 미입증·미등록 | 실제 판매 가격과 송수신기 구성, 채널 및 주파수 대역에 관한 대조를 읽었다. 같은 주파수 대역만으로 원품의 기존 송신기와 호환된다고 추정하지 않았다. 추가 호환성 검증이 필요하다. |
| KiNa_키나 | [23341496 VRX-9202H2](https://hackathon.savetax.now/#/submission/e0225d7f-45b1-453d-bb42-6cc4850101af) | 새 반증 미입증·미등록 | 실제 판매 가격과 송수신기 구성, 채널 및 주파수 대역에 관한 대조를 읽었다. 같은 주파수 대역만으로 원품의 기존 송신기와 호환된다고 추정하지 않았다. 추가 호환성 검증이 필요하다. |
| KiNa_키나 | [25153196 HSTW-IEL-6800M(8G4SF)SⅡ-P](https://hackathon.savetax.now/#/submission/a8164abc-2326-43f0-9798-e9f09a6b4ffb) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [25419922 VIXAI-SL187JC](https://hackathon.savetax.now/#/submission/b0536c91-8e23-493a-9652-47f7a4dfdda2) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [24020215 ACTVISION P8](https://hackathon.savetax.now/#/submission/f1bdec38-b14c-4e04-b412-794da8192d03) | 새 반증 미입증·미등록 | HC P8 키트 1,269.95 USD와 TB10 Plus, 전원·수신 카드 포함 표시를 읽었다. DDP의 국가별 예외를 기록했다. 판형 차이가 실제 납품 장소의 설치를 막는지는 확인하지 못했다. |
| KiNa_키나 | [23202195 조미용](https://hackathon.savetax.now/#/submission/96f80564-57fb-41e4-85de-bbbbb478d24c) | 새 반증 미입증·미등록 | 우성물산의 국내산 고춧가루 1kg 19,500원과 원더미트의 21,800원을 읽었다. 군납의 살균·수분·표시·포장 세부 요구를 확인하지 못해 일반 판매품의 미충족으로 단정하지 않았다. |
| KiNa_키나 | [25454998 4C 36](https://hackathon.savetax.now/#/submission/5038fe3d-51c0-46e2-b492-65dd64313347) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [25689649 SCN-640IP](https://hackathon.savetax.now/#/submission/4514075b-1712-4d34-b5b6-1aa6bd23e641) | 새 반증 미입증·미등록 | Vision Datum의 25mm 렌즈 선택품 2,128 USD, Observation Ver. 및 USB2.0 Type-C를 읽었다. 온도측정 범위와 정확도는 표에서 공란이며 일반 설명과 표현이 엇갈린다. 원품의 확정 온도측정·출력 요구를 독립 문서로 확보하지 못해 추가 반증은 보류했… |
| KiNa_키나 | [22958405 EK0011](https://hackathon.savetax.now/#/submission/99b6d1b5-3490-4e77-bedb-7bca0e68d251) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24290854 VI-ACG100L](https://hackathon.savetax.now/#/submission/41a426c9-7950-4ba5-9564-8c42e43817fb) | 새 반증 미입증·미등록 | 두 쿠팡 상품 주소는 HTTP 403으로 현재 옵션을 읽지 못했다. 원제출은 기본 설치 포함 가격과 온도·보증 차이를 공개했다. 차단만으로 가격이 허위라고 판단하지 않았다. |
| KiNa_키나 | [24882496 SJG-306X1](https://hackathon.savetax.now/#/submission/48086e95-5933-436d-8234-a53b9b789822) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24551063 DWT-1299C](https://hackathon.savetax.now/#/submission/42f14083-8a96-4b84-a3e8-bf2ac53908c1) | 새 반증 미입증·미등록 | 판매처의 표시 가격과 등·좌판, 팔걸이, 캐스터 및 접이식 구성에 관한 원제출의 대조를 읽었다. 치수 차이는 공개되어 있으며 미확인 세부 성능을 오류로 단정하지 않았다. |
| KiNa_키나 | [25220478 MKS-1000S](https://hackathon.savetax.now/#/submission/d832219e-9799-485a-9cca-daa078d876ee) | 새 반증 미입증·미등록 | 닥터파이어의 케이텔 5,990원과 23년도 제품 재고정리, 배송 구간표를 읽었다. 재고정리 신품을 중고로 분류하지 않았다. 음량과 동작온도에 관한 추가 인증 자료는 확보하지 못했다. |
| KiNa_키나 | [23848051 MKS-TO-1500](https://hackathon.savetax.now/#/submission/e9f295d4-f614-4b0b-a92d-a92d5fcdd9ee) | 새 반증 미입증·미등록 | 케이텔 5,990원과 현대방재 6,000원의 별도 판매 원문을 읽었다. 닥터파이어 배송 구간표는 111개 미만까지만 노출되어 대량 납품 수량에 요율을 임의로 외삽하지 않았다. |
| KiNa_키나 | [25630445 TJH-3](https://hackathon.savetax.now/#/submission/e0ffaa87-2fa4-4106-80c0-42b23b44f67c) | 새 반증 미입증·미등록 | STS-SL 500×700×300의 372,200원, STS304와 이중문, 화물 착불 조건을 읽었다. 원제출이 설치 공임을 더했고 깊이 구간의 한계를 명시했다. 미확인 추가 공임을 만들지 않았다. |
| KiNa_키나 | [20917953 BJ-1-200](https://hackathon.savetax.now/#/submission/84275f3b-9cdc-4007-b1f6-d44e0e43ef01) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [23448357 GRPS-110](https://hackathon.savetax.now/#/submission/91916d28-70cf-4a50-9156-731780a5cbec) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [24629436 TC-1003](https://hackathon.savetax.now/#/submission/81037a1f-fadd-403f-a23d-52c5aac92cde) | 새 반증 미입증·미등록 | 삼성가구몰의 IN-3005와 인채널 FP-PW5001 판매 원문을 읽었다. 원제출은 높이와 크기 차이, 매립 콘센트의 별도 구성을 밝혔다. 미확인 조립비를 추가하지 않았다. |
| KiNa_키나 | [23136253 CG640](https://hackathon.savetax.now/#/submission/4cd82c57-3d94-4063-98c6-36ade121702b) | 새 반증 미입증·미등록 | Wcctv 주소는 HTTP 403으로 현재 상품 조건을 읽지 못했다. 원제출은 HDMI·아날로그 출력 부재와 25fps를 공개했다. 접근 차단을 가격 오류의 근거로 쓰지 않았다. |
| KiNa_키나 | [24790859 SS-233](https://hackathon.savetax.now/#/submission/05e16a53-53ca-4065-abf5-1d4562eac57a) | 새 반증 미입증·미등록 | OW-700의 기본가 77,000원과 올문장 추가 33,000원, 보조 판매처를 읽었다. 실제 옵션 선택 후 합계는 추가로 검증하지 못해 옵션 오류를 단정하지 않았다. |
| KiNa_키나 | [24798606 SD-204](https://hackathon.savetax.now/#/submission/332742f5-7108-47d7-9dbe-71edf5769948) | 새 반증 미입증·미등록 | 듀비온 NMD1의 429,000원과 무료배송, 선택 방문설치 55,000원을 읽었다. 가림판과 폰캡의 차이는 원제출이 밝혔다. 선택 설치 서비스를 일률적인 필수 비용으로 더하지 않았다. |
| KiNa_키나 | [26266404 GD-MD2000](https://hackathon.savetax.now/#/submission/729208be-b507-45c3-972d-7b4ee9b3fe34) | 새 반증 미입증·미등록 | THD-7000의 1,800,000원 판매 원문을 읽었다. 원제출은 SNR의 측정 항목과 조건 차이를 공개했다. 서로 다른 측정값만으로 성능 열위를 단정하지 않았다. |
| KiNa_키나 | [25314321 KBN-TDMS200](https://hackathon.savetax.now/#/submission/d12436c2-f32c-498c-b912-107ac23d6e9a) | 새 반증 미입증·미등록 | 툴스팜의 DR-SF400DSC 522,200원과 원제출의 풍량·전력 대조를 읽었다. 원품의 천장·벽 설치와 실제 대체품 시공 범위는 추가 확인이 필요하다. 소비전력 증가를 성능 향상으로 간주하지 않았다. |
| KiNa_키나 | [23491239 HS-55AC-5-23](https://hackathon.savetax.now/#/submission/76b63752-fb4f-4f4f-b3b3-471f7133c3b3) | 새 반증 미입증·미등록 | 네덜란드 판매처의 LigoDLB MACH 5ac를 읽었다. 다른 형번의 OEM 동일성은 참가자의 추론이며 확정하지 않았다. 국내 주파수 설정과 인증, 배송 비용은 미확인이다. |
| KiNa_키나 | [25013208 OH-301](https://hackathon.savetax.now/#/submission/6b1a8dd7-cf5f-43f5-8329-538a9ead78e2) | 새 반증 미입증·미등록 | HA-813HN의 555,500원 판매 원문을 읽었다. 원제출은 컵·칫솔용 두 기기를 합산했다. 보조 제품 SW-320H의 타이머 옵션을 직접 선택한 합계는 이번 조사에서 검증하지 못했다. |
| KiNa_키나 | [23661497 (IE)15x3.5inch Drive DAE](https://hackathon.savetax.now/#/submission/dff56070-01cc-46cd-abf4-27f3b94d269c) | 새 반증 미입증·미등록 | BoyuTechs의 Unity XT 10,999 USD와 10개 드라이브 구성을 읽었다. 원제출은 부족한 드라이브 5개를 추가해 180TB로 맞췄다. eBay는 HTTP 403으로 추가 5개 구매 조건을 현재 확인하지 못했다. |
| KiNa_키나 | [24194433 NHM-2408PI-BT](https://hackathon.savetax.now/#/submission/b7e48f85-2ed3-4518-8665-7847a5c353d4) | 새 반증 미입증·미등록 | 본체 448,500원, 전원장치 70,000원과 코드 10,700원 원문을 읽었다. 원품의 PoE 예산은 140W이므로 다른 모델에 제기된 320W 대 240W 전원 문제만으로 이 제품의 공급 부족을 단정하지 않았다. 보안 인증과 동작온도 차이는 미해결이다. |
| KiNa_키나 | [25645025 HS-IPG804MBT](https://hackathon.savetax.now/#/submission/34c4a036-7577-40ce-a30b-c36d3906b62e) | 새 반증 미입증·미등록 | 제조사 이미지에서 비교품의 PoE 가용 320W와 전체 전원 350W를 확인했다. 선택 전원장치는 240W다. 기존 반증과 같은 전원 쟁점이 있어 중복 접수는 보류했으며 원품 240W 부하를 충족하는 실제 조합 검증이 필요하다. |
| KiNa_키나 | [25610254 MV-MIPG804MBT](https://hackathon.savetax.now/#/submission/9bb5d4d9-a0c8-4b9e-b203-4df0a5bc3cda) | 새 반증 미입증·미등록 | 비교품 제조사의 PoE 320W, 전체 전원 350W 사양과 240W 선택 전원을 확인했다. sampple의 기존 반증이 같은 전원 쟁점을 제기했다. 새 전원 구성의 판매 조건을 검증하지 못해 추가 반증은 보류했다. |
| KiNa_키나 | [24357726 IKWR-0902N](https://hackathon.savetax.now/#/submission/1f2da565-b218-41f4-862a-1b84a98a291b) | 새 반증 미입증·미등록 | 실제 판매 가격과 송수신기 구성, 채널 및 주파수 대역에 관한 대조를 읽었다. 같은 주파수 대역만으로 원품의 기존 송신기와 호환된다고 추정하지 않았다. 추가 호환성 검증이 필요하다. |
| KiNa_키나 | [25344260 WH-9000V](https://hackathon.savetax.now/#/submission/bf6aa2d8-e5fc-4027-a788-d4a2c5483500) | 새 반증 미입증·미등록 | 실제 판매 가격과 송수신기 구성, 채널 및 주파수 대역에 관한 대조를 읽었다. 같은 주파수 대역만으로 원품의 기존 송신기와 호환된다고 추정하지 않았다. 추가 호환성 검증이 필요하다. |
| KiNa_키나 | [24480646 PP-VL-B33](https://hackathon.savetax.now/#/submission/8cc73887-4390-440a-bfae-eefd86072f72) | 새 반증 미입증·미등록 | 판매처의 표시 가격과 등·좌판, 팔걸이, 캐스터 및 접이식 구성에 관한 원제출의 대조를 읽었다. 치수 차이는 공개되어 있으며 미확인 세부 성능을 오류로 단정하지 않았다. |
| KiNa_키나 | [23518898 ACH-JMN10AC](https://hackathon.savetax.now/#/submission/fd01f03f-2ce5-4484-9617-b0b3e1612c7d) | 새 반증 미입증·미등록 | 판매처의 표시 가격과 등·좌판, 팔걸이, 캐스터 및 접이식 구성에 관한 원제출의 대조를 읽었다. 치수 차이는 공개되어 있으며 미확인 세부 성능을 오류로 단정하지 않았다. |
| KiNa_키나 | [24480642 PP-VL-TW10](https://hackathon.savetax.now/#/submission/218a1550-7144-4551-85a5-464bd2fcef7f) | 새 반증 미입증·미등록 | 판매처의 표시 가격과 등·좌판, 팔걸이, 캐스터 및 접이식 구성에 관한 원제출의 대조를 읽었다. 치수 차이는 공개되어 있으며 미확인 세부 성능을 오류로 단정하지 않았다. |
| KiNa_키나 | [26129518 RDAS-34H16](https://hackathon.savetax.now/#/submission/089474e5-43c4-4043-ba00-08fc921b5844) | 새 반증 미입증·미등록 | 한화 HRX-1635 4TB의 1,496,000원과 추가 WD 6TB의 594,000원을 읽었다. 원제출은 전용 녹화기와 PC 기반 녹화기의 차이, 가림 녹화 등 기능 차이를 공개했다. 독립 원규격 검증은 미완료다. |
| KiNa_키나 | [25344258 WR-9000VD](https://hackathon.savetax.now/#/submission/e31b843f-4fae-41ae-a61c-a66ef275d03e) | 새 반증 미입증·미등록 | 실제 판매 가격과 송수신기 구성, 채널 및 주파수 대역에 관한 대조를 읽었다. 같은 주파수 대역만으로 원품의 기존 송신기와 호환된다고 추정하지 않았다. 추가 호환성 검증이 필요하다. |
| KiNa_키나 | [24549306 DY-(B-S/C)MP200](https://hackathon.savetax.now/#/submission/9d50ffe0-ae17-4c6c-aee9-149a3afd49a3) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [25603568 DUX-9002](https://hackathon.savetax.now/#/submission/1e6bba12-91eb-4c09-953e-b4b8344f2284) | 새 반증 미입증·미등록 | 실제 판매 가격과 송수신기 구성, 채널 및 주파수 대역에 관한 대조를 읽었다. 같은 주파수 대역만으로 원품의 기존 송신기와 호환된다고 추정하지 않았다. 추가 호환성 검증이 필요하다. |
| KiNa_키나 | [22403472 ESMP-200](https://hackathon.savetax.now/#/submission/9122f0b0-2412-4af8-80c3-02a4f0e469ad) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [23271042 SJ-3510](https://hackathon.savetax.now/#/submission/9e42ca05-0266-4b17-92f8-216d07bd43ae) | 반증 유지 | 롤별 공개 배송비·정수 판매 단위를 반영한 조건부 재계산 |
| KiNa_키나 | [25985165 NOMAL-2x2-ido-10-35](https://hackathon.savetax.now/#/submission/27eefe81-503f-40ae-9122-e3a097af754c) | 반증 유지 | 롤별 공개 배송비·정수 판매 단위를 반영한 조건부 재계산 |
| KiNa_키나 | [24996583 STRONG-4x4-NonSlip-JY-10-35](https://hackathon.savetax.now/#/submission/dd6f8d57-922d-4ca5-bf45-864848a60d9d) | 반증 유지 | 롤별 공개 배송비·정수 판매 단위를 반영한 조건부 재계산 |
| KiNa_키나 | [20930262 SJ8-200](https://hackathon.savetax.now/#/submission/f177934d-8da7-41bc-94ed-d8eaccca6925) | 반증 유지 | 정수 판매 단위의 끝수 비용 검토 |
| KiNa_키나 | [24242677 HLFD-20WASB](https://hackathon.savetax.now/#/submission/7e445a18-d208-406b-b6cb-e81acb91bf23) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [24310134 OEG-SL5126CB050](https://hackathon.savetax.now/#/submission/d91d2d4e-c302-4a1b-a9d7-939dee334a83) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [25552970 S63-15TG](https://hackathon.savetax.now/#/submission/3de90bbc-18fb-4f55-9fb2-9f429c2e7f24) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [25887230 Astra-C18](https://hackathon.savetax.now/#/submission/fc09e96d-8afd-4c95-aa49-ea4095bf20fa) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [25775998 OGH25](https://hackathon.savetax.now/#/submission/f02090ed-86d4-48ca-8a13-8d982958de04) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [24587726 AU360-A01](https://hackathon.savetax.now/#/submission/c2150467-02da-4e4b-82ed-5eff46b475df) | 새 반증 미입증·미등록 | 본문은 대체품과 비교 한계를 구별했다. 실제 판매 원문을 읽었으나 이번 조사 범위에서 새로 확정할 반증 근거를 얻지 못했다. 원품의 모든 세부 사양을 독립 검증한 것은 아니다. |
| KiNa_키나 | [24473535 TCT320LF](https://hackathon.savetax.now/#/submission/3a9306c6-d55c-4941-9d1b-710361bd53ce) | 새 반증 미입증·미등록 | 판매처의 표시 가격과 등·좌판, 팔걸이, 캐스터 및 접이식 구성에 관한 원제출의 대조를 읽었다. 치수 차이는 공개되어 있으며 미확인 세부 성능을 오류로 단정하지 않았다. |
| KiNa_키나 | [26151326 DT381B-226520](https://hackathon.savetax.now/#/submission/2206fa65-1c68-4cb0-a54b-be62cf909dcc) | 새 반증 미입증·미등록 | 완성 PC 판매 원문과 부품 추가 구성 가격을 읽었다. 원제출은 운영체제 미포함과 SSD·복구 솔루션의 차이를 밝혔다. PM9E1의 PCIe 5.0과 비교 SSD의 인터페이스 차이는 있으나, 실제 시스템의 링크 조건과 현재 선택 옵션까지 검증하지 못해 추가 성능 반증은 확정하지 않았다. |
| KiNa_키나 | [26063770 DT281-GD50E-002](https://hackathon.savetax.now/#/submission/d0f1b81d-5ebb-4175-8383-b6e60088912d) | 새 반증 미입증·미등록 | 완성 PC 판매 원문과 부품 추가 구성 가격을 읽었다. 원제출은 운영체제 미포함과 SSD·복구 솔루션의 차이를 밝혔다. PM9E1의 PCIe 5.0과 비교 SSD의 인터페이스 차이는 있으나, 실제 시스템의 링크 조건과 현재 선택 옵션까지 검증하지 못해 추가 성능 반증은 확정하지 않았다. |
| KiNa_키나 | [25148718 ASZ-7526HKP](https://hackathon.savetax.now/#/submission/eaa4e20f-44d1-4057-a5ef-8ed178d262b2) | 새 반증 미입증·미등록 | 완성 PC 판매 원문과 부품 추가 구성 가격을 읽었다. 원제출은 운영체제 미포함과 SSD·복구 솔루션의 차이를 밝혔다. PM9E1의 PCIe 5.0과 비교 SSD의 인터페이스 차이는 있으나, 실제 시스템의 링크 조건과 현재 선택 옵션까지 검증하지 못해 추가 성능 반증은 확정하지 않았다. |
| KiNa_키나 | [26152656 DG481-GC41-005](https://hackathon.savetax.now/#/submission/8b872628-9044-45b3-9c42-1dd4b69a21a7) | 새 반증 미입증·미등록 | 완성 PC 판매 원문과 부품 추가 구성 가격을 읽었다. 원제출은 운영체제 미포함과 SSD·복구 솔루션의 차이를 밝혔다. PM9E1의 PCIe 5.0과 비교 SSD의 인터페이스 차이는 있으나, 실제 시스템의 링크 조건과 현재 선택 옵션까지 검증하지 못해 추가 성능 반증은 확정하지 않았다. |
| KiNa_키나 | [26151311 DS381A-226500](https://hackathon.savetax.now/#/submission/264a9191-6355-4f03-b6cf-373a8a07f0c5) | 새 반증 미입증·미등록 | 완성 PC 판매 원문과 부품 추가 구성 가격을 읽었다. 원제출은 운영체제 미포함과 SSD·복구 솔루션의 차이를 밝혔다. PM9E1의 PCIe 5.0과 비교 SSD의 인터페이스 차이는 있으나, 실제 시스템의 링크 조건과 현재 선택 옵션까지 검증하지 못해 추가 성능 반증은 확정하지 않았다. |
| KiNa_키나 | [26063769 DT281-GD50E-001](https://hackathon.savetax.now/#/submission/9e3e198b-6e8c-43e1-a1f0-1c1fad45de8d) | 새 반증 미입증·미등록 | 완성 PC 판매 원문과 부품 추가 구성 가격을 읽었다. 원제출은 운영체제 미포함과 SSD·복구 솔루션의 차이를 밝혔다. PM9E1의 PCIe 5.0과 비교 SSD의 인터페이스 차이는 있으나, 실제 시스템의 링크 조건과 현재 선택 옵션까지 검증하지 못해 추가 성능 반증은 확정하지 않았다. |
| KiNa_키나 | [26060432 A5SC-3NBDF](https://hackathon.savetax.now/#/submission/d1a5385d-e198-4d84-92cd-0d0c9533c069) | 새 반증 미입증·미등록 | 완성 PC 판매 원문과 부품 추가 구성 가격을 읽었다. 원제출은 운영체제 미포함과 SSD·복구 솔루션의 차이를 밝혔다. PM9E1의 PCIe 5.0과 비교 SSD의 인터페이스 차이는 있으나, 실제 시스템의 링크 조건과 현재 선택 옵션까지 검증하지 못해 추가 성능 반증은 확정하지 않았다. |
| KiNa_키나 | [25257860 (MX)Flex 5260 Shelf](https://hackathon.savetax.now/#/submission/8064321d-5b04-491e-bbe3-52a567240221) | 새 반증 미입증·미등록 | TeciSoft의 16,894.77 USD, 5년 Essential 지원과 설치 서비스 표기를 읽었다. 96TB 원시 용량과 약 65TiB 유효 용량을 단순한 용량 불일치로 반증하지 않았다. 판매처는 국제배송을 지원하지만 목적지별 운임은 별도다. 한국 설치 서비스 적용 여부와 운임 금액… |
| KiNa_키나 | [22448211 KB100-12](https://hackathon.savetax.now/#/submission/0acfb208-d0f1-492f-b577-bf0696bfb2e4) | 새 반증 미입증·미등록 | KB100-12 12V 100Ah의 배터리파크 210,000원과 배터리마켓 221,000원을 읽었다. 확인한 범위에서 동일 모델과 가격에 관한 새 오류를 찾지 못했다. |
| KiNa_키나 | [24445466 Windows 11 Pro](https://hackathon.savetax.now/#/submission/de1c1b18-bfdc-4c12-ae03-18e3bfa23079) | 철회·등록 불가 | 철회된 제출로 반증 등록 대상이 아니다. 본문과 기존 반증을 보존했으며 새 공개 반증은 준비하지 않았다. |
| KiNa_키나 | [24445466 Windows 11 Pro](https://hackathon.savetax.now/#/submission/bd568d58-d02d-420f-bdb7-8d90a42dfff2) | 철회·등록 불가 | 철회된 제출로 반증 등록 대상이 아니다. 본문과 기존 반증을 보존했으며 새 공개 반증은 준비하지 않았다. |
| shine | [26094292 TI86-2326057](https://hackathon.savetax.now/#/submission/4a37e024-d244-4bb4-9a9e-3edf8bed4880) | 반증 유지 | 검증된 핵심 구성 누락: 조달 외장 RTX 그래픽카드가 비교 조립 구성에 없음 |
| shine | [24684435 (CN)SL-M4040ND](https://hackathon.savetax.now/#/submission/a67e1e0e-4d74-4b21-b00b-bc7284bacc5c) | 반증 유지 | 검증된 링크·인용 모순: 프린터 근거가 실제 의류 상품 페이지 |
| shine | [25822921 ITA176-T4732327](https://hackathon.savetax.now/#/submission/c47d1443-91e3-40c6-a987-516e3c32203b) | 새 반증 미입증·미등록 | 직접 판매 근거가 현재 가격비교 종료 공지로 열려 현재 가격·판매 구성 검증 불가. 접근실패만으로 원 제출 오류를 단정하지 않음 |
| shine | [25890504 B7M-UT16S1HN/R56](https://hackathon.savetax.now/#/submission/4c580577-c265-4c25-a99e-2f7f6907a33a) | 반증 유지 | 검증된 핵심 구성 누락: 조달 외장 RTX 그래픽카드가 비교 조립 구성에 없음 |
| shine | [25935428 TU2-RB5-506R55](https://hackathon.savetax.now/#/submission/1639b784-079d-4bf7-aa01-1c00bf3fcc00) | 반증 유지 | 검증된 핵심 구성 누락: 조달 외장 RTX 그래픽카드가 비교 조립 구성에 없음 |
| shine | [25148614 BMZ-7701CEI](https://hackathon.savetax.now/#/submission/e2359a87-ea88-42a0-8c5c-ba7b8989bded) | 반증 유지 | 검증된 구성액 증빙 누락: 완제품이라고 선언한 B 일부가 미입증 RAM·SSD·전원·케이스 예산 |
| shine | [26104727 TSB-9619000](https://hackathon.savetax.now/#/submission/878f2561-0535-4256-8756-bd234edf8a4b) | 반증 유지 | 검증된 구성액 증빙 누락: 완제품이라고 선언한 B 일부가 미입증 RAM·SSD·전원·케이스 예산 |
| shine | [25545996 PFOA-SC-SC-1C-3M(SM)](https://hackathon.savetax.now/#/submission/f17a4c62-5fca-404d-8f40-b3e879e1e11d) | 반증 유지 | 검증된 필수 납품범위 불일치: 공식 현장설치도 원품을 설치조정 없는 케이블 단품가와 비교 |
| shine | [25291291 AFC-LC/SC TYPE 3M(해킹방지)](https://hackathon.savetax.now/#/submission/035b024e-92f9-4500-8d9c-41d6e7b30dec) | 반증 유지 | 검증된 필수 납품범위 불일치: 공식 현장설치도 원품을 설치조정 없는 케이블 단품가와 비교 |
| shine | [25720092 KOLV050-SC](https://hackathon.savetax.now/#/submission/7103aba7-3d6f-4948-9f88-a373ab1bb087) | 반증 유지 | 검증된 LED 핵심 표시 성능 열위: P5/192×192를 P6.67/144×144와 1:1 비교 |
| shine | [26021584 SYS-L57SO-96A](https://hackathon.savetax.now/#/submission/f22e9fc2-b090-4c5e-8457-72826d72f446) | 반증 유지 | 검증된 LED 핵심 표시 성능 열위: P5.7 원품을 P6.67과 비교 |
| shine | [26166178 DW-O-AA](https://hackathon.savetax.now/#/submission/b07a270a-6b9a-43cb-b964-2bff0602b97d) | 반증 유지 | 검증된 출처 표기 불일치: EXW·배송 견적 원문을 연구자 산출 도착도 관측가로 등록 |
| shine | [25545995 PFOA-SC-SC-1C-3M(MM)](https://hackathon.savetax.now/#/submission/e32d1ed9-9a8e-4c50-8158-319ba181a0aa) | 새 반증 미입증·미등록 | 직접 판매 근거가 현재 가격비교 종료 공지로 열려 현재 가격·판매 구성 검증 불가. 접근실패만으로 원 제출 오류를 단정하지 않음 |
| shine | [25545975 PPGA-LC(APC)-1.5M(SM)](https://hackathon.savetax.now/#/submission/d23cb557-de34-42b8-b9a8-2639d089d5dc) | 새 반증 미입증·미등록 | 직접 판매 근거가 현재 가격비교 종료 공지로 열려 현재 가격·판매 구성 검증 불가. 접근실패만으로 원 제출 오류를 단정하지 않음 |
| shine | [26085546 TT-ISO39](https://hackathon.savetax.now/#/submission/d604f152-abb6-445d-980b-1f7da085ec29) | 반증 유지 | 검증된 출처 표기 불일치: EXW·배송 견적 원문을 연구자 산출 도착도 관측가로 등록 |
| shine | [25744130 O1010-39TG-W](https://hackathon.savetax.now/#/submission/9dfca16e-4ae9-49d5-a3ab-6bca28205eb9) | 반증 유지 | 검증된 출처 표기 불일치: EXW·배송 견적 원문을 연구자 산출 도착도 관측가로 등록 |
| shine | [25471481 P2SG-NMG-30P](https://hackathon.savetax.now/#/submission/437a42c9-ae23-4b9c-8b90-cdac3fb1a5f2) | 반증 유지 | 검증된 출처 표기 불일치: EXW·배송 견적 원문을 연구자 산출 도착도 관측가로 등록 |
| shine | [26085654 OPT-HP-SC-1.5M](https://hackathon.savetax.now/#/submission/662183cd-4979-4fc5-8330-fc247af072eb) | 새 반증 미입증·미등록 | 직접 판매 근거가 현재 가격비교 종료 공지로 열려 현재 가격·판매 구성 검증 불가. 접근실패만으로 원 제출 오류를 단정하지 않음 |
| shine | [25038548 (CN)ROE-S20KM](https://hackathon.savetax.now/#/submission/fddeeb1e-bdb2-4acd-8edc-19e787bc3dfa) | 새 반증 미입증·미등록 | 직접 판매 근거가 현재 가격비교 종료 공지로 열려 현재 가격·판매 구성 검증 불가. 접근실패만으로 원 제출 오류를 단정하지 않음 |
| shine | [25291290 AFC-LC/SC TYPE 5M(해킹방지)](https://hackathon.savetax.now/#/submission/26356fe5-b6ea-465d-80de-c8f3d1e90536) | 새 반증 미입증·미등록 | 직접 판매 근거가 현재 가격비교 종료 공지로 열려 현재 가격·판매 구성 검증 불가. 접근실패만으로 원 제출 오류를 단정하지 않음 |
| shine | [25291293 A-FC-LC/SC TYPE 1M(해킹방지)](https://hackathon.savetax.now/#/submission/47d15bf8-64dc-4937-ad39-652fda5256c2) | 새 반증 미입증·미등록 | 직접 판매 근거가 현재 가격비교 종료 공지로 열려 현재 가격·판매 구성 검증 불가. 접근실패만으로 원 제출 오류를 단정하지 않음 |
| shine | [25720095 KILV025-M](https://hackathon.savetax.now/#/submission/81f011e5-c247-4f1d-b065-aaf6d56011e7) | 반증 유지 | 검증된 면적·수량 오류: 1920×640 완제품 1대에 640×480 캐비닛 1대 가격 적용 |
| shine | [25545981 PPGA-SC-1.5M(SM)](https://hackathon.savetax.now/#/submission/0689a900-c0d5-41e4-9d2b-7b8cf99e81b9) | 반증 유지 | 검증된 광케이블 선택 규격 불일치: 1.5m 원품에 1m SC-SC 상품가 적용 |
| shine | [25545979 PPGA-LC-1.5M(SM)](https://hackathon.savetax.now/#/submission/4b86fefa-0d80-46af-a644-7d05a85c1dfe) | 반증 유지 | 검증된 광케이블 선택 규격 불일치: 1.5m 원품에 1m SC-SC 상품가 적용 |
| shine | [25808970 (CN)PT-VGZ821K](https://hackathon.savetax.now/#/submission/51fe134b-1f22-480c-833b-ad458d716a09) | 새 반증 미입증·미등록 | 원품 PT-VGZ821K와 대체 PT-VMZ82는 8000ANSI lm·WUXGA·LCD·레이저 핵심 성능이 대체로 대응. 동일 하드웨어/조달 파생 관계는 제조사 매핑으로 확인되지 않았으나 모델 차이만으로 반증하지 않음 |
| shine | [24516873 HP-FPT-SC/PC-S](https://hackathon.savetax.now/#/submission/08097280-4e18-4f4b-b1a2-0cce6b77046f) | 반증 유지 | 검증된 광케이블 선택 규격 불일치: 1.5m 원품에 1m SC-SC 상품가 적용 |
| shine | [24528628 AhnLab EPP Management 1.0 SP1](https://hackathon.savetax.now/#/submission/02afddd6-f01e-49f9-8e77-a06e8189da47) | 반증 유지 | 검증된 라이선스 유형·VAT 오류: 갱신/VAT 별도를 본품/VAT 포함 단가로 사용 |
| shine | [25789425 HH447S5N](https://hackathon.savetax.now/#/submission/35d532b0-95a2-4920-b7bd-826f2ca48579) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25803975 S14-B741651V0](https://hackathon.savetax.now/#/submission/0dce3f2d-9065-41ce-8780-6ef8584501be) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25661572 KR176-T4416220](https://hackathon.savetax.now/#/submission/6dde2372-4ac3-4eed-bf15-0908a51370a0) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25527971 X3448S5N](https://hackathon.savetax.now/#/submission/582f30d1-0444-4f48-b17b-0ae60142cbae) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25586019 MI4EKD-4600BA](https://hackathon.savetax.now/#/submission/bbf22ba4-f341-4d19-83c3-f9805d9fc48a) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25792439 JA-144F5S2H](https://hackathon.savetax.now/#/submission/e08bc24d-5afa-48b6-9dbd-f161ed5cab84) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25554358 NY-E144SI00](https://hackathon.savetax.now/#/submission/5a5a5cc6-7181-4c04-97cc-44073ef51434) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25586018 MI4EKD-4640BA](https://hackathon.savetax.now/#/submission/04bf485b-7007-4d9a-aa8f-ff9dfad1f4c7) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25776526 SD110-GRRB25S1M](https://hackathon.savetax.now/#/submission/fef6e684-c9bf-4f57-9ec5-d9acf8267bfc) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25770760 HSB4-BX50P0](https://hackathon.savetax.now/#/submission/fa395e02-f011-4072-b9e4-3a9c6cac8c27) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25776537 TD210-GRRB25S1M](https://hackathon.savetax.now/#/submission/6827610e-59d5-4884-9c58-39fe8a14c51a) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25797444 CM4-E41-Q0002](https://hackathon.savetax.now/#/submission/bbdcb09d-8713-4bd5-a937-362f82ccd06a) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [26179352 GLISX025](https://hackathon.savetax.now/#/submission/bdb5c220-3e61-460e-be3f-86b750e9b609) | 반증 유지 | 검증된 출처 표기 불일치: EXW·배송 견적 원문을 연구자 산출 도착도 관측가로 등록 |
| shine | [25723498 DLUX-S2.5](https://hackathon.savetax.now/#/submission/482aef56-f39d-4751-a600-8a18d937c2eb) | 반증 유지 | 검증된 출처 표기 불일치: EXW·배송 견적 원문을 연구자 산출 도착도 관측가로 등록 |
| shine | [25991497 RAL-S250](https://hackathon.savetax.now/#/submission/d466ac11-d0b0-4961-94e6-d2c33ca7700e) | 반증 유지 | 검증된 출처 표기 불일치: EXW·배송 견적 원문을 연구자 산출 도착도 관측가로 등록 |
| shine | [25493416 MPC-X147R32S512V407](https://hackathon.savetax.now/#/submission/d05019f5-97b2-4110-946b-67c7b8c65faa) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [26111309 T15-B873212V6](https://hackathon.savetax.now/#/submission/3f247257-59ab-4589-86bd-5fe76d8f2d2b) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25493417 MPC-X147R32S1H2V407](https://hackathon.savetax.now/#/submission/5162702f-43b6-4739-a1cd-b3a98abad170) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25803994 T14-B773251V7](https://hackathon.savetax.now/#/submission/039b8e87-f466-40cd-bf43-597e0fe55655) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [26149858 DT387C-26252H](https://hackathon.savetax.now/#/submission/89d7f0e5-f7a5-49b5-b60a-cee319bf9ff8) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25296577 WDM-I149S10ET-R6](https://hackathon.savetax.now/#/submission/50e31fab-ff76-4839-b636-e3f54ddcc6a3) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [26121861 JAB-U65G21T2TR57](https://hackathon.savetax.now/#/submission/cc2ae1e1-c948-4c0e-a79a-1d0bd508921c) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25822927 IT179-B4732329](https://hackathon.savetax.now/#/submission/adc386de-b155-47d7-b6b4-c0f343baec3f) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25694288 J-U94F1T2TSA](https://hackathon.savetax.now/#/submission/d3a30c6f-4336-4b6c-8db4-fbac79afec7f) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25553841 PHANTOM-D007](https://hackathon.savetax.now/#/submission/085f5812-9926-4cd2-8028-8d792ba04e53) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25613351 OTS-29001](https://hackathon.savetax.now/#/submission/b78e12a3-2061-4621-a292-6d6bf5dd11bd) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25845488 T-DT594T1M64-P1R58](https://hackathon.savetax.now/#/submission/6d45fd4b-df4a-429e-8a0a-dd1c54fc71a2) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [26104728 TBZ-E8EB458](https://hackathon.savetax.now/#/submission/d945df39-f761-4637-aba7-ba90d206b801) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25934611 NEWTON-C9N90-L01](https://hackathon.savetax.now/#/submission/29960fe4-f059-4c58-8060-f73e0f319d5c) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [26111317 T15-B873250V6](https://hackathon.savetax.now/#/submission/7d239202-6b9a-42d7-82cb-632593d896dc) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25845480 T-DT598T2M128-P1R58](https://hackathon.savetax.now/#/submission/c2242357-1ab5-45c1-b188-69f2d44e5269) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [25935404 TU2-RB9-523R56](https://hackathon.savetax.now/#/submission/2954e2fb-5597-48b0-a3b8-446efbcf5cbf) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [26081320 RBD9-M5B32](https://hackathon.savetax.now/#/submission/1a066142-7f40-444c-b458-818782392e05) | 반증 유지 | 검증된 구성·단위 오류: 완제품 조달 금액에서 CPU 부품 가격만 차감 |
| shine | [26082630 스타리아 HEV 투어러 11인승 모던 2026년](https://hackathon.savetax.now/#/submission/61b5b166-6e17-486c-89b8-01f2026683b0) | 철회·등록 불가 | 철회 제출이므로 현행 API 규칙상 반증 등록 대상 아님 |
| WISP | [25543301 FGFL-30050-002](https://hackathon.savetax.now/#/submission/9868e12b-d926-44aa-9f80-0a20f76de825) | 새 반증 미입증·미등록 | 원품 개별 규격서의 300W·34,500lm와 제조사 카탈로그의 해당 모델·물품번호를 확인했다. 에누리의 두 실제 판매처는 포인트라이팅·잇이즈LED로 연결되지만 스마트스토어 HTTP429·브라우저 오류 화면 때문에 실제 300W 판매품의 정격 광속·구성을 읽지 못했다. 읽기 실패를 오류… |
| WISP | [24279134 GC-150AE1-AF](https://hackathon.savetax.now/#/submission/e5c9b90d-952d-4a19-af37-208e4083a9b1) | 새 반증 미입증·미등록 | 원품의 개별 제원과 실제 Airtec 정격표를 직접 대조했다. 원품과 대체품의 명시 정격 광속은17,250lm로 같으므로 전력×효율을 곱해 원품의 광속이 더 크다고 바꾸어 주장하지 않는다. 형상·색온도·효율 또는 특허 구조의 차이가 있어도 실제 요구조건상 대체 불가능함을 입증하지 못한 … |
| WISP | [24733610 JJFLD24-150GE](https://hackathon.savetax.now/#/submission/41589762-6a78-4d22-963b-d3fa452d7c74) | 새 반증 미입증·미등록 | 원품의 개별 제원과 실제 Airtec 정격표를 직접 대조했다. 원품과 대체품의 명시 정격 광속은17,250lm로 같으므로 전력×효율을 곱해 원품의 광속이 더 크다고 바꾸어 주장하지 않는다. 형상·색온도·효율 또는 특허 구조의 차이가 있어도 실제 요구조건상 대체 불가능함을 입증하지 못한 … |
| WISP | [25256538 SVB-FL150-L](https://hackathon.savetax.now/#/submission/4ee4b045-21fc-42db-b968-ff47ebb19f87) | 새 반증 미입증·미등록 | 원품의 개별 제원과 실제 Airtec 정격표를 직접 대조했다. 원품과 대체품의 명시 정격 광속은17,250lm로 같으므로 전력×효율을 곱해 원품의 광속이 더 크다고 바꾸어 주장하지 않는다. 형상·색온도·효율 또는 특허 구조의 차이가 있어도 실제 요구조건상 대체 불가능함을 입증하지 못한 … |
| WISP | [24827045 EEFC9-150DS](https://hackathon.savetax.now/#/submission/96135e35-8603-4b90-8af4-6eab13ce9d90) | 새 반증 미입증·미등록 | 원품의 개별 제원과 실제 Airtec 정격표를 직접 대조했다. 원품과 대체품의 명시 정격 광속은17,250lm로 같으므로 전력×효율을 곱해 원품의 광속이 더 크다고 바꾸어 주장하지 않는다. 형상·색온도·효율 또는 특허 구조의 차이가 있어도 실제 요구조건상 대체 불가능함을 입증하지 못한 … |
| WISP | [25322349 JMFLLP-150](https://hackathon.savetax.now/#/submission/6745e178-d065-4076-b62a-f0747525a717) | 새 반증 미입증·미등록 | 원품 공식 PDF의 해당 모델·150W·255×255×208mm·원형 및 필립스 Xitanium150W 컨버터 구성을 읽었다. PDF 텍스트에는 수치 광속·광효율이 확인되지 않았다. 실제 Airtec은17,250lm·115lm/W이나 원품의 대응 출력과 핵심 차이 증명이 부족해 새 반증… |
| WISP | [25321310 P-FHM150UH1-S857](https://hackathon.savetax.now/#/submission/8a1ab071-6e65-4e5a-9edb-0df35a596e06) | 반증 유지 | 제조사와 실제 판매 정격표의 광속·광효율 차이 |
| WISP | [23938175 GI-150LC17](https://hackathon.savetax.now/#/submission/9ab3181e-b656-4209-90dd-eba801443d99) | 새 반증 미입증·미등록 | 원품의 개별 제원과 실제 Airtec 정격표를 직접 대조했다. 원품과 대체품의 명시 정격 광속은17,250lm로 같으므로 전력×효율을 곱해 원품의 광속이 더 크다고 바꾸어 주장하지 않는다. 형상·색온도·효율 또는 특허 구조의 차이가 있어도 실제 요구조건상 대체 불가능함을 입증하지 못한 … |
| WISP | [24094041 W-FL150-NE](https://hackathon.savetax.now/#/submission/535091c8-909a-4915-b730-2a58f8c99687) | 새 반증 미입증·미등록 | 원품의 개별 제원과 실제 Airtec 정격표를 직접 대조했다. 원품과 대체품의 명시 정격 광속은17,250lm로 같으므로 전력×효율을 곱해 원품의 광속이 더 크다고 바꾸어 주장하지 않는다. 형상·색온도·효율 또는 특허 구조의 차이가 있어도 실제 요구조건상 대체 불가능함을 입증하지 못한 … |
| WISP | [24906272 IEG-GOG35BB150](https://hackathon.savetax.now/#/submission/a07917e7-25d5-47f0-92d8-ae6f9601ec13) | 반증 유지 | 원품 정격 광속과 실제 판매품 정격 광속의 차이 |
| WISP | [25543302 FLDF-15057-001](https://hackathon.savetax.now/#/submission/4f7e4a3b-321b-41e2-b29c-7dc381023478) | 공개 정정·주장 철회 | 공통 카탈로그와 모델별 원규격의 충돌을 확인해 앞선 관련 주장을 공개 정정·철회했다. |
| WISP | [25543237 FLCC-15057-002](https://hackathon.savetax.now/#/submission/2d89c10e-e44b-4af6-9a37-219741fb3918) | 공개 정정·주장 철회 | 공통 카탈로그와 모델별 원규격의 충돌을 확인해 앞선 관련 주장을 공개 정정·철회했다. |
| WISP | [25326120 NL-EA-PLC150](https://hackathon.savetax.now/#/submission/6e0682a5-5836-49cb-9ed1-a83d8c74d27c) | 새 반증 미입증·미등록 | 원품의 개별 제원과 실제 Airtec 정격표를 직접 대조했다. 원품과 대체품의 명시 정격 광속은17,250lm로 같으므로 전력×효율을 곱해 원품의 광속이 더 크다고 바꾸어 주장하지 않는다. 형상·색온도·효율 또는 특허 구조의 차이가 있어도 실제 요구조건상 대체 불가능함을 입증하지 못한 … |
| WISP | [25312520 EPDB150DF-S857](https://hackathon.savetax.now/#/submission/1845c701-0d38-457b-b894-87778854d457) | 반증 유지 | 정격 광속·광효율의 실제 차이 |
| WISP | [25321318 P-HSP150UK-S857](https://hackathon.savetax.now/#/submission/2eb36706-b396-4535-8371-a37ef9c44e68) | 반증 유지 | 정격 광속·광효율의 실제 차이 |
| WISP | [25048582 KKL-SP-150MRN](https://hackathon.savetax.now/#/submission/aa86947b-589b-4eb9-bf2b-41b840e1f516) | 새 반증 미입증·미등록 | 원품의 개별 제원과 실제 Airtec 정격표를 직접 대조했다. 원품과 대체품의 명시 정격 광속은17,250lm로 같으므로 전력×효율을 곱해 원품의 광속이 더 크다고 바꾸어 주장하지 않는다. 형상·색온도·효율 또는 특허 구조의 차이가 있어도 실제 요구조건상 대체 불가능함을 입증하지 못한 … |
| WISP | [25543571 (CN)83GWA006KR](https://hackathon.savetax.now/#/submission/fdeca55d-d066-45c6-a022-12b636bcdd1d) | 반증 유지 | 원품 Gigabit Ethernet과 Windows Pro의 비교 구성 대응 |
| WISP | [25719385 HDJN P75QMFBB](https://hackathon.savetax.now/#/submission/56e78e53-68af-473a-a271-5a3460f2ea49) | 반증 유지 | 실제 원규격과 비교품의 필수 구성·핵심 사양 차이 |
| WISP | [25910042 KCQ86OPS](https://hackathon.savetax.now/#/submission/6d0cc1e5-3873-4d52-ab71-88545940e9a1) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [25920580 7PAN5-RK86Q OPS](https://hackathon.savetax.now/#/submission/8f88c2e7-46ab-4519-a914-4385d878a6a8) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [26008547 7PAN5-RK86Q R2](https://hackathon.savetax.now/#/submission/23f1009a-dcf4-42f4-b3f9-c2eec7e15459) | 반증 유지 | 실제 원규격과 비교품의 필수 구성·핵심 사양 차이 |
| WISP | [26152668 DT281-GC51-003](https://hackathon.savetax.now/#/submission/fa387cef-ec76-4cc9-a8bb-cf6bf47427ee) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [25569863 A3TC-5NBDN](https://hackathon.savetax.now/#/submission/24449fe7-3822-42be-8f9e-b4a77e1b623e) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [23487709 (CN)RDS-270HV](https://hackathon.savetax.now/#/submission/62cb4601-be66-4f7e-81be-ab97a6c7064e) | 새 반증 미입증·미등록 | 크기·FHD·입력단자·밝기250·응답속도 및 스탠드에서 공개 사양상 주요 대응을 확인. 동적 명암비만 높은 원품은 동적 값과 일반 대비1000:1을 섞어 열위로 판정하지 않음 |
| WISP | [25225675 (CN)TRM-24BPS](https://hackathon.savetax.now/#/submission/6ad00773-9f78-4ad2-9051-4b58061ce638) | 반증 유지 | 검증된 핵심 사양 대응 오류: 밝기·명암비·주사율 중 원품보다 낮은 공개 사양을 같은 사양 이상으로 확정 |
| WISP | [24795633 (CN)WM2700EP](https://hackathon.savetax.now/#/submission/d484f685-2d02-4285-a38c-2507040c4584) | 반증 유지 | 검증된 핵심 사양 대응 오류: 밝기·명암비·주사율 중 원품보다 낮은 공개 사양을 같은 사양 이상으로 확정 |
| WISP | [26045754 (CN)AM24KDS](https://hackathon.savetax.now/#/submission/b8b744ea-77ab-42e0-988d-77d21c46f9ee) | 새 반증 미입증·미등록 | 크기·FHD·입력단자·밝기250·응답속도 및 스탠드에서 공개 사양상 주요 대응을 확인. 동적 명암비만 높은 원품은 동적 값과 일반 대비1000:1을 섞어 열위로 판정하지 않음 |
| WISP | [25642049 Wemade 24WMS](https://hackathon.savetax.now/#/submission/620fae53-946f-4852-8cc3-3ccd1a9c9789) | 반증 유지 | 검증된 핵심 사양 대응 오류: 밝기·명암비·주사율 중 원품보다 낮은 공개 사양을 같은 사양 이상으로 확정 |
| WISP | [25528091 (CN)UTO-2703](https://hackathon.savetax.now/#/submission/811a9a61-8c74-449e-977c-e1697a60b916) | 반증 유지 | 검증된 핵심 사양 대응 오류: 밝기·명암비·주사율 중 원품보다 낮은 공개 사양을 같은 사양 이상으로 확정 |
| WISP | [24118771 (CN)NYL6050AM](https://hackathon.savetax.now/#/submission/7a6788d0-a83f-4c3e-b47d-f8dd02f7d270) | 반증 유지 | 검증된 핵심 사양 대응 오류: 밝기·명암비·주사율 중 원품보다 낮은 공개 사양을 같은 사양 이상으로 확정 |
| WISP | [25113831 (CN)AM27KH](https://hackathon.savetax.now/#/submission/bb034d1f-dea8-4fc1-9ede-1bbb2e83e539) | 반증 유지 | 검증된 핵심 사양 대응 오류: 밝기·명암비·주사율 중 원품보다 낮은 공개 사양을 같은 사양 이상으로 확정 |
| WISP | [24974696 (CN)T1M-B270DP](https://hackathon.savetax.now/#/submission/4d672e21-8cf9-46ae-b790-59837cefd252) | 새 반증 미입증·미등록 | 크기·FHD·입력단자·밝기250·응답속도 및 스탠드에서 공개 사양상 주요 대응을 확인. 동적 명암비만 높은 원품은 동적 값과 일반 대비1000:1을 섞어 열위로 판정하지 않음 |
| WISP | [25597102 (CN)L27S1WDHM](https://hackathon.savetax.now/#/submission/4319f5fe-4989-478e-b0fe-923020718880) | 반증 유지 | 검증된 핵심 사양 대응 오류: 밝기·명암비·주사율 중 원품보다 낮은 공개 사양을 같은 사양 이상으로 확정 |
| WISP | [25470293 hybrid-Q6101A](https://hackathon.savetax.now/#/submission/8ef3ac7e-9777-401b-b96b-e5d113947ecc) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [26036767 HDJN P65QMFB](https://hackathon.savetax.now/#/submission/55b10381-dccd-404f-9e6c-5e20129a4ce3) | 반증 유지 | 실제 원규격과 비교품의 필수 구성·핵심 사양 차이 |
| WISP | [24735886 (CN)RDS-240NT](https://hackathon.savetax.now/#/submission/8ac83827-644e-4570-af40-1334ee2cec8a) | 반증 유지 | 검증된 핵심 사양 대응 오류: 터치 입력 미대응 |
| WISP | [25678003 (CN)KRM-HD270DPO](https://hackathon.savetax.now/#/submission/d04b7571-888f-4fe3-9e12-bc69d6f1c412) | 반증 유지 | 검증된 핵심 사양 대응 오류: 밝기·명암비·주사율 중 원품보다 낮은 공개 사양을 같은 사양 이상으로 확정 |
| WISP | [25484710 (CN)6860V](https://hackathon.savetax.now/#/submission/9f9dd681-3cc5-4f62-bd45-a067ba2a4005) | 새 반증 미입증·미등록 | 크기·FHD·입력단자·밝기250·응답속도 및 스탠드에서 공개 사양상 주요 대응을 확인. 동적 명암비만 높은 원품은 동적 값과 일반 대비1000:1을 섞어 열위로 판정하지 않음 |
| WISP | [25470272 hybrid-Q6100A](https://hackathon.savetax.now/#/submission/8e896527-0fca-4c2c-9ded-5dbcd9715635) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [26028599 STG-DL65](https://hackathon.savetax.now/#/submission/b0d345db-074b-4e60-883c-f1944a6341bf) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25484711 (CN)6860VP](https://hackathon.savetax.now/#/submission/72da1888-5dfd-4af7-86d8-7dbd13be2609) | 새 반증 미입증·미등록 | 크기·FHD·입력단자·밝기250·응답속도 및 스탠드에서 공개 사양상 주요 대응을 확인. 동적 명암비만 높은 원품은 동적 값과 일반 대비1000:1을 섞어 열위로 판정하지 않음 |
| WISP | [26031139 STG-Qtra65](https://hackathon.savetax.now/#/submission/8d2de34b-d6bc-4abe-8414-10561cc26e8e) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25470295 hybrid-Q6101B](https://hackathon.savetax.now/#/submission/ffb060ee-8494-4d8d-b723-6ea36af1152c) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25567307 HCBQ-CREMETA86Z35](https://hackathon.savetax.now/#/submission/d3b67461-99b2-4349-9d4a-7bae521823d8) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [25887123 TB-OH86TP](https://hackathon.savetax.now/#/submission/d4e3f616-c422-41b4-b0fd-0e33df268317) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [26057140 A8GC-5XTNT](https://hackathon.savetax.now/#/submission/9a8eca3d-372d-4496-95da-c93950d89418) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25470284 hybrid-Q8100A](https://hackathon.savetax.now/#/submission/e33dcef7-6411-489f-9673-202929788eec) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25516259 EP-QY86C](https://hackathon.savetax.now/#/submission/7ed34e5f-1fce-4c2c-9d33-31a998c94cae) | 반증 유지 | 모델별 최종 원규격과 판매품의 영상·음성 입력장치 구성 차이 |
| WISP | [25284443 NQN86CONF](https://hackathon.savetax.now/#/submission/2d5d7b86-0fd0-47d7-b55e-270a390188ee) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [26036771 HDJN P86QMFB](https://hackathon.savetax.now/#/submission/8fb387a7-6f42-41f8-b4b8-185094c7372b) | 반증 유지 | 실제 원규격과 비교품의 필수 구성·핵심 사양 차이 |
| WISP | [25910038 CCBEK-5486G4](https://hackathon.savetax.now/#/submission/b54dbe92-f67e-476e-a060-29cd5a43af5e) | 반증 유지 | 모델별 최종 원규격과 판매품의 영상·음성 입력장치 구성 차이 |
| WISP | [25284444 NQN86PT](https://hackathon.savetax.now/#/submission/b7941739-123d-49c5-945d-df8061eff068) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [25825824 EB-QO86CT](https://hackathon.savetax.now/#/submission/0d5b2529-3a78-4acc-9e03-521b0c64f426) | 반증 유지 | 모델별 최종 원규격과 판매품의 영상·음성 입력장치 구성 차이 |
| WISP | [25304403 NRB-IFPD-8613MP](https://hackathon.savetax.now/#/submission/a4b01b35-30df-4145-ac9c-0f2c13d67ce9) | 반증 유지 | 모델별 최종 원규격과 판매품의 영상·음성 입력장치 구성 차이 |
| WISP | [25516258 EP-QX86C](https://hackathon.savetax.now/#/submission/9182b4ed-e474-42cb-bd07-91c17a23c251) | 반증 유지 | 모델별 최종 원규격과 판매품의 영상·음성 입력장치 구성 차이 |
| WISP | [25910040 HCB-5286C4](https://hackathon.savetax.now/#/submission/d788afa9-caa4-4ada-8a03-9ee36fe71d2b) | 반증 유지 | 모델별 최종 원규격과 판매품의 영상·음성 입력장치 구성 차이 |
| WISP | [26031133 STG-QL86](https://hackathon.savetax.now/#/submission/6e19c939-f7c7-41b0-af38-f7464bd9a679) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25887122 TB-OH86T](https://hackathon.savetax.now/#/submission/55ac65cc-92d8-47af-9e44-645bc4b49908) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [26036773 HDJN P86QMAB](https://hackathon.savetax.now/#/submission/29deb268-05ed-4168-b1ab-2d565a825267) | 반증 유지 | 실제 원규격과 비교품의 필수 구성·핵심 사양 차이 |
| WISP | [25470299 hybrid-Q7101B](https://hackathon.savetax.now/#/submission/f401f16d-cfdb-4651-ab83-9edb94f5696a) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25470305 hybrid-Q8101A](https://hackathon.savetax.now/#/submission/777a905d-ed39-4200-b302-f52276f1e1f5) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25284441 NQN86ZL](https://hackathon.savetax.now/#/submission/9564eee2-3bd8-42d2-af67-2c516c169d60) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [25470308 hybrid-Q8103B](https://hackathon.savetax.now/#/submission/f37dc1fb-8b13-4f28-bced-f202bed29190) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25442405 HCB-5286G1](https://hackathon.savetax.now/#/submission/6644a47d-6429-45f7-90a1-15f9b5ba7331) | 반증 유지 | 제조사·공식 원규격과 비교품의 기본 구성 차이 |
| WISP | [25208788 HDP E86UPGI](https://hackathon.savetax.now/#/submission/08adaa9a-8614-41f7-8865-7e96b786d9cc) | 반증 유지 | 제조사·공식 원규격과 비교품의 기본 구성 차이 |
| WISP | [25717114 TB-GH86-TVC](https://hackathon.savetax.now/#/submission/5b2b8f26-168a-4c0e-a64f-6d5fbdbc662b) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [25370619 NB-K312E40-OB57-BH](https://hackathon.savetax.now/#/submission/bf7c04c8-e376-4279-8423-7e0fd1060dc7) | 새 반증 미입증·미등록 | 소노 실제 상품과 상세 이미지를 직접 읽었다. 대체품의 40W·5,120lm 이상·128lm/W 이상·5700K·Ra80 이상은 원품 4,400lm보다 밝으며 원품의 명시 광효율에도 미달하지 않는다. 높이는24.3mm로 원품22mm와 차이가 있으나 치수 차이만으로 핵심 용도를 충족하지 … |
| WISP | [24790063 KKL-40EM1280N](https://hackathon.savetax.now/#/submission/cc1b2f79-493f-447b-a0c0-2a845d9fa769) | 새 반증 미입증·미등록 | 소노 실제 상품과 상세 이미지를 직접 읽었다. 대체품의 40W·5,120lm 이상·128lm/W 이상·5700K·Ra80 이상은 원품 4,400lm보다 밝으며 원품의 명시 광효율에도 미달하지 않는다. 높이는24.3mm로 원품22mm와 차이가 있으나 치수 차이만으로 핵심 용도를 충족하지 … |
| WISP | [25920578 7PAN5-RK86Q](https://hackathon.savetax.now/#/submission/f5417b62-4557-435f-965c-8b9c97fa3d3c) | 반증 유지 | 실제 원규격과 비교품의 필수 구성·핵심 사양 차이 |
| WISP | [25910041 KCQ86](https://hackathon.savetax.now/#/submission/bffa90dc-d4d1-46f8-b176-983eeeb867b2) | 반증 유지 | 실제 원품의 카메라·마이크와 대체품 기본 구성의 차이 |
| WISP | [25719381 HDJN P86QMFBA](https://hackathon.savetax.now/#/submission/818b680a-3123-47cd-9d8c-34517bcbab97) | 반증 유지 | 실제 원규격과 비교품의 필수 구성·핵심 사양 차이 |
| WISP | [25567305 HCBQ-CREMETA8600Z35](https://hackathon.savetax.now/#/submission/f9eb50b0-c852-4045-8e28-456b6d396328) | 반증 유지 | 원품 OPS·영상·음성 입력장치와 대체품 기본 구성의 차이 |
| WISP | [25442404 HCB-5286G](https://hackathon.savetax.now/#/submission/6570c060-e84f-42ee-94fb-b476603cd5f7) | 반증 유지 | 제조사·공식 원규격과 비교품의 기본 구성 차이 |
| WISP | [25719380 HDJN P86QMABB](https://hackathon.savetax.now/#/submission/02e6391a-2f1f-4594-8bb5-e776e664a11e) | 반증 유지 | 실제 원규격과 비교품의 필수 구성·핵심 사양 차이 |
| WISP | [25208787 HDP E86UPCI](https://hackathon.savetax.now/#/submission/003eb5b1-a054-44bb-b3df-f630d16e3074) | 반증 유지 | 제조사·공식 원규격과 비교품의 기본 구성 차이 |
| WISP | [25616727 DSC100F](https://hackathon.savetax.now/#/submission/a08191e4-3bfc-4af8-82f7-a1e77e4ffcaf) | 새 반증 미입증·미등록 | 카나레 2S7F 스피콘 100m 릴의 498,000원 상품이 검색 원문에 있습니다. 판매자의 G마켓 연관상품 08도 100m에 498,000원을 표시하므로, 짧은 기본 길이의 가격을 잘못 인용했다는 반증은 성립하지 않습니다. |
| WISP | [24150630 VXUC6-100M](https://hackathon.savetax.now/#/submission/1ce28eda-410d-41b1-84e5-bb931112ee22) | 새 반증 미입증·미등록 | CAT.6·RJ45-RJ45·100m 완제품인 NM-FCS6100은 원품의 공개 핵심 규격에 대응합니다. 현재 다나와 배송 포함 106,680원은 제출 단가 106,940원보다 낮아 가격 오류를 뒷받침하지 않습니다. |
| WISP | [25479985 GT-UPC-02H](https://hackathon.savetax.now/#/submission/b91026ed-35b7-4c7a-a005-a5ac1266ae00) | 새 반증 미입증·미등록 | 에누리 원문의 가가전자 LS전선 제작 블루 2.5m CAT.6 UTP는 5,207원·배송비 3,000원 별도로, 제출 인용과 일치합니다. 원품의 RJ45·CAT.6 UTP·2.5m와 같은 범주이며, 제출도 배송비 별도라고 공개했습니다. |
| WISP | [25441611 OPC-3M-6A](https://hackathon.savetax.now/#/submission/c012b36e-2dbd-431e-bf39-1be2761ba525) | 새 반증 미입증·미등록 | 원품과 대체 NM-FC6A30은 CAT.6A UTP·RJ45·3m라는 핵심 규격이 대응합니다. 제출자가 현장설치도와 단순 연결용 완제품의 비교 범위를 공개했으므로, 설치라는 단어만으로 누락 비용을 확정하지 않았습니다. |
| WISP | [26178921 DT361B-416500](https://hackathon.savetax.now/#/submission/800d3a7c-66a0-44e3-bf4c-e2cf706f5cb3) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [25859212 TNH-D11900](https://hackathon.savetax.now/#/submission/0e1ac1e9-658b-4124-9933-19747c3064bf) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [25784867 IYU-M45J9](https://hackathon.savetax.now/#/submission/25316a78-474e-4081-be4f-b0612db11661) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [26023413 A4UM-3NBDS](https://hackathon.savetax.now/#/submission/336b97f3-724f-41cf-a474-eaf18033d8dc) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [26173346 A4TC-5NBDN](https://hackathon.savetax.now/#/submission/f355690a-98c0-41ee-8ee2-499dbfbdda90) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [26166268 DT281-GC71-004](https://hackathon.savetax.now/#/submission/e8f59af9-332a-4473-acc5-09893ddbf73b) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [26152655 DG481-GC31-001](https://hackathon.savetax.now/#/submission/e23dbc4b-1fbf-4f40-908f-6382ed88dbbc) | 새 반증 미입증·미등록 | 주요 연산·메모리·저장장치 구성은 원시 속성과 대체 완제품의 본문 사양이 대응한다. 폼팩터·전원·입력장치·복구 솔루션·AS 차이를 본문이 이미 공개했다. 단순 전원 정격이나 외형 차이만으로 실제 성능 부족을 단정하지 않았다. 판매 상세를 확인하지 못해 부속품 포함 범위와 가격의 최종 적… |
| WISP | [23206109 SFC8000G](https://hackathon.savetax.now/#/submission/414600f0-4a26-434f-9deb-b09bc17a3d2a) | 새 반증 미입증·미등록 | SOLTECH SFC8000G의 모델·기가비트 8포트·관리형 사양과 제출 가격 531,000원·무료배송이 현재 원문에서 일치합니다. |
| WISP | [23913976 (CN)VPL-CXZ10](https://hackathon.savetax.now/#/submission/e8629644-29e8-44d7-a193-b5efc3fdbb0a) | 새 반증 미입증·미등록 | Sony VPL-CXZ10의 모델·XGA 1024×768·3LCD 레이저·5,000lm·5.7kg·16W와 현재 1,950,000원·무료배송 표기가 대응합니다. |
| WISP | [26311187 (ID)43UH7Q-E](https://hackathon.savetax.now/#/submission/246f7e93-91fa-40f9-9819-14ae912419a6) | 새 반증 미입증·미등록 | LG 43UH7Q-E의 벽걸이 설치 포함 판매 상품이 실제로 존재합니다. 제출자도 현장설치 조건을 맞추는 비교 범위를 밝혔으므로, 설치가 빠진 가격이라고 반증할 수 없습니다. |
| WISP | [22171846 FDF-M-SC-04P](https://hackathon.savetax.now/#/submission/2590c8a9-b71f-48cb-9702-811d2326634f) | 새 반증 미입증·미등록 | 현재 에누리 원문은 18,700원에 배송비 3,000원 별도로 표시하지만 제출은 shipping_included=true와 비교 단가 18,700원을 썼습니다. 표기 차이는 확인했으나 실제 판매처의 수량별 무료배송 조건을 검증하지 못해 금액 오류로 확정하지 않았습니다. |
| WISP | [23618084 (CN)H6008](https://hackathon.savetax.now/#/submission/6b944b0e-29d8-45f8-b9ff-684f18bb928a) | 새 반증 미입증·미등록 | EFM ipTIME H6008은 동일 모델·기가비트 8포트·132×75×24mm이며 18,790원도 일치합니다. 이 가격은 제품 15,790원과 배송비 3,000원의 합계라 배송비를 다시 더하면 중복 가산입니다. |
| WISP | [25937063 (TH)WUS721208BLE6L4](https://hackathon.savetax.now/#/submission/d2b76331-1330-4938-9190-f9179afabafd) | 새 반증 미입증·미등록 | Western Digital HA340 WUS721208BLE6L4는 현재 원문에서도 8TB·SATA·7,200RPM·256MB로 원품과 일치합니다. 현재 배송 포함 686,570원은 제출 단가 687,080원보다 낮습니다. |
| WISP | [22978414 (TW)ST6000NM0024](https://hackathon.savetax.now/#/submission/4158a955-2835-4fdc-b8a2-9f3ea9048549) | 새 반증 미입증·미등록 | Seagate ST6000NM0024의 모델·6TB·SATA III·7,200RPM·128MB와 326,540원·무료배송이 일치합니다. 해외구매 형태도 제출 본문에 공개되어 있습니다. |
| WISP | [24349954 (CN)NVIDIA RTX A4000](https://hackathon.savetax.now/#/submission/b6721f31-e547-4000-a610-b2ff57487dba) | 새 반증 미입증·미등록 | 제출한 GPU·GDDR6메모리 용량과 공개 원규격/근거 상품이 대응하고, 병행수입·보증 차이도 본문에 공개. 현재 직접 읽은 가격비교 총액은 제출B와 같거나 낮아 별도 가격 오류 근거 없음 |
| WISP | [24715965 SFP-LX20](https://hackathon.savetax.now/#/submission/229cc1f1-66f5-412e-9d21-a4f4397a7de4) | 새 반증 미입증·미등록 | SOLTECH SFP-LX20의 동일 모델 코드와 21,200원·무료배송이 현재 원문에서 일치합니다. 원품도 부품 모듈로 명시되어 완제품 스위치 가격을 모듈 가격과 혼동한 사례가 아닙니다. |
| WISP | [24090605 3070 D6](https://hackathon.savetax.now/#/submission/d1be39fb-b425-4b21-8641-7300f71b44b1) | 새 반증 미입증·미등록 | RTX3070 배송4000 누락이라는 초기 단서는 직접 원문에서 반증됨. 다나와B568690은564690+4000 합계이며 실제 판매처도RTX3070·568690을 표시. 보드제조사 원품 미확인은 본문에 공개되어 별도 오류로 단정하지 않음 |
| WISP | [24612316 SFC505GHP](https://hackathon.savetax.now/#/submission/3bb9bd64-3859-4d56-b67a-5607e10af83d) | 새 반증 미입증·미등록 | SOLTECH SFC505GHP의 동일 모델·기가비트 5포트·185.4×123×44mm가 맞고 97,990원도 컴오아시스 본문에서 직접 확인했습니다. 다나와의 이 금액은 제품 93,990원과 배송 4,000원의 합계라 별도 배송 누락이라는 주장은 중복 가산할 우려가 있습니다. |
| WISP | [26034528 (CN)SUS550CHD](https://hackathon.savetax.now/#/submission/cff95880-0c06-4e74-91a3-31a44e19ca27) | 새 반증 미입증·미등록 | 전자랜드의 실제 SUS550CHD 상품에서 일반 판매가 521,000원·무료배송과 스탠드형·벽걸이형(+100,000원) 옵션을 직접 확인했습니다. 제출의 스탠드형 521,000원·무료배송은 원문과 일치합니다. |
| WISP | [25468355 (CN)RTX 4000 Ada Generation](https://hackathon.savetax.now/#/submission/6d5ffac1-4b04-467e-922f-9d950d347570) | 새 반증 미입증·미등록 | 제출한 GPU·GDDR6메모리 용량과 공개 원규격/근거 상품이 대응하고, 병행수입·보증 차이도 본문에 공개. 현재 직접 읽은 가격비교 총액은 제출B와 같거나 낮아 별도 가격 오류 근거 없음 |
| WISP | [25468354 (CN)RTX 5000 Ada Generation](https://hackathon.savetax.now/#/submission/2d25ca1e-3343-4589-bb2c-69eee268eaba) | 새 반증 미입증·미등록 | 제출한 GPU·GDDR6메모리 용량과 공개 원규격/근거 상품이 대응하고, 병행수입·보증 차이도 본문에 공개. 현재 직접 읽은 가격비교 총액은 제출B와 같거나 낮아 별도 가격 오류 근거 없음 |

## 접수와 한계

반증 사용량 2 → 132회. 신규 등록 사용량은 64회, 남은 신규 등록은 36회로 바뀌지 않았다. 반증 등록은 상대 예상액의 즉시 삭감이나 운영진의 최종 인정을 뜻하지 않는다.

검증: 외부 전송·인증 경계·멱등 복구를 다루는 관련 테스트 29개 통과. 반증 첨부에 URL을 잘못 넣는 경우도 자산 UUID 검사로 차단했다. 실제 접수 영수증과 공개 재조회는 모든 등록 건에서 대조했다.

- [등록한 반증 본문과 공개 링크](participant-counterevidence-bodies-20261019.md)
- [전체 감사·출처·영수증·납품 관련 번호](participant-counterevidence-20261019.json)
- [규정별 적용 기록](counterevidence-rules-20261019.json)
