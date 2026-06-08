/* ──────────────────────────────────────────────────────────────────────────
   Pipeline Intelligence — app logic
   Vanilla JS + SVG. Depends on PIPELINE global from pipeline_data.js
   ────────────────────────────────────────────────────────────────────────── */

// ─── STATE ────────────────────────────────────────────────────────────────────
const S = {
  tap: '',
  sector: '',
  stage: '',
  minPrem: 0,         // lakhs
  minRisk: 0,
  starredOnly: false,
  search: '',
  sortKey: 'opp',
  sortDir: 'desc',
  drawerName: null,
  focusedIdx: -1,
  searchOpen: false,
  searchFocusedIdx: -1,
  filteredRows: [],
};

// Restore starred from localStorage
try {
  const stars = JSON.parse(localStorage.getItem('pipeline_stars') || '[]');
  const starSet = new Set(stars);
  PIPELINE.forEach(r => { if (starSet.has(r.n)) r.starred = true; });
} catch (e) {}

function persistStars() {
  try {
    const starred = PIPELINE.filter(r => r.starred).map(r => r.n);
    localStorage.setItem('pipeline_stars', JSON.stringify(starred));
  } catch (e) {}
}

// ─── META / HELPERS ───────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

const TAP_META = {
  preseed:    { label:'Uninsured',     icon:'🔍', cls:'pre', color:'#7388A1' },
  untapped:   { label:'First buyer',   icon:'🌱', cls:'unt', color:'#E0A04A' },
  strike_now: { label:'Strike now',    icon:'⚡', cls:'str', color:'#E54343' },
  covered:    { label:'Renewal target',icon:'🔄', cls:'cov', color:'#4B89D6' },
};
const STAGE_META = {
  'Pre-seed': { cls:'stg-pre',  abbr:'PRESEED' },
  'Seed':     { cls:'stg-seed', abbr:'SEED' },
  'Series A': { cls:'stg-a',    abbr:'SERIES A' },
  'Series B+':{ cls:'stg-b',    abbr:'SERIES B+' },
};
const STAGE_ORDER = ['Pre-seed','Seed','Series A','Series B+'];
const ALL_SECTORS = [...new Set(PIPELINE.map(r => r.sec))].sort();

function fmt(n) { return Number.isFinite(n) ? (Number.isInteger(n) ? String(n) : n.toFixed(1).replace(/\.0$/,'')) : '—'; }
function fmtCr(lakhs) { return fmt(Math.round(lakhs/100 * 10) / 10) + ' Cr'; }
function fmtRev(cr) {
  if (!cr || cr === 0) return 'Pre-revenue';
  if (cr >= 1000) return '₹' + Math.round(cr/100)/10 + 'k Cr';
  return '₹' + Math.round(cr) + ' Cr';
}
function fmtTeam(n) { return n >= 1000 ? Math.round(n/100)/10 + 'k' : String(n); }
function oppCls(s) { return s >= 80 ? 'hi' : s >= 60 ? 'md' : 'lo'; }
function riskCls(s) { return s >= 70 ? 'hi' : s >= 45 ? 'md' : 'lo'; }
function abbrevSector(s) {
  return { 'Fintech':'Fintech','Healthtech':'Health','Deeptech / AI / Robotics':'Deeptech','Edtech':'Edtech',
           'Agritech / Foodtech':'Agritech','Cleantech / Climatetech':'Cleantech','D2C / Consumer Brands':'D2C',
           'Gaming / Media / Content':'Gaming','HRtech':'HRtech','SaaS / Enterprise Software':'SaaS',
           'Logistics / Mobility':'Logistics','Spacetech':'Space','Legaltech':'Legal' }[s] || s.split('/')[0].trim().substring(0,10);
}

// ─── AGGREGATIONS ─────────────────────────────────────────────────────────────
function computeAggs(rows) {
  const byTap = {}, bySector = {}, bySectorStage = {};
  let totalPremium = 0, totalScore = 0;
  for (const r of rows) {
    if (!byTap[r.tap]) byTap[r.tap] = { count: 0, premSum: 0 };
    byTap[r.tap].count++; byTap[r.tap].premSum += r.max;
    if (!bySector[r.sec]) bySector[r.sec] = { count: 0, premSum: 0, scores: [], tapCounts: {} };
    bySector[r.sec].count++; bySector[r.sec].premSum += r.max;
    bySector[r.sec].scores.push(r.score);
    bySector[r.sec].tapCounts[r.tap] = (bySector[r.sec].tapCounts[r.tap] || 0) + 1;
    const k = r.sec + '|' + r.stage;
    if (!bySectorStage[k]) bySectorStage[k] = { uninsured: 0, count: 0 };
    bySectorStage[k].count++;
    if (r.tap === 'preseed' || r.tap === 'untapped' || r.tap === 'strike_now') bySectorStage[k].uninsured++;
    totalPremium += r.max; totalScore += r.score;
  }
  return { byTap, bySector, bySectorStage, totalPremium, avgScore: rows.length ? totalScore / rows.length : 0 };
}
const GLOBAL_AGGS = computeAggs(PIPELINE);
const GLOBAL_MAX_PREM = Math.max(...PIPELINE.map(r => r.max));

// ─── FILTER ──────────────────────────────────────────────────────────────────
function getFiltered() {
  const q = S.search.trim().toLowerCase();
  return PIPELINE.filter(r => {
    if (S.tap && r.tap !== S.tap) return false;
    if (S.sector && r.sec !== S.sector) return false;
    if (S.stage && r.stage !== S.stage) return false;
    if (S.minPrem > 0 && r.max < S.minPrem) return false;
    if (S.minRisk > 0 && r.score < S.minRisk) return false;
    if (S.starredOnly && !r.starred) return false;
    if (q && !r.n.toLowerCase().includes(q) && !r.sec.toLowerCase().includes(q)) return false;
    return true;
  });
}

function toggleFilter(key, val) {
  S[key] = S[key] === val ? '' : val;
  if (key === 'tap')   { S.stage = ''; S.sector = ''; }
  if (key === 'sector'){ S.tap = ''; }
  if (key === 'stage') { S.tap = ''; }
  rerender();
}

function clearFilters() {
  S.tap = ''; S.sector = ''; S.stage = '';
  S.minPrem = 0; S.minRisk = 0;
  S.starredOnly = false; S.search = '';
  if ($('search-input')) $('search-input').value = '';
  rerender();
}

function rerender() {
  S.focusedIdx = -1;
  renderFilterStrip();
  renderKPIs();
  renderPriorityQueue();
  renderTable();
  renderStatusBar();
  highlightViz();
}

// ─── TOPBAR + SEARCH ──────────────────────────────────────────────────────────
function renderTopbar() {
  $('topbar').innerHTML = `
    <div class="brand-mark">IL</div>
    <span class="topbar-title">Pipeline Intelligence</span>
    <span class="topbar-sub">RM Workspace</span>
    <div class="search-wrap">
      <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="7" cy="7" r="5"/><path d="m11 11 3 3" stroke-linecap="round"/>
      </svg>
      <input class="search-input" id="search-input" placeholder="Search 263 accounts…" autocomplete="off"/>
      <span class="search-kbd">⌘K</span>
      <div class="search-results" id="search-results"></div>
    </div>
    <div class="topbar-sep"></div>
    <div class="kpi-strip" id="kpi-strip"></div>
    <div class="user-avatar" title="Priya Sharma · West RM">PS</div>`;

  const input = $('search-input');
  input.addEventListener('input', e => {
    S.search = e.target.value;
    renderSearchResults();
    renderTable();
    renderStatusBar();
  });
  input.addEventListener('focus', () => { S.searchOpen = true; renderSearchResults(); });
  input.addEventListener('blur', () => setTimeout(() => { S.searchOpen = false; $('search-results').classList.remove('visible'); }, 180));
  input.addEventListener('keydown', e => {
    const results = $('search-results').querySelectorAll('.search-result');
    if (e.key === 'ArrowDown') { e.preventDefault(); S.searchFocusedIdx = Math.min(results.length - 1, S.searchFocusedIdx + 1); updateSearchFocus(); }
    else if (e.key === 'ArrowUp')   { e.preventDefault(); S.searchFocusedIdx = Math.max(0, S.searchFocusedIdx - 1); updateSearchFocus(); }
    else if (e.key === 'Enter')     { if (S.searchFocusedIdx >= 0 && results[S.searchFocusedIdx]) { results[S.searchFocusedIdx].click(); } }
    else if (e.key === 'Escape')    { input.blur(); input.value = ''; S.search = ''; rerender(); }
  });
}

function renderSearchResults() {
  const q = S.search.trim().toLowerCase();
  const box = $('search-results');
  if (!q || !S.searchOpen) { box.classList.remove('visible'); return; }
  const matches = PIPELINE
    .filter(r => r.n.toLowerCase().includes(q) || r.sec.toLowerCase().includes(q))
    .sort((a,b) => b.opp - a.opp)
    .slice(0, 8);
  if (matches.length === 0) {
    box.innerHTML = `<div style="padding:14px;font-size:11px;color:var(--txt3)">No matches for "${esc(q)}"</div>`;
    box.classList.add('visible');
    return;
  }
  box.innerHTML = matches.map((r, i) => `
    <div class="search-result${i === S.searchFocusedIdx ? ' focused' : ''}" data-name="${esc(r.n)}">
      <div class="sr-name">${esc(r.n)}</div>
      <div class="sr-meta">${esc(r.sec)} · ${esc(r.stage)}</div>
      <div class="sr-opp ${oppCls(r.opp)}">${r.opp}</div>
    </div>`).join('');
  box.classList.add('visible');
  box.querySelectorAll('.search-result').forEach(el => {
    el.onmousedown = e => { e.preventDefault(); openDrawer(el.dataset.name); $('search-input').blur(); $('search-input').value = ''; S.search = ''; rerender(); };
  });
  S.searchFocusedIdx = -1;
}

function updateSearchFocus() {
  const results = $('search-results').querySelectorAll('.search-result');
  results.forEach((el, i) => el.classList.toggle('focused', i === S.searchFocusedIdx));
}

// ─── KPIs ─────────────────────────────────────────────────────────────────────
function renderKPIs() {
  const rows = getFiltered();
  const aggs = computeAggs(rows);
  const topSec = Object.entries(aggs.bySector).sort((a,b) => b[1].premSum - a[1].premSum)[0];
  $('kpi-strip').innerHTML = [
    ['Pool',     '₹' + fmtCr(aggs.totalPremium), 'accent'],
    ['Accounts', rows.length + '/' + PIPELINE.length, ''],
    ['Avg Risk', fmt(aggs.avgScore), ''],
    ['Top Sec',  topSec ? topSec[0].split('/')[0].trim().substring(0,10) : '—', ''],
  ].map(([l, v, c]) => `
    <div class="kpi-chip">
      <span class="kpi-chip-label">${esc(l)}</span>
      <span class="kpi-chip-val ${c}">${esc(v)}</span>
    </div>`).join('');
}

// ─── FILTER STRIP ─────────────────────────────────────────────────────────────
function renderFilterStrip() {
  const hasFilter = S.tap || S.sector || S.stage || S.minPrem || S.minRisk || S.starredOnly || S.search;
  $('filter-strip').innerHTML = `
    <span class="fs-label">Status</span>
    <button class="fs-btn ${!S.tap && !S.sector && !S.stage ? 'active-all' : ''}" id="fs-all">All</button>
    ${['preseed','untapped','strike_now','covered'].map(t => {
      const m = TAP_META[t]; const active = S.tap === t;
      return `<button class="fs-btn ${active ? 'active-' + m.cls : ''}" data-tap="${t}">${m.icon} ${m.label}</button>`;
    }).join('')}
    <div class="fs-divider"></div>
    <button class="fs-btn ${S.starredOnly ? 'active-star' : ''}" id="fs-star">★ Starred</button>
    <div class="fs-divider"></div>
    <select class="fs-select" id="fs-sector">
      <option value="">All sectors</option>
      ${ALL_SECTORS.map(s => `<option value="${esc(s)}" ${S.sector === s ? 'selected' : ''}>${esc(s)}</option>`).join('')}
    </select>
    <select class="fs-select" id="fs-stage">
      <option value="">All stages</option>
      ${STAGE_ORDER.map(s => `<option value="${esc(s)}" ${S.stage === s ? 'selected' : ''}>${esc(s)}</option>`).join('')}
    </select>
    <div class="fs-range" id="fs-range-prem">
      <button class="fs-btn">₹ Premium ${S.minPrem > 0 ? `· ≥${S.minPrem} L` : ''}</button>
      <div class="fs-range-pop">
        <div class="fs-range-label">Min. premium</div>
        <div class="fs-range-val" id="prem-val">${S.minPrem} L+ (${PIPELINE.filter(r => r.max >= S.minPrem).length} accounts)</div>
        <input type="range" min="0" max="200" step="5" value="${S.minPrem}" id="prem-slider"/>
      </div>
    </div>
    <div class="fs-range" id="fs-range-risk">
      <button class="fs-btn">⚠ Risk ${S.minRisk > 0 ? `· ≥${S.minRisk}` : ''}</button>
      <div class="fs-range-pop">
        <div class="fs-range-label">Min. risk score</div>
        <div class="fs-range-val" id="risk-val">${S.minRisk}+ (${PIPELINE.filter(r => r.score >= S.minRisk).length} accounts)</div>
        <input type="range" min="0" max="100" step="5" value="${S.minRisk}" id="risk-slider"/>
      </div>
    </div>
    <div class="fs-sep"></div>
    <button class="fs-clear ${hasFilter ? 'visible' : ''}" id="fs-clear">✕ Clear</button>
    <span class="fs-count">${getFiltered().length} acc.</span>`;

  $('fs-all').onclick   = () => { clearFilters(); };
  $('fs-clear').onclick = () => { clearFilters(); };
  $('fs-star').onclick  = () => { S.starredOnly = !S.starredOnly; rerender(); };
  $('fs-sector').onchange = e => toggleFilter('sector', e.target.value);
  $('fs-stage').onchange  = e => toggleFilter('stage', e.target.value);
  document.querySelectorAll('[data-tap]').forEach(btn => btn.onclick = () => toggleFilter('tap', btn.dataset.tap));

  // Range pop-outs
  ['fs-range-prem','fs-range-risk'].forEach(id => {
    const el = $(id);
    if (!el) return;
    el.querySelector('.fs-btn').onclick = e => {
      e.stopPropagation();
      document.querySelectorAll('.fs-range').forEach(r => { if (r.id !== id) r.classList.remove('open'); });
      el.classList.toggle('open');
    };
  });
  document.addEventListener('click', e => {
    if (!e.target.closest('.fs-range')) {
      document.querySelectorAll('.fs-range').forEach(r => r.classList.remove('open'));
    }
  });
  const ps = $('prem-slider');
  if (ps) ps.oninput = e => {
    S.minPrem = +e.target.value;
    $('prem-val').textContent = `${S.minPrem} L+ (${PIPELINE.filter(r => r.max >= S.minPrem).length} accounts)`;
    renderTable(); renderStatusBar();
  };
  const rs = $('risk-slider');
  if (rs) rs.oninput = e => {
    S.minRisk = +e.target.value;
    $('risk-val').textContent = `${S.minRisk}+ (${PIPELINE.filter(r => r.score >= S.minRisk).length} accounts)`;
    renderTable(); renderStatusBar();
  };
}

// ─── PRIORITY QUEUE ────────────────────────────────────────────────────────────
function renderPriorityQueue() {
  const rows = getFiltered();
  const top = [...rows].sort((a, b) => b.opp - a.opp).slice(0, 5);
  const dateStr = 'Week of May 18, 2026';

  const cards = top.length ? top.map(r => {
    const m = TAP_META[r.tap];
    const glow = r.tap === 'strike_now' ? ' strike-glow' : '';
    return `
      <div class="pq-card${glow}" data-name="${esc(r.n)}">
        <div class="pq-card-top">
          <span class="tap-badge tap-${m.cls}">${m.icon} ${m.label}</span>
          <span><span class="pq-opp ${oppCls(r.opp)}">${r.opp}</span><span class="pq-opp-label">OPP</span></span>
        </div>
        <div class="pq-card-name">${esc(r.n)}</div>
        <div class="pq-meta">${esc(r.sec)} · ${esc(r.stage)}</div>
        <div class="pq-stats">
          <span><strong>₹${fmt(r.min)}–${fmt(r.max)} L</strong></span>
          <span>Risk <strong>${r.score}</strong></span>
        </div>
        <div class="pq-signal">${r.signal ? '⚡ ' + esc(r.signal.text) : '— No recent signal'}</div>
      </div>`;
  }).join('') : `<div style="grid-column:1/-1;padding:30px;text-align:center;color:var(--txt3);font-size:11px">No accounts match — clear filters to see your top 5 calls.</div>`;

  $('priority-queue').innerHTML = `
    <div class="pq-head">
      <span class="pq-title">Today's <span class="pq-title-accent">priority queue</span></span>
      <span class="pq-sub">top 5 by composite Opportunity Score · highest leverage next-calls</span>
      <span class="pq-context">${esc(dateStr)} · Priya Sharma · West India</span>
    </div>
    <div class="pq-cards">${cards}</div>`;

  $('priority-queue').querySelectorAll('.pq-card').forEach(el => el.onclick = () => openDrawer(el.dataset.name));
}

// ─── FUNNEL ────────────────────────────────────────────────────────────────────
function renderFunnel() {
  const aggs = GLOBAL_AGGS;
  const maxPrem = Math.max(...['preseed','untapped','strike_now','covered'].map(t => (aggs.byTap[t] || {}).premSum || 0));
  const bands = [
    { tap:'preseed',    label:'Uninsured',      icon:'🔍', fillCls:'band-fill-pre' },
    { tap:'untapped',   label:'First buyer',    icon:'🌱', fillCls:'band-fill-unt' },
    { tap:'strike_now', label:'Strike now',     icon:'⚡', fillCls:'band-fill-str' },
    { tap:'covered',    label:'Renewal target', icon:'🔄', fillCls:'band-fill-cov' },
  ];
  const rows = bands.map(b => {
    const d = aggs.byTap[b.tap] || { count: 0, premSum: 0 };
    const pct = maxPrem > 0 ? Math.max(4, Math.round(d.premSum / maxPrem * 100)) : 4;
    return `
      <div class="funnel-band${S.tap === b.tap ? ' active-band' : ''}" data-band="${b.tap}">
        <span class="band-icon">${b.icon}</span>
        <span class="band-label">${b.label}</span>
        <div class="band-track">
          <div class="band-fill ${b.fillCls}" style="width:${pct}%">
            <span class="band-fill-label">₹${fmtCr(d.premSum)}</span>
          </div>
        </div>
        <div class="band-meta">
          <span class="band-meta-cr">₹${fmtCr(d.premSum)}</span>
          <span class="band-meta-cos">${d.count} co.</span>
        </div>
      </div>`;
  }).join('');
  const total = PIPELINE.reduce((s, r) => s + r.max, 0);
  $('funnel-panel').innerHTML = `
    <div class="panel-head">
      <span class="panel-title">Premium Opportunity Funnel</span>
      <span class="panel-sub">by market status · click to filter</span>
    </div>
    <div class="funnel-body">
      ${rows}
      <div class="funnel-total">
        <span class="funnel-total-label">Total addressable pool</span>
        <span class="funnel-total-val">₹${fmtCr(total)}</span>
      </div>
    </div>`;
  $('funnel-panel').querySelectorAll('.funnel-band').forEach(el => el.onclick = () => toggleFilter('tap', el.dataset.band));
}

// ─── HEATMAP ───────────────────────────────────────────────────────────────────
function renderHeatmap() {
  const bss = GLOBAL_AGGS.bySectorStage;
  const allCounts = ALL_SECTORS.flatMap(sec => STAGE_ORDER.map(stg => (bss[sec + '|' + stg] || {}).uninsured || 0));
  const maxCount = Math.max(...allCounts, 1);
  function cellColor(count) {
    if (count === 0) return 'var(--bg)';
    const t = count / maxCount;
    const r = Math.round(7 + t * (173 - 7)), g = Math.round(11 + t * (30 - 11)), b = Math.round(18 + t * (35 - 18));
    return `rgb(${r},${g},${b})`;
  }
  function sparkSVG(sec) {
    const cos = PIPELINE.filter(r => r.sec === sec);
    const bins = new Array(10).fill(0);
    cos.forEach(c => { bins[Math.min(9, Math.floor(c.score / 10))]++; });
    const maxBin = Math.max(...bins, 1);
    const W = 80, H = 18, bw = 7, gap = 1;
    const rects = bins.map((cnt, i) => {
      const bh = Math.max(1, Math.round(cnt / maxBin * H));
      const x = i * (bw + gap); const y = H - bh;
      const alpha = 0.25 + 0.75 * (i / 9);
      return `<rect x="${x}" y="${y}" width="${bw}" height="${bh}" fill="rgba(173,30,35,${alpha.toFixed(2)})"/>`;
    }).join('');
    return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="display:block">${rects}</svg>`;
  }
  const header = `
    <div class="heat-cell heat-hdr">Sector</div>
    <div class="heat-cell heat-hdr">Pre</div>
    <div class="heat-cell heat-hdr">Seed</div>
    <div class="heat-cell heat-hdr">Ser A</div>
    <div class="heat-cell heat-hdr">B+</div>
    <div class="heat-cell heat-hdr">Risk →</div>`;
  const body = ALL_SECTORS.map(sec => {
    const cells = STAGE_ORDER.map(stg => {
      const k = sec + '|' + stg;
      const d = bss[k] || { uninsured: 0, count: 0 };
      const isActive = S.sector === sec && S.stage === stg;
      return `<div class="heat-cell clickable${isActive ? ' active-cell' : ''}"
        style="background:${cellColor(d.uninsured)}"
        data-sec="${esc(sec)}" data-stg="${esc(stg)}"
        title="${esc(sec)} · ${esc(stg)}: ${d.uninsured} uninsured / ${d.count} total">
        ${d.uninsured > 0 ? `<span class="heat-num">${d.uninsured}</span>` : ''}
      </div>`;
    }).join('');
    return `
      <div class="heat-cell heat-sec-label" data-sec="${esc(sec)}" title="${esc(sec)}">${esc(abbrevSector(sec))}</div>
      ${cells}
      <div class="heat-spark-cell heat-cell">${sparkSVG(sec)}</div>`;
  }).join('');
  $('heatmap-panel').innerHTML = `
    <div class="panel-head">
      <span class="panel-title">Coverage Gap Matrix</span>
      <span class="panel-sub">uninsured count · sector × stage · risk sparkline</span>
    </div>
    <div class="heat-body">
      <div class="heat-grid">${header}${body}</div>
      <div class="heat-foot">Darker red = more uninsured. Right-column sparkline = risk score distribution (0→100); high-risk sectors lean right.</div>
    </div>`;
  $('heatmap-panel').querySelectorAll('[data-sec][data-stg]').forEach(el => {
    el.onclick = () => { S.tap = ''; S.sector = el.dataset.sec; S.stage = el.dataset.stg; rerender(); };
  });
  $('heatmap-panel').querySelectorAll('.heat-sec-label').forEach(el => {
    el.onclick = () => toggleFilter('sector', el.dataset.sec);
  });
}

// ─── SECTOR BUBBLES ────────────────────────────────────────────────────────────
function renderBubbles() {
  const agg = GLOBAL_AGGS.bySector;
  const sectors = ALL_SECTORS.map(sec => {
    const d = agg[sec] || { count: 0, premSum: 0, tapCounts: {} };
    const domTap = Object.entries(d.tapCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'covered';
    return { sec, count: d.count, premSum: d.premSum, domTap, scores: d.scores || [] };
  }).filter(s => s.count > 0);
  const maxPrem = Math.max(...sectors.map(s => s.premSum));
  const SVG_W = 1200;
  const maxR = 84, minR = 28;
  sectors.forEach(s => { s.r = minR + (maxR - minR) * Math.sqrt(s.premSum / maxPrem); });
  sectors.sort((a, b) => b.r - a.r);
  // Distribute across two rows
  const row1 = [], row2 = [];
  let w1 = 0, w2 = 0;
  for (const s of sectors) {
    const need = s.r * 2 + 20;
    if (w1 <= w2) { row1.push(s); w1 += need; } else { row2.push(s); w2 += need; }
  }
  function place(row, cy) {
    const totalW = row.reduce((w, s) => w + s.r * 2 + 18, 0) - 18;
    let x = (SVG_W - totalW) / 2;
    row.forEach(s => { s.cx = x + s.r; s.cy = cy; x += s.r * 2 + 18; });
  }
  const maxR1 = Math.max(...row1.map(s => s.r), maxR);
  const maxR2 = Math.max(...row2.map(s => s.r), maxR);
  place(row1, maxR1 + 14);
  place(row2, maxR1 * 2 + maxR2 + 44);
  const totalH = maxR1 * 2 + maxR2 * 2 + 70;
  const TAP_COLORS = { preseed:'#7388A1', untapped:'#E0A04A', strike_now:'#E54343', covered:'#4B89D6' };

  const circles = sectors.map(s => {
    const color = TAP_COLORS[s.domTap] || '#7388A1';
    const active = S.sector === s.sec;
    const dimmed = S.sector && !active;
    const abbrev = abbrevSector(s.sec);
    const fontMain = s.r > 55 ? 13 : s.r > 40 ? 11 : 9;
    const fontSub  = s.r > 55 ? 10 : s.r > 40 ? 9 : 8;
    const bgAlpha = active ? 0.30 : 0.13;
    return `
      <g class="sector-bubble${dimmed ? ' dimmed' : ''}" data-sec="${esc(s.sec)}">
        <circle cx="${s.cx}" cy="${s.cy}" r="${s.r}"
          fill="${color}" fill-opacity="${bgAlpha}"
          stroke="${color}" stroke-opacity="${active ? 0.9 : 0.45}"
          stroke-width="${active ? 2.5 : 1.5}"/>
        ${s.r > 38 ? `
          <text x="${s.cx}" y="${s.cy - (fontSub + 2)}" text-anchor="middle"
            font-family="'Space Grotesk',sans-serif" font-size="${fontMain}" font-weight="600"
            fill="${color}" opacity="0.95">${esc(abbrev)}</text>
          <text x="${s.cx}" y="${s.cy + fontMain}" text-anchor="middle"
            font-family="'IBM Plex Mono',monospace" font-size="${fontSub}" fill="${color}" opacity="0.7">₹${fmtCr(s.premSum)}</text>
          <text x="${s.cx}" y="${s.cy + fontMain + fontSub + 2}" text-anchor="middle"
            font-family="'IBM Plex Mono',monospace" font-size="${fontSub - 1}" fill="${color}" opacity="0.5">${s.count} co.</text>` : `
          <text x="${s.cx}" y="${s.cy + fontMain/2 - 1}" text-anchor="middle"
            font-family="'Space Grotesk',sans-serif" font-size="${fontMain}" font-weight="600" fill="${color}" opacity="0.9">${esc(abbrev)}</text>`}
        <rect x="${s.cx - s.r}" y="${s.cy - s.r}" width="${s.r * 2}" height="${s.r * 2}" fill="transparent"/>
      </g>`;
  }).join('');

  const legend = Object.entries(TAP_META).map(([k, m], i) => `
    <g transform="translate(${i * 132}, 0)">
      <circle cx="8" cy="8" r="6" fill="${TAP_COLORS[k]}" fill-opacity="0.3" stroke="${TAP_COLORS[k]}" stroke-opacity="0.7" stroke-width="1.5"/>
      <text x="20" y="12" font-family="'DM Sans',sans-serif" font-size="10" fill="#6B849E">${m.icon} ${m.label}</text>
    </g>`).join('');

  $('bubble-panel').innerHTML = `
    <div class="panel-head">
      <span class="panel-title">Sector Intelligence</span>
      <span class="panel-sub">bubble size = premium pool · colour = dominant status · click to filter · hover for detail</span>
    </div>
    <div class="bubble-outer">
      <svg viewBox="0 0 ${SVG_W} ${totalH}" width="100%" style="display:block">
        ${circles}
        <g transform="translate(20,${totalH - 22})">${legend}</g>
      </svg>
    </div>`;
  $('bubble-panel').querySelectorAll('.sector-bubble').forEach(el => {
    el.onclick = () => toggleFilter('sector', el.dataset.sec);
    el.addEventListener('mouseenter', e => showBubbleTooltip(e, el.dataset.sec));
    el.addEventListener('mouseleave', hideTooltip);
  });
}

function showBubbleTooltip(e, sec) {
  const d = GLOBAL_AGGS.bySector[sec];
  if (!d) return;
  const avg = Math.round(d.scores.reduce((a, b) => a + b, 0) / d.scores.length);
  const mx = Math.max(...d.scores);
  const dom = Object.entries(d.tapCounts).sort((a, b) => b[1] - a[1])[0];
  const tip = $('tooltip');
  tip.innerHTML = `
    <div class="tt-title">${esc(sec)}</div>
    <div class="tt-row"><span>Companies</span><span class="tt-val">${d.count}</span></div>
    <div class="tt-row"><span>Premium pool</span><span class="tt-val">₹${fmtCr(d.premSum)}</span></div>
    <div class="tt-row"><span>Avg / max risk</span><span class="tt-val">${avg} / ${mx}</span></div>
    ${dom ? `<div class="tt-row"><span>Dominant status</span><span class="tt-val">${TAP_META[dom[0]]?.label || dom[0]}</span></div>` : ''}`;
  tip.classList.add('show');
  positionTooltip(e);
}
function hideTooltip() { $('tooltip').classList.remove('show'); }
function positionTooltip(e) {
  const tip = $('tooltip');
  let x = e.clientX + 14, y = e.clientY - 20;
  if (x + 280 > window.innerWidth) x = e.clientX - 290;
  if (y + 160 > window.innerHeight) y = e.clientY - 160;
  tip.style.left = x + 'px'; tip.style.top = y + 'px';
}
document.addEventListener('mousemove', e => { if ($('tooltip')?.classList.contains('show')) positionTooltip(e); });

// ─── HIGHLIGHT VIZ (on filter change) ─────────────────────────────────────────
function highlightViz() {
  document.querySelectorAll('.funnel-band').forEach(el => {
    el.classList.toggle('active-band', S.tap === el.dataset.band);
  });
  document.querySelectorAll('.sector-bubble').forEach(el => {
    const active = S.sector === el.dataset.sec;
    el.classList.toggle('dimmed', !!S.sector && !active);
    el.querySelectorAll('circle').forEach(c => {
      c.setAttribute('fill-opacity', active ? '0.30' : '0.13');
      c.setAttribute('stroke-opacity', active ? '0.9' : '0.45');
      c.setAttribute('stroke-width', active ? '2.5' : '1.5');
    });
  });
  document.querySelectorAll('.heat-cell.clickable').forEach(el => {
    const match = (!S.sector || S.sector === el.dataset.sec) && (!S.stage || S.stage === el.dataset.stg);
    el.style.opacity = match ? '1' : '0.3';
    el.classList.toggle('active-cell', S.sector === el.dataset.sec && S.stage === el.dataset.stg);
  });
}

// ─── TABLE ─────────────────────────────────────────────────────────────────────
function renderTable() {
  const rows = getFiltered();
  S.filteredRows = rows;
  const sorted = [...rows].sort((a, b) => {
    let v = 0;
    if (S.sortKey === 'opp')   v = (b.opp || 0) - (a.opp || 0);
    if (S.sortKey === 'max')   v = (b.max || 0) - (a.max || 0);
    if (S.sortKey === 'score') v = (b.score || 0) - (a.score || 0);
    if (S.sortKey === 'n')     v = a.n.localeCompare(b.n);
    if (S.sortKey === 'sec')   v = (a.sec || '').localeCompare(b.sec || '');
    if (S.sortKey === 'stage') {
      const o = { 'Pre-seed':0,'Seed':1,'Series A':2,'Series B+':3 };
      v = (o[a.stage] ?? 9) - (o[b.stage] ?? 9);
    }
    return S.sortDir === 'asc' ? -v : v;
  });
  S.filteredRows = sorted;
  const gmax = Math.max(...rows.map(r => r.max), 1);

  const SORT_COLS = [
    { label:'',        key:null,    style:'width:28px' },
    { label:'Opp',     key:'opp',   sortable:true, style:'width:78px' },
    { label:'Company', key:'n',     sortable:true, style:'width:280px' },
    { label:'Sector',  key:'sec',   sortable:true, style:'width:110px' },
    { label:'Stage',   key:'stage', sortable:true, style:'width:72px' },
    { label:'Status',  key:null,    style:'width:112px' },
    { label:'Bundle',  key:null,    style:'width:140px' },
    { label:'Premium', key:'max',   sortable:true, style:'width:148px' },
    { label:'Risk',    key:'score', sortable:true, style:'width:54px;text-align:center' },
    { label:'',        key:null,    style:'width:28px' },
  ];

  const thead = `<thead><tr>${SORT_COLS.map(c => {
    if (!c.sortable) return `<th class="th" style="${c.style}">${c.label}</th>`;
    const active = S.sortKey === c.key;
    const arr = active ? (S.sortDir === 'desc' ? '↓' : '↑') : '⇅';
    return `<th class="th sortable${active ? ' sort-active' : ''}" data-sk="${c.key}" style="${c.style}">${c.label}<span class="sort-arr">${arr}</span></th>`;
  }).join('')}</tr></thead>`;

  function tapBadge(tap) {
    const m = TAP_META[tap] || { cls:'cov', icon:'?', label:'—' };
    return `<span class="tap-badge tap-${m.cls}">${m.icon} ${m.label}</span>`;
  }
  function stageBadge(stg) {
    const m = STAGE_META[stg] || { cls:'stg-b', abbr:stg };
    return `<span class="stage-badge ${m.cls}">${esc(m.abbr)}</span>`;
  }
  function arcGauge(score) {
    const s = score || 0;
    const R = 14, cx = 18, cy = 18;
    const circ = 2 * Math.PI * R;
    const filled = circ * s / 100;
    const c = riskCls(s) === 'hi' ? '#E54343' : riskCls(s) === 'md' ? '#E0A04A' : '#7388A1';
    return `<svg width="36" height="36" viewBox="0 0 36 36">
      <circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="#17243C" stroke-width="3"/>
      <circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="${c}" stroke-width="3"
        stroke-dasharray="${filled.toFixed(2)} ${(circ - filled).toFixed(2)}"
        stroke-linecap="round" transform="rotate(-90 ${cx} ${cy})"/>
      <text x="${cx}" y="${cy + 3.5}" text-anchor="middle" font-family="'IBM Plex Mono',monospace" font-size="9" fill="${c}" font-weight="600">${s}</text>
    </svg>`;
  }
  function oppCell(opp) {
    const cls = oppCls(opp);
    return `<div class="opp-cell">
      <span class="opp-num ${cls}">${opp}</span>
      <div class="opp-bar-track"><div class="opp-bar-fill ${cls}" style="width:${opp}%"></div></div>
    </div>`;
  }
  function riskPillCls(s) { return s >= 70 ? 'risk-hi' : s >= 45 ? 'risk-md' : 'risk-lo'; }

  const tbody = sorted.length ? sorted.map((r, i) => {
    const focused = S.focusedIdx === i;
    return `
      <tr class="tr${focused ? ' focused' : ''}" data-name="${esc(r.n)}" data-idx="${i}">
        <td class="td td-star">
          <button class="star-btn ${r.starred ? 'starred' : ''}" data-star="${esc(r.n)}" title="${r.starred ? 'Unstar' : 'Star'}">${r.starred ? '★' : '☆'}</button>
        </td>
        <td class="td td-opp">${oppCell(r.opp)}</td>
        <td class="td td-co">
          <span class="co-name">${esc(r.n)}</span>
          <div class="co-meta-row">
            <span class="co-risk-pill ${riskPillCls(r.score)}">${esc(r.risk)}</span>
            <span class="co-incumbent ${r.incumbent === 'None' ? 'none' : ''}">
              ${r.incumbent === 'None' ? '○ Uninsured' : 'vs <strong>' + esc(r.incumbent) + '</strong>'}
            </span>
          </div>
          ${r.signal ? `<span class="co-signal">⚡ ${esc(r.signal.text)}</span>` : ''}
        </td>
        <td class="td td-sector">${esc(r.sec)}</td>
        <td class="td td-stage">${stageBadge(r.stage)}</td>
        <td class="td td-tap">${tapBadge(r.tap)}</td>
        <td class="td td-bundle" title="${esc(r.bundle)}">${esc(r.bundle)}</td>
        <td class="td td-premium">
          <div class="prem-bar-wrap">
            <div class="prem-bar-track"><div class="prem-bar-fill" style="width:${Math.max(3, Math.round(r.max / gmax * 100))}%"></div></div>
            <span class="prem-label">₹${fmt(r.min)}–${fmt(r.max)} L</span>
          </div>
        </td>
        <td class="td td-score">${arcGauge(r.score)}</td>
        <td class="td td-action">
          <span class="row-action">›</span>
        </td>
      </tr>`;
  }).join('') :
  `<tr><td colspan="10" class="tbl-empty">
    <strong>No accounts match the current filters</strong>
    Try widening your status, sector, or stage selection — or <span class="link" id="empty-clear">clear all filters</span>.
  </td></tr>`;

  $('table-panel').innerHTML = `
    <div class="panel-head" style="padding-bottom:12px">
      <span class="panel-title">Pipeline Table</span>
      <span class="panel-sub">click any row to open profile · ${sorted.length} accounts · sorted by ${S.sortKey === 'opp' ? 'opportunity score' : S.sortKey}</span>
    </div>
    <div class="table-wrap">
      <table class="pipeline-table">${thead}<tbody>${tbody}</tbody></table>
    </div>`;

  $('table-panel').querySelectorAll('th[data-sk]').forEach(th => {
    th.onclick = () => {
      const k = th.dataset.sk;
      if (S.sortKey === k) S.sortDir = S.sortDir === 'desc' ? 'asc' : 'desc';
      else { S.sortKey = k; S.sortDir = 'desc'; }
      renderTable();
    };
  });
  $('table-panel').querySelectorAll('.tr').forEach(tr => {
    tr.onclick = e => {
      if (e.target.closest('.star-btn')) return;
      openDrawer(tr.dataset.name);
    };
  });
  $('table-panel').querySelectorAll('.star-btn').forEach(btn => {
    btn.onclick = e => {
      e.stopPropagation();
      const r = PIPELINE.find(x => x.n === btn.dataset.star);
      if (r) {
        r.starred = !r.starred;
        persistStars();
        btn.classList.toggle('starred', r.starred);
        btn.textContent = r.starred ? '★' : '☆';
        renderStatusBar();
        if (S.starredOnly) renderTable();
      }
    };
  });
  const ec = $('empty-clear');
  if (ec) ec.onclick = clearFilters;
}

// ─── DRAWER ─────────────────────────────────────────────────────────────────
function openDrawer(name) {
  const r = PIPELINE.find(x => x.n === name);
  if (!r) return;
  S.drawerName = name;
  const m = TAP_META[r.tap];
  const inc = r.incumbent === 'None';
  const total = r.bundleLines.reduce((s, [_,v]) => s + v, 0);
  const yearsSince = 2026 - r.founded;

  $('drawer-body').innerHTML = `
    <h1 class="dr-h1">${esc(r.n)}</h1>
    <div class="dr-subtitle">
      <span>${esc(r.sec)}</span><span class="sep"></span>
      <span>${esc(r.stage)}</span><span class="sep"></span>
      <span>${esc(r.city)}</span><span class="sep"></span>
      <span>Founded ${r.founded} · ${yearsSince} yr</span>
    </div>
    <div class="dr-status-row">
      <span class="tap-badge tap-${m.cls}">${m.icon} ${m.label}</span>
      <span style="font-size:11px;color:var(--txt3)">${inc ? 'Currently uninsured' : 'Renewal target · ' + esc(r.incumbent)}</span>
    </div>

    <div class="dr-metrics">
      <div class="dr-metric">
        <span class="dr-metric-label">Premium</span>
        <span class="dr-metric-val">₹${fmt(r.min)}–${fmt(r.max)}</span>
        <span class="dr-metric-sub">Lakhs / year</span>
      </div>
      <div class="dr-metric">
        <span class="dr-metric-label">Risk Score</span>
        <span class="dr-metric-val ${riskCls(r.score)}">${r.score}</span>
        <span class="dr-metric-sub">/ 100</span>
      </div>
      <div class="dr-metric">
        <span class="dr-metric-label">Opportunity</span>
        <span class="dr-metric-val ${oppCls(r.opp)}">${r.opp}</span>
        <span class="dr-metric-sub">composite score</span>
      </div>
      <div class="dr-metric">
        <span class="dr-metric-label">Team</span>
        <span class="dr-metric-val">${fmtTeam(r.team)}</span>
        <span class="dr-metric-sub">${fmtRev(r.revenue)}</span>
      </div>
    </div>

    ${r.signal ? `
      <div class="dr-section">
        <div class="dr-section-label">Recent signal</div>
        <div class="dr-signal">
          <span class="dr-signal-date">${r.signal.daysAgo === 1 ? 'YESTERDAY' : r.signal.daysAgo + ' DAYS AGO'}</span>
          <span class="dr-signal-text">${esc(r.signal.text)}</span>
        </div>
      </div>` : ''}

    <div class="dr-section">
      <div class="dr-section-label">Risk drivers</div>
      ${(r.drivers || []).map(d => `
        <div class="dr-driver"><div class="dr-driver-bullet"></div>${esc(d)}</div>`).join('')}
    </div>

    <div class="dr-section">
      <div class="dr-section-label">Profile</div>
      <div class="dr-profile-grid">
        <div class="dr-profile-key">HQ</div>           <div class="dr-profile-val">${esc(r.city)}</div>
        <div class="dr-profile-key">Founded</div>      <div class="dr-profile-val">${r.founded} (${yearsSince} yr)</div>
        <div class="dr-profile-key">Team</div>         <div class="dr-profile-val">${r.team.toLocaleString('en-IN')} FTE</div>
        <div class="dr-profile-key">Revenue</div>      <div class="dr-profile-val">${esc(fmtRev(r.revenue))}</div>
        <div class="dr-profile-key">Operations</div>   <div class="dr-profile-val">${esc(r.operations || '—')}</div>
        <div class="dr-profile-key">Stage</div>        <div class="dr-profile-val">${esc(r.stage)}</div>
      </div>
    </div>

    <div class="dr-section">
      <div class="dr-section-label">Recommended bundle</div>
      <div class="dr-bundle-card">
        <div class="dr-bundle-name">${esc(r.bundle)}</div>
        ${r.bundleLines.map(([name, amt]) => `
          <div class="dr-bundle-line"><strong>${esc(name)}</strong><span class="amount">₹${amt} L</span></div>`).join('')}
        <div class="dr-bundle-total">
          <span>Est. annual premium</span>
          <span class="amount">₹${fmt(r.min)}–${fmt(r.max)} L</span>
        </div>
      </div>
    </div>

    <div class="dr-section">
      <div class="dr-section-label">Pitch angle</div>
      <div class="dr-pitch">${esc(r.pitch)}</div>
    </div>

    <div class="dr-section">
      <div class="dr-section-label">Incumbent</div>
      <div class="dr-incumbent">
        <span class="dr-incumbent-dot ${inc ? 'none' : 'has'}"></span>
        <span class="dr-incumbent-name">${inc ? 'No current cover' : esc(r.incumbent)}</span>
        <span class="dr-incumbent-tag">${inc ? 'Greenfield' : 'Displacement'}</span>
      </div>
    </div>
  `;

  // Header breadcrumb + star
  $('drawer-breadcrumb').innerHTML = `Pipeline / <strong>${esc(r.n)}</strong>`;
  const dstar = $('drawer-star');
  dstar.classList.toggle('starred', !!r.starred);
  dstar.textContent = r.starred ? '★' : '☆';
  dstar.onclick = () => {
    r.starred = !r.starred;
    persistStars();
    dstar.classList.toggle('starred', r.starred);
    dstar.textContent = r.starred ? '★' : '☆';
    renderTable(); renderStatusBar();
  };

  $('drawer').classList.add('open');
  $('drawer-scrim').classList.add('open');
}
function closeDrawer() {
  S.drawerName = null;
  $('drawer').classList.remove('open');
  $('drawer-scrim').classList.remove('open');
}

// ─── STATUS BAR ───────────────────────────────────────────────────────────────
function renderStatusBar() {
  const rows = getFiltered();
  const totalCr = Math.round(rows.reduce((s, r) => s + r.max, 0) / 100 * 10) / 10;
  const starred = PIPELINE.filter(r => r.starred).length;
  const now = new Date();
  const time = now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false });
  $('status-bar').innerHTML = `
    <span class="status-pulse"></span>
    <span><strong>Live</strong> · last sync ${time}</span>
    <span class="status-sep"></span>
    <span>On screen: <strong>₹${totalCr} Cr</strong> across <strong>${rows.length}</strong> accounts</span>
    <span class="status-sep"></span>
    <span>Watchlist: <strong>${starred}</strong></span>
    <span class="status-sep"></span>
    <span>Avg opp: <strong class="accent">${rows.length ? Math.round(rows.reduce((s, r) => s + r.opp, 0) / rows.length) : '—'}</strong></span>
    <span class="status-sep-flex"></span>
    <span class="status-kbd"><span class="kbd">/</span> search</span>
    <span class="status-kbd"><span class="kbd">j</span><span class="kbd">k</span> navigate</span>
    <span class="status-kbd"><span class="kbd">↵</span> open</span>
    <span class="status-kbd"><span class="kbd">s</span> star</span>
    <span class="status-kbd"><span class="kbd">esc</span> close</span>`;
}

// ─── KEYBOARD ─────────────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  // Skip if typing in input (except search input handles its own)
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

  if (e.key === '/' || ((e.metaKey || e.ctrlKey) && e.key === 'k')) {
    e.preventDefault();
    $('search-input').focus(); $('search-input').select();
    return;
  }
  if (e.key === 'Escape') {
    if (S.drawerName) closeDrawer();
    else if (S.tap || S.sector || S.stage || S.minPrem || S.minRisk || S.starredOnly || S.search) clearFilters();
    return;
  }
  if (S.drawerName) return; // disable nav while drawer open
  if (e.key === 'j' || e.key === 'ArrowDown') {
    e.preventDefault();
    S.focusedIdx = Math.min((S.filteredRows.length - 1), S.focusedIdx + 1);
    updateRowFocus();
  } else if (e.key === 'k' || e.key === 'ArrowUp') {
    e.preventDefault();
    S.focusedIdx = Math.max(0, S.focusedIdx - 1);
    updateRowFocus();
  } else if (e.key === 'Enter') {
    if (S.focusedIdx >= 0 && S.filteredRows[S.focusedIdx]) openDrawer(S.filteredRows[S.focusedIdx].n);
  } else if (e.key === 's' || e.key === 'S') {
    if (S.focusedIdx >= 0 && S.filteredRows[S.focusedIdx]) {
      const r = S.filteredRows[S.focusedIdx];
      r.starred = !r.starred;
      persistStars();
      renderTable(); renderStatusBar();
    }
  }
});

function updateRowFocus() {
  document.querySelectorAll('.tr').forEach((tr, i) => tr.classList.toggle('focused', i === S.focusedIdx));
  const focused = document.querySelector('.tr.focused');
  if (focused) focused.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

// ─── DRAWER CLOSE WIRES ───────────────────────────────────────────────────────
$('drawer-close').onclick = closeDrawer;
$('drawer-scrim').onclick = closeDrawer;

// ─── INIT ─────────────────────────────────────────────────────────────────────
function init() {
  renderTopbar();
  renderFilterStrip();
  renderKPIs();
  renderPriorityQueue();
  renderFunnel();
  renderHeatmap();
  renderBubbles();
  renderTable();
  renderStatusBar();
}
init();
