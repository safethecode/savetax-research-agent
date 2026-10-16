# VIXAI-120B 1CH의 유료 객체분석 대안 검토

물품 **24338860, VIXAI-120G v4.0(VIXAI-120B)**는 2026-10-16T11:47:43.608658+00:00 공식 조회에서 available였다. **115개 fact·115개 납품요구·5,571조·4,011,120,000원**, 각 조당720,000원이다. 이 문서는 **미접수·미preview, 채택0원·ready=false**다. [공식 fact API](https://hackathon.savetax.now/v1/events/current/items/24338860)

[정확 계약 규격서의 G2B 첨부 페이지](https://shop.g2b.go.kr/link/GMSF001_01/?ctrtItemMngNo=002461991_1000000001)에서9쪽 PDF를 실제 다운로드하고 전체 페이지를 렌더해 읽었다.1쪽은1조=1CH·기간 제한 없음을,3쪽4.1은 사람·차량 검출/분류와 추적 객체 목록·개별 궤적 히스토리·바운딩박스·객체 겹침 처리를 명시한다.4.2는 객체/이벤트 녹화·검색이다. PTZ 자동추적과 도로 유고는 별도220B/220R 제품과 구분하며2025 카탈로그의 기능을 이 계약의 동일 권리로 자동 적용하지 않았다.

3쪽의 설치 H/W는 Xeon/Corei7·RAM16GB·HDD1TB·GPU1GB/IntelHD·Windows10+ 권장 사양이다. API의 RAM32GB 속성과 다르며 서버를 SW 가격에 포함한 것으로 읽지 않는다.7~8쪽에는 현장 설치·연계 확인과1년 하자보수·월 방문 점검·4시간 응답·이전 및 교육이 있다.

[Agent DVR 공식 가격표](https://www.ispyconnect.com/buy)에서 **서버1대·Annual을 실제 선택한 Professional은 USD215.46/년**이다(2026-10-16T11:53:05.994671+00:00). 가격 계산기만 사용했고 Select Plan·카트·구매·결제·계정 생성은 하지 않았다. KRW 통화 선택기는 없었으며 모든 가격이USD라는 안내를 읽었다. 원품1CH마다 이 전체 요금을 부담하는 보수 비교로, 무제한 카메라 수로 나누지 않는다.

[내장 객체인식](https://www.ispyconnect.com/docs/agent/ai-config)은 사람·차량을 로컬 ONNX 모델로 분석하고 연속 처리할 수 있다. [객체 추적](https://www.ispyconnect.com/docs/agent/motion-detection)은 바운딩박스·경로선 Heat Map·MOSSE/CSRT·추적 Timeout을, [녹화 검색](https://www.ispyconnect.com/docs/agent/timeline)은 객체 유형과 영역 검색을 설명한다. 외부 유료AI 서버는 필수가 아니다. 원품과 동일한 개체별 영구 궤적DB·목록UI·겹침 처리 성능을 확인한 것은 아니며, 실제 카메라·서버의 연계/처리량 시험도 미실시다.

[기관 이용 약관](https://www.ispyconnect.com/terms)4.2는 정부·교육기관의 상용 이용권을 요구한다. Annual 선불에 남는 영구 로컬권은 호스팅 기반 기능을 제외한다. 제3자에게 유료 호스팅을 제공하는 용도는4.3상 계속 활성 Professional 구독이 필요하므로 직접 기관 로컬 운영과 구별한다. 국내 현장 설치·월 방문 지원을 이 취득가에 포함하지 않는다.

[미 연준 H.10](https://www.federalreserve.gov/releases/h10/current/)의2026-10-13 공표 중10-09 값1USD=1,342.13KRW를 적용하면 참고 원가는289,175.3298원이다.115개 fact별 버림을 합친 세금·수수료 전 **조건부 차액은2,400,124,190원**이다. 별도10% 예산 시나리오는2,239,024,604원이지만 실제 세금으로 확인한 값은 아니다. 카드 적용환율이나 관측된 원화 판매가로 표시하지 않고 채택액에 합산하지 않는다.

한국 VAT·최종 결제 통화의 실제 값이 미확인이다. [현행 제출 스키마](https://hackathon.savetax.now/docs/submission-schema.md)의 `observed_price_krw`는 페이지에 표시된 양의 정수 원화 관측가이며, 이 외화 환산을 그 필드에 넣는 공식 예외는 확인하지 못했다. 외화 비교 자체가 금지됐다고 단정하지 않으며 **KRW 판매가나 점수 본문을 꾸미지 않았다**.

기존 GeoVision Advanced의 국내 실견1,407,000원은 원품보다 비싸 제외했다. 기존 Dahua NVR+2TB HDD를1CH마다 부담하는665,000원 구성은 공식1.2 가격 차이 조건 미달이다. NVR 자체4CH 경계·8CH SMD와 카메라측8CH 메타데이터를 구별했고, 개체별 궤적 히스토리·겹침 처리를 검증하지 않은 채8입력 수로 가격을 나누지 않았다.

모든115개 fact·계약·납품요구·listing·라인 번호와Q/C는 [동반 JSON](vixai120b-alternative-review.json)에 보존했다. 정확 원규격 PDF SHA256은 `e2543bcec14d9a2349632a1978b84f3a8617817b6c2ec43b60c6fbfbfd9a0ba4`다. 원본 PDF·이미지와 API 전체는 재배포하지 않는다. 국내 원화 판매원천이나 외화 표현 예외가 확인되기 전 자료로 보존하고 다음 고액 신규 후보로 이동한다.
