#!/usr/bin/env python3
"""Rebuild region-catalog, enrich market summary, refresh site-meta from existing data."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def dump(name: str, obj) -> None:
    (DATA / name).write_text(
        json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def sample_quality(total: int, months: int) -> str:
    if total == 0:
        return "none"
    if months <= 6:
        return "very_low"
    if total < 80:
        return "limited"
    return "normal"


def data_status(total: int) -> str:
    return "no_transactions" if total == 0 else "ok"


def main() -> None:
    decline = load("population-decline-regions-2024.json")
    interest = load("population-decline-interest-regions-2026.json")
    index = load("population-region-index-with-codes.json")
    market = load("region-market-summary-24m.json")
    series = load("monthly-series-24m-all.json")

    all_months = {
        s["month"]
        for body in series.values()
        for s in (body.get("series") or [])
        if s.get("month")
    }
    period_start = min(all_months) if all_months else None
    period_end = max(all_months) if all_months else None
    collected_at = next(
        (m.get("collectedAt") for m in market if m.get("collectedAt")),
        date.today().isoformat(),
    )

    enriched = []
    for m in market:
        key = m["key"]
        ser = (series.get(key) or {}).get("series") or []
        zero_months = sum(1 for s in ser if (s.get("count") or 0) == 0)
        total = m.get("totalCount24m") or 0
        months = m.get("monthsWithTrades") or 0
        item = dict(m)
        item["periodStart"] = period_start
        item["periodEnd"] = period_end
        item["collectedAt"] = collected_at
        item["zeroTransactionMonthCount"] = (
            zero_months if ser else max(0, 24 - months)
        )
        item["dataStatus"] = data_status(total)
        item["sampleQuality"] = sample_quality(total, months)
        item.setdefault("medianPricePerSqm", None)
        enriched.append(item)
    dump("region-market-summary-24m.json", enriched)
    market_by_key = {m["key"]: m for m in enriched}

    catalog_regions = []
    for r in index["regions"]:
        province = r["normalizedProvince"]
        name = r["name"]
        key = f"{province}-{name}"
        lawd = r.get("lawdCd")
        sm = market_by_key.get(key)
        total = (sm or {}).get("totalCount24m") or 0
        months = (sm or {}).get("monthsWithTrades") or 0
        catalog_regions.append(
            {
                "regionId": f"reg-{lawd}",
                "sigunguCode": lawd,
                "regionSlug": f"{lawd}-{name}",
                "key": key,
                "name": name,
                "province": province,
                "provinceRaw": r.get("province"),
                "designationType": r["regionType"],
                "sourceNotice": r.get("sourceNotice"),
                "designationSourceId": (
                    "src-decline-notice-2024-15"
                    if r["regionType"] == "decline"
                    else "src-interest-notice-2025-78"
                ),
                "effectiveFrom": (
                    decline["source"]["effectiveDate"]
                    if r["regionType"] == "decline"
                    else interest["source"]["effectiveDate"]
                ),
                "effectiveTo": (
                    None
                    if r["regionType"] == "decline"
                    else interest["source"].get("expiryDate")
                ),
                "dataStatus": data_status(total),
                "sampleQuality": sample_quality(total, months),
                "hasMarketSummary": sm is not None,
                "hasSeries": key in series,
            }
        )
    catalog_regions.sort(key=lambda x: (x["province"], x["name"]))
    catalog = {
        "version": "1.0",
        "generatedAt": date.today().isoformat(),
        "periodStart": period_start,
        "periodEnd": period_end,
        "totalRegions": len(catalog_regions),
        "summary": {
            "decline": sum(1 for x in catalog_regions if x["designationType"] == "decline"),
            "interest": sum(1 for x in catalog_regions if x["designationType"] == "interest"),
            "ok": sum(1 for x in catalog_regions if x["dataStatus"] == "ok"),
            "no_transactions": sum(
                1 for x in catalog_regions if x["dataStatus"] == "no_transactions"
            ),
            "error": sum(1 for x in catalog_regions if x["dataStatus"] == "error"),
        },
        "regions": catalog_regions,
    }
    dump("region-catalog.json", catalog)

    meta = {
        "siteName": "인구감소지역 부동산",
        "version": "2026-H2-R1",
        "lastSiteUpdate": date.today().isoformat(),
        "transactionPeriodStart": period_start,
        "transactionPeriodEnd": period_end,
        "transactionCollectedAt": collected_at,
        "policyLastVerifiedAt": "2026-08-04",
        "regionCount": 107,
        "declineCount": 89,
        "interestCount": 18,
        "dataFiles": [
            "data/region-catalog.json",
            "data/region-market-summary-24m.json",
            "data/monthly-series-24m-all.json",
            "data/source-manifest.json",
        ],
        "disclaimer": (
            "투자 권유가 아니라 정책·시장 안내용입니다. "
            "세제 적용은 취득 시점 법령과 관계기관 확인이 필요합니다."
        ),
    }
    dump("site-meta.json", meta)
    print(
        f"built catalog={catalog['totalRegions']} "
        f"period={period_start}~{period_end} summary={catalog['summary']}"
    )


if __name__ == "__main__":
    main()
