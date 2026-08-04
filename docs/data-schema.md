# 데이터 스키마 (R1)

이 문서는 PRD `FR-RE-001`~`004`의 공통 데이터 규칙을 고정한다.

## 디렉터리 규칙

| 경로 | 역할 |
| --- | --- |
| `data/*.json` | 배포용 산출물 (검증 통과본) |
| `scripts/` | 재현 가능한 빌드·검증 |
| `region/` | 지역 상세 정적 페이지 (빌드 생성) |
| 원천 API 응답 | 저장소에 두지 않음 (운영 환경 또는 릴리스 자산) |

수동으로 고친 배포 JSON을 원천으로 다시 쓰지 않는다.

## `region-catalog.json`

107개 지역의 기준정보.

| 필드 | 설명 |
| --- | --- |
| `regionId` | 불변 내부 키 (`reg-{sigunguCode}`) |
| `sigunguCode` | LAWD_CD 5자리 |
| `regionSlug` | URL 슬러그 (`{code}-{name}`) |
| `key` | 화면·시계열 조인 키 (`{province}-{name}`) |
| `designationType` | `decline` \| `interest` |
| `designationSourceId` | `source-manifest` 참조 |
| `dataStatus` | `ok` \| `no_transactions` \| `error` |
| `sampleQuality` | `none` \| `very_low` \| `limited` \| `normal` |

## `region-market-summary-24m.json`

지역별 24개월 요약. 행 수는 항상 107.

추가 R1 필드:

- `periodStart`, `periodEnd` (`YYYYMM`)
- `collectedAt` (ISO date)
- `zeroTransactionMonthCount`
- `dataStatus`, `sampleQuality`
- `medianPricePerSqm` (원 거래 면적 집계 후 채움, 없으면 `null`)

## 표본 품질 규칙

| 상태 | 조건 |
| --- | --- |
| `none` | 거래 0건 |
| `very_low` | 거래 발생 월 ≤ 6 |
| `limited` | 24개월 거래 < 80 |
| `normal` | 그 외 |

## `source-manifest.json`

법령·고시·거래 데이터의 출처 수명주기.

필수 필드: `sourceId`, `title`, `publisher`, `sourceType`, `url`, `status`, `lastVerifiedAt`

`status`: `active` \| `upcoming` \| `expired` \| `review_required` \| `unavailable`

`expired`는 배포 차단. `review_required`는 경고.

## `site-meta.json`

사이트 헤더·푸터에 쓰는 최신성 메타.

## 검증

```bash
python3 scripts/build_catalog.py
python3 scripts/build_region_pages.py
python3 scripts/validate_data.py
```

실패 시 GitHub Pages 산출물을 갱신하지 않는다.
