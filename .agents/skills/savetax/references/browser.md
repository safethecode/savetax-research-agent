# 판매 화면 읽기

HTTP로 읽히는 공개 원문은 먼저 그 경로를 쓴다. JS·선택 옵션·상세 iframe이 필요한 경우에만 기존 Browser Harness·Jev를 사용한다. 검색 발췌와 Jev의 DONE은 가격 검증이나 사양 인정이 아니다.

저장소 root에서 실행한다. 명령 지원 여부는 해당 `--help`로 확인한다.

```powershell
python -m savetax browser-status --session research
python -m savetax browser-read --session research --url '<실제 공개 HTTPS URL>' --output work/browser/product.json
python -m savetax browser-jev --help
```

`browser-plan`은 다음 동작 제안, `browser-jev`는 실행 루프다. 모델 판단과 실제 실행·화면 관측을 구분한다. TypeSafe·Parallel 키는 각 서비스 환경변수로만 사용하고 SaveTax PAT를 브라우저 자식 프로세스에 넘기지 않는다. 설치·연결 문제가 있을 때만 저장소 `docs/integrations/browser.md`를 읽는다.

## 화면에서 확인할 것

- 선택한 전체 모델·옵션명·수량이 실제 상품 행에 나타나는지 읽는다. 별도 적용 버튼·비동기 갱신이 있으면 반영 후 합계를 읽는다.
- 기본가와 선택 옵션가, 일반가와 조건부 할인, 포함/별도 VAT·배송·필수 구성품을 대조한다.
- 수량 입력 후 나타나는 팔레트·운임·세금도 기록한다. 반환 환급은 미리 빼지 않는다.
- 실제 표시된 BUY/품절과 숨겨진 템플릿을 구별한다. 검색/상품검색 MCP의 재고 표시는 실제 선택 채널의 판매 상태를 대신하지 않는다.
- 상세 이미지·도면·iframe의 해당 모델 사양을 읽는다. 다른 세대·suffix·새 버전의 사양을 섞지 않는다.
- HWP/HWPX는 기존 `document-read`로 실제 형식·해시·텍스트를 추출한다. 표·도면·변경 추적은 원본 화면을 함께 보며 추출 성공을 최종 규격 확정으로 세지 않는다.

같은 브라우저 세션과 공용 MCP는 직렬로 조작한다. 독립 CLI는 이름 있는 본인 세션만 쓰고 다른 사람/에이전트의 탭을 닫지 않는다. 직접 만든 임시 탭만 정리한다. CLI의 `new_tab`은 빈 탭을 재사용할 수 있으므로 새로 만든 target ID를 알고 있을 때만 종료한다.

구매·장바구니·문의·로그인·캡차 조작은 수행하지 않는다. 접근 차단은 우회하지 않고 다른 판매처로 넘어간다. 정상 HTTP·Content-Type·파일 크기 또는 실제 화면을 확인하지 않은 수집물을 성공으로 기록하지 않는다.
