#!/usr/bin/env python3
"""Validate core data products for deploy gate (PRD R1 / FR-RE-004)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXPECTED_REGIONS = 107
EXPECTED_DECLINE = 89
EXPECTED_INTEREST = 18


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def err(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def load(name: str):
    path = DATA / name
    if not path.exists():
        raise FileNotFoundError(name)
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    r = Report()

    required = [
        "region-catalog.json",
        "region-market-summary-24m.json",
        "monthly-series-24m-all.json",
        "source-manifest.json",
        "site-meta.json",
        "map-points.json",
        "population-region-index-with-codes.json",
        "representative-deals.json",
    ]
    for name in required:
        if not (DATA / name).exists():
            r.err(f"missing required file: {name}")
    if r.errors:
        return finish(r)

    catalog = load("region-catalog.json")
    market = load("region-market-summary-24m.json")
    series = load("monthly-series-24m-all.json")
    manifest = load("source-manifest.json")
    meta = load("site-meta.json")
    points = load("map-points.json")
    index = load("population-region-index-with-codes.json")
    deals = load("representative-deals.json")

    regions = catalog.get("regions") or []
    if len(regions) != EXPECTED_REGIONS:
        r.err(f"catalog regions={len(regions)} expected={EXPECTED_REGIONS}")

    decline_n = sum(1 for x in regions if x.get("designationType") == "decline")
    interest_n = sum(1 for x in regions if x.get("designationType") == "interest")
    if decline_n != EXPECTED_DECLINE:
        r.err(f"decline count={decline_n} expected={EXPECTED_DECLINE}")
    if interest_n != EXPECTED_INTEREST:
        r.err(f"interest count={interest_n} expected={EXPECTED_INTEREST}")

    ids = [x.get("regionId") for x in regions]
    slugs = [x.get("regionSlug") for x in regions]
    keys = [x.get("key") for x in regions]
    codes = [x.get("sigunguCode") for x in regions]
    for label, values in (
        ("regionId", ids),
        ("regionSlug", slugs),
        ("key", keys),
        ("sigunguCode", codes),
    ):
        if len(values) != len(set(values)):
            r.err(f"duplicate {label}")
        if any(v in (None, "") for v in values):
            r.err(f"empty {label} present")

    if len(market) != EXPECTED_REGIONS:
        r.err(f"market summary rows={len(market)} expected={EXPECTED_REGIONS}")
    if len(points) != EXPECTED_REGIONS:
        r.err(f"map points={len(points)} expected={EXPECTED_REGIONS}")

    market_by_key = {m.get("key"): m for m in market}
    point_keys = {p.get("key") for p in points}
    catalog_keys = set(keys)

    if catalog_keys != set(market_by_key):
        missing = catalog_keys - set(market_by_key)
        extra = set(market_by_key) - catalog_keys
        if missing:
            r.err(f"market missing keys: {sorted(missing)[:5]}")
        if extra:
            r.err(f"market extra keys: {sorted(extra)[:5]}")

    if catalog_keys != point_keys:
        r.err("catalog keys and map-points keys diverge")

    status_counts = {"ok": 0, "no_transactions": 0, "error": 0}
    for m in market:
        st = m.get("dataStatus")
        if st not in status_counts:
            r.err(f"unknown dataStatus for {m.get('key')}: {st}")
            continue
        status_counts[st] += 1
        required_fields = [
            "periodStart",
            "periodEnd",
            "collectedAt",
            "sampleQuality",
            "zeroTransactionMonthCount",
        ]
        for f in required_fields:
            if f not in m:
                r.err(f"market {m.get('key')} missing {f}")
        total = m.get("totalCount24m") or 0
        if st == "no_transactions" and total != 0:
            r.err(f"{m.get('key')}: no_transactions but total={total}")
        if st == "ok" and total == 0:
            r.err(f"{m.get('key')}: ok but total=0")
        if m.get("median24m") is not None and m["median24m"] < 0:
            r.err(f"{m.get('key')}: negative median")

    if sum(status_counts.values()) != EXPECTED_REGIONS:
        r.err(f"status sum {sum(status_counts.values())} != {EXPECTED_REGIONS}")

    # series continuity for regions with trades
    for key, body in series.items():
        ser = body.get("series") or []
        if len(ser) != 24:
            r.warn(f"series {key}: months={len(ser)} (expected 24)")
        months = [s.get("month") for s in ser]
        if months != sorted(months):
            r.err(f"series {key}: months not sorted")
        for s in ser:
            if (s.get("count") or 0) < 0:
                r.err(f"series {key}: negative count")

    series_keys = set(series.keys())
    if catalog_keys - series_keys:
        r.warn(f"series missing {len(catalog_keys - series_keys)} catalog keys")

    # index match
    idx_regions = index.get("regions") or []
    if len(idx_regions) != EXPECTED_REGIONS:
        r.err(f"index regions={len(idx_regions)} expected={EXPECTED_REGIONS}")
    if (index.get("summary") or {}).get("unmatched", 0) not in (0, None):
        r.err("index has unmatched regions")

    # source manifest
    sources = manifest.get("sources") or []
    if not sources:
        r.err("source-manifest empty")
    source_ids = [s.get("sourceId") for s in sources]
    if len(source_ids) != len(set(source_ids)):
        r.err("duplicate sourceId")
    required_source_ids = {
        "src-decline-notice-2024-15",
        "src-interest-notice-2025-78",
        "src-molit-rtms-apt",
        "src-special-act",
    }
    missing_src = required_source_ids - set(source_ids)
    if missing_src:
        r.err(f"missing required sources: {sorted(missing_src)}")
    for s in sources:
        for f in ("title", "publisher", "sourceType", "url", "status", "lastVerifiedAt"):
            if not s.get(f):
                r.err(f"source {s.get('sourceId')} missing {f}")
        if s.get("status") == "expired":
            r.err(f"expired source blocks deploy: {s.get('sourceId')}")
        if s.get("status") == "review_required":
            r.warn(f"source needs review: {s.get('sourceId')}")

    # site meta
    for f in (
        "lastSiteUpdate",
        "transactionPeriodStart",
        "transactionPeriodEnd",
        "transactionCollectedAt",
        "policyLastVerifiedAt",
    ):
        if not meta.get(f):
            r.err(f"site-meta missing {f}")

    if meta.get("transactionPeriodStart") != catalog.get("periodStart"):
        r.err("site-meta periodStart != catalog periodStart")
    if meta.get("transactionPeriodEnd") != catalog.get("periodEnd"):
        r.err("site-meta periodEnd != catalog periodEnd")

    # deals optional completeness
    if len(deals) < EXPECTED_REGIONS:
        r.warn(f"representative-deals rows={len(deals)} < {EXPECTED_REGIONS}")

    return finish(r, status_counts)


def finish(r: Report, status_counts: dict | None = None) -> int:
    if status_counts:
        print("dataStatus:", status_counts)
    for w in r.warnings:
        print(f"WARN: {w}")
    for e in r.errors:
        print(f"ERROR: {e}")
    if r.errors:
        print(f"FAILED: {len(r.errors)} error(s), {len(r.warnings)} warning(s)")
        return 1
    print(f"OK: validation passed ({len(r.warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
