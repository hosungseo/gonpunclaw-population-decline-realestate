#!/usr/bin/env python3
"""Generate static region detail pages from catalog + market summary (R2 foundation)."""

from __future__ import annotations

import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "region"


def load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def format_price(v):
    if v is None:
        return "-"
    e, m = divmod(int(round(v)), 10000)
    if e > 0 and m > 0:
        return f"{e}.{str(round(m / 100)).zfill(2)}억"
    if e > 0:
        return f"{e}억"
    return f"{int(v):,}만원"


def quality_label(q: str) -> str:
    return {
        "none": "거래 없음",
        "very_low": "표본 매우 적음",
        "limited": "표본 제한",
        "normal": "일반",
    }.get(q or "", q or "-")


def ym(s: str | None) -> str:
    if not s or len(s) < 6:
        return "-"
    return f"{s[:4]}-{s[4:6]}"


TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <link rel="canonical" href="{canonical}" />
  <link rel="preconnect" href="https://cdn.jsdelivr.net" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,480;7..72,560;7..72,650&family=IBM+Plex+Mono:wght@400;500;600&family=Noto+Serif+KR:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../../assets/css/site.css" />
  <link rel="stylesheet" href="../../assets/css/explore.css" />
  <link rel="stylesheet" href="../../assets/css/design-upgrade.css" />
</head>
<body>
  <header class="hero" style="min-height:auto">
    <div class="container hero-inner" style="grid-template-columns:1fr;padding:48px 0 32px">
      <div>
        <div class="brand"><span class="brand-mark"></span><span class="brand-name">인구감소지역 부동산</span></div>
        <div class="eyebrow">{type_label}</div>
        <h1 style="font-size:clamp(32px,5vw,48px)">{name}</h1>
        <p class="hero-copy">{province} · 지정 근거와 최근 24개월 거래 표본</p>
        <div class="freshness-bar" style="margin-top:16px">
          <span>거래 기준 {period}</span>
          <span>수집일 {collected}</span>
          <span>표본 {quality}</span>
        </div>
        <div class="cta-row" style="margin-top:20px">
          <a class="btn secondary" href="../../index.html#markets">지도로 돌아가기</a>
          <a class="btn secondary" href="../../sources.html">출처·방법론</a>
        </div>
      </div>
    </div>
  </header>
  <main>
    <div class="container" style="padding:32px 0 64px">
      <div class="panel" style="display:block">
        <div class="badge {type_class}">{type_label}</div>
        <h2 style="margin:12px 0 8px">{name}</h2>
        <p class="muted">{province} · 시군구 코드 {lawd} · slug {slug}</p>
        <div class="metric-strip" style="margin:20px 0">
          <div><strong>{total}</strong><span>24개월 거래</span></div>
          <div><strong>{median}</strong><span>중위가격</span></div>
          <div><strong>{months}/24</strong><span>거래 발생 월</span></div>
          <div><strong>{zero}</strong><span>무거래 월</span></div>
        </div>
        <p><strong>데이터 상태:</strong> {status_label}</p>
        <p><strong>최근 거래월:</strong> {latest}</p>
        <p><strong>가격 범위:</strong> {price_range}</p>
        <p><strong>㎡당 중위(참고):</strong> {sqm}</p>
        <p class="caution">{caution}</p>
        <div class="toolbar-row" style="margin-top:16px">
          <button type="button" class="btn secondary" id="btn-cite">인용 복사</button>
          <a class="btn secondary" href="../../compare.html?regions={code}">비교에 넣기</a>
          <a class="btn secondary" href="../../policies/second-home.html">세컨드홈 확인</a>
        </div>
        <hr style="border:none;border-top:1px solid var(--line);margin:24px 0" />
        <h3>지정·출처</h3>
        <ul>
          <li>지정 유형: {type_label}</li>
          <li>지정 근거 ID: {source_id}</li>
          <li>적용 시작: {effective_from}</li>
          <li>적용 종료: {effective_to}</li>
        </ul>
        {policymap_block}
        <h3>인용용 텍스트</h3>
        <pre id="cite-text" style="white-space:pre-wrap;background:#fff;border:1px solid var(--line);padding:12px;border-radius:12px;font-size:13px">{citation}</pre>
        <p class="muted">이 페이지는 투자 권유가 아닙니다. 수치와 특례는 기준일과 공식 원문을 함께 확인하세요.</p>
        <script>
          document.getElementById('btn-cite')?.addEventListener('click', async () => {{
            const t = document.getElementById('cite-text').textContent;
            try {{ await navigator.clipboard.writeText(t); alert('인용 텍스트를 복사했습니다.'); }}
            catch {{ prompt('복사하세요', t); }}
          }});
        </script>
      </div>
    </div>
  </main>
  <footer><div class="container">인구감소지역 부동산 · 정적 지역 상세 (R1 기반 / R2 확장)</div></footer>
</body>
</html>
"""


def page_for(region: dict, market: dict | None, meta: dict, policymap_links: dict) -> str:
    sm = market or {}
    total = sm.get("totalCount24m") or 0
    months = sm.get("monthsWithTrades") or 0
    zero = sm.get("zeroTransactionMonthCount")
    if zero is None:
        zero = max(0, 24 - months)
    type_class = region["designationType"]
    type_label = (
        "인구감소관심지역"
        if type_class == "interest"
        else "인구감소지역"
    )
    period = f"{ym(sm.get('periodStart') or meta.get('transactionPeriodStart'))} ~ {ym(sm.get('periodEnd') or meta.get('transactionPeriodEnd'))}"
    status = sm.get("dataStatus") or region.get("dataStatus")
    status_label = {
        "ok": "수집 성공",
        "no_transactions": "해당 기간 확인된 거래 없음",
        "error": "수집 오류",
    }.get(status, status or "-")
    if total == 0:
        caution = "최근 24개월 거래가 확인되지 않았습니다. 무거래와 수집 오류를 구분하며, 지정 근거·특례 정보를 우선 확인하세요."
    elif months <= 6:
        caution = "거래 발생 월이 적어 중위가격이 크게 흔들릴 수 있습니다. 표본 두께를 가격과 함께 보세요."
    elif total < 80:
        caution = "표본이 제한적입니다. 개별 거래 1~2건이 중위에 큰 영향을 줄 수 있습니다."
    else:
        caution = "실거래가는 국토부 공개자료 기준이며, 투자 권유가 아니라 정책·시장 안내용입니다."

    price_range = "-"
    if sm.get("priceMin24m") is not None and sm.get("priceMax24m") is not None:
        price_range = f"{format_price(sm['priceMin24m'])} ~ {format_price(sm['priceMax24m'])}"

    title = f"{region['name']} · {type_label} | 인구감소지역 부동산"
    description = (
        f"{region['province']} {region['name']} {type_label}. "
        f"최근 24개월 거래 {total}건, 표본 {quality_label(region.get('sampleQuality'))}."
    )
    sqm_v = sm.get("medianPricePerSqm")
    sqm = f"{round(sqm_v):,}만원/㎡" if sqm_v is not None else "-"
    citation = "\n".join([
        f"{region['province']} {region['name']} ({type_label})",
        f"거래기간: {period}",
        f"24개월 거래: {total}건 / 표본: {quality_label(region.get('sampleQuality'))}",
        f"중위가격: {format_price(sm.get('median24m'))}",
        f"㎡당 중위(참고): {sqm}",
        f"수집일: {sm.get('collectedAt') or meta.get('transactionCollectedAt') or '-'}",
        "출처: 국토교통부 실거래가 공개자료 · 행정안전부 인구감소지역 지정 고시",
        f"상세: https://hosungseo.github.io/gonpunclaw-population-decline-realestate/region/{region['regionSlug']}/",
    ])
    pm = policymap_links.get(region.get("sigunguCode")) or policymap_links.get(region.get("key"))
    if pm and pm.get("verified") and pm.get("url"):
        policymap_block = (
            f"<h3>현장 지도 (PolicyMap)</h3><p><a href=\"{html.escape(pm['url'])}\" target=\"_blank\" rel=\"noopener\">"
            f"{html.escape(pm.get('title') or '검증된 공개 지도')}</a>"
            f"<br><span class=\"muted\">기준일 {html.escape(str(pm.get('asOf') or '-'))} · {html.escape(str(pm.get('owner') or ''))}</span></p>"
        )
    else:
        policymap_block = (
            "<h3>현장 지도 (PolicyMap)</h3>"
            "<p class=\"muted\">이 지역에 검증된 공개 PolicyMap 연결이 아직 없습니다. "
            "프로젝트 참고: <a href=\"https://github.com/hosungseo/k-policymap\" target=\"_blank\" rel=\"noopener\">k-policymap</a></p>"
        )
    return TEMPLATE.format(
        title=html.escape(title),
        description=html.escape(description),
        canonical=html.escape(
            f"https://hosungseo.github.io/gonpunclaw-population-decline-realestate/region/{region['regionSlug']}/"
        ),
        type_label=html.escape(type_label),
        type_class=html.escape(type_class),
        name=html.escape(region["name"]),
        province=html.escape(region["province"]),
        period=html.escape(period),
        collected=html.escape(str(sm.get("collectedAt") or meta.get("transactionCollectedAt") or "-")),
        quality=html.escape(quality_label(region.get("sampleQuality"))),
        lawd=html.escape(str(region.get("sigunguCode"))),
        slug=html.escape(region["regionSlug"]),
        total=f"{total:,}",
        median=html.escape(format_price(sm.get("median24m"))),
        months=months,
        zero=zero,
        status_label=html.escape(status_label),
        latest=html.escape(ym(sm.get("latestTradeMonth"))),
        price_range=html.escape(price_range),
        sqm=html.escape(sqm),
        caution=html.escape(caution),
        source_id=html.escape(str(region.get("designationSourceId") or "-")),
        effective_from=html.escape(str(region.get("effectiveFrom") or "-")),
        effective_to=html.escape(str(region.get("effectiveTo") or "해당 없음")),
        code=html.escape(str(region.get("sigunguCode"))),
        citation=html.escape(citation),
        policymap_block=policymap_block,
    )


def main() -> None:
    catalog = load("region-catalog.json")
    market = {m["key"]: m for m in load("region-market-summary-24m.json")}
    meta = load("site-meta.json")
    try:
        pm = load("policymap-links.json")
        policymap_links = pm.get("regions") or {}
    except FileNotFoundError:
        policymap_links = {}
    OUT.mkdir(exist_ok=True)
    n = 0
    for region in catalog["regions"]:
        slug = region["regionSlug"]
        dest = OUT / slug
        dest.mkdir(parents=True, exist_ok=True)
        html_doc = page_for(region, market.get(region["key"]), meta, policymap_links)
        (dest / "index.html").write_text(html_doc, encoding="utf-8")
        n += 1
    # index of regions
    rows = []
    for region in catalog["regions"]:
        rows.append(
            f'<li><a href="./{html.escape(region["regionSlug"])}/">'
            f'{html.escape(region["province"])} {html.escape(region["name"])}</a> '
            f'<span class="muted">({html.escape(region["designationType"])})</span></li>'
        )
    index_html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>지역 목록 · 인구감소지역 부동산</title>
  <link rel="stylesheet" href="../assets/css/site.css" />
</head>
<body>
  <main class="container" style="padding:40px 0 80px">
    <p><a href="../index.html">← 홈</a></p>
    <h1>지역 상세 (107)</h1>
    <p class="muted">R1에서 정적 URL을 확정했습니다. 각 페이지는 지정 유형·표본·기준일을 포함합니다.</p>
    <ul style="line-height:1.9;columns:2;gap:32px">{''.join(rows)}</ul>
  </main>
</body>
</html>
"""
    (OUT / "index.html").write_text(index_html, encoding="utf-8")
    print(f"wrote {n} region pages + region/index.html")


if __name__ == "__main__":
    main()
