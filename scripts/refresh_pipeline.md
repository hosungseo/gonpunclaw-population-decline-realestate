# 월별 거래 데이터 갱신 파이프라인 (R1 골격)

PRD `FR-RE-002`에 맞춘 단계. 원 API 키는 환경 변수로만 주입한다.

## 단계

1. **수집** — 국토교통부 아파트 매매 실거래 공개 API, 시군구(`LAWD_CD`) × 월
2. **원본 보관** — 운영 환경에 raw 응답 + 수집 시각 (저장소 커밋 금지 권장)
3. **정규화** — 금액·면적·취소·중복 처리 규칙 적용
4. **지역 연결** — `region-catalog.json`의 `sigunguCode`/`key`로 107곳 매핑
5. **집계** — 월별 시계열 + 24개월 요약 + 대표 거래
6. **풍부화** — `build_catalog.py`로 `dataStatus`·`sampleQuality`·기간 필드
7. **검증** — `validate_data.py` (실패 시 중단)
8. **페이지 생성** — `build_region_pages.py`
9. **배포** — 검증 통과 후에만 Pages 반영

## 로컬 명령 (현재 스냅샷 재생성)

```bash
python3 scripts/build_catalog.py
python3 scripts/build_region_pages.py
python3 scripts/validate_data.py
```

## 환경 변수 (수집 단계 예정)

- `MOLIT_RTMS_KEY` — 공공데이터포털 일반 인증키
- `COLLECT_MONTHS` — 기본 24

## 실패 시

- 기존 검증본 `data/*.json` 유지
- `dataStatus=error` 지역만 표시하는 보고 파일을 남긴 뒤 배포 차단
