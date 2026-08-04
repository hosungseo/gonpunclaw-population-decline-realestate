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
  <nav class="site-nav" aria-label="주요 메뉴">
    <div class="container site-nav-inner">
      <a class="site-nav-brand" href="../../index.html">인구감소지역 부동산</a>
      <div class="site-nav-links">
        <a href="../../index.html#markets">탐색</a>
        <a href="../../compare.html">비교</a>
        <a href="../../policies/second-home.html">세컨드홈</a>
        <a href="../../sources.html">출처</a>
      </div>
    </div>
  </nav>
  <header class="region-hero">
    <div class="container region-hero-inner">
      <div>
        <a class="region-back" href="../">107개 지역</a>
        <div class="region-kicker">{province} · {type_label}</div>
        <h1>{name}</h1>
        <p>지정 근거와 최근 24개월 아파트 거래 표본을 함께 봅니다.</p>
      </div>
      <div class="region-record" aria-label="지역 데이터 레코드">
        <span>REGION RECORD</span>
        <strong>{lawd}</strong>
        <small>거래 {period}<br />수집 {collected}</small>
      </div>
    </div>
  </header>
  <main class="region-page">
    <div class="container region-detail-shell">
      <section class="region-overview">
        <div class="region-section-head">
          <div>
            <span class="badge {type_class}">{type_label}</span>
            <h2>시장 표본 요약</h2>
          </div>
          <span class="sample-badge {quality_class}">표본 · {quality}</span>
        </div>
        <div class="region-metrics">
          <div><span>24개월 거래</span><strong>{total}<small>건</small></strong></div>
          <div><span>중위가격</span><strong>{median}</strong></div>
          <div><span>거래 발생 월</span><strong>{months}<small>/24</small></strong></div>
          <div><span>무거래 월</span><strong>{zero}<small>개월</small></strong></div>
        </div>
        <dl class="region-facts">
          <div><dt>데이터 상태</dt><dd>{status_label}</dd></div>
          <div><dt>최근 거래월</dt><dd>{latest}</dd></div>
          <div><dt>가격 범위</dt><dd>{price_range}</dd></div>
          <div><dt>㎡당 중위 <small>참고</small></dt><dd>{sqm}</dd></div>
        </dl>
        <p class="region-caution">{caution}</p>
        <div class="region-actions">
          <a class="btn primary" href="../../compare.html?regions={code}">비교에 넣기</a>
          <a class="btn secondary" href="../../policies/second-home.html">세컨드홈 확인</a>
          <button type="button" class="btn secondary" id="btn-cite">인용 복사</button>
        </div>
        <details class="region-citation">
          <summary>인용용 텍스트 보기</summary>
          <pre id="cite-text">{citation}</pre>
        </details>
      </section>
      <aside class="region-evidence">
        <div class="region-evidence-label">Designation</div>
        <h2>지정·출처</h2>
        <dl>
          <div><dt>지정 유형</dt><dd>{type_label}</dd></div>
          <div><dt>시군구 코드</dt><dd>{lawd}</dd></div>
          <div><dt>지정 근거 ID</dt><dd>{source_id}</dd></div>
          <div><dt>적용 시작</dt><dd>{effective_from}</dd></div>
          <div><dt>적용 종료</dt><dd>{effective_to}</dd></div>
        </dl>
        {policymap_block}
        <a class="region-source-link" href="../../sources.html">출처·방법론 전체 보기 →</a>
      </aside>
        <script>
          document.getElementById('btn-cite')?.addEventListener('click', async () => {{
            const t = document.getElementById('cite-text').textContent;
            try {{ await navigator.clipboard.writeText(t); alert('인용 텍스트를 복사했습니다.'); }}
            catch {{ prompt('복사하세요', t); }}
          }});
        </script>
    </div>
  </main>
  <footer><div class="container">인구감소지역 부동산 · 투자 권유가 아닌 정책·시장 안내 · <a href="../">지역 목록</a></div></footer>
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
        quality_class=html.escape(str(region.get("sampleQuality") or "none")),
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
    # searchable index of regions
    rows = []
    provinces = sorted({region["province"] for region in catalog["regions"]})
    for region in catalog["regions"]:
        sm = market.get(region["key"]) or {}
        designation = region["designationType"]
        designation_label = "관심지역" if designation == "interest" else "인구감소지역"
        quality = quality_label(region.get("sampleQuality"))
        search_text = f'{region["province"]} {region["name"]} {region["sigunguCode"]}'.lower()
        rows.append(
            f'<a class="region-directory-item" href="./{html.escape(region["regionSlug"])}/" '
            f'data-search="{html.escape(search_text)}" data-province="{html.escape(region["province"])}" '
            f'data-type="{html.escape(designation)}">'
            f'<span class="region-directory-name"><small>{html.escape(region["province"])}</small>'
            f'<strong>{html.escape(region["name"])}</strong></span>'
            f'<span class="region-directory-data"><small>24개월 거래</small>'
            f'<strong>{int(sm.get("totalCount24m") or 0):,}<i>건</i></strong></span>'
            f'<span class="region-directory-data"><small>표본</small><strong class="quality-text">{html.escape(quality)}</strong></span>'
            f'<span class="region-type-mark {html.escape(designation)}">{designation_label}</span>'
            f'<span class="region-directory-arrow" aria-hidden="true">↗</span></a>'
        )
    province_options = ''.join(
        f'<option value="{html.escape(province)}">{html.escape(province)}</option>'
        for province in provinces
    )
    index_html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>지역 목록 · 인구감소지역 부동산</title>
  <meta name="description" content="인구감소지역·관심지역 107곳의 최근 24개월 거래 표본과 상세 페이지를 찾습니다." />
  <link rel="preconnect" href="https://cdn.jsdelivr.net" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css" rel="stylesheet" />
  <link href="https://fonts.googleapis.com/css2?family=Literata:opsz,wght@7..72,480;7..72,560;7..72,650&family=IBM+Plex+Mono:wght@400;500;600&family=Noto+Serif+KR:wght@400;500;600&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="../assets/css/site.css" />
  <link rel="stylesheet" href="../assets/css/explore.css" />
  <link rel="stylesheet" href="../assets/css/design-upgrade.css" />
</head>
<body>
  <nav class="site-nav" aria-label="주요 메뉴">
    <div class="container site-nav-inner">
      <a class="site-nav-brand" href="../index.html">인구감소지역 부동산</a>
      <div class="site-nav-links">
        <a href="../index.html#markets">탐색</a>
        <a href="../compare.html">비교</a>
        <a href="../policies/second-home.html">세컨드홈</a>
        <a href="../sources.html">출처</a>
      </div>
    </div>
  </nav>
  <header class="directory-hero">
    <div class="container directory-hero-inner">
      <div>
        <div class="region-kicker">Region directory · 107</div>
        <h1>정책 대상 지역 찾기</h1>
        <p>이름, 시도, 시군구 코드로 지역을 찾고 거래 표본과 지정 근거를 확인하세요.</p>
      </div>
      <div class="directory-count"><strong id="directory-count">107</strong><span>표시 지역</span></div>
    </div>
  </header>
  <main class="container directory-main">
    <div class="directory-toolbar">
      <label class="directory-search"><span class="sr-only">지역 검색</span><input id="directory-search" type="search" placeholder="지역명·시도·코드 검색" autocomplete="off" /></label>
      <select id="directory-province" aria-label="시도 선택"><option value="all">시도 전체</option>{province_options}</select>
      <select id="directory-type" aria-label="지정 유형"><option value="all">유형 전체</option><option value="decline">인구감소지역</option><option value="interest">관심지역</option></select>
      <button type="button" id="directory-reset">초기화</button>
    </div>
    <div class="directory-list" id="directory-list">{''.join(rows)}</div>
    <div class="directory-empty" id="directory-empty" hidden>조건에 맞는 지역이 없습니다.</div>
  </main>
  <footer><div class="container">인구감소지역 부동산 · <a href="../index.html#markets">전국 지도</a> · <a href="../sources.html">출처</a></div></footer>
  <script>
    const search = document.getElementById('directory-search');
    const province = document.getElementById('directory-province');
    const type = document.getElementById('directory-type');
    const items = [...document.querySelectorAll('.region-directory-item')];
    const count = document.getElementById('directory-count');
    const empty = document.getElementById('directory-empty');
    function filterDirectory() {{
      const q = search.value.trim().toLowerCase();
      let visible = 0;
      items.forEach((item) => {{
        const show = (!q || item.dataset.search.includes(q)) &&
          (province.value === 'all' || item.dataset.province === province.value) &&
          (type.value === 'all' || item.dataset.type === type.value);
        item.hidden = !show;
        if (show) visible += 1;
      }});
      count.textContent = visible;
      empty.hidden = visible !== 0;
    }}
    [search, province, type].forEach((control) => control.addEventListener('input', filterDirectory));
    document.getElementById('directory-reset').addEventListener('click', () => {{
      search.value = ''; province.value = 'all'; type.value = 'all'; filterDirectory(); search.focus();
    }});
  </script>
</body>
</html>
"""
    (OUT / "index.html").write_text(index_html, encoding="utf-8")
    print(f"wrote {n} region pages + region/index.html")


if __name__ == "__main__":
    main()
