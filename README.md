# 인구감소지역 부동산 — 특례와 실제 거래를 함께 보는 안내서

**배포 URL:** https://hosungseo.github.io/gonpunclaw-population-decline-realestate/

## 왜 이 사이트를 만들었나

수도권 부동산에는 수많은 서비스와 관심이 몰리지만, 인구감소지역의 시장을 체계적으로 보여주는 곳은 많지 않습니다. 이 사이트는 그 공백을 메우는 [공픈클로(gonpunclaw)](https://github.com/hosungseo) 실험입니다.

## 이 사이트는 무엇인가

인구감소지역·인구감소관심지역 **107곳**의 **법적 특례**와 **실제 아파트 거래 표본**을 함께 보여주는 공공형 안내 서비스입니다.

투자 추천이 아닙니다. 관심 지역을 고르면 **무엇이 정책적으로 다른지**, **거래 표본은 어느 정도인지**, **근거와 기준일은 무엇인지**를 확인하는 것이 목표입니다.

## 주요 화면

| 경로 | 내용 |
| --- | --- |
| [`/`](./index.html) | 특례 안내 + 지도 탐색 + 표본 품질 + 비교함 |
| [`/region/`](./region/) | 107개 지역 상세 URL |
| [`/compare.html`](./compare.html) | 2~3곳 비교, URL 공유, CSV |
| [`/policies/`](./policies/) | 특례 목록 |
| [`/policies/second-home.html`](./policies/second-home.html) | 세컨드홈 확인 순서 |
| [`/policies/timeline.html`](./policies/timeline.html) | 정책 변화 타임라인 |
| [`/sources.html`](./sources.html) | 출처 매니페스트·방법론 |

## 2026 H2 구현 상태

문서: [`docs/PRD-2026-H2.md`](./docs/PRD-2026-H2.md) · [`docs/UPGRADE-PLAN-2026-H2.md`](./docs/UPGRADE-PLAN-2026-H2.md) · [`docs/data-schema.md`](./docs/data-schema.md)

### R1 — 믿을 수 있는 최신 자료
- 출처 매니페스트, 지역 카탈로그, 기준일 표시
- 데이터 검증 게이트 + CI
- CSS/JS 분리, 표본 품질 상태

### R2 — 찾고 비교하기
- 지역 검색·시도·유형·거래량 필터
- 107개 정적 상세 URL
- 2~3곳 비교 페이지 + URL 상태
- ㎡당 중위(대표 거래 기반 참고치)
- 모바일 검색 우선 레이아웃
- 비교/테이블 CSV 다운로드

### R3 — 정책·생활 맥락
- 세컨드홈 확인 순서 (확정 판정 금지, 서버 미저장)
- 정책 변화 타임라인
- PolicyMap 연결 슬롯 (검증된 지도만 노출)
- 지역 상세 인용 복사

### 데이터 갱신
```bash
# 기존 스냅샷 메타 재생성
python3 scripts/build_catalog.py
python3 scripts/enrich_from_deals.py
python3 scripts/build_region_pages.py
python3 scripts/validate_data.py

# 국토부 API 월별 수집 (키 필요)
export MOLIT_RTMS_KEY=...
python3 scripts/collect_rtms.py

# 키 없이 파이프라인 dry-run
python3 scripts/collect_rtms.py --dry-run
```

## 데이터 출처

| 데이터 | 출처 | 기준 |
| --- | --- | --- |
| 인구감소지역 | 행정안전부 고시 2024-15 | 89개 |
| 인구감소관심지역 | 행정안전부 고시 2025-78 | 18개 |
| 실거래가 | 국토교통부 아파트 매매 공개자료 | 최근 24개월 스냅샷 |
| 시군구 코드 | LAWD_CD | 107 전량 매칭 |

상세 상태: [`sources.html`](./sources.html)

## 주의

- **투자 권유가 아니라 정책·시장 안내용**입니다.
- 거래 건수가 적은 지역은 월별 변동이 크게 보일 수 있습니다.
- 세제특례 적용 여부는 취득 시점 법령과 전문가·관계기관 확인이 필요합니다.
- ㎡당 중위는 전수 집계 전에는 대표 거래 기반 **참고치**일 수 있습니다.

## 기술 스택

- 정적 HTML/CSS/Vanilla JS + Leaflet
- GitHub Pages
- Python 빌드·검증 스크립트
