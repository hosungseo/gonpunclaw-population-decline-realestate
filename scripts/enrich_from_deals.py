#!/usr/bin/env python3
"""Fill medianPricePerSqm from representative deals when full-window sqm is missing; rebuild search index."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def median(vals):
    vals = sorted(vals)
    if not vals:
        return None
    n = len(vals)
    mid = n // 2
    return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2


def main() -> None:
    market = json.loads((DATA / "region-market-summary-24m.json").read_text(encoding="utf-8"))
    rep = json.loads((DATA / "representative-deals.json").read_text(encoding="utf-8"))
    catalog = json.loads((DATA / "region-catalog.json").read_text(encoding="utf-8"))

    sqm_by_key = {}
    for r in rep:
        key = f"{r['province']}-{r['name']}"
        ratios = []
        for d in r.get("deals") or []:
            try:
                area = float(d.get("area") or 0)
                price = float(d.get("price") or 0)
                if area > 0 and price > 0:
                    ratios.append(price / area)
            except (TypeError, ValueError):
                pass
        if ratios:
            sqm_by_key[key] = round(median(ratios), 2)

    for m in market:
        if m.get("medianPricePerSqm") is None and m["key"] in sqm_by_key:
            m["medianPricePerSqm"] = sqm_by_key[m["key"]]
            m["medianPricePerSqmMethod"] = "representative_deals_median"
            m["medianPricePerSqmNote"] = (
                "대표 거래 표본 기반 근사치. 전수 집계 전에는 참고용으로만 사용."
            )
        elif m.get("medianPricePerSqm") is not None and not m.get("medianPricePerSqmMethod"):
            m["medianPricePerSqmMethod"] = "existing"
        if m.get("medianPricePerSqm") is None:
            m["medianPricePerSqmMethod"] = None
            m["medianPricePerSqmNote"] = "면적 정보 부족"

    (DATA / "region-market-summary-24m.json").write_text(
        json.dumps(market, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    market_by_key = {m["key"]: m for m in market}
    index = []
    for r in catalog["regions"]:
        m = market_by_key.get(r["key"], {})
        index.append(
            {
                "key": r["key"],
                "regionSlug": r["regionSlug"],
                "sigunguCode": r["sigunguCode"],
                "name": r["name"],
                "province": r["province"],
                "designationType": r["designationType"],
                "searchText": f"{r['province']} {r['name']} {r.get('provinceRaw') or ''} {r['sigunguCode']}",
                "totalCount24m": m.get("totalCount24m") or 0,
                "sampleQuality": m.get("sampleQuality") or r.get("sampleQuality"),
                "dataStatus": m.get("dataStatus") or r.get("dataStatus"),
                "median24m": m.get("median24m"),
                "medianPricePerSqm": m.get("medianPricePerSqm"),
                "monthsWithTrades": m.get("monthsWithTrades") or 0,
                "latestTradeMonth": m.get("latestTradeMonth"),
                "zeroTransactionMonthCount": m.get("zeroTransactionMonthCount"),
            }
        )
    (DATA / "region-search-index.json").write_text(
        json.dumps(
            {"version": "1.0", "generatedAt": date.today().isoformat(), "count": len(index), "regions": index},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    filled = sum(1 for m in market if m.get("medianPricePerSqm") is not None)
    print(f"enrich ok: sqm={filled}/{len(market)} search_index={len(index)}")


if __name__ == "__main__":
    main()
