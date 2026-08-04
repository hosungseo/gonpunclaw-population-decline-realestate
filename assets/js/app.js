const badge = document.getElementById('panel-badge');
const ptitle = document.getElementById('panel-title');
const sub = document.getElementById('panel-sub');
const stat1 = document.getElementById('panel-stat-1');
const stat2 = document.getElementById('panel-stat-2');
const deals = document.getElementById('panel-deals');
const policy = document.getElementById('panel-policy');
const countChart = document.getElementById('count-chart');
const medianChart = document.getElementById('median-chart');
const countCaption = document.getElementById('count-caption');
const medianCaption = document.getElementById('median-caption');
const insight = document.getElementById('panel-insight');
const caution = document.getElementById('panel-caution');
const provinceFilter = document.getElementById('province-filter');
const typeFilter = document.getElementById('type-filter');
const select = document.getElementById('region-select');
const zoomNote = document.getElementById('map-zoom-note');
const mapReset = document.getElementById('map-reset');
const regionList = document.getElementById('map-region-list');
const regionSearch = document.getElementById('region-search');
const searchSuggest = document.getElementById('search-suggest');
const tradeVolumeFilter = document.getElementById('trade-volume-filter');
const listHint = document.getElementById('list-hint');
const mapLoading = document.getElementById('map-loading');
const heroSearchForm = document.getElementById('hero-search-form');
const heroRegionSearch = document.getElementById('hero-region-search');

heroSearchForm?.addEventListener('submit', (event) => {
  event.preventDefault();
  const query = heroRegionSearch?.value.trim() || '';
  document.getElementById('markets')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  window.setTimeout(() => {
    if (query) {
      regionSearch.value = query;
      regionSearch.dispatchEvent(new Event('input', { bubbles: true }));
    }
    regionSearch.focus({ preventScroll: true });
  }, 420);
});

const COMPARE_KEY = 'pop-decline-compare-v1';
let monthlySeries = {};
let marketSummary = [];
let selectedLayer = null;
let siteMeta = null;
let regionCatalog = null;
let compareSelection = loadCompare();
let currentKey = null;
let filteredKeys = [];

function loadCompare(){
  try {
    const raw = localStorage.getItem(COMPARE_KEY);
    const arr = raw ? JSON.parse(raw) : [];
    return Array.isArray(arr) ? arr.filter(Boolean).slice(0, 3) : [];
  } catch { return []; }
}
function saveCompare(){
  try { localStorage.setItem(COMPARE_KEY, JSON.stringify(compareSelection)); } catch {}
}

function showToast(msg){
  const el = document.getElementById('toast');
  if(!el) return;
  el.hidden = false;
  el.textContent = msg;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(()=>{ el.hidden = true; }, 2200);
}

function ymLabel(ym){
  if(!ym || String(ym).length < 6) return '-';
  const s=String(ym);
  return s.slice(0,4)+'-'+s.slice(4,6);
}
function sampleLabel(q){
  return ({none:'거래 없음',very_low:'표본 매우 적음',limited:'표본 제한',normal:'일반'})[q]||q||'-';
}
function statusLabel(s){
  return ({ok:'수집 성공',no_transactions:'해당 기간 확인된 거래 없음',error:'수집 오류'})[s]||s||'-';
}
function formatSqm(v){
  if(v==null) return '-';
  return Math.round(v).toLocaleString()+'만원/㎡';
}
function formatPrice(v){
  if(v==null) return '-';
  const e=Math.floor(v/10000),m=v%10000;
  if(e>0&&m>0) return e+'.'+String(Math.round(m/100)).padStart(2,'0')+'억';
  if(e>0) return e+'억';
  return v.toLocaleString()+'만원';
}

function renderFreshness(){
  const el=document.getElementById('freshness-bar');
  if(!el || !siteMeta) return;
  const p1=ymLabel(siteMeta.transactionPeriodStart);
  const p2=ymLabel(siteMeta.transactionPeriodEnd);
  el.innerHTML =
    '<span><strong>거래 기준</strong> '+p1+' ~ '+p2+'</span>'+
    '<span><strong>수집일</strong> '+(siteMeta.transactionCollectedAt||'-')+'</span>'+
    '<span><strong>사이트 갱신</strong> '+(siteMeta.lastSiteUpdate||'-')+'</span>'+
    '<span><strong>법령 확인</strong> '+(siteMeta.policyLastVerifiedAt||'-')+'</span>'+
    '<span><a href="./sources.html">출처</a></span>'+
    '<span><a href="./compare.html">비교</a></span>'+
    '<span><a href="./policies/">특례</a></span>';
  const foot=document.getElementById('footer-freshness');
  if(foot){
    foot.textContent = '거래 '+p1+'~'+p2+' · 수집 '+ (siteMeta.transactionCollectedAt||'-') + ' · 갱신 '+(siteMeta.lastSiteUpdate||'-');
  }
}

function renderBars(c,vals,kind,fmt){
  const nums=vals.map(v=>v??0),mx=Math.max(...nums,1);
  const avg=nums.reduce((a,b)=>a+b,0)/nums.length;
  const ab=Math.max(0,Math.min(84,(avg/mx)*84));
  const lbl=fmt?fmt(avg):Math.round(avg).toLocaleString();
  c.innerHTML='<div class="mini-avg-line '+(kind==='interest'?'interest':'')+'" style="bottom:'+ab+'px"></div><div class="mini-avg-label" style="bottom:'+ab+'px">평균 '+lbl+'</div>'+nums.map(v=>{
    const h=Math.max(3,Math.round(((v??0)/mx)*84));
    return '<div class="mini-bar '+(kind==='interest'?'interest':'')+'" style="height:'+h+'px"></div>';
  }).join('');
  return avg;
}
function buildInsight(p,s){
  const t=s?.totalCount24m??0,m=s?.monthsWithTrades??0;
  if(t===0) return '최근 24개월 기준 아파트 실거래가 확인되지 않아, 정책 정보 중심으로 해석하는 편이 맞습니다.';
  if(m<=6) return '최근 24개월 중 거래가 확인된 달이 '+m+'개월로 적어, 가격보다 거래 존재 여부 자체를 먼저 보는 지역입니다.';
  if(t<80) return '거래는 이어지고 있지만 표본이 두껍지는 않아, 개별 거래가격보다 범위와 최근 거래월을 함께 보는 것이 좋습니다.';
  if(t<400) return '거래가 희소 지역은 아니어서 최근 2년 흐름을 참고할 수 있지만, 월별 변동은 여전히 크게 튈 수 있습니다.';
  return '최근 24개월 거래가 비교적 충분히 누적돼, 이 지역은 정책 대상 지역 중에서도 시장 흐름을 읽어볼 만한 편입니다.';
}
function buildCaution(s){
  const t=s?.totalCount24m??0,m=s?.monthsWithTrades??0;
  if(s?.apiGapRestored) return '참고: 일부 지역은 실시간 API 공백으로 직전 검증 스냅샷을 표시합니다. 출처 페이지의 수집 메모를 확인하세요.';
  if(t===0) return '주의: 최근 24개월 거래가 없어 그래프 해석보다 지정 유형과 특례 방향을 우선 확인하세요.';
  if(m<=6) return '주의: 거래가 '+m+'개월만 확인돼 월별 중위가격이 크게 흔들릴 수 있습니다.';
  if(t<80) return '주의: 표본이 얇은 지역은 특정 단지 1~2건이 중위가격에 큰 영향을 줄 수 있습니다.';
  return '실거래가는 국토부 공개자료 기준이며, 투자 권유가 아니라 정책·시장 안내용입니다.';
}
function genericData(pt,sm){
  const kind=pt.regionType==='interest'?'인구감소관심지역':'인구감소지역';
  const total=sm?.totalCount24m??0,months=sm?.monthsWithTrades??0;
  const latest=sm?.latestTradeMonth?sm.latestTradeMonth.slice(0,4)+'-'+sm.latestTradeMonth.slice(4,6):'확인 중';
  const median=sm?.median24m!=null?formatPrice(Math.round(sm.median24m)):'없음';
  const range=sm?.priceMin24m!=null&&sm?.priceMax24m!=null?formatPrice(sm.priceMin24m)+'~'+formatPrice(sm.priceMax24m):'거래 확인 중';
  const sqm=sm?.medianPricePerSqm!=null?formatSqm(sm.medianPricePerSqm):'면적 표본 없음';
  const rd=(window._repDeals||[]).find(d=>d.province===pt.province&&d.name===pt.name);
  const dealRows=(rd&&rd.deals&&rd.deals.length>0)?rd.deals.map(d=>[d.name||'거래',d.area+'㎡ · '+d.year+'년 · '+(d.road||''),formatPrice(d.price)]):[['최근 거래월',latest,months>0?months+'개월에서 거래 확인':'거래 희소'],['24개월 중위가격',median,sm?.latestMedian!=null?'최근월 중위 '+formatPrice(Math.round(sm.latestMedian)):'최근월 중위 없음'],['㎡당 중위(참고)',sqm,sm?.medianPricePerSqmNote||'대표 거래 기반']];
  return {
    badgeClass:pt.regionType,
    badge:'선택 지역 · '+kind,
    title:pt.name,
    sub:pt.province+' · 최근 24개월 아파트 실거래와 정책 지위',
    stat1:'최근 24개월 '+total.toLocaleString()+'건',
    stat2:range+' · '+sqm,
    deals:dealRows,
    policy:pt.regionType==='interest'
      ? '적용 특례 예시 · 관심지역 대응계획 · 세컨드홈 범위 확인 · 특례 섹션 참고'
      : '적용 특례 예시 · 주거·정주 인센티브 · 양도세·종부세 특례 · 특례 섹션 참고'
  };
}

function catalogByKey(key){
  return (regionCatalog?.regions||[]).find(r=>r.key===key);
}

function renderCompareTray(){
  const tray=document.getElementById('compare-tray');
  if(!tray) return;
  if(!compareSelection.length){
    tray.innerHTML='<span class="muted">비교함 비어 있음 · 패널에서 「비교에 추가」(최대 3)</span> <a class="btn secondary" href="./compare.html">비교 페이지</a>';
    return;
  }
  const labels=compareSelection.map(code=>{
    const r=(regionCatalog?.regions||[]).find(x=>x.sigunguCode===code);
    return r? r.name : code;
  });
  tray.innerHTML =
    '<span><strong>비교함</strong> '+labels.join(' · ')+' <span class="muted">('+compareSelection.length+'/3)</span></span>'+
    '<a class="btn primary" href="./compare.html?regions='+encodeURIComponent(compareSelection.join(','))+'">비교 열기</a>'+
    '<button type="button" class="btn secondary" id="compare-clear">비우기</button>';
  document.getElementById('compare-clear')?.addEventListener('click',()=>{
    compareSelection=[];
    saveCompare();
    renderCompareTray();
    showToast('비교함을 비웠습니다');
  });
}

function setRegionUrl(key){
  const cat=catalogByKey(key);
  const url=new URL(location.href);
  if(cat){
    url.searchParams.set('region', cat.sigunguCode);
  } else {
    url.searchParams.set('region', key);
  }
  history.replaceState(null, '', url);
}

function renderPanel(data,key){
  currentKey=key;
  badge.className='badge '+data.badgeClass;
  badge.textContent=data.badge;
  ptitle.textContent=data.title;
  sub.textContent=data.sub;
  stat1.textContent=data.stat1;
  stat2.textContent=data.stat2;
  deals.innerHTML=data.deals.map(i=>'<li><div><strong>'+i[0]+'</strong><small>'+i[1]+'</small></div><div class="deal-price">'+i[2]+'</div></li>').join('');
  policy.textContent=data.policy;
  const sm=marketSummary.find(s=>s.key===key);
  insight.textContent=buildInsight({regionType:data.badgeClass},sm);
  caution.textContent=buildCaution(sm);
  const series=monthlySeries[key]?.series||[];
  if(series.length){
    renderBars(countChart,series.map(s=>s.count),data.badgeClass,v=>Math.round(v).toLocaleString()+'건');
    renderBars(medianChart,series.map(s=>s.median),data.badgeClass,v=>formatPrice(Math.round(v)));
    const nz=series.filter(s=>s.count>0).length;
    countCaption.textContent=ymLabel(series[0].month)+' ~ '+ymLabel(series[series.length-1].month)+' · 거래월 '+nz+'개월';
    medianCaption.textContent=ymLabel(series[0].month)+' ~ '+ymLabel(series[series.length-1].month)+' · 중위 실거래가(만원)';
  } else {
    countChart.innerHTML='';medianChart.innerHTML='';
    countCaption.textContent='시계열 없음';
    medianCaption.textContent='시계열 없음';
  }

  const metaRow=document.getElementById('panel-meta');
  if(metaRow){
    const q=sm?.sampleQuality||'normal';
    const st=sm?.dataStatus||'ok';
    const zero=sm?.zeroTransactionMonthCount;
    const cat=catalogByKey(key);
    const restored = sm?.apiGapRestored
      ? '<span class="sample-badge restored">스냅샷 복구</span>'
      : '';
    metaRow.innerHTML =
      '<span class="sample-badge '+q+'">표본 · '+sampleLabel(q)+'</span>'+
      restored+
      '<span class="data-status-note">상태: '+statusLabel(st)+
      (zero!=null?' · 무거래 월 '+zero+'개':'')+
      (sm?.medianPricePerSqm!=null?' · ㎡당 '+formatSqm(sm.medianPricePerSqm):'')+
      (sm?.collectedAt?' · 수집 '+sm.collectedAt:'')+
      '</span>'+
      '<div class="panel-actions">'+
      (cat? '<a class="btn secondary" href="./region/'+encodeURIComponent(cat.regionSlug)+'/">지역 상세</a>' : '')+
      ' <button type="button" class="btn secondary" id="btn-add-compare">비교에 추가</button>'+
      ' <button type="button" class="btn secondary" id="btn-copy-cite">인용 복사</button>'+
      ' <button type="button" class="btn secondary" id="btn-share-region">링크 복사</button>'+
      ' <a class="btn secondary" href="./policies/second-home.html">세컨드홈</a>'+
      '</div>';

    document.getElementById('btn-add-compare')?.addEventListener('click',()=>{
      if(!cat) return;
      if(compareSelection.includes(cat.sigunguCode)){
        showToast('이미 비교함에 있습니다');
        return;
      }
      if(compareSelection.length>=3){
        showToast('비교는 최대 3개입니다');
        return;
      }
      compareSelection.push(cat.sigunguCode);
      saveCompare();
      renderCompareTray();
      showToast(cat.name+'을(를) 비교함에 담았습니다');
    });
    document.getElementById('btn-copy-cite')?.addEventListener('click', async ()=>{
      if(!cat) return;
      const text = [
        cat.province+' '+cat.name+' ('+(cat.designationType==='interest'?'인구감소관심지역':'인구감소지역')+')',
        '거래기간: '+ymLabel(sm?.periodStart)+' ~ '+ymLabel(sm?.periodEnd),
        '24개월 거래: '+(sm?.totalCount24m??0)+'건 / 표본: '+sampleLabel(sm?.sampleQuality),
        '중위가격: '+(sm?.median24m!=null?formatPrice(Math.round(sm.median24m)):'-'),
        '㎡당 중위(참고): '+formatSqm(sm?.medianPricePerSqm),
        '수집일: '+(sm?.collectedAt||'-'),
        '출처: 국토교통부 실거래가 · 행정안전부 인구감소지역 지정 고시',
        '상세: https://hosungseo.github.io/gonpunclaw-population-decline-realestate/region/'+encodeURIComponent(cat.regionSlug)+'/'
      ].join('\n');
      try { await navigator.clipboard.writeText(text); showToast('인용 텍스트를 복사했습니다'); }
      catch { prompt('복사하세요', text); }
    });
    document.getElementById('btn-share-region')?.addEventListener('click', async ()=>{
      const shareUrl = new URL(location.href);
      if(cat) shareUrl.searchParams.set('region', cat.sigunguCode);
      shareUrl.hash = 'markets';
      try {
        await navigator.clipboard.writeText(shareUrl.toString());
        showToast('지역 링크를 복사했습니다');
      } catch {
        prompt('복사하세요', shareUrl.toString());
      }
    });
  }
  setRegionUrl(key);
}

// Leaflet
const map = L.map('leaflet-map',{center:[35.9,127.8],zoom:7,minZoom:6,maxZoom:12,attributionControl:false});
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png',{subdomains:'abcd',maxZoom:19}).addTo(map);

let districtLayers={}, points=[], selectRegion=()=>{};

function invalidateMapSoon(){
  setTimeout(()=>map.invalidateSize(), 50);
  setTimeout(()=>map.invalidateSize(), 300);
}

Promise.all([
  fetch('./data/provinces.geojson').then(r=>r.json()),
  fetch('./data/target-districts.geojson').then(r=>r.json()),
  fetch('./data/map-points.json').then(r=>r.json()),
  fetch('./data/monthly-series-24m-all.json').then(r=>r.json()).catch(()=>({})),
  fetch('./data/region-market-summary-24m.json').then(r=>r.json()).catch(()=>[]),
  fetch('./data/representative-deals.json').then(r=>r.json()).catch(()=>[]),
  fetch('./data/site-meta.json').then(r=>r.json()).catch(()=>null),
  fetch('./data/region-catalog.json').then(r=>r.json()).catch(()=>null)
]).then(([provGeo,distGeo,pts,ser,sum,dl,meta,catalog])=>{
  monthlySeries=ser||{};marketSummary=sum||[];window._repDeals=dl||[];points=pts;
  siteMeta=meta; regionCatalog=catalog;
  renderFreshness();
  renderCompareTray();
  if(mapLoading) mapLoading.classList.add('is-done');

  L.geoJSON(provGeo,{style:{fillColor:'#e8e4dc',fillOpacity:0.3,color:'#bbb',weight:1}}).addTo(map);

  L.geoJSON(distGeo,{
    style:f=>({fillColor:f.properties.regionType==='interest'?'#b57a2a':'#1f5f4a',fillOpacity:0.35,color:'#fff',weight:1.2}),
    onEachFeature:(f,layer)=>{
      const p=f.properties;
      layer.bindTooltip(p.province+' '+p.name,{sticky:true});
      districtLayers[p.key]=layer;
      layer.on('click',()=>{
        selectRegion(p.key);
        document.getElementById('region-panel')?.scrollIntoView({behavior:'smooth',block:'nearest'});
      });
      layer.on('mouseover',()=>{if(selectedLayer!==layer)layer.setStyle({fillOpacity:0.55,weight:2});});
      layer.on('mouseout',()=>{if(selectedLayer!==layer)layer.setStyle({fillOpacity:0.35,weight:1.2});});
    }
  }).addTo(map);

  selectRegion=function(key){
    if(selectedLayer)selectedLayer.setStyle({fillOpacity:0.35,weight:1.2,color:'#fff'});
    const layer=districtLayers[key];
    if(layer){
      selectedLayer=layer;
      layer.setStyle({fillOpacity:0.7,weight:3,color:'#1d1b18'});
      layer.bringToFront();
    }
    const pt=points.find(p=>p.key===key);
    if(pt){
      const sm=marketSummary.find(s=>s.key===key);
      renderPanel(genericData(pt,sm),key);
      if(select) select.value=key;
      Array.from(regionList.children).forEach(p=>p.classList.remove('active'));
      const pill=regionList.querySelector('[data-key="'+CSS.escape(key)+'"]');
      if(pill){
        pill.classList.add('active');
        pill.scrollIntoView({block:'nearest'});
      }
    }
    invalidateMapSoon();
  };

  const provinces=[...new Set(points.map(p=>p.province))].sort();
  provinces.forEach(pr=>{
    const o=document.createElement('option');
    o.value=pr; o.textContent=pr;
    provinceFilter.appendChild(o);
  });

  function volumeOk(pt){
    if(!tradeVolumeFilter || tradeVolumeFilter.value==='all') return true;
    const sm=marketSummary.find(s=>s.key===pt.key);
    const t=sm?.totalCount24m||0;
    const v=tradeVolumeFilter.value;
    if(v==='zero') return t===0;
    if(v==='low') return t>0 && t<80;
    if(v==='mid') return t>=80 && t<400;
    if(v==='high') return t>=400;
    if(v==='recent') return (sm?.monthsWithTrades||0)>0;
    return true;
  }

  function applyFilters(){
    const pv=provinceFilter.value,tp=typeFilter.value;
    const q=(regionSearch?.value||'').trim().toLowerCase();
    select.innerHTML='<option value="">지역 선택</option>';
    regionList.innerHTML='';

    Object.entries(districtLayers).forEach(([k,layer])=>{
      const p=layer.feature.properties;
      const text=(p.province+' '+p.name+' '+(p.lawdCd||'')).toLowerCase();
      const ok=(pv==='all'||p.province===pv)&&(tp==='all'||p.regionType===tp)&&volumeOk({key:k})&&(!q||text.includes(q));
      layer.setStyle({fillOpacity:ok?0.35:0.05, weight: ok?1.2:0.6});
    });

    const filtered=points.filter(p=>{
      const text=(p.province+' '+p.name+' '+(p.lawdCd||'')).toLowerCase();
      return (pv==='all'||p.province===pv)&&(tp==='all'||p.regionType===tp)&&volumeOk(p)&&(!q||text.includes(q));
    }).sort((a,b)=> (a.province+a.name).localeCompare(b.province+b.name,'ko'));
    filteredKeys = filtered.map(p=>p.key);

    const showList = filtered.length <= 48 || pv !== 'all' || !!q || tp !== 'all' || (tradeVolumeFilter && tradeVolumeFilter.value !== 'all');
    if(listHint){
      listHint.textContent = showList
        ? filtered.length+'곳 · 클릭하여 패널 열기'
        : '시도를 고르거나 검색하면 목록이 열립니다 (현재 '+filtered.length+'곳)';
    }

    filtered.forEach(pt=>{
      const o=document.createElement('option');
      o.value=pt.key;
      o.textContent=pt.province+' '+pt.name;
      select.appendChild(o);
    });

    if(showList){
      const listItems = filtered.slice(0, 80);
      listItems.forEach(pt=>{
        const sm=marketSummary.find(s=>s.key===pt.key);
        const pill=document.createElement('button');
        pill.type='button';
        pill.className='region-pill '+pt.regionType+(currentKey===pt.key?' active':'');
        pill.dataset.key=pt.key;
        const count = sm?.totalCount24m ?? 0;
        pill.innerHTML = '<span>'+pt.name+'</span><span class="pill-meta">'+(count? count.toLocaleString()+'건' : '무거래')+'</span>';
        pill.addEventListener('click',()=>selectRegion(pt.key));
        regionList.appendChild(pill);
      });
      if(filtered.length > 80){
        const more=document.createElement('div');
        more.className='muted';
        more.style.padding='8px';
        more.textContent='외 '+(filtered.length-80)+'곳은 검색으로 좁혀 보세요';
        regionList.appendChild(more);
      }
    } else {
      const tip=document.createElement('div');
      tip.className='muted';
      tip.style.padding='8px 4px';
      tip.textContent='전국 107곳은 지도에서 바로 고르거나, 시도·검색으로 목록을 여세요.';
      regionList.appendChild(tip);
    }

    const countEl=document.getElementById('filter-count');
    if(countEl) countEl.textContent='표시 '+filtered.length+'곳';

    if(pv!=='all'){
      const layers=filtered.map(p=>districtLayers[p.key]).filter(Boolean);
      if(layers.length) map.fitBounds(L.featureGroup(layers).getBounds(),{padding:[28,28]});
      if(zoomNote) zoomNote.textContent=pv+' 확대';
    } else if(q && filtered.length && filtered.length <= 12){
      const layers=filtered.map(p=>districtLayers[p.key]).filter(Boolean);
      if(layers.length) map.fitBounds(L.featureGroup(layers).getBounds(),{padding:[28,28]});
      if(zoomNote) zoomNote.textContent='검색 '+filtered.length+'곳';
    } else if(q && filtered.length===0){
      if(zoomNote) zoomNote.textContent='검색 결과 없음';
    } else {
      map.setView([35.9,127.8],7);
      if(zoomNote) zoomNote.textContent='전국 보기';
    }

    if(searchSuggest){
      if(!q){ searchSuggest.hidden=true; searchSuggest.innerHTML=''; }
      else {
        const hits=filtered.slice(0,12);
        searchSuggest.hidden=!hits.length;
        searchSuggest.innerHTML=hits.map(pt=>{
          const sm=marketSummary.find(s=>s.key===pt.key);
          const kind=pt.regionType==='interest'?'관심':'감소';
          return '<button type="button" data-key="'+pt.key+'">'+pt.province+' '+pt.name+' · '+kind+' · '+((sm?.totalCount24m||0).toLocaleString())+'건</button>';
        }).join('');
        searchSuggest.querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{
          selectRegion(btn.dataset.key);
          searchSuggest.hidden=true;
          const pt=points.find(p=>p.key===btn.dataset.key);
          if(regionSearch && pt) regionSearch.value=pt.name;
        }));
      }
    }
    invalidateMapSoon();
  }

  provinceFilter.addEventListener('change',applyFilters);
  typeFilter.addEventListener('change',applyFilters);
  if(tradeVolumeFilter) tradeVolumeFilter.addEventListener('change',applyFilters);
  if(regionSearch){
    regionSearch.addEventListener('input',applyFilters);
    regionSearch.addEventListener('keydown',e=>{
      if(e.key==='Enter'){
        e.preventDefault();
        const first=searchSuggest?.querySelector('button');
        if(first) first.click();
        else if(filteredKeys[0]) selectRegion(filteredKeys[0]);
      }
      if(e.key==='Escape'){
        searchSuggest.hidden=true;
      }
    });
  }
  mapReset.addEventListener('click',()=>{
    provinceFilter.value='all';
    typeFilter.value='all';
    if(tradeVolumeFilter) tradeVolumeFilter.value='all';
    if(regionSearch) regionSearch.value='';
    applyFilters();
    showToast('필터를 초기화했습니다');
  });
  select.addEventListener('change',()=>{if(select.value)selectRegion(select.value);});

  // Compare table
  const tbody=document.getElementById('compare-tbody');
  const tableFilter=document.getElementById('table-province-filter');
  const tableEl=document.getElementById('compare-table');
  let sortCol='totalCount24m',sortAsc=false;
  function renderTable(){
    if(!tbody || !tableFilter) return;
    const pv=tableFilter.value;
    let data=marketSummary.filter(s=>pv==='all'||s.province===pv);
    data.sort((a,b)=>{
      let va=a[sortCol]??0, vb=b[sortCol]??0;
      if(typeof va==='string') return sortAsc ? va.localeCompare(vb,'ko') : vb.localeCompare(va,'ko');
      return sortAsc?(va>vb?1:-1):(va<vb?1:-1);
    });
    tbody.innerHTML=data.map(s=>{
      const tb=s.regionType==='interest'?'<span class="type-badge interest">관심</span>':'<span class="type-badge decline">감소</span>';
      return '<tr style="cursor:pointer" data-key="'+s.key+'"><td>'+s.province+'</td><td>'+s.name+'</td><td>'+tb+'</td><td>'+(s.totalCount24m||0).toLocaleString()+'</td><td>'+(s.median24m!=null?formatPrice(Math.round(s.median24m)):'-')+'</td><td>'+formatSqm(s.medianPricePerSqm)+'</td><td>'+(s.priceMin24m!=null?formatPrice(s.priceMin24m):'-')+'</td><td>'+(s.priceMax24m!=null?formatPrice(s.priceMax24m):'-')+'</td><td>'+(s.monthsWithTrades||0)+'/24 · '+sampleLabel(s.sampleQuality)+'</td></tr>';
    }).join('');
    tbody.querySelectorAll('tr').forEach(tr=>{
      tr.addEventListener('click',()=>{
        selectRegion(tr.dataset.key);
        document.getElementById('region-panel')?.scrollIntoView({behavior:'smooth',block:'start'});
      });
    });
  }
  if(tableFilter){
    provinces.forEach(pr=>{
      const o=document.createElement('option');
      o.value=pr; o.textContent=pr;
      tableFilter.appendChild(o);
    });
    tableFilter.addEventListener('change',renderTable);
  }
  tableEl?.querySelectorAll('th[data-col]').forEach(th=>{
    th.addEventListener('click',()=>{
      const c=th.dataset.col;
      if(sortCol===c) sortAsc=!sortAsc;
      else { sortCol=c; sortAsc=false; }
      renderTable();
    });
  });
  renderTable();

  document.getElementById('btn-download-table')?.addEventListener('click',()=>{
    const pv=tableFilter?.value||'all';
    const data=marketSummary.filter(s=>pv==='all'||s.province===pv);
    const header=['province','name','regionType','totalCount24m','median24m','medianPricePerSqm','priceMin24m','priceMax24m','monthsWithTrades','sampleQuality','dataStatus','latestTradeMonth','lawdCd'];
    const rows=data.map(s=>header.map(h=>JSON.stringify(s[h]??'')).join(','));
    const csv=[header.join(','),...rows].join('\n');
    const blob=new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'});
    const a=document.createElement('a');
    a.href=URL.createObjectURL(blob);
    a.download='region-market-summary.csv';
    a.click();
    URL.revokeObjectURL(a.href);
    showToast('CSV를 내려받았습니다');
  });

  applyFilters();
  invalidateMapSoon();
  window.addEventListener('resize', invalidateMapSoon);

  const params=new URLSearchParams(location.search);
  const focus=params.get('region');
  let start = points.find(p=>p.name==='해남군');
  if(focus){
    const cat=(regionCatalog?.regions||[]).find(r=>
      r.sigunguCode===focus || r.regionSlug===focus || r.key===focus || r.name===focus
    );
    start = points.find(p=>
      p.key===focus || p.name===focus || String(p.lawdCd)===String(focus) || (cat && p.key===cat.key)
    ) || start;
  }
  if(start) selectRegion(start.key);
}).catch(err=>{
  console.error(err);
  if(mapLoading){
    mapLoading.classList.remove('is-done');
    mapLoading.textContent='데이터를 불러오지 못했습니다. 새로고침 해 주세요.';
  }
});
