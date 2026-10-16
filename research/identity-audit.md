# 독립 제품 동일성 감사

관측 UTC: 2026-10-16T01:54:10.599290+00:00

모니터 **false**: 상세설명의 대체발송 공지가 결정적이다. 프로젝터 **true (본체 모델 기준)**: 소매 상세 사양과 조달 원본 사양이 일치한다. 제조국 표기는 미해결이다.

## 25109623 — same_product=false

소매 상세 iframe에 기존모델 단종 및 S22D30x 대체발송을 명시. 상품명상의 LS22C312EAKXKR와 실제발송모델이 다름.

소매: https://item.gmarket.co.kr/Item?goodsCode=3688303268

상세 iframe: https://item.gmarket.co.kr/Item/ItemDetailV2?detailVersionType=2&fasterDeliveryYn=false&fromBottomLayer=true&goodsCode=3688303268&isNew=true

원문: “※ S22C310(2) 제품 단종(품절)되어” / “후속 신제품 S22D30x 상품으로 대체발송됩니다.”

주문옵션으로 동일모델을 선택할 수 있다는 근거 없음. 본문과 iframe 모두 저가옵션의 다른 모델 선택항목을 노출하지 않지만, 선택옵션과 관계없이 대체발송 공지가 결정적이다.

| 항목 | 조달 원본 | 소매 상세 | 판단 |
|---|---|---|---|
| 모델 | (CN)LS22C312EAKXKR | 제목 LS22C312EAKXKR / 실제발송 S22D30x | 불일치 |
| 규격 | 54.6cm; 1920×1080; 250; 488.4×394.1×217.4; 2.4kg (raw synonyms) | 실제발송 S22D30x의 구체 모델 및 규격 미기재 | 구체제품 미확정 |
| 상태 | 데이터에 새상품 여부 명시필드 없음 | 새상품 | 반품/중고 근거 없음 |
| 구성 | 액정모니터 1대 단위 | 기본 모니터 표시; 대체모델 정확한 구성 미확인 | 동일구성 판단불가 |

조달 출처: https://api.savetax.now/v1/listings/002270042_1280002067, https://api.savetax.now/v1/listings/002470119_1050000452, https://api.savetax.now/v1/listings/R25TA00906342060000944, https://api.savetax.now/v1/listings/002470082_1050000272, https://api.savetax.now/v1/listings/002470216_1080000138; snapshot release r20261011T012137. 원본 위치 work/private/hardware-evidence-private.json (existing raw snapshot, not refetched)

## 24035326 — same_product=true

소매 상세 iframe의 모델명과 실제 제품 사양이 조달 raw synonyms 및 엡손 공식 EB-X550KG 사양과 여러 독립필드에서 일치. 다른 저가모델/대체발송 공지 근거 없음. 제품 본체 모델 기준 동일 판정이며 제조국 표기 불일치는 남음.

소매: https://item.gmarket.co.kr/Item?goodsCode=3583096259

상세 iframe: https://item.gmarket.co.kr/Item/ItemDetailV2?detailVersionType=2&fasterDeliveryYn=false&fromBottomLayer=true&goodsCode=3583096259&isNew=true

원문: “품명 : 프로젝터, EB-X550KG” / “해상도 1024x768, XGA 4:3” / “밝기 5,500 안시루멘” / “제조국 : 중국”

소매 본문 460줄 및 상세 iframe 41줄에 별도 저가모델 선택옵션 없음. 제목만이 아니라 iframe의 사양으로 판정. 동적 주문옵션 API/결제흐름까지 조사한 것은 아니므로 숨겨진 옵션 부재를 완전 증명하지 않음.

| 항목 | 조달 원본 | 소매 상세 | 판단 |
|---|---|---|---|
| 모델/브랜드 | Epson (PH)EB-X550KG | Epson EB-X550KG; 본문 브랜드 엡손 | 모델 본체 일치 |
| 투사/해상도 | 3LCD; XGA(1024×768) | 3LCD; 1024x768, XGA 4:3 | 일치 |
| 밝기/명암비 | 5500ANSI lm; 15000:1 | 5500 안시루멘; 15000:1 | 일치 |
| 단자 | HDMI×2 | HDMI×2; D-Sub, RCA, RJ45, USB-A/USB-B | 기재범위 일치 |
| 크기/스피커 | 폭377 깊이291; 16W Monaural | 377×101×291mm; 16W 모노 | 기재범위 일치 |
| 상태/구성 | 프로젝터 대 단위; 상세 구성품 미확인 | 새상품; 구성품 -; 무선랜유닛별매 | 본체 근거 충족, 추가부속 동일성 미확인 |
| 제조국/접두어 | 모델 필드 (PH) 접두어; 원산지 별도필드 없음 | 상세 iframe 제조국 중국 | 불일치 가능성 남음; PH 뜻을 출처로 확인하지 못했으므로 필리핀산이라고 확정하지 않음 |

조달 출처: https://api.savetax.now/v1/listings/0024C1282_1040000001; snapshot release r20261011T012137. 원본 위치 work/private/hardware-evidence-private.json (existing raw snapshot, not refetched)

(PH)/(CN)은 정의 문서를 확보하지 못했으므로 원산지라고 확정하지 않는다. 프로젝터 제조국 “중국” 표기는 소매 판매자의 고시이며, 다른 모델이라는 증거로 단독 사용하지 않았다.

엡손 공식 교차검증: https://www.epson.co.kr/비즈니스용-제품/프로젝터/중형-강당-미팅룸-프로젝터/EB-X550KG/p/V11H820151

외부제보 수정/취하 및 git commit은 하지 않았다.
