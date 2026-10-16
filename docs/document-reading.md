# 공식 규격서 본문 읽기

나라장터에서 내려받은 문서의 확장자와 실제 형식이 다를 때 `document-read`로 파일 내용을 먼저 판별한다. 네트워크 요청 없이 로컬 파일만 읽으며 원본 파일을 변경하지 않는다.

```powershell
python -m pip install -e ".[documents]"
python -m savetax document-read --input work/specification.hwpx --output work/specification-text.json
```

기본 설치만으로 HWPX ZIP을 읽을 수 있다. HWP CFB에는 선택 의존성 `olefile`이 필요하다. 출력에는 실제 형식, 확장자 불일치, 원본 바이트 수와 SHA256, 구역별 본문, 추출 시각과 한계가 남는다. HWPX는 패키지의 spine 순서를 따르고, 순서 정보가 없으면 구역 파일명의 숫자순을 썼다고 표시한다. HWP는 본문 스트림을 읽고 제어 정보의 바이트를 일반 글자로 옮기지 않는다.

HWP 압축 뒤에 CRC32와 원문 길이를 담은 8바이트 후미가 있는 문서도 두 값을 검산한 뒤 읽는다. 손상된 레코드·압축 데이터, 지원하지 않는 보호 형식, 본문 없는 문서는 추출 성공으로 반환하지 않는다. 파일은 기본 25MB, 압축 내부 총용량은 100MB까지 읽는다. 매크로·문서 속 링크를 실행하지 않는다.

`evidence_status=unreviewed_text_extraction`은 본문 추출 상태다. 표의 행·열 대응, 이미지·도면·페이지 배치와 가격·사양·대체 가능성은 별도로 검토한다. 숫자가 텍스트에 있다는 이유만으로 특정 열의 규격값으로 확정하지 않는다. 스캔된 그림의 글자는 이 명령이 OCR하지 않는다.

HWPX 본문에 변경추적의 `insertBegin/End`·`deleteBegin/End`가 있으면 구역별 개수와 `revision_review.status=markers_detected`를 남긴다. 삽입·삭제 이력을 자동 승인하거나 거부하지 않으므로 예전 값과 새 값이 함께 추출될 수 있다. `no_known_markers`는 이 네 표식을 찾지 못했다는 뜻이며 최종본이나 사양 검증을 뜻하지 않는다. HWP의 변경추적은 판별하지 않아 `not_assessed`로 표시한다. 한컴오피스 AI 교육용 규격서에서 50조/10조와 ELA/ALA가 함께 추출된 사례를 계기로 추가했다.

실제 검증에는 춘추·동계 운동복 규격서 2개와 MD-25S·BDK-SC-002 규격서 2개를 썼다. 운동복 파일은 게시 확장자가 HWPX였지만 실제 형식은 HWP CFB였고, 다른 두 파일은 HWPX였다. 원본 파일은 `work/`에만 보존한다.

형식 해석은 [한컴 HWP 5.0 공개 명세](https://cdn.hancom.com/link/docs/%ED%95%9C%EA%B8%80%EB%AC%B8%EC%84%9C%ED%8C%8C%EC%9D%BC%ED%98%95%EC%8B%9D_5.0_revision1.2.pdf), [한컴 HWPX 구조 설명](https://tech.hancom.com/hwpxformat/), [한컴 HWPX 본문 설명](https://tech.hancom.com/python-hwpx-parsing-2/)을 참고했다. 전체 렌더러를 구현했다는 뜻은 아니다.
