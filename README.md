# 인구감소지역 부동산 — 특례와 실제 거래를 함께 보는 안내서

**배포 URL:** https://hosungseo.github.io/gonpunclaw-population-decline-realestate/

## 왜 이 사이트를 만들었나

수도권 부동산에는 수많은 서비스와 관심이 몰리지만, 인구감소지역의 시장을 체계적으로 보여주는 곳은 많지 않습니다.

플랫폼 기업은 이용자가 많은 곳으로 갑니다. 인구감소지역처럼 관심이 적은 영역에는 민간 유인이 약합니다. AI로 개발 허들이 낮아진 지금, 관심이 적은 곳에도 공공형 안내 서비스를 만드는 것이 가능합니다. 이 사이트는 그 실험을 하는 [공픈클로(gonpunclaw)](https://github.com/hosungseo) 프로젝트의 일부입니다.

## 이 사이트는 무엇인가

인구감소지역·인구감소관심지역 **107곳**의 **법적 특례**와 **실제 아파트 거래 표본**을 함께 보여주는 공공형 안내 서비스입니다.

투자 추천이 아닙니다. 관심 지역을 고르면 **무엇이 정책적으로 다른지**, **거래 표본은 어느 정도인지**, **근거와 기준일은 무엇인지**를 확인하는 것이 목표입니다.

## 2026 H2 R1 업그레이드

PRD: [`docs/PRD-2026-H2.md`](./docs/PRD-2026-H2.md) · 기획: [`docs/UPGRADE-PLAN-2026-H2.md`](./docs/UPGRADE-PLAN-2026-H2.md) · 스키마: [`docs/data-schema.md`](./docs/data-schema.md)

| 항목 | 상태 |
| --- | --- |
| 출처 매니페스트 `data/source-manifest.json` | 완료 |
| 지역 카탈로그 `data/region-catalog.json` (107) | 완료 |
| 시장 요약 표본 품질·기준일 필드 | 완료 |
| 데이터 검증 게이트 `scripts/validate_data.py` | 완료 |
| CSS/JS 분리 (`assets/css`, `assets/js`) | 완료 |
| 사이트 전체 기준일 표시 | 완료 |
| 출처 페이지 `/sources.html` | 완료 |
| 지역 상세 정적 URL 107개 `/region/{code}-{name}/` | 완료 (R2 기반) |
| 월별 API 자동 수집 | 골격만 (`scripts/refresh_pipeline.md`) |

## 구조

### 챕터 1: 그래서 무엇이 달라지나
- 세제특례 / 정주지원 / 도시계획 특례 / 관심지역 제도
- 근거 법령·정책뉴스 연결

### 챕터 2: 정책 대상 지역의 시장은 어떻게 움직였나
- 지도 + 시도 필터 + 지역 패널 (24개월 거래·중위가)
- 표본 품질 배지 · 무거래 월 · 수집일
- 지역 비교 테이블
- [지역 상세 목록](./region/) · [출처·방법론](./sources.html)

## 데이터 출처

| 데이터 | 출처 | 기준 |
| --- | --- | --- |
| 인구감소지역 | 행정안전부 고시 2024-15 | 89개 |
| 인구감소관심지역 | 행정안전부 고시 2025-78 | 18개 |
| 실거래가 | 국토교통부 아파트 매매 공개자료 | 최근 24개월 (현재 스냅샷 2024.01~2025.12) |
| 시군구 코드 | LAWD_CD 매핑 | 107 전량 매칭 |

상세 상태·확인일은 [`sources.html`](./sources.html)과 `data/source-manifest.json`을 본다.

## 로컬 빌드·검증

```bash
python3 scripts/build_catalog.py
python3 scripts/build_region_pages.py
python3 scripts/validate_data.py
```

검증 실패 시 배포하지 않는 것이 원칙이다. GitHub Actions: `.github/workflows/validate.yml`

## 기술 스택

- 정적 HTML + CSS + Vanilla JS (+ Leaflet 지도)
- GitHub Pages
- Python 스크립트로 데이터 메타·지역 페이지 생성

## 주의

- **투자 권유가 아니라 정책·시장 안내용**입니다.
- 거래 건수가 적은 지역은 월별 변동이 크게 보일 수 있습니다.
- 세제특례 적용 여부는 취득 시점 법령과 전문가·관계기관 확인이 필요합니다.
