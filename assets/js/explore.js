/* Shared explore helpers for compare / second-home / timeline */
const ExplorePage = (() => {
  const sampleLabel = (q) =>
    ({ none: "거래 없음", very_low: "표본 매우 적음", limited: "표본 제한", normal: "일반" }[q] || q || "-");
  const typeLabel = (t) => (t === "interest" ? "인구감소관심지역" : "인구감소지역");
  const ym = (s) => {
    if (!s) return "-";
    s = String(s);
    return s.length >= 6 ? `${s.slice(0, 4)}-${s.slice(4, 6)}` : s;
  };
  const formatPrice = (v) => {
    if (v == null) return "-";
    const e = Math.floor(v / 10000);
    const m = v % 10000;
    if (e > 0 && m > 0) return `${e}.${String(Math.round(m / 100)).padStart(2, "0")}억`;
    if (e > 0) return `${e}억`;
    return `${Number(v).toLocaleString()}만원`;
  };
  const formatSqm = (v) => (v == null ? "-" : `${Math.round(v).toLocaleString()}만원/㎡`);

  async function loadIndex() {
    const res = await fetch("./data/region-search-index.json");
    const data = await res.json();
    return data.regions || [];
  }

  function parseRegionsParam() {
    const q = new URLSearchParams(location.search).get("regions") || "";
    return q
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean)
      .slice(0, 3);
  }

  function writeRegionsParam(codes) {
    const url = new URL(location.href);
    if (codes.length) url.searchParams.set("regions", codes.join(","));
    else url.searchParams.delete("regions");
    history.replaceState(null, "", url);
  }

  function initCompare() {
    let regions = [];
    let selected = []; // sigunguCode list

    const search = document.getElementById("compare-search");
    const suggest = document.getElementById("compare-suggest");
    const chips = document.getElementById("compare-chips");
    const grid = document.getElementById("compare-grid");
    const empty = document.getElementById("compare-empty");
    const peers = document.getElementById("suggest-peers");

    function byCode(code) {
      return regions.find((r) => r.sigunguCode === code || r.regionSlug === code || r.key === code);
    }

    function render() {
      writeRegionsParam(selected);
      chips.innerHTML = selected
        .map((code) => {
          const r = byCode(code);
          if (!r) return "";
          return `<span class="chip">${r.province} ${r.name}<button type="button" data-remove="${r.sigunguCode}" aria-label="제거">×</button></span>`;
        })
        .join("");
      chips.querySelectorAll("[data-remove]").forEach((btn) => {
        btn.addEventListener("click", () => {
          selected = selected.filter((c) => c !== btn.dataset.remove);
          render();
        });
      });

      const items = selected.map(byCode).filter(Boolean);
      if (items.length < 2) {
        grid.innerHTML = "";
        empty.hidden = false;
      } else {
        empty.hidden = true;
        grid.innerHTML = items
          .map((r) => {
            const warn =
              r.sampleQuality === "none" || r.sampleQuality === "very_low" || r.sampleQuality === "limited"
                ? `<div class="warn-box" style="margin-top:12px;padding:10px 12px;font-size:13px">표본 경고: ${sampleLabel(r.sampleQuality)}. 가격만으로 비교하지 마세요.</div>`
                : "";
            return `<article class="compare-card">
              <div class="sample-badge ${r.designationType === "interest" ? "limited" : "normal"}">${typeLabel(r.designationType)}</div>
              <h3>${r.name}</h3>
              <div class="muted">${r.province}</div>
              <dl style="margin-top:14px">
                <div><dt>24개월 거래</dt><dd>${(r.totalCount24m || 0).toLocaleString()}건</dd></div>
                <div><dt>거래 발생 월</dt><dd>${r.monthsWithTrades || 0}/24</dd></div>
                <div><dt>무거래 월</dt><dd>${r.zeroTransactionMonthCount ?? "-"}</dd></div>
                <div><dt>중위가격</dt><dd>${formatPrice(r.median24m)}</dd></div>
                <div><dt>㎡당 중위(참고)</dt><dd>${formatSqm(r.medianPricePerSqm)}</dd></div>
                <div><dt>최근 거래월</dt><dd>${ym(r.latestTradeMonth)}</dd></div>
                <div><dt>표본 품질</dt><dd>${sampleLabel(r.sampleQuality)}</dd></div>
              </dl>
              <p style="margin-top:12px"><a href="./region/${encodeURIComponent(r.regionSlug)}/">상세 페이지</a></p>
              ${warn}
            </article>`;
          })
          .join("");
      }

      // peer suggestions from first selection
      if (!items.length) {
        peers.innerHTML = "";
        return;
      }
      const base = items[0];
      const candidates = regions
        .filter((r) => r.sigunguCode !== base.sigunguCode && !selected.includes(r.sigunguCode))
        .map((r) => {
          let score = 0;
          if (r.province === base.province) score += 3;
          if (r.designationType === base.designationType) score += 2;
          const diff = Math.abs((r.totalCount24m || 0) - (base.totalCount24m || 0));
          score += Math.max(0, 2 - diff / 500);
          return { r, score };
        })
        .sort((a, b) => b.score - a.score)
        .slice(0, 6);
      peers.innerHTML = `<h3>비교 후보 제안</h3>
        <div class="chip-row">${candidates
          .map(
            ({ r }) =>
              `<button type="button" class="chip" data-add="${r.sigunguCode}">${r.province} ${r.name} · ${sampleLabel(r.sampleQuality)}</button>`
          )
          .join("")}</div>
        <p class="muted" style="margin:10px 0 0">같은 시도·지정 유형·비슷한 거래 규모를 우선합니다.</p>`;
      peers.querySelectorAll("[data-add]").forEach((btn) => {
        btn.addEventListener("click", () => add(btn.dataset.add));
      });
    }

    function add(code) {
      const r = byCode(code);
      if (!r) return;
      if (selected.includes(r.sigunguCode)) return;
      if (selected.length >= 3) {
        alert("비교는 최대 3개까지입니다.");
        return;
      }
      selected.push(r.sigunguCode);
      render();
    }

    function showSuggest(q) {
      q = (q || "").trim().toLowerCase();
      if (!q) {
        suggest.hidden = true;
        suggest.innerHTML = "";
        return;
      }
      const hits = regions
        .filter((r) => r.searchText.toLowerCase().includes(q) || r.name.includes(q))
        .slice(0, 12);
      if (!hits.length) {
        suggest.hidden = true;
        return;
      }
      suggest.hidden = false;
      suggest.innerHTML = hits
        .map(
          (r) =>
            `<button type="button" data-code="${r.sigunguCode}">${r.province} ${r.name} · ${typeLabel(r.designationType)}</button>`
        )
        .join("");
      suggest.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => {
          add(btn.dataset.code);
          search.value = "";
          suggest.hidden = true;
        });
      });
    }

    loadIndex().then((list) => {
      regions = list;
      selected = parseRegionsParam()
        .map((c) => byCode(c)?.sigunguCode)
        .filter(Boolean);
      render();
    });

    search.addEventListener("input", () => showSuggest(search.value));
    document.getElementById("btn-clear").addEventListener("click", () => {
      selected = [];
      render();
    });
    document.getElementById("btn-copy-url").addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(location.href);
        alert("비교 URL을 복사했습니다.");
      } catch {
        prompt("이 주소를 복사하세요", location.href);
      }
    });
    document.getElementById("btn-csv").addEventListener("click", () => {
      const items = selected.map(byCode).filter(Boolean);
      if (items.length < 2) {
        alert("CSV는 2개 이상 선택 후 받을 수 있습니다.");
        return;
      }
      const header = [
        "province",
        "name",
        "designationType",
        "totalCount24m",
        "monthsWithTrades",
        "zeroTransactionMonthCount",
        "median24m",
        "medianPricePerSqm",
        "latestTradeMonth",
        "sampleQuality",
        "sigunguCode",
      ];
      const rows = items.map((r) => header.map((h) => JSON.stringify(r[h] ?? "")).join(","));
      const csv = [header.join(","), ...rows].join("\n");
      const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `region-compare-${selected.join("-")}.csv`;
      a.click();
      URL.revokeObjectURL(a.href);
    });
  }

  function initSecondHome() {
    const base = location.pathname.includes("/policies/") ? "../" : "./";
    Promise.all([
      fetch(base + "data/second-home-checklist.json").then((r) => r.json()),
      fetch(base + "data/source-manifest.json").then((r) => r.json()),
    ]).then(([cfg, manifest]) => {
      document.getElementById("disclaimer").textContent = cfg.disclaimer;
      const answers = {};
      const stepsEl = document.getElementById("steps");
      const resultEl = document.getElementById("result");

      // block if critical sources expired
      const blocked = (cfg.sourceIds || []).some((id) => {
        const s = (manifest.sources || []).find((x) => x.sourceId === id);
        return s && (s.status === "expired" || s.status === "unavailable");
      });
      if (blocked) {
        stepsEl.innerHTML =
          '<div class="warn-box">관련 근거가 만료·이용불가 상태라 체크리스트 결과를 제공하지 않습니다. 공식 원문을 직접 확인하세요.</div>';
        return;
      }

      stepsEl.innerHTML = (cfg.steps || [])
        .map((step) => {
          const opts = (step.options || [])
            .map(
              (o) =>
                `<label><input type="radio" name="${step.id}" value="${o.id}" data-score="${o.score}" /> ${o.label}</label>`
            )
            .join("");
          return `<section class="step-card" data-step="${step.id}">
            <h3>${step.question}</h3>
            <p class="muted">${step.help || ""}</p>
            <div class="option-row">${opts}</div>
          </section>`;
        })
        .join("");

      function compute() {
        const scores = (cfg.steps || []).map((step) => answers[step.id]).filter(Boolean);
        if (scores.length < (cfg.steps || []).length) {
          resultEl.hidden = true;
          return;
        }
        let key = "possible";
        if (scores.includes("out_of_scope")) key = "out_of_scope";
        else if (scores.includes("extra_check")) key = "extra_check";
        const res = cfg.resultRules[key];
        resultEl.hidden = false;
        resultEl.innerHTML = `<strong>${res.label}</strong><p>${res.detail}</p>
          <p class="muted">이 결과는 저장되지 않으며 세무 확정 판단이 아닙니다.</p>`;
      }

      stepsEl.querySelectorAll('input[type="radio"]').forEach((input) => {
        input.addEventListener("change", () => {
          answers[input.name] = input.dataset.score;
          compute();
        });
      });

      document.getElementById("official-links").innerHTML = (cfg.officialLinks || [])
        .map((l) => `<li><a href="${l.url}" target="_blank" rel="noopener">${l.label}</a></li>`)
        .join("");
    });
  }

  function initTimeline() {
    const base = location.pathname.includes("/policies/") ? "../" : "./";
    Promise.all([
      fetch(base + "data/policy-timeline.json").then((r) => r.json()),
      fetch(base + "data/source-manifest.json").then((r) => r.json()),
    ]).then(([tl, manifest]) => {
      const srcMap = Object.fromEntries((manifest.sources || []).map((s) => [s.sourceId, s]));
      const events = (tl.events || []).slice().sort((a, b) => (a.date < b.date ? 1 : -1));
      document.getElementById("timeline").innerHTML = events
        .map((e) => {
          const links = (e.sourceIds || [])
            .map((id) => srcMap[id])
            .filter(Boolean)
            .map((s) => `<a href="${s.url}" target="_blank" rel="noopener">${s.title}</a>`)
            .join(" · ");
          return `<article class="tl-item ${e.status || ""}">
            <div class="tl-date">${e.date} · ${e.category} · ${e.status}</div>
            <h3>${e.title}</h3>
            <p>${e.summary}</p>
            <div class="muted">${links || "출처 연결 없음"}</div>
          </article>`;
        })
        .join("");
    });
  }

  return { initCompare, initSecondHome, initTimeline, loadIndex, sampleLabel, formatPrice, formatSqm, ym, typeLabel };
})();
