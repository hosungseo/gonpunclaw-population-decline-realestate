#!/usr/bin/env python3
"""
Monthly RTMS (MOLIT apartment trade) collection skeleton.

Requires env MOLIT_RTMS_KEY for live fetch.
Without the key, runs a dry-run that only rebuilds catalog/pages from existing data.

Pipeline:
  1) collect months x regions
  2) normalize (caller may store raw outside repo)
  3) aggregate monthly series + market summary
  4) build_catalog + validate
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
API = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"


def months_back(end_yyyymm: str, n: int = 24) -> list[str]:
    y, m = int(end_yyyymm[:4]), int(end_yyyymm[4:6])
    out = []
    for _ in range(n):
        out.append(f"{y:04d}{m:02d}")
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(out))


def normalize_key(key: str) -> str:
    """Accept Encoding or Decoding form of data.go.kr serviceKey."""
    key = (key or "").strip().strip("'\"")
    if not key:
        return key
    # If already percent-encoded, decode once so urlencode can re-encode safely.
    if "%" in key:
        return urllib.parse.unquote(key)
    return key


def parse_items(root: ET.Element, yyyymm: str) -> list[dict]:
    items = []
    for item in root.findall(".//item"):
        def t(tag: str):
            el = item.find(tag)
            return el.text.strip() if el is not None and el.text else None

        amt = t("dealAmount") or t("거래금액")
        if amt:
            amt = amt.replace(",", "").strip()
        try:
            price = int(amt) if amt else None
        except ValueError:
            price = None
        area = t("excluUseAr") or t("전용면적")
        try:
            area_f = float(area) if area else None
        except ValueError:
            area_f = None
        items.append(
            {
                "price": price,
                "area": area_f,
                "year": t("buildYear") or t("건축년도"),
                "name": t("aptNm") or t("아파트"),
                "road": t("roadNm") or t("도로명") or t("umdNm") or "",
                "month": yyyymm,
            }
        )
    return items


def fetch_month(lawd: str, yyyymm: str, key: str, sleep: float = 0.12) -> list[dict]:
    """Fetch all pages for one region-month. Retries transient errors."""
    key = normalize_key(key)
    all_items: list[dict] = []
    page = 1
    page_size = 1000
    while True:
        params = {
            "serviceKey": key,
            "LAWD_CD": lawd,
            "DEAL_YMD": yyyymm,
            "pageNo": str(page),
            "numOfRows": str(page_size),
        }
        url = API + "?" + urllib.parse.urlencode(params)
        last_err = None
        root = None
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "gonpunclaw-rtms/1.0"})
                with urllib.request.urlopen(req, timeout=90) as resp:
                    raw = resp.read()
                root = ET.fromstring(raw)
                code = root.findtext(".//resultCode") or ""
                # 000 / 00 / empty = success on various MOLIT payloads
                if code and code not in ("000", "00", "0"):
                    msg = root.findtext(".//resultMsg") or ""
                    raise RuntimeError(f"API resultCode={code} msg={msg}")
                break
            except Exception as e:
                last_err = e
                time.sleep(0.8 * (attempt + 1))
        if root is None:
            raise RuntimeError(f"fetch failed {lawd} {yyyymm}: {last_err}")

        page_items = parse_items(root, yyyymm)
        all_items.extend(page_items)
        total = root.findtext(".//totalCount")
        try:
            total_n = int(total) if total is not None else len(all_items)
        except ValueError:
            total_n = len(all_items)
        if len(all_items) >= total_n or len(page_items) < page_size:
            break
        page += 1
        if page > 50:
            break
        time.sleep(sleep)
    return all_items


def median(vals: list[float]):
    vals = sorted(v for v in vals if v is not None)
    if not vals:
        return None
    n = len(vals)
    mid = n // 2
    return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--end", default=None, help="YYYYMM end month (default: site-meta period end or previous month)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.15)
    args = parser.parse_args()

    key = normalize_key(os.environ.get("MOLIT_RTMS_KEY", "").strip())
    catalog = json.loads((DATA / "region-catalog.json").read_text(encoding="utf-8"))
    regions = catalog["regions"]

    if not key or args.dry_run:
        print("DRY-RUN: no live API collection (set MOLIT_RTMS_KEY to enable).")
        print(f"Would collect 24 months × {len(regions)} regions.")
        os.system(f"{sys.executable} {ROOT/'scripts'/'build_catalog.py'}")
        os.system(f"{sys.executable} {ROOT/'scripts'/'enrich_from_deals.py'}")
        os.system(f"{sys.executable} {ROOT/'scripts'/'build_region_pages.py'}")
        return os.system(f"{sys.executable} {ROOT/'scripts'/'validate_data.py'}")

    end = args.end
    if not end:
        meta = json.loads((DATA / "site-meta.json").read_text(encoding="utf-8"))
        end = meta.get("transactionPeriodEnd") or date.today().strftime("%Y%m")
    window = months_back(end, 24)
    print(f"Collecting {window[0]}..{window[-1]} for {len(regions)} regions")

    series_all = {}
    market = []
    rep_deals = []

    for i, reg in enumerate(regions, 1):
        lawd = reg["sigunguCode"]
        key_name = reg["key"]
        monthly = []
        all_prices = []
        all_sqm = []
        latest_month = None
        latest_median = None
        best_deals = []

        for ym in window:
            try:
                items = fetch_month(lawd, ym, key, sleep=args.sleep)
            except Exception as e:
                print(f"ERROR {key_name} {ym}: {e}")
                items = []
            prices = [x["price"] for x in items if x.get("price")]
            med = median(prices)
            mn = min(prices) if prices else None
            mx = max(prices) if prices else None
            monthly.append({"month": ym, "count": len(prices), "median": med, "min": mn, "max": mx})
            all_prices.extend(prices)
            for x in items:
                if x.get("price") and x.get("area"):
                    all_sqm.append(x["price"] / x["area"])
            if prices:
                latest_month = ym
                latest_median = med
                # keep up to 3 highest recent deals as representative
                ranked = sorted(items, key=lambda d: d.get("price") or 0, reverse=True)[:3]
                best_deals = [
                    {
                        "name": d.get("name") or "거래",
                        "area": str(d.get("area") or ""),
                        "year": str(d.get("year") or ""),
                        "road": d.get("road") or "",
                        "price": d.get("price"),
                    }
                    for d in ranked
                ]
            time.sleep(args.sleep)

        total = sum(m["count"] for m in monthly)
        months_with = sum(1 for m in monthly if m["count"] > 0)
        zero_months = sum(1 for m in monthly if m["count"] == 0)
        data_status = "no_transactions" if total == 0 else "ok"
        if months_with == 0:
            sample_q = "none"
        elif months_with <= 6:
            sample_q = "very_low"
        elif total < 80:
            sample_q = "limited"
        else:
            sample_q = "normal"

        series_all[key_name] = {
            "province": reg["province"],
            "name": reg["name"],
            "regionType": reg["designationType"],
            "lawdCd": lawd,
            "series": monthly,
        }
        market.append(
            {
                "key": key_name,
                "province": reg["province"],
                "name": reg["name"],
                "regionType": reg["designationType"],
                "lawdCd": lawd,
                "totalCount24m": total,
                "monthsWithTrades": months_with,
                "latestTradeMonth": latest_month,
                "latestMedian": latest_median,
                "median24m": median(all_prices),
                "priceMin24m": min(all_prices) if all_prices else None,
                "priceMax24m": max(all_prices) if all_prices else None,
                "periodStart": window[0],
                "periodEnd": window[-1],
                "collectedAt": date.today().isoformat(),
                "zeroTransactionMonthCount": zero_months,
                "dataStatus": data_status,
                "sampleQuality": sample_q,
                "medianPricePerSqm": round(median(all_sqm), 2) if all_sqm else None,
                "medianPricePerSqmMethod": "full_window_median" if all_sqm else None,
                "medianPricePerSqmNote": "24개월 전수 거래 기반 ㎡당 중위(만원)" if all_sqm else None,
            }
        )
        rep_deals.append(
            {
                "province": reg["province"],
                "name": reg["name"],
                "lawdCd": lawd,
                "month": latest_month,
                "deals": best_deals,
            }
        )
        print(f"[{i}/{len(regions)}] {key_name}: {total} trades")

    (DATA / "monthly-series-24m-all.json").write_text(
        json.dumps(series_all, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA / "region-market-summary-24m.json").write_text(
        json.dumps(market, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA / "representative-deals.json").write_text(
        json.dumps(rep_deals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # refresh catalog + pages + validate
    os.system(f"{sys.executable} {ROOT/'scripts'/'build_catalog.py'}")
    os.system(f"{sys.executable} {ROOT/'scripts'/'enrich_from_deals.py'}")
    os.system(f"{sys.executable} {ROOT/'scripts'/'build_region_pages.py'}")
    return os.system(f"{sys.executable} {ROOT/'scripts'/'validate_data.py'}")


if __name__ == "__main__":
    raise SystemExit(main())
