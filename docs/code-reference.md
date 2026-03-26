# 시군구 코드 참고 메모

## 출처
- 내부 참고 리포: `hosungseo/k-policymap`
- 참고 파일: `scripts/fetch_housing.py`

## 활용 방식
- `k-policymap`의 전국 시군구 `LAWD_CD` 코드 테이블을 참고해
  인구감소지역/인구감소관심지역 통합 인덱스에 코드 매핑을 수행했다.
- 이번 프로젝트에서는 원본을 그대로 베끼기보다, 참고용 데이터셋으로 JSON 변환 후 매칭에 사용했다.

## 결과
- 대상 지역 총 107개
- 코드 매칭 성공 107개
- 미매칭 0개

## 생성 파일
- `data/reference-sigungu-codes-from-k-policymap.json`
- `data/population-region-index-with-codes.json`

## 다음 단계
- `population-region-index-with-codes.json` 기반으로 실거래가 수집 자동화
- MVP 지역 카드에 `lawdCd` 직접 연결
