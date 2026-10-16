# Linux 서버 백신 1년 사용권 유료 대안 — 오프라인 검토본

물품 23454737 AhnLab V3 Net for Linux Server 3.6은 2026-10-16 12:21:24 UTC 공식 조회에서 available이었다. 비교 가능한 납품요구 라인은 91개, 수량은 6,132조, 비교금액은 2,908,530,240원이다. 정확한 원규격은 1조를 서버 1대의 1년 사용권으로 설명한다. ‘30~299 Server’는 가격 구간이다.

[실제 국내 상품 37](https://www.bitdefendershop.co.kr/product/business.asp?productNo=37)은 GravityZone Business Security다. 2026-10-16 12:29:36 UTC에 자체 브라우저로 **1 device 단가 24,200원, 1년·보호수량 5의 합계 121,000원(부가세 포함), ‘바로구매’ 표시**를 읽었다. ‘시스템 사양’ 탭을 눌러 같은 상품의 Linux 지원도 확인했다. 정적 HTML에는 하단 금액이 24,200원으로 남아 있으나, 실제 브라우저에서 수량 5를 계산한 합계는 121,000원이다.

[연결된 구매안내](https://www.bitdefendershop.co.kr/images/_temp/buy_info2.jpg)는 박스·패키지 배송 없이 ESD를 이메일로 제공한다고 명시한다. 공통 구매안내는 구매와 동시에 즉시 발급한다고 쓰고, 해당 상품 상단은 17시 전 주문 당일 발급·이후 익일 발급·휴일에는 다음 근무일 발급을 안내한다. 별도 물리 운송료를 가산하지 않았다. 구매·계정 생성·판매자 연락은 하지 않았다. 안내 이미지의 SHA256은 `51ef9b0ba151a0f3b50b2db490fd9b00d82749bc5c42d3cf4b36a8ae71865776`이다.

[제조사 비교문서](https://www.bitdefender.com/en-us/business/compare)는 Linux를 서버로 세며, 파일 서버를 구매한 좌석의 최대 30%로 제한한다. 원품 서버 1대마다 최소 5 device의 전액 121,000원을 부담하면 서버 비율은 1/5=20%로 이 범위 안에 든다. 남은 4개 슬롯도 비용에 포함한다. [사업용 약관](https://www.bitdefender.com/en-us/site/view/eula-business-solutions)은 내부 업무 이용과 구매한 라이선스 좌석 범위를 규정한다.

[Antimalware 문서](https://www.bitdefender.com/business/support/en/77209-376308-antimalware.html)는 Linux BEST 에이전트와 기본 포함 방역 모듈을 설명한다. 비교 대상은 유료 소프트웨어 사용권이며, 일반 Linux 서버의 악성코드 방역이라는 핵심 목적에 대응한다. [현재 요구사항](https://www.bitdefender.com/business/support/en/77209-376327-endpoint-protection.html)은 Linux에서 최소 2 vCPU·4GB RAM·디스크 2.5GB 및 임시 공간과 지원 OS·커널을 요구한다. NFS 실시간 검사에는 양측 fanotify 등의 조건이 있다.

원품의 RAM 512MB, 구형 OS·ProLinux, 프로세스·메모리 사전검사, Docker 실시간 검사, EPP 연동, GS 1등급, 현장 설치·4시간 응답·교육과 모두 일치하는 것은 아니다. 각 기관의 실제 환경 적합성과 설치·이전 비용은 확인하지 않았다.

모든 91개 fact에 **B=121,000원/원품 서버 1대·1년**을 적용한 조건부 취득가격 차액은 **2,166,558,240원**이다. 가중 조달단가는 비교단가의 3.92배로, 공식 조건인 1.2배 이상을 충족한다. 공식 preview·접수는 0회이며 채택액도 0원이다. 설치·지원까지 완료한 실제 예산 절감액으로 확정하지 않았다.

[공개 JSON](linuxserver23454737-review.json)에 전체 91개의 계약번호·납품요구번호·라인·등재번호와 각 Q/C·단위·세금·기간, 원본 ZIP/HWP·현재 판매 원문·관측 기록의 해시를 보존했다. 4,134,433바이트 ZIP과 정확한 225,792바이트 HWP 원문은 공개 재배포하지 않았다. 오프라인 offer와 본문 초안은 work/highvalue-hardware/after120b/diverse-ten/에 있다. 모든 가격 note에서 관측 단가 24,200원과 최소 5개 전체 121,000원/Server의 관계를 명시했다.
