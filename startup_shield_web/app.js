/* ═══════════════════════════════════════════════════════════════
   SPARC 3.0 — Redesigned frontend
   ═══════════════════════════════════════════════════════════════ */

/* ─── CONSTANTS ──────────────────────────────────────────────── */
const SECTIONS = [
  { id: "identity",  label: "Identity",  icon: "◎" },
  { id: "shape",     label: "Shape",     icon: "⬡" },
  { id: "exposure",  label: "Exposure",  icon: "⚡" },
  { id: "advanced",  label: "Advanced",  icon: "⚙" },
];

const SECTOR_ICONS = {
  "Fintech":                     "💳",
  "Healthtech":                  "🏥",
  "SaaS / Enterprise Software":  "💻",
  "Deeptech / AI / Robotics":    "🤖",
  "Edtech":                      "🎓",
  "D2C / Consumer Brands":       "🛍",
  "Logistics / Mobility":        "🚚",
  "Agritech / Foodtech":         "🌱",
  "Cleantech / Climatetech":     "🌿",
  "Gaming / Media / Content":    "🎮",
  "HRtech":                      "👥",
  "Legaltech":                   "⚖",
  "Proptech":                    "🏠",
  "Spacetech":                   "🚀",
  "Insurtech":                   "🛡",
  "Other":                       "✦",
};

const OPS_ICONS = {
  "Digital-only":         "🌐",
  "Hybrid (online+offline)": "⟳",
  "Offline / Physical":   "🏢",
  "Hardware / IoT":       "📦",
  "Marketplace":          "🔀",
};

const FUNDING_ICONS = {
  "Pre-seed":  "🌱",
  "Seed":      "🌿",
  "Series A":  "🌳",
  "Series B+": "🌲",
};

/* ─── STATE ──────────────────────────────────────────────────── */
const state = {
  meta: null,
  view: "role",
  section: 0,   // 0..3
  maxVisitedSection: 0,
  saveTimer: null,
  profile: {},
  customerProfile: {},
  quoteInputs: {},
  companyLookupCache: [],
};

/* ─── NAVIGATION HISTORY ────────────────────────────────────── */
let _navHistory = [];   // [{label, fn, args}]
let _navPos     = -1;   // current position in history

function _navLabel(view) {
  return { role: 'Home', signals: 'Signal Radar', pipeline: 'Pipeline', customer: 'Customer Quote', underwriter: 'Risk Form', results: 'Results', loading: null }[view] || view;
}

function navPush(fn, ...args) {
  // Truncate forward history when branching
  _navHistory = _navHistory.slice(0, _navPos + 1);
  _navHistory.push({ fn, args, view: state.view });
  _navPos = _navHistory.length - 1;
  fn(...args);
  _updateNavButtons();
}

let _navCalledByHistory = false;

function navBack() {
  if (_navPos <= 0) return;
  _navPos--;
  _navCalledByHistory = true;
  const entry = _navHistory[_navPos];
  entry.fn(...entry.args);
  _navCalledByHistory = false;
  _updateNavButtons();
}

function navForward() {
  if (_navPos >= _navHistory.length - 1) return;
  _navPos++;
  _navCalledByHistory = true;
  const entry = _navHistory[_navPos];
  entry.fn(...entry.args);
  _navCalledByHistory = false;
  _updateNavButtons();
}

function _updateNavButtons() {
  const bar = document.getElementById('nav-history-bar');
  if (!bar) return;
  const backBtn = document.getElementById('nav-back-btn');
  const fwdBtn  = document.getElementById('nav-fwd-btn');
  const label   = document.getElementById('nav-crumb');
  if (backBtn) backBtn.disabled = _navPos <= 0;
  if (fwdBtn)  fwdBtn.disabled  = _navPos >= _navHistory.length - 1;
  if (label) {
    const prev = _navPos > 0 ? _navHistory[_navPos - 1] : null;
    const next = _navPos < _navHistory.length - 1 ? _navHistory[_navPos + 1] : null;
    backBtn && (backBtn.title = prev ? 'Back to ' + _navLabel(prev.view) : 'No history');
    fwdBtn  && (fwdBtn.title  = next ? 'Forward to ' + _navLabel(next.view) : 'Nothing ahead');
  }
  bar.style.display = _navHistory.length > 1 ? 'flex' : 'none';
}

function _injectNavBar() {
  if (document.getElementById('nav-history-bar')) return;
  const bar = document.createElement('div');
  bar.id = 'nav-history-bar';
  bar.innerHTML = `
    <button id="nav-back-btn" class="nav-hist-btn" onclick="navBack()" disabled title="Back">&#8592;</button>
    <button id="nav-fwd-btn"  class="nav-hist-btn" onclick="navForward()" disabled title="Forward">&#8594;</button>
  `;
  document.body.appendChild(bar);
  _updateNavButtons();
}

/* ─── UTILS ──────────────────────────────────────────────────── */
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
const labelize = (k) => k.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());
const STORAGE_KEY = "sparc_underwriter_profile_v1";

const SECTION_IDS = ["section-identity","section-shape","section-exposure","section-advanced"];
const SECTION_FIELDS = {
  identity: ["startup_name", "sector", "funding_stage", "team_size", "has_investors"],
  shape: ["operations", "data_sensitivity", "ai_in_product", "customer_type", "annual_revenue_cr", "total_insurable_asset_value_cr", "product_description"],
  exposure: ["data_handled", "regulatory", "physical_assets", "biggest_fear"],
  advanced: [
    "investor_cn_hk_pct", "cumulative_fundraising_inr_cr", "holdco_domicile",
    "founder_equity_pct", "has_independent_directors", "dpiit_recognition", "rbi_registration",
    "gig_headcount_pct", "posh_ic_constituted", "state_footprint",
    "cert_in_poc_designated", "sdf_likely", "data_localisation_status",
    "ai_tier", "hardware_software_split", "b2b_pct", "export_eu_pct",
    "export_us_pct", "export_china_pct", "chinese_supplier_pct_cogs",
    "listed_customer_brsr_dependency", "facility_climate_risk_zone",
    "gross_profit_cr", "fleet_count", "healthcare_operations", "payment_or_card_program",
    "product_recall_exposure", "food_or_pharma_manufacturing",
    "contract_bid_or_performance_bond_need", "project_value_cr",
    "event_or_production_operations", "claims_last_3_years",
  ],
};

const SECTOR_TAILORING = {
  "Fintech": { key: "fintech", label: "Fintech" },
  "Healthtech": { key: "healthtech", label: "Healthtech" },
  "Deeptech / AI / Robotics": { key: "deeptech", label: "Deeptech" },
  "D2C / Consumer Brands": { key: "d2c", label: "D2C" },
  "Logistics / Mobility": { key: "logistics", label: "Logistics" },
};

function getTailoring() {
  return SECTOR_TAILORING[state.profile?.sector] || null;
}

function tailoringTag(sectionId) {
  const t = getTailoring();
  if (!t) return "";
  const activeSections = {
    fintech: ["exposure", "advanced"],
    healthtech: ["exposure"],
    deeptech: ["shape", "advanced"],
    d2c: ["exposure", "advanced"],
    logistics: ["exposure", "advanced"],
  }[t.key] || [];
  if (!activeSections.includes(sectionId)) return "";
  return `<div class="tailor-tag">Tailored for ${esc(t.label)} <span aria-hidden="true">🎯</span></div>`;
}

function sectionHeader(index, title, sectionId, suffix="") {
  return `
    <div class="section-head">
      <div>
        <div class="section-label">${String(index + 1).padStart(2, "0")} — ${esc(title)}${suffix}</div>
        ${tailoringTag(sectionId)}
      </div>
      <span class="save-status">Saved ✓</span>
    </div>`;
}

function sectionHeaderWithReset(index, title, sectionId, suffix="") {
  return `
    <div class="section-head">
      <div>
        <div class="section-label">${String(index + 1).padStart(2, "0")} - ${esc(title)}${suffix}</div>
        ${tailoringTag(sectionId)}
      </div>
      <div class="section-head-actions">
        <button class="section-reset-btn" type="button" onclick="resetSectionInputs('${esc(sectionId)}')">Reset screen</button>
        <span class="save-status">Saved</span>
      </div>
    </div>`;
}

sectionHeader = sectionHeaderWithReset;

function fieldFilled(key) {
  const value = state.profile?.[key];
  if (key === "ai_in_product") return typeof value === "boolean";
  if (key === "team_size") return Number(value) > 0;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "boolean") return value === true;
  if (typeof value === "number") return value > 0;
  if (value === null || value === undefined) return false;
  const text = String(value).trim();
  return text !== "" && text !== "None" && text !== "Unknown";
}

function sectionCount(sectionId) {
  const keys = SECTION_FIELDS[sectionId] || [];
  return {
    filled: keys.filter(fieldFilled).length,
    total: keys.length,
  };
}

function saveDraftProfile() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      profile: state.profile,
      maxVisitedSection: state.maxVisitedSection,
      section: state.section,
    }));
  } catch (e) {
    // localStorage may be unavailable in private or embedded contexts.
  }
}

function loadDraftProfile(defaults) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return structuredClone(defaults);
    const saved = JSON.parse(raw);
    state.maxVisitedSection = Math.min(SECTIONS.length - 1, Math.max(0, Number(saved.maxVisitedSection || 0)));
    state.section = Math.min(state.maxVisitedSection, Math.max(0, Number(saved.section || 0)));
    return { ...structuredClone(defaults), ...(saved.profile || {}) };
  } catch (e) {
    return structuredClone(defaults);
  }
}

function showSavedMicroLabel() {
  const label = document.querySelector(".form-section.visible .save-status");
  if (!label) return;
  label.classList.add("visible");
  clearTimeout(state.saveTimer);
  state.saveTimer = setTimeout(() => label.classList.remove("visible"), 1200);
}

function afterProfileChange({ refreshAdaptive = false } = {}) {
  saveDraftProfile();
  if (refreshAdaptive) refreshAdaptiveSections();
  updateProgress();
  updateProfileSummary();
  updateSectionScorePreview();
  showSavedMicroLabel();
}

const SECTION_RESET_VALUES = {
  identity: {
    startup_name: "",
    sector: "",
    sub_sector: null,
    funding_stage: "",
    team_size: 0,
    has_investors: "No",
  },
  shape: {
    operations: "",
    data_sensitivity: "",
    ai_in_product: false,
    ai_tier: "None",
    customer_type: [],
    annual_revenue_cr: 0,
    total_insurable_asset_value_cr: 0,
    product_description: "",
  },
  exposure: {
    data_handled: [],
    regulatory: [],
    physical_assets: [],
    biggest_fear: "",
  },
  advanced: {
    investor_cn_hk_pct: 0,
    cumulative_fundraising_inr_cr: 0,
    holdco_domicile: "India",
    founder_equity_pct: 0,
    has_independent_directors: false,
    dpiit_recognition: false,
    rbi_registration: null,
    gig_headcount_pct: 0,
    posh_ic_constituted: false,
    state_footprint: [],
    cert_in_poc_designated: false,
    sdf_likely: false,
    sdf_probability: 0,
    data_localisation_status: "Unknown",
    ai_tier: "None",
    hardware_software_split: 0,
    b2b_pct: 0,
    export_eu_pct: 0,
    export_us_pct: 0,
    export_china_pct: 0,
    chinese_supplier_pct_cogs: 0,
    listed_customer_brsr_dependency: false,
    facility_climate_risk_zone: "Low",
    gross_profit_cr: 0,
    fleet_count: 0,
    healthcare_operations: false,
    payment_or_card_program: false,
    product_recall_exposure: false,
    food_or_pharma_manufacturing: false,
    contract_bid_or_performance_bond_need: false,
    project_value_cr: 0,
    event_or_production_operations: false,
    claims_last_3_years: 0,
  },
};

window.resetSectionInputs = (sectionId) => {
  const resetValues = SECTION_RESET_VALUES[sectionId];
  if (!resetValues) return;
  Object.entries(resetValues).forEach(([key, value]) => {
    state.profile[key] = Array.isArray(value) ? [] : value;
  });
  const needsAdaptiveRefresh = ["identity", "shape", "exposure", "advanced"].includes(sectionId);
  afterProfileChange({ refreshAdaptive: needsAdaptiveRefresh });
};

window.importProfileFromJson = (analyse = false) => {
  const input = $("profile-import-json");
  try {
    const raw = (input?.value || "").trim();
    if (!raw) {
      if (analyse && state.profile?.startup_name) {
        updateProfileImportStatus(`Analysing loaded form for ${state.profile.startup_name}.`, "success");
        runAnalysis();
      } else {
        updateProfileImportStatus("Paste JSON or load a company record before importing.", "error");
      }
      return;
    }
    const parsed = extractProfileJson(raw);
    const { profile, importedKeys, ignored } = normalizeImportedProfile(parsed);
    state.profile = profile;
    state.quoteInputs = {};
    state.quoteSuggestionsPreFilled = false;
    state.section = 0;
    state.maxVisitedSection = SECTIONS.length - 1;
    saveDraftProfile();
    refreshAdaptiveSections();
    updateProfileImportStatus(
      `Imported ${importedKeys.length} fields${ignored.length ? `; ignored ${ignored.length} unknown keys` : ""}.`,
      "success"
    );
    if (analyse) runAnalysis();
  } catch (err) {
    updateProfileImportStatus(`Import failed: ${err.message}`, "error");
  }
};

function applyImportedCompanyProfile(profile, analyse = false) {
  state.profile = { ...structuredClone(state.meta?.defaults || {}), ...(profile || {}) };
  state.quoteInputs = {};
  state.quoteSuggestionsPreFilled = false;
  state.section = 0;
  state.maxVisitedSection = SECTIONS.length - 1;
  saveDraftProfile();
  refreshAdaptiveSections();
  const query = $("company-profile-query");
  const results = $("company-profile-results");
  if (query) query.value = profile.startup_name || "";
  if (results) results.classList.remove("open");
  updateProfileImportStatus(`Loaded database record for ${profile.startup_name}. Review the populated fields, then click Import and analyse when ready.`, "success");
  if (analyse) runAnalysis();
}

window.searchCompanyProfiles = async () => {
  const query = $("company-profile-query")?.value || "";
  const results = $("company-profile-results");
  if (results) results.innerHTML = `<div class="company-profile-empty">Searching...</div>`;
  try {
    const res = await fetch(`/api/company-profiles?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "Search failed");
    const matches = data.matches || [];
    if (!matches.length) {
      if (results) results.innerHTML = `<div class="company-profile-empty">No company record found. Try another name or paste JSON.</div>`;
      return;
    }
    if (results) {
      results.innerHTML = matches.map(item => `
        <div class="company-profile-result">
          <div>
            <strong>${esc(item.name)}</strong>
            <span>${esc(item.sector)} · ${esc(item.funding_stage)} · ${esc(item.team_size)} people</span>
          </div>
          <div class="company-profile-actions">
            <button type="button" class="btn btn-primary" onclick="loadCompanyProfile('${esc(item.name)}', false)">Load into form</button>
          </div>
        </div>`).join("");
    }
  } catch (err) {
    if (results) results.innerHTML = `<div class="company-profile-empty">Error: ${esc(err.message)}</div>`;
  }
};

async function fetchCompanyLookupOptions(query = "") {
  const res = await fetch(`/api/company-profiles?q=${encodeURIComponent(query)}&limit=100`);
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || "Search failed");
  state.companyLookupCache = data.matches || [];
  return state.companyLookupCache;
}

function renderCompanyLookupDropdown(matches, query = "") {
  const results = $("company-profile-results");
  if (!results) return;
  const count = state.meta?.seedCompanyProfiles || matches.length || 0;
  if (!matches.length) {
    results.innerHTML = `<div class="company-profile-empty">No company record found${query ? ` for "${esc(query)}"` : ""}. Try another name or paste JSON.</div>`;
    results.classList.add("open");
    return;
  }
  results.innerHTML = `
    <div class="company-profile-dropdown-head">${query ? `${matches.length} matching company record${matches.length === 1 ? "" : "s"}` : `Showing ${matches.length} company records from database`}</div>
    ${matches.map(item => `
      <button class="company-profile-option" type="button" data-company-name="${esc(item.name)}" onclick="loadCompanyProfileFromOption(this, false)">
        <span>
          <strong>${esc(item.name)}</strong>
          <em>${esc(item.sector)} · ${esc(item.funding_stage)} · ${esc(item.team_size)} people</em>
        </span>
        <b>Load</b>
      </button>`).join("")}
    ${!query && count > matches.length ? `<div class="company-profile-empty">Type to narrow the ${esc(count)} company database records.</div>` : ""}`;
  results.classList.add("open");
}

window.showCompanyLookupDropdown = async () => {
  const query = $("company-profile-query")?.value || "";
  const results = $("company-profile-results");
  if (results) {
    results.innerHTML = `<div class="company-profile-empty">Loading company database...</div>`;
    results.classList.add("open");
  }
  try {
    renderCompanyLookupDropdown(await fetchCompanyLookupOptions(query), query);
  } catch (err) {
    if (results) results.innerHTML = `<div class="company-profile-empty">Error: ${esc(err.message)}</div>`;
  }
};

window.searchCompanyProfiles = async () => {
  const query = $("company-profile-query")?.value || "";
  const results = $("company-profile-results");
  if (results) {
    results.innerHTML = `<div class="company-profile-empty">Searching...</div>`;
    results.classList.add("open");
  }
  try {
    renderCompanyLookupDropdown(await fetchCompanyLookupOptions(query), query);
  } catch (err) {
    if (results) results.innerHTML = `<div class="company-profile-empty">Error: ${esc(err.message)}</div>`;
  }
};

window.loadCompanyProfileFromOption = (button, analyse = false) => {
  const name = button?.dataset?.companyName;
  if (name) window.loadCompanyProfile(name, analyse);
};

window.loadCompanyProfile = async (name, analyse = false) => {
  try {
    const res = await fetch(`/api/company-profiles?name=${encodeURIComponent(name)}`);
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "Profile not found");
    applyImportedCompanyProfile(data.profile, analyse);
  } catch (err) {
    updateProfileImportStatus(`Company lookup failed: ${err.message}`, "error");
  }
};

const COVER_ALIASES = {
  "CYBER": "cyber_liability", "D_AND_O": "dno_liability", "PI_TECH_EO": "professional_indemnity",
  "CGL_I_ELITE": "comprehensive_general_liability", "PUBLIC_LIABILITY": "public_liability",
  "PRODUCT_LIABILITY": "product_liability", "EMPLOYERS_COMP": "employees_comp",
  "GROUP_HEALTH": "employee_health", "GROUP_PA": "group_pa",
  "BHARAT_SOOKSHMA": "property_fire", "PROPERTY_FIRE": "property_fire",
  "PROPERTY_ALL_RISK": "property_all_risk", "ELECTRONIC_EQUIPMENT": "electronic_equipment",
  "BUSINESS_INTERRUPTION": "business_interruption", "MACHINERY_BREAKDOWN": "machinery_breakdown",
  "MOTOR_FLEET": "motor_fleet", "HEALTHCARE_PI": "healthcare_pi",
  "FINANCIAL_SERVICES_PI": "financial_services_pi", "PAYMENT_PROTECTION": "payment_protection",
  "PRODUCT_RECALL": "product_recall", "TOTAL_RECALL": "product_recall",
  "EVENT_PRODUCTION": "event_production", "ENTERTAINMENT_PRODUCTION": "event_production",
  "ENGINEERING_CAR_EAR_CPM_MBD_EEI": "engineering", "SURETY": "surety",
  "MARINE_CARGO": "marine_transit", "TRADE_CREDIT": "trade_credit",
  "PRAKRITIK_PARAMETRIC": "parametric", "CRIME_FIDELITY": "crime_fidelity",
  "Drone_RPAS": "drone_insurance",
  "EMPLOYMENT_PRACTICES": "employment_practices",
  "employment_practices": "employment_practices",
  "EPL": "employment_practices",
  "epl": "employment_practices",
  "EPLI": "employment_practices",
  "epli": "employment_practices",
  "GROUP_CRITI_SHIELD": "group_criti_shield",
  "group_criti_shield": "group_criti_shield",
  "criti_shield": "group_criti_shield",
  "GROUP_HOSPISHIELD": "group_hospishield",
  "group_hospishield": "group_hospishield",
  "hospishield": "group_hospishield",
  "BHARAT_LAGHU": "property_fire",
  "bharat_laghu": "property_fire",
};

Object.assign(COVER_ALIASES, {
  "Cyber Liability": "CYBER",
  "cyber liability": "CYBER",
  "cyber_liability": "CYBER",
  "Dno Liability": "D_AND_O",
  "D&O Liability": "D_AND_O",
  "D and O": "D_AND_O",
  "Directors and Officers Liability": "D_AND_O",
  "dno_liability": "D_AND_O",
  "Professional Indemnity": "PI_TECH_EO",
  "Professional Indemnity / Tech E&O": "PI_TECH_EO",
  "Tech E&O": "PI_TECH_EO",
  "professional_indemnity": "PI_TECH_EO",
  "Employee Health": "GROUP_HEALTH",
  "Group Health": "GROUP_HEALTH",
  "employee_health": "GROUP_HEALTH",
  "Group Pa": "GROUP_PA",
  "Group Personal Accident": "GROUP_PA",
  "group_pa": "GROUP_PA",
  "Employment Practices": "EMPLOYMENT_PRACTICES",
  "Employment Practices Liability": "EMPLOYMENT_PRACTICES",
  "employment_practices": "EMPLOYMENT_PRACTICES",
  "Key Person": "key_person",
  "Key Person Insurance": "key_person",
  "key_person": "key_person",
  "Crime Fidelity": "CRIME_FIDELITY",
  "Crime / Fidelity": "CRIME_FIDELITY",
  "crime_fidelity": "CRIME_FIDELITY",
});

function canonicalCoverCandidates(key) {
  const raw = String(key || "").trim();
  if (!raw) return [];
  const titleish = raw.replace(/_/g, " ").replace(/\s+/g, " ").trim();
  const upperish = raw.replace(/[\s/-]+/g, "_").replace(/&/g, "AND").toUpperCase();
  const lowerish = raw.toLowerCase();
  const aliasValues = [
    COVER_ALIASES[raw],
    COVER_ALIASES[titleish],
    COVER_ALIASES[upperish],
    COVER_ALIASES[lowerish],
  ].filter(Boolean);
  return [...new Set([
    raw,
    titleish,
    upperish,
    lowerish,
    ...aliasValues,
    ...aliasValues.map(v => COVER_ALIASES[v]).filter(Boolean),
  ].filter(Boolean))];
}

const PRODUCT_BLURBS = {
  "CYBER":                            "Covers data breach response, ransomware recovery, and regulatory penalties — directly required by CERT-In Directions 2022 and the DPDP Act.",
  "D_AND_O":                          "Protects founders and directors personally if investors, regulators, or employees file suit over decisions made on the company's behalf.",
  "PI_TECH_EO":                       "Pays legal defence and client claims if your software, API, or professional services cause a customer a financial loss or system failure.",
  "CRIME_FIDELITY":                   "Reimburses losses from employee fraud, theft, or forgery — critical once you have a finance team, vendor access, or payment flows.",
  "GROUP_HEALTH":                     "Medical cover for your entire team — a key hiring benefit and an IRDAI-regulated expectation once your headcount crosses 20.",
  "GROUP_PA":                         "Accidental death and disability cover for your workforce, and mandatory for aggregator platforms under the Code on Social Security 2020.",
  "EMPLOYERS_COMP":                   "Statutory payout if an employee is injured or dies at work — required under the Employees' Compensation Act 1923.",
  "PRODUCT_LIABILITY":                "Covers legal defence and settlements if your physical product causes injury or property damage to a customer or third party.",
  "PUBLIC_LIABILITY":                 "Covers third-party bodily injury or property damage claims arising from your premises, events, or day-to-day operations.",
  "BHARAT_SOOKSHMA":                  "IRDAI-standardised product for micro enterprises. Covers building, plant, machinery, furniture, raw materials, and stock at one business location up to INR 5 Cr sum insured.",
  "MARINE_CARGO":                     "Covers goods in transit against loss or damage while your products move between warehouses, ports, or last-mile customers.",
  "TRADE_CREDIT":                     "Pays you when a B2B buyer defaults on an invoice — essential for startups extending credit terms to distributors or enterprise clients.",
  "ENGINEERING_CAR_EAR_CPM_MBD_EEI": "Covers physical damage to machinery, equipment under erection, and electronics — essential for hardware, robotics, and manufacturing startups.",
  "SURETY":                           "A performance bond required for government contracts, guaranteeing project completion and protecting against contractor default.",
  "PRAKRITIK_PARAMETRIC":             "Pays out automatically when a climate trigger — flood index, wind speed — is breached. No claims investigation; instant liquidity for climate-exposed ops.",
  "Drone_RPAS":                       "DGCA-mandated insurance for drone operations, covering hull damage and third-party liability arising from aerial activities under Drone Rules 2021.",
  "CGL_I_ELITE":                      "Comprehensive general liability for bodily injury, property damage, and personal injury claims from any third party — the corporate liability cornerstone.",
  "EMPLOYMENT_PRACTICES":             "Covers legal defence and settlements if an employee sues the company for wrongful termination, discrimination, harassment, or POSH Act violations. Mandatory in any startup approaching 50+ headcount with active hiring and termination activity.",
  "employment_practices":             "Covers legal defence and settlements if an employee sues the company for wrongful termination, discrimination, harassment, or POSH Act violations. Mandatory in any startup approaching 50+ headcount with active hiring and termination activity.",
  "EPL":                              "Covers legal defence and settlements if an employee sues the company for wrongful termination, discrimination, harassment, or POSH Act violations. Mandatory in any startup approaching 50+ headcount with active hiring and termination activity.",
  "GROUP_CRITI_SHIELD":               "Pays a lump-sum benefit to employees diagnosed with a covered critical illness (cancer, heart attack, stroke, organ failure). Supplements group health when treatment costs exceed hospitalisation — a strong retention benefit for senior hires.",
  "group_criti_shield":               "Pays a lump-sum benefit to employees diagnosed with a covered critical illness (cancer, heart attack, stroke, organ failure). Supplements group health when treatment costs exceed hospitalisation — a strong retention benefit for senior hires.",
  "GROUP_HOSPISHIELD":                "Daily hospital cash benefit that pays a fixed amount per day of hospitalisation regardless of actual medical bills — covers incidentals, loss of income, and recovery costs not reimbursed by the primary group health policy.",
  "group_hospishield":                "Daily hospital cash benefit that pays a fixed amount per day of hospitalisation regardless of actual medical bills — covers incidentals, loss of income, and recovery costs not reimbursed by the primary group health policy.",
};
Object.assign(PRODUCT_BLURBS, {
  "BUSINESS_INTERRUPTION": "Covers lost gross profit and continuing expenses after insured property damage disrupts operations.",
  "PROPERTY_ALL_RISK": "Broader property cover for labs, plants, warehouses, and infrastructure where named-peril fire cover is too narrow.",
  "MACHINERY_BREAKDOWN": "Covers sudden mechanical or electrical breakdown of production, lab, plant, and process machinery.",
  "MOTOR_FLEET": "Commercial motor package protection for owned or operated delivery vehicles, goods carriers, trailers, and field-service fleets.",
  "HEALTHCARE_PI": "Medical professional liability for clinical negligence, patient injury, diagnostic error, and healthcare service exposure.",
  "FINANCIAL_SERVICES_PI": "Financial institution professional indemnity for lending, payments, wealthtech, insurtech, and regulated advisory exposure.",
  "PAYMENT_PROTECTION": "Covers payment/card programme losses, unauthorised transaction exposure, and customer compensation obligations.",
  "PRODUCT_RECALL": "Pays recall, contamination, withdrawal, replacement, and brand rehabilitation costs for controlled product batches.",
  "EVENT_PRODUCTION": "Production and event package cover for venue, equipment, liability, interruption, and cancellation-sensitive operations.",
  "key_person": "Protects the company against financial disruption if a founder or critical leader dies or is disabled. It gives the startup cash runway to hire, transition responsibilities, and reassure investors during a leadership shock.",
});

const OFFICIAL_IL_BUNDLE_NAMES = new Set([
  "Business Shield SME",
  "Corporate Cover II",
  "MSME Suraksha Kavach",
  "Bharat Sookshma Udyam Suraksha",
  "Industrial All Risk (IAR) Policy",
  "Group Safeguard Insurance Policy",
  "Contractor All Risk (CAR) Insurance Policy",
  "Business Edge Policy",
  "Enterprise Secure Package Policy",
]);

const formatVal = (v) => {
  if (Array.isArray(v)) return v.length ? v.join(", ") : "None";
  if (v === null || v === undefined || v === "") return "None";
  if (typeof v === "boolean") return v ? "Yes" : "No";
  return String(v);
};

const API_OPERATION_MAP = {
  "Hardware / IoT": "Hybrid",
  "Marketplace": "Digital-only",
  "Hybrid (online+offline)": "Hybrid",
  "Offline / Physical": "Physical-only",
};

const REVENUE_MAP = {
  "Pre-revenue": 0,
  "Below INR 1 Cr": 0.5,
  "INR 1-5 Cr": 3,
  "INR 5-25 Cr": 15,
  "INR 25 Cr+": 50,
};

const TEAM_MAP = {
  "1-10": 7,
  "11-50": 25,
  "51-200": 100,
  "200+": 300,
};

const PROFILE_IMPORT_ALIASES = {
  company_name: "startup_name",
  business_name: "startup_name",
  name: "startup_name",
  industry: "sector",
  stage: "funding_stage",
  funding_status: "funding_stage",
  employees: "team_size",
  employee_count: "team_size",
  headcount: "team_size",
  operating_model: "operations",
  model: "operations",
  customers: "customer_type",
  customer_types: "customer_type",
  sensitive_data: "data_handled",
  data_types: "data_handled",
  regulations: "regulatory",
  regulatory_exposures: "regulatory",
  assets: "physical_assets",
  physical_asset: "physical_assets",
  fear: "biggest_fear",
  concern: "biggest_fear",
  revenue_cr: "annual_revenue_cr",
  arr_cr: "annual_revenue_cr",
  assets_cr: "total_insurable_asset_value_cr",
};

const PROFILE_IMPORT_ARRAY_FIELDS = new Set([
  "customer_type",
  "data_handled",
  "regulatory",
  "physical_assets",
  "state_footprint",
  "vehicle_types",
]);

const PROFILE_IMPORT_NUMBER_FIELDS = new Set([
  "team_size",
  "investor_cn_hk_pct",
  "cumulative_fundraising_inr_cr",
  "founder_equity_pct",
  "gig_headcount_pct",
  "sdf_probability",
  "hardware_software_split",
  "b2b_pct",
  "annual_revenue_cr",
  "total_insurable_asset_value_cr",
  "gross_profit_cr",
  "fleet_count",
  "project_value_cr",
  "export_eu_pct",
  "export_us_pct",
  "export_china_pct",
  "chinese_supplier_pct_cogs",
]);

const PROFILE_IMPORT_BOOLEAN_FIELDS = new Set([
  "dpiit_recognition",
  "rbi_registration",
  "posh_ic_constituted",
  "cert_in_poc_designated",
  "sdf_likely",
  "ai_in_product",
  "has_independent_directors",
  "healthcare_operations",
  "payment_or_card_program",
  "product_recall_exposure",
  "food_or_pharma_manufacturing",
  "contract_bid_or_performance_bond_need",
  "event_or_production_operations",
  "claims_last_3_years",
  "listed_customer_brsr_dependency",
]);

function extractProfileJson(raw) {
  const text = String(raw || "").trim().replace(/^```(?:json)?/i, "").replace(/```$/i, "").trim();
  if (!text) throw new Error("Paste a JSON startup profile first.");
  try {
    return JSON.parse(text);
  } catch (firstErr) {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) return JSON.parse(text.slice(start, end + 1));
    throw firstErr;
  }
}

function coerceImportValue(key, value) {
  if (PROFILE_IMPORT_ARRAY_FIELDS.has(key)) {
    if (Array.isArray(value)) return value.filter(v => v !== null && v !== undefined && String(v).trim() !== "").map(v => String(v).trim());
    if (typeof value === "string") return value.split(",").map(v => v.trim()).filter(Boolean);
    return [];
  }
  if (PROFILE_IMPORT_NUMBER_FIELDS.has(key)) {
    const num = Number(value);
    return Number.isFinite(num) ? num : 0;
  }
  if (PROFILE_IMPORT_BOOLEAN_FIELDS.has(key)) {
    if (typeof value === "boolean") return value;
    if (typeof value === "string") return ["true", "yes", "y", "1"].includes(value.trim().toLowerCase());
    return Boolean(value);
  }
  return value;
}

function normalizeImportedProfile(input) {
  if (!input || typeof input !== "object" || Array.isArray(input)) {
    throw new Error("The pasted profile must be a JSON object.");
  }
  const defaults = structuredClone(state.meta?.defaults || {});
  const allowed = new Set([...Object.keys(defaults), ...Object.values(PROFILE_IMPORT_ALIASES)]);
  const normalized = {};
  const ignored = [];
  Object.entries(input).forEach(([rawKey, rawValue]) => {
    const key = PROFILE_IMPORT_ALIASES[rawKey] || rawKey;
    if (!allowed.has(key)) {
      ignored.push(rawKey);
      return;
    }
    normalized[key] = coerceImportValue(key, rawValue);
  });
  if (normalized.operations === "Hybrid") normalized.operations = "Hybrid (online+offline)";
  if (normalized.ai_tier && normalized.ai_tier !== "None") normalized.ai_in_product = true;
  if (normalized.sdf_probability !== undefined && normalized.sdf_probability >= 0.5) normalized.sdf_likely = true;
  return { profile: { ...defaults, ...normalized }, importedKeys: Object.keys(normalized), ignored };
}

function updateProfileImportStatus(message, tone = "neutral") {
  const el = $("profile-import-status");
  if (!el) return;
  el.className = `profile-import-status ${tone}`;
  el.textContent = message;
}

function renderProfileImportPanel() {
  return `
    <details class="profile-import-card">
      <summary>
        <span>
          <strong>Search your database for the name of your company</strong>
          <em>Retrieve a company record for risk assessment, or paste JSON to score directly.</em>
        </span>
        <b>Open</b>
      </summary>
      <div class="company-lookup-box">
        <label>Company database lookup</label>
        <div class="company-lookup-row">
          <input id="company-profile-query" class="f-input" type="text" placeholder="Enter company name, e.g. Razorpay, Zepto, Practo, Freshworks" onfocus="showCompanyLookupDropdown()" oninput="searchCompanyProfiles()" onkeydown="if(event.key==='Enter') searchCompanyProfiles()" autocomplete="off" />
        </div>
        <div id="company-profile-results" class="company-profile-results"></div>
      </div>
      <div class="profile-import-divider"><span>or paste JSON</span></div>
      <textarea id="profile-import-json" class="profile-import-textarea" spellcheck="false" placeholder='{"startup_name":"PayNova Technologies","sector":"Fintech","funding_stage":"Series B+"}'></textarea>
      <div class="profile-import-actions">
        <button class="btn btn-ghost" type="button" onclick="importProfileFromJson(false)">Import into form</button>
        <button class="btn btn-primary" type="button" onclick="importProfileFromJson(true)">Import and analyse</button>
      </div>
      <div id="profile-import-status" class="profile-import-status">Accepted format: JSON object using API field names or common aliases like company_name, stage, employees, customers, regulations.</div>
    </details>`;
}

function buildProfile(sourceProfile = state.profile) {
  const profile = structuredClone(sourceProfile || {});
  profile.operations = API_OPERATION_MAP[profile.operations] || profile.operations;
  if (profile.data_sensitivity === "Very High") profile.data_sensitivity = "High";
  const founderEquity = Number(profile.founder_equity_pct ?? 0.5);
  profile.founder_concentration_index = founderEquity * (1 - (profile.has_independent_directors ? 0.4 : 0));
  if (profile.sdf_likely === true) {
    profile.sdf_probability = Math.max(Number(profile.sdf_probability || 0), 0.75);
  } else if (profile.sdf_probability === undefined || profile.sdf_probability === null || profile.sdf_probability === "") {
    profile.sdf_probability = 0.05;
  } else {
    profile.sdf_probability = Number(profile.sdf_probability) || 0;
  }
  return profile;
}

/* ─── INIT ───────────────────────────────────────────────────── */
async function init() {
  renderApp();
  _injectNavBar();
  const stub = buildStubMeta();
  try {
    const res = await fetch("/api/meta");
    if (!res.ok) throw new Error("no meta");
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("json")) throw new Error("not json");
    const serverMeta = await res.json();
    // Merge: server values take priority, stub fills any missing fields
    state.meta = { ...stub, ...serverMeta };
    state.profile = loadDraftProfile(state.meta.defaults);
  } catch (e) {
    state.meta = stub;
    state.profile = loadDraftProfile(state.meta.defaults);
  }
  resetCustomerProfile();

  // Restore last result if Vercel live-reloaded mid-session
  try {
    const saved = sessionStorage.getItem("sparc_last_result");
    if (saved) {
      const restored = JSON.parse(saved);
      if (restored?.profile?.startup_name) {
        renderResults(restored);
        return;
      }
    }
  } catch (_) {}

  renderRoleSelection();
}

function buildStubMeta() {
  return {
    defaults: {
      startup_name: "",
      sector: "SaaS / Enterprise Software",
      sub_sector: null,
      funding_stage: "Series A",
      team_size: 20,
      operations: "Digital-only",
      data_sensitivity: "Medium",
      ai_in_product: false,
      ai_tier: "None",
      customer_type: [],
      has_investors: "No",
      product_description: "",
      data_handled: [],
      regulatory: [],
      physical_assets: [],
      biggest_fear: "",
      investor_cn_hk_pct: 0,
      cumulative_fundraising_inr_cr: 0,
      holdco_domicile: "India",
      founder_equity_pct: 0.5,
      has_independent_directors: false,
      dpiit_recognition: false,
      rbi_registration: null,
      gig_headcount_pct: 0,
      posh_ic_constituted: false,
      state_footprint: [],
      cert_in_poc_designated: false,
      sdf_likely: false,
      data_localisation_status: "Unknown",
      hardware_software_split: 0,
      b2b_pct: 0.5,
      export_eu_pct: 0,
      export_us_pct: 0,
      export_china_pct: 0,
      chinese_supplier_pct_cogs: 0,
      listed_customer_brsr_dependency: false,
      facility_climate_risk_zone: "Low",
      annual_revenue_cr: 0,
      total_insurable_asset_value_cr: 0,
      gross_profit_cr: 0,
      fleet_count: 0,
      vehicle_types: [],
      healthcare_operations: false,
      payment_or_card_program: false,
      product_recall_exposure: false,
      food_or_pharma_manufacturing: false,
      contract_bid_or_performance_bond_need: false,
      project_value_cr: 0,
      event_or_production_operations: false,
      claims_last_3_years: false,
    },
    sectors: [
      "Fintech","Healthtech","SaaS / Enterprise Software","Deeptech / AI / Robotics",
      "Edtech","D2C / Consumer Brands","Logistics / Mobility","Agritech / Foodtech",
      "Cleantech / Climatetech","Gaming / Media / Content","HRtech","Legaltech",
      "Proptech","Spacetech","Insurtech","Other",
    ].map(n=>({name:n})),
    subSectorOptions: {},
    fundingStages: ["Pre-seed","Seed","Series A","Series B+"],
    operations: ["Digital-only","Physical-only","Hybrid"],
    dataSensitivity: ["Low","Medium","High"],
    customerTypeOptions: ["B2B Enterprise","B2B SMB","B2C Consumers","Government / PSU","D2C"],
    dataHandledOptions: [
      "Employee / HR data (payroll, biometrics)",
      "Customer behavioural / usage data",
      "Payments / financial transactions",
      "Health / medical records",
      "Children's data",
      "Biometric data",
      "Personal identity data (KYC / Aadhaar)",
      "Physical inventory / goods",
      "None / minimal",
    ],
    regulatoryOptions: [
      "DPDP Act obligations","RBI / SEBI / IRDAI licensed","FSSAI / food safety",
      "CDSCO / medical devices","DGCA / drone operations","IT Act / CERT-In obligations",
      "Labour Codes / gig worker regulations","MV Act / transport regulations",
      "NMC / telemedicine regulations","None / minimal",
    ],
    physicalAssetOptions: [
      "Office / coworking space","Warehouse / fulfilment centre","Manufacturing plant / factory",
      "Lab / R&D equipment","Medical devices / diagnostic equipment","Vehicles / delivery fleet",
      "Drones / UAV equipment","Kitchen / food processing","Cold chain / refrigeration",
      "Solar / clean energy infrastructure","Retail stores / kiosks","Data centre / server room",
      "None - fully cloud",
    ],
    states: ["Maharashtra","Karnataka","Delhi NCR","Tamil Nadu","Telangana","Gujarat","Rajasthan","Others"],
    holdcoDomiciles: ["India","Singapore","USA (Delaware)","Cayman Islands","Mauritius","UK","UAE","Netherlands"],
    rbiRegistrations: ["None","PA (Payment Aggregator)","PG (Payment Gateway)","NBFC","NBFC-AA","Prepaid Instruments"],
    aiTiers: ["None","Applied","Autonomous","Frontier"],
    climateZones: ["Low","Medium","High","Very High"],
  };
}

/* ─── TOP BAR ────────────────────────────────────────────────── */
function renderApp() {
  document.getElementById("app").innerHTML = `
    <div class="app-wrap">
      <header class="topbar">
        <div class="topbar-brand">
          <div class="brand-mark">S</div>
          <span class="topbar-name">SPARC</span>
        </div>
        <div class="topbar-sep"></div>
        <span class="topbar-sub">ICICI Lombard · Startup Risk Intelligence</span>
        <div class="topbar-mode" role="tablist" aria-label="App mode">
          <button type="button" class="topbar-mode-pill is-active" data-mode="analyse" role="tab" aria-selected="true">Analyse</button>
          <button type="button" class="topbar-mode-pill" data-mode="commerce" role="tab" aria-selected="false">Commerce</button>
        </div>
      </header>
      <div id="main-content"></div>
    </div>`;
  document.querySelectorAll(".topbar-mode-pill").forEach(btn => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-mode");
      if (mode === "commerce") enterCommerceMode();
      else exitCommerceMode();
    });
  });
}

/* ─── FORM RENDER ────────────────────────────────────────────── */
function resetCustomerProfile() {
  state.customerProfile = {
    business_name: "",
    persona: null,
    industry: state.meta?.defaults?.sector || "SaaS / Enterprise Software",
    revenue_range: "INR 1-5 Cr",
    team_range: "11-50",
    funding_status: "Seed",
    main_concern: "Customer contracts",
    handles: ["customer_data", "contracts"],
  };
}

function renderAutoProfilingLoader(companyName) {
  const BLIPS = [
    { angle: 32,  r: 62 }, { angle: 78,  r: 40 }, { angle: 118, r: 70 },
    { angle: 155, r: 50 }, { angle: 198, r: 65 }, { angle: 242, r: 38 },
    { angle: 285, r: 72 }, { angle: 318, r: 48 }, { angle: 348, r: 30 },
  ];

  // Intel checklist: each item ticks at `tickAt` ms
  const INTEL = [
    { text: "Public company profile loaded",      tickAt: 800  },
    { text: "Regulatory filings scanned",         tickAt: 1800 },
    { text: "Sector risk benchmarks applied",     tickAt: 2800 },
    { text: "Data exposure vectors mapped",       tickAt: 3800 },
    { text: "13 risk dimensions scored",          tickAt: 5200 },
    { text: "ICICI Lombard bundles matched",      tickAt: 6800 },
  ];

  // Stats: { label, target, suffix, duration ms }
  const STATS = [
    { id: "stat-sources", label: "Sources",    target: 847, suffix: "",  dur: 4000 },
    { id: "stat-rules",   label: "Regulations",target: 23,  suffix: "",  dur: 3000 },
    { id: "stat-signals", label: "Signals",    target: 9,   suffix: "",  dur: 5000 },
  ];

  const toXY = (deg, r) => {
    const rad = (deg - 90) * Math.PI / 180;
    return [+(100 + r * Math.cos(rad)).toFixed(1), +(100 + r * Math.sin(rad)).toFixed(1)];
  };

  const blipsSvg = BLIPS.map((b, i) => {
    const [x, y] = toXY(b.angle, b.r);
    return `<g class="rblip" id="rblip-${i}">
      <circle cx="${x}" cy="${y}" r="3" fill="#AD1E23"/>
      <circle cx="${x}" cy="${y}" r="3" fill="none" stroke="#AD1E23" stroke-width="1.5" opacity=".6">
        <animate attributeName="r" from="4" to="14" dur="2s" repeatCount="indefinite"/>
        <animate attributeName="opacity" from="0.6" to="0" dur="2s" repeatCount="indefinite"/>
      </circle>
    </g>`;
  }).join("");

  $("main-content").innerHTML = `
    <main class="profiling-loader-shell">
      <div class="profiling-loader-inner">
        <div class="profiling-command-card">

          <div class="pcc-eyebrow">
            <span class="pcc-dot"></span>
            SPARC Intelligence &middot; Risk Analysis
          </div>
          <div class="pcc-company">${esc(companyName)}</div>

          <div class="pcc-body">
            <!-- LEFT: radar -->
            <div class="pcc-radar-col">
              <div class="radar-wrap">
                <div class="radar-sweep"></div>
                <svg class="radar-svg" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="100" cy="100" r="85" fill="none" stroke="rgba(255,255,255,.06)" stroke-width="1"/>
                  <circle cx="100" cy="100" r="57" fill="none" stroke="rgba(255,255,255,.05)" stroke-width="1"/>
                  <circle cx="100" cy="100" r="28" fill="none" stroke="rgba(255,255,255,.07)" stroke-width="1"/>
                  <line x1="100" y1="14" x2="100" y2="186" stroke="rgba(255,255,255,.04)" stroke-width="1"/>
                  <line x1="14"  y1="100" x2="186" y2="100" stroke="rgba(255,255,255,.04)" stroke-width="1"/>
                  <circle cx="100" cy="100" r="2.5" fill="rgba(255,255,255,.35)"/>
                  ${blipsSvg}
                </svg>
              </div>
              <!-- Stats row below radar -->
              <div class="pcc-stats">
                ${STATS.map(s => `
                  <div class="pcc-stat">
                    <span class="pcc-stat-num" id="${s.id}">0</span>
                    <span class="pcc-stat-label">${s.label}</span>
                  </div>`).join("")}
              </div>
            </div>

            <!-- RIGHT: intel checklist -->
            <div class="pcc-intel-col">
              <div class="pcc-intel-label">Intelligence feed</div>
              <ul class="pcc-checklist">
                ${INTEL.map((item, i) => `
                  <li class="pcc-check-item" id="ci-${i}">
                    <span class="pcc-check-icon"></span>
                    <span class="pcc-check-text">${item.text}</span>
                  </li>`).join("")}
              </ul>
            </div>
          </div>

          <div class="pcc-bar-track" style="margin-top:20px;">
            <div class="pcc-bar-fill" id="profiling-bar" style="width:4%"></div>
          </div>

        </div>
        <p class="profiling-disclaimer">Gemini &middot; Google Search grounding &middot; IRDAI actuarial data</p>
      </div>
    </main>`;

  // Blip reveal timed to sweep position
  const SWEEP_OFFSET_DEG = 62, REV_MS = 3000;
  BLIPS.forEach((b, i) => {
    let deg = b.angle - SWEEP_OFFSET_DEG;
    if (deg < 0) deg += 360;
    setTimeout(() => {
      const el = document.getElementById(`rblip-${i}`);
      if (el) el.classList.add("rblip-on");
    }, (deg / 360) * REV_MS + 120);
  });

  // Intel checklist ticks
  INTEL.forEach((item, i) => {
    setTimeout(() => {
      const li = document.getElementById(`ci-${i}`);
      if (li) li.classList.add("ci-done");
    }, item.tickAt);
  });

  // Stats counter animation
  STATS.forEach(s => {
    const el = document.getElementById(s.id);
    if (!el) return;
    const start = performance.now();
    const tick = (now) => {
      const pct = Math.min((now - start) / s.dur, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - pct, 3);
      el.textContent = Math.round(eased * s.target) + s.suffix;
      if (pct < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  // Progress bar
  const steps = [
    { pct: 28, ms: 0    },
    { pct: 60, ms: 3200 },
    { pct: 85, ms: 6400 },
  ];
  const bar = document.getElementById("profiling-bar");
  steps.forEach(s => {
    setTimeout(() => { if (bar) bar.style.width = s.pct + "%"; }, s.ms);
  });

  return () => {
    if (bar) bar.style.width = "100%";
    BLIPS.forEach((_, i) => {
      const el = document.getElementById(`rblip-${i}`);
      if (el) el.classList.add("rblip-on");
    });
    INTEL.forEach((_, i) => {
      const li = document.getElementById(`ci-${i}`);
      if (li) li.classList.add("ci-done");
    });
    STATS.forEach(s => {
      const el = document.getElementById(s.id);
      if (el) el.textContent = s.target + s.suffix;
    });
  };
}

function classifyAutofillError(rawMessage) {
  const m = String(rawMessage || "");
  if (/503|high demand|unavailable|overloaded|capacity/i.test(m))
    return { title: "AI engine is temporarily busy", hint: "Demand spikes usually resolve in under a minute. Try again shortly." };
  if (/504|timeout|timed out|DEADLINE_EXCEEDED/i.test(m))
    return { title: "Request timed out", hint: "The profiling request took too long. Try again — it usually succeeds on the second attempt." };
  if (/429|rate.?limit|quota/i.test(m))
    return { title: "Rate limit reached", hint: "Too many requests in a short window. Wait a moment and try again." };
  if (/401|403|auth|api.?key/i.test(m))
    return { title: "Authentication error", hint: "There is a configuration issue on the server. Contact the admin." };
  if (/network|fetch|Failed to fetch/i.test(m))
    return { title: "Connection failed", hint: "Could not reach the server. Check your network and try again." };
  if (/JSON|parse|json object/i.test(m))
    return { title: "AI engine is temporarily busy", hint: "The model returned an incomplete response. Try again — it usually works on the second attempt." };
  return { title: "Profile could not be generated", hint: "An unexpected error occurred. Try again or enter details manually below." };
}

function renderProfileSneak(profile) {
  const summary = (profile.product_description || "").trim();
  const risks   = (profile.biggest_fear || "").trim();
  if (!summary && !risks) return;
  const shell = document.querySelector(".profiling-loader-inner");
  if (!shell) return;
  const card = document.createElement("div");
  card.className = "profile-sneak-card";
  card.innerHTML = `
    <div class="profile-sneak-header">
      <span class="profile-sneak-name">${esc(profile.startup_name || "")}</span>
      <span class="profile-sneak-meta">${esc(profile.sector || "")}${profile.funding_stage ? " &middot; " + esc(profile.funding_stage) : ""}</span>
    </div>
    ${summary ? `<p class="profile-sneak-summary">${esc(summary)}</p>` : ""}
    ${risks   ? `<p class="profile-sneak-risks"><span class="profile-sneak-risks-label">Top risks:</span> ${esc(risks)}</p>` : ""}`;
  shell.appendChild(card);
  requestAnimationFrame(() => card.classList.add("profile-sneak-visible"));
}

async function triggerAutoProfiling(companyName, _retryCount = 0, signalContext = null) {
  const cancelLoader = renderAutoProfilingLoader(companyName);
  try {
    // Step 1: /api/autofill — Gemini only, no server.py import, fast (<8s)
    const autofillRes = await fetch("/api/autofill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_name: companyName }),
    });
    let profile;
    try {
      profile = await autofillRes.json();
    } catch (jsonErr) {
      if (_retryCount < 1) {
        cancelLoader();
        return triggerAutoProfiling(companyName, _retryCount + 1, signalContext);
      }
      throw new Error("JSON parse error: " + jsonErr.message);
    }
    if (!autofillRes.ok || profile.error) {
      const errMsg = profile.error || "";
      const isTransient = !autofillRes.ok || /busy|overload|503|504|timeout|incomplete|truncat|json|parse/i.test(errMsg);
      if (_retryCount < 1 && isTransient) {
        cancelLoader();
        return triggerAutoProfiling(companyName, _retryCount + 1, signalContext);
      }
      throw new Error(errMsg || "Auto-profile failed");
    }

    // Local dev server returns a full result from /api/autofill already (profile+scores+bundles).
    // Vercel's /api/autofill returns only the raw Gemini profile — needs a second /api/analyze call.
    if (profile.scores && profile.bundle_match) {
      cancelLoader();
      if (signalContext) profile.signal_context = signalContext;
      renderResults(profile);
      return;
    }

    renderProfileSneak(profile);

    // Step 2: /api/analyze — pure Python computation, no Gemini, fast (<3s)
    const analyzeRes = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });
    let result;
    try {
      result = await analyzeRes.json();
    } catch (jsonErr) {
      throw new Error("Analyze parse error: " + jsonErr.message);
    }
    cancelLoader();
    if (!analyzeRes.ok || result.error) {
      throw new Error(result.error || "Analysis failed");
    }
    if (signalContext) result.signal_context = signalContext;
    renderResults(result);
  } catch (err) {
    cancelLoader();
    const { title, hint } = classifyAutofillError(err.message);
    $("main-content").innerHTML = `
      <main class="hev-shell hev-error-shell">
        <div class="hev-error-card">
          <div class="hev-error-icon">⚠</div>
          <div class="hev-error-company">${esc(companyName)}</div>
          <h2 class="hev-error-title">${esc(title)}</h2>
          <p class="hev-error-hint">${esc(hint)}</p>
          <div class="hev-error-actions">
            <button class="hev-search-btn" type="button" id="autofill-error-retry">
              Try again
              <span class="hev-btn-icon">↺</span>
            </button>
            <button class="hev-error-ghost" type="button" id="autofill-error-back">Back to home</button>
          </div>
        </div>
      </main>`;
    $("autofill-error-retry").onclick = () => triggerAutoProfiling(companyName);
    $("autofill-error-back").onclick  = () => renderRoleSelection();
  }
}

function renderRoleSelection() {
  state.view = "role";
  if (!_navCalledByHistory) { _navHistory = _navHistory.slice(0, _navPos + 1); _navHistory.push({ fn: renderRoleSelection, args: [], view: "role" }); _navPos = _navHistory.length - 1; setTimeout(_updateNavButtons, 0); }
  $("main-content").innerHTML = `
    <main class="hev-shell">

      <div class="hev-orb" aria-hidden="true"></div>

      <section class="hev-hero">
        <div class="hev-eyebrow hev-reveal">
          <span class="hev-eyebrow-dot"></span>
          SPARC &middot; Pre-meeting intelligence
        </div>

        <h1 class="hev-headline hev-reveal">
          Know every risk<br>
          <span class="hev-hl-mid">before the</span><br>
          <em>meeting starts.</em>
        </h1>

        <p class="hev-sub hev-reveal">Type a company name. SPARC pulls live public data and runs the full 13-dimension risk model in seconds &mdash; no form required.</p>

        <div class="hev-search-wrap hev-reveal">
          <div class="hev-search-shell">
            <div class="hev-search-inner">
              <svg class="hev-search-icon" width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
                <circle cx="7.5" cy="7.5" r="5" stroke="currentColor" stroke-width="1.5"/>
                <path d="M11.5 11.5L15 15" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <input id="autofill-company-input" class="hev-search-input" type="text"
                placeholder="Search any Indian startup&hellip;" autocomplete="off" spellcheck="false" />
              <button id="autofill-company-btn" class="hev-search-btn" type="button">
                Analyse
                <span class="hev-btn-icon">→</span>
              </button>
            </div>
          </div>
          <div class="hev-try-pills">
            <span class="hev-try-label">Try:</span>
            <button class="hev-try-pill" data-name="Zepto">Zepto</button>
            <button class="hev-try-pill" data-name="Razorpay">Razorpay</button>
            <button class="hev-try-pill" data-name="CRED">CRED</button>
            <button class="hev-try-pill" data-name="Ather Energy">Ather Energy</button>
            <button class="hev-try-pill" data-name="Pristyn Care">Pristyn Care</button>
          </div>
        </div>
      </section>

      <div class="hev-secondary hev-reveal">

        <button class="hev-pipeline-card" type="button" id="pipeline-entry-btn">
          <div class="hev-pipeline-inner">
            <div class="hev-pipeline-left">
              <span class="hev-pipeline-tag">⚡ Pipeline Intelligence</span>
              <h2 class="hev-pipeline-h">Verified startups &mdash;<br>ranked by premium opportunity.</h2>
              <p class="hev-pipeline-d">Know who to call before the meeting starts.</p>
            </div>
            <span class="hev-pipeline-arrow">→</span>
          </div>
        </button>

        <div class="hev-mode-stack">
          <button class="hev-mode-card" type="button" id="customer-role-btn">
            <div class="hev-mode-card-inner">
              <span class="hev-mode-kicker">RM Quick Classify</span>
              <strong class="hev-mode-name">Fast prospect scoring</strong>
              <span class="hev-mode-arrow-r">→</span>
            </div>
          </button>
          <button class="hev-mode-card" type="button" id="underwriter-role-btn">
            <div class="hev-mode-card-inner">
              <span class="hev-mode-kicker">Full SPARC Assessment</span>
              <strong class="hev-mode-name">Deep risk profiling</strong>
              <span class="hev-mode-arrow-r">→</span>
            </div>
          </button>
        </div>

      </div>

      <section class="hev-signal-radar hev-reveal" aria-label="Startup trigger intelligence">
        <div class="hev-signal-head">
          <span class="hev-signal-kicker">Signal Radar &middot; proposed lead engine</span>
          <div>
            <h2>Approach the startup when the risk trigger appears.</h2>
            <p>Monitor credible public signals, update the SPARC profile, score bundle fit, and create an RM-ready approach task after human review.</p>
          </div>
        </div>

        <div class="hev-signal-flow" aria-label="Signal Radar workflow">
          <span>Public signal</span>
          <span>Profile update</span>
          <span>Bundle fit</span>
          <span>RM review</span>
          <span>Approach task</span>
        </div>

        <div class="hev-signal-grid" role="table" aria-label="Startup signal to insurance angle map">
          <div class="hev-signal-row hev-signal-row-head" role="row">
            <span role="columnheader">Signal</span>
            <span role="columnheader">Why it matters</span>
            <span role="columnheader">Likely insurance angle</span>
          </div>
          <div class="hev-signal-row" role="row">
            <span role="cell">Funding round</span>
            <span role="cell">Board, investor, governance risk rises</span>
            <span role="cell">D&amp;O, Key Person, Cyber</span>
          </div>
          <div class="hev-signal-row" role="row">
            <span role="cell">Warehouse / factory</span>
            <span role="cell">Physical asset exposure rises</span>
            <span role="cell">Property, IAR, Fire, CGL</span>
          </div>
          <div class="hev-signal-row" role="row">
            <span role="cell">Drone / robotics expansion</span>
            <span role="cell">Regulatory and third-party liability</span>
            <span role="cell">Drone RPAS, IAR</span>
          </div>
          <div class="hev-signal-row" role="row">
            <span role="cell">Fintech licence / RBI mention</span>
            <span role="cell">Regulated data and operational risk</span>
            <span role="cell">Cyber, PI, D&amp;O, Crime</span>
          </div>
          <div class="hev-signal-row" role="row">
            <span role="cell">Healthcare expansion</span>
            <span role="cell">Patient data and professional liability</span>
            <span role="cell">Cyber, PI, CGL</span>
          </div>
          <div class="hev-signal-row" role="row">
            <span role="cell">Export / import news</span>
            <span role="cell">Transit and credit exposure appears</span>
            <span role="cell">Marine Cargo, Trade Credit</span>
          </div>
          <div class="hev-signal-row" role="row">
            <span role="cell">IPO / pre-IPO news</span>
            <span role="cell">Director liability and scrutiny rise</span>
            <span role="cell">D&amp;O, Crime, Cyber</span>
          </div>
        </div>

        <div class="hev-signal-guardrails">
          <span>Human review before outreach</span>
          <span>Official company email preferred</span>
          <span>Source URL and confidence stored</span>
        </div>
        <button class="hev-signal-open" type="button" id="signal-radar-open">
          Open Signal Radar
        </button>
      </section>

    </main>`;

  const input = $("autofill-company-input");
  const btn   = $("autofill-company-btn");

  const go = () => {
    const name = input.value.trim();
    if (!name) { input.focus(); return; }
    triggerAutoProfiling(name);
  };

  btn.onclick = go;
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") go(); });

  document.querySelectorAll(".hev-try-pill").forEach(pill => {
    pill.onclick = () => {
      input.value = pill.dataset.name;
      triggerAutoProfiling(pill.dataset.name);
    };
  });

  $("pipeline-entry-btn").onclick = () => renderPipelineDashboard();
  $("signal-radar-open").onclick = () => renderSignalRadarDashboard();
  $("customer-role-btn").onclick = () => {
    if (!state.customerProfile?.industry) resetCustomerProfile();
    renderCustomerInput();
  };
  $("underwriter-role-btn").onclick = () => renderForm();

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("hev-visible"); });
  }, { threshold: 0.05 });
  document.querySelectorAll(".hev-reveal").forEach((el, i) => {
    el.style.transitionDelay = `${i * 80}ms`;
    revealObserver.observe(el);
  });
}

// ─── Pipeline Intelligence dashboard ─────────────────────────────────────────

// Signal Radar dashboard
let _signalRadarData = null;
let _signalRadarFilter = "";

function renderSignalRadarLoader() {
  return `
    <div class="signal-loader pipeline-loading" role="status" aria-live="polite">
      <div class="signal-loader-radar" aria-hidden="true">
        <span class="sl-ring sl-ring-1"></span>
        <span class="sl-ring sl-ring-2"></span>
        <span class="sl-ring sl-ring-3"></span>
        <span class="sl-sweep"></span>
        <span class="sl-core"></span>
        <span class="sl-ping sl-ping-1"></span>
        <span class="sl-ping sl-ping-2"></span>
        <span class="sl-ping sl-ping-3"></span>
      </div>
      <div class="signal-loader-copy">
        <div class="sl-kicker">Live public-source scan</div>
        <div class="sl-title">Loading public trigger signals</div>
        <div class="sl-subtitle">Reading startup news, extracting company names, classifying insurable pivots, and mapping each signal to SPARC bundles.</div>
        <div class="sl-pipeline" aria-hidden="true">
          <span style="--i:0">RSS ingest</span>
          <span style="--i:1">Company filter</span>
          <span style="--i:2">Risk trigger</span>
          <span style="--i:3">Bundle match</span>
          <span style="--i:4">RM task</span>
        </div>
      </div>
    </div>`;
}

async function renderSignalRadarDashboard(filter = _signalRadarFilter, forceRefresh = false) {
  state.view = "signals";
  if (!_navCalledByHistory) { _navHistory = _navHistory.slice(0, _navPos + 1); _navHistory.push({ fn: renderSignalRadarDashboard, args: [filter, false], view: "signals" }); _navPos = _navHistory.length - 1; setTimeout(_updateNavButtons, 0); }
  _signalRadarFilter = filter || "";
  const mc = $("main-content");

  mc.innerHTML = `
    <main class="hev-shell">
      <div class="signal-shell">
        <button class="btn btn-ghost pipeline-back-btn" type="button" id="signal-back">&larr; Back</button>
        <section class="signal-hero">
          <span class="signal-eyebrow">Signal Radar</span>
          <h1>Startup triggers converted into RM approach tasks.</h1>
          <p>Public news signals are classified into SPARC profile deltas, bundle fit, premium range, contact-source status, and a human-reviewed next action.</p>
        </section>
        ${renderSignalRadarLoader()}
      </div>
    </main>`;
  $("signal-back").onclick = () => renderRoleSelection();

  const cachedLive = String(_signalRadarData?.source_status || "").startsWith("live_");
  if (!_signalRadarData || forceRefresh || !cachedLive) {
    try {
      const res = await fetch(`/api/signals?limit=30&days=30&t=${Date.now()}`, { cache: "no-store" });
      _signalRadarData = await res.json();
      if (!res.ok || _signalRadarData.error) throw new Error(_signalRadarData.error || "Signal scan failed");
    } catch (e) {
      mc.querySelector(".pipeline-loading").textContent = "Failed to load Signal Radar. Check the server and try again.";
      return;
    }
  }

  const allSignals = _signalRadarData.signals || [];
  const signals = _signalRadarFilter
    ? allSignals.filter(s => s.signal_id === _signalRadarFilter)
    : allSignals;
  const kpis = _signalRadarData.kpis || {};
  const signalTypes = [...new Map(allSignals.map(s => [s.signal_id, s.signal])).entries()];
  const liveMode = String(_signalRadarData.source_status || "").startsWith("live_");
  const sourceLabel = _signalRadarData.source_status === "live_rss"
    ? "Live public news via startup RSS feeds"
    : _signalRadarData.source_status === "live_google_news"
      ? "Live public news via Google News RSS"
      : _signalRadarData.source_status === "live_gdelt"
        ? "Live public news via GDELT"
        : _signalRadarData.source_status === "live_multi"
          ? "Live public news via multiple feeds"
          : "Sample trigger task list";
  const sourceDetail = liveMode
    ? "Showing public articles classified into SPARC-ready triggers."
    : "Live news source did not respond in time; showing a review-ready sample list until refresh succeeds.";

  mc.innerHTML = `
    <main class="hev-shell">
      <div class="signal-shell">
        <div class="signal-topbar">
          <button class="btn btn-ghost pipeline-back-btn" type="button" id="signal-back">&larr; Back</button>
          <button class="signal-refresh" type="button" id="signal-refresh">Refresh scan</button>
        </div>

        <section class="signal-hero">
          <span class="signal-eyebrow">Signal Radar</span>
          <h1>Startup triggers converted into RM approach tasks.</h1>
          <p>Public news signals are classified into SPARC profile deltas, bundle fit, premium range, contact-source status, and a human-reviewed next action.</p>
          <div class="signal-source-note">
            <span>Source mode: ${escHtml(sourceLabel)}</span>
            <span>Window: ${escHtml(_signalRadarData.window_label || "Last 30 days")}</span>
            <span>${escHtml(sourceDetail)}</span>
            <span>${escHtml(_signalRadarData.source_policy || "Human review required before outreach.")}</span>
          </div>
        </section>

        <section class="signal-kpis" aria-label="Signal Radar metrics">
          <div><span>Total signals</span><strong>${kpis.total || allSignals.length}</strong></div>
          <div><span>High confidence</span><strong>${kpis.high_confidence || 0}</strong></div>
          <div><span>Open premium pool</span><strong>INR ${formatCr(kpis.premium_pool_cr || 0)} Cr</strong></div>
          <div><span>Top trigger</span><strong>${escHtml(kpis.top_signal || "—")}</strong></div>
        </section>

        <div class="signal-filter-row">
          <button class="signal-filter ${!_signalRadarFilter ? "active" : ""}" data-signal="">All</button>
          ${signalTypes.map(([id, label]) => `
            <button class="signal-filter ${_signalRadarFilter === id ? "active" : ""}" data-signal="${escHtml(id)}">${escHtml(label)}</button>
          `).join("")}
        </div>

        <section class="signal-task-list">
          ${signals.length ? signals.map(renderSignalTask).join("") : `
            <div class="signal-empty">
              <strong>No signals in this filter.</strong>
              <span>Try another trigger type or refresh the scan.</span>
            </div>
          `}
        </section>
      </div>
    </main>`;

  $("signal-back").onclick = () => renderRoleSelection();
  $("signal-refresh").onclick = () => renderSignalRadarDashboard(_signalRadarFilter, true);
  document.querySelectorAll(".signal-filter").forEach(btn => {
    btn.onclick = () => renderSignalRadarDashboard(btn.dataset.signal || "", false);
  });
  document.querySelectorAll(".signal-analyze-btn").forEach(btn => {
    btn.onclick = () => triggerAutoProfiling(btn.dataset.company);
  });
  document.querySelectorAll(".signal-draft-btn").forEach(btn => {
    btn.onclick = () => {
      let sig;
      try { sig = JSON.parse(btn.dataset.signal); } catch (_) { sig = {}; }
      window.__pendingSignalContext = {
        signal: sig.signal,
        company_name: sig.company,
        insurance_angle: sig.insurance_angle,
        recommended_bundle: sig.recommended_bundle,
        headline: sig.headline,
        regulation_tag: sig.regulation_tag,
        confidence: sig.confidence,
      };
      triggerAutoProfiling(sig.company);
    };
  });
}

function renderSignalTask(signal) {
  const premium = Number(signal.premium_max_lakh || 0) > 0
    ? `INR ${formatLakh(signal.premium_min_lakh)}-${formatLakh(signal.premium_max_lakh)}L`
    : "Needs quote inputs";
  const deltas = (signal.profile_delta || []).slice(0, 5);
  return `
    <article class="signal-task">
      <div class="signal-task-main">
        <div class="signal-task-head">
          <span class="signal-type">${escHtml(signal.signal)}</span>
          ${signal.regulation_tag ? `<span class="signal-reg-badge reg-${escHtml(String(signal.regulation_tag).toLowerCase())}">${escHtml(signal.regulation_tag)}</span>` : ""}
          <span class="signal-confidence ${Number(signal.confidence) < 55 ? "low" : ""}">${escHtml(signal.confidence || "—")}% confidence</span>
        </div>
        <h2>${escHtml(signal.company)}</h2>
        <p>${escHtml(signal.headline)}</p>
        <div class="signal-meta">
          <span>${escHtml(signal.sector || "Sector inferred")}</span>
          <span>${escHtml(signal.funding_stage || "Stage inferred")}</span>
          <span>${escHtml(signal.source || "Public source")}</span>
        </div>
        <dl class="signal-intel">
          <div class="signal-intel-row">
            <dt>Signal Indicator</dt>
            <dd>${escHtml(signal.signal_indicator || signal.signal || "—")}</dd>
          </div>
          <div class="signal-intel-row">
            <dt>Telemetry Source</dt>
            <dd>${escHtml(signal.telemetry_source || "—")}</dd>
          </div>
          <div class="signal-intel-row">
            <dt>Underwriting Rationale &amp; Risk Implication</dt>
            <dd>${escHtml(signal.underwriting_rationale || signal.why_it_matters || "—")}</dd>
          </div>
          <div class="signal-intel-row">
            <dt>Target ICICI Lombard Products</dt>
            <dd>${escHtml(signal.target_products || signal.insurance_angle || "—")}</dd>
          </div>
        </dl>
      </div>
      <div class="signal-task-side">
        <div class="signal-reco">
          <span>Recommended bundle</span>
          <strong>${escHtml(signal.recommended_bundle)}</strong>
        </div>
        <div class="signal-side-grid">
          <div><span>Premium range</span><strong>${premium}</strong></div>
          <div><span>Insurance angle</span><strong>${escHtml(signal.insurance_angle)}</strong></div>
          <div><span>Email source</span><strong>${escHtml(signal.contact_status)}</strong></div>
          <div><span>Review status</span><strong>${escHtml(signal.review_status)}</strong></div>
        </div>
        <div class="signal-deltas">
          ${deltas.map(d => `<span>${escHtml(String(d).replace(/_/g, " "))}</span>`).join("")}
        </div>
        <p class="signal-action">${escHtml(signal.rm_action)}</p>
        <div class="signal-actions">
          ${signal.source_url ? `<a href="${escHtml(signal.source_url)}" target="_blank" rel="noopener">Open source</a>` : ""}
          <button class="signal-draft-btn" type="button" data-signal='${JSON.stringify({company:signal.company,sector:signal.sector,funding_stage:signal.funding_stage,signal:signal.signal,insurance_angle:signal.insurance_angle,underwriting_rationale:signal.underwriting_rationale,recommended_bundle:signal.recommended_bundle,headline:signal.headline,regulation_tag:signal.regulation_tag,confidence:signal.confidence}).replace(/'/g,"&#39;")}'>Draft outreach</button>
          <button class="signal-analyze-btn" type="button" data-company="${escHtml(signal.company)}">Run SPARC</button>
        </div>
      </div>
    </article>`;
}

let _pipelineData = null; // cache so we don't re-fetch on filter change
let _pipelineView = "table"; // "table" | "heat"
let _pipelineSort = { key: "premium", dir: "desc" }; // active sort state

const PIPELINE_SORT_KEYS = {
  rank:    (a, b) => (b.max_lakh || 0) - (a.max_lakh || 0),
  company: (a, b) => a.startup_name.localeCompare(b.startup_name),
  sector:  (a, b) => (a.sector || "").localeCompare(b.sector || ""),
  stage:   (a, b) => {
    const o = { "Pre-seed": 0, "Seed": 1, "Series A": 2, "Series B+": 3 };
    return (o[a.funding_stage] ?? 9) - (o[b.funding_stage] ?? 9);
  },
  premium: (a, b) => (b.max_lakh || 0) - (a.max_lakh || 0),
  score:   (a, b) => (b.overall_score || 0) - (a.overall_score || 0),
};

async function renderPipelineDashboard(sectorFilter = "", stageFilter = "", tapFilter = "untapped") {
  state.view = "pipeline";
  if (!_navCalledByHistory) { _navHistory = _navHistory.slice(0, _navPos + 1); _navHistory.push({ fn: renderPipelineDashboard, args: [sectorFilter, stageFilter, tapFilter], view: "pipeline" }); _navPos = _navHistory.length - 1; setTimeout(_updateNavButtons, 0); }
  const mc = $("main-content");

  // Loading skeleton
  mc.innerHTML = `
    <main class="hev-shell">
      <div class="pipeline-shell">
        <div class="pipeline-brief">
          <button class="btn btn-ghost pipeline-back-btn" type="button" id="pipeline-back">&larr; Back</button>
          <div class="pipeline-brief-copy">
            <span class="pipeline-eyebrow">RM call sheet</span>
            <h1 class="pipeline-title">Pipeline Intelligence</h1>
            <p class="pipeline-subtitle">Loading verified startup profiles and premium opportunity scores.</p>
          </div>
        </div>
        <div class="pipeline-loading">Loading pipeline data&hellip;</div>
      </div>
    </main>`;
  $("pipeline-back").onclick = () => renderRoleSelection();

  // Fetch (use cache after first load)
  if (!_pipelineData) {
    try {
      const res = await fetch("/api/pipeline?limit=500");
      _pipelineData = await res.json();
    } catch (e) {
      mc.querySelector(".pipeline-loading").textContent = "Failed to load pipeline. Is the server running?";
      return;
    }
  }

  // Apply filters client-side from cache
  const allCompanies = _pipelineData.companies || [];
  let companies = allCompanies;
  if (sectorFilter) companies = companies.filter(c => c.sector.toLowerCase().includes(sectorFilter.toLowerCase()));
  if (stageFilter)  companies = companies.filter(c => c.funding_stage.toLowerCase() === stageFilter.toLowerCase());
  if (tapFilter)    companies = companies.filter(c => c.tap_status === tapFilter);

  // Apply column sort (persisted in _pipelineSort)
  const sortFn = PIPELINE_SORT_KEYS[_pipelineSort.key] || PIPELINE_SORT_KEYS.premium;
  companies = [...companies].sort((a, b) => _pipelineSort.dir === "asc" ? sortFn(b, a) : sortFn(a, b));

  const kpis = _pipelineData.kpis || {};
  const totalPoolCr = Math.round(companies.reduce((s, c) => s + (c.max_lakh || 0), 0) / 100);
  const untappedPoolCr = Math.round(companies.filter(c => c.tap_status !== "covered").reduce((s,c) => s + (c.max_lakh||0), 0) / 100);
  const untappedCount = companies.filter(c => c.tap_status !== "covered").length;

  const sectors = companies.map(c => c.sector).filter(Boolean);
  const topSector = sectors.length ? [...sectors].sort((a, b) => sectors.filter(x=>x===b).length - sectors.filter(x=>x===a).length)[0] : "";
  const avgScore = companies.length ? (companies.reduce((s,c) => s + (c.overall_score||0), 0) / companies.length).toFixed(1) : "—";
  const stageCounts = allCompanies.reduce((acc, c) => {
    const stage = c.funding_stage || "Unknown";
    acc[stage] = (acc[stage] || 0) + 1;
    return acc;
  }, {});
  const activeCut = tapFilter
    ? ({ preseed: "Uninsured — Pre-seed accounts", untapped: "First buyer — Seed accounts", strike_now: "Strike now — Series A", covered: "Renewal target — Series B+" }[tapFilter] || "Filtered")
    : "All market stages";

  // Sector options
  const allSectors = [...new Set((_pipelineData.companies||[]).map(c => c.sector).filter(Boolean))].sort();
  const allStages = [...new Set((_pipelineData.companies||[]).map(c => c.funding_stage).filter(Boolean))].sort();

  mc.innerHTML = `
    <main class="hev-shell">
    <div class="pipeline-shell">
      <section class="pipeline-brief">
        <button class="btn btn-ghost pipeline-back-btn" type="button" id="pipeline-back">&larr; Back</button>
        <div class="pipeline-brief-copy">
          <span class="pipeline-eyebrow">RM call sheet</span>
          <h1 class="pipeline-title">Pipeline Intelligence</h1>
          <p class="pipeline-subtitle">Verified Indian startup profiles ranked by estimated premium, stage urgency, and sector concentration. Use it to pick the next founder call, not to browse a raw database.</p>
          <div class="pipeline-stage-strip" aria-label="Stage mix">
            <span>Pre-seed <strong>${stageCounts["Pre-seed"] || 0}</strong></span>
            <span>Seed <strong>${stageCounts.Seed || 0}</strong></span>
            <span>Series A <strong>${stageCounts["Series A"] || 0}</strong></span>
            <span>Series B+ <strong>${stageCounts["Series B+"] || 0}</strong></span>
          </div>
        </div>
        <div class="pipeline-brief-aside">
          <span>Current cut</span>
          <strong>${escHtml(activeCut)}</strong>
          <small>${companies.length} accounts visible from ${allCompanies.length} verified rows</small>
        </div>
      </section>

      <div class="pipeline-kpis">
        <div class="pipeline-kpi pipeline-kpi-accent">
          <span class="kpi-label">Open premium</span>
          <span class="kpi-val">INR ${kpis.untapped_pool_cr || untappedPoolCr} Cr</span>
          <span class="kpi-note">Pre-seed, Seed, and Series A opportunity in this cut.</span>
        </div>
        <div class="pipeline-kpi">
          <span class="kpi-label">Early-stage accounts</span>
          <span class="kpi-val">${kpis.untapped_count || untappedCount}</span>
          <span class="kpi-note">Not yet treated as mature covered-market accounts.</span>
        </div>
        <div class="pipeline-kpi">
          <span class="kpi-label">Premium pool</span>
          <span class="kpi-val">INR ${totalPoolCr} Cr</span>
          <span class="kpi-note">Sum of upper-bound indicative premium ranges.</span>
        </div>
        <div class="pipeline-kpi">
          <span class="kpi-label">Dominant sector</span>
          <span class="kpi-val">${topSector || "—"}</span>
          <span class="kpi-note">Average risk score: ${avgScore}</span>
        </div>
      </div>

      <div class="pipeline-filters pipeline-filters-sticky">
        <div class="pipeline-view-toggle">
          <button class="pvt-btn ${_pipelineView === "table" ? "pvt-active" : ""}" id="pvt-table">Table</button>
          <button class="pvt-btn ${_pipelineView === "heat" ? "pvt-active" : ""}" id="pvt-heat">Heat map</button>
        </div>
        <div class="pipeline-filter-divider"></div>
        <button class="btn pipeline-tap-btn tap-all ${!tapFilter ? "active" : ""}" data-tap="">All</button>
        <button class="btn pipeline-tap-btn tap-preseed ${tapFilter === "preseed" ? "active" : ""}" data-tap="preseed">🔍 Uninsured</button>
        <button class="btn pipeline-tap-btn tap-untapped ${tapFilter === "untapped" ? "active" : ""}" data-tap="untapped">🌱 First buyer</button>
        <button class="btn pipeline-tap-btn tap-strike ${tapFilter === "strike_now" ? "active" : ""}" data-tap="strike_now">⚡ Strike now</button>
        <div class="pipeline-filters-right">
          <select id="pipeline-sector-filter" class="pipeline-select">
            <option value="">All sectors</option>
            ${allSectors.map(s => `<option value="${s}" ${s === sectorFilter ? "selected" : ""}>${s}</option>`).join("")}
          </select>
          <select id="pipeline-stage-filter" class="pipeline-select">
            <option value="">All stages</option>
            ${allStages.map(s => `<option value="${s}" ${s === stageFilter ? "selected" : ""}>${s}</option>`).join("")}
          </select>
          <span class="pipeline-count">${companies.length} accounts</span>
        </div>
      </div>

      ${_pipelineView === "heat" ? renderSectorHeat(companies) : `
      <div class="pipeline-table-wrap">
        <table class="pipeline-table">
          <caption>Ranked opportunity list. Click a row to open the company risk profile.</caption>
          <thead>
            <tr>
              ${[
                ["#",                   "rank"],
                ["Company",             "company"],
                ["Sector",              "sector"],
                ["Stage",               "stage"],
                ["Market Status",       null],
                ["Recommended Bundle",  null],
                ["Est. Premium",        "premium"],
                ["Risk Score",          "score"],
              ].map(([label, key]) => {
                if (!key) return `<th>${label}</th>`;
                const active = _pipelineSort.key === key;
                const arrow = active ? (_pipelineSort.dir === "desc" ? " ↓" : " ↑") : " ⇅";
                return `<th class="pipeline-th-sort${active ? " sort-active" : ""}" data-sort-key="${key}">${label}<span class="sort-arrow">${arrow}</span></th>`;
              }).join("")}
            </tr>
          </thead>
          <tbody>
            ${companies.map((c, i) => `
              <tr class="pipeline-row tap-row-${c.tap_status || "covered"}" data-name="${escHtml(c.startup_name)}">
                <td class="pipeline-rank">${i + 1}</td>
                <td class="pipeline-company">
                  <strong>${escHtml(c.startup_name)}</strong>
                  <span>${escHtml(c.top_risk || "Risk profile ready")}</span>
                </td>
                <td class="pipeline-sector">${escHtml(c.sector)}</td>
                <td><span class="pipeline-stage">${escHtml(c.funding_stage)}</span></td>
                <td>${tapBadge(c.tap_status)}</td>
                <td class="pipeline-bundle">${escHtml(c.bundle_name || "—")}</td>
                <td class="pipeline-premium">${c.max_lakh ? `INR ${formatLakh(c.min_lakh)}-${formatLakh(c.max_lakh)}L` : "—"}</td>
                <td><span class="pipeline-score score-${scoreClass(c.overall_score)}">${c.overall_score || "—"}</span></td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>`}
    </div>
    </main>`;

  $("pipeline-back").onclick = () => renderRoleSelection();
  $("pvt-table").onclick = () => { _pipelineView = "table"; renderPipelineDashboard(sectorFilter, stageFilter, tapFilter); };
  $("pvt-heat").onclick  = () => { _pipelineView = "heat";  renderPipelineDashboard(sectorFilter, stageFilter, tapFilter); };
  $("pipeline-sector-filter").onchange = e => renderPipelineDashboard(e.target.value, $("pipeline-stage-filter").value, tapFilter);
  $("pipeline-stage-filter").onchange  = e => renderPipelineDashboard($("pipeline-sector-filter").value, e.target.value, tapFilter);
  mc.querySelectorAll(".pipeline-tap-btn").forEach(btn => {
    btn.onclick = () => renderPipelineDashboard(
      $("pipeline-sector-filter").value,
      $("pipeline-stage-filter").value,
      btn.dataset.tap
    );
  });

  // Column sort headers
  mc.querySelectorAll(".pipeline-th-sort").forEach(th => {
    th.onclick = () => {
      const key = th.dataset.sortKey;
      if (_pipelineSort.key === key) {
        _pipelineSort.dir = _pipelineSort.dir === "desc" ? "asc" : "desc";
      } else {
        _pipelineSort.key = key;
        _pipelineSort.dir = "desc";
      }
      renderPipelineDashboard(sectorFilter, stageFilter, tapFilter);
    };
  });

  if (_pipelineView === "table") {
    mc.querySelectorAll(".pipeline-row").forEach(row => {
      row.onclick = () => triggerAutoProfiling(row.dataset.name);
    });
  } else {
    // Heat view: clicking a sector row filters the table
    mc.querySelectorAll(".heat-row[data-sector]").forEach(row => {
      row.onclick = () => { _pipelineView = "table"; renderPipelineDashboard(row.dataset.sector, "", ""); };
    });
  }
}

function renderSectorHeat(allCompanies) {
  // Group by sector
  const map = {};
  for (const c of allCompanies) {
    const s = c.sector || "Unknown";
    if (!map[s]) map[s] = { total: 0, untapped: 0, untapped_lakh: 0, total_lakh: 0, risk_sum: 0 };
    map[s].total++;
    map[s].total_lakh += c.max_lakh || 0;
    map[s].risk_sum += c.overall_score || 0;
    if (c.tap_status === "preseed" || c.tap_status === "untapped" || c.tap_status === "strike_now") {
      map[s].untapped++;
      map[s].untapped_lakh += c.max_lakh || 0;
    }
  }

  const rows = Object.entries(map)
    .map(([sector, d]) => ({
      sector,
      ...d,
      untapped_cr: Math.round(d.untapped_lakh / 100 * 10) / 10,
      total_cr: Math.round(d.total_lakh / 100 * 10) / 10,
      pct_untapped: Math.round(d.untapped / d.total * 100),
      avg_risk: Math.round(d.risk_sum / d.total),
    }))
    .sort((a, b) => b.untapped_lakh - a.untapped_lakh);

  const maxLakh = Math.max(...rows.map(r => r.untapped_lakh), 1);

  return `
    <div class="heat-wrap">
      <div class="heat-legend">
        <span class="heat-leg-item"><span class="heat-bar-demo heat-bar-untapped"></span> Uninsured (Seed)</span>
        <span class="heat-leg-item"><span class="heat-bar-demo heat-bar-strike"></span> Strike Now (Series A)</span>
        <span class="heat-leg-item text-muted">Click any row to filter the table</span>
      </div>
      ${rows.map(r => {
        const barW = Math.round(r.untapped_lakh / maxLakh * 100);
        const seedLakh = allCompanies.filter(c => c.sector === r.sector && c.tap_status === "untapped").reduce((s,c) => s+(c.max_lakh||0), 0);
        const strikeLakh = allCompanies.filter(c => c.sector === r.sector && c.tap_status === "strike_now").reduce((s,c) => s+(c.max_lakh||0), 0);
        const seedW = r.untapped_lakh > 0 ? Math.round(seedLakh / r.untapped_lakh * barW) : 0;
        const strikeW = barW - seedW;
        return `
        <div class="heat-row" data-sector="${escHtml(r.sector)}">
          <div class="heat-sector">${escHtml(r.sector)}</div>
          <div class="heat-bar-wrap">
            <div class="heat-bar-track">
              <div class="heat-bar-fill heat-bar-untapped" style="width:${seedW}%"></div><div class="heat-bar-fill heat-bar-strike" style="width:${strikeW}%"></div>
            </div>
            <span class="heat-bar-label">₹${r.untapped_cr} Cr untapped</span>
          </div>
          <div class="heat-stats">
            <span class="heat-stat-main">${r.untapped} / ${r.total}</span>
            <span class="heat-stat-sub">uninsured</span>
          </div>
          <div class="heat-stats">
            <span class="heat-stat-main">${r.pct_untapped}%</span>
            <span class="heat-stat-sub">untapped</span>
          </div>
          <div class="heat-stats">
            <span class="heat-stat-main heat-risk-${r.avg_risk >= 70 ? "high" : r.avg_risk >= 45 ? "med" : "low"}">${r.avg_risk}</span>
            <span class="heat-stat-sub">avg risk</span>
          </div>
        </div>`;
      }).join("")}
    </div>`;
}

function tapBadge(tap) {
  if (tap === "preseed")    return `<span class="badge badge-preseed">🔍 Uninsured</span>`;
  if (tap === "untapped")   return `<span class="badge badge-untapped">🌱 First buyer</span>`;
  if (tap === "strike_now") return `<span class="badge badge-strike">⚡ Strike now</span>`;
  return `<span class="badge badge-covered">🔄 Renewal target</span>`;
}

function scoreClass(s) {
  if (!s) return "na";
  if (s >= 75) return "high";
  if (s >= 45) return "med";
  return "low";
}

function formatLakh(value) {
  const n = Number(value || 0);
  if (!Number.isFinite(n)) return "0";
  return Number.isInteger(n) ? String(n) : n.toFixed(1).replace(/\.0$/, "");
}

function formatCr(value) {
  const n = Number(value || 0);
  if (!Number.isFinite(n)) return "0";
  return Number.isInteger(n) ? String(n) : n.toFixed(1).replace(/\.0$/, "");
}

function escHtml(str) {
  return String(str || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ─────────────────────────────────────────────────────────────────────────────

function renderCustomerInput() {
  state.view = "customer";
  if (!_navCalledByHistory) { _navHistory = _navHistory.slice(0, _navPos + 1); _navHistory.push({ fn: renderCustomerInput, args: [], view: "customer" }); _navPos = _navHistory.length - 1; setTimeout(_updateNavButtons, 0); }
  const meta = state.meta;
  const p = state.customerProfile;
  const sectors = (meta.sectors || []).map(s => s.name);
  const handleOptions = [
    ["customer_data", "Customer data"],
    ["payments", "Online payments"],
    ["contracts", "B2B contracts"],
    ["employees", "Employees"],
    ["physical_ops", "Office, stock, or equipment"],
  ];

  $("main-content").innerHTML = `
    <main class="customer-shell">
      <section class="customer-form-panel">
        <button class="link-button" type="button" id="customer-back-role">Back to role selection</button>
        <div class="customer-head">
          <div class="intake-eyebrow">Customer input</div>
          <h1>Get a startup insurance recommendation in under two minutes</h1>
          <p>Answer a few business-friendly questions. We will translate them into the SPARC risk model and keep the output concise.</p>
        </div>

        <div class="customer-grid">
          <div class="field-group">
            <label>Business name</label>
            <input class="f-input" type="text" value="${esc(p.business_name)}" placeholder="e.g. BrightPay" data-customer-key="business_name" />
          </div>
          <div class="field-group">
            <label>Industry</label>
            <select class="f-select" data-customer-key="industry">
              ${sectors.map(v => `<option ${p.industry===v?"selected":""}>${esc(v)}</option>`).join("")}
            </select>
          </div>
          <div class="field-group">
            <label>Annual revenue range</label>
            <select class="f-select" data-customer-key="revenue_range">
              ${["Pre-revenue","Below INR 1 Cr","INR 1-5 Cr","INR 5-25 Cr","INR 25 Cr+"].map(v => `<option ${p.revenue_range===v?"selected":""}>${esc(v)}</option>`).join("")}
            </select>
          </div>
          <div class="field-group">
            <label>Team size</label>
            <select class="f-select" data-customer-key="team_range">
              ${["1-10","11-50","51-200","200+"].map(v => `<option ${p.team_range===v?"selected":""}>${esc(v)}</option>`).join("")}
            </select>
          </div>
          <div class="field-group">
            <label>Funding status</label>
            <select class="f-select" data-customer-key="funding_status">
              ${(meta.fundingStages || ["Pre-seed","Seed","Series A","Series B+"]).map(v => `<option ${p.funding_status===v?"selected":""}>${esc(v)}</option>`).join("")}
            </select>
          </div>
        </div>

        <div class="field-group">
          <label>Main concern right now</label>
          <div class="customer-choice-row" id="customer-concerns">
            ${["Customer contracts","Data breach","Investor or board risk","Employee benefits","Product or service claims","Property or equipment loss"].map(v => `
              <button class="customer-chip ${p.main_concern===v?"active":""}" type="button" data-concern="${esc(v)}">${esc(v)}</button>`).join("")}
          </div>
        </div>

        <div class="field-group">
          <label>What applies to your business?</label>
          <div class="customer-check-grid">
            ${handleOptions.map(([key, label]) => `
              <label class="customer-check">
                <input type="checkbox" value="${key}" ${(p.handles || []).includes(key) ? "checked" : ""} />
                <span>${esc(label)}</span>
              </label>`).join("")}
          </div>
        </div>

        <div class="customer-actions">
          <button class="btn btn-ghost" type="button" id="customer-reset-btn">Reset</button>
          <button class="btn btn-primary btn-lg" type="button" id="customer-submit-btn">Show my recommendation</button>
        </div>
      </section>

      <aside class="customer-side">
        <div class="customer-side-card">
          <div class="sidebar-card-label">What you will see</div>
          <div class="info-list">
            <div class="info-row"><div class="info-dot"></div><span>Best-fit bundle for your stage</span></div>
            <div class="info-row"><div class="info-dot"></div><span>Top 3 products to discuss first</span></div>
            <div class="info-row"><div class="info-dot"></div><span>Baseline cover to start with</span></div>
            <div class="info-row"><div class="info-dot"></div><span>Plain-language RM nudge</span></div>
          </div>
        </div>
      </aside>
    </main>`;

  bindCustomerInput();
}

function bindCustomerInput() {
  $("customer-back-role").onclick = () => renderRoleSelection();
  $("customer-reset-btn").onclick = () => {
    resetCustomerProfile();
    renderCustomerInput();
  };
  document.querySelectorAll("[data-customer-key]").forEach(el => {
    const update = () => { state.customerProfile[el.dataset.customerKey] = el.value; };
    el.addEventListener("input", update);
    el.addEventListener("change", update);
  });
  document.querySelectorAll("[data-concern]").forEach(btn => {
    btn.addEventListener("click", () => {
      state.customerProfile.main_concern = btn.dataset.concern;
      document.querySelectorAll("[data-concern]").forEach(x => x.classList.toggle("active", x === btn));
    });
  });
  document.querySelectorAll(".customer-check input").forEach(el => {
    el.addEventListener("change", () => {
      state.customerProfile.handles = [...document.querySelectorAll(".customer-check input:checked")].map(x => x.value);
    });
  });
  $("customer-submit-btn").onclick = () => runCustomerAnalysis();
}

function teamRangeToNumber(range) {
  return TEAM_MAP[range] || 25;
}

function mapCustomerToUnderwritingProfile(customer) {
  const handles = new Set(customer.handles || []);
  const profile = structuredClone(state.meta.defaults);
  profile.startup_name = customer.business_name?.trim() || "Your startup";
  profile.sector = customer.industry || profile.sector;
  profile.funding_stage = customer.funding_status || profile.funding_stage;
  profile.team_size = TEAM_MAP[customer.team_range] ?? 25;
  profile.annual_revenue_cr = REVENUE_MAP[customer.revenue_range] ?? 3;
  profile.product_description = `Industry: ${customer.industry || profile.sector}. Main concern: ${customer.main_concern}. Revenue range: ${customer.revenue_range}.`;
  profile.has_investors = ["Seed", "Series A", "Series B+"].includes(profile.funding_stage) ? "Yes" : "No";
  profile.customer_type = handles.has("contracts") ? ["B2B Enterprise"] : ["B2C Consumers"];
  profile.operations = handles.has("physical_ops") ? "Hybrid" : "Digital-only";
  profile.data_sensitivity = handles.has("payments") || handles.has("customer_data") ? "High" : "Medium";
  profile.data_handled = [];
  profile.regulatory = [];
  profile.physical_assets = [];

  if (handles.has("customer_data")) {
    profile.data_handled.push("Customer behavioural / usage data");
    profile.regulatory.push("DPDP Act obligations");
  }
  if (handles.has("payments")) {
    profile.data_handled.push("Payments / financial transactions");
    profile.regulatory.push("IT Act / CERT-In obligations");
  }
  if (handles.has("employees")) {
    profile.data_handled.push("Employee / HR data (payroll, biometrics)");
  }
  if (handles.has("physical_ops")) {
    profile.physical_assets.push("Office / coworking space");
  }
  if (customer.main_concern === "Data breach" && !profile.regulatory.includes("IT Act / CERT-In obligations")) {
    profile.regulatory.push("IT Act / CERT-In obligations");
  }
  if (customer.main_concern === "Employee benefits" && !handles.has("employees")) {
    profile.data_handled.push("Employee / HR data (payroll, biometrics)");
  }

  profile.biggest_fear = customer.main_concern || "";
  profile.b2b_pct = handles.has("contracts") ? 0.75 : 0.25;
  return buildProfile(profile);
}

async function runCustomerAnalysis() {
  renderCustomerLoading();
  const mappedProfile = mapCustomerToUnderwritingProfile(state.customerProfile);
  state.quoteInputs = {};
  state.quoteSuggestionsPreFilled = false;
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(mappedProfile),
    });
    const result = await res.json();
    if (!res.ok || result.error) throw new Error(result.error || "Analysis failed");
    renderCustomerResults(result);
  } catch (err) {
    $("main-content").innerHTML = `
      <div style="padding:100px 40px;max-width:640px;margin:0 auto;">
        <div class="error-box">${esc(err.message)}</div>
        <button class="btn btn-ghost" style="margin-top:16px;" onclick="renderCustomerInput()">Back to customer inputs</button>
      </div>`;
  }
}

function renderCustomerLoading() {
  $("main-content").innerHTML = `
    <div class="loading-screen customer-loading">
      <div class="loading-ring"></div>
      <div class="loading-text">Building your recommendation</div>
      <div class="loading-sub">Translating your profile into a simple bundle and product shortlist.</div>
    </div>`;
}

function getBaselineProduct(result) {
  const recs = result.recommendations || [];
  return recs.find(p => p.mandatory) || recs.find(p => p.priority === "Critical") || recs[0] || null;
}

function getWhyText(why, key, section, fallback = "") {
  if (!key) return fallback || "";
  const primary = section ? why?.[section] : why;
  const candidates = canonicalCoverCandidates(key);
  if (primary && typeof primary === "object") {
    for (const candidate of candidates) {
      const value = primary[candidate];
      if (typeof value === "string" && value.trim()) return value.trim();
    }
  }
  if (why && !section) {
    for (const candidate of candidates) {
      const value = why[candidate];
      if (typeof value === "string" && value.trim()) return value.trim();
    }
  }
  return fallback || "";
}

function getProductWhy(product, why) {
  if (!product) return "";
  return getWhyText(
    why,
    product.key,
    "products",
    getWhyText(why, product.key, null, product.nudge || PRODUCT_BLURBS[product.key] || "")
  );
}

function getCoverWhy(key, why, section = "bundle_covers") {
  const fallback = canonicalCoverCandidates(key)
    .map(candidate => PRODUCT_BLURBS[candidate])
    .find(Boolean) || "";
  return getWhyText(
    why,
    key,
    section,
    fallback
  );
}

function customerProductReason(product, result = {}) {
  if (!product) return "";
  return getProductWhy(product, result.why_it_matters) || "Relevant for the risks most likely to affect your business at this stage.";
}

function customerExplanation(result) {
  const p = result.profile || {};
  const topRisk = (result.top_risks || [])[0]?.name?.replace(" Risk", "").toLowerCase() || "business continuity";
  const bundle = result.bundle_match?.name || "the recommended bundle";
  return result.why_it_matters?.bundle || `For a ${p.funding_stage || "growing"} ${p.sector || "startup"} with about ${p.team_size || "your current"} people, ${bundle} is the clearest starting point. It prioritises ${topRisk} and keeps the first discussion focused on covers that protect contracts, data, people, and day-to-day operations.`;
}

function customerNudge(result) {
  const p = result.profile || {};
  if ((p.customer_type || []).includes("B2B Enterprise")) {
    return "This is commonly selected by businesses at your stage before signing larger customer contracts.";
  }
  if ((p.data_handled || []).length) {
    return "Founders with similar data exposure often review this cover early to avoid expensive surprises after a breach or customer complaint.";
  }
  return "Teams at this stage often start with baseline protection now, then expand the cover as revenue and operations scale.";
}

function renderCustomerResults(result) {
  result = normalizeGroupSafeguardCompanion(result);
  const p = result.profile || {};
  const bundle = result.bundle_match || {};
  const why = result.why_it_matters || {};
  const topProducts = (result.recommendations || []).slice(0, 3);
  const baseline = getBaselineProduct(result);
  const companion = bundle.companion_bundle || {};
  const companionCovers = [
    ...(companion.mandatory_covers || []),
    ...(companion.optional_covers || []),
  ];

  $("main-content").innerHTML = `
    <main class="customer-results">
      <section class="customer-results-hero">
        <button class="link-button light" type="button" onclick="renderCustomerInput()">Edit customer inputs</button>
        <div class="customer-results-top">
          <div>
            <div class="customer-results-kicker">Your startup shield recommendation</div>
            <h1>${esc(bundle.name || "Recommended startup protection")}</h1>
            <p>${esc(customerExplanation(result))}</p>
          </div>
          <div class="customer-fit">
            <strong>${bundle.fit_pct || Math.round(100 - Math.min(70, result.overall || 0) / 2)}%</strong>
            <span>profile fit</span>
          </div>
        </div>
      </section>

      <section class="customer-result-grid">
        <article class="customer-result-card customer-bundle-card">
          <div class="card-label">Recommended bundle</div>
          <h2>${esc(bundle.name || "Bundle recommendation")}</h2>
          <p>${esc(bundle.description || "A practical set of covers matched to your current business profile.")}</p>
          ${why.bundle ? `<p class="customer-bundle-why">${esc(why.bundle)}</p>` : ""}
          ${bundle.companion_bundle?.name ? `
            <div class="customer-companion-bundle">
              <div class="card-label">Also review</div>
              <h3>${esc(bundle.companion_bundle.name)}</h3>
              <p>${esc(why.companion_bundle || bundle.companion_note || "This second package covers the startup's sector-specific risks alongside workforce protection.")}</p>
              ${companionCovers.length ? `
                <div class="customer-cover-list">
                  ${companionCovers.slice(0, 6).map(c => `
                    <div class="customer-cover-item">
                      <strong>${esc(labelize(c))}</strong>
                      <span>${esc(getCoverWhy(c, why, "companion_covers"))}</span>
                    </div>`).join("")}
                </div>` : ""}
            </div>` : ""}
          ${result.bundle_only_pricing_quote?.gross_premium_lakh ? `<div class="customer-price">Indicative bundle premium: INR ${esc(result.bundle_only_pricing_quote.gross_premium_lakh)}L incl. GST</div>` : ""}
        </article>

        <article class="customer-result-card">
          <div class="card-label">Baseline product</div>
          ${baseline ? `
            <h2>${esc(baseline.name || labelize(baseline.key))}</h2>
            <p>${esc(customerProductReason(baseline, result))}</p>
          ` : `<p>No baseline product was returned for this profile.</p>`}
        </article>
      </section>

      <section class="customer-products-section">
        <div class="result-section-head">
          <div class="result-section-bar"></div>
          <div class="result-section-title">Top 3 products to discuss first</div>
        </div>
        <div class="customer-product-grid">
          ${topProducts.map((product, i) => `
            <article class="customer-product-card">
              <div class="customer-product-rank">#${i + 1}</div>
              <h3>${esc(product.name || labelize(product.key))}</h3>
              <p>${esc(customerProductReason(product, result))}</p>
              <div class="customer-product-tags">
                <span>${esc(product.priority || "Recommended")}</span>
                ${product.mandatory ? "<span>Baseline</span>" : ""}
              </div>
            </article>`).join("") || `<div class="r-card">${emptyState("i", "No products returned", "Try changing the customer profile inputs.")}</div>`}
        </div>
      </section>

      <section class="customer-rm-banner">
        <div>
          <div class="customer-rm-label">Next best action</div>
          <h2>Send to customer</h2>
          <p>${esc(customerNudge(result))}</p>
        </div>
        <button class="btn btn-primary btn-lg" type="button" id="email-draft-btn">Draft outreach email</button>
      </section>

      <div class="customer-result-actions">
        <button class="btn btn-ghost" type="button" onclick="renderRoleSelection()">Back to role selection</button>
        <button class="btn btn-ghost" type="button" onclick="renderForm()">Open underwriter view</button>
      </div>
    </main>`;

  state.profile = structuredClone(p);
  window.__customerResult = result;

  const emailBtn = $("email-draft-btn");
  if (emailBtn) emailBtn.onclick = () => showEmailDraftModal(result);
}

function buildEmailDraft(result) {
  const p = result.profile || {};
  const company   = p.startup_name || "your company";
  const sector    = p.sector || "your sector";
  const stage     = p.funding_stage || "this stage";
  const team      = p.team_size ? `${p.team_size}-person team` : "your team";
  const bundle    = result.bundle_match?.name || "the recommended bundle";
  const risks     = (result.top_risks || []).slice(0, 2).map(r => r.name.replace(" Risk", "")).join(" and ") || "your top risk areas";
  const bullets   = (result.pitch_bullets || []).filter(Boolean);

  const subject = `Insurance cover recommendation for ${company} — ${bundle}`;

  const bulletLines = bullets.length
    ? bullets.map(b => `  • ${b}`).join("\n")
    : `  • ${bundle} directly maps to your highest-risk exposure areas: ${risks}.`;

  const body =
`Hi [Founder name],

Following our conversation about ${company}, I ran a quick profile through our startup risk tool.

Based on your stage (${stage}), sector (${sector}), and ${team}, the strongest fit is ${bundle}.

Here is why this matters for ${company}:

${bulletLines}

Your top risk areas — ${risks} — are directly addressed by this bundle's mandatory covers.

I would be happy to walk you through the specifics and get an indicative quote across in 24 hours. When works for a quick call this week?

Warm regards,
[Your name]
ICICI Lombard`;

  return { subject, body };
}

function showEmailDraftModal(result) {
  const { subject, body } = buildEmailDraft(result);

  const overlay = document.createElement("div");
  overlay.className = "email-modal-overlay";
  overlay.innerHTML = `
    <div class="email-modal">
      <div class="email-modal-head">
        <span class="email-modal-kicker">Outreach email draft</span>
        <button class="email-modal-close" id="email-modal-close" aria-label="Close">&times;</button>
      </div>
      <div class="email-modal-field">
        <label class="email-modal-label">Subject</label>
        <div class="email-subject-line">${esc(subject)}</div>
      </div>
      <div class="email-modal-field">
        <label class="email-modal-label">Body</label>
        <textarea class="email-body-area" id="email-body-area" spellcheck="true">${esc(body)}</textarea>
      </div>
      <div class="email-modal-actions">
        <button class="btn btn-primary" id="email-gmail-btn">Open in Gmail</button>
        <button class="btn btn-ghost" id="email-modal-dismiss">Close</button>
      </div>
    </div>`;

  document.body.appendChild(overlay);

  const close = () => document.body.removeChild(overlay);
  document.getElementById("email-modal-close").onclick  = close;
  document.getElementById("email-modal-dismiss").onclick = close;
  overlay.addEventListener("click", e => { if (e.target === overlay) close(); });

  document.getElementById("email-gmail-btn").onclick = () => {
    const ta = document.getElementById("email-body-area");
    const gmailUrl = "https://mail.google.com/mail/?view=cm&fs=1"
      + "&su=" + encodeURIComponent(subject)
      + "&body=" + encodeURIComponent(ta.value);
    window.open(gmailUrl, "_blank");
  };
}

function renderForm() {
  state.view = "underwriter";
  if (!_navCalledByHistory) { _navHistory = _navHistory.slice(0, _navPos + 1); _navHistory.push({ fn: renderForm, args: [], view: "underwriter" }); _navPos = _navHistory.length - 1; setTimeout(_updateNavButtons, 0); }
  state.section = Math.min(SECTIONS.length - 1, Math.max(0, state.section || 0));
  state.maxVisitedSection = Math.max(state.maxVisitedSection || 0, state.section);
  const mc = $("main-content");
  mc.innerHTML = `
    <div class="intake-shell">
      <aside class="step-sidebar">
        <div class="step-sidebar-title">Assessment steps</div>
        <div class="step-sidebar-sub">Jump between visited sections.</div>
        <nav class="step-list" id="section-sidebar"></nav>
      </aside>

      <main class="intake-main">
        <div class="intake-hero">
          <div class="intake-eyebrow">Risk Analysis</div>
          <h1>Tell us about<br/>your startup</h1>
          <p>We'll map your risk exposure across 13 categories and recommend the exact insurance covers you need.</p>
          ${renderProfileImportPanel()}
        </div>

        <div class="progress-row" id="progress-row"></div>

        <div id="form-sections">
          ${renderSectionIdentity()}
          ${renderSectionShape()}
          ${renderSectionExposure()}
          ${renderSectionAdvanced()}
        </div>

        <div class="intake-nav">
          <button class="btn btn-ghost" id="back-btn" type="button" disabled>← Back</button>
          <div class="nav-spacer"></div>
          <button class="btn btn-primary btn-lg" id="next-btn" type="button">Continue →</button>
        </div>
      </main>

      <aside class="intake-sidebar">
        <div class="sidebar-card">
          <div class="sidebar-card-label">Your profile so far</div>
          <div id="profile-summary"></div>
        </div>
        <div class="sidebar-card section-score-card">
          <div class="sidebar-card-label">Section score preview</div>
          <div id="section-score-preview"></div>
        </div>
        <div class="sidebar-card">
          <div class="sidebar-card-label">We'll calculate</div>
          <div class="info-list">
            ${[
              "Risk score across 13 categories",
              "Overall exposure rating out of 100",
              "Personalised ICICI Lombard products",
              "Premium cost estimates",
              "Non-insurance mitigation actions",
            ].map(t=>`<div class="info-row"><div class="info-dot"></div><span>${t}</span></div>`).join("")}
          </div>
        </div>
      </aside>
    </div>`;

  bindForm();
  updateProgress();
  showSection(state.section, { noScroll: true });
  updateProfileSummary();
  updateSectionScorePreview();
}

/* ── Section 0: Identity ──────────────────────────────────── */
function renderSectionIdentity() {
  const meta = state.meta;
  const sectors = meta.sectors.map(s=>s.name);
  const p = state.profile;

  const sectorCards = sectors.map(s => `
    <button class="choice-card ${p.sector===s?"active":""}" type="button" data-key="sector" data-value="${esc(s)}" onclick="chooseCard(this,'sector',false)">
      <div class="cc-icon">${SECTOR_ICONS[s]||"✦"}</div>
      <div class="cc-label">${esc(s)}</div>
    </button>`).join("");

  const stageCards = meta.fundingStages.map(s => `
    <button class="choice-card ${p.funding_stage===s?"active":""}" type="button" data-key="funding_stage" data-value="${esc(s)}" onclick="chooseCard(this,'funding_stage',false)">
      <div class="cc-icon">${FUNDING_ICONS[s]||"●"}</div>
      <div class="cc-label">${esc(s)}</div>
    </button>`).join("");

  return `
    <div class="form-section" id="section-identity">
      ${sectionHeader(0, "Identity", "identity")}
      <div class="section-label">01 — Identity</div>

      <div class="field-group">
        <label>Startup name</label>
        <input class="f-input" id="f-name" type="text" placeholder="e.g. Acme Labs" value="${esc(p.startup_name||"")}" oninput="setVal('startup_name',this.value)" />
      </div>

      <div class="field-group">
        <label>Founder / contact email</label>
        <input class="f-input" id="f-email" type="email" placeholder="e.g. founder@acmelabs.com" value="${esc(p.contact_email||"")}" oninput="setVal('contact_email',this.value)" />
      </div>

      <div class="field-group">
        <label>Sector</label>
        <div class="card-grid">${sectorCards}</div>
      </div>

      <div class="field-group">
        <label>Funding stage</label>
        <div class="card-grid">${stageCards}</div>
      </div>

      <div class="field-row">
        <div class="field-group">
          <label>Team size (full-time)</label>
          <div class="range-wrap">
            <input type="range" min="0" max="500" step="1"
              value="${p.team_size ?? 20}"
              oninput="setVal('team_size',Number(this.value)); this.nextElementSibling.textContent=this.value" />
            <div class="range-bubble">${p.team_size ?? 20}</div>
          </div>
        </div>
        <div class="field-group">
          <label>Institutional investors?</label>
          <div class="pill-grid">
            ${["Yes","No"].map(v=>`<button class="pill ${p.has_investors===v?"active":""}" type="button" data-key="has_investors" data-value="${esc(v)}" onclick="chooseVal('has_investors','${v}',false)">${v}</button>`).join("")}
          </div>
        </div>
      </div>
    </div>`;
}

/* ── Section 1: Shape ─────────────────────────────────────── */
function renderSectionShape() {
  const meta = state.meta;
  const p = state.profile;
  const tailoring = getTailoring();

  const opsCards = meta.operations.map(s => `
    <button class="choice-card ${p.operations===s?"active":""}" type="button" data-key="operations" data-value="${esc(s)}" onclick="chooseCard(this,'operations',false)">
      <div class="cc-icon">${OPS_ICONS[s]||"●"}</div>
      <div class="cc-label">${esc(s)}</div>
    </button>`).join("");

  const sensitivityPills = meta.dataSensitivity.map(v=>`
    <button class="pill ${p.data_sensitivity===v?"active":""}" type="button" data-key="data_sensitivity" data-value="${esc(v)}" onclick="chooseVal('data_sensitivity','${v}',false)">${v}</button>`).join("");

  const custPills = meta.customerTypeOptions.map(v=>`
    <button class="pill ${(p.customer_type||[]).includes(v)?"active":""}" type="button" data-key="customer_type" data-value="${esc(v)}" onclick="chooseVal('customer_type','${esc(v)}',true)">${esc(v)}</button>`).join("");

  const mkShapeNumber = (key, label, help) => `
    <div class="field-group">
      <label>${esc(label)}</label>
      <input class="f-input" type="number" min="0" step="0.1" value="${esc(p[key] ?? 0)}" oninput="setVal('${key}',Number(this.value||0))" />
      <small>${esc(help)}</small>
    </div>`;

  const aiTierInline = tailoring?.key === "deeptech" && p.ai_in_product ? `
    <div class="branch-subfield">
      <label>AI Tier</label>
      <select class="f-select" onchange="setVal('ai_tier',this.value||'None')">
        ${(meta.aiTiers || ["None","Applied","Autonomous","Frontier"]).map(o=>`<option value="${esc(o)}" ${p.ai_tier===o?"selected":""}>${esc(o)}</option>`).join("")}
      </select>
      <small>Relevant to Deeptech ↑</small>
    </div>` : "";

  return `
    <div class="form-section" id="section-shape">
      ${sectionHeader(1, "Shape", "shape")}
      <div class="section-label">02 — Shape</div>

      <div class="field-group">
        <label>Operating model</label>
        <div class="card-grid">${opsCards}</div>
      </div>

      <div class="field-row">
        <div class="field-group">
          <label>Data sensitivity</label>
          <div class="pill-grid">${sensitivityPills}</div>
        </div>
        <div class="field-group">
          <label>AI / ML in core product?</label>
          <div class="pill-grid">
            ${["No","Yes"].map(v=>`<button class="pill ${(p.ai_in_product?(v==="Yes"):(v==="No"))?"active":""}" type="button" data-key="ai_toggle" data-value="${v}" onclick="setAI('${v}')">${v}</button>`).join("")}
          </div>
          ${aiTierInline}
        </div>
      </div>

      <div class="field-group">
        <label>Customers <span style="font-weight:400;color:var(--ink-faint)">(select all that apply)</span></label>
        <div class="pill-grid">${custPills}</div>
      </div>

      <div class="field-row">
        ${mkShapeNumber("annual_revenue_cr", "Annual revenue / ARR (INR Cr)", "Used for premium sizing. Enter 0 to skip.")}
        ${mkShapeNumber("total_insurable_asset_value_cr", "Total insurable asset value (INR Cr)", "Used for premium sizing. Enter 0 to skip.")}
      </div>

      <div class="field-group">
        <label>What does your product do? <span style="font-weight:400;color:var(--ink-faint)">(optional)</span></label>
        <textarea class="f-textarea" placeholder="e.g. We build a UPI payment gateway for SMBs…" oninput="setVal('product_description',this.value)">${esc(p.product_description||"")}</textarea>
        <small>This is shown to your RM and does not affect the score.</small>
      </div>
    </div>`;
}

/* ── Section 2: Exposure ──────────────────────────────────── */
function pillItem(item) {
  if (typeof item === "string") return { label: item, value: item, relevant: false };
  return {
    label: item.label || item.value || "",
    value: item.value || item.label || "",
    relevant: !!item.relevant,
  };
}

function removeValuesFromGroups(groups, values) {
  const banned = new Set(values);
  return groups.map(group => ({
    ...group,
    items: (group.items || []).filter(item => !banned.has(pillItem(item).value)),
  })).filter(group => group.rule || group.heading || group.items.length);
}

function mkPillsGrouped(groups, profileKey) {
  return groups.map(({heading, items, rule}) => [
    rule ? `<span class="pill-divider-rule"></span>` : "",
    heading ? `<span class="pill-divider">${esc(heading)}</span>` : "",
    ...(items || []).map(item => {
      const pItem = pillItem(item);
      const active = (state.profile[profileKey] || []).includes(pItem.value);
      const cls = `pill ${active ? "active" : ""} ${pItem.relevant ? "relevant" : ""}`.trim();
      return `<button class="${cls}" type="button" data-key="${profileKey}" data-value="${esc(pItem.value)}" onclick="chooseVal('${profileKey}','${esc(pItem.value)}',true)">${esc(pItem.label)}</button>`;
    })
  ].join("")).join("");
}

function renderSectionExposure() {
  const tailoring = getTailoring();
  let dataGroups = [
    { heading: "Personal & financial",
      items: ["Payments / financial transactions", "Personal identity data (KYC / Aadhaar)", "Health / medical records", "Minors' / children's data", "Sensitive personal data (DPDP Act)"] },
    { heading: "Business & IP",
      items: ["Employee / HR data (payroll, biometrics)", "Intellectual property / source code", "Customer behavioural / usage data"] },
    { heading: "Operational",
      items: ["Location / GPS tracking data", "Physical inventory / goods"] },
    { rule: true, heading: "",
      items: ["None of the above"] },
  ];

  let regGroups = [
    { heading: "Financial & data",
      items: ["RBI / SEBI / IRDAI licensed", "DPDP Act obligations", "IT Act / CERT-In obligations"] },
    { heading: "Health & life sciences",
      items: ["FSSAI / food safety", "CDSCO / medical devices", "NMC / telemedicine regulations"] },
    { heading: "Operations & transport",
      items: ["DGCA / drone operations", "MV Act / transport regulations", "Labour Codes / gig worker regulations"] },
    { heading: "Product & environment",
      items: ["BIS / QCO product certification", "EPR / environmental compliance", "SEBI BRSR / ESG reporting", "Competition Act / CCI"] },
    { rule: true, heading: "",
      items: ["None / minimal"] },
  ];

  let assetGroups = [
    { heading: "Premises & retail",
      items: ["Office / coworking space", "Warehouse / fulfilment centre", "Retail stores / kiosks"] },
    { heading: "Production & lab",
      items: ["Manufacturing plant / factory", "Lab / R&D equipment", "Kitchen / food processing", "Cold chain / refrigeration"] },
    { heading: "Specialist equipment",
      items: ["Medical devices / diagnostic equipment", "Drones / UAV equipment", "Solar / clean energy infrastructure"] },
    { heading: "Transport & tech",
      items: ["Vehicles / delivery fleet", "Data centre / server room"] },
    { rule: true, heading: "",
      items: ["None - fully cloud"] },
  ];

  if (tailoring?.key === "fintech") {
    regGroups = [
      {
        heading: "Relevant to Fintech ↑",
        items: [
          { label: "RBI / NBFC licensing", value: "RBI / SEBI / IRDAI licensed", relevant: true },
          { label: "SEBI regulations", value: "RBI / SEBI / IRDAI licensed", relevant: true },
        ],
      },
      ...removeValuesFromGroups(regGroups, ["RBI / SEBI / IRDAI licensed"]),
    ];
  } else if (tailoring?.key === "healthtech") {
    dataGroups = [
      {
        heading: "Relevant to Healthtech ↑",
        items: [
          { label: "Health / medical records", value: "Health / medical records", relevant: true },
          { label: "Biometric data", value: "Employee / HR data (payroll, biometrics)", relevant: true },
        ],
      },
      ...removeValuesFromGroups(dataGroups, ["Health / medical records", "Employee / HR data (payroll, biometrics)"]),
    ];
    regGroups = [
      {
        heading: "Most relevant to Healthtech ↑",
        items: [{ label: "DPDP Act obligations", value: "DPDP Act obligations", relevant: true }],
      },
      ...removeValuesFromGroups(regGroups, ["DPDP Act obligations"]),
    ];
  } else if (tailoring?.key === "d2c") {
    dataGroups = [
      {
        heading: "Relevant to D2C ↑",
        items: [{ label: "Customer behavioural / usage data", value: "Customer behavioural / usage data", relevant: true }],
      },
      ...removeValuesFromGroups(dataGroups, ["Customer behavioural / usage data"]),
    ];
  } else if (tailoring?.key === "logistics") {
    assetGroups = [
      {
        heading: "Relevant to Logistics ↑",
        items: [{ label: "Fleet / vehicles", value: "Vehicles / delivery fleet", relevant: true }],
      },
      ...removeValuesFromGroups(assetGroups, ["Vehicles / delivery fleet"]),
    ];
  }

  const p = state.profile;
  return `
    <div class="form-section" id="section-exposure">
      ${sectionHeader(2, "Exposure", "exposure")}
      <div class="section-label">03 — Exposure</div>

      <div class="field-group">
        <label>Sensitive data you handle <span style="font-weight:400;color:var(--ink-faint)">(select all)</span></label>
        <div class="pill-grid">${mkPillsGrouped(dataGroups, "data_handled")}</div>
      </div>

      <div class="field-group">
        <label>Regulatory exposure <span style="font-weight:400;color:var(--ink-faint)">(select all)</span></label>
        <div class="pill-grid">${mkPillsGrouped(regGroups, "regulatory")}</div>
      </div>

      <div class="field-group">
        <label>Physical assets <span style="font-weight:400;color:var(--ink-faint)">(select all)</span></label>
        <div class="pill-grid">${mkPillsGrouped(assetGroups, "physical_assets")}</div>
      </div>

      <div class="field-group">
        <label>Biggest risk concern <span style="font-weight:400;color:var(--ink-faint)">(optional)</span></label>
        <textarea class="f-textarea" placeholder="e.g. A data breach that damages customer trust…" oninput="setVal('biggest_fear',this.value)">${esc(p.biggest_fear||"")}</textarea>
        <small>This is shown to your RM and does not affect the score.</small>
      </div>
    </div>`;
}

/* ── Section 3: Advanced ──────────────────────────────────── */
function renderSectionAdvanced() {
  const meta = state.meta;
  const p = state.profile;
  const tailoring = getTailoring();

  const mkSlider = (key, label, min, max, step, decimals=2) => {
    const val = Number(p[key] ?? 0);
    return `
      <div class="adv-slider-row">
        <span class="adv-slider-label">${label}</span>
        <input type="range" class="adv-range" min="${min}" max="${max}" step="${step}" value="${val}"
          oninput="setVal('${key}',Number(this.value)); this.nextElementSibling.textContent=Number(this.value).toFixed(${decimals})" />
        <span class="adv-slider-val">${val.toFixed(decimals)}</span>
      </div>`;
  };

  const mkNumber = (key, label, step=1, min=0, help="") => {
    const val = p[key] ?? "";
    return `
      <div class="adv-number-item">
        <label class="adv-select-label">${label}</label>
        <input class="f-input adv-number-input" type="number" min="${min}" step="${step}" value="${esc(val)}"
          oninput="setVal('${key}',Number(this.value||0))" />
        ${help ? `<div class="adv-help">${esc(help)}</div>` : ""}
      </div>`;
  };

  const mkSelect = (key, label, opts, nullLabel="") => {
    const cur = p[key];
    return `
      <div class="adv-select-item">
        <label class="adv-select-label">${label}</label>
        <select class="f-select" style="height:38px;font-size:13px;" onchange="setVal('${key}',this.value||null)">
          ${nullLabel?`<option value="">${esc(nullLabel)}</option>`:""}
          ${opts.map(o=>`<option value="${esc(o)}" ${cur===o?"selected":""}>${esc(o)}</option>`).join("")}
        </select>
      </div>`;
  };

  const mkCheck = (key, label) => `
    <label class="adv-check">
      <input type="checkbox" id="chk-${key}" ${p[key]?"checked":""} onchange="setVal('${key}',this.checked)" />
      <span>${label}</span>
    </label>`;

  const sdfCheck = mkCheck("sdf_likely", "DPDP Act §10 Significant Data Fiduciary designation likely");

  const selectedStates = Array.isArray(p.state_footprint) ? p.state_footprint : (p.state_footprint ? [p.state_footprint] : []);
  const statePills = meta.states.map(s=>`
    <button class="pill ${selectedStates.includes(s)?"active":""}" type="button" data-key="state_footprint" data-value="${esc(s)}" onclick="chooseVal('state_footprint','${esc(s)}',false)">${esc(s)}</button>`).join("");

  const rbiProminent = tailoring?.key === "fintech" ? `
    <div class="branch-panel">
      <div class="branch-label">Relevant to Fintech ↑</div>
      ${mkSelect("rbi_registration","RBI registration",meta.rbiRegistrations,"None")}
    </div>` : "";
  const governanceSelects = tailoring?.key === "fintech"
    ? `${mkSelect("holdco_domicile","Holdco domicile",meta.holdcoDomiciles)}`
    : `${mkSelect("holdco_domicile","Holdco domicile",meta.holdcoDomiciles)}${mkSelect("rbi_registration","RBI registration",meta.rbiRegistrations,"None")}`;

  const gigWorkforce = tailoring?.key === "logistics" ? `
    <div class="branch-panel">
      <div class="branch-label">Relevant to Logistics ↑</div>
      ${mkSlider("gig_headcount_pct","Gig / contractor workforce %",0,1,.01)}
      <p class="branch-note">Typically 40–80% for logistics startups</p>
    </div>` : mkSlider("gig_headcount_pct","Gig / contractor workforce %",0,1,.01);

  const dataAiTop = tailoring?.key === "deeptech" ? `
    <div class="branch-panel">
      <div class="branch-label">Relevant to Deeptech ↑</div>
      <div class="branch-mixed-grid">
        ${mkSelect("ai_tier","AI tier",meta.aiTiers)}
        ${sdfCheck}
      </div>
    </div>` : "";
  const dataAiSliders = `${mkSlider("hardware_software_split","Hardware revenue share",0,1,.01)}`;
  const dataAiSelects = tailoring?.key === "deeptech"
    ? `${mkSelect("data_localisation_status","Data localisation",["Unknown","Full_onshore","Hybrid","Offshore"])}`
    : `${mkSelect("data_localisation_status","Data localisation",["Unknown","Full_onshore","Hybrid","Offshore"])}${mkSelect("ai_tier","AI tier",meta.aiTiers)}`;

  const internationalExposure = tailoring?.key === "d2c" ? `
    <div class="branch-panel">
      <div class="branch-label">International exposure</div>
      <div class="branch-slider-grid">
        ${mkSlider("export_eu_pct","EU revenue",0,1,.01)}
        ${mkSlider("export_us_pct","US revenue",0,1,.01)}
        ${mkSlider("export_china_pct","China revenue",0,1,.01)}
      </div>
    </div>` : "";
  const marketSliders = tailoring?.key === "d2c"
    ? `${mkSlider("b2b_pct","B2B revenue",0,1,.01)}${mkSlider("chinese_supplier_pct_cogs","Chinese supplier COGS",0,1,.01)}`
    : `${mkSlider("b2b_pct","B2B revenue",0,1,.01)}${mkSlider("export_eu_pct","EU revenue",0,1,.01)}${mkSlider("export_us_pct","US revenue",0,1,.01)}${mkSlider("export_china_pct","China revenue",0,1,.01)}${mkSlider("chinese_supplier_pct_cogs","Chinese supplier COGS",0,1,.01)}`;

  return `
    <div class="form-section" id="section-advanced">
      ${sectionHeader(3, "Advanced", "advanced", ` <span style="font-weight:500;color:var(--ink-faint);text-transform:none;letter-spacing:0;">(optional)</span>`)}
      <div class="section-label">04 — Advanced <span style="font-weight:500;color:var(--ink-faint);text-transform:none;letter-spacing:0;">(optional)</span></div>

      <div class="adv-group">
        <div class="adv-group-title">Governance &amp; capital</div>
        ${rbiProminent}
        <div class="adv-sliders">
          ${mkSlider("investor_cn_hk_pct","China / HK investor BO",0,1,.01)}
          ${mkSlider("cumulative_fundraising_inr_cr","Total fundraising (INR Cr)",0,10000,10,0)}
          ${mkSlider("founder_equity_pct","Founder equity %",0,1,.01)}
        </div>
        <div class="adv-selects">
          ${governanceSelects}
        </div>
        <div class="adv-checks">
          ${mkCheck("dpiit_recognition","DPIIT recognised startup")}
          ${mkCheck("has_independent_directors","Has independent board directors")}
        </div>
      </div>

      <div class="adv-group">
        <div class="adv-group-title">Commercial sizing for pricing</div>
        <div class="adv-number-grid">
          ${mkNumber("gross_profit_cr","Gross profit / BI basis",0.1,0,"INR Cr")}
          ${mkNumber("claims_last_3_years","Claims last 3 years",1,0,"Count of prior insurance claims")}
        </div>
      </div>

      <div class="adv-group">
        <div class="adv-group-title">Workforce &amp; gig risk</div>
        <div class="adv-sliders">
          ${gigWorkforce}
        </div>
        <div class="adv-checks">
          ${mkCheck("posh_ic_constituted","POSH IC constituted")}
          ${mkCheck("cert_in_poc_designated","CERT-In POC designated")}
        </div>
        <div class="adv-state-wrap">
          <div class="adv-state-label">State footprint <span style="font-weight:400;color:var(--ink-faint)">(primary state drives geo loading)</span></div>
          <div class="pill-grid">${statePills}</div>
        </div>
      </div>

      <div class="adv-group">
        <div class="adv-group-title">Data &amp; AI</div>
        ${dataAiTop}
        <div class="adv-sliders">
          ${dataAiSliders}
        </div>
        <div class="adv-selects">
          ${dataAiSelects}
        </div>
        ${tailoring?.key === "deeptech" ? "" : `<div class="adv-checks">${sdfCheck}</div>`}
      </div>

      <div class="adv-group">
        <div class="adv-group-title">Market &amp; supply chain</div>
        ${internationalExposure}
        <div class="adv-sliders">
          ${marketSliders}
        </div>
        <div class="adv-checks">${mkCheck("listed_customer_brsr_dependency","Listed customers require BRSR")}</div>
      </div>

      <div class="adv-group">
        <div class="adv-group-title">Physical &amp; environmental</div>
        <div class="adv-selects" style="max-width:360px;">
          ${mkSelect("facility_climate_risk_zone","Facility climate risk zone",meta.climateZones)}
        </div>
        <div class="adv-number-grid">
          ${mkNumber("fleet_count","Owned/operated fleet count",1,0,"Vehicles")}
          ${mkNumber("project_value_cr","Project / contract value",0.1,0,"INR Cr")}
        </div>
        <div class="adv-checks">
          ${mkCheck("healthcare_operations","Healthcare/clinical operations")}
          ${mkCheck("payment_or_card_program","Payment/card programme")}
          ${mkCheck("product_recall_exposure","Product recall exposure")}
          ${mkCheck("food_or_pharma_manufacturing","Food/pharma manufacturing")}
          ${mkCheck("contract_bid_or_performance_bond_need","Bid/performance bond need")}
          ${mkCheck("event_or_production_operations","Event/production operations")}
        </div>
      </div>
    </div>`;
}

/* ─── FORM BIND / INTERACTIONS ──────────────────────────────── */
function bindForm() {
  $("back-btn").onclick = () => {
    if (state.section > 0) { showSection(state.section - 1); }
  };
  $("next-btn").onclick = () => {
    if (state.section < SECTIONS.length - 1) {
      showSection(state.section + 1);
    } else {
      runAnalysis();
    }
  };
}

function showSection(idx, opts = {}) {
  const nextIdx = Math.min(SECTIONS.length - 1, Math.max(0, idx));
  state.section = nextIdx;
  state.maxVisitedSection = Math.max(state.maxVisitedSection || 0, nextIdx);
  saveDraftProfile();
  document.querySelectorAll(".form-section").forEach(el => el.classList.remove("visible"));
  const el = $(SECTION_IDS[nextIdx]);
  if (el) el.classList.add("visible");

  $("back-btn").disabled = nextIdx === 0;
  $("next-btn").textContent = nextIdx === SECTIONS.length - 1 ? "Analyse my startup →" : "Continue →";
  $("next-btn").classList.toggle("analyse-ready", nextIdx === SECTIONS.length - 1);
  updateProgress();
  updateProfileSummary();
  updateSectionScorePreview();
  if (!opts.noScroll) window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateProgress() {
  const row = $("progress-row");
  const sidebar = $("section-sidebar");
  const renderStep = (s, i, compact = false) => {
    const count = sectionCount(s.id);
    const done = i < state.maxVisitedSection;
    const active = i === state.section;
    const locked = i > state.maxVisitedSection;
    const cls = `${done ? "done" : ""} ${active ? "active" : ""} ${locked ? "locked" : ""}`.trim();
    const completed = done ? `<span class="step-complete">completed ✓ · ${count.filled}/${count.total}</span>` : `<span class="step-count">${count.filled}/${count.total}</span>`;
    const disabled = locked ? "disabled" : "";
    return `
      <button class="${compact ? "progress-step" : "sidebar-step"} ${cls}" type="button" ${disabled} onclick="jumpToSection(${i})">
        <span class="step-icon">${esc(s.icon)}</span>
        <span class="step-text">
          <strong>${esc(s.label)}</strong>
          ${compact ? `<em>${count.filled}/${count.total}</em>` : completed}
        </span>
      </button>`;
  };
  if (row) {
    row.innerHTML = SECTIONS.map((s, i) => {
      const line = i < SECTIONS.length - 1 ? `<div class="progress-line"></div>` : "";
      return renderStep(s, i, true) + line;
    }).join("");
  }
  if (sidebar) {
    sidebar.innerHTML = SECTIONS.map((s, i) => renderStep(s, i)).join("");
  }
}

window.jumpToSection = (idx) => {
  if (idx <= state.maxVisitedSection) showSection(idx);
};

function refreshAdaptiveSections() {
  const holder = $("form-sections");
  if (!holder) return;
  holder.innerHTML = `
    ${renderSectionIdentity()}
    ${renderSectionShape()}
    ${renderSectionExposure()}
    ${renderSectionAdvanced()}`;
  showSection(state.section, { noScroll: true });
}

// Global helpers called from onclick attributes
window.setVal = (key, val) => {
  state.profile[key] = val;
  if (key === "ai_tier") state.profile.ai_in_product = val !== "None";
  afterProfileChange({ refreshAdaptive: key === "ai_tier" && getTailoring()?.key === "deeptech" });
};

window.setAI = (v) => {
  state.profile.ai_in_product = v === "Yes";
  state.profile.ai_tier = v === "Yes" ? "Applied" : "None";
  document.querySelectorAll(`.pill[data-key="ai_toggle"]`).forEach(btn => {
    btn.classList.toggle("active", btn.dataset.value === v);
  });
  afterProfileChange({ refreshAdaptive: getTailoring()?.key === "deeptech" });
};

window.chooseCard = (el, key, multi) => {
  const val = el.dataset.value;
  if (!multi) {
    document.querySelectorAll(`.choice-card[data-key="${key}"]`).forEach(b => b.classList.remove("active"));
    el.classList.add("active");
    state.profile[key] = val;
    if (key === "sector") state.profile.sub_sector = null;
  } else {
    el.classList.toggle("active");
    const cur = new Set(state.profile[key] || []);
    cur.has(val) ? cur.delete(val) : cur.add(val);
    state.profile[key] = [...cur];
  }
  afterProfileChange({ refreshAdaptive: key === "sector" });
};

window.chooseVal = (key, val, multi) => {
  if (!multi) {
    state.profile[key] = val;
    document.querySelectorAll(`.pill[data-key="${key}"]`).forEach(b => {
      b.classList.toggle("active", b.dataset.value === val);
    });
  } else {
    const cur = new Set(state.profile[key] || []);
    cur.has(val) ? cur.delete(val) : cur.add(val);
    state.profile[key] = [...cur];
    document.querySelectorAll(`.pill[data-key="${key}"]`).forEach(b => {
      b.classList.toggle("active", cur.has(b.dataset.value));
    });
  }
  afterProfileChange();
};

function updateProfileSummary() {
  const el = $("profile-summary");
  if (!el) return;
  const p = state.profile;
  const items = [
    ["Name",       p.startup_name || "—"],
    ["Sector",     p.sector       || "—"],
    ["Stage",      p.funding_stage|| "—"],
    ["Team",       p.team_size ? `${p.team_size} FTEs` : "—"],
    ["Model",      p.operations   || "—"],
    ["Customers",  (p.customer_type||[]).join(", ") || "—"],
  ];
  el.innerHTML = items.map(([k,v]) => `
    <div class="profile-item">
      <span class="profile-item-key">${k}</span>
      <span class="profile-item-val">${esc(String(v))}</span>
    </div>`).join("");
}

function riskTone(level) {
  if (level >= 3) return "red";
  if (level >= 2) return "amber";
  return "green";
}

function operationalRiskPreview() {
  const p = state.profile;
  const operations = API_OPERATION_MAP[p.operations] || p.operations;
  const dataSensitivity = p.data_sensitivity === "Very High" ? "High" : p.data_sensitivity;
  let level = 1;
  if (dataSensitivity === "High") level += 1;
  if (["Hybrid", "Physical-only"].includes(operations)) level += 1;
  if (p.operations === "Marketplace") level += 1;
  return { tone: riskTone(level), label: level >= 3 ? "High" : level === 2 ? "Medium" : "Low" };
}

function exposureRiskPreview() {
  const p = state.profile;
  let level = 1;
  const sensitive = new Set(["Payments / financial transactions", "Health / medical records", "Personal identity data (KYC / Aadhaar)", "Sensitive personal data (DPDP Act)"]);
  if ((p.data_handled || []).some(v => sensitive.has(v))) level += 1;
  if ((p.regulatory || []).filter(v => !String(v).includes("None")).length >= 2) level += 1;
  if ((p.physical_assets || []).filter(v => !String(v).includes("None")).length >= 2) level += 1;
  return { tone: riskTone(level), label: level >= 3 ? "High" : level === 2 ? "Medium" : "Low" };
}

function updateSectionScorePreview() {
  const el = $("section-score-preview");
  if (!el) return;
  const p = state.profile;
  const items = [];
  if (state.maxVisitedSection > 0) {
    items.push(`
      <div class="score-preview-row locked">
        <span>Profile</span>
        <strong>${esc(p.sector || "Startup")} · ${esc(p.funding_stage || "Stage")} · ${esc(p.team_size || "—")} people</strong>
      </div>`);
  }
  if (state.maxVisitedSection > 1) {
    const op = operationalRiskPreview();
    items.push(`
      <div class="score-preview-row locked">
        <span>Operational Risk</span>
        <strong class="risk-pill ${op.tone}">${op.label}</strong>
      </div>`);
  }
  if (state.maxVisitedSection > 2) {
    const exposure = exposureRiskPreview();
    items.push(`
      <div class="score-preview-row locked">
        <span>Exposure Risk</span>
        <strong class="risk-pill ${exposure.tone}">${exposure.label}</strong>
      </div>`);
  }
  if (state.maxVisitedSection >= 3) {
    items.push(`
      <div class="score-preview-ready">
        <strong>Full risk profile ready</strong>
        <span>Analyse is ready when you are.</span>
      </div>`);
  }
  el.innerHTML = items.length ? items.join("") : `<p class="score-preview-empty">Complete Identity to lock the first preview.</p>`;
}

/* ─── ANALYSIS ───────────────────────────────────────────────── */
async function runAnalysis() {
  renderLoading();
  state.quoteInputs = {};
  state.quoteSuggestionsPreFilled = false;
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildProfile()),
    });
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("json")) throw new Error("no-backend");
    const result = await res.json();
    if (!res.ok || result.error) throw new Error(result.error || "Analysis failed");
    renderResults(result);
  } catch (err) {
    // Fall back to demo response when no backend is connected
    try {
      const demoRes = await fetch("./demo-response.json");
      const demo = await demoRes.json();
      // Patch the demo profile with what the user actually entered
      if (state.profile.startup_name) demo.profile.startup_name = state.profile.startup_name;
      if (state.profile.sector) demo.profile.sector = state.profile.sector;
      if (state.profile.funding_stage) demo.profile.funding_stage = state.profile.funding_stage;
      if (state.profile.team_size) demo.profile.team_size = state.profile.team_size;
      if (state.profile.operations) demo.profile.operations = state.profile.operations;
      renderResults(demo);
    } catch {
      $("main-content").innerHTML = `
        <div style="padding:80px 40px;padding-top:100px;max-width:600px;margin:0 auto;">
          <div class="error-box">${esc(err.message)}</div>
          <button class="btn btn-ghost" style="margin-top:16px;" onclick="renderForm()">← Edit inputs</button>
        </div>`;
    }
  }
}

function renderLoading() {
  $("main-content").innerHTML = `
    <div class="loading-screen">
      <div class="loading-ring"></div>
      <div class="loading-text">Analysing your startup</div>
      <div class="loading-sub">Running 13 risk models against your profile</div>
      <div class="loading-steps">
        <div class="loading-step"><div class="loading-step-dot"></div>Scoring digital &amp; data exposure…</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Mapping regulatory triggers…</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Matching ICICI Lombard products…</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Estimating premium ranges…</div>
      </div>
    </div>`;
}

/* ─── RESULTS RENDER ─────────────────────────────────────────── */
function normalizeGroupSafeguardCompanion(result) {
  const bundle = result?.bundle_match;
  if (!bundle || bundle.name !== "Group Safeguard Insurance Policy") return result;
  if (bundle.companion_bundle?.name) return result;

  const alternatives = Array.isArray(result.bundle_alternatives) ? [...result.bundle_alternatives] : [];
  if (!alternatives.length) return result;

  const companion = { ...alternatives.shift(), alternative_status: "companion" };
  result.bundle_match = {
    ...bundle,
    companion_bundle: companion,
    companion_note: (
      "Group Safeguard is strongest for workforce benefits, but it is not sector-specific. " +
      "Review this second package alongside it for the startup's operating and sector risks."
    ),
  };
  result.bundle_alternatives = alternatives;
  result.recommended_bundle_set = [result.bundle_match, companion];
  return result;
}

function setupScrollReveal() {
  // Stagger siblings within each grid
  document.querySelectorAll(".cs-grid, .products-grid, .products-list").forEach(grid => {
    [...grid.children].forEach((card, i) => {
      card.style.transitionDelay = `${i * 75}ms`;
    });
  });

  const SCRAMBLE_AMOUNTS = ["₹1–4 Cr","₹8–24 Cr","₹5–18 Cr","₹2–9 Cr","₹11–30 Cr","₹4–15 Cr","₹6–22 Cr","₹3–10 Cr"];

  function scrambleExposure(card) {
    const el = card.querySelector(".cs-exposure-val");
    if (!el || el.dataset.scrambled) return;
    el.dataset.scrambled = "1";
    const realText = el.textContent;
    let n = 0;
    const iv = setInterval(() => {
      el.textContent = SCRAMBLE_AMOUNTS[n % SCRAMBLE_AMOUNTS.length];
      el.classList.add("ev-scrambling");
      n++;
      if (n >= 9) {
        clearInterval(iv);
        el.textContent = realText;
        el.classList.remove("ev-scrambling");
        el.classList.add("ev-settled");
        setTimeout(() => el.classList.remove("ev-settled"), 700);
      }
    }, 65);
  }

  function animateScore(card) {
    const el = card.querySelector(".product-tag.score");
    if (!el || el.dataset.animated) return;
    el.dataset.animated = "1";
    const m = el.textContent.match(/^([\d.]+)(\/[\d.]+.*)/);
    if (!m) return;
    const target = parseFloat(m[1]), rest = m[2];
    const t0 = performance.now(), dur = 700;
    const tick = now => {
      const p = Math.min((now - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = `${Math.round(eased * target)}${rest}`;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      el.classList.add("scroll-revealed");
      observer.unobserve(el);
      // Trigger number effects after card settles
      const delay = parseFloat(el.style.transitionDelay || "0") * 1000 + 350;
      setTimeout(() => {
        if (el.classList.contains("cs-card"))      scrambleExposure(el);
        if (el.classList.contains("product-card")) animateScore(el);
      }, delay);
    });
  }, { threshold: 0.08, rootMargin: "0px 0px -30px 0px" });

  document.querySelectorAll(".cs-card, .product-card, .product-row").forEach(el => observer.observe(el));
}

function profileToPricingInputs(profile, lob, sumInsuredInr) {
  const p = profile || {};
  const stageMap = {
    "Pre-seed": "preseed",
    "Seed": "seed",
    "Series A": "seriesA",
    "Series B": "seriesB",
    "Series B+": "seriesC+",
    "Series C": "seriesC+",
    "Series D+": "seriesC+",
    "Growth": "seriesC+",
    "Pre-IPO": "pre_ipo",
    "Late Stage / Pre-IPO": "pre_ipo",
  };
  const nicMap = {
    "SaaS / Enterprise Software": "6201",
    "Fintech": "6499",
    "Healthtech": "8610",
    "Edtech": "8550",
    "Logistics / Mobility": "4941",
    "Logistics / Supply Chain": "4941",
    "E-commerce / D2C": "4791",
    "D2C / Consumer Brands": "4791",
    "Agritech": "0111",
    "Agritech / Foodtech": "0111",
    "Climate / Energy": "3510",
    "Cleantech / Climatetech": "3510",
    "Cybersecurity": "6201",
    "AI / ML": "6201",
    "Deeptech / AI / Robotics": "6201",
    "Media / Content": "5911",
    "Gaming / Media / Content": "9200",
    "Gaming": "9200",
    "Real Estate / Proptech": "6810",
    "Proptech": "6810",
    "Travel / Hospitality": "5510",
    "Manufacturing": "2599",
  };
  const cityStateMap = {
    "Bengaluru": "Karnataka",
    "Bangalore": "Karnataka",
    "Mumbai": "Maharashtra",
    "Pune": "Maharashtra",
    "Delhi": "Delhi",
    "Gurugram": "Haryana",
    "Gurgaon": "Haryana",
    "Noida": "Uttar Pradesh",
    "Hyderabad": "Telangana",
    "Chennai": "Tamil Nadu",
    "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat",
  };
  const revenue = Number(p.annual_revenue_cr || 0) * 1e7;
  const loadings = {};
  if (p.dpiit_recognised || p.dpiit_recognition) loadings.dpiit_recognised = 1;
  if (p.cert_in_poc_designated) loadings.cert_in_poc_designated = 1;
  if (p.dpdp_dpo_appointed || p.sdf_likely) loadings.dpdp_dpo_appointed = 1;
  return {
    revenue_current_inr: Math.max(revenue || 0, 4000000),
    revenue_projected_inr: Math.max((revenue || 0) * 1.4, 6000000),
    nic_code: nicMap[p.sector] || "6201",
    stage: stageMap[p.funding_stage] || "seed",
    state: cityStateMap[p.hq_city] || p.state || "Karnataka",
    headcount: Number(p.team_size || 50),
    years_since_incorporation: Number(p.years_since_incorporation || 3),
    cin: p.cin || "U99999MH2020PTC000000",
    dpiit_recognised: Boolean(p.dpiit_recognised || p.dpiit_recognition),
    line_of_business: _LOB_TO_PRICING_LOB[lob] || lob,
    sum_insured_inr: sumInsuredInr,
    deductible_inr: sumInsuredInr >= 1e8 ? 500000 : 100000,
    prior_claims: 0,
    loadings,
  };
}

// Map product recommendation keys → pricing LOB id + display label
const _PRODUCT_KEY_TO_LOB = {
  D_AND_O:                    ["DO",       "D&O"],
  DNO_LIABILITY:              ["DO",       "D&O"],
  CYBER:                      ["Cyber",    "Cyber"],
  CYBER_LIABILITY:            ["Cyber",    "Cyber"],
  PI:                         ["PI",       "PI"],
  PI_TECH_EO:                 ["PI",       "PI / Tech E&O"],
  CGL:                        ["CGL",      "CGL"],
  COMMERCIAL_GENERAL_LIABILITY:["CGL",     "CGL"],
  PUBLIC_LIABILITY:           ["CGL",      "Public Liability"],
  PRODUCT_LIABILITY:          ["CGL",      "Product Liability"],
  FIRE_AND_PROPERTY:          ["Property", "Fire & Property"],
  PROPERTY_ALL_RISK:          ["Property", "Prop. All Risk"],
  BUSINESS_INTERRUPTION:      ["BI",       "Business Int."],
  MACHINERY_BREAKDOWN:        ["MB",       "Machinery Bkdn"],
  ELECTRONIC_EQUIPMENT:       ["EEI",      "Elec. Equipment"],
  GROUP_HEALTH:               ["GH",       "Group Health"],
  EMPLOYEE_HEALTH:            ["GH",       "Group Health"],
  GROUP_PA:                   ["GPA",      "Group PA"],
  GPA:                        ["GPA",      "Group PA"],
  EMPLOYEES_COMP:             ["EC",       "Emp. Comp."],
  WORKMEN_COMPENSATION:       ["EC",       "Emp. Comp."],
  CRIME_FIDELITY:             ["Crime",    "Crime"],
};

// IAR sub-types that the pricing backend routes through "Property" formula
const _LOB_TO_PRICING_LOB = { BI: "Property", MB: "Property", EEI: "Property" };

function _lobsFromResult(result) {
  const bundle = result.bundle_match || {};
  const allKeys = [
    ...(bundle.mandatory_covers || []),
    ...(bundle.optional_covers || []),
    ...(bundle.companion_bundle?.mandatory_covers || []),
    ...(bundle.companion_bundle?.optional_covers || []),
    ...(result.recommendations || []).map(r => typeof r === "string" ? r : r.key).filter(Boolean),
  ];
  const seen = new Set();
  const chips = [];
  for (const key of allKeys) {
    const entry = _PRODUCT_KEY_TO_LOB[key] || _PRODUCT_KEY_TO_LOB[(key || "").toUpperCase()];
    if (!entry) continue;
    const [lob, label] = entry;
    if (!seen.has(lob)) {
      seen.add(lob);
      chips.push([lob, label]);
    }
  }
  return chips;
}

function renderEstimateQuoteButton(result) {
  const profile = result.profile || result; // accept both result obj and bare profile
  const name = profile?.startup_name || "this profile";
  const chips = _lobsFromResult(result.bundle_match !== undefined ? result : { bundle_match: {}, recommendations: [] });
  const chipHtml = chips.length
    ? chips.map(([lob, label]) => `<button class="eq-lob-chip" type="button" data-lob="${lob}">${label}</button>`).join("")
    : `<span class="eq-no-lobs">Run analysis to see available covers</span>`;
  return `
    <div class="estimate-quote-strip">
      <div>
        <div class="eq-label">Premium Triage</div>
        <div class="eq-title">Estimate quote for ${esc(name)}</div>
        <div class="eq-hint">Formula-chain calculator with editable public-source factors.</div>
      </div>
      <div class="eq-lob-chips" id="eq-lob-chips">${chipHtml}</div>
    </div>
    <div id="pricing-panel" class="pricing-panel hidden"></div>`;
}

function bindEstimateQuotePanel(profile) {
  const chips = document.querySelectorAll("#eq-lob-chips .eq-lob-chip");
  chips.forEach(btn => {
    btn.addEventListener("click", () => {
      chips.forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      loadPricingPanel(profile || window.__result?.profile || state.profile, btn.dataset.lob);
    });
  });
}

function estimateSumInsured(profile, lob) {
  const revCr  = Number(profile.annual_revenue_cr || 0);
  const stage  = profile.funding_stage || "Seed";
  const team   = Number(profile.team_size || 10);
  const assets = profile.physical_assets || [];
  const hasHeavyAssets = assets.some(a =>
    ["Warehouse", "Manufacturing", "Data centre", "Cold chain", "Medical device"].some(k => a.includes(k))
  );

  // Per-stage: floor, ceiling, and revenue multiplier (all in INR crores × 1e7)
  const stageBands = {
    "Pre-seed": { floor: 1e7,  ceil: 5e7,   f: 0.20 },
    "Seed":     { floor: 2e7,  ceil: 10e7,  f: 0.18 },
    "Series A": { floor: 3e7,  ceil: 25e7,  f: 0.15 },
    "Series B+":{ floor: 5e7,  ceil: 100e7, f: 0.12 },
  };
  const s = stageBands[stage] || stageBands["Seed"];
  const revBasedSI = revCr > 0
    ? Math.min(Math.max(revCr * 1e7 * s.f, s.floor), s.ceil)
    : s.floor;

  switch (lob) {
    case "DO":       return revBasedSI;
    case "Cyber":    return Math.min(revBasedSI * 0.8, 25e7);
    case "PI":       return Math.min(revBasedSI * 0.6, 20e7);
    case "CGL":      return Math.min(Math.max(revBasedSI * 0.4, 1e7), 5e7);
    case "Property": return hasHeavyAssets ? Math.min(revBasedSI * 1.2, 50e7) : Math.min(revBasedSI * 0.3, 3e7);
    case "GH":       return Math.max(team * 5e5, 5e6); // ₹5L floater per head
    default:         return revBasedSI;
  }
}

async function loadPricingPanel(profile, lob, siOverrideInr = null) {
  const panel = $("pricing-panel");
  if (!panel) return;
  panel.innerHTML = '<div class="pricing-loading">Calculating indicative range...</div>';
  panel.classList.remove("hidden");
  const geminiSI = Number(profile.sum_insured_cr || 0) * 1e7;
  const si = siOverrideInr || (geminiSI > 0 ? geminiSI : estimateSumInsured(profile, lob));
  const inputs = profileToPricingInputs(profile, lob, si);
  try {
    const res = await fetch("/api/pricing", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(inputs),
    });
    const raw = await res.text();
    let data = {};
    try {
      data = raw ? JSON.parse(raw) : {};
    } catch (_parseErr) {
      const compact = String(raw || "").replace(/\s+/g, " ").trim();
      const detail = compact
        ? compact.slice(0, 220)
        : `Non-JSON response from pricing endpoint (${res.status})`;
      throw new Error(detail);
    }
    if (!res.ok || data.error) throw new Error(data.error || "Pricing failed");
    renderPricingCalculator(panel, data.quote, data.loadings_catalog, profile, lob);
  } catch (err) {
    panel.innerHTML = `<div class="pricing-error">Pricing error: ${esc(err.message)}</div>`;
  }
}

function renderPricingCalculator(container, Q, CATALOG, profile, LOB) {
  const EXP_MULTI = 1 / (1 - 0.18 - 0.125 - 0.04 - 0.08);
  const BAND = 0.30;
  const CLAMP = 0.25;
  const ratingOverrides = {};
  const catalogOverrides = {};
  const activeLoadings = new Set((Q.active_loadings || []).map(x => x.id));
  let currentSI = Q.inputs_echo?.sum_insured_inr || estimateSumInsured(profile, LOB);
  const customAdjustments = []; // {id, label, value} added by the underwriter
  const catalogState = {
    search: "",
    filter: "applicable",
    scrollTop: 0,
    mobileOpen: false,
    focusTarget: "",
    openDetails: new Set((Q.active_loadings || []).map(x => x.id)),
  };

  const money = (n) => "Rs. " + Math.round(Number(n) || 0).toLocaleString("en-IN");
  const compactMoney = (n) => {
    const v = Number(n) || 0;
    if (v >= 1e7) return "Rs. " + (v / 1e7).toFixed(2) + " Cr";
    if (v >= 1e5) return "Rs. " + (v / 1e5).toFixed(2) + " L";
    return money(v);
  };
  const pctText = (v) => (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "%";
  const labelStep = (step) => String(step || "").replace(/^\d+[a-z]?\.\s*[×x+÷-]?\s*/i, "").trim();
  const sourceLink = (entry) => entry?.source_url
    ? `<a href="${esc(entry.source_url)}" target="_blank" rel="noopener">${esc(entry.source_citation || "-")}</a>`
    : esc(entry?.source_citation || "-");
  const catalogValue = (id) => Number(catalogOverrides[id] ?? CATALOG[id]?.value ?? 0);
  const catalogMatchesSearch = (label) => !catalogState.search || label.toLowerCase().includes(catalogState.search.toLowerCase());
  const preserveCatalogStateFromDOM = () => {
    const searchEl = container.querySelector("#pc-catalog-search");
    const filterEl = container.querySelector("#pc-catalog-filter");
    const listEl = container.querySelector("#pc-catalog-list");
    const mobileToggle = container.querySelector("#pc-catalog-mobile-toggle");
    if (searchEl) catalogState.search = searchEl.value || "";
    if (filterEl) catalogState.filter = filterEl.value || "applicable";
    if (listEl) catalogState.scrollTop = listEl.scrollTop || 0;
    if (mobileToggle) catalogState.mobileOpen = mobileToggle.getAttribute("aria-expanded") === "true";
  };
  const rerender = () => {
    preserveCatalogStateFromDOM();
    render();
  };

  function recalc() {
    const trace = Q.factor_trace || [];
    const baseStep = trace.find(s => String(s.step).startsWith("1."));
    const pureStep = trace.find(s => String(s.step).startsWith("2."));
    const baseRaw = Number(baseStep?.raw_value || 0);
    const baseVal = Number(ratingOverrides[baseStep?.step] ?? baseRaw);
    let tech = Number(pureStep?.raw_value || 0);
    if (baseRaw > 0 && baseVal > 0) tech *= baseVal / baseRaw;
    trace.filter(s => /^[34]/.test(String(s.step))).forEach(s => {
      tech *= Number(ratingOverrides[s.step] ?? s.raw_value ?? 1);
    });
    let net = 0;
    activeLoadings.forEach(id => {
      if (CATALOG[id]) net += catalogValue(id);
    });
    customAdjustments.forEach(adj => { net += adj.value; });
    const clamped = Math.abs(net) > CLAMP;
    net = Math.max(-CLAMP, Math.min(CLAMP, net));
    const loaded = tech * (1 + net);
    const gross = loaded * EXP_MULTI;
    const gstAmt = gross * 0.18;
    const mid = gross + gstAmt + Number(Q.stamp_duty_inr || 0);
    return { tech, net, loaded, gross, gstAmt, mid, low: mid * (1 - BAND), high: mid * (1 + BAND), clamped };
  }

  function valueCell(kind, key, value, display, isPct = false) {
    const overridden = kind === "factor" ? Object.prototype.hasOwnProperty.call(ratingOverrides, key) : Object.prototype.hasOwnProperty.call(catalogOverrides, key);
    return `<button class="pc-val editable${overridden ? " overridden" : ""}" type="button" data-kind="${kind}" data-key="${esc(key)}" data-pct="${isPct ? "1" : "0"}" data-value="${esc(String(value))}">
      ${overridden ? '<span class="override-dot"></span>' : ""}<span class="val-text">${esc(display)}</span><span class="edit-pencil">edit</span>${overridden ? '<span class="reset-x" data-reset="1">x</span>' : ""}
    </button>`;
  }

  function renderSIRow() {
    const siCr = (currentSI / 1e7).toFixed(2);
    return `<div class="pc-row pc-si-row">
      <div class="pc-op"></div>
      <div class="pc-label">Sum Insured<span class="pc-sub">Heuristic estimate — edit to override</span></div>
      <button class="pc-val editable" type="button" data-kind="si" data-key="si" data-pct="0" data-value="${currentSI}">
        <span class="val-text">₹${siCr} Cr</span><span class="edit-pencil">edit</span>
      </button>
      <div class="pc-src">—</div>
      <div class="pc-conf"></div>
    </div>`;
  }

  function renderRows() {
    const trace = Q.factor_trace || [];
    const ratingRows = trace.filter(s => parseInt(s.step, 10) <= 4).map(s => {
      const n = parseInt(s.step, 10);
      const editable = n === 1 || n === 3 || n === 4;
      const raw = Number(ratingOverrides[s.step] ?? s.raw_value);
      const display = n === 1 ? money(raw) : n === 2 ? s.value : raw.toFixed(3);
      return `<div class="pc-row${n === 2 ? " sub" : ""}">
        <div class="pc-op">${n === 1 ? "" : n === 2 ? "=" : "x"}</div>
        <div class="pc-label">${esc(labelStep(s.step))}${s.is_placeholder ? '<span class="ph-tag">PH</span>' : ""}<span class="pc-sub">${esc((s.notes || "").slice(0, 110))}</span></div>
        ${editable ? valueCell("factor", s.step, raw, display, false) : `<div class="pc-val${n === 2 ? " bold" : ""}"><span class="val-text">${esc(display)}</span></div>`}
        <div class="pc-src">${sourceLink(s)}</div>
        <div class="pc-conf"><span class="pc-conf-dot pc-conf-${esc(s.is_placeholder ? "PLACEHOLDER" : (s.confidence || "medium"))}"></span></div>
      </div>`;
    }).join("");
    const expenseRows = trace.filter(s => [6, 7].includes(parseInt(s.step, 10))).map(s => `
      <div class="pc-row">
        <div class="pc-op">${String(s.step).startsWith("6.") ? "÷" : "+"}</div>
        <div class="pc-label">${esc(labelStep(s.step))}</div>
        <div class="pc-val"><span class="val-text">${esc(s.value)}</span></div>
        <div class="pc-src">${sourceLink(s)}</div>
        <div class="pc-conf"><span class="pc-conf-dot pc-conf-${esc(s.confidence || "medium")}"></span></div>
      </div>`).join("");
    const activeRows = [
      ...Array.from(activeLoadings).map(id => {
        const item = CATALOG[id];
        if (!item) return "";
        const v = catalogValue(id);
        return `<div class="pc-loading-row">
          <div><strong>${esc(labelize(id))}</strong><span>${esc((item.source?.citation || "").slice(0, 95))}</span></div>
          ${valueCell("loading", id, v, pctText(v), true)}
          <button class="pc-mini-btn" type="button" data-remove-loading="${esc(id)}">x</button>
        </div>`;
      }),
      ...customAdjustments.map(adj => `
        <div class="pc-loading-row pc-custom-row">
          <div><strong>${esc(adj.label)}</strong><span class="pc-custom-tag">Custom</span></div>
          <div class="pc-val bold ${adj.value < 0 ? "grn" : "red"}">${pctText(adj.value)}</div>
          <button class="pc-mini-btn" type="button" data-remove-custom="${esc(adj.id)}">x</button>
        </div>`),
    ].join("") || `<div class="pc-empty">No adjustments applied.</div>`;
    const catalogRows = Object.entries(CATALOG || {}).map(([id, item]) => {
      const ok = (item.applies_to || []).includes(LOB);
      const on = activeLoadings.has(id);
      const v = catalogValue(id);
      const label = item.label || labelize(id);
      const matchesFilter = catalogState.filter === "all"
        || (catalogState.filter === "applicable" && ok)
        || (catalogState.filter === "active" && on);
      if (!matchesFilter || !catalogMatchesSearch(label)) return "";
      const dir = item.direction === "discount" ? "grn" : "red";
      const confBadge = item.confidence
        ? `<span class="pc-conf-badge pc-conf-${esc(item.confidence)}">${esc(item.confidence)}</span>`
        : "";
      const irdaiBadge = item.irdai_formalised
        ? `<span class="pc-irdai-badge">IRDAI</span>`
        : "";
      const rangeText = (item.low_pct != null && item.high_pct != null)
        ? `${item.direction === "discount" ? "-" : "+"}${item.low_pct}% – ${item.direction === "discount" ? "-" : "+"}${item.high_pct}%`
        : pctText(v);
      const srcUrl = item.source?.url || "";
      const srcCitation = item.source?.citation || "";
      const sourceHtml = srcUrl
        ? `<a class="pc-src-link" href="${esc(srcUrl)}" target="_blank" rel="noopener">${esc(srcCitation || srcUrl)}</a>`
        : (srcCitation ? `<span class="pc-src-text">${esc(srcCitation)}</span>` : "");
      const open = catalogState.openDetails.has(id) || on;
      return `<details class="pc-catalog-row${ok ? "" : " muted"}" data-catalog-id="${esc(id)}" ${open ? "open" : ""}>
        <summary>
          <div class="pc-cat-summary-inner">
            <div class="pc-cat-head-left">
              <strong>${esc(label)}</strong>
              <div class="pc-cat-badges">${confBadge}${irdaiBadge}${ok ? "" : `<span class="pc-na-badge">N/A for ${LOB}</span>`}</div>
            </div>
            <div class="pc-cat-head-right">
              <span class="pc-val ${dir}">${rangeText}</span>
              <button class="pc-mini-btn" type="button" data-toggle-loading="${esc(id)}" ${ok ? "" : "disabled"}>${on ? "− Remove" : "+ Add"}</button>
            </div>
          </div>
        </summary>
        <div class="pc-catalog-detail">
          ${item.rationale ? `<p class="pc-detail-rationale">${esc(item.rationale)}</p>` : ""}
          <div class="pc-detail-meta">
            <span><em>Applies to:</em> ${esc((item.applies_to || []).join(", ") || "All")}</span>
            ${item.notes ? `<span><em>Note:</em> ${esc(item.notes)}</span>` : ""}
          </div>
          ${sourceHtml ? `<div class="pc-detail-source">Source: ${sourceHtml}</div>` : ""}
        </div>
      </details>`;
    }).filter(Boolean).join("");
    return { ratingRows, expenseRows, activeRows, catalogRows };
  }

  function render() {
    const rows = renderRows();
    const c = recalc();
    container.innerHTML = `
      <div class="pc-shell">
        <div class="pc-topline">
          <div><div class="eq-label">Premium Triage</div><h3>${esc(LOB)} formula-chain quote</h3><p>${esc(profile?.startup_name || "Startup")} | NIC ${esc(Q.inputs_echo?.nic_code || "")} | ${esc(Q.inputs_echo?.stage || "")} | ${esc(Q.inputs_echo?.state || "")}</p></div>
          <div class="pc-topline-actions">
            <button class="pc-explain-btn" type="button" id="pc-explain-btn" title="Show step-by-step calculation rationale">Why this number?</button>
            <button class="pc-reset-all" type="button" id="pc-reset-all">Reset all edits</button>
          </div>
        </div>
        <div class="pc-layout">
          <div class="pc-left">
            <div class="pc-left-layout">
              <div class="pc-main">
                <div class="pc-section-eyebrow">Rating Factors</div>
                <div class="pc-factor-table">${renderSIRow()}${rows.ratingRows}<div class="pc-row sub"><div class="pc-op">=</div><div class="pc-label">Technical premium<span class="pc-sub">Before adjustments and expense loading</span></div><div class="pc-val bold"><span class="val-text">${money(c.tech)}</span></div><div class="pc-src">derived</div><div class="pc-conf"></div></div></div>
                <div class="pc-section-eyebrow">Active Adjustments</div>
                <div class="pc-loadings-card"><div class="pc-loadings-head"><span>Loadings and discounts</span><span class="pc-net-badge ${c.net < 0 ? "pc-net-neg" : c.net > 0 ? "pc-net-pos" : "pc-net-zero"}">${pctText(c.net)}</span></div><div class="pc-loadings-list">${rows.activeRows}</div><div class="pc-clamp ${c.clamped ? "on" : ""}">Net adjustment clamped to +/-25%</div></div>
                <div class="pc-custom-adj-wrap" id="pc-custom-adj-wrap">
                  <button class="pc-add-custom-btn" type="button" id="pc-add-custom-btn">+ Add custom adjustment</button>
                  <div class="pc-custom-form hidden" id="pc-custom-form">
                    <input class="pc-custom-label-input" id="pc-custom-label" type="text" placeholder="Label, e.g. Renewal loyalty discount" maxlength="60">
                    <input class="pc-custom-pct-input" id="pc-custom-pct" type="number" step="0.5" placeholder="e.g. -10 or +15">
                    <span class="pc-custom-pct-hint">%</span>
                    <button class="pc-mini-btn pc-custom-apply" type="button" id="pc-custom-apply">Apply</button>
                    <button class="pc-mini-btn" type="button" id="pc-custom-cancel">Cancel</button>
                  </div>
                </div>
                <button class="pc-catalog-mobile-toggle" type="button" id="pc-catalog-mobile-toggle" aria-expanded="${catalogState.mobileOpen ? "true" : "false"}">Add from catalog</button>
                <div class="pc-section-eyebrow">Expense and Tax</div>
                <div class="pc-factor-table">${rows.expenseRows}</div>
              </div>
              <aside class="pc-catalog-rail${catalogState.mobileOpen ? " is-open" : ""}">
                <div class="pc-loadings-card pc-catalog-card">
                  <div class="pc-loadings-head pc-catalog-head">
                    <div>
                      <span>Add from catalog</span>
                      <p>Search and schedule adjustments without pushing the quote downward.</p>
                    </div>
                  </div>
                  <div class="pc-catalog-controls">
                    <input id="pc-catalog-search" class="pc-catalog-search" type="search" value="${esc(catalogState.search)}" placeholder="Search factor, e.g. ISO, DPIIT, litigation">
                    <select id="pc-catalog-filter" class="pc-catalog-filter">
                      <option value="all"${catalogState.filter === "all" ? " selected" : ""}>All</option>
                      <option value="applicable"${catalogState.filter === "applicable" ? " selected" : ""}>Applicable to current LOB</option>
                      <option value="active"${catalogState.filter === "active" ? " selected" : ""}>Active only</option>
                    </select>
                  </div>
                  <div class="pc-catalog-meta"><span>${Object.keys(CATALOG || {}).length} factors</span><span>${rows.catalogRows ? "Live catalog" : "No matching factors"}</span></div>
                  <div class="pc-catalog-list" id="pc-catalog-list">${rows.catalogRows || `<div class="pc-empty">No catalog adjustments match the current search/filter state.</div>`}</div>
                </div>
              </aside>
            </div>
          </div>
          <aside class="pc-right">
            <div class="pcard">
              <div class="pc-range-head"><div class="pc-range-eyebrow">Indicative range (+/-30%)</div><div class="pc-range-row"><span class="pc-range-amt">${compactMoney(c.low)}</span><span class="pc-range-dash">to</span><span class="pc-range-amt">${compactMoney(c.high)}</span></div><div class="pc-range-mid">Mid: <span>${money(c.mid)}</span></div></div>
              <div class="pc-breakdown">
                <div><span>Technical premium</span><strong>${money(c.tech)}</strong></div>
                <div><span>Net adjustment ${pctText(c.net)}</span><strong class="${c.net < 0 ? "grn" : c.net > 0 ? "red" : ""}">${money(c.loaded - c.tech)}</strong></div>
                <div><span>Loaded premium</span><strong>${money(c.loaded)}</strong></div>
                <div><span>Expense multiplier</span><strong>x ${EXP_MULTI.toFixed(3)}</strong></div>
                <div><span>Gross premium</span><strong>${money(c.gross)}</strong></div>
                <div><span>GST @ 18%</span><strong>${money(c.gstAmt)}</strong></div>
                <div><span>Stamp duty</span><strong>${money(Q.stamp_duty_inr)}</strong></div>
                <div class="total"><span>Mid-point incl. GST</span><strong>${money(c.mid)}</strong></div>
              </div>
              <div class="pc-kpi-strip"><span>${((c.mid / Number(Q.inputs_echo?.revenue_current_inr || 1)) * 10000).toFixed(1)} bps revenue</span><span>DQ ${Number(Q.data_quality_score || 0).toFixed(2)}</span><span>${esc(Q.decision || "indicative_quote")}</span></div>
            </div>
            <div class="pc-disclaimer">Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.</div>
            <details class="pc-sources"><summary>Sources cited</summary>${(Q.sources_cited || []).map(s => `<div class="pc-source-row"><span>${esc(s.code)}</span><a href="${esc(s.url || "#")}" target="_blank" rel="noopener">${esc(s.citation || "")}</a></div>`).join("")}</details>
          </aside>
        </div>
        <div class="pc-explain-modal hidden" id="pc-explain-modal" role="dialog" aria-modal="true" aria-labelledby="pc-explain-title">
          <div class="pc-explain-backdrop" id="pc-explain-backdrop"></div>
          <div class="pc-explain-card">
            <header class="pc-explain-header">
              <div>
                <div class="pc-explain-eyebrow">Premium Triage — calculation walkthrough</div>
                <h3 id="pc-explain-title">How we arrived at ${money(c.mid)}</h3>
              </div>
              <button class="pc-explain-close" type="button" id="pc-explain-close" aria-label="Close">×</button>
            </header>
            <div class="pc-explain-body">${renderExplanation(c)}</div>
          </div>
        </div>
      </div>`;
    bind();
  }

  function renderExplanation(c) {
    const trace = Q.factor_trace || [];
    const baseStep = trace.find(s => String(s.step).startsWith("1."));
    const baseRate = Number(ratingOverrides[baseStep?.step] ?? baseStep?.raw_value ?? 0);
    const siCr = (currentSI / 1e7).toFixed(2);
    const insuredName = esc(profile?.startup_name || "Startup");
    const nic = esc(Q.inputs_echo?.nic_code || "—");
    const stage = esc(Q.inputs_echo?.stage || "—");
    const stateName = esc(Q.inputs_echo?.state || "—");
    const tenure = Number(Q.inputs_echo?.years_since_incorporation || 0).toFixed(1);

    const ratingRows = trace
      .filter(s => { const n = parseInt(s.step, 10); return n >= 2 && n <= 4; })
      .map(s => {
        const v = Number(ratingOverrides[s.step] ?? s.raw_value ?? 1);
        const effect = v === 1
          ? "neutral"
          : v > 1
            ? `loads premium <strong>+${((v - 1) * 100).toFixed(1)}%</strong>`
            : `discounts premium <strong>−${((1 - v) * 100).toFixed(1)}%</strong>`;
        const phTag = s.is_placeholder ? ' <span class="pc-explain-ph">PLACEHOLDER</span>' : "";
        return `<tr>
          <td><strong>${esc(labelStep(s.step))}</strong>${phTag}</td>
          <td class="pc-explain-num">×${v.toFixed(3)}</td>
          <td>${effect}</td>
          <td>${esc(s.notes || "—")}</td>
          <td>${sourceLink(s)}</td>
        </tr>`;
      }).join("");

    const adjustments = [
      ...Array.from(activeLoadings).map(id => {
        const item = CATALOG[id];
        if (!item) return null;
        return {
          label: labelize(id),
          pct: catalogValue(id),
          why: item.source?.citation || item.rationale || "Catalog adjustment",
          source: item.source?.url ? `<a href="${esc(item.source.url)}" target="_blank" rel="noopener">${esc(item.source.citation || "Source")}</a>` : esc(item.source?.citation || ""),
        };
      }).filter(Boolean),
      ...customAdjustments.map(a => ({
        label: a.label,
        pct: a.value,
        why: "Custom adjustment — underwriter judgement",
        source: "—",
      })),
    ];
    const adjRows = adjustments.length
      ? adjustments.map(a => `<tr>
          <td><strong>${esc(a.label)}</strong></td>
          <td class="pc-explain-num ${a.pct < 0 ? "grn" : "red"}">${pctText(a.pct)}</td>
          <td>${esc(a.why)}</td>
          <td>${a.source}</td>
        </tr>`).join("")
      : `<tr><td colspan="4" class="pc-explain-empty">No loadings or discounts applied. Premium reflects rating factors only.</td></tr>`;

    const placeholders = (Q.placeholders_used || []);
    const dqLine = placeholders.length
      ? `Score is reduced by <strong>${placeholders.length} placeholder factor${placeholders.length > 1 ? "s" : ""}</strong> (${placeholders.map(p => esc(p)).join(", ")}). Replacing these with carrier-quoted or broker-benchmarked values will lift the score.`
      : `All rating factors trace to a cited public source. Score reflects the credibility of those sources.`;

    const sourcesList = (Q.sources_cited || []).map(s => `<tr>
        <td><code>${esc(s.code || "—")}</code></td>
        <td><a href="${esc(s.url || "#")}" target="_blank" rel="noopener">${esc(s.citation || s.url || "—")}</a></td>
      </tr>`).join("");

    return `
      <section class="pc-explain-section">
        <h4>1 · What this quote actually is</h4>
        <p>An <strong>indicative premium estimate</strong> for ${esc(LOB)} cover, generated under IRDAI's File-and-Use detariffed regime (in force since 2007 for most general insurance lines). It is <strong>not a bindable quote</strong> — every value is either a cited public-domain rate or a flagged placeholder. Use it to plan, benchmark carrier quotes, and frame underwriter conversations.</p>
      </section>

      <section class="pc-explain-section">
        <h4>2 · The risk we are pricing</h4>
        <div class="pc-explain-anchor">
          <div><span>Insured</span><strong>${insuredName}</strong></div>
          <div><span>Line of business</span><strong>${esc(LOB)}</strong></div>
          <div><span>NIC 2008 code</span><strong>${nic}</strong></div>
          <div><span>Funding stage</span><strong>${stage}</strong></div>
          <div><span>State</span><strong>${stateName}</strong></div>
          <div><span>Years since incorporation</span><strong>${tenure}</strong></div>
          <div><span>Sum Insured</span><strong>₹${siCr} Cr</strong></div>
        </div>
      </section>

      <section class="pc-explain-section">
        <h4>3 · Step 1 — Pure premium</h4>
        <p>We anchor on a <strong>base rate of ₹${Math.round(baseRate).toLocaleString("en-IN")} per ₹1 crore of Sum Insured</strong> for this line, then multiply by the SI in crores.</p>
        <div class="pc-explain-formula">₹${Math.round(baseRate).toLocaleString("en-IN")} / cr × ${siCr} cr = <strong>${money(baseRate * (currentSI / 1e7))}</strong></div>
        <p class="pc-explain-source">Source: ${sourceLink(baseStep)} <span class="pc-explain-conf">confidence: ${esc(baseStep?.confidence || "medium")}</span></p>
      </section>

      <section class="pc-explain-section">
        <h4>4 · Steps 2–4 — Risk multipliers</h4>
        <p>Pure premium is multiplied by a chain of risk factors. Each one captures a different driver — sector hazard, startup stage, state, tenure, sum-insured band, deductible, and the insured's own loss experience. Every factor is sourced from a public Indian regulator, bureau, or carrier disclosure, or flagged <span class="pc-explain-ph">PLACEHOLDER</span> when no public source exists.</p>
        <div class="pc-explain-table-wrap">
          <table class="pc-explain-table">
            <thead><tr><th>Factor</th><th>×</th><th>Effect</th><th>What it captures</th><th>Source</th></tr></thead>
            <tbody>${ratingRows}</tbody>
          </table>
        </div>
        <p class="pc-explain-running">After all multipliers → <strong>Technical premium = ${money(c.tech)}</strong></p>
      </section>

      <section class="pc-explain-section">
        <h4>5 · Step 5 — Underwriter adjustments</h4>
        <p>Schedule-rated loadings or discounts toggled from the catalog (or added manually). The net adjustment is clamped to <strong>±25%</strong> in line with standard schedule-rating practice.</p>
        <div class="pc-explain-table-wrap">
          <table class="pc-explain-table">
            <thead><tr><th>Adjustment</th><th>%</th><th>Rationale</th><th>Source</th></tr></thead>
            <tbody>${adjRows}</tbody>
          </table>
        </div>
        <p class="pc-explain-running">Net adjustment: <strong>${pctText(c.net)}</strong>${c.clamped ? " (clamped at ±25%)" : ""} → Loaded premium = <strong>${money(c.loaded)}</strong></p>
      </section>

      <section class="pc-explain-section">
        <h4>6 · Step 6 — Expense and reinsurance gross-up</h4>
        <p>Insurers must recover operating expenses, broker commission, reinsurance cession, and a target profit margin before they break even. The loaded premium is grossed up by dividing by (1 − total load):</p>
        <ul class="pc-explain-list">
          <li><strong>Management expense ratio · 18%</strong> — derived from <a href="https://www.irdai.gov.in/" target="_blank" rel="noopener">IRDAI Annual Report</a> industry averages for general insurers</li>
          <li><strong>Broker commission · 12.5%</strong> — within caps under <a href="https://www.irdai.gov.in/" target="_blank" rel="noopener">IRDAI (Payment of Commission) Regulations, 2023</a></li>
          <li><strong>Reinsurance cession load · 4%</strong> — calibrated to GIC Re obligatory cession share (placeholder until carrier-specific treaty cost is supplied)</li>
          <li><strong>Target profit margin · 8%</strong> — IRDAI solvency-implied target</li>
        </ul>
        <div class="pc-explain-formula">${money(c.loaded)} ÷ (1 − 0.18 − 0.125 − 0.04 − 0.08) = ${money(c.loaded)} × ${EXP_MULTI.toFixed(3)} = <strong>${money(c.gross)}</strong> gross premium</div>
      </section>

      <section class="pc-explain-section">
        <h4>7 · Step 7 — Statutory loads (GST + stamp duty)</h4>
        <ul class="pc-explain-list">
          <li><strong>GST @ 18% = ${money(c.gstAmt)}</strong> — per Department of Financial Services notification on insurance premium GST</li>
          <li><strong>Stamp duty (${stateName}) = ${money(Q.stamp_duty_inr || 0)}</strong> — per state stamp act schedule for policies of insurance</li>
        </ul>
        <div class="pc-explain-formula"><strong>Final indicative premium (mid-point) = ${money(c.mid)}</strong></div>
      </section>

      <section class="pc-explain-section">
        <h4>8 · Why a range, not a single number?</h4>
        <p>Indian general-insurance rate filings are <strong>not publicly browsable</strong> (no SERFF equivalent exists). Public sources let us anchor a credible mid-point, but the actual rate any insurer will offer will vary by approximately <strong>±30%</strong> depending on appetite, treaty terms, competitive intent, and risk-specific underwriter judgement. We surface this honestly as an indicative range of <strong>${compactMoney(c.low)} – ${compactMoney(c.high)}</strong> rather than pretending a precision we do not have.</p>
      </section>

      <section class="pc-explain-section">
        <h4>9 · Data quality score: <span class="pc-explain-dq">${Number(Q.data_quality_score || 0).toFixed(2)}</span> / 1.00</h4>
        <p>${dqLine} A score above 0.70 is generally defensible to a CFO / MD / CEO audience; below 0.50 the engine returns <code>refer_to_underwriter</code> rather than a quote.</p>
      </section>

      <section class="pc-explain-section">
        <h4>10 · Sources cited in this quote</h4>
        <div class="pc-explain-table-wrap">
          <table class="pc-explain-table pc-explain-sources">
            <thead><tr><th>Ref</th><th>Citation</th></tr></thead>
            <tbody>${sourcesList || `<tr><td colspan="2" class="pc-explain-empty">No structured sources attached to this quote.</td></tr>`}</tbody>
          </table>
        </div>
        <p class="pc-explain-foot">Every numeric value above is editable in the formula chain — overrides reset the source confidence to "underwriter override" in audit trail.</p>
      </section>`;
  }

  function startEdit(btn, clickEvent) {
    if (clickEvent?.target?.dataset?.reset) {
      if (btn.dataset.kind === "factor") delete ratingOverrides[btn.dataset.key];
      if (btn.dataset.kind === "loading") delete catalogOverrides[btn.dataset.key];
      rerender();
      return;
    }
    const isPct = btn.dataset.pct === "1";
    const isSI  = btn.dataset.kind === "si";
    const input = document.createElement("input");
    input.className = "pc-inline-input";
    input.type = "number";
    input.step = isSI ? "0.5" : isPct ? "0.5" : "0.01";
    input.placeholder = isSI ? "₹ Cr" : "";
    // SI stored in raw INR, show/edit in Cr
    input.value = isSI
      ? (Number(btn.dataset.value) / 1e7).toFixed(2)
      : isPct ? (Number(btn.dataset.value) * 100).toFixed(2) : String(Number(btn.dataset.value));
    btn.replaceWith(input);
    input.focus();
    input.select();
    const save = () => {
      const n = Number(input.value);
      if (isSI) {
        if (Number.isFinite(n) && n > 0) {
          currentSI = n * 1e7;
          loadPricingPanel(profile, LOB, currentSI);
        } else {
          rerender();
        }
        return;
      }
      if (Number.isFinite(n)) {
        if (btn.dataset.kind === "factor") ratingOverrides[btn.dataset.key] = n;
        if (btn.dataset.kind === "loading") catalogOverrides[btn.dataset.key] = isPct ? n / 100 : n;
      }
      rerender();
    };
    input.addEventListener("blur", save, { once: true });
    input.addEventListener("keydown", e => {
      if (e.key === "Enter") input.blur();
      if (e.key === "Escape") rerender();
    });
  }

  function bind() {
    container.querySelectorAll(".pc-val.editable").forEach(btn => btn.addEventListener("click", e => startEdit(btn, e)));
    const catalogSearch = container.querySelector("#pc-catalog-search");
    const catalogFilter = container.querySelector("#pc-catalog-filter");
    const catalogList = container.querySelector("#pc-catalog-list");
    const mobileToggle = container.querySelector("#pc-catalog-mobile-toggle");
    if (catalogSearch) catalogSearch.addEventListener("input", () => {
      catalogState.search = catalogSearch.value || "";
      catalogState.scrollTop = 0;
      catalogState.focusTarget = "search";
      render();
    });
    if (catalogFilter) catalogFilter.addEventListener("change", () => {
      catalogState.filter = catalogFilter.value || "applicable";
      catalogState.scrollTop = 0;
      catalogState.focusTarget = "filter";
      render();
    });
    if (catalogList) {
      catalogList.scrollTop = catalogState.scrollTop || 0;
      catalogList.addEventListener("scroll", () => {
        catalogState.scrollTop = catalogList.scrollTop || 0;
      });
    }
    if (catalogState.focusTarget === "search" && catalogSearch) {
      catalogSearch.focus();
      const len = catalogSearch.value.length;
      catalogSearch.setSelectionRange(len, len);
      catalogState.focusTarget = "";
    }
    if (catalogState.focusTarget === "filter" && catalogFilter) {
      catalogFilter.focus();
      catalogState.focusTarget = "";
    }
    if (mobileToggle) mobileToggle.addEventListener("click", () => {
      catalogState.mobileOpen = !catalogState.mobileOpen;
      render();
    });
    container.querySelectorAll(".pc-catalog-row").forEach(row => row.addEventListener("toggle", () => {
      const id = row.dataset.catalogId;
      if (!id) return;
      if (row.open) catalogState.openDetails.add(id);
      else catalogState.openDetails.delete(id);
    }));
    container.querySelectorAll("[data-toggle-loading]").forEach(btn => btn.addEventListener("click", e => {
      e.stopPropagation(); // prevent <details> toggle when button is inside <summary>
      const id = btn.dataset.toggleLoading;
      activeLoadings.has(id) ? activeLoadings.delete(id) : activeLoadings.add(id);
      catalogState.openDetails.add(id);
      rerender();
    }));
    container.querySelectorAll("[data-remove-loading]").forEach(btn => btn.addEventListener("click", () => {
      activeLoadings.delete(btn.dataset.removeLoading);
      rerender();
    }));
    container.querySelectorAll("[data-remove-custom]").forEach(btn => btn.addEventListener("click", () => {
      const idx = customAdjustments.findIndex(a => a.id === btn.dataset.removeCustom);
      if (idx !== -1) customAdjustments.splice(idx, 1);
      rerender();
    }));
    const addBtn    = document.getElementById("pc-add-custom-btn");
    const form      = document.getElementById("pc-custom-form");
    const applyBtn  = document.getElementById("pc-custom-apply");
    const cancelBtn = document.getElementById("pc-custom-cancel");
    if (addBtn) addBtn.addEventListener("click", () => {
      form.classList.remove("hidden");
      addBtn.classList.add("hidden");
      document.getElementById("pc-custom-label").focus();
    });
    if (cancelBtn) cancelBtn.addEventListener("click", () => {
      form.classList.add("hidden");
      addBtn.classList.remove("hidden");
    });
    if (applyBtn) applyBtn.addEventListener("click", () => {
      const label = (document.getElementById("pc-custom-label").value || "").trim();
      const pct   = Number(document.getElementById("pc-custom-pct").value);
      if (!label || !Number.isFinite(pct) || pct === 0) return;
      customAdjustments.push({ id: "custom_" + Date.now(), label, value: pct / 100 });
      rerender();
    });
    const reset = $("pc-reset-all");
    if (reset) reset.addEventListener("click", () => {
      Object.keys(ratingOverrides).forEach(k => delete ratingOverrides[k]);
      Object.keys(catalogOverrides).forEach(k => delete catalogOverrides[k]);
      customAdjustments.length = 0;
      catalogState.search = "";
      catalogState.filter = "applicable";
      catalogState.scrollTop = 0;
      render();
    });
    const explainBtn      = $("pc-explain-btn");
    const explainModal    = $("pc-explain-modal");
    const explainClose    = $("pc-explain-close");
    const explainBackdrop = $("pc-explain-backdrop");
    const openExplain  = () => { if (explainModal) explainModal.classList.remove("hidden"); document.body.classList.add("pc-explain-open"); };
    const closeExplain = () => { if (explainModal) explainModal.classList.add("hidden"); document.body.classList.remove("pc-explain-open"); };
    if (explainBtn)      explainBtn.addEventListener("click", openExplain);
    if (explainClose)    explainClose.addEventListener("click", closeExplain);
    if (explainBackdrop) explainBackdrop.addEventListener("click", closeExplain);
    if (explainModal) {
      const escHandler = (e) => { if (e.key === "Escape" && !explainModal.classList.contains("hidden")) closeExplain(); };
      document.addEventListener("keydown", escHandler);
    }
  }

  render();
}

function renderResults(result) {
  result = normalizeGroupSafeguardCompanion(result);
  // Consume any pending signal context (set by "Draft outreach" button on signal cards)
  if (window.__pendingSignalContext) {
    result.signal_context = window.__pendingSignalContext;
    window.__pendingSignalContext = null;
  }
  if (!_navCalledByHistory) { const _r = result; _navHistory = _navHistory.slice(0, _navPos + 1); _navHistory.push({ fn: renderResults, args: [_r], view: "results" }); _navPos = _navHistory.length - 1; setTimeout(_updateNavButtons, 0); }
  window.__outreachLoaded = false;
  state.profile = structuredClone(result.profile || state.profile);
  const p = result.profile;
  const autofilledFields = new Set(result.autofilled_fields || []);
  const heroExtraMeta = [];
  if (autofilledFields.has("annual_revenue_cr") && Number(p.annual_revenue_cr || 0) > 0) {
    heroExtraMeta.push(`<span>INR ${formatCr(p.annual_revenue_cr)} Cr revenue</span>`);
  }
  if (autofilledFields.has("total_insurable_asset_value_cr") && Number(p.total_insurable_asset_value_cr || 0) > 0) {
    heroExtraMeta.push(`<span>INR ${formatCr(p.total_insurable_asset_value_cr)} Cr insurable assets</span>`);
  }

  const gaugeClass = result.overall >= 70 ? "gauge-critical" : result.overall >= 45 ? "gauge-moderate" : "gauge-low";
  const gaugeColor = result.overall >= 70 ? "var(--red)" : result.overall >= 45 ? "var(--amber)" : "var(--green)";

  $("main-content").innerHTML = `
    <div class="results-wrap">

      <!-- Hero -->
      <div class="results-hero">
        <div>
          <div class="hero-eyebrow">Risk Report</div>
          <div class="hero-title">${esc(p.startup_name)} — ${result.overall}/100 overall risk</div>
          <div class="hero-meta">
            <span>${esc(p.sector)}</span>
            <span>${esc(p.funding_stage)}</span>
            <span>${p.team_size} people</span>
            <span>${esc(p.operations)}</span>
            ${heroExtraMeta.join("")}
          </div>
          ${p.product_description ? `<div class="hero-product-desc">${esc(p.product_description)}</div>` : ""}
          ${(() => {
            const rev = Number(p.annual_revenue_cr || 0);
            const siCr = Number(p.sum_insured_cr || 0);
            const assets = siCr > 0 ? siCr : (rev > 0 ? Math.round(rev * 1.5) : 0);
            if (!rev && !assets) return "";
            return `<div class="hero-financials">
              ${rev > 0 ? `<div class="hero-fin-stat"><span class="hero-fin-label">Annual revenue</span><span class="hero-fin-value">INR ${Number(rev).toLocaleString("en-IN")} Cr</span></div>` : ""}
              ${assets > 0 ? `<div class="hero-fin-stat"><span class="hero-fin-label">Insurable assets</span><span class="hero-fin-value">INR ${Number(assets).toLocaleString("en-IN")} Cr</span></div>` : ""}
            </div>`;
          })()}
        </div>
        <div class="hero-actions">
          <button class="btn-hero-ghost" onclick="renderRoleSelection()" style="margin-right:auto;">← Home</button>
          <button class="btn-hero-primary" onclick="openSummaryPDF()">Download report</button>
          <button class="btn-hero-ghost" onclick="renderForm()">Edit inputs</button>
          <button class="btn-hero-ghost" onclick="openAdvancedPanel()" id="btn-refine-inputs" title="Add governance, gig, data &amp; AI, and physical inputs to sharpen the risk score">Refine inputs ⚙</button>
        </div>
      </div>

      <!-- Section nav -->
      <nav class="section-nav">
        ${[["bundle","Bundle"],["outreach","Outreach"],["quote","Estimated Quote"],["risk","Risk scores"],["triggers","Actions"]].map(([id,l],i)=>`<button class="snav-pill${i===0?" snav-active":""}" onclick="showTab('${id}')" id="snav-${id}">${l}</button>`).join("")}
      </nav>

      <!-- KPI strip — always visible -->
      <div class="kpi-row">
        ${renderKPI("Overall risk", `${result.overall}/100`)}
        ${renderKPI("Top risk", (result.top_risks||[])[0]?.name?.replace(" Risk","") || "—")}
        ${renderKPI("Critical covers", (result.recommendations||[]).filter(r=>r.priority==="Critical").length + " products")}
        ${renderKPI("Bundle quote", result.bundle_only_pricing_quote?.gross_premium_lakh ? `INR ${result.bundle_only_pricing_quote.gross_premium_lakh}L` : "Input needed")}
        ${renderKPI("Premium range", shouldSuppressBenchmarkRange(result) ? "Enterprise UW" : (result.premium_summary ? `INR ${result.premium_summary.min_lakh}-${result.premium_summary.max_lakh}L` : "N/A"))}
        ${renderKPI("Risk clusters", Object.keys(result.clusters||{}).length + " analysed")}
      </div>

      <!-- ── TAB: Bundle ── -->
      <div class="tab-panel" id="tab-bundle">
        <div class="result-section">
          <div class="result-section-head">
            <div class="result-section-bar"></div>
            <div class="result-section-title">Bundle recommendation</div>
            <button class="pdf-trigger-btn" type="button" onclick="downloadReport(window.__result)" title="Download founder summary as text">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download summary
            </button>
          </div>
          ${renderGenAIStatus(result)}
          ${renderFounderContextStrip(result.profile)}
          ${renderBundleHero(result.bundle_match, result.recommendations, result.why_it_matters)}
          ${renderBundleAlternatives(result.bundle_alternatives)}
        </div>
        ${renderClaimsScenarios(result)}
        <div class="result-section">
          <div class="result-section-head">
            <div class="result-section-bar"></div>
            <div class="result-section-title">Additional recommended products</div>
          </div>
          <div class="products-list">
            ${(() => {
              const normalise = k => COVER_ALIASES[k] || k;
              const bundleKeys = new Set([
                ...(result.bundle_match?.mandatory_covers || []),
                ...(result.bundle_match?.optional_covers || []),
                ...(result.bundle_match?.companion_bundle?.mandatory_covers || []),
                ...(result.bundle_match?.companion_bundle?.optional_covers || []),
              ].map(normalise));
              const additionalRecs = (result.recommendations || []).filter(r => !bundleKeys.has(normalise(r.key)));
              if (!additionalRecs.length) {
                return `<div class="r-card">${emptyState("✓", "All recommended products are in your bundle", "The engine has no additional products to recommend outside the selected bundle.")}</div>`;
              }
              return renderProductRows(additionalRecs, result.product_mapping, result.why_it_matters);
            })()}
          </div>
          ${renderBadProducts(result.not_preferred_recommendations)}
        </div>
      </div>

      <!-- ── TAB: Outreach ── -->
      <div class="tab-panel" id="tab-outreach" style="display:none">
        <div class="ot-subnav" id="ot-subnav" style="${result.signal_context ? "" : "display:none"}">
          <button class="ot-sub-pill ot-sub-active" id="ot-sub-company" onclick="showOutreachSubTab('company')">Company outreach</button>
          <button class="ot-sub-pill" id="ot-sub-signal" onclick="showOutreachSubTab('signal')">Signal outreach</button>
        </div>
        <div class="ot-sub-panel" id="ot-panel-company">
          <div id="outreach-static">${renderFounderPitch(result)}</div>
          <div id="outreach-dynamic">${renderOutreach(result.outreach_fallback || {}, "fallback", null)}</div>
        </div>
        <div class="ot-sub-panel" id="ot-panel-signal" style="display:none">
          <div id="signal-outreach-context"></div>
          <div id="signal-outreach-dynamic"></div>
        </div>
      </div>

      <!-- ── TAB: Estimated Quote ── -->
      <div class="tab-panel" id="tab-quote" style="display:none">
        ${renderEstimateQuoteButton(result)}
        ${renderV2Insights(result)}
        ${renderMethodologyModal(result)}
        <details class="expander-card" style="margin-bottom:14px;">
          <summary>Product comparison table</summary>
          <div class="expander-body">${renderComparisonTable(result.recommendations)}</div>
        </details>
      </div>

      <!-- ── TAB: Risk scores ── -->
      <div class="tab-panel" id="tab-risk" style="display:none">
        <div class="result-section">
          <div class="result-section-head">
            <div class="result-section-bar"></div>
            <div class="result-section-title">Risk overview</div>
          </div>
          <div class="score-grid">
            <div class="r-card" style="display:flex;flex-direction:column;">
              <div class="card-label">Overall risk score</div>
              <div class="gauge-wrap" style="flex:1;">
                <div class="gauge-ring" style="--score:${Math.min(100,result.overall)};background:radial-gradient(circle at center,white 0 57%,transparent 58%),conic-gradient(${gaugeColor} calc(${Math.min(100,result.overall)} * 1%),var(--surface) 0);">
                  <div class="gauge-ring-inner">
                    <strong>${result.overall}</strong>
                    <span>/100</span>
                  </div>
                </div>
                <div class="gauge-label">${overallLabel(result.overall)}</div>
              </div>
            </div>
            <div class="r-card">
              <div class="card-label">Risk categories</div>
              <div id="score-bars-wrap">${renderScoreBars(result.scores)}</div>
            </div>
            <div class="r-card">
              <div class="card-label">Spider graph</div>
              <canvas id="risk-radar" class="radar-canvas" width="340" height="300"></canvas>
            </div>
          </div>
        </div>
        <div class="result-section">
          <div class="result-section-head">
            <div class="result-section-bar"></div>
            <div class="result-section-title">Top risk drivers</div>
          </div>
          <div class="drivers-grid">
            ${renderDriverCards((result.top_risks||[]).slice(0,3))}
          </div>
        </div>
        <details class="expander-card" style="margin-bottom:14px;">
          <summary>Score breakdown — multipliers applied</summary>
          <div class="expander-body">${renderBreakdown(result.multiplier_breakdown)}</div>
        </details>

        <!-- Methodology button + panel -->
        <div style="text-align:center;margin:32px 0 12px;">
          <button id="methodology-btn" onclick="toggleMethodology()" style="display:inline-flex;align-items:center;gap:10px;background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);color:#fff;border:none;padding:14px 32px;border-radius:10px;font-size:14px;font-weight:700;cursor:pointer;letter-spacing:.03em;box-shadow:0 4px 16px rgba(15,23,42,.25);transition:box-shadow .2s,transform .1s;" onmouseover="this.style.boxShadow='0 8px 28px rgba(15,23,42,.35)';this.style.transform='translateY(-1px)'" onmouseout="this.style.boxShadow='0 4px 16px rgba(15,23,42,.25)';this.style.transform=''">
            <span style="font-size:16px;">🔬</span>
            <span>How was this calculated? — Full 21-step methodology</span>
            <span style="font-size:11px;background:rgba(255,255,255,.15);border-radius:4px;padding:2px 7px;">▼ expand</span>
          </button>
        </div>
        <div id="methodology-panel" style="display:none">
          ${renderMethodologyPanel(result)}
        </div>
      </div>

      <!-- ── TAB: Actions ── -->
      <div class="tab-panel" id="tab-triggers" style="display:none">
        <div class="result-section two-col">
          <div class="r-card">
            <div class="card-label">Regulatory triggers</div>
            ${renderTriggers(result.regulatory_triggers)}
          </div>
          <div class="r-card">
            <div class="card-label">Non-insurance actions</div>
            ${renderMitigations(result.mitigations)}
          </div>
        </div>
        ${renderDownstream(result.downstream_opportunities)}
        <details class="expander-card" style="margin-bottom:14px;">
          <summary>Global products — how SPARC compares</summary>
          <div class="expander-body">
            <div class="products-grid">${renderGlobalProducts(result.global_products)}</div>
          </div>
        </details>
        ${renderCustomTriggers(result.custom_triggers)}
        <details class="expander-card" style="margin-bottom:24px;">
          <summary>Assumptions used</summary>
          <div class="expander-body">
            <div class="kv-grid">${renderAssumptions(result.assumptions)}</div>
          </div>
        </details>
        <details class="refine-panel-wrap" style="margin-bottom:24px;">
          <summary>⚙ Refine profile — adjust to sharpen scores</summary>
          <div class="refine-body" id="refine-body">
            ${renderRefineBody()}
          </div>
        </details>
        ${renderPolicyWordingComparison(result)}
      </div>

    </div>`;

  // Store result globally for download
  window.__result = result;
  window.__refineResult = result;

  // Persist to sessionStorage so Vercel live-reloads don't wipe the session
  try { sessionStorage.setItem("sparc_last_result", JSON.stringify(result)); } catch (_) {}

  // Bind product row expand/collapse
  window.toggleProductRow = (i) => {
    const row = document.getElementById(`prow-${i}`);
    if (row) row.classList.toggle('expanded');
  };

  // Bind refine
  bindRefine();
  bindPolicyWordingUpload();
  bindEstimateQuotePanel(result.profile);

  // Bind outreach buttons (fallback already rendered)
  const outreachDynEl = document.getElementById("outreach-dynamic");
  if (outreachDynEl) _bindOutreachButtons(outreachDynEl);

  // Draw radar — deferred so the canvas exists in DOM
  setTimeout(() => drawRadar("risk-radar", result.scores, { maxLabelLength: 16 }), 100);

  // Overdrive: scroll-reveal + number shock
  setTimeout(setupScrollReveal, 80);

  // Activate default tab — go directly to outreach sub-tab if signal context is set
  if (result.signal_context) {
    showTab("outreach");
    showOutreachSubTab("signal");
  } else {
    showTab("bundle");
  }
}

/* ─── TAB NAVIGATION ─────────────────────────────────────────── */
window.__outreachLoaded = false;

function _buildAdvPanel(loading) {
  return `
    <div class="adv-panel-backdrop" onclick="closeAdvancedPanel()"></div>
    <div class="adv-panel-drawer">
      <div class="adv-panel-head">
        <div class="adv-panel-title">Refine risk inputs</div>
        <div class="adv-panel-subtitle">AI-estimated advanced signals — governance, gig exposure, data/AI tier, physical assets. Adjust any value then recalculate.</div>
        <button class="adv-panel-close" onclick="closeAdvancedPanel()" aria-label="Close">✕</button>
      </div>
      <div class="adv-panel-body" id="adv-panel-body">
        ${loading
          ? `<div class="adv-panel-loading"><div class="loading-ring" style="width:32px;height:32px;"></div><span>AI is estimating advanced inputs…</span></div>`
          : renderSectionAdvanced()}
      </div>
      <div class="adv-panel-footer">
        <button class="adv-panel-cancel" onclick="closeAdvancedPanel()">Cancel</button>
        <button class="adv-panel-recalc" id="adv-recalc-btn" onclick="recalcFromAdvanced()" ${loading ? "disabled" : ""}>Recalculate risk score →</button>
      </div>
    </div>`;
}

async function openAdvancedPanel() {
  const existing = document.getElementById("adv-refine-panel");
  if (existing) { closeAdvancedPanel(); return; }
  if (window.__result?.profile) state.profile = structuredClone(window.__result.profile);

  const panel = document.createElement("div");
  panel.id = "adv-refine-panel";
  panel.innerHTML = _buildAdvPanel(true);
  document.body.appendChild(panel);
  requestAnimationFrame(() => panel.querySelector(".adv-panel-drawer").classList.add("adv-panel-open"));

  const companyName = state.profile?.startup_name || window.__result?.profile?.startup_name || "";
  try {
    const res = await fetch("/api/autofill-advanced", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_name: companyName, profile: state.profile }),
    });
    const data = await res.json();
    if (data.fields && Object.keys(data.fields).length) {
      Object.assign(state.profile, data.fields);
    }
  } catch (_) {}

  const body = document.getElementById("adv-panel-body");
  const recalc = document.getElementById("adv-recalc-btn");
  if (body) body.innerHTML = renderSectionAdvanced();
  if (recalc) { recalc.disabled = false; recalc.textContent = "Recalculate risk score →"; }
}

function closeAdvancedPanel() {
  const panel = document.getElementById("adv-refine-panel");
  if (!panel) return;
  const drawer = panel.querySelector(".adv-panel-drawer");
  drawer.classList.remove("adv-panel-open");
  drawer.addEventListener("transitionend", () => panel.remove(), { once: true });
}

async function recalcFromAdvanced() {
  const btn = document.getElementById("adv-recalc-btn");
  if (btn) { btn.textContent = "Recalculating…"; btn.disabled = true; }
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state.profile),
    });
    const result = await res.json();
    if (!res.ok || result.error) throw new Error(result.error || "Analysis failed");
    closeAdvancedPanel();
    renderResults(result);
  } catch (err) {
    if (btn) { btn.textContent = "Recalculate risk score →"; btn.disabled = false; }
  }
}

window.showTab = (id) => {
  document.querySelectorAll(".tab-panel").forEach(p => { p.style.display = "none"; });
  document.querySelectorAll(".snav-pill").forEach(p => p.classList.remove("snav-active"));
  const panel = document.getElementById("tab-" + id);
  if (panel) panel.style.display = "";
  const btn = document.getElementById("snav-" + id);
  if (btn) btn.classList.add("snav-active");
  if (id === "risk" && window.__result) {
    setTimeout(() => drawRadar("risk-radar", window.__result.scores, { maxLabelLength: 16 }), 50);
  }
  if (id === "outreach" && !window.__outreachLoaded && window.__result) {
    window.__outreachLoaded = true;
    loadOutreachTab(window.__result);
  }
};

window.showOutreachSubTab = (id) => {
  document.querySelectorAll(".ot-sub-panel").forEach(p => { p.style.display = "none"; });
  document.querySelectorAll(".ot-sub-pill").forEach(p => p.classList.remove("ot-sub-active"));
  const panel = document.getElementById("ot-panel-" + id);
  if (panel) panel.style.display = "";
  const btn = document.getElementById("ot-sub-" + id);
  if (btn) btn.classList.add("ot-sub-active");
};

function _bindOutreachButtons(container) {
  container.querySelectorAll("[data-copy]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await navigator.clipboard?.writeText(btn.dataset.copy || "");
      const orig = btn.textContent;
      btn.textContent = "Copied ✓";
      setTimeout(() => btn.textContent = orig, 1800);
    });
  });
  container.querySelectorAll(".il-send-email-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const item = _outreachItems[btn.dataset.key] || {};
      openEmailModal(item.email_subject || "", item.email_body || "", item.email_html_data, window.__result?.profile?.contact_email || "");
    });
  });
}

function _bindSignalOutreachButtons(container, sigCtx, outreachPrompts) {
  // Standard copy/send bindings
  _bindOutreachButtons(container);
  // Add "Copy signal email HTML" button behaviour
  container.querySelectorAll(".ot-copy-signal-email").forEach(btn => {
    btn.addEventListener("click", async () => {
      const key = btn.dataset.key || Object.keys(outreachPrompts || {})[0] || "";
      const item = (outreachPrompts || {})[key] || {};
      openSignalOutreachEmail(sigCtx, item);
    });
  });
}

async function loadOutreachTab(result) {
  const dynamicEl = document.getElementById("outreach-dynamic");
  const staticEl  = document.getElementById("outreach-static");
  if (!dynamicEl) return;

  // Inject progress loader
  const banner = document.createElement("div");
  banner.id = "outreach-ai-loader";
  banner.className = "outreach-ai-loader";
  banner.innerHTML =
    `<div class="oal-header">` +
      `<span class="oal-label">Generating AI drafts for all covers</span>` +
      `<span class="oal-pct" id="oal-pct">0%</span>` +
    `</div>` +
    `<div class="oal-track"><div class="oal-bar" id="oal-bar"></div></div>`;
  dynamicEl.prepend(banner);

  // Eased fake-progress: fast to 40%, then slow crawl to 90% over ~25s
  let pct = 0;
  const pctEl = document.getElementById("oal-pct");
  const barEl = document.getElementById("oal-bar");
  const _setProgress = (v) => {
    pct = Math.min(v, 99);
    if (pctEl) pctEl.textContent = Math.round(pct) + "%";
    if (barEl) barEl.style.width = pct + "%";
  };
  const startTs = Date.now();
  const _tick = () => {
    const elapsed = (Date.now() - startTs) / 1000;
    // fast phase 0-6s → 0-40%, slow phase 6-30s → 40-90%
    const target = elapsed < 6
      ? (elapsed / 6) * 40
      : 40 + ((elapsed - 6) / 24) * 50;
    _setProgress(target);
    if (pct < 99) _progressTimer = setTimeout(_tick, 200);
  };
  let _progressTimer = setTimeout(_tick, 200);

  // Render signal context card if signal context is present
  const sigCtx = result.signal_context;
  const sigCtxEl = document.getElementById("signal-outreach-context");
  if (sigCtx && sigCtxEl) {
    const regBadge = sigCtx.regulation_tag
      ? `<span class="signal-reg-badge reg-${escHtml(String(sigCtx.regulation_tag).toLowerCase())}">${escHtml(sigCtx.regulation_tag)}</span>` : "";
    sigCtxEl.innerHTML =
      `<div class="ot-signal-card">` +
        `<div class="ot-signal-head">` +
          `<span class="signal-type">${escHtml(sigCtx.signal || "Signal")}</span>` +
          regBadge +
          (sigCtx.confidence ? `<span class="signal-confidence">${escHtml(String(sigCtx.confidence))}% confidence</span>` : "") +
        `</div>` +
        `<p class="ot-signal-headline">${escHtml(sigCtx.headline || "")}</p>` +
        `<div class="ot-signal-meta">` +
          `<span><strong>Insurance angle:</strong> ${escHtml(sigCtx.insurance_angle || "")}</span>` +
          `<span><strong>Bundle:</strong> ${escHtml(sigCtx.recommended_bundle || "")}</span>` +
        `</div>` +
      `</div>`;
  }

  try {
    const res = await fetch("/api/outreach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile: result.profile,
        scores: result.scores,
        recommendations: result.recommendations,
        bundle_match: result.bundle_match,
        display_regulatory_triggers: result.display_regulatory_triggers,
        regulatory_triggers_fired: result.regulatory_triggers_fired,
        signal_context: result.signal_context || {},
      }),
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.error || `API ${res.status}`);
    }
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    clearTimeout(_progressTimer);
    _setProgress(100);
    window.__result.outreach_prompts   = data.outreach_prompts;
    window.__result.outreach_source    = data.outreach_source;
    window.__result.outreach_error     = data.outreach_error;
    window.__result.objection_handlers = data.objection_handlers;
    if (data.pitch?.bullets?.length) {
      window.__result.pitch_bullets = data.pitch.bullets;
      window.__result.pitch_meta    = {
        trigger_question: data.pitch.trigger_question || "",
        best_timing:      data.pitch.best_timing      || "",
      };
    }
    if (staticEl) staticEl.innerHTML = renderFounderPitch(window.__result);
    await new Promise(r => setTimeout(r, 300)); // let 100% flash briefly

    // Render company sub-tab drafts
    dynamicEl.innerHTML = renderOutreach(data.outreach_prompts, data.outreach_source, data.outreach_error);
    _bindOutreachButtons(dynamicEl);

    // Render signal sub-tab drafts if signal context present
    const sigDynEl = document.getElementById("signal-outreach-dynamic");
    if (sigCtx && sigDynEl) {
      const firstKey = Object.keys(data.outreach_prompts || {})[0] || "";
      sigDynEl.innerHTML =
        `<button class="ot-copy-signal-email ot-sub-pill ot-sub-active" type="button" data-key="${escHtml(firstKey)}" style="margin-bottom:18px;">` +
          `Copy signal email HTML` +
        `</button>` +
        renderOutreach(data.outreach_prompts, data.outreach_source, data.outreach_error);
      _bindSignalOutreachButtons(sigDynEl, sigCtx, data.outreach_prompts);
    }
  } catch (err) {
    clearTimeout(_progressTimer);
    _setProgress(100);
    await new Promise(r => setTimeout(r, 300));
    // Show static pitch and a non-blocking retry notice — don't block the whole tab
    if (staticEl) staticEl.innerHTML = renderFounderPitch(result);
    const loader = document.getElementById("outreach-ai-loader");
    if (loader) {
      loader.innerHTML =
        `<div class="oal-header oal-error" style="margin-bottom:8px;">` +
          `<span class="oal-label">AI email drafts unavailable (Gemini busy). </span>` +
          `<button class="oal-retry-btn" type="button" id="oal-retry">Retry</button>` +
        `</div>`;
      document.getElementById("oal-retry")?.addEventListener("click", () => {
        window.__outreachLoaded = false;
        loadOutreachTab(window.__result);
      });
    }
    if (dynamicEl) dynamicEl.innerHTML = renderOutreach(result.outreach_fallback || {}, "fallback", null);
  }
}

/* ─── METHODOLOGY PANEL ──────────────────────────────────────────── */
async function openSignalOutreachEmail(sigCtx, outreachItem) {
  let template = "";
  try {
    const res = await fetch("/email-template-signal-outreach.html");
    if (res.ok) template = await res.text();
  } catch (_) {}
  if (!template) {
    alert("Signal email template not found.");
    return;
  }
  const profile = window.__result?.profile || {};
  const filled = template
    .replace(/\{\{SIGNAL_TYPE\}\}/g, escHtml(sigCtx.signal || ""))
    .replace(/\{\{REGULATION_BADGE\}\}/g, escHtml(sigCtx.regulation_tag || ""))
    .replace(/\{\{HEADLINE\}\}/g, escHtml(sigCtx.headline || ""))
    .replace(/\{\{COMPANY_NAME\}\}/g, escHtml(sigCtx.company_name || profile.startup_name || ""))
    .replace(/\{\{EMAIL_SUBJECT\}\}/g, escHtml(outreachItem.email_subject || ""))
    .replace(/\{\{EMAIL_BODY\}\}/g, (outreachItem.email_body || "").replace(/\n/g, "<br>"))
    .replace(/\{\{INSURANCE_ANGLE\}\}/g, escHtml(sigCtx.insurance_angle || ""))
    .replace(/\{\{PREHEADER_TEXT\}\}/g, escHtml(outreachItem.email_subject || sigCtx.signal || ""))
    .replace(/\{\{CTA_URL\}\}/g, "")
    .replace(/\{\{CTA_TEXT\}\}/g, "Schedule a call")
    .replace(/\{\{RM_NAME\}\}/g, "Your Name")
    .replace(/\{\{RM_TITLE\}\}/g, "Relationship Manager, ICICI Lombard")
    .replace(/\{\{RM_PHONE\}\}/g, "+91 XXXXX XXXXX")
    .replace(/\{\{RM_EMAIL\}\}/g, "rm@icicilombard.com");
  try {
    await navigator.clipboard.writeText(filled);
    // Brief toast
    const toast = document.createElement("div");
    toast.className = "ot-toast";
    toast.textContent = "Signal email HTML copied to clipboard";
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
  } catch (_) {
    alert("Clipboard write failed — try copying manually.");
  }
}

window.toggleMethodology = () => {
  const panel = document.getElementById("methodology-panel");
  const btn   = document.getElementById("methodology-btn");
  if (!panel) return;
  const hidden = panel.style.display === "none";
  panel.style.display = hidden ? "" : "none";
  const tag = btn.querySelector("span:last-child");
  const lbl = btn.querySelector("span:nth-child(2)");
  if (tag) tag.textContent = hidden ? "▲ collapse" : "▼ expand";
  if (lbl) lbl.textContent = hidden ? "Hide methodology" : "How was this calculated? — Full 21-step methodology";
  btn.style.background = hidden
    ? "linear-gradient(135deg,#B91C1C 0%,#DC2626 100%)"
    : "linear-gradient(135deg,#0F172A 0%,#1E293B 100%)";
  if (hidden) {
    setTimeout(() => {
      const top = panel.getBoundingClientRect().top + window.scrollY - 80;
      window.scrollTo({ top, behavior: "smooth" });
    }, 60);
  }
};

function renderMethodologyPanel(result) {
  const p      = result.profile || {};
  const scores = result.scores  || {};
  const recs   = result.recommendations || [];
  const bundle = result.bundle_match;

  /* ── Static sector base weights (mirrors risk_engine.py SECTOR_PROFILES) ── */
  const SW = {
    "SaaS / Enterprise Software": { cyber_technical:8,data_privacy:8,liability:8,ip_infringement:7,key_person:5,governance_fraud:5,property:2,regulatory_compliance:8,esg_climate:2,geopolitical:6,gig_labour:2,policy_velocity:6,reputation:6 },
    "Fintech":                    { cyber_technical:10,data_privacy:10,liability:9,ip_infringement:5,key_person:8,governance_fraud:9,property:3,regulatory_compliance:10,esg_climate:3,geopolitical:8,gig_labour:5,policy_velocity:9,reputation:9 },
    "Healthtech":                 { cyber_technical:10,data_privacy:9,liability:9,ip_infringement:8,key_person:6,governance_fraud:7,property:5,regulatory_compliance:9,esg_climate:4,geopolitical:6,gig_labour:5,policy_velocity:8,reputation:8 },
    "D2C / Consumer Brands":      { cyber_technical:7,data_privacy:6,liability:8,ip_infringement:6,key_person:4,governance_fraud:7,property:8,regulatory_compliance:9,esg_climate:6,geopolitical:9,gig_labour:6,policy_velocity:5,reputation:8 },
    "Deeptech / AI / Robotics":   { cyber_technical:7,data_privacy:7,liability:7,ip_infringement:10,key_person:8,governance_fraud:5,property:7,regulatory_compliance:8,esg_climate:7,geopolitical:10,gig_labour:2,policy_velocity:7,reputation:6 },
    "Edtech":                     { cyber_technical:7,data_privacy:8,liability:8,ip_infringement:6,key_person:7,governance_fraud:10,property:3,regulatory_compliance:9,esg_climate:2,geopolitical:6,gig_labour:4,policy_velocity:7,reputation:9 },
    "Agritech":                   { cyber_technical:4,data_privacy:5,liability:6,ip_infringement:4,key_person:5,governance_fraud:6,property:8,regulatory_compliance:8,esg_climate:9,geopolitical:5,gig_labour:5,policy_velocity:5,reputation:4 },
    "Cleantech / Climatetech":    { cyber_technical:5,data_privacy:4,liability:7,ip_infringement:7,key_person:6,governance_fraud:6,property:9,regulatory_compliance:9,esg_climate:10,geopolitical:7,gig_labour:3,policy_velocity:5,reputation:6 },
    "Logistics / Mobility":       { cyber_technical:6,data_privacy:6,liability:10,ip_infringement:3,key_person:4,governance_fraud:5,property:8,regulatory_compliance:10,esg_climate:8,geopolitical:6,gig_labour:10,policy_velocity:4,reputation:7 },
    "Legaltech":                  { cyber_technical:7,data_privacy:8,liability:9,ip_infringement:7,key_person:5,governance_fraud:4,property:2,regulatory_compliance:9,esg_climate:1,geopolitical:3,gig_labour:3,policy_velocity:7,reputation:8 },
    "HRtech":                     { cyber_technical:8,data_privacy:9,liability:6,ip_infringement:4,key_person:5,governance_fraud:5,property:2,regulatory_compliance:9,esg_climate:2,geopolitical:4,gig_labour:8,policy_velocity:6,reputation:7 },
    "Gaming / Media / Content":   { cyber_technical:6,data_privacy:7,liability:9,ip_infringement:8,key_person:5,governance_fraud:8,property:3,regulatory_compliance:10,esg_climate:2,geopolitical:7,gig_labour:2,policy_velocity:10,reputation:9 },
    "Foodtech / Cloud Kitchen":   { cyber_technical:6,data_privacy:6,liability:9,ip_infringement:4,key_person:4,governance_fraud:6,property:8,regulatory_compliance:10,esg_climate:7,geopolitical:5,gig_labour:10,policy_velocity:6,reputation:10 },
  };

  /* ── Per-sector category reasons (key highlights only) ── */
  const WHY = {
    "Fintech":{ "Cyber Technical Risk":"BFSI is India's #1 targeted sector; card/internet fraud +334% YoY in FY24","Data Privacy Risk":"Likely SDF designation; DPDPA §33 ₹250cr penalty; 72-hr breach notification","Governance & Fraud Risk":"Fraud losses 8× in H1 FY25 to ₹21,367cr; BharatPe EOW FIR (₹81.3cr fake-vendor fraud)","Regulatory Compliance Risk":"8+ major RBI circulars in 2024; Paytm §35A enforcement precedent","Policy Velocity Risk":"Highest regulatory circular frequency of any Indian sector","Geopolitical Risk":"PN3 + RBI data localisation + cross-border settlement rules","Key Person Risk":"RBI Fit & Proper — regulator can replace CEO (Paytm Jan-2024 precedent)","Liability Risk":"Consumer Protection Act strict liability; fintech platforms = deemed RE","Reputation Risk":"Trust-dependent sector; single breach collapses user acquisition" },
    "Healthtech":{ "Cyber Technical Risk":"Star Health breach Sep-2024: 31M health records exposed on Telegram","Data Privacy Risk":"DPDPA health-data SPDI; Jan-2025 draft rules — no special health-data carve-out","Liability Risk":"5.2M medical negligence cases/year; 80% surgical procedures","IP Infringement Risk":"Pharma + medical device patents; AI diagnostics creating new patent disputes","Regulatory Compliance Risk":"CDSCO SaMD Class B/C/D mandatory licensing; NABL accreditation" },
    "D2C / Consumer Brands":{ "Property Risk":"Warehouse fire/flood in D2C corridors; logistics costs 10–18% of revenue","Geopolitical Risk":"D2C funding down 54% from 2022 peak; Chinese supplier CBAM exposure","Regulatory Compliance Risk":"BIS QCO + LMPC + EPR; FSSAI per-SKU licensing","Liability Risk":"NCDRC Honda 2024 — strict liability for product defects on manufacturer","Reputation Risk":"Viral social media incidents (MDH/Everest ban, Zepto finger-in-ice-cream 2024)" },
    "Deeptech / AI / Robotics":{ "IP Infringement Risk":"ANI v. OpenAI Delhi HC 2024 — first AI copyright case; personality rights","Geopolitical Risk":"Dual-use export controls (DGFT) + PN3 = dual exposure","Policy Velocity Risk":"MeitY AI Advisory revised twice in 15 days (Mar 2024)","Key Person Risk":"Typically built around 1–2 founding scientists with no substitutes" },
    "Logistics / Mobility":{ "Gig & Labour Risk":"5M+ delivery workers; 24% accident rate; Karnataka/Rajasthan gig Acts impose levy","Liability Risk":"MV Act §149 unlimited TP liability; 36% of road deaths on national highways","Regulatory Compliance Risk":"MV Aggregator Guidelines 2025 — ₹5L health + ₹10L term per driver mandatory" },
    "Edtech":{ "Governance & Fraud Risk":"Byju's: Prosus wrote off $500M; 3 investors left board; NCLT admission Jul-2024","Reputation Risk":"60% of parents now seek refunds from edtech platforms post-Byju's collapse","Data Privacy Risk":"DPDPA §9 — ₹200cr penalty for minor data without verifiable parental consent" },
    "Gaming / Media / Content":{ "Policy Velocity Risk":"Online Gaming Act 2025 (assented 22-Aug-2025) disrupted an entire sector in months","Governance & Fraud Risk":"DGGI detected ₹81,875cr GST evasion in online gaming FY24","Regulatory Compliance Risk":"118 operators issued show-cause notices; 658 offshore entities under investigation" },
    "Foodtech / Cloud Kitchen":{ "Gig & Labour Risk":"Zomato/Swiggy rider deaths documented 2024; gig workforce = majority of headcount","Reputation Risk":"Zepto finger-in-ice-cream 2024; April 2024 survey: majority have low/no FSSAI confidence","Regulatory Compliance Risk":"18,000+ FSSAI enforcement actions 2024; AI-based FoSCoS inspections expanding" },
    "Cleantech / Climatetech":{ "ESG & Climate Risk":"ALMM List-II for solar cells Jun-2026; EPR phased through FY2028; CCTS carbon market live","Geopolitical Risk":"CBAM — India among largest payers alongside China and Russia","Property Risk":"Installed hardware + lender covenants frequently require fire or all-risk cover" },
    "Agritech":{ "ESG & Climate Risk":"35M hectares lost to drought (2015–21); 33.9M to excess rain; food inflation doubled","Property Risk":"65% of Indian farmland is rainfed; crop/equipment loss endemic and escalating" },
    "SaaS / Enterprise Software":{ "Cyber Technical Risk":"boAt (7.5M records), Hathway (41.5M records), BSNL SIM data — all breached in 2024","Data Privacy Risk":"DPDPA SDF likely at scale; CERT-In 72-hr breach notification mandatory","Liability Risk":"SLA breach and outage claims from enterprise clients; PI contractual exposure" },
    "HRtech":{ "Data Privacy Risk":"Payroll + biometric + health data = triple DPDPA Sensitive Personal Data exposure","Gig & Labour Risk":"HRtech platforms managing gig payrolls face SS Code §113–114 aggregator levy" },
    "Legaltech":{ "Liability Risk":"AI-legal advice liability; Advocates Act unauthorised-practice risk","Data Privacy Risk":"Privileged-data + client confidentiality creates DPDPA Sensitive Data exposure" },
  };

  const sW   = SW[p.sector] || {};
  const sWhy = WHY[p.sector] || {};

  /* ── Citation accumulator ── */
  const refs = [];
  const cite = (...sources) => sources.map(s => {
    if (!refs.includes(s)) refs.push(s);
    return `<sup class="mcite">[${refs.indexOf(s)+1}]</sup>`;
  }).join("");

  const mh  = cols => `<tr>${cols.map(c=>`<th>${esc(c)}</th>`).join("")}</tr>`;
  const act = flag => flag ? ' class="m-active-row"' : "";
  const catKeys = ["Cyber Technical Risk","Data Privacy Risk","Liability Risk","IP Infringement Risk","Key Person Risk","Governance & Fraud Risk","Property Risk","Regulatory Compliance Risk","ESG & Climate Risk","Geopolitical Risk","Gig & Labour Risk","Policy Velocity Risk","Reputation Risk"];
  const catShort = { "Cyber Technical Risk":"cyber_technical","Data Privacy Risk":"data_privacy","Liability Risk":"liability","IP Infringement Risk":"ip_infringement","Key Person Risk":"key_person","Governance & Fraud Risk":"governance_fraud","Property Risk":"property","Regulatory Compliance Risk":"regulatory_compliance","ESG & Climate Risk":"esg_climate","Geopolitical Risk":"geopolitical","Gig & Labour Risk":"gig_labour","Policy Velocity Risk":"policy_velocity","Reputation Risk":"reputation" };

  const ts = p.team_size || 10;
  const tlf = (0.85 + 0.08 * Math.log1p(ts / 10)).toFixed(3);
  let kpM, tM;
  if      (ts <=  5) { kpM=1.5;  tM=0.8;  }
  else if (ts <= 10) { kpM=1.4;  tM=1.0;  }
  else if (ts <= 20) { kpM=1.2;  tM=1.0;  }
  else if (ts <= 50) { kpM=1.0;  tM=1.15; }
  else if (ts <=150) { kpM=0.85; tM=1.30; }
  else               { kpM=0.7;  tM=1.50; }

  const OPS = {
    "Digital-only":  { property:"0.4", liability:"0.8", cyber:"1.2", gig:"0.6" },
    "Physical-only": { property:"1.4", liability:"1.2", cyber:"0.7", gig:"1.3" },
    "Hybrid":        { property:"1.0", liability:"1.0", cyber:"1.0", gig:"1.0" },
  };
  const om = OPS[p.operations] || OPS["Hybrid"];

  const steps = [];

  /* ── STEP 1 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">1</span><span class="m-step-title">Base sector weight — ${esc(p.sector||"Unknown")} (scored out of 10 per category)</span></div>
    <p class="m-p">Each of the 13 risk categories is expert-scored for every sector using Indian regulatory enforcement data, actuarial loss statistics, and research literature. These are the starting weights for <strong>${esc(p.sector||"this sector")}</strong>:</p>
    <table class="m-table"><thead>${mh(["Risk category","Base weight /10","Key reason"])}</thead><tbody>
    ${catKeys.map(cat => {
      const k = catShort[cat]; const w = sW[k]!==undefined ? sW[k] : "—"; const why = sWhy[cat]||"";
      return `<tr><td>${esc(cat)}</td><td style="text-align:center;font-weight:700;">${w}</td><td style="font-size:11px;color:var(--ink-muted);">${esc(why)}</td></tr>`;
    }).join("")}
    </tbody></table>
    <p class="m-cite">${cite("CERT-In Annual Report 2025 — 29.44 lakh cyber incidents recorded; BFSI ranked #1 targeted sector","IBM Cost of a Data Breach India 2024 — average breach cost ₹19.5 crore (+9% YoY)","RBI Circular Index 2024 — 8+ major circulars; SRO framework; CIMS reporting","BioCatch / RBI Fraud Trends H1 FY25 — fraud losses 8× to ₹21,367 crore","DPDPA 2023 (Act 22 of 2023) — §33 ₹250cr maximum penalty per breach","CERT-In Directions No. 20(3)/2022-CERT-In (28-Apr-2022) — 6-hour breach notification; 180-day log retention")}</p>
  </div>`);

  /* ── STEP 2 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">2</span><span class="m-step-title">Stage multiplier — controls exposure scaling across the funding lifecycle</span></div>
    <p class="m-p">Later-stage companies have larger attack surfaces, more employees, stronger regulatory scrutiny, and greater investor stakes. The default multiplier scales risk linearly. Governance and Policy Velocity use separate curves.</p>
    <table class="m-table"><thead>${mh(["Stage","Default multiplier","Logic"])}</thead><tbody>
      <tr${act(p.funding_stage==="Pre-seed")}><td>Pre-seed</td><td>0.70</td><td>Tiny team, limited exposure surface, minimal regulatory radar</td></tr>
      <tr${act(p.funding_stage==="Seed")}><td>Seed</td><td>0.90</td><td>Growing but still lean; some contractual exposure emerging</td></tr>
      <tr${act(p.funding_stage==="Series A")}><td>Series A</td><td>1.10</td><td>Institutional investors + growing team + enterprise customer contracts</td></tr>
      <tr${act(p.funding_stage==="Series B+")}><td>Series B+</td><td>1.30</td><td>Complex governance, regulatory scrutiny, larger public profile and blast radius</td></tr>
    </tbody></table>
    <p class="m-p" style="margin-top:10px;"><strong>Governance</strong> uses a U-shaped curve: 0.90 at Pre-seed (founder concentration), 0.85 at Seed, 1.00 at A, 1.30 at B+ (more stakeholders = more governance surface). <strong>Policy Velocity</strong> is inverted — Pre-seed = 1.10, Series A = 0.95 — because large companies have legal and lobbying buffers; startups feel regulatory shocks directly and immediately.</p>
    <p class="m-cite">${cite("Swiss Re sigma No. 1/2024 — SME liability exposure scales with company maturity and stakeholder count","SEBI Listing Obligations & Disclosure Requirements Regulations 2015 — Reg 17 board composition obligations at scale")}</p>
  </div>`);

  /* ── STEP 3 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">3</span><span class="m-step-title">Operations multiplier — ${esc(p.operations||"Hybrid")}</span></div>
    <p class="m-p">How a company operates fundamentally changes which risks dominate. A delivery fleet has opposite cyber-vs-property risk to a cloud-only SaaS app.</p>
    <table class="m-table"><thead>${mh(["Operations type","Property","Liability","Cyber","Gig & Labour"])}</thead><tbody>
      ${["Digital-only","Hybrid","Physical-only"].map(op => { const m=OPS[op]; return `<tr${act(op===p.operations)}><td>${esc(op)}</td><td>${m.property}</td><td>${m.liability}</td><td>${m.cyber}</td><td>${m.gig}</td></tr>`; }).join("")}
    </tbody></table>
    <p class="m-p" style="margin-top:10px;"><strong>${esc(p.operations||"Hybrid")}</strong>: Cyber ×${om.cyber}, Property ×${om.property}, Liability ×${om.liability}, Gig & Labour ×${om.gig}.</p>
    <p class="m-cite">${cite("CERT-In Annual Report 2025 — 87% of incidents target cloud-hosted, API-first, and digital-only companies","NDMA Climate Hazard Atlas — physical property incident classification by exposure zone","TRIP Centre IIT Delhi Road Safety Report 2024 — national highways = 36% of all road deaths; physical ops liability")}</p>
  </div>`);

  /* ── STEP 4 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">4</span><span class="m-step-title">Data sensitivity multiplier — ${esc(p.data_sensitivity||"Medium")}</span></div>
    <p class="m-p">Data sensitivity determines how exposed the startup is to DPDPA penalties, cyber-breach costs, and regulatory compliance obligations. High sensitivity (payments, health, biometrics, KYC) triggers the steepest multipliers.</p>
    <table class="m-table"><thead>${mh(["Sensitivity level","Cyber multiplier","Data Privacy multiplier","Compliance multiplier"])}</thead><tbody>
      <tr${act(p.data_sensitivity==="Low")}><td>Low</td><td>0.6</td><td>0.5</td><td>0.8</td></tr>
      <tr${act(p.data_sensitivity==="Medium")}><td>Medium</td><td>1.0</td><td>1.0</td><td>1.0</td></tr>
      <tr${act(p.data_sensitivity==="High")}><td>High</td><td>1.4</td><td><strong>1.5</strong></td><td>1.3</td></tr>
    </tbody></table>
    <p class="m-p" style="margin-top:10px;">Data Privacy gets the steepest high-sensitivity multiplier (1.5×) because DPDPA §33 imposes ₹250 crore per breach specifically for <em>Sensitive Personal Data</em> — payment data, health records, biometrics, and KYC identifiers.</p>
    <p class="m-cite">${cite("DPDPA 2023 §33 — ₹250 crore maximum penalty per breach of sensitive personal data","DPDP Rules G.S.R. 846(E) notified 13-Nov-2025 — SDF designation, algorithmic audit obligations, and data localisation","IBM Cost of a Data Breach India 2024 — breaches involving regulated data cost 2.3× more than non-regulated","Surfshark Data Breach Report 2024 — India ranked 5th globally by volume of personal data records breached")}</p>
  </div>`);

  /* ── STEP 5 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">5</span><span class="m-step-title">Dynamic adjusters — profile-specific regulatory signals</span></div>
    <p class="m-p">These adjusters fire only when specific advanced inputs are declared. Each is derived from a concrete regulation or empirical loss data point — they make the risk score responsive to the startup's actual operating model rather than just its sector label.</p>
    <table class="m-table"><thead>${mh(["Input signal","Categories elevated","Formula","Legal / actuarial basis"])}</thead><tbody>
      <tr><td>SDF probability (0–1)</td><td>Data Privacy ↑</td><td>1.0 + (prob × 0.5)</td><td>DPDPA §10 Significant Data Fiduciary designation</td></tr>
      <tr><td>Chinese investor / supplier %</td><td>Geopolitical ↑</td><td>1.0 + (inv% × 0.8) + (supplier% × 0.4)</td><td>DPIIT Press Note 3 (17-Apr-2020); PN2 2026-series</td></tr>
      <tr><td>Gig headcount %</td><td>Gig & Labour ↑</td><td>1.0 + (gig% × 1.2)</td><td>SS Code 2020 §§113–114; NITI Aayog Gig Economy 2024</td></tr>
      <tr><td>Gig state footprint (KA/RJ/BR/JH/TG)</td><td>Gig & Labour ↑ additional</td><td>×1.25 cap if gig% > 10%</td><td>Karnataka / Rajasthan / Bihar / Jharkhand Gig Acts 2023–25</td></tr>
      <tr><td>Hardware revenue %</td><td>Property ↑ · Compliance ↑</td><td>1.0 + (hw% × 0.6)</td><td>BIS QCO IS 17043/15844 (1-Aug-2024); BEE energy standards</td></tr>
      <tr><td>EU export %</td><td>ESG & Climate ↑</td><td>1.0 + (eu% × 1.5)</td><td>CBAM Regulation 2023/956 — definitive phase 1-Jan-2026</td></tr>
      <tr><td>AI in product = Yes</td><td>Policy Velocity ↑ · Compliance ↑</td><td>Fixed ×1.3</td><td>MeitY AI Advisory 15-Mar-2024; SGI Rules 10-Feb-2026; EU AI Act Art 2(1)(c)</td></tr>
      <tr><td>Founder concentration index</td><td>Governance ↑</td><td>1.0 + (index × 0.5)</td><td>Companies Act 2013 §2(60) officer-in-default; SEBI Listing Reg 17</td></tr>
      <tr><td>Cumulative raise > ₹2,000cr</td><td>Governance ↑</td><td>+0.30 fixed adder</td><td>Competition Act DVT — ₹2,000cr threshold live 10-Sep-2024</td></tr>
      <tr><td>Listed customer BRSR dependency</td><td>ESG & Climate ↑</td><td>×1.2</td><td>SEBI BRSR Value-Chain Circular 28-Mar-2025</td></tr>
      <tr><td>Climate risk zone (Low→Extreme)</td><td>ESG & Climate ↑ · Property ↑</td><td>1.0 / 1.2 / 1.5 / 1.8</td><td>IMD Climate Hazard Atlas; NDMA Guidelines; ND-GAIN Index 2024</td></tr>
      <tr><td>B2B revenue %</td><td>Liability ↑</td><td>1.0 + (b2b% × 0.4)</td><td>Swiss Re sigma — B2B contractual PI exposure scales with enterprise sales %</td></tr>
    </tbody></table>
    <p class="m-cite">${cite("DPIIT Press Note 3 (17-Apr-2020) — government-route FDI from land-border countries including China","NITI Aayog Future of Work: India's Gig Economy 2024 — 7.7M gig workers; projected 23.5M by 2029–30","CBAM Regulation (EU) 2023/956 — Carbon Border Adjustment Mechanism definitive phase from 1-Jan-2026; India among largest payers","MeitY AI Advisory 15-Mar-2024 (revised 3-Apr-2024); SafetyNet for Generative AI (SGI) Rules 10-Feb-2026","Competition (Amendment) Act 2023 — Deal Value Threshold ₹2,000cr live 10-Sep-2024","SEBI BRSR Core + Value-Chain Circular 28-Mar-2025 — ESG obligations push-through to supplier startups","ND-GAIN Index 2024 — India ranked 20th most climate-vulnerable nation globally")}</p>
  </div>`);

  /* ── STEP 6 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">6</span><span class="m-step-title">Team-size modifiers — ${ts} people</span></div>
    <p class="m-p"><strong>Team liability factor</strong> (applied to Liability and Reputation): <code>0.85 + 0.08 × ln(1 + team_size ÷ 10)</code><br>
    For ${ts} people → <code>0.85 + 0.08 × ln(${(1+ts/10).toFixed(2)}) = <strong>${tlf}</strong></code><br>
    Log-scaling reflects that liability losses grow sub-linearly with headcount — doubling people does not double claims.</p>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:12px;">
      <table class="m-table">
        <caption class="m-caption">Key Person multiplier — fewer people = higher concentration risk</caption>
        <thead>${mh(["Team size","kp_mult"])}</thead><tbody>
          ${[["≤ 5","1.5",ts<=5],["6–10","1.4",ts>=6&&ts<=10],["11–20","1.2",ts>=11&&ts<=20],["21–50","1.0",ts>=21&&ts<=50],["51–150","0.85",ts>=51&&ts<=150],["151+","0.7",ts>150]].map(([r,v,a])=>`<tr${a?' class="m-active-row"':""}><td>${r}</td><td><strong>${v}</strong></td></tr>`).join("")}
        </tbody>
      </table>
      <table class="m-table">
        <caption class="m-caption">Property / Gig multiplier — more people = more assets at risk</caption>
        <thead>${mh(["Team size","team_mult"])}</thead><tbody>
          ${[["≤ 10","0.8–1.0",ts<=10],["11–20","1.0",ts>=11&&ts<=20],["21–50","1.15",ts>=21&&ts<=50],["51–150","1.30",ts>=51&&ts<=150],["151+","1.50",ts>150]].map(([r,v,a])=>`<tr${a?' class="m-active-row"':""}><td>${r}</td><td><strong>${v}</strong></td></tr>`).join("")}
        </tbody>
      </table>
    </div>
    <p class="m-cite">${cite("Swiss Re sigma No. 1/2024 — corporate liability losses follow log(headcount) growth, not linear; loss-development pattern analysis","ESIC Act 1948 — statutory health insurance threshold: 10+ employees in ESIC-notified areas","Sexual Harassment of Women at Workplace Act 2013 §4 — Internal Committee mandatory for 10+ employees")}</p>
  </div>`);

  /* ── STEP 7 ── */
  const sortOrder = ["Cyber Technical Risk","Data Privacy Risk","Regulatory Compliance Risk","Governance & Fraud Risk","Policy Velocity Risk","Geopolitical Risk","Reputation Risk","Liability Risk","Key Person Risk","IP Infringement Risk","ESG & Climate Risk","Gig & Labour Risk","Property Risk"];
  const sortedCats = sortOrder.filter(k=>k in scores).concat(Object.keys(scores).filter(k=>!sortOrder.includes(k)));
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">7</span><span class="m-step-title">Scale to 100 — final scores for ${esc(p.startup_name||"this startup")}</span></div>
    <p class="m-p">Formula: <code>score = base_weight × (stage_mult) × (ops_mult) × (data_mult) × (dynamic_adjusters) × 7.5</code>, capped at 100.<br>
    <strong>Why 7.5?</strong> A typical mid-risk profile (sector base ≈ 7, Seed stage 0.9, medium data, no adjusters) computes to 7 × 0.9 × 1.0 × 7.5 = 47.25 — anchoring the scale around 50 for average inputs, with room for high-risk profiles to reach 100.</p>
    <table class="m-table"><thead>${mh(["Risk category","Final score","Severity"])}</thead><tbody>
    ${sortedCats.map(cat => {
      const s=scores[cat]; const sev=s>=70?"🔴 Critical":s>=40?"🟡 Elevated":"🟢 Low";
      return `<tr><td>${esc(cat)}</td><td style="text-align:center;font-weight:700;">${s}/100</td><td>${sev}</td></tr>`;
    }).join("")}
    <tr style="border-top:2px solid var(--border);"><td><strong>Overall (average of 13 categories)</strong></td><td style="text-align:center;font-weight:700;">${result.overall||"—"}/100</td><td>${(result.overall||0)>=70?"🔴 High risk":(result.overall||0)>=45?"🟡 Medium-High":"🟢 Manageable"}</td></tr>
    </tbody></table>
  </div>`);

  /* ── STEP 8 ── */
  const PRM = { "cyber_liability":"Cyber Technical (1.0) · Data Privacy (0.7) · Regulatory Compliance (0.3)","dno_liability":"Liability (0.7) · Governance & Fraud (0.6) · Regulatory Compliance (0.5)","professional_indemnity":"Liability (1.0) · Cyber Technical (0.2) · IP Infringement (0.3)","employee_health":"Key Person (0.5) · Liability (0.2) · Gig & Labour (0.3)","group_pa":"Key Person (0.6) · Liability (0.2) · Gig & Labour (0.4)","employees_comp":"Liability (0.6) · Regulatory Compliance (0.6) · Property (0.2) · Gig & Labour (0.5)","property_fire":"Property (1.0) · ESG & Climate (0.3)","business_edge":"Property (0.7) · Liability (0.4)","public_liability":"Liability (0.8) · Property (0.3)","product_liability":"Liability (0.9) · Regulatory Compliance (0.3) · IP Infringement (0.2)","marine_transit":"Property (0.8) · Geopolitical (0.3)","key_person":"Key Person (1.0) · Governance & Fraud (0.3)","employment_practices":"Liability (0.6) · Regulatory Compliance (0.6) · Gig & Labour (0.5)","crime_fidelity":"Cyber Technical (0.3) · Liability (0.4) · Governance & Fraud (0.6) · Regulatory Compliance (0.3)","comprehensive_general_liability":"Liability (0.9) · Regulatory Compliance (0.3)","business_interruption":"Property (0.5) · Cyber Technical (0.3) · Liability (0.2) · Policy Velocity (0.3)","property_all_risk":"Property (1.0) · Liability (0.2) · ESG & Climate (0.3)","electronic_equipment":"Property (0.7) · Cyber Technical (0.2)","machinery_breakdown":"Property (0.8) · Regulatory Compliance (0.1)","motor_fleet":"Liability (0.8) · Property (0.6) · Gig & Labour (0.4)","trade_credit":"Regulatory Compliance (0.4) · Liability (0.5) · Geopolitical (0.3)","drone_insurance":"Liability (0.7) · Property (0.5) · Regulatory Compliance (0.4)","msme_suraksha":"Property (0.6) · Liability (0.4)","enterprise_secure":"Property (0.8) · Liability (0.4) · Regulatory Compliance (0.2) · ESG & Climate (0.2)","contractors_all_risk":"Property (0.9) · Liability (0.5)","clinical_trials":"Regulatory Compliance (0.8) · Liability (0.6)","gadget_equipment":"Property (0.5) · Cyber Technical (0.2)","money_insurance":"Property (0.4) · Liability (0.3)" };
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">8</span><span class="m-step-title">Product fit score — risk-map weighted average</span></div>
    <p class="m-p">Each insurance product has a <em>risk map</em> — weighted links to the risk categories it addresses. The fit score is the weighted average of only those linked categories:<br>
    <code>fit_score = Σ(risk_category_score × weight) ÷ Σ(weights)</code><br>
    This means a product only scores high if the startup actually has elevated risk in the categories that product covers. Property Fire cannot score high for a digital-only startup because Property Risk = low → the dot-product stays low regardless of sector.</p>
    <table class="m-table"><thead>${mh(["Product","Risk categories it addresses (weight)"])}</thead><tbody>
    ${Object.entries(PRM).map(([k,v])=>`<tr><td style="font-size:11px;font-weight:600;">${esc(k.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase()))}</td><td style="font-size:11px;color:var(--ink-muted);">${esc(v)}</td></tr>`).join("")}
    </tbody></table>
    <p class="m-cite">${cite("IRDAI Product Regulations — insurable interest doctrine defines which products can be legally bound for which insured categories","Insurance Act 1938 §2(6D) — definition of insurable interest in Indian insurance law")}</p>
  </div>`);

  /* ── STEP 9 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">9</span><span class="m-step-title">Sector exclusions — hard filter before scoring</span></div>
    <p class="m-p">Products that are structurally inapplicable to <strong>${esc(p.sector||"this sector")}</strong> are removed from the pool before any scoring. They cannot appear in recommendations regardless of how the scores fall. This prevents absurd outputs (a neobank being recommended a clinical trials policy) and mirrors IRDAI eligibility rules.</p>
    <p class="m-p">Exclusions are static per sector: e.g. Fintech excludes <em>clinical_trials, product_liability, marine_transit, motor_fleet, drone_insurance, contractors_all_risk, machinery_breakdown, msme_suraksha, money_insurance</em>.</p>
    <p class="m-cite">${cite("IRDAI Regulations on product eligibility — insurable interest doctrine","Insurance Act 1938 §2(6D) — insurable interest requirement","IRDAI (Non-Life Insurance Products) Regulations 2019 — eligible insured categories per product class")}</p>
  </div>`);

  /* ── STEP 10 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">10</span><span class="m-step-title">Sector override boosts — structurally essential products (+40%, floor 50)</span></div>
    <p class="m-p">Certain products are non-negotiable for a sector because regulation mandates them or real-world loss data makes them unavoidable. These receive <code>score × 1.4</code> with a guaranteed floor of 50 — ensuring they always surface, even if the startup's raw risk profile is mild in those categories.</p>
    <p class="m-p">Examples:
      <strong>Fintech</strong> → Crime & Fidelity, D&O, Trade Credit (BharatPe ₹81.3cr fraud, Paytm §35A halt).
      <strong>Logistics</strong> → Marine Transit, Public Liability, Motor Fleet (MV Act §149 unlimited TP liability).
      <strong>D2C</strong> → Product Liability, Marine Transit, MSME Suraksha (CPA 2019 §84 strict product liability).
    </p>
    <p class="m-cite">${cite("EOW Mumbai — BharatPe FIR May-2023: ₹81.3 crore fake-vendor fraud via finance team","RBI Press Release prid=57345 — Paytm Payments Bank §35A customer onboarding halt 31-Jan-2024","Byju's NCLT admission 16-Jul-2024; US Bankruptcy Court $1.07bn judgment 20-Nov-2025","MV Act 1988 §149 — unlimited third-party liability for motor vehicles on Indian roads","Consumer Protection Act 2019 §84 — strict product liability on manufacturers and platforms")}</p>
  </div>`);

  /* ── STEP 11 ── */
  const d_and_o_active = ["Series A","Series B+"].includes(p.funding_stage);
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">11</span><span class="m-step-title">Stage boosts — D&O for Series A / B+</span></div>
    <p class="m-p">At Series A and Series B+, D&O Liability receives a compliance-adjusted additional boost:<br>
    <code>compliance_factor = 1.0 + (Regulatory Compliance Risk ÷ 200)</code><br>
    <code>new_score = score × (1 + 0.45 × compliance_factor)</code> with a floor of 55.</p>
    <p class="m-p">Current stage: <strong>${esc(p.funding_stage||"—")}</strong> → D&O stage boost is ${d_and_o_active ? "<strong style='color:var(--red)'>ACTIVE</strong>" : "<em>not triggered (Seed / Pre-seed)</em>"}.</p>
    <p class="m-p">The compliance_factor link means startups in highly regulated sectors (Fintech, Healthtech) get a larger D&O boost than those in lightly regulated ones — reflecting the higher personal liability exposure from regulatory enforcement.</p>
    <p class="m-cite">${cite("NVCA Model Term Sheet 2024 — D&O insurance standard requirement post-priced institutional round","SEBI Listing Obligations & Disclosure Requirements Regulations 2015 — Reg 17 mandatory independent directors","Companies Act 2013 §2(60) — 'officer in default' personal liability for director-level decisions","RBI Fit & Proper Criteria 2024 — MD/CEO approval required; Paytm precedent shows board-level personal exposure is real")}</p>
  </div>`);

  /* ── STEP 12 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">12</span><span class="m-step-title">Team-size boosts — thresholds that unlock specific products</span></div>
    <table class="m-table"><thead>${mh(["Trigger","Product boosted","Boost applied","Active for ${ts} people?"])}</thead><tbody>
      <tr${act(ts>=10)}><td>Team ≥ 10</td><td>Employee Health Insurance</td><td>×1.20, guaranteed floor 40</td><td>${ts>=10?"✓ <strong>YES</strong>":"✗ Not yet"}</td></tr>
      <tr${act(ts>=25)}><td>Team ≥ 25</td><td>Employment Practices Liability</td><td>×1.15, guaranteed floor 38</td><td>${ts>=25?"✓ <strong>YES</strong>":"✗ Not yet"}</td></tr>
    </tbody></table>
    <p class="m-cite">${cite("ESIC Act 1948 §2(12) and §38 — compulsory insurance for employees in ESIC-notified establishments with 10+ workers","Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act 2013 §4 — Internal Committee mandatory for 10+ employees","ICLG India Employment Law 2024 — wrongful termination and discrimination claims scale proportionally with headcount")}</p>
  </div>`);

  /* ── STEP 13 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">13</span><span class="m-step-title">Regulatory trigger boosts — advanced profile signals</span></div>
    <p class="m-p">These boosts fire only when specific inputs are declared. Each maps directly to a statutory obligation or documented loss event — they surface the right product at the right moment rather than relying on generic sector logic.</p>
    <table class="m-table"><thead>${mh(["Trigger condition","Products boosted","Boost","Legal / actuarial basis"])}</thead><tbody>
      <tr><td>Gig workers > 30% of headcount</td><td>Employees Comp, Employment Practices, Group PA</td><td>×1.45, floor 55</td><td>SS Code 2020 §§113–114; MV Aggregator Guidelines 2025</td></tr>
      <tr><td>Hardware revenue > 30%</td><td>Product Liability</td><td>×1.50, floor 60</td><td>CPA 2019 §84; BIS QCO IS 17043/15844 (1-Aug-2024)</td></tr>
      <tr><td>EU exports > 10% of revenue</td><td>Trade Credit, Marine Transit</td><td>×1.35, floor 50</td><td>CBAM Regulation 2023/956 — definitive phase 1-Jan-2026</td></tr>
      <tr><td>Chinese BO > 10% or raise > ₹2,000cr</td><td>D&O Liability, Crime & Fidelity</td><td>×1.40, floor 55</td><td>DPIIT Press Note 3 (2020); Competition Act DVT 10-Sep-2024</td></tr>
      <tr><td>AI in product = Yes</td><td>Professional Indemnity</td><td>×1.40, floor 55</td><td>MeitY AI Advisory 15-Mar-2024; SGI Rules 10-Feb-2026; EU AI Act Art 2(1)(c)</td></tr>
      <tr><td>RBI registration present (NBFC / PA / PPI / RIA)</td><td>D&O Liability, Business Interruption</td><td>×1.45, floor 60</td><td>RBI §35A direction — Paytm Jan-2024; Kotak Mahindra Apr-2024</td></tr>
      <tr><td>Listed customer BRSR dependency = Yes</td><td>Enterprise Secure Package</td><td>×1.25, floor 45</td><td>SEBI BRSR Value-Chain Circular 28-Mar-2025</td></tr>
    </tbody></table>
    <p class="m-cite">${cite("Social Security Code 2020 §§113–114 — gig aggregator mandatory contribution to social security fund","MoRTH Motor Vehicle Aggregator Guidelines 2025 — ₹5 lakh health cover + ₹10 lakh term life per driver, mandatory","Consumer Protection Act 2019 §84 — manufacturer / platform strict product liability","BIS Quality Control Order IS 17043 (August 2024) — mandatory BIS certification for electronics sold in India","DPIIT Press Note 3 (17-Apr-2020) — government-route FDI approval for >10% beneficial ownership from land-border countries","Competition (Amendment) Act 2023 — Deal Value Threshold: ₹2,000cr cumulative raises trigger CCI filing","RBI Press Release prid=57345 — Paytm PB §35A halt 31-Jan-2024; RBI Action on Kotak Mahindra 24-Apr-2024","SEBI BRSR Value-Chain Circular 28-Mar-2025 — ESG disclosure obligations pushed to top 250 listed companies' key suppliers")}</p>
  </div>`);

  /* ── STEP 14 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">14</span><span class="m-step-title">Sort, top 5, mandatory append</span></div>
    <p class="m-p">After all boosts, all eligible products are sorted by final fit score descending. The top 5 become the primary recommendations. Mandatory appends then ensure critical products are never missed, regardless of ranking:</p>
    <ul class="m-list">
      <li>Sector override products not already in top 5 → appended as <strong>mandatory</strong></li>
      <li>D&O Liability → mandatory append for Series A / B+ if not in top 5</li>
      <li>Employee Health → always appended as mandatory (ESIC statutory obligation)</li>
      <li>Healthtech MedDevice SaMD sub-sector → Clinical Trials + Product Liability mandatory (CDSCO SaMD Guidance 21-Oct-2025)</li>
      <li>Logistics / Foodtech + gig headcount > 20% → Group PA + Employees Comp mandatory (MV Aggregator Guidelines 2025)</li>
    </ul>
    <p class="m-cite">${cite("CDSCO SaMD Draft Guidance 21-Oct-2025 — Class B/C/D AI diagnostic devices require mandatory licensing before commercial deployment","ESIC Act 1948 §38 — compulsory registration and insurance in notified areas")}</p>
  </div>`);

  /* ── STEP 15 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">15</span><span class="m-step-title">Priority label — final classification of each recommendation</span></div>
    <table class="m-table" style="max-width:380px;"><thead>${mh(["Fit score","Label","Meaning"])}</thead><tbody>
      <tr><td>≥ 70</td><td><strong>🔴 Critical</strong></td><td>Cover immediately — uninsured exposure is material and likely</td></tr>
      <tr><td>40–69</td><td><strong>🟡 Recommended</strong></td><td>Strongly consider — risk is real but not existential without it</td></tr>
      <tr><td>&lt; 40</td><td><strong>🟢 Optional</strong></td><td>Good to have — low probability or low severity for this profile</td></tr>
    </tbody></table>
    ${recs.length ? `<p class="m-p" style="margin-top:14px;"><strong>Actual product scores for ${esc(p.startup_name||"this startup")}:</strong></p>
    <table class="m-table"><thead>${mh(["Product","Fit score","Priority"])}</thead><tbody>
    ${recs.map(r=>`<tr><td>${esc(r.name||r.key)}</td><td style="text-align:center;font-weight:700;">${r.score}</td><td>${r.priority==="Critical"?"🔴 Critical":r.priority==="Recommended"?"🟡 Recommended":"🟢 Optional"}</td></tr>`).join("")}
    </tbody></table>` : ""}
  </div>`);

  /* ── STEP 16 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">16</span><span class="m-step-title">Bundle eligibility gates — hard filters applied before bundle scoring</span></div>
    <p class="m-p">Every bundle in the catalog declares which sectors and stages it is valid for. The engine eliminates non-matching bundles before any scoring — they receive no score and appear only as alternatives if the best match is weak.</p>
    <p class="m-p">Additional gates from <code>research_config.json</code>:</p>
    <ul class="m-list">
      <li><strong>Asset band</strong> — a fab/plant bundle (Industrial All Risk) won't be offered to an <em>asset_light</em> company</li>
      <li><strong>SI cap / floor</strong> — Bharat Sookshma Udyam: up to ₹5cr insurable assets; Bharat Laghu Udyam: ₹5–50cr; Enterprise Secure: Series B+ only</li>
      <li><strong>Hard decline</strong> — Gaming.Real_Money sub-sector: blanket prohibition under Online Gaming Act 2025 §5; all products declined</li>
    </ul>
    ${bundle ? `<p class="m-p">Matched bundle for this startup: <strong>${esc(bundle.name)}</strong> — eligible stages: ${esc((bundle.eligible_stages||[]).join(", "))}.</p>` : ""}
    <p class="m-cite">${cite("Online Gaming Act 2025 (assented 22-Aug-2025) §5 — blanket prohibition on real-money gaming without SRO registration","IRDAI MSME Suraksha Kavach Guidelines — eligible insurable asset value ceiling","Bharat Laghu Udyam Suraksha Policy — IRDAI-standardised product for assets ₹5cr–₹50cr")}</p>
  </div>`);

  /* ── STEP 17 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">17</span><span class="m-step-title">Bundle coverage score — dot-product of bundle's covered risks × startup's actual scores</span></div>
    <p class="m-p">Each bundle declares which risk categories it addresses (<code>covered_risks</code>). The coverage score is a weighted dot-product:<br>
    <code>coverage_score = Σ (risk_weight[category] × startup_score[category])</code> for each category in the bundle's covered_risks list.</p>
    <p class="m-p">The startup's highest-scoring categories dominate the sum. A bundle that covers Cyber + Data Privacy will score far higher for a Fintech (Cyber=100, Data Privacy=100) than for an Agritech (Cyber=27, Data Privacy=32).</p>
    ${bundle ? `<p class="m-p"><strong>${esc(bundle.name)}</strong> covers: <em>${esc((bundle.covered_risks||[]).join(" · "))}</em>.</p>` : ""}
    <p class="m-p">Risk category weights are loaded from <code>research_config.json</code> — calibrated using IRDAI Annual Report segment premiums, Swiss Re sigma pricing, and ICICI Lombard's historical commercial lines data.</p>
    <p class="m-cite">${cite("IRDAI Annual Report FY2023–24 — gross direct premium by product segment; fire, liability, health, marine, engineering","Swiss Re sigma No. 1/2024 — global non-life insurance market sizing and pricing methodology","ICICI Lombard General Insurance Annual Report FY2023–24 — segment premium growth and loss ratios")}</p>
  </div>`);

  /* ── STEP 18 ── */
  const stageKey = (p.funding_stage==="Pre-seed"||p.funding_stage==="Seed")?"seed":p.funding_stage==="Series A"?"series_a":"series_b";
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">18</span><span class="m-step-title">Composite multipliers — sector × stage × asset type × geography</span></div>
    <p class="m-p">The raw coverage score is scaled by four layers of multipliers compounded per risk category:<br>
    <code>composite_mult = sector_mult × stage_mult × asset_mult × geo_mult</code></p>
    <table class="m-table"><thead>${mh(["Layer","Config key","What it adjusts"])}</thead><tbody>
      <tr><td>Sector multiplier</td><td><code>sector_multipliers[${esc(p.sector||"sector")}]</code></td><td>Elevates / dampens specific risk weights for this industry across all bundles</td></tr>
      <tr><td>Stage multiplier</td><td><code>stage_multipliers[${stageKey}]</code></td><td>Scales for company maturity — early-stage has lower exposure surface</td></tr>
      <tr><td>Asset multiplier</td><td><code>asset_multipliers[asset_light / lab / warehouse / fab_or_plant]</code></td><td>Physical asset intensity — digital startup = lower property weights in bundle scoring</td></tr>
      <tr><td>Geo multiplier</td><td><code>geo_multipliers[state]</code></td><td>Scalar applied uniformly — e.g. Karnataka companies face higher gig-law multiplier</td></tr>
    </tbody></table>
    <p class="m-cite">${cite("NITI Aayog Gig Economy Report 2024 — Karnataka, Rajasthan, Bihar, Jharkhand, Telangana ranked most aggressive on gig-worker legislation","IMD Climate Hazard Atlas — state-level flood, cyclone, and heat zone classification for property underwriting")}</p>
  </div>`);

  /* ── STEP 19 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">19</span><span class="m-step-title">Revenue score — commercial attractiveness of each bundle for ICICI Lombard</span></div>
    <p class="m-p">SPARC also scores each bundle by its market opportunity — ensuring what gets recommended is commercially viable to pitch and bind, not just theoretically risk-appropriate:<br>
    <code>revenue_score = 100 × (0.35×TAM_norm + 0.25×adoption×margin×40 + 0.20×trajectory + 0.20×0.7)</code></p>
    <table class="m-table"><thead>${mh(["Component","Weight","Data source"])}</thead><tbody>
      <tr><td>Startup-addressable TAM (normalised)</td><td>35%</td><td>IRDAI segment premiums + Swiss Re sigma SME market estimates</td></tr>
      <tr><td>Adoption rate × underwriter margin</td><td>25%</td><td>ICICI Lombard segment take-up and loss ratio data (FY24)</td></tr>
      <tr><td>Trajectory (up / flat / down)</td><td>20%</td><td>IRDAI segment premium CAGR FY22–FY24</td></tr>
      <tr><td>Quality baseline (fixed 0.7)</td><td>20%</td><td>Minimum confidence floor for all active products in the catalog</td></tr>
    </tbody></table>
    <p class="m-p">This prevents the engine from recommending bundles that are technically eligible but commercially marginal — an important constraint for an RM-facing sales tool.</p>
    <p class="m-cite">${cite("IRDAI Annual Report FY2023–24 — segment premium growth rates by product class","Swiss Re sigma No. 1/2024 — global SME commercial lines market size and growth","ICICI Lombard General Insurance Annual Report FY2023–24 — commercial lines segment data")}</p>
  </div>`);

  /* ── STEP 20 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">20</span><span class="m-step-title">Final bundle score — coverage + revenue + adoption, penalised by actuarial risk</span></div>
    <p class="m-p"><code>final_score = (0.45 × coverage_score + 0.30 × (revenue_score÷100) + 0.25 × adoption) × (2 − risk_multiplier)</code></p>
    <table class="m-table"><thead>${mh(["Weight","Component","What it rewards"])}</thead><tbody>
      <tr><td><strong>45%</strong></td><td>Coverage score</td><td>Risk-appropriateness — bundle's covered_risks align with this startup's highest-scoring categories</td></tr>
      <tr><td><strong>30%</strong></td><td>Revenue score</td><td>Market opportunity — TAM × adoption × margin; commercially viable to pitch and bind</td></tr>
      <tr><td><strong>25%</strong></td><td>Adoption rate</td><td>Proven take-up in this sector/stage — a bundle nobody buys will not help the RM</td></tr>
      <tr><td colspan="3"><em>× (2 − risk_multiplier)</em>: Risk penalty — bundles with higher actuarial loss ratios score lower, nudging toward cleanly bindable products</td></tr>
    </tbody></table>
    ${bundle ? `<p class="m-p" style="margin-top:10px;"><strong>Recommended bundle: ${esc(bundle.name)}</strong>${bundle.final_score!=null?` — final score: ${bundle.final_score}`:""} · fit: ${bundle.fit_pct||"—"}%</p>` : ""}
    <p class="m-cite">${cite("Swiss Re sigma No. 1/2024 — actuarial loss ratio benchmarks by commercial lines segment","IRDAI Annual Report FY2023–24 — product-level incurred claims ratios")}</p>
  </div>`);

  /* ── STEP 21 ── */
  steps.push(`<div class="m-step">
    <div class="m-step-head"><span class="m-step-num">21</span><span class="m-step-title">Legacy fit % — human-readable match strength shown on the bundle card</span></div>
    <p class="m-p">The fit percentage displayed on the bundle card is computed separately from the ranking score. It provides a simpler signal for RM communication:<br>
    <code>fit_pct = (sector match → +40) + (stage match → +30) + 30 × (avg top-3 risk scores ÷ 100) × relevance_factor</code><br>
    Where <code>relevance_factor = 1.0</code> if sector is in the bundle's eligible set, <code>0.55</code> if it is a fallback nearest-match.</p>
    ${bundle ? `<p class="m-p"><strong>${esc(bundle.name)}</strong> fit: <strong>${bundle.fit_pct||"—"}%</strong> (${bundle.match_strength||"strong"} match).</p>` : ""}
    <div class="m-insight">
      <strong>Core insight:</strong> The engine never hardcodes which bundle a sector receives. The recommendation emerges from the math — risk scores × coverage weights × eligibility gates × commercial signal — and arrives at the same answer for the same profile every time. Every output is traceable back to a specific data point, regulation, or actuarial source listed in the references below.
    </div>
  </div>`);

  /* ── REFERENCES ── */
  const refsHtml = `<div class="m-step m-citations">
    <div class="m-step-head"><span class="m-step-num" style="background:var(--ink-muted);min-width:44px;">Ref</span><span class="m-step-title">Research references & data sources</span></div>
    <ol class="m-ref-list">${refs.map(r=>`<li>${esc(r)}</li>`).join("")}</ol>
  </div>`;

  return `<div class="methodology-wrap">${steps.join("")}${refsHtml}</div>`;
}

/* ─── RESULT HELPERS ─────────────────────────────────────────── */
function renderKPI(label, value) {
  const statusByLabel = {
    "Overall risk": "Composite exposure",
    "Top risk": "Primary driver",
    "Critical covers": "Action count",
    "Bundle quote": "Indicative quote",
    "Premium range": "Pricing mode",
    "Risk clusters": "Model depth",
  };
  return `
    <div class="kpi-card">
      <div class="kpi-label">${esc(label)}</div>
      <div class="kpi-value">${esc(String(value))}</div>
      <div class="kpi-status">${esc(statusByLabel[label] || "Decision signal")}</div>
    </div>`;
}

function bundleCoverItems(bundle, why, limit = 4) {
  if (!bundle) return [];
  const raw = [
    ...(bundle.mandatory_covers || []),
    ...(bundle.optional_covers || []),
    ...(bundle.companion_bundle?.mandatory_covers || []),
    ...(bundle.companion_bundle?.optional_covers || []),
  ];
  const seen = new Set();
  return raw
    .filter(key => {
      const normalised = COVER_ALIASES[key] || key;
      if (seen.has(normalised)) return false;
      seen.add(normalised);
      return true;
    })
    .slice(0, limit)
    .map(key => ({
      key,
      label: labelize(key),
      why: getCoverWhy(key, why, bundle.companion_bundle?.mandatory_covers?.includes(key) ? "companion_covers" : "bundle_covers"),
    }));
}

function renderDecisionBrief(result) {
  const bundle = result.bundle_match || {};
  if (!bundle?.name) return "";
  const profile = result.profile || {};
  const topRisks = (result.top_risks || []).slice(0, 3).map(r => r.name?.replace(" Risk", "")).filter(Boolean);
  const covers = bundleCoverItems(bundle, result.why_it_matters || {}, 4);
  const quote = result.bundle_only_pricing_quote;
  const quoted = isQuoted(quote);
  const quoteText = quoted
    ? `Bundle quote: INR ${quote.gross_premium_lakh}L incl. GST`
    : "Quote pending: confirm underwriting inputs";
  const nextAction = quoted
    ? "Next action: review underwriter checks and use the quote tab for pricing discussion."
    : "Next action: open Estimated Quote, confirm suggested limits, then generate the bundle price.";
  const genaiPrimary = result.recommendation_mode === "primary" && result.genai_source === "gemini";
  const decisionSource = genaiPrimary ? "GenAI-ranked with deterministic guardrails" : "Deterministic recommendation";
  const why = bundle.genai_why_it_fits || result.why_it_matters?.bundle || bundle.description || `${bundle.name} is the best current package fit for ${profile.sector || "this startup"}.`;

  return `
    <div class="decision-brief">
      <div class="decision-main">
        <div class="decision-label">Recommended decision</div>
        <h3>${esc(bundle.name)}</h3>
        <p>${esc(why)}</p>
        <div class="decision-meta">
          <span>${esc(decisionSource)}</span>
          <span>${esc(bundle.fit_pct || 0)}% profile fit</span>
          <span>${esc(quoteText)}</span>
        </div>
      </div>
      <div class="decision-side">
        <div class="decision-side-title">Why it matters now</div>
        <div class="decision-risk-line">${esc(topRisks.length ? topRisks.join(", ") : "Current exposure profile")}</div>
        <div class="decision-cover-list">
          ${covers.map(item => `
            <div class="decision-cover">
              <strong>${esc(item.label)}</strong>
              <span>${esc(item.why || "Mapped to one of the startup's current risk exposures.")}</span>
            </div>`).join("")}
        </div>
        <div class="decision-next">${esc(nextAction)}</div>
      </div>
    </div>`;
}

function renderPricingSeparation(result) {
  const bundleQuote = result.bundle_only_pricing_quote;
  const fullQuote = result.pricing_engine_quote;
  const quoteReady = isQuoted(bundleQuote) || isQuoted(fullQuote);
  const suppressBenchmark = shouldSuppressBenchmarkRange(result);
  const scale = fullQuote?.pricing_scale || bundleQuote?.pricing_scale || {};
  const activeQuote = bundleQuote?.covers_priced?.length ? bundleQuote : fullQuote;
  const benchmark = activeQuote?.benchmark_comparison || {};
  const summary = result.premium_summary;
  const benchmarkValue = suppressBenchmark
    ? "Startup benchmark not comparable"
    : summary
      ? `INR ${summary.min_lakh}-${summary.max_lakh}L`
      : "Unavailable";
  const benchmarkNote = suppressBenchmark
    ? (benchmark.explanation || scale.message || "Selected limits or specialty operations need underwriter-led validation, so startup benchmark ranges are hidden.")
    : "Early benchmark only. It does not include selected SI, GST, bundle discount, claims loadings, or underwriter checks.";
  const quoteValue = quoteReady
    ? quoteDisplayText(activeQuote)
    : "Input needed";
  const quoteNote = quoteReady
    ? "Generated from submitted underwriting inputs, line-specific pricing bases, confidence rules, bundle discount, and GST."
    : "Use the suggested limits below as a starting point, then generate a quote.";

  return `
    <div class="pricing-mode-brief">
      <div class="pricing-mode-card ${suppressBenchmark ? "muted" : ""}">
        <div class="pricing-mode-label">Benchmark range</div>
        <div class="pricing-mode-value">${esc(benchmarkValue)}</div>
        <p>${esc(benchmarkNote)}</p>
      </div>
      <div class="pricing-mode-card ${quoteReady ? "active" : ""}">
        <div class="pricing-mode-label">Quote estimate</div>
        <div class="pricing-mode-value">${esc(quoteValue)}</div>
        ${quoteReady ? confidenceBadge(activeQuote?.quote_confidence) : ""}
        <p>${esc(quoteNote)}</p>
      </div>
    </div>`;
}

function renderGenAIStatus(result) {
  const source = result.genai_source;
  const err = result.genai_error;
  // Only surface a visible indicator when there's an actionable error or GenAI is live
  if (source === "gemini") {
    return `<div style="display:inline-flex;align-items:center;gap:6px;font-size:11px;color:var(--ink-muted);margin-bottom:12px;"><span style="width:6px;height:6px;border-radius:50%;background:#059669;flex-shrink:0;"></span>AI-enhanced recommendation</div>`;
  }
  if (err) {
    return `<div style="display:inline-flex;align-items:center;gap:6px;font-size:11px;color:var(--ink-muted);margin-bottom:12px;" title="${esc(err)}"><span style="width:6px;height:6px;border-radius:50%;background:var(--ink-faint);flex-shrink:0;"></span>Deterministic recommendation</div>`;
  }
  return "";
}

function renderFounderContextStrip(profile) {
  const product = (profile?.product_description || "").trim();
  const concern = (profile?.biggest_fear || "").trim();
  if (!product && !concern) return "";
  return `
    <div class="founder-context-strip" aria-label="Founder context used">
      <div class="founder-context-kicker">Founder context used</div>
      <div class="founder-context-grid">
        ${product ? `
          <div class="founder-context-item">
            <span>Product</span>
            <strong>${esc(product)}</strong>
          </div>` : ""}
        ${concern ? `
          <div class="founder-context-item">
            <span>Concern</span>
            <strong>${esc(concern)}</strong>
          </div>` : ""}
      </div>
    </div>`;
}

function isQuoted(q) {
  return q?.covers_priced?.length > 0;
}

function confidenceLabel(band) {
  return {
    technically_priced: "Technically priced",
    directional_only: "Directional only",
    underwriter_required: "Underwriter validation required",
  }[band || ""] || "Indicative";
}

function confidenceClass(band) {
  return band === "underwriter_required" ? "danger" : band === "directional_only" ? "warn" : "ok";
}

function confidenceBadge(conf) {
  const band = typeof conf === "string" ? conf : conf?.band;
  return `<span class="pricing-confidence ${confidenceClass(band)}">${esc(confidenceLabel(band))}</span>`;
}

function quoteDisplayText(quote) {
  if (!quote) return "Input needed";
  if (quote.precision_mode === "suppressed") return "Underwriter validation required";
  const range = quote.display_premium_range_lakh;
  if (quote.precision_mode === "range" && range) return `INR ${range.min}-${range.max}L`;
  return `INR ${quote.display_premium_lakh || quote.gross_premium_lakh}L`;
}

function coverPremiumText(c) {
  if (c?.precision_mode === "suppressed") return "UW review";
  if (c?.precision_mode === "range" && c.display_premium_range_lakh) {
    return `INR ${c.display_premium_range_lakh.min}-${c.display_premium_range_lakh.max}L`;
  }
  return `INR ${c?.display_premium_lakh || c?.premium_lakh}L`;
}

function renderPricePanel(quote, tagLabel, tagClass, subtitle) {
  if (!quote || !isQuoted(quote)) return "";
  const covers = quote.covers_priced || [];
  const flags  = quote.underwriter_referral_flags || [];
  const scale = quote.pricing_scale || {};
  const benchmark = quote.benchmark_comparison || {};
  const explanation = quote.explanation_items || [];
  return `
    <div class="pricing-card">
      <span class="pricing-panel-tag ${tagClass}">${esc(tagLabel)}</span>
      <div class="pricing-head">
        <div>
          <div class="pricing-title">${esc(quoteDisplayText(quote))}</div>
          <div class="premium-card-note">${esc(subtitle)} &nbsp;·&nbsp; incl. 18% GST</div>
          ${confidenceBadge(quote.quote_confidence)}
          ${scale.label ? `<div class="premium-card-note"><strong>${esc(scale.label)}</strong> - ${esc(scale.message || "")}</div>` : ""}
          ${benchmark.status && benchmark.status !== "comparable" ? `<div class="premium-card-note"><strong>Benchmark:</strong> ${esc(benchmark.explanation || "Startup benchmark is not comparable to this selected structure.")}</div>` : ""}
        </div>
        <div class="pricing-totals">
          <div class="kv-row"><span class="kv-key">Net premium</span><span class="kv-val">INR ${esc(quote.net_premium_lakh)}L</span></div>
          <div class="kv-row"><span class="kv-key">GST (18%)</span><span class="kv-val">INR ${esc(quote.gst_lakh)}L</span></div>
          <div class="kv-row"><span class="kv-key">${quote.cover_count} cover${quote.cover_count !== 1 ? "s" : ""}</span><span class="kv-val">INR ${esc(quote.total_sum_insured_cr)}Cr SI</span></div>
          ${quote.bundle_discount_lakh > 0 ? `<div class="kv-row"><span class="kv-key">Bundle discount</span><span class="kv-val" style="color:var(--green,#2e7d32)">−INR ${esc(quote.bundle_discount_lakh)}L</span></div>` : ""}
        </div>
      </div>
      <div class="pricing-cover-grid">
        ${covers.map(c => `
          <div class="pricing-cover">
            <div class="pricing-cover-name">${esc(c.cover_name || labelize(c.cover_key))} ${confidenceBadge(c.quote_confidence_band)}</div>
            <div class="pricing-cover-premium">${esc(coverPremiumText(c))}</div>
            <div class="pricing-cover-basis">${esc(c.exposure_label || "")} | ${esc((c.pricing_basis || "").replace(/_/g, " "))} | risk ${esc(c.average_risk_score ?? "n/a")}/100</div>
          </div>`).join("")}
      </div>
      ${explanation.length ? `<div class="pricing-explain">${explanation.map(x => `<div>${esc(x)}</div>`).join("")}</div>` : ""}
      ${flags.length ? `
        <div class="pricing-notes" style="grid-template-columns:1fr;">
          <div><div class="card-label">Underwriter checks</div>${flags.map(f => `<div class="callout-item compact"><span>${esc(f)}</span></div>`).join("")}</div>
        </div>` : ""}
    </div>`;
}

function reviseQuoteInputs() {
  state.quotePanelMode = "edit";
  renderResults(window.__result);
}

function shouldSuppressBenchmarkRange(result) {
  const scale = result?.pricing_engine_quote?.pricing_scale || result?.bundle_only_pricing_quote?.pricing_scale;
  return scale?.benchmark_range_applicable === false;
}

const SLIDER_RANGES = {
  cyber_limit_cr:               { min: 1,   max: 50,   step: 0.5 },
  dno_limit_cr:                 { min: 1,   max: 30,   step: 0.5 },
  pi_limit_cr:                  { min: 1,   max: 25,   step: 0.5 },
  crime_limit_cr:               { min: 0.5, max: 15,   step: 0.5 },
  employment_practices_limit_cr:{ min: 0.5, max: 15,   step: 0.5 },
  product_liability_limit_cr:   { min: 1,   max: 25,   step: 0.5 },
  public_liability_limit_cr:    { min: 1,   max: 25,   step: 0.5 },
  property_sum_insured_cr:      { min: 1,   max: 200,  step: 5   },
  gross_profit_si_cr:           { min: 1,   max: 100,  step: 1   },
  equipment_sum_insured_cr:     { min: 1,   max: 100,  step: 1   },
  stock_sum_insured_cr:         { min: 1,   max: 100,  step: 1   },
  annual_revenue_cr:            { min: 1,   max: 500,  step: 5   },
  data_records_lakhs:           { min: 0,   max: 500,  step: 5   },
  headcount:                    { min: 5,   max: 5000, step: 5   },
};

let _quoteDebounceTimer = null;

window.triggerLiveQuote = () => {
  clearTimeout(_quoteDebounceTimer);
  const badge = document.getElementById("quote-live-badge");
  if (badge) { badge.textContent = "Updating…"; badge.style.opacity = "1"; }
  _quoteDebounceTimer = setTimeout(() => generatePricingEstimate(), 480);
};

window.syncSlider = (key, value) => {
  const n = parseFloat(value);
  if (!Number.isFinite(n) || n < 0) return;
  const slider = document.getElementById(`qs-slider-${key}`);
  const input  = document.getElementById(`qs-input-${key}`);
  if (slider && parseFloat(slider.value) !== n) slider.value = n;
  if (input  && parseFloat(input.value)  !== n) input.value  = n;
  window.setQuoteInput(key, n);
  window.triggerLiveQuote();
};

function renderLiveSliderField(row) {
  const range = SLIDER_RANGES[row.key];
  if (!range || row.unit === "yes/no") return null;
  const val = quoteFieldValue(row) || range.min;
  const numericVal = Number(val) || range.min;
  const rangeMax = Math.max(range.max, numericVal);
  const isCount = row.unit === "count";
  return `
    <div class="ls-row">
      <div class="ls-label-row">
        <span class="ls-label">${esc(row.label)}</span>
        <div class="ls-value-wrap">
          <input type="number" class="ls-num" id="qs-input-${esc(row.key)}"
            min="${range.min}" max="${rangeMax}" step="${range.step}"
            value="${esc(String(val))}"
            oninput="syncSlider('${esc(row.key)}', this.value)">
          <span class="ls-unit">${esc(row.unit || "Cr")}</span>
        </div>
      </div>
      <input type="range" class="ls-range" id="qs-slider-${esc(row.key)}"
        min="${range.min}" max="${rangeMax}" step="${range.step}"
        value="${esc(String(val))}"
        oninput="syncSlider('${esc(row.key)}', this.value)">
      <div class="ls-endpoints"><span>${isCount ? range.min : `${range.min} Cr`}</span><span>${isCount ? rangeMax : `${rangeMax} Cr`}</span></div>
    </div>`;
}

function renderLiveSliderStrip(fields) {
  const sliderFields = (fields || []).filter(r => SLIDER_RANGES[r.key] && r.unit !== "yes/no");
  if (!sliderFields.length) return "";
  return `
    <div class="ls-strip">
      <div class="ls-strip-head">
        <span class="ls-strip-title">Adjust coverage limits</span>
        <span id="quote-live-badge" class="ls-badge" style="opacity:0">Updating…</span>
      </div>
      <div class="ls-strip-grid">
        ${sliderFields.map(r => renderLiveSliderField(r)).filter(Boolean).join("")}
      </div>
    </div>`;
}

window.toggleHowCalculated = (show) => {
  const modal = document.getElementById("how-calc-modal");
  if (!modal) return;
  const next = show !== undefined ? show : modal.style.display === "none";
  modal.style.display = next ? "flex" : "none";
  document.body.style.overflow = next ? "hidden" : "";
};

function fmtMethodMult(value) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n.toFixed(3)}x` : "n/a";
}

function fmtMethodRate(cover) {
  const rol = Number(cover?.loadings?.enterprise_rol);
  if (Number.isFinite(rol) && rol > 0) return `Enterprise ROL ${(rol * 100).toFixed(2)}%`;
  const rate = Number(cover?.base_rate_lakh_per_cr);
  return Number.isFinite(rate) ? `${rate.toFixed(3)}L/unit` : "n/a";
}

function renderQuoteMathSummaryRows(quote, label) {
  if (!quote || quote.quote_type === "input_required") return "";
  return `
    <tr>
      <td>${esc(label)}</td>
      <td>${esc(quote.cover_count ?? quote.covers_priced?.length ?? "n/a")}</td>
      <td>INR ${esc(quote.total_sum_insured_cr ?? "n/a")}Cr</td>
      <td>INR ${esc(quote.subtotal_premium_lakh ?? "n/a")}L</td>
      <td>${Math.round(Number(quote.bundle_discount_rate || 0) * 100)}% / INR ${esc(quote.bundle_discount_lakh ?? 0)}L</td>
      <td>INR ${esc(quote.net_premium_lakh ?? "n/a")}L</td>
      <td>INR ${esc(quote.gst_lakh ?? "n/a")}L</td>
      <td>INR ${esc(quote.gross_premium_lakh ?? "n/a")}L</td>
      <td>${esc(quote.quote_confidence_label || quote.quote_confidence?.band || quote.precision_mode || "n/a")}</td>
    </tr>`;
}

function renderQuoteLoadingRows(quote, quoteLabel) {
  if (!quote?.covers_priced?.length) return "";
  return quote.covers_priced.map(cover => {
    const l = cover.loadings || {};
    return `
      <tr>
        <td>${esc(quoteLabel)}</td>
        <td>${esc(cover.cover_name || labelize(cover.cover_key))}</td>
        <td>${esc(cover.exposure_label || "")}</td>
        <td>${esc(fmtMethodRate(cover))}</td>
        <td>${fmtMethodMult(l.risk)}</td>
        <td>${fmtMethodMult(l.stage)}</td>
        <td>${fmtMethodMult(l.sector)}</td>
        <td>${fmtMethodMult(l.climate)}</td>
        <td>${fmtMethodMult(l.controls)}</td>
        <td>${fmtMethodMult(l.claims)}</td>
        <td>${fmtMethodMult(l.revenue)}</td>
        <td>${fmtMethodMult(l.records)}</td>
        <td>${cover.loading_cap_applied ? "Yes" : "No"}</td>
        <td>${esc(cover.quote_confidence?.band || cover.quote_confidence_band || cover.precision_mode || "n/a")}</td>
      </tr>`;
  }).join("");
}

function renderPricingMethodologyAppendix(result = {}) {
  const bundleQ = result.bundle_only_pricing_quote || {};
  const fullQ = result.pricing_engine_quote || {};
  const profile = result.profile || {};
  const loadingRows = [
    renderQuoteLoadingRows(bundleQ, "Bundle quote"),
    renderQuoteLoadingRows(fullQ, "Full recommended cover"),
  ].join("");
  const summaryRows = [
    renderQuoteMathSummaryRows(bundleQ, "Bundle quote"),
    renderQuoteMathSummaryRows(fullQ, "Full recommended cover"),
  ].join("");
  const stage = profile.funding_stage || "not supplied";
  const sector = profile.sector || "not supplied";
  const climate = profile.facility_climate_risk_zone || "Low / default";
  const records = profile.data_records_lakhs ?? profile.records_count ?? "not supplied";
  const revenue = profile.annual_revenue_cr ?? profile.revenue_cr ?? "not supplied";
  const claims = profile.claims_last_3_years ?? "unknown / not confirmed";

  return `
    <div class="hc-step">
      <div class="hc-step-head"><div class="hc-step-num">6</div><div class="hc-step-title">Actual quote views priced by SPARC</div></div>
      <div class="hc-step-body">
        <p>SPARC creates two quote views. <strong>Bundle quote</strong> prices only the covers inside the recommended bundle. <strong>Full recommended cover</strong> prices the bundle covers plus additional critical or recommended standalone products.</p>
        <table class="hc-mini-table hc-wide-table">
          <thead><tr><th>Quote view</th><th>Covers</th><th>Total SI</th><th>Subtotal</th><th>Bundle discount</th><th>Net</th><th>GST</th><th>Gross</th><th>Precision</th></tr></thead>
          <tbody>${summaryRows || `<tr><td colspan="9">Quote has not been generated yet.</td></tr>`}</tbody>
        </table>
        <p class="hc-note">Formula: Gross premium = (sum of cover premiums - bundle discount) x 1.18. GST is applied after the discount, not before it.</p>
      </div>
    </div>

    <div class="hc-step">
      <div class="hc-step-head"><div class="hc-step-num">7</div><div class="hc-step-title">Input-derived weightages used in this quote</div></div>
      <div class="hc-step-body">
        <p>The table below shows the actual multipliers returned by the pricing engine for the current SPARC input. These are the weightages applied after the selected exposure, base rate, and pricing basis are chosen.</p>
        <table class="hc-mini-table hc-wide-table">
          <thead>
            <tr>
              <th>View</th><th>Cover</th><th>Exposure</th><th>Base / ROL</th><th>Risk</th><th>Stage</th><th>Sector</th><th>Climate</th><th>Controls</th><th>Claims</th><th>Revenue</th><th>Records</th><th>Cap?</th><th>Confidence</th>
            </tr>
          </thead>
          <tbody>${loadingRows || `<tr><td colspan="14">No cover-level weightages available yet.</td></tr>`}</tbody>
        </table>
        <p class="hc-note">For liability covers at enterprise limits, SPARC may replace base-rate multiplication with enterprise Rate on Line (ROL). In those rows, the displayed ROL is the governing pricing rate.</p>
      </div>
    </div>

    <div class="hc-step">
      <div class="hc-step-head"><div class="hc-step-num">8</div><div class="hc-step-title">How entered inputs change the weightages</div></div>
      <div class="hc-step-body">
        <table class="hc-mini-table">
          <thead><tr><th>Input entered in SPARC</th><th>Current value</th><th>Pricing effect</th><th>Weightage rule</th></tr></thead>
          <tbody>
            <tr><td>Funding stage</td><td>${esc(stage)}</td><td>Later-stage companies carry higher stakeholder, investor, and contract exposure.</td><td>Pre-seed 0.90x, Seed 1.00x, Series A 1.12x, Series B+ 1.28x.</td></tr>
            <tr><td>Average risk score per cover</td><td>Cover-specific</td><td>Higher score increases the risk loading, but it is capped.</td><td>Risk loading = 0.75 + 0.75 x risk_score/100, capped at 1.50x.</td></tr>
            <tr><td>Sector</td><td>${esc(sector)}</td><td>Sector modifies only relevant covers, e.g. fintech cyber/PI, logistics motor, healthtech healthcare PI.</td><td>Sector loading comes from cover-specific adjustment maps; default is 1.00x.</td></tr>
            <tr><td>Climate zone</td><td>${esc(climate)}</td><td>Applies to property, BI, parametric, and marine-style physical exposure.</td><td>Low 1.00x, Medium 1.08x, High 1.18x, Extreme / Very High 1.32x.</td></tr>
            <tr><td>Controls</td><td>CERT-In POC, POSH IC, data localisation where supplied</td><td>Good controls reduce specific cover loading.</td><td>Cyber CERT-In POC 0.92x; full onshore data localisation 0.96x; POSH controls for benefit/people covers 0.97x.</td></tr>
            <tr><td>Claims history</td><td>${esc(String(claims))}</td><td>Confirmed prior claims increase premium; unknown claims reduce confidence and trigger checks.</td><td>Claims loading = 1.00 + 0.15 per claim, capped at 1.75x.</td></tr>
            <tr><td>Revenue</td><td>${esc(String(revenue))}</td><td>Applies to cyber, PI, financial services PI, healthcare PI, payment protection, product recall.</td><td>&lt;5Cr 0.92x; 5-20Cr 1.00x; 20-50Cr 1.08x; 50-100Cr 1.15x; 100Cr+ 1.20x.</td></tr>
            <tr><td>Data records</td><td>${esc(String(records))}</td><td>Applies to cyber; large record counts also trigger DPDP/SDF validation.</td><td>&lt;1 lakh 0.95x; 1-10 lakh 1.00x; 10-50 lakh 1.10x; 50-100 lakh 1.20x; 100 lakh+ 1.30x.</td></tr>
            <tr><td>Employee count</td><td>${esc(String(profile.team_size || "not supplied"))}</td><td>Drives group health, PA, EPL, and people-risk exposure.</td><td>Group health uses per-head burning cost: 500+ lives 0.12-0.18L; 100-499 lives 0.13-0.20L; below 100 lives 0.15-0.24L, risk-adjusted.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="hc-step">
      <div class="hc-step-head"><div class="hc-step-num">9</div><div class="hc-step-title">Step-by-step premium calculation</div></div>
      <div class="hc-step-body">
        <ol class="hc-list">
          <li><strong>Select covers to price:</strong> bundle quote uses only bundle mandatory covers; full recommended cover uses bundle covers plus critical/recommended standalone products.</li>
          <li><strong>Infer or read underwriting inputs:</strong> limits, property SI, employee count, fleet count, cargo turnover, receivables, and other exposures are prepared before pricing.</li>
          <li><strong>Price each cover individually:</strong> most covers use Exposure x Base rate x Combined loading.</li>
          <li><strong>Apply loadings:</strong> risk, stage, sector, climate, controls, claims, revenue, and records are multiplied together.</li>
          <li><strong>Cap excessive loading:</strong> risk loading is capped at 1.50x; combined loading is capped at 4.00x, with liability-like covers capped more tightly at 2.00x.</li>
          <li><strong>Use enterprise ROL for large liability limits:</strong> for large liability SI, premium may be Limit x Rate on Line instead of startup base-rate math.</li>
          <li><strong>Apply minimum premium:</strong> each cover has a minimum viable premium floor.</li>
          <li><strong>Sum all cover premiums:</strong> subtotal = sum of all priced covers.</li>
          <li><strong>Apply bundle discount:</strong> 5% for 3-4 covers and 10% for 5+ covers when a named bundle is priced.</li>
          <li><strong>Add GST:</strong> GST = net premium x 18%; gross = net + GST.</li>
          <li><strong>Set precision mode:</strong> technically priced, directional only, or underwriter validation required depending on missing data, large limits, specialty exposures, and benchmark comparability.</li>
        </ol>
        <p class="hc-note">Complete formula: cover premium = max(minimum premium, exposure x base rate x capped loading). For enterprise liability: cover premium = limit x ROL. Portfolio gross = (sum of covers - discount) x 1.18.</p>
      </div>
    </div>

    <div class="hc-step">
      <div class="hc-step-head"><div class="hc-step-num">10</div><div class="hc-step-title">References behind the pricing structure</div></div>
      <div class="hc-step-body">
        <table class="hc-mini-table">
          <thead><tr><th>Reference type</th><th>What it supports</th><th>Source</th></tr></thead>
          <tbody>
            <tr><td>Code reference</td><td>Premium math is deterministic and outside GenAI.</td><td><code>pricing_engine.py</code> module header and <code>_price_cover</code>.</td></tr>
            <tr><td>Code reference</td><td>GST, caps, enterprise thresholds, ROL bands, PricingRule metadata.</td><td><code>pricing_engine.py</code>: constants, <code>ENTERPRISE_LIABILITY_ROL_BANDS</code>, <code>PricingRule</code>.</td></tr>
            <tr><td>Code reference</td><td>Bundle-only vs full recommended cover quote split.</td><td><code>startup_shield_web/server.py</code>: two calls to <code>price_output_stage</code>.</td></tr>
            <tr><td>GST</td><td>Commercial/group insurance premiums use 18% GST in the app.</td><td><a href="https://www.financialservices.gov.in/beta/index.php/en/exemption-on-gst" target="_blank" rel="noopener">Department of Financial Services GST note</a>.</td></tr>
            <tr><td>Property segmentation</td><td>Bharat Sookshma up to INR 5Cr and Bharat Laghu from INR 5Cr to INR 50Cr support property thresholds.</td><td><a href="https://taxguru.in/corporate-law/standard-products-fire-allied-perils-insurance-business.html" target="_blank" rel="noopener">Standard fire/allied perils products summary</a>.</td></tr>
            <tr><td>Tariff status</td><td>IRDAI tariff de-notification supports market-driven indicative pricing, not fixed tariff lookup.</td><td><a href="https://irdai.gov.in/notifications" target="_blank" rel="noopener">IRDAI notifications</a>.</td></tr>
            <tr><td>D&amp;O underwriting basis</td><td>D&amp;O pricing/referral uses ownership, governance, securities exposure, transactions, prior notices, and claims-made context.</td><td><a href="https://www.hdfcergo.com/documents/Downloads/proposalform/directors-and-officers-liability-insurance-proposal-form.pdf" target="_blank" rel="noopener">HDFC ERGO D&amp;O proposal form</a>.</td></tr>
            <tr><td>Marine basis</td><td>Marine open policy pricing is turnover / limit-per-sending led, not generic SI-led.</td><td><a href="https://www.newindia.co.in/marine/open-policy-for-cargo" target="_blank" rel="noopener">New India Assurance Open Policy for Cargo</a>.</td></tr>
            <tr><td>Trade credit basis</td><td>Trade credit depends on turnover, payment terms, buyers, countries, and loss history.</td><td><a href="https://www.allianz-trade.com/en_US/what-is-trade-credit-insurance/credit-insurance-cost.html" target="_blank" rel="noopener">Allianz Trade credit insurance cost guide</a>.</td></tr>
            <tr><td>Group health basis</td><td>Group health requires census-style employee/dependent data; headcount-only output should remain directional.</td><td><a href="https://www.rahejaqbe.com/uploads/images/group-health/pdf/download/Proposal-Form-Group-Health-Insurance-V01.pdf" target="_blank" rel="noopener">Example group health proposal form</a>.</td></tr>
          </tbody>
        </table>
        <p class="hc-note">Heuristic disclosure: exact base rates, enterprise ROL bands, risk/stage/sector multipliers, bundle discounts, confidence thresholds, and 85%-120% display ranges are commercial assumptions for an indicative engine. They should be calibrated against real quote logs, sold-policy premiums, underwriter appetite matrices, and loss-ratio reviews before being described as market-calibrated.</p>
      </div>
    </div>`;
}

function renderMethodologyModal(result = {}) {
  return `
  <div id="how-calc-modal" class="hc-overlay" style="display:none" onclick="if(event.target===this)toggleHowCalculated(false)">
    <div class="hc-drawer" onclick="event.stopPropagation()">
      <div class="hc-header">
        <div>
          <div class="card-label">Pricing methodology</div>
          <h2 class="hc-title">How SPARC calculates your estimated premium</h2>
        </div>
        <button class="hc-close" onclick="toggleHowCalculated(false)" aria-label="Close">&#x2715;</button>
      </div>
      <div class="hc-body">
        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">1</div><div class="hc-step-title">Benchmark layer</div></div>
          <div class="hc-step-body">
            <p>SPARC keeps startup benchmark ranges separate from quote math. Benchmarks are assumption-led orientation ranges under standard startup conditions, not insurer-approved tariffs, bindable quotes, or final market averages.</p>
            <p class="hc-note">If the selected structure is outside the startup benchmark box, the benchmark is suppressed and the UI shows why it is not comparable.</p>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">2</div><div class="hc-step-title">Quote layer</div></div>
          <div class="hc-step-body">
            <p>Each cover is priced using a line-specific basis before any risk adjustment is applied. This prevents marine, group health, property, and liability covers from being forced through one generic formula.</p>
            <table class="hc-mini-table">
              <thead><tr><th>Product type</th><th>Pricing basis</th><th>Primary exposure</th></tr></thead>
              <tbody>
                <tr><td>Cyber, D&amp;O, PI, Crime</td><td>limit_based_liability / fidelity_limit_with_controls</td><td>Selected liability limit plus controls and claims history</td></tr>
                <tr><td>Public, CGL, Product Liability</td><td>premises_operations_liability / turnover_plus_limit_liability</td><td>Limit, site or product hazard, and operating footprint</td></tr>
                <tr><td>Group Health / PA</td><td>employee_benefit_census</td><td>Lives, census, age mix, plan design, and claims experience</td></tr>
                <tr><td>Property / Engineering</td><td>asset_value_property / project_value_engineering</td><td>Declared asset value, project value, occupancy, and site complexity</td></tr>
                <tr><td>Marine / Trade Credit</td><td>annual_transit_turnover / credit_turnover_or_receivables</td><td>Transit turnover, max-send, routes, debtors, and payment terms</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">3</div><div class="hc-step-title">Referral layer</div></div>
          <div class="hc-step-body">
            <p>When a cover leaves SPARC's calibrated operating box, the engine reduces precision instead of compounding penalties into a false point estimate. Large limits, missing census data, unconfirmed marine max-send, missing debtor data, specialty hardware, or unknown claims history can move a cover to directional-only or underwriter-required.</p>
            <table class="hc-mini-table">
              <thead><tr><th>Confidence mode</th><th>Display</th><th>Meaning</th></tr></thead>
              <tbody>
                <tr><td>Technically priced</td><td>Point estimate</td><td>Inputs are inside the deterministic startup pricing box.</td></tr>
                <tr><td>Directional only</td><td>Premium range</td><td>Useful for planning, but richer underwriting data is needed.</td></tr>
                <tr><td>Underwriter validation required</td><td>Precise display suppressed</td><td>Risk needs insurer or underwriter review before price presentation.</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">4</div><div class="hc-step-title">Explanation layer</div></div>
          <div class="hc-step-body">
            <p>Every quote carries confidence metadata, calibration basis, precision mode, benchmark comparability, and short explanation items. The UI uses that metadata to decide whether to show a point estimate, a range, or an underwriter-led referral message.</p>
            <p class="hc-note">Gross, net, discount, and GST totals remain numeric for auditability. Bundle discount is applied to subtotal first, then GST is calculated on the discounted net premium.</p>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">5</div><div class="hc-step-title">Claims discipline</div></div>
          <div class="hc-step-body">
            <p>SPARC is a deterministic, non-bindable pre-underwriting estimate tool. It can support planning and broker conversations, but it should not be read as a bindable quote, insurer-approved premium, compulsory cover determination, or final underwriting decision.</p>
          </div>
        </div>
        ${renderPricingMethodologyAppendix(result)}
      </div>
    </div>
  </div>`;
}

function renderDualPricingPanel(result) {
  const bundleQ = result.bundle_only_pricing_quote;
  const fullQ   = result.pricing_engine_quote;
  const bundleName = result.bundle_match?.name || "Recommended bundle";
  const fullCount  = fullQ?.covers_to_price?.length || fullQ?.cover_count || "";
  const fields  = fullQ?.required_inputs || bundleQ?.required_inputs || [];

  if ((!isQuoted(bundleQ) && !isQuoted(fullQ)) || state.quotePanelMode === "edit") {
    state.quotePanelMode = null;
    return renderQuoteInputPanel(fullQ || bundleQ);
  }

  return `
    <div class="pricing-split">
      ${renderPricePanel(bundleQ, "Bundle price", "bundle", bundleName)}
    </div>
    ${renderLiveSliderStrip(fields)}`;
}

function renderPricingQuote(quote) {
  if (!quote) return "";
  if (quote.quote_type === "input_required" || !quote?.covers_priced?.length) {
    return renderQuoteInputPanel(quote);
  }
  const covers = quote.covers_priced || [];
  const flags = quote.underwriter_referral_flags || [];
  const missing = quote.missing_inputs || [];
  const assumptions = quote.assumptions || [];
  const scale = quote.pricing_scale || {};
  const benchmark = quote.benchmark_comparison || {};
  const explanation = quote.explanation_items || [];
  return `
    <div class="pricing-card">
      <div class="pricing-head">
        <div>
          <div class="premium-card-label">Pricing engine quote</div>
          <div class="pricing-title">${esc(quoteDisplayText(quote))}</div>
          <div class="premium-card-note">${esc(quote.method || "Line-specific indicative pricing with capped loadings and referral rules.")}</div>
          ${confidenceBadge(quote.quote_confidence)}
          ${scale.label ? `<div class="premium-card-note"><strong>${esc(scale.label)}</strong> - ${esc(scale.message || "")}</div>` : ""}
          ${benchmark.status && benchmark.status !== "comparable" ? `<div class="premium-card-note"><strong>Benchmark:</strong> ${esc(benchmark.explanation || "Startup benchmark is not comparable to this selected structure.")}</div>` : ""}
        </div>
        <div class="pricing-totals">
          <div class="kv-row"><span class="kv-key">Net premium</span><span class="kv-val">INR ${esc(quote.net_premium_lakh)}L</span></div>
          <div class="kv-row"><span class="kv-key">GST</span><span class="kv-val">INR ${esc(quote.gst_lakh)}L</span></div>
          <div class="kv-row"><span class="kv-key">Total SI</span><span class="kv-val">INR ${esc(quote.total_sum_insured_cr)}Cr</span></div>
        </div>
      </div>
      <div class="pricing-cover-grid">
        ${covers.slice(0, 8).map(c => `
          <div class="pricing-cover">
            <div class="pricing-cover-name">${esc(c.cover_name || labelize(c.cover_key))} ${confidenceBadge(c.quote_confidence_band)}</div>
            <div class="pricing-cover-premium">${esc(coverPremiumText(c))}</div>
            <div class="pricing-cover-basis">${esc(c.exposure_label || "")} | ${esc((c.pricing_basis || "").replace(/_/g, " "))} | risk ${esc(c.average_risk_score ?? "n/a")}/100</div>
          </div>`).join("")}
      </div>
      ${explanation.length ? `<div class="pricing-explain">${explanation.map(x => `<div>${esc(x)}</div>`).join("")}</div>` : ""}
      ${flags.length || missing.length || assumptions.length ? `
        <div class="pricing-notes">
          ${flags.length ? `<div><div class="card-label">Underwriter checks</div>${flags.map(f => `<div class="callout-item compact"><span>${esc(f)}</span></div>`).join("")}</div>` : ""}
          ${missing.length ? `<div><div class="card-label">Inputs to confirm</div>${missing.map(m => `<div class="callout-item compact"><span>${esc(m)}</span></div>`).join("")}</div>` : ""}
          ${assumptions.length ? `<div><div class="card-label">Assumptions</div>${assumptions.map(a => `<div class="callout-item compact"><span>${esc(a)}</span></div>`).join("")}</div>` : ""}
        </div>` : ""}
    </div>`;
}

function quoteFieldValue(row) {
  const source = state.quoteInputs || {};
  for (const key of (row.aliases || [row.key])) {
    if (!Object.prototype.hasOwnProperty.call(source, key)) continue;
    const val = source[key];
    if (val !== undefined && val !== null && val !== "") return val;
  }
  return "";
}

function quoteFieldHasValue(row) {
  const source = state.quoteInputs || {};
  return (row.aliases || [row.key]).some(key => Object.prototype.hasOwnProperty.call(source, key));
}

function formatQuoteSuggestion(row) {
  const suggestion = row?.suggestion;
  if (!suggestion) return "";
  const value = suggestion.value;
  if (row.unit === "yes/no") return value ? "Yes" : "No";
  if (row.unit === "count") return String(Math.round(Number(value) || 0));
  const num = Number(value);
  if (!Number.isFinite(num)) return String(value ?? "");
  return `${num % 1 === 0 ? num.toFixed(0) : num.toFixed(2)}${row.unit ? ` ${row.unit}` : ""}`;
}

function quoteSuggestionPlaceholder(row) {
  const suggestion = formatQuoteSuggestion(row);
  return suggestion ? `Suggested: ${suggestion}` : "";
}

function renderQuoteSuggestion(row) {
  if (!row?.suggestion) return "";
  const text = formatQuoteSuggestion(row);
  const confidence = row.suggestion.confidence || "medium";
  const reason = row.suggestion.reason || "Estimated from startup profile.";
  return `
    <small class="quote-suggestion">
      <span>Suggested ${esc(text)} · ${esc(confidence)} confidence</span>
      <button type="button" onclick="applyQuoteSuggestion('${esc(row.key)}')">Use</button>
      <i>${esc(reason)}</i>
    </small>`;
}

window.setQuoteInput = (key, value) => {
  if (!state.quoteInputs) state.quoteInputs = {};
  if (value === "" || value === null || value === undefined || Number.isNaN(value)) {
    delete state.quoteInputs[key];
  } else {
    state.quoteInputs[key] = value;
  }
};

window.applyQuoteSuggestion = (key) => {
  const quote = window.__result?.pricing_engine_quote || window.__result?.bundle_only_pricing_quote || {};
  const row = (quote.required_inputs || []).find(item => item.key === key);
  if (!row?.suggestion) return;
  window.setQuoteInput(key, row.suggestion.value);
  // Re-render only the quote input panel — avoid full renderResults which flashes the page
  // and resets the active tab.
  const pricingCard = document.querySelector("#tab-quote .pricing-card");
  if (pricingCard) {
    const tmp = document.createElement("div");
    tmp.innerHTML = renderQuoteInputPanel(quote);
    pricingCard.replaceWith(tmp.firstElementChild);
  }
};

function renderQfChip(row) {
  const val = quoteFieldValue(row);
  const hasSlider = !!SLIDER_RANGES[row.key] && row.unit !== "yes/no";
  const isToggle = row.unit === "yes/no";
  const conf = row.suggestion?.confidence || "medium";

  let displayVal;
  if (isToggle) {
    displayVal = val ? "Yes" : "No";
  } else if (row.unit === "count") {
    displayVal = `${Math.round(Number(val) || 0)} ${row.unit}`;
  } else {
    const n = Number(val);
    displayVal = `${Number.isFinite(n) ? (n % 1 === 0 ? n.toFixed(0) : n.toFixed(2)) : (val || "—")} ${row.unit || "Cr"}`;
  }

  const confBadge = conf !== "high"
    ? `<span class="qf-chip-conf qf-conf-${conf}">${conf === "medium" ? "MED" : "LOW"}</span>`
    : "";

  if (hasSlider) {
    return `
      <div class="qf-chip qf-chip--expandable" id="qf-chip-${esc(row.key)}" onclick="toggleQfChip('${esc(row.key)}')">
        <div class="qf-chip-inner">
          <span class="qf-chip-label">${esc(row.label)}</span>
          <div class="qf-chip-right">
            ${confBadge}
            <span class="qf-chip-val">${esc(displayVal)}</span>
            <svg class="qf-chip-icon" viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6l4 4 4-4"/></svg>
          </div>
        </div>
        <div class="qf-chip-expand" id="qf-expand-${esc(row.key)}" style="display:none;">
          ${renderLiveSliderField(row)}
          ${row.help ? `<small style="font-size:11px;color:var(--ink-muted);margin-top:4px;display:block;">${esc(row.help)}</small>` : ""}
        </div>
      </div>`;
  }

  if (isToggle) {
    return `
      <div class="qf-chip qf-chip--toggle">
        <div class="qf-chip-inner">
          <span class="qf-chip-label">${esc(row.label)}</span>
          <div class="qf-chip-right">
            ${confBadge}
            <select class="qf-chip-select"
              onchange="setQuoteInput('${esc(row.key)}', this.value === 'yes'); event.stopPropagation();">
              <option value="no" ${!val ? "selected" : ""}>No</option>
              <option value="yes" ${val ? "selected" : ""}>Yes</option>
            </select>
          </div>
        </div>
      </div>`;
  }

  return `
    <div class="qf-chip">
      <div class="qf-chip-inner">
        <span class="qf-chip-label">${esc(row.label)}</span>
        <div class="qf-chip-right">
          ${confBadge}
          <span class="qf-chip-val">${esc(displayVal)}</span>
        </div>
      </div>
    </div>`;
}

window.toggleQfChip = (key) => {
  const chip = document.getElementById(`qf-chip-${key}`);
  const expand = document.getElementById(`qf-expand-${key}`);
  if (!chip || !expand) return;
  const open = expand.style.display !== "none";
  expand.style.display = open ? "none" : "block";
  chip.classList.toggle("qf-chip--open", !open);
};

function renderQuoteInputPanel(quote) {
  const fields = quote.required_inputs || [];
  const covers = quote.covers_to_price || [];
  // Pre-fill every field on first render — never leave a blank that blocks quoting.
  // Priority: suggestion value → slider min → type default. Never overwrites user edits.
  if (!state.quoteSuggestionsPreFilled) {
    fields.forEach(row => {
      if (quoteFieldHasValue(row)) return;
      if (row.suggestion != null) {
        window.setQuoteInput(row.key, row.suggestion.value);
      } else if (SLIDER_RANGES[row.key]) {
        window.setQuoteInput(row.key, SLIDER_RANGES[row.key].min);
      } else if (row.unit === "yes/no") {
        window.setQuoteInput(row.key, false);
      } else if (row.unit === "count") {
        window.setQuoteInput(row.key, 1);
      } else {
        window.setQuoteInput(row.key, 1);
      }
    });
    state.quoteSuggestionsPreFilled = true;
  }

  const html = `
    <div class="pricing-card">
      <div class="qf-card-head">
        <div>
          <div class="premium-card-label">Estimated quote</div>
          <div class="qf-confirmed-line">
            <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="2,8 6,12 14,4"/></svg>
            Coverage limits confirmed from your profile
          </div>
          <div class="qf-hint">All inputs pre-filled. Tap any field to adjust, then generate.</div>
        </div>
        <button class="btn btn-primary qf-generate-btn" type="button" onclick="generatePricingEstimate()">Generate quote</button>
      </div>
      ${covers.length ? `
        <div class="cover-pills qf-cover-pills">
          ${covers.slice(0, 10).map(c => `<span class="cover-pill">${esc(c.cover_name || labelize(c.cover_key))}</span>`).join("")}
        </div>` : ""}
      <div class="qf-chips-grid">
        ${fields.map(row => renderQfChip(row)).join("")}
      </div>
      <div class="qf-footer">
        <span id="pricing-estimate-status" style="font-size:12px;color:var(--ink-muted);"></span>
        <span id="quote-live-badge" class="ls-badge" style="opacity:0">Updating…</span>
      </div>
    </div>`;

  // Auto-generate when inputs are available
  if (fields.length > 0) {
    setTimeout(() => {
      if (window.__result && !isQuoted(window.__result?.bundle_only_pricing_quote) && !isQuoted(window.__result?.pricing_engine_quote)) {
        generatePricingEstimate();
      }
    }, 150);
  }

  return html;
}

async function generatePricingEstimate() {
  const status = $("pricing-estimate-status");
  if (status) status.textContent = "Calculating from submitted inputs...";
  state.profile.quote_requested = true;
  // Remember which tab is active so we can restore it after re-render
  const activeTab = document.querySelector(".snav-pill.snav-active")?.id?.replace("snav-", "") || "quote";
  try {
    const payload = buildProfile();
    payload.quote_requested = true;
    payload.quote_user_inputs = { ...(state.quoteInputs || {}) };
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    if (!res.ok || result.error) throw new Error(result.error || "Failed");
    renderResults(result);
    showTab(activeTab);
  } catch (err) {
    if (status) status.textContent = `Error: ${err.message}`;
  }
}

function overallLabel(score) {
  if (score >= 70) return "High exposure — prioritise critical covers and governance actions now.";
  if (score >= 45) return "Moderate exposure — buy essentials first and review quarterly.";
  return "Lower exposure — start with baseline covers and revisit as you scale.";
}

function renderActionBanner(recs) {
  if (!recs?.length) return "";
  const critical = recs.filter(r => r.priority === "Critical").slice(0, 3);
  if (!critical.length) return "";
  return `
    <div class="action-banner">
      <div class="action-banner-title">Buy now — ${critical.length} critical cover${critical.length>1?"s":""} for your profile</div>
      ${critical.map(r => `
        <div class="action-item-row">
          <span class="action-item-name">${esc(r.name||r.key)}</span>
          ${r.premium ? `<span class="action-price-tag">INR ${r.premium.min_lakh.toFixed(1)}-${r.premium.max_lakh.toFixed(1)}L</span>` : ""}
          <span class="action-why">${esc(r.nudge||"")}</span>
        </div>`).join("")}
    </div>`;
}

function renderScoreBars(scores) {
  const all = Object.entries(scores).sort((a,b) => b[1]-a[1]);
  const critical = all.filter(([,s]) => s >= 70);
  const watch    = all.filter(([,s]) => s >= 40 && s < 70);
  const low      = all.filter(([,s]) => s < 40);

  const renderItem = ([name, score]) => {
    const lvl = score >= 70 ? "critical" : score >= 40 ? "watch" : "low";
    const badgeLabel = score >= 70 ? "Critical" : score >= 40 ? "Watch" : "Low";
    return `
      <div class="score-bar-item${lvl === "critical" ? " sbi-critical-item" : ""}">
        <div class="sbi-head">
          <span class="sbi-name">${esc(name)}</span>
          <div class="sbi-right">
            <span class="sbi-score">${score}</span>
            <span class="badge badge-${lvl}">${badgeLabel}</span>
          </div>
        </div>
        <div class="sbi-bar">
          <div class="sbi-fill ${lvl}" style="width:${Math.min(100,score)}%"></div>
        </div>
      </div>`;
  };

  const parts = [];
  if (critical.length) parts.push(`<div class="sbi-tier-label sbi-tier-critical">Critical exposure — ${critical.length} categor${critical.length===1?"y":"ies"}</div>${critical.map(renderItem).join("")}`);
  if (watch.length)    parts.push(`<div class="sbi-tier-label">Watch — ${watch.length} categor${watch.length===1?"y":"ies"}</div>${watch.map(renderItem).join("")}`);
  if (low.length)      parts.push(`<div class="sbi-tier-label">Low exposure — ${low.length} categor${low.length===1?"y":"ies"}</div>${low.map(renderItem).join("")}`);
  return parts.join("");
}

const emptyState = (icon, title, sub="") => `
  <div class="empty-state">
    <div class="empty-state-icon">${icon}</div>
    <div class="empty-state-title">${title}</div>
    ${sub ? `<div class="empty-state-sub">${sub}</div>` : ""}
  </div>`;

function renderDriverCards(risks) {
  if (!risks?.length) return emptyState("📊", "No risk drivers available", "Run the analysis to see your top risk drivers.");
  const explanations = {
    "Cyber Technical Risk": "Digital footprint, data sensitivity and cloud posture create breach and continuity exposure.",
    "Data Privacy Risk": "Personal or sensitive data creates consent, fiduciary, retention and breach-notification obligations.",
    "Regulatory Compliance Risk": "Sector or selected exposure carries licensing, audit, reporting or statutory compliance pressure.",
    "Governance & Fraud Risk": "Investors, controls, fraud exposure and board accountability drive D&O and crime coverage needs.",
    "Liability Risk": "Customer contracts, product failures and negligence claims create third-party loss exposure.",
    "IP Infringement Risk": "AI training data, copyrights and patent landscape create escalating IP litigation risk.",
  };
  return risks.map((r, i) => `
    <div class="driver-card">
      <div class="driver-rank">#${i+1} Driver</div>
      <div class="driver-name">${esc(r.name)}</div>
      <div class="driver-score-row">
        <div class="driver-score-num">${r.score}</div>
        <div class="sbi-bar" style="flex:1;"><div class="sbi-fill critical" style="width:${Math.min(100,r.score)}%"></div></div>
      </div>
      <div class="driver-desc">${explanations[r.name] || "This category is above the rest of your profile and should be reviewed with controls and coverage."}</div>
    </div>`).join("");
}

function renderProductCards(recs, mapping, why = {}) {
  const byKey = Object.fromEntries((mapping||[]).map(r=>[r.key, r]));
  if (!recs?.length) return `<p style="color:var(--ink-muted)">No recommended products.</p>`;
  const appetiteLabels = { good:"Good risk", moderate:"Moderate", bad:"Not preferred", tbd:"Under review" };
  return recs.map(p => {
    const prio = p.priority || "Optional";
    const prioClass = prio === "Critical" ? "critical" : prio === "Recommended" ? "recommended" : "";
    const prioFlag = prio !== "Optional" ? `<div class="product-card-flag flag-${prio.toLowerCase()}">${esc(prio)} cover</div>` : "";
    return `
      <div class="product-card ${prioClass}">
        ${prioFlag}
        <div class="product-card-name">${esc(p.name||p.key)}</div>
        <div class="product-card-tags">
          <span class="product-tag score">${p.score}/100 fit</span>
          <span class="product-tag appetite-${p.appetite||"tbd"}">${appetiteLabels[p.appetite||"tbd"]}</span>
          ${p.mandatory ? `<span class="product-tag baseline">Baseline</span>` : ""}
        </div>
        <div class="product-card-il"><strong>ICICI Lombard:</strong> ${esc(p.il_product||"")}</div>
        <div class="product-card-nudge">${esc(getProductWhy(p, why) || p.nudge || "")}</div>
        ${p.premium ? `
          <div class="product-premium">
            <div class="product-premium-amount">INR ${p.premium.min_lakh.toFixed(1)} - ${p.premium.max_lakh.toFixed(1)}L</div>
            <div class="product-premium-basis">${esc(p.premium.basis)}</div>
          </div>` : ""}
      </div>`;
  }).join("");
}

function renderBadProducts(products) {
  if (!products?.length) return "";
  return `
    <details style="margin-top:16px;">
      <summary style="cursor:pointer;font-size:13px;font-weight:700;color:var(--ink-muted);padding:4px 0;">
        Available but not preferred (${products.length})
      </summary>
      <div class="products-grid" style="margin-top:12px;">${products.map(p=>`
        <div class="product-card">
          <div class="product-card-flag" style="color:var(--ink-faint);">Not preferred</div>
          <div class="product-card-name">${esc(p.name||p.key)}</div>
          <div class="product-card-desc" style="font-style:italic;">${esc(p.bad_reason||"Not preferred for this sector.")}</div>
        </div>`).join("")}
      </div>
    </details>`;
}

// ── Claims scenarios ─────────────────────────────────────────────
// Keyed as COVER_KEY → { default, SECTOR_NAME }. Pick sector variant first, fall back to default.
const CLAIMS_SCENARIOS = {
  cyber_liability: {
    Fintech: {
      event: "Payment API breach exposes transaction records for 800,000 customers",
      exposure_label: "Uninsured exposure",
      exposure: "₹15–60 Cr",
      costs: [
        "CERT-In 6-hour mandatory reporting + forensic audit: ₹1.5–3 Cr",
        "Customer notification (SMS + email to 800K): ₹40–80L",
        "DPDP Act civil penalty exposure: up to ₹250 Cr per incident",
        "Regulatory response team + legal counsel: ₹2–5 Cr",
      ],
      with_cover: "Cyber policy covers forensic investigation, breach notification costs, regulatory defence, and civil penalties — activating the moment the incident is reported.",
    },
    Healthtech: {
      event: "Patient records for 200,000 users exfiltrated via a third-party EMR integration",
      exposure_label: "Uninsured exposure",
      exposure: "₹8–25 Cr",
      costs: [
        "Patient notification + credit monitoring setup: ₹60L–1.2 Cr",
        "Forensic investigation and remediation: ₹1–2.5 Cr",
        "NMC/MoHFW regulatory inquiry defence: ₹1–3 Cr",
        "DPDP Act penalty (sensitive health data): up to ₹250 Cr",
      ],
      with_cover: "Cyber policy covers breach response, patient notification, regulatory defence, and penalty exposure — including health data classified as sensitive personal data under DPDP.",
    },
    default: {
      event: "Ransomware attack encrypts production database; 3 weeks of downtime",
      exposure_label: "Uninsured exposure",
      exposure: "₹3–12 Cr",
      costs: [
        "Forensic investigation and system recovery: ₹80L–2 Cr",
        "CERT-In 6-hour reporting + government response: ₹40–80L",
        "Customer notification and PR crisis management: ₹60L–1.5 Cr",
        "Revenue loss during 3 weeks of downtime",
      ],
      with_cover: "Cyber policy covers forensic costs, system restoration, ransom negotiation support, regulatory response, and business interruption during the outage.",
    },
  },
  dno_liability: {
    default: {
      event: "Institutional investor sues board for alleged misrepresentation in the Series B pitch deck",
      exposure_label: "Per-director legal exposure",
      exposure: "₹2–8 Cr",
      costs: [
        "Legal defence for 3–4 board members: ₹1.5–4 Cr",
        "2-year dispute timeline — founders distracted, fundraising stalled",
        "Settlement or judgment: ₹3–15 Cr",
        "Personal assets of directors at risk without cover",
      ],
      with_cover: "D&O policy pays legal defence costs for each named director from day one, and covers settlements — protecting personal assets and keeping founders focused on the business.",
    },
    "Series B+": {
      event: "Series C investor claims board failed to disclose a material regulatory breach before the round closed",
      exposure_label: "Board-level liability",
      exposure: "₹5–20 Cr",
      costs: [
        "High Court securities litigation: ₹3–6 Cr in legal fees",
        "SEBI adjudication proceedings (if listed path): ₹1–3 Cr",
        "Potential rescission of investment round",
        "Reputational damage to founders' future fundraising",
      ],
      with_cover: "D&O policy covers director defence costs, regulatory investigation fees, and any final judgment — regardless of which director is named.",
    },
  },
  professional_indemnity: {
    Fintech: {
      event: "Payment gateway logs 4 hours of unplanned downtime during a client's peak sale event",
      exposure_label: "Contract breach claim",
      exposure: "₹5–18 Cr",
      costs: [
        "Client claims ₹12 Cr in lost transaction revenue",
        "SLA penalty clauses triggered across 3 enterprise clients",
        "Legal arbitration costs: ₹80L–2 Cr",
        "Emergency engineering response + overtime: ₹30–60L",
      ],
      with_cover: "PI / Tech E&O policy covers client claims arising from your technology failure, SLA breach penalties, and arbitration costs — without you having to prove it wasn't negligence first.",
    },
    default: {
      event: "A bug in your SaaS platform causes a client to overbill 10,000 end customers",
      exposure_label: "Client claim exposure",
      exposure: "₹3–10 Cr",
      costs: [
        "Client's remediation and refund costs: ₹2–6 Cr",
        "NCDRC class action risk from end customers",
        "Legal defence and settlement: ₹1–4 Cr",
        "Contract termination + lost ARR",
      ],
      with_cover: "PI / Tech E&O covers the client's claim for financial loss caused by your software error — including defence costs before any liability is established.",
    },
  },
  product_liability: {
    "D2C / Consumer Brands": {
      event: "A manufacturing defect in your earphone causes a battery fire; one hospitalization, 12 NCDRC complaints filed",
      exposure_label: "Product recall + liability",
      exposure: "₹4–22 Cr",
      costs: [
        "Recall of 50,000 units across Amazon, Flipkart, D2Mart: ₹1.5–3 Cr",
        "Hospitalization compensation and legal defence: ₹80L–2 Cr",
        "NCDRC class action defence: ₹1–4 Cr",
        "Brand rehabilitation and PR campaign: ₹1–3 Cr",
      ],
      with_cover: "Product Liability policy covers bodily injury and property damage claims from product defects, recall costs, and NCDRC/consumer court defence — including strict liability under Consumer Protection Act 2019.",
    },
    Healthtech: {
      event: "A diagnostic device gives incorrect readings for 3 months; patient harm alleged in 8 cases",
      exposure_label: "Recall + patient liability",
      exposure: "₹8–30 Cr",
      costs: [
        "Device recall and replacement: ₹2–5 Cr",
        "NMC investigation + CDSCO regulatory response: ₹1–3 Cr",
        "Patient compensation claims (8 cases): ₹3–10 Cr",
        "Hospital partner contract penalties: ₹1–3 Cr",
      ],
      with_cover: "Product Liability covers patient injury claims, recall costs, and regulatory defence — including CDSCO proceedings for medical device failures.",
    },
    "Deeptech / AI / Robotics": {
      event: "A UAV loses control during an infrastructure survey; structural damage to third-party equipment and one injury",
      exposure_label: "Third-party liability",
      exposure: "₹1.5–8 Cr",
      costs: [
        "Third-party property damage: ₹40L–1.5 Cr",
        "Bodily injury claim: ₹80L–3 Cr",
        "DGCA investigation + potential Type Certificate suspension",
        "Legal defence: ₹50L–2 Cr",
      ],
      with_cover: "Drone RPAS policy (mandated by DGCA Rule 44) covers third-party bodily injury and property damage from drone operations — and protects your Type Certificate from regulatory action.",
    },
  },
  employment_practices: {
    default: {
      event: "Senior engineer claims wrongful termination after raising a code ethics complaint internally",
      exposure_label: "Employment tribunal exposure",
      exposure: "₹1–4 Cr",
      costs: [
        "Employment tribunal defence: ₹40–80L in legal fees",
        "Out-of-court settlement (industry average): ₹80L–2 Cr",
        "POSH-related harassment claim from same period: additional ₹30–60L",
        "HR compliance audit triggered by labour department",
      ],
      with_cover: "Employment Practices Liability policy covers legal defence and settlements for wrongful termination, discrimination, and harassment claims — without the founders personally funding the defence.",
    },
  },
  crime_fidelity: {
    Fintech: {
      event: "A finance team member diverts ₹2.3 Cr over 18 months via fake vendor invoices; discovered in year-end audit",
      exposure_label: "Internal fraud loss",
      exposure: "₹2.3 Cr (irrecoverable)",
      costs: [
        "Direct financial loss: ₹2.3 Cr — banks have no liability once transfers are authorised",
        "Forensic accounting to trace and document the fraud: ₹30–60L",
        "Legal recovery proceedings (low probability of full recovery)",
        "Regulatory disclosure obligations under RBI PA guidelines",
      ],
      with_cover: "Crime / Fidelity Guarantee policy covers direct financial loss from employee dishonesty — reimbursing the business as soon as the fraud is documented, not after a court verdict.",
    },
    default: {
      event: "An operations manager executes ₹85L in unauthorised bank transfers to a personal account over 6 months",
      exposure_label: "Fidelity fraud loss",
      exposure: "₹85L (unrecoverable)",
      costs: [
        "Bank's liability ends at point of authorisation — full loss on the company",
        "Forensic investigation: ₹15–30L",
        "Legal recovery: uncertain timeline, uncertain outcome",
        "Leadership distraction during critical fundraising period",
      ],
      with_cover: "Fidelity Guarantee covers employee dishonesty losses as soon as the fraud is proven — paid to the business directly, regardless of whether the employee is prosecuted.",
    },
  },
  property_all_risk: {
    "Deeptech / AI / Robotics": {
      event: "A lab fire destroys ₹8 Cr of drone assembly equipment and test rigs; 6-month lead time on replacement parts",
      exposure_label: "Asset replacement + BI loss",
      exposure: "₹10–18 Cr",
      costs: [
        "Equipment replacement at market value: ₹8 Cr",
        "6 months of lost revenue while operations halt: ₹3–8 Cr",
        "DGCA re-certification after equipment change: ₹20–40L",
        "Client penalty clauses triggered by delivery delays",
      ],
      with_cover: "Property All Risk policy covers replacement of lab equipment and machinery at reinstatement value, plus Business Interruption cover for lost revenue during the rebuild period.",
    },
    default: {
      event: "Flooding from an unseasonable monsoon event damages warehouse stock worth ₹4 Cr and halts operations for 6 weeks",
      exposure_label: "Asset + BI loss",
      exposure: "₹5–9 Cr",
      costs: [
        "Stock replacement: ₹4 Cr",
        "6 weeks' lost gross profit: ₹1–3 Cr",
        "Emergency relocation and logistics: ₹30–60L",
        "Supply chain penalties from unfulfilled orders",
      ],
      with_cover: "Property All Risk covers stock and asset damage at reinstatement value; Business Interruption add-on covers lost gross profit during the recovery period.",
    },
  },
  healthcare_pi: {
    Healthtech: {
      event: "A telemedicine platform's AI triage tool recommends incorrect dosage; adverse patient outcome triggers NMC inquiry",
      exposure_label: "Medical negligence claim",
      exposure: "₹3–15 Cr",
      costs: [
        "NMC / NBE regulatory proceedings: ₹80L–2 Cr",
        "Patient compensation claim: ₹2–8 Cr",
        "Platform audit and AI model documentation: ₹40–80L",
        "Hospital partner contract suspension",
      ],
      with_cover: "Healthcare PI covers professional negligence claims against the platform and its partner doctors — including AI-assisted clinical decision support errors that cause patient harm.",
    },
  },
  property_fire: {
    "Foodtech / Cloud Kitchen": {
      event: "A gas leak in a cloud kitchen ignites during peak service hours; the unit is gutted and operations halt for 11 weeks",
      exposure_label: "Asset loss + downtime",
      exposure: "₹1.5–4 Cr",
      costs: [
        "Kitchen equipment and fitout replacement: ₹80L–2 Cr",
        "Stock and raw material write-off: ₹20–50L",
        "11 weeks of lost revenue with fixed costs continuing: ₹60L–1.5 Cr",
        "Landlord's reinstatement demand under lease terms",
      ],
      with_cover: "Property Fire policy reinstates your kitchen assets at replacement value — letting you reopen without wiping out working capital or taking emergency debt.",
    },
    default: {
      event: "Electrical fault causes a fire at the primary office; servers, fixtures, and stock destroyed overnight",
      exposure_label: "Asset replacement cost",
      exposure: "₹1–3 Cr",
      costs: [
        "Equipment and furniture replacement: ₹60L–1.5 Cr",
        "Stock and inventory loss: ₹30–80L",
        "Emergency relocation + fit-out: ₹20–50L",
        "Weeks of downtime with payroll and rent continuing",
      ],
      with_cover: "Property Fire policy pays for reinstatement of damaged assets at current replacement cost — covering the full rebuild without dipping into working capital.",
    },
  },
  public_liability: {
    "Foodtech / Cloud Kitchen": {
      event: "A delivery rider slips on wet flooring at a cloud kitchen pickup bay; fractured wrist, consumer forum notice served within 48 hours",
      exposure_label: "Third-party bodily injury",
      exposure: "₹20–80L",
      costs: [
        "Hospitalization and medical bills: ₹5–15L",
        "Consumer forum or civil court claim: ₹15–50L",
        "Legal defence costs: ₹10–25L",
        "Reputational risk from social media coverage of the incident",
      ],
      with_cover: "Public Liability pays third-party injury and property damage claims arising from your premises or operations — covering legal defence and compensation without touching operating funds.",
    },
    default: {
      event: "A visitor at your office is injured when a ceiling fixture falls; they file a ₹40L negligence claim",
      exposure_label: "Third-party liability",
      exposure: "₹20–60L",
      costs: [
        "Medical costs and compensation: ₹15–40L",
        "Legal defence: ₹5–20L",
        "Court or settlement timeline: 12–24 months of management distraction",
      ],
      with_cover: "Public Liability covers compensation and legal defence costs for bodily injury or property damage to third parties at your premises — fully funded by the policy.",
    },
  },
  machinery_breakdown: {
    "Foodtech / Cloud Kitchen": {
      event: "A central blast chiller fails mid-week; ₹18L of perishable inventory is lost and the kitchen is offline for 9 days awaiting a replacement compressor",
      exposure_label: "Equipment + inventory loss",
      exposure: "₹25–70L",
      costs: [
        "Perishable stock write-off: ₹15–25L",
        "Emergency repair or replacement of compressor unit: ₹8–20L",
        "9 days of lost kitchen revenue: ₹10–30L",
        "Penalty clauses from food aggregator SLAs",
      ],
      with_cover: "Machinery Breakdown policy covers sudden mechanical failure and repair costs — plus consequential stock loss — so a single equipment failure doesn't cascade into a working capital crisis.",
    },
    default: {
      event: "A key production machine breaks down unexpectedly; a 3-week lead time on parts halts output entirely",
      exposure_label: "Repair + lost output",
      exposure: "₹30–90L",
      costs: [
        "Repair or replacement of the failed component: ₹15–40L",
        "Lost production revenue over 3 weeks: ₹20–60L",
        "Client penalties for delayed delivery: ₹10–25L",
      ],
      with_cover: "Machinery Breakdown covers sudden mechanical or electrical failure — repair costs, parts, and consequential business interruption — with no waiting for depreciation disputes.",
    },
  },
  group_personal_accident: {
    "Foodtech / Cloud Kitchen": {
      event: "A kitchen team member sustains a severe burn injury during service; permanently loses the use of two fingers on the dominant hand",
      exposure_label: "Employer liability + compensation",
      exposure: "₹15–50L",
      costs: [
        "Immediate hospitalization and surgery: ₹5–12L",
        "Permanent partial disability compensation (statutory): ₹10–30L",
        "Legal claim if no GPA cover; ESIC gap for non-covered workers",
        "Potential labour department inquiry",
      ],
      with_cover: "Group Personal Accident pays accidental death and disability benefits directly to the employee or dependants — covering the gap above ESIC and shielding the company from personal claims.",
    },
    default: {
      event: "Two field executives are involved in a road accident during a client visit; one sustains permanent partial disability",
      exposure_label: "Disability + legal exposure",
      exposure: "₹10–40L",
      costs: [
        "Medical treatment and rehabilitation: ₹5–15L",
        "Disability compensation statutory obligation: ₹8–25L",
        "Civil claim from employee if no group cover in place",
        "EPFO/ESIC compliance scrutiny triggered",
      ],
      with_cover: "Group Personal Accident pays accidental death, permanent disability, and temporary disability benefits — directly and promptly — without the company funding compensation from cash reserves.",
    },
  },
  employees_compensation: {
    "Foodtech / Cloud Kitchen": {
      event: "A delivery packer suffers a repetitive strain injury deemed work-related; Employees' Compensation Commissioner orders ₹6.2L payment within 30 days",
      exposure_label: "Statutory compensation order",
      exposure: "₹5–20L",
      costs: [
        "Commissioner's compensation award: ₹6.2L (immediate payment required)",
        "Legal defence before the EC Commissioner: ₹2–5L",
        "Penalty for delayed payment under ECA 1923: 50% additional sum",
        "Labour department follow-up audit across other workers",
      ],
      with_cover: "Employees' Compensation policy pays the statutory award directly — including the penalty for delayed payment — so the company avoids a cash crisis from an unexpected regulatory order.",
    },
    default: {
      event: "A warehouse worker falls from a loading platform; Employees' Compensation Commissioner orders ₹9L in statutory compensation",
      exposure_label: "Statutory EC award",
      exposure: "₹8–25L",
      costs: [
        "EC Commissioner award: ₹9L (must be paid within 30 days)",
        "Legal representation costs: ₹1–3L",
        "50% penalty if payment is delayed beyond the deadline",
        "Risk of labour department audit across all workers",
      ],
      with_cover: "Employees' Compensation cover pays the full statutory award, legal costs, and any penalty — activated the moment the Commissioner's order is issued, with no working capital impact.",
    },
  },
  money_insurance: {
    "Foodtech / Cloud Kitchen": {
      event: "A cash float held at a cloud kitchen for change and petty expenses is stolen during a break-in overnight",
      exposure_label: "Cash theft loss",
      exposure: "₹2–8L",
      costs: [
        "Cash-in-premises loss: ₹2–5L",
        "Safe damage and security upgrade: ₹50K–1.5L",
        "Police FIR and insurance documentation time: operational distraction",
      ],
      with_cover: "Money Insurance covers cash stolen from your premises, in transit, or from a safe — reimbursed promptly so petty cash operations and float management are not disrupted.",
    },
    default: {
      event: "Cash collected during a field sales drive is stolen from the courier; ₹4L unrecovered",
      exposure_label: "Cash-in-transit theft",
      exposure: "₹2–8L",
      costs: [
        "Direct cash loss: ₹4L (unrecoverable from courier unless proven negligence)",
        "Police and legal process: ₹20–50K",
        "Operational disruption and finance reconciliation costs",
      ],
      with_cover: "Money Insurance covers cash in transit and on premises against theft — reimbursing the full loss without needing to establish courier liability.",
    },
  },
};

function renderClaimsScenarios(result) {
  const bundle = result.bundle_match;
  if (!bundle) return "";
  const sector = result.profile?.sector || result.sector || "";
  // bundle_match.mandatory_covers uses short ALL-CAPS keys (e.g. "CYBER", "D_AND_O")
  // from research_config.json — normalise to the snake_case keys CLAIMS_SCENARIOS uses.
  const normKey = k => COVER_ALIASES[k] || COVER_ALIASES[String(k).toUpperCase()] || k;
  const mandatory = (bundle.mandatory_covers || []).map(normKey);

  // Build ordered list of covers to show: mandatory first, then high-risk optionals
  const scores = result.scores || {};
  const scoreOf = (cover) => {
    const spec = { cyber_liability: ["Cyber Technical Risk","Data Privacy Risk"], dno_liability: ["Governance & Fraud Risk","Regulatory Compliance Risk"], professional_indemnity: ["Liability Risk","IP Infringement Risk"], product_liability: ["Liability Risk","Reputation Risk"], employment_practices: ["Gig & Labour Risk","Governance & Fraud Risk"], crime_fidelity: ["Governance & Fraud Risk"], property_all_risk: ["Property Risk","ESG & Climate Risk"], property_fire: ["Property Risk","ESG & Climate Risk"], public_liability: ["Liability Risk","Operational Continuity Risk"], machinery_breakdown: ["Operational Continuity Risk","Property Risk"], group_personal_accident: ["People & HR Risk","Gig & Labour Risk"], employees_compensation: ["People & HR Risk","Gig & Labour Risk"], money_insurance: ["Governance & Fraud Risk"], healthcare_pi: ["Liability Risk"] };
    const keys = spec[cover] || [];
    if (!keys.length) return 0;
    return keys.reduce((s, k) => s + (parseFloat(scores[k]) || 0), 0) / keys.length;
  };

  const coverPriority = [...mandatory, ...(bundle.optional_covers || []).map(normKey)].filter(c => CLAIMS_SCENARIOS[c]);
  coverPriority.sort((a, b) => (mandatory.includes(b) ? 1 : 0) - (mandatory.includes(a) ? 1 : 0) || scoreOf(b) - scoreOf(a));

  const toShow = coverPriority.slice(0, 3);
  if (!toShow.length) return "";

  const scenarios = toShow.map(coverKey => {
    const bank = CLAIMS_SCENARIOS[coverKey];
    const s = bank[sector] || bank[result.profile?.funding_stage] || bank.default;
    if (!s) return null;
    return { coverKey, s };
  }).filter(Boolean);

  if (!scenarios.length) return "";

  const coverLabel = (k) => ({ cyber_liability:"Cyber Liability", dno_liability:"Directors & Officers", professional_indemnity:"PI / Tech E&O", product_liability:"Product Liability", employment_practices:"Employment Practices", crime_fidelity:"Crime / Fidelity", property_all_risk:"Property All Risk", property_fire:"Property Fire", public_liability:"Public Liability", machinery_breakdown:"Machinery Breakdown", group_personal_accident:"Group Personal Accident", employees_compensation:"Employees' Compensation", money_insurance:"Money Insurance", healthcare_pi:"Healthcare PI", drone_rpas:"Drone RPAS" }[k] || labelize(k));

  return `
    <div class="result-section">
      <div class="result-section-head">
        <div class="result-section-bar"></div>
        <div class="result-section-title">What happens without these covers</div>
      </div>
      <p class="cs-intro">Based on your profile and the covers flagged as mandatory, here are three realistic claim scenarios — the kind that happen every quarter in Indian startups at your stage.</p>
      <div class="cs-grid">
        ${scenarios.map(({ coverKey, s }) => `
          <div class="cs-card">
            <div class="cs-card-top">
              <span class="cs-cover-tag">${esc(coverLabel(coverKey))}</span>
              <span class="cs-mandatory-badge">${(bundle.mandatory_covers||[]).includes(coverKey) ? "Mandatory" : "Recommended"}</span>
            </div>
            <div class="cs-event">${esc(s.event)}</div>
            <div class="cs-exposure-row">
              <span class="cs-exposure-label">${esc(s.exposure_label)}</span>
              <span class="cs-exposure-val">${esc(s.exposure)}</span>
            </div>
            <ul class="cs-costs">
              ${s.costs.map(c => `<li>${esc(c)}</li>`).join("")}
            </ul>
            <div class="cs-with-cover">
              <span class="cs-with-label">With cover</span>
              <span>${esc(s.with_cover)}</span>
            </div>
          </div>`).join("")}
      </div>
    </div>`;
}

function getCoverColor(key) {
  const k = key.toLowerCase();
  if (/cyber/.test(k))                              return "#3B82F6";
  if (/pi|tech.*eo|professional.*indem|indemnity/.test(k)) return "#818CF8";
  if (/^d.?o|director/.test(k))                    return "#A78BFA";
  if (/crime|fidelit/.test(k))                      return "#FBBF24";
  if (/employ|epli/.test(k))                        return "#34D399";
  if (/property|fire|burglary/.test(k))             return "#F97316";
  if (/marine|cargo/.test(k))                       return "#22D3EE";
  if (/group|health|gtl|gpa|medical/.test(k))       return "#4ADE80";
  if (/liabilit/.test(k))                           return "#FB7185";
  if (/key.?person|keyman/.test(k))                 return "#F472B6";
  if (/work.*comp|wc|workmen/.test(k))              return "#60A5FA";
  return "#94A3B8";
}

function renderFitGauge(pct) {
  const r = 28, circ = 2 * Math.PI * r;
  const filled = (pct / 100) * circ;
  const color  = pct >= 75 ? "#4ADE80" : pct >= 50 ? "#FBBF24" : "#FB7185";
  return `<svg width="76" height="76" viewBox="0 0 72 72" aria-label="${pct}% profile fit">
    <circle cx="36" cy="36" r="${r}" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="5"/>
    <circle cx="36" cy="36" r="${r}" fill="none" stroke="${color}" stroke-width="5"
      stroke-dasharray="${filled.toFixed(1)} ${(circ - filled).toFixed(1)}"
      stroke-linecap="round" transform="rotate(-90 36 36)"/>
    <text x="36" y="33" text-anchor="middle" dominant-baseline="middle"
      font-size="13" font-weight="800" fill="${color}" font-family="inherit">${pct}%</text>
    <text x="36" y="46" text-anchor="middle" dominant-baseline="middle"
      font-size="8" font-weight="600" fill="rgba(255,255,255,.45)" letter-spacing=".08em">FIT</text>
  </svg>`;
}

function coverExposureLabel(key) {
  const k = String(key || "").toLowerCase();
  if (/cyber|data/.test(k)) return "Data breach and outage loss";
  if (/d.?and.?o|dno|director|officer/.test(k)) return "Board and governance liability";
  if (/pi|professional|tech.*eo|indemnity/.test(k)) return "Client negligence claims";
  if (/crime|fidelity|fraud/.test(k)) return "Internal fraud loss";
  if (/employers|workmen|workers|comp/.test(k)) return "Workforce injury liability";
  if (/employment|epl/.test(k)) return "Employment dispute defence";
  if (/public|cgl|general.?liability/.test(k)) return "Third-party injury or damage";
  if (/product|recall/.test(k)) return "Product failure or recall";
  if (/marine|cargo|transit/.test(k)) return "Goods movement loss";
  if (/property|fire|burglary|iar/.test(k)) return "Asset damage and downtime";
  if (/group.?health|health/.test(k)) return "Employee healthcare continuity";
  if (/group.?pa|accident/.test(k)) return "Employee accident benefit";
  return "Profile-specific exposure";
}

function renderBundleHero(bundle, recs, why = {}) {
  if (!bundle?.name) return `<div class="r-card">${emptyState("📦", "No bundle matched", "No packaged bundle was a strong enough fit for this profile. Recommended products are listed individually below.")}</div>`;

  const mandatory = bundle.mandatory_covers || [];
  const optional  = bundle.optional_covers  || [];
  const companion = bundle.companion_bundle || null;
  const eyebrow   = bundle.nearest_fallback ? "Closest package fit" : "Recommended package";
  const isOfficial = bundle.is_real_il_bundle === true || OFFICIAL_IL_BUNDLE_NAMES.has(bundle.name);

  const coverItems = [
    ...mandatory.map(c => ({ key: c, type: "mandatory" })),
    ...optional.map(c  => ({ key: c, type: "optional"  })),
  ];
  const companionCoverItems = companion ? [
    ...((companion.mandatory_covers || []).map(c => ({ key: c, type: "mandatory" }))),
    ...((companion.optional_covers || []).map(c => ({ key: c, type: "optional" }))),
  ] : [];

  const fitPct = bundle.fit_pct || 0;
  return `
    <div class="bundle-hero">
      <div class="bundle-hero-top">
        <div style="flex:1;min-width:0;">
          <div class="bundle-hero-eyebrow">${eyebrow}</div>
          <div class="bundle-hero-name">${esc(bundle.name)}</div>
          <div class="bundle-hero-il">${esc(bundle.il_product_name || "")}</div>
          <div class="bundle-hero-badges">
            <span class="bundle-badge-crit">${esc(bundle.criticality || "High")} Priority</span>
            <span class="bundle-badge ${isOfficial ? "real" : "curated"}">${isOfficial ? "Official IL Product" : "Curated Cover Set"}</span>
          </div>
        </div>
        <div class="bundle-fit-gauge-wrap">
          ${renderFitGauge(fitPct)}
          <div class="bundle-fit-gauge-label">Profile fit</div>
        </div>
      </div>

      <div class="bundle-hero-desc">${esc(bundle.description || "")}</div>
      ${why?.bundle ? `<div class="bundle-why-note">${esc(why.bundle)}</div>` : ""}
      <div class="bundle-decision-row">
        <div><span>Mandatory covers</span><strong>${mandatory.length}</strong></div>
        <div><span>Optional covers</span><strong>${optional.length}</strong></div>
        <div><span>Fit score</span><strong>${fitPct}%</strong></div>
        <div><span>RM action</span><strong>${esc(bundle.criticality || "Review")}</strong></div>
      </div>

      ${companion?.name ? `
        <div class="bundle-companion">
          <div class="bundle-companion-label">Also recommend alongside Group Safeguard</div>
          <div class="bundle-companion-main">
            <div>
              <div class="bundle-companion-name">${esc(companion.name)}</div>
              <div class="bundle-companion-desc">${esc(why?.companion_bundle || bundle.companion_note || "Group Safeguard handles workforce benefits; this second package addresses the startup's sector and operating risks.")}</div>
            </div>
            <div class="bundle-companion-fit">${companion.fit_pct || 0}% fit</div>
          </div>
          <div class="bundle-companion-covers">
            ${companionCoverItems.slice(0, 8).map(({ key, type }) => {
              const color = getCoverColor(key);
              return `
              <div class="bundle-cover-item compact">
                <div class="bundle-cover-icon" style="background:${color}22;color:${color};">${type === "optional" ? "Opt" : "Core"}</div>
                <div>
                  <div class="bundle-cover-name">${esc(labelize(key))}</div>
                  <div class="bundle-cover-blurb">${esc(getCoverWhy(key, why, "companion_covers"))}</div>
                </div>
              </div>`;
            }).join("")}
          </div>
        </div>` : ""}

      <div class="bundle-covers-label">Covers included - ${mandatory.length} mandatory · ${optional.length} optional</div>
      <div class="coverage-map">
        <div class="coverage-map-head">
          <span>Cover</span>
          <span>Exposure transferred</span>
          <span>Why it applies</span>
        </div>
        ${coverItems.map(({ key, type }) => {
          const blurb = getCoverWhy(key, why, "bundle_covers");
          const color = getCoverColor(key);
          return `
            <div class="coverage-map-row">
              <div class="coverage-cover">
                <span class="coverage-dot" style="background:${color};"></span>
                <div>
                  <div class="bundle-cover-name">${esc(labelize(key))}</div>
                  <div class="coverage-type">${type === "optional" ? "Optional add-on" : "Mandatory cover"}</div>
                </div>
              </div>
              <div class="coverage-exposure">${esc(coverExposureLabel(key))}</div>
              <div class="bundle-cover-blurb">${esc(blurb || "")}</div>
            </div>`;
        }).join("")}
      </div>

      ${(bundle.prerequisite_notes || []).map(n => `
        <div style="margin-top:14px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:var(--r-sm);padding:10px 14px;font-size:12px;color:rgba(255,255,255,.6);">${esc(n)}</div>`).join("")}
    </div>`;
}

function renderBundleAlternatives(bundles) {
  if (!bundles?.length) return "";
  const statusLabel = (b) => b.alternative_status === "tied" ? "Tied with top pick" : "Lesser relevant";
  return `
    <details class="expander-card" style="margin-top:14px;">
      <summary>Other bundle options (${bundles.length})</summary>
      <div class="expander-body">
        <div class="products-grid-2col">
          ${bundles.map(b => `
            <div class="product-card">
              <div class="product-card-flag">${statusLabel(b)} · Rank ${b.rank}</div>
              <div class="product-card-name">${esc(b.name)} <span class="product-tag score">${b.fit_pct || 0}% fit</span></div>
              <div class="product-card-desc">${esc(b.description || "")}</div>
              <div class="product-card-il">${esc(b.il_product_name || "")}</div>
              <div class="cover-pills" style="margin-top:8px;">
                ${(b.mandatory_covers || []).slice(0, 4).map(c => `<span class="cover-pill">${esc(labelize(c))}</span>`).join("")}
              </div>
            </div>`).join("")}
        </div>
      </div>
    </details>`;
}

function pct(v) {
  if (v === null || v === undefined || v === "") return "n/a";
  const n = Number(v);
  if (!Number.isFinite(n)) return esc(v);
  return `${Math.round(n * 100)}%`;
}

const SIGNAL_LABELS = {
  handles_pii:          "Handles personal data",
  rbi_licensed:         "RBI-licensed business",
  sebi_regulated:       "SEBI-regulated entity",
  healthtech:           "Health data processed",
  fintech:              "Financial services product",
  has_investors:        "Has institutional investors",
  ai_in_product:        "AI used in product",
  b2b_contracts:        "B2B contracts in place",
  physical_assets:      "Owns physical assets",
  gig_workers:          "Employs gig / contract workers",
  export_operations:    "Operates internationally",
  cert_in_obligations:  "CERT-In reporting obligations",
};

const RISK_FACTOR_LABELS = {
  claims_frequency: "How often claims occur in this sector",
  claims_freq:      "How often claims occur in this sector",
  settlement:       "Typical time to resolve a claim",
  settlement_time:  "Typical time to resolve a claim",
  regulatory_volatility: "How fast regulations are changing",
  market_saturation:     "Competition in this cover segment",
};

const RISK_FACTOR_META = {
  claims_frequency:     { explain: "Derived from your property and liability risk scores. Higher means claims happen more frequently in your sector — so insurers price accordingly.", source: "IRDAI Annual Report 2024" },
  claims_freq:          { explain: "Derived from your property and liability risk scores. Higher means claims happen more frequently in your sector — so insurers price accordingly.", source: "IRDAI Annual Report 2024" },
  settlement:           { explain: "A measure of claim complexity. Higher scores reflect governance and regulatory exposure where disputes are more likely to escalate before they settle.", source: "IRDAI Grievance & Settlement Report 2024" },
  settlement_time:      { explain: "A measure of claim complexity. Higher scores reflect governance and regulatory exposure where disputes are more likely to escalate before they settle.", source: "IRDAI Grievance & Settlement Report 2024" },
  regulatory_volatility:{ explain: "Based on your regulatory compliance and policy velocity scores. High means your sector is under active legislative change — raising the chance of an enforcement action or mandatory cover trigger.", source: "CERT-In / RBI / MeitY regulatory activity, 2024" },
  market_saturation:    { explain: "Calculated as 1 minus the average adoption rate for your recommended bundle. Higher means fewer peers have bought this cover yet — less pricing competition, more greenfield opportunity.", source: "IRDAI segment premiums + NASSCOM startup survey 2024" },
};

const STAGE_ORDER = ["Pre-seed", "Seed", "Series A", "Series B", "Series B+", "Growth", "Late Stage / Pre-IPO"];

function renderV2Insights(result) {
  const isV2 = Boolean(result?.config_version || result?.graduation_map || result?.compliance_flags);
  if (!isV2) return "";

  const ins = result.bundle_insights;
  const revenue = result.revenue_breakdown || [];
  const risk = result.risk_multiplier_breakdown || {};
  const path = result.coverage_roadmap || [];
  const normaliseCover = (key) => COVER_ALIASES[key] || COVER_ALIASES[String(key || "").toUpperCase()] || key;
  const displayedCovers = new Set([
    ...(result.bundle_match?.mandatory_covers || []),
    ...(result.bundle_match?.optional_covers || []),
    ...(result.bundle_match?.companion_bundle?.mandatory_covers || []),
    ...(result.bundle_match?.companion_bundle?.optional_covers || []),
    ...(result.recommendations || []).map(p => p.key),
  ].flatMap(key => [key, normaliseCover(key)]).filter(Boolean));
  const triggerSource = result.display_regulatory_triggers || result.regulatory_triggers_fired || [];
  const triggers = triggerSource.filter(t => displayedCovers.has(t.product) || displayedCovers.has(normaliseCover(t.product)));

  const riskItems = Object.entries(risk)
    .filter(([k, v]) => RISK_FACTOR_LABELS[k] != null && v != null)
    .map(([k, v]) => [RISK_FACTOR_LABELS[k], v]);

  const trajectoryLabel = (t) => ({ up: "Growing market", down: "Declining market", stable: "Stable market" }[t] || t || "");
  const complianceItems = triggers.length && ins && Array.isArray(ins.compliance_plain) ? ins.compliance_plain.slice(0, triggers.length) : [];

  const sortedPath = [...path].sort((a, b) => {
    const ai = STAGE_ORDER.indexOf(a.stage || "");
    const bi = STAGE_ORDER.indexOf(b.stage || "");
    return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
  });

  return `
    <details class="expander-card insights-card" style="margin-top:14px;">
      <summary>Why this was recommended</summary>
      <div class="expander-body">

        ${ins?.headline ? `<div class="insights-headline">${esc(ins.headline)}</div>` : ""}

        <!-- ── Bundle fit ── -->
        ${revenue.length ? `
        <div class="wtr-section">
          <div class="wtr-section-head">
            <span class="wtr-section-title">Bundle fit for your profile</span>
            <span class="wtr-section-src">Source: IRDAI segment data &middot; Swiss Re SME estimates &middot; IL product benchmarks</span>
          </div>
          <p class="wtr-section-desc">Each bundle is scored on three commercial factors: how large the insurance market is for that bundle type, how many startups at your stage actually buy it, and the margin ICICI Lombard earns on it. The recommended bundle scored highest on all three combined.</p>
          <div class="wtr-bundle-list">
            ${revenue.slice(0, 3).map(r => {
              const adoptedPool = (r.tam_cr && r.adoption)
                ? Math.round(r.tam_cr * r.adoption)
                : null;
              const marginAdjusted = (adoptedPool != null && r.margin)
                ? Math.round(adoptedPool * r.margin)
                : null;
              const traj = trajectoryLabel(r.trajectory);
              return `
              <div class="wtr-bundle-card">
                <div class="wtr-bundle-top">
                  <span class="wtr-bundle-name">${esc(r.bundle || "Bundle")}</span>
                  ${traj ? `<span class="wtr-traj ${r.trajectory || ""}">${r.trajectory === "up" ? "↑" : r.trajectory === "down" ? "↓" : "→"} ${esc(traj)}</span>` : ""}
                </div>
                <div class="wtr-bundle-stats">
                  ${r.tam_cr != null ? `<div class="wtr-stat"><div class="wtr-stat-val">INR ${r.tam_cr.toLocaleString("en-IN")} Cr</div><div class="wtr-stat-lbl">Estimated premium pool</div><div class="wtr-stat-tip">Total annual Indian premium opportunity for this bundle category.</div></div>` : ""}
                  ${r.adoption != null ? `<div class="wtr-stat"><div class="wtr-stat-val">${Math.round(r.adoption * 100)}%</div><div class="wtr-stat-lbl">Estimated adoption</div><div class="wtr-stat-tip">Share of comparable startups likely to carry this bundle at this stage.</div></div>` : ""}
                  ${adoptedPool != null ? `<div class="wtr-stat"><div class="wtr-stat-val">INR ${adoptedPool.toLocaleString("en-IN")} Cr</div><div class="wtr-stat-lbl">Adopted premium pool</div><div class="wtr-stat-tip">Estimated premium pool × estimated adoption rate.</div></div>` : ""}
                  ${r.margin != null ? `<div class="wtr-stat"><div class="wtr-stat-val">${Math.round(r.margin * 100)}%</div><div class="wtr-stat-lbl">Expected contribution margin</div><div class="wtr-stat-tip">Illustrative net margin after claims, expenses, and distribution assumptions.</div></div>` : ""}
                  ${marginAdjusted != null ? `<div class="wtr-stat wtr-stat-hi"><div class="wtr-stat-val">INR ${marginAdjusted.toLocaleString("en-IN")} Cr</div><div class="wtr-stat-lbl">Margin-adjusted opportunity</div><div class="wtr-stat-tip">Adopted premium pool × expected contribution margin. Treat as an illustrative model assumption unless backed by internal data.</div></div>` : ""}
                </div>
              </div>`;
            }).join("")}
          </div>
          ${ins?.why_now ? `<div class="wtr-ai-note">${esc(ins.why_now)}</div>` : ""}
          ${ins?.social_proof ? `<div class="wtr-ai-note">${esc(ins.social_proof)}</div>` : ""}
        </div>` : ""}

        <!-- ── Market risk factors ── -->
        ${riskItems.length ? `
        <div class="wtr-section">
          <div class="wtr-section-head">
            <span class="wtr-section-title">Market risk factors for this cover</span>
          </div>
          <p class="wtr-section-desc">These four factors reflect how exposed your sector is right now — based on your SPARC risk scores calibrated against Indian insurance market data. They inform how the engine weighs your bundle recommendation, not the premium amount.</p>
          <div class="wtr-risk-list">
            ${Object.entries(risk)
              .filter(([k]) => RISK_FACTOR_META[k] != null)
              .map(([k, v]) => {
                const meta = RISK_FACTOR_META[k];
                const label = RISK_FACTOR_LABELS[k] || k;
                const pctVal = Math.round((v || 0) * 100);
                return `
                <div class="wtr-risk-row">
                  <div class="wtr-risk-head">
                    <span class="wtr-risk-name">${esc(label)}</span>
                    <span class="wtr-risk-val">${pctVal}%</span>
                  </div>
                  <div class="wtr-risk-bar"><div class="wtr-risk-fill" style="width:${pctVal}%;background:${pctVal >= 70 ? "var(--red)" : pctVal >= 45 ? "#f59e0b" : "#4caf50"}"></div></div>
                  <div class="wtr-risk-explain">${esc(meta.explain)} <span class="hc-src">${esc(meta.source)}</span></div>
                </div>`;
              }).join("")}
          </div>
        </div>` : ""}

        <!-- ── Coverage roadmap ── -->
        ${sortedPath.length ? `
        <div class="wtr-section">
          <div class="wtr-section-head">
            <span class="wtr-section-title">Your coverage roadmap as you grow</span>
          </div>
          <p class="wtr-section-desc">As your company raises and scales, your risk profile changes and different bundles become the right fit. This is the recommended progression — each stage builds on the last.</p>
          ${ins?.roadmap_narrative ? `<div class="wtr-ai-note">${esc(ins.roadmap_narrative)}</div>` : ""}
          <div class="wtr-roadmap">
            ${sortedPath.map((p, i) => `
              <div class="wtr-roadmap-step">
                <div class="wtr-roadmap-dot">${i + 1}</div>
                <div class="wtr-roadmap-body">
                  <div class="wtr-roadmap-stage">${esc(p.stage || `Step ${i + 1}`)}</div>
                  <div class="wtr-roadmap-bundle">${esc(p.bundle || p.recommendation || "")}</div>
                </div>
              </div>`).join("")}
          </div>
        </div>` : ""}

        <!-- ── Regulatory triggers ── -->
        ${triggers.length ? `
        <div class="wtr-section">
          <div class="wtr-section-head">
            <span class="wtr-section-title">Why certain covers were flagged as mandatory</span>
          </div>
          <p class="wtr-section-desc">These covers were not recommended because of a general best practice — they were flagged because a specific regulation applies to your company based on your sector, data handling, or operating model.</p>
          <div class="wtr-trigger-list">
            ${triggers.map(t => `
              <div class="wtr-trigger-row">
                <div class="wtr-trigger-signal">${esc(SIGNAL_LABELS[t.signal] || t.signal || "Trigger")}</div>
                <div class="wtr-trigger-arrow">→</div>
                <div class="wtr-trigger-cover">${esc(t.product || "")}</div>
                <div class="wtr-trigger-reg">${t.citation_url
                  ? `<a href="${esc(t.citation_url)}" target="_blank" rel="noopener noreferrer" class="wtr-reg-link">${esc(t.regulation || t.reg || "")}</a>`
                  : `<span>${esc(t.regulation || t.reg || "")}</span>`}</div>
              </div>`).join("")}
          </div>
          ${complianceItems.length ? complianceItems.map(c => `<div class="wtr-ai-note">${esc(c)}</div>`).join("") : ""}
        </div>` : ""}

      </div>
    </details>`;
}

function renderProductRows(recs, mapping, why = {}) {
  const byKey = Object.fromEntries((mapping || []).map(r => [r.key, r]));
  if (!recs?.length) return emptyState("🛡️", "No products recommended", "The engine found no matching ICICI Lombard products for this profile. Try adjusting your inputs.");
  const appetiteLabels = { good: "Good risk", moderate: "Moderate", bad: "Not preferred", tbd: "Under review" };

  const tierBadge = (tier) => {
    if (tier === "auto")        return `<span class="product-tag" style="background:#e6f4ea;color:#1e7e34;border:1px solid #a8d5b5;">✓ RM can pitch</span>`;
    if (tier === "conditional") return `<span class="product-tag" style="background:#fff8e1;color:#856404;border:1px solid #ffd54f;">⚡ Sector check needed</span>`;
    if (tier === "referral")    return `<span class="product-tag" style="background:#fdecea;color:#b71c1c;border:1px solid #ef9a9a;">⚠ Refer to underwriter</span>`;
    return "";
  };

  const uwQuestions = (p) => {
    if (!p.underwriting_questions?.length) return "";
    return `<details style="margin-top:10px;">
      <summary style="font-size:11px;font-weight:600;color:var(--ink-muted);cursor:pointer;letter-spacing:.04em;text-transform:uppercase;">Key underwriting questions</summary>
      <ol style="margin:6px 0 0 16px;padding:0;font-size:12px;color:var(--ink-body);line-height:1.7;">
        ${p.underwriting_questions.map(q => `<li>${esc(q)}</li>`).join("")}
      </ol>
      ${p.required_documents?.length ? `<div style="margin-top:6px;font-size:11px;color:var(--ink-muted);"><strong>Required docs:</strong> ${esc(p.required_documents.join(" · "))}</div>` : ""}
    </details>`;
  };

  return recs.map((p, i) => {
    const prio      = p.priority || "Optional";
    const prioClass = prio === "Critical" ? "critical" : prio === "Recommended" ? "recommended" : "";

    return `
      <div class="product-row ${prioClass}" id="prow-${i}">
        <div class="product-row-left">
          <div class="product-row-name">${esc(p.name || p.key)}</div>
          <div class="product-row-il">${esc(p.il_product || "")}</div>
          <div style="display:flex;gap:5px;margin-top:4px;flex-wrap:wrap;">
            <span class="product-tag score">${p.score}/100 fit</span>
            <span class="product-tag appetite-${p.appetite || "tbd"}">${appetiteLabels[p.appetite || "tbd"]}</span>
            ${p.mandatory ? `<span class="product-tag baseline">Baseline</span>` : ""}
            <span class="badge badge-${prio === "Critical" ? "critical" : prio === "Recommended" ? "watch" : "low"}" style="font-size:10px;">${esc(prio)}</span>
            ${tierBadge(p.referral_tier)}
          </div>
          ${uwQuestions(p)}
        </div>
        <div class="product-row-nudge">${esc(getProductWhy(p, why) || p.nudge || "")}</div>
        <div class="product-row-right">
          ${p.premium ? `<div class="product-row-premium">INR ${p.premium.min_lakh.toFixed(1)}-${p.premium.max_lakh.toFixed(1)}L</div>
          <div style="font-size:11px;color:var(--ink-faint);text-align:right;">${esc(p.premium.basis)}</div>` : ""}
          <button class="product-row-expand" onclick="toggleProductRow(${i})" title="Expand">›</button>
        </div>
      </div>`;
  }).join("");
}

function renderTimeline(bundles) {
  if (!bundles?.length) return emptyState("📅", "No timeline data", "Coverage timeline will appear once products are recommended.");
  return bundles.map((b,i) => `
    <div class="timeline-item">
      <div class="tl-dot">${i+1}</div>
      <div class="tl-time">${esc(b.timeline)}</div>
      <div class="tl-name">${esc(b.name)}</div>
      <div class="tl-count">${b.products.length} product${b.products.length!==1?"s":""}</div>
    </div>`).join("");
}

function renderTriggers(triggers) {
  if (!triggers?.length) return emptyState("✅", "No regulatory triggers", "No major regulatory flags were detected for this profile.");
  return triggers.map(t=>`
    <div class="callout-item">
      <strong>${esc(t.name)}</strong>
      <span>${esc(t.detail)}</span>
    </div>`).join("");
}

function renderMitigations(items) {
  if (!items?.length) return emptyState("✅", "No actions required", "No non-insurance mitigation actions were flagged for this profile.");
  return items.map(t=>`
    <div class="callout-item">
      <strong>${esc(t.risk)}</strong>
      <span>${esc(t.action)}</span>
    </div>`).join("");
}

function renderAssumptions(assumptions) {
  const entries = Object.entries(assumptions||{});
  if (!entries.length) return `<p style="color:var(--ink-muted);font-size:13px;">No assumptions recorded.</p>`;
  return entries.map(([k,v])=>`
    <div class="kv-row">
      <span class="kv-key">${esc(labelize(k))}</span>
      <span class="kv-val">${esc(formatVal(v))}</span>
    </div>`).join("");
}

function policyWordingOptions(result) {
  const options = [];
  const seen = new Set();
  const add = (value, label) => {
    if (!value || seen.has(value)) return;
    seen.add(value);
    options.push({ value, label: label || value });
  };
  add(result.bundle_match?.name, `Bundle: ${result.bundle_match?.name || ""}`);
  (result.bundle_alternatives || []).slice(0, 4).forEach(b => add(b.name, `Alt bundle: ${b.name}`));
  (result.recommendations || []).forEach(p => add(p.key || p.name, p.name || p.key));
  return options;
}

function renderPolicyWordingComparison(result) {
  return ""; // hidden
  const options = policyWordingOptions(result);
  if (!options.length) return "";
  const bundleName = result.bundle_match?.name || "recommended bundle";
  return `
    <div class="result-section" id="coverage-gaps">
      <div class="result-section-head">
        <div class="result-section-bar"></div>
        <div class="result-section-title">Coverage gap checker</div>
      </div>
      <div class="policy-wording-card">
        <div class="policy-wording-head">
          <div>
            <div class="card-label">Start with one click</div>
            <p>Check ${esc(bundleName)} against SPARC's wording reference and this startup's recommended covers. No policy document needed.</p>
          </div>
          <select id="policy-wording-product" class="f-select">
            ${options.map(o => `<option value="${esc(o.value)}">${esc(o.label)}</option>`).join("")}
          </select>
        </div>
        <div class="policy-wording-actions">
          <button class="btn btn-primary" type="button" onclick="comparePolicyWording({referenceOnly:true})">Check recommended bundle gaps</button>
          <span id="policy-wording-status" class="policy-wording-status">Uses deterministic SPARC reference data from the policy wording comparison pack.</span>
        </div>
        <details class="policy-advanced-review">
          <summary>I already have a policy document</summary>
          <p>Optional exact wording review. Paste exclusions, schedule notes, or relevant clauses if a customer has an existing policy.</p>
          <textarea id="policy-wording-text" class="policy-wording-textarea" placeholder="Paste policy terms, exclusions, schedule notes, or wording excerpts here..."></textarea>
          <div class="policy-wording-actions">
            <label class="policy-upload-btn">
              Upload .txt/.md wording
              <input id="policy-wording-file" type="file" accept=".txt,.md,.json,.csv,.html,.htm,text/*" />
            </label>
            <button class="btn btn-ghost" type="button" onclick="comparePolicyWording({referenceOnly:false})">Compare exact wording</button>
            <span class="policy-wording-status">For DOCX/PDF, open the file and paste the relevant text excerpt.</span>
          </div>
        </details>
        <div id="policy-wording-output"></div>
      </div>
    </div>`;
}

function bindPolicyWordingUpload() {
  const input = $("policy-wording-file");
  if (!input) return;
  input.addEventListener("change", async () => {
    const file = input.files?.[0];
    if (!file) return;
    const status = $("policy-wording-status");
    if (/\.docx$/i.test(file.name)) {
      if (status) status.textContent = "DOCX upload is not parsed in-browser yet. Open the DOCX and paste the wording text.";
      return;
    }
    const text = await file.text();
    const area = $("policy-wording-text");
    if (area) area.value = text;
    if (status) status.textContent = `Loaded ${file.name} (${text.length} characters).`;
  });
}

function renderPolicyList(title, items, cls = "") {
  if (!items?.length) return "";
  return `
    <div class="policy-result-block ${cls}">
      <strong>${esc(title)}</strong>
      <ul>${items.slice(0, 10).map(item => {
        const text = typeof item === "string" ? item : item.text || item.why_it_matters || item.key || "";
        const status = typeof item === "object" && item.status ? `<em>${esc(item.status.replace(/_/g, " "))}</em>` : "";
        return `<li><span>${esc(text)}</span>${status}</li>`;
      }).join("")}</ul>
    </div>`;
}

function renderPolicyComparisonResult(data) {
  if (!data?.ok) return `<div class="notice">${esc(data?.error || "Policy comparison failed.")}</div>`;
  const ai = data.genai_summary;
  const isReferenceOnly = data.comparison_mode === "reference_only";
  return `
    <div class="policy-result-grid">
      <div class="policy-result-summary">
        <div class="card-label">${esc(data.matched_reference || "Policy wording")} ${isReferenceOnly ? "gap check" : "review"}</div>
        <p>${esc(ai?.plain_english_summary || data.summary || "Comparison completed.")}</p>
        <div class="policy-result-meta">
          <span>${data.manual_review_required ? "Manual review required" : "No major deterministic gaps flagged"}</span>
          <span>GenAI: ${esc(data.genai_source || "fallback")}</span>
          <span>${isReferenceOnly ? "No document needed" : "Pasted wording check"}</span>
        </div>
        ${data.genai_error ? `<div class="notice">${esc(data.genai_error)}</div>` : ""}
      </div>
      ${renderPolicyList(isReferenceOnly ? "Key exclusions to explain upfront" : "Expected exclusions from reference", data.expected_exclusions)}
      ${renderPolicyList("Coverage gaps to discuss", ai?.coverage_gaps_to_discuss?.length ? ai.coverage_gaps_to_discuss : data.coverage_gaps)}
      ${renderPolicyList(isReferenceOnly ? "SPARC recommended covers outside this reference" : "Recommended covers not detected in pasted wording", data.missing_recommended_covers, "warn")}
      ${renderPolicyList("Profile-specific flags", data.profile_gap_flags, "warn")}
      ${renderPolicyList("Questions for underwriter", ai?.questions_for_underwriter || [])}
      ${renderPolicyList("Universal exclusions detected", data.universal_exclusions_detected)}
    </div>`;
}

window.comparePolicyWording = async (opts = {}) => {
  const referenceOnly = opts.referenceOnly !== false;
  const status = $("policy-wording-status");
  const output = $("policy-wording-output");
  const text = $("policy-wording-text")?.value || "";
  const product = $("policy-wording-product")?.value || "";
  if (status) status.textContent = referenceOnly ? "Checking recommended coverage gaps..." : "Comparing wording...";
  if (output) output.innerHTML = "";
  try {
    const result = window.__result || {};
    const res = await fetch("/api/policy/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_name: product,
        policy_text: referenceOnly ? "" : text,
        reference_only: referenceOnly,
        profile: result.profile || state.profile,
        bundle_match: result.bundle_match,
        recommendations: result.recommendations,
        scores: result.scores,
      }),
    });
    const data = await res.json();
    if (!res.ok || data.error) throw new Error(data.error || "Comparison failed");
    if (status) status.textContent = referenceOnly ? "Gap check complete." : "Comparison complete.";
    if (output) output.innerHTML = renderPolicyComparisonResult(data);
  } catch (err) {
    if (status) status.textContent = `Error: ${err.message}`;
    if (output) output.innerHTML = `<div class="notice">${esc(err.message)}</div>`;
  }
};

// ── ICICI Lombard V1 email template ────────────────────────────────────────

const _RISK_DESCRIPTIONS = {
  "Cyber Technical Risk":       "Data breach, ransomware, and business disruption from cyber attacks.",
  "Data Privacy Risk":          "Regulatory penalties and liability from mishandling personal data.",
  "Liability Risk":             "Third-party claims for injury or property damage from operations.",
  "Property Risk":              "Damage, loss, and disruption to physical assets and infrastructure.",
  "Governance & Fraud Risk":    "Director/officer liability, internal fraud, and governance failures.",
  "Gig & Labour Risk":          "Statutory and compliance exposure across employees and gig workers.",
  "Regulatory Compliance Risk": "Penalties and legal action from evolving regulatory requirements.",
  "ESG & Climate Risk":         "Physical and transition risk from climate events and ESG obligations.",
  "IP Infringement Risk":       "Exposure from intellectual property disputes and technology claims.",
  "Key Person Risk":            "Business disruption from loss of critical founders or executives.",
  "Geopolitical Risk":          "Cross-border exposure from political and trade disruptions.",
  "Policy Velocity Risk":       "Rapid regulatory change creating gaps in existing coverage.",
  "Reputation Risk":            "Brand damage from public incidents or media exposure.",
};

let _outreachItems = {};


function _ilRiskCards(riskNames) {
  return (riskNames || []).slice(0, 3).map((name, i) => `
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FFFFFF;border:1px solid #D1CFBB;border-radius:4px;margin-bottom:10px;">
      <tr><td style="padding:20px 24px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
          <td valign="top" width="48" style="width:48px;padding-right:10px;">
            <div style="font-family:Georgia,'Times New Roman',serif;color:#F15E2A;font-size:28px;line-height:1;">0${i + 1}</div>
          </td>
          <td valign="top">
            <div style="font-family:Arial,Helvetica,sans-serif;color:#053C6D;font-size:13px;font-weight:bold;line-height:1.3;margin-bottom:5px;">${name}</div>
            <div style="font-family:Arial,Helvetica,sans-serif;color:#6B7280;font-size:12px;line-height:1.55;">${_RISK_DESCRIPTIONS[name] || "Key exposure area identified by our expert underwriters."}</div>
          </td>
        </tr></table>
      </td></tr>
    </table>`).join("");
}

function buildILEmailHtml(subject, body, d) {
  d = d || {};
  const company   = d.company      || "your company";
  const industry  = d.industry     || "your sector";
  const product   = d.product_name || "this policy";
  const riskNames = d.risk_names   || [];
  const bodyPara  = d.body_para    || "";
  const personalizedPoints = Array.isArray(d.personalized_points)
    ? d.personalized_points.map(point => String(point || "").trim()).filter(point => point && point !== "...").slice(0, 3)
    : [];
  const rmName    = d.rm_name      || "{{RM_NAME}}";
  const rmPhone   = d.rm_phone     || "{{RM_PHONE}}";
  const rmEmail   = d.rm_email     || "{{RM_EMAIL}}";
  const cards     = _ilRiskCards(riskNames);
  const personalizedHtml = personalizedPoints.length ? `
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#FFF3EC;border:1px solid #D1CFBB;border-radius:4px;margin:0 0 26px 0;">
      <tr><td style="padding:18px 20px;">
        <div style="font-family:Arial,Helvetica,sans-serif;color:#053C6D;font-size:12px;font-weight:bold;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:10px;">Why this is relevant to ${esc(company)}</div>
        ${personalizedPoints.map(point => `
          <div style="font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:13px;line-height:1.55;margin:8px 0 0 0;">&bull; ${esc(point)}</div>
        `).join("")}
      </td></tr>
    </table>` : "";

  return `<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="X-UA-Compatible" content="IE=edge"><meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light only"><meta name="supported-color-schemes" content="light only">
<title>${subject}</title>
<!--[if mso]><style>table,td,div,p,a{font-family:Arial,Helvetica,sans-serif!important;}</style>
<xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch><o:AllowPNG/></o:OfficeDocumentSettings></xml><![endif]-->
<style>
body,table,td,a{-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;}
table,td{mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;}
img{border:0;display:block;}a{text-decoration:none;}
body{margin:0;padding:0;width:100%!important;background:#D1CFBB;}
@media screen and (max-width:620px){
  .container{width:100%!important;}
  .px-body{padding-left:28px!important;padding-right:28px!important;}
}
</style>
</head>
<body style="margin:0;padding:0;background:#D1CFBB;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#D1CFBB;">A tailored coverage recommendation for ${company} from ICICI Lombard.</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#D1CFBB;">
<tr><td align="center" style="padding:32px 16px;">
<table role="presentation" class="container" width="580" cellpadding="0" cellspacing="0" border="0" style="width:580px;max-width:580px;border-radius:6px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.10);">

  <!-- ── HEADER ── -->
  <tr><td style="background:#053C6D;padding:28px 40px;" class="px-body">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td>
        <div style="font-family:Georgia,'Times New Roman',serif;color:#FFFFFF;font-size:20px;letter-spacing:0.06em;line-height:1;">ICICI LOMBARD</div>
        <div style="font-family:Arial,Helvetica,sans-serif;color:#F15E2A;font-size:9px;letter-spacing:0.32em;margin-top:4px;">GENERAL&nbsp;&nbsp;INSURANCE</div>
      </td>
      <td align="right" style="font-family:Arial,Helvetica,sans-serif;color:#7B9CBB;font-size:10px;letter-spacing:0.16em;text-transform:uppercase;vertical-align:middle;">Commercial Lines</td>
    </tr></table>
  </td></tr>

  <!-- ── EYEBROW + HEADLINE ── -->
  <tr><td style="background:#FFFFFF;padding:36px 40px 20px 40px;" class="px-body">
    <div style="font-family:Arial,Helvetica,sans-serif;color:#F15E2A;font-size:10px;font-weight:bold;letter-spacing:0.24em;text-transform:uppercase;margin-bottom:10px;">For the ${esc(industry)} sector</div>
    <div style="font-family:Georgia,'Times New Roman',serif;color:#053C6D;font-size:26px;line-height:1.25;font-weight:normal;margin-bottom:20px;">A tailored approach to protecting ${esc(company)}&rsquo;s journey</div>
    <p style="margin:0 0 6px 0;font-family:Arial,Helvetica,sans-serif;color:#22262E;font-size:15px;line-height:1.65;">Dear ${esc(company)} team,</p>
    <p style="margin:0 0 20px 0;font-family:Arial,Helvetica,sans-serif;color:#22262E;font-size:15px;line-height:1.65;">Greetings from ICICI Lombard!</p>
    <p style="margin:0 0 28px 0;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:1.7;">Our expert underwriters have been closely studying risk profiles across the ${esc(industry)} landscape, and ${esc(company)} stood out. Based on their assessment, your most significant risk dimensions deserve proactive, well-structured coverage — especially at your current stage of growth.</p>
  </td></tr>

  <!-- ── RISK CARDS ── -->
  <tr><td style="background:#FFFFFF;padding:0 40px 28px 40px;" class="px-body">
    <div style="font-family:Arial,Helvetica,sans-serif;color:#6B7280;font-size:10px;font-weight:bold;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:14px;">Most material risk dimensions</div>
    ${cards}
  </td></tr>

  <!-- ── PRODUCT PARA ── -->
  <tr><td style="background:#FFFFFF;padding:0 40px 36px 40px;" class="px-body">
    <p style="margin:0 0 28px 0;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:1.7;">We&rsquo;d love to introduce you to <strong style="color:#053C6D;">${esc(product)}</strong>. ${esc(bodyPara)} It is thoughtfully designed for companies like yours and we believe it can give your team real peace of mind as you scale.</p>
    <p style="margin:0 0 28px 0;font-family:Arial,Helvetica,sans-serif;color:#374151;font-size:14px;line-height:1.7;">We&rsquo;d be delighted to walk you through how ${esc(product)} fits your journey &mdash; no pressure, just a friendly conversation at a time that works for you.</p>
    ${personalizedHtml}
    <!--[if !mso]><!-- -->
    <a href="mailto:${rmEmail}" style="display:inline-block;background:#F15E2A;color:#FFFFFF;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:bold;letter-spacing:0.04em;line-height:48px;padding:0 30px;border-radius:4px;text-decoration:none;">Book a 20-min call &rarr;</a>
    <!--<![endif]-->
  </td></tr>

  <!-- ── DIVIDER ── -->
  <tr><td style="background:#FFFFFF;padding:0 40px;" class="px-body"><div style="height:1px;background:#E4E7ED;line-height:1px;font-size:1px;">&nbsp;</div></td></tr>

  <!-- ── SIGNATURE ── -->
  <tr><td style="background:#FFFFFF;padding:24px 40px 36px 40px;" class="px-body">
    <div style="font-family:Georgia,'Times New Roman',serif;color:#9CA3AF;font-style:italic;font-size:13px;margin-bottom:8px;">Warm regards,</div>
    <div style="font-family:Arial,Helvetica,sans-serif;font-weight:bold;color:#053C6D;font-size:14px;">${esc(rmName)}</div>
    <div style="font-family:Arial,Helvetica,sans-serif;color:#9CA3AF;font-size:12px;margin-top:3px;">ICICI Lombard &mdash; Commercial Lines</div>
    <div style="margin-top:8px;font-family:Arial,Helvetica,sans-serif;font-size:13px;">
      <a href="tel:${rmPhone}" style="color:#22262E;text-decoration:none;">${esc(rmPhone)}</a>
      <span style="color:#F15E2A;padding:0 6px;">&middot;</span>
      <a href="mailto:${rmEmail}" style="color:#22262E;text-decoration:none;">${esc(rmEmail)}</a>
    </div>
  </td></tr>

  <!-- ── FOOTER ── -->
  <tr><td style="background:#053C6D;padding:20px 40px;" class="px-body">
    <div style="font-family:Georgia,'Times New Roman',serif;color:#4A6080;font-size:11px;letter-spacing:0.05em;margin-bottom:6px;">ICICI LOMBARD GENERAL INSURANCE COMPANY LIMITED</div>
    <div style="font-family:Arial,Helvetica,sans-serif;color:#4A6080;font-size:10px;line-height:1.7;">
      <div>414, Veer Savarkar Marg, Prabhadevi, Mumbai &mdash; 400025 &nbsp;&middot;&nbsp; Reg. No. 115</div>
      <div style="margin-top:8px;">
        <a href="https://www.icicilombard.com" style="color:#F15E2A;text-decoration:none;">icicilombard.com</a>
        <span style="color:#253A52;padding:0 6px;">&middot;</span>
        <a href="#" style="color:#4A6080;text-decoration:underline;">Unsubscribe</a>
        <span style="color:#253A52;padding:0 6px;">&middot;</span>
        <a href="https://www.icicilombard.com/privacy-policy" style="color:#4A6080;text-decoration:underline;">Privacy</a>
      </div>
      <div style="margin-top:10px;color:#2E4060;font-size:9px;line-height:1.6;">Insurance is the subject matter of solicitation. Please read the sales brochure and policy wordings carefully before concluding a sale.</div>
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>`;
}

function openEmailModal(subject, body, htmlData, contactEmail = "") {
  document.getElementById("il-email-modal")?.remove();
  const html = buildILEmailHtml(subject, body, htmlData);
  const mailtoBody = encodeURIComponent(body);
  const mailtoSubject = encodeURIComponent(subject);
  const mailtoTo = encodeURIComponent(contactEmail);
  const modal = document.createElement("div");
  modal.id = "il-email-modal";
  modal.style.cssText = "position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;";
  modal.innerHTML = `
    <div style="background:#fff;border-radius:10px;width:100%;max-width:700px;max-height:92vh;display:flex;flex-direction:column;box-shadow:0 8px 48px rgba(0,0,0,.3);overflow:hidden;">
      <div style="background:#053C6D;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;">
        <div>
          <div style="color:#fff;font-weight:700;font-size:14px;letter-spacing:.02em;">ICICI Lombard &mdash; Email Preview</div>
          <div style="color:#A9B7CC;font-size:11px;margin-top:2px;">Commercial Lines outreach template</div>
        </div>
        <button id="il-modal-close" style="background:none;border:none;color:#A9B7CC;font-size:22px;cursor:pointer;line-height:1;padding:0 4px;">&times;</button>
      </div>
      ${contactEmail ? `
      <div style="padding:8px 18px;background:#f0f4f8;border-bottom:1px solid #dde4ed;flex-shrink:0;display:flex;align-items:center;gap:8px;">
        <span style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.05em;font-weight:600;white-space:nowrap;">To:</span>
        <span id="il-email-to-addr" style="flex:1;font-size:13px;color:#1a1a2e;font-weight:500;">${esc(contactEmail)}</span>
        <button id="il-copy-to" style="background:none;border:1px solid #c0c8d4;color:#555;padding:3px 10px;border-radius:4px;font-size:11px;cursor:pointer;white-space:nowrap;">Copy</button>
      </div>` : ""}
      <div style="padding:10px 18px;background:#f0f4f8;border-bottom:1px solid #dde4ed;flex-shrink:0;">
        <div style="font-size:11px;color:#888;margin-bottom:2px;text-transform:uppercase;letter-spacing:.05em;">Subject</div>
        <div style="font-size:13px;font-weight:600;color:#1a1a2e;">${esc(subject)}</div>
      </div>
      <div style="flex:1;overflow:hidden;">
        <iframe style="width:100%;height:100%;min-height:460px;border:none;display:block;" srcdoc="${esc(html).replace(/"/g, "&quot;")}"></iframe>
      </div>
      <div style="padding:12px 18px;border-top:1px solid #e8e8e8;display:flex;gap:8px;flex-wrap:wrap;background:#fafafa;flex-shrink:0;">
        <a href="mailto:${mailtoTo}?subject=${mailtoSubject}&body=${mailtoBody}" target="_blank"
           style="display:inline-flex;align-items:center;gap:5px;background:#053C6D;color:#fff;padding:8px 16px;border-radius:5px;font-size:12px;font-weight:600;text-decoration:none;">
          ✉️ Open in Mail Client
        </a>
        <a href="https://mail.google.com/mail/?view=cm&fs=1&to=${mailtoTo}&su=${mailtoSubject}&body=${mailtoBody}" target="_blank"
           style="display:inline-flex;align-items:center;gap:5px;background:#EA4335;color:#fff;padding:8px 16px;border-radius:5px;font-size:12px;font-weight:600;text-decoration:none;">
          🔴 Open in Gmail
        </a>
        <button id="il-copy-html" style="display:inline-flex;align-items:center;gap:5px;background:#F15E2A;color:#fff;border:none;padding:8px 16px;border-radius:5px;font-size:12px;font-weight:600;cursor:pointer;">
          📋 Copy HTML
        </button>
        <button id="il-download-html" style="display:inline-flex;align-items:center;gap:5px;background:#1a7a4a;color:#fff;border:none;padding:8px 16px;border-radius:5px;font-size:12px;font-weight:600;cursor:pointer;">
          ⬇️ Download HTML
        </button>
        <button id="il-modal-close2" style="margin-left:auto;background:none;border:1px solid #ddd;color:#666;padding:8px 14px;border-radius:5px;font-size:12px;cursor:pointer;">Close</button>
      </div>
    </div>`;
  document.body.appendChild(modal);
  document.getElementById("il-modal-close").onclick  = () => modal.remove();
  document.getElementById("il-modal-close2").onclick = () => modal.remove();
  modal.addEventListener("click", e => { if (e.target === modal) modal.remove(); });
  const copyToBtn = document.getElementById("il-copy-to");
  if (copyToBtn) {
    copyToBtn.addEventListener("click", async () => {
      await navigator.clipboard?.writeText(contactEmail);
      copyToBtn.textContent = "Copied ✓";
      setTimeout(() => { copyToBtn.textContent = "Copy"; }, 1800);
    });
  }
  document.getElementById("il-copy-html").addEventListener("click", async () => {
    await navigator.clipboard?.writeText(html);
    const btn = document.getElementById("il-copy-html");
    if (btn) { btn.textContent = "✅ Copied!"; setTimeout(() => { btn.textContent = "📋 Copy HTML"; }, 2000); }
  });
  document.getElementById("il-download-html").addEventListener("click", () => {
    const slug = (subject || "email").toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 40);
    const blob = new Blob([html], { type: "text/html;charset=utf-8" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href = url; a.download = `icici-lombard-${slug}.html`;
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 200);
  });
}

function renderFounderPitch(result) {
  const bullets  = result.pitch_bullets || [];
  const handlers = result.objection_handlers || [];
  const meta     = result.pitch_meta || {};
  if (!bullets.length && !handlers.length) return "";

  const bulletText = bullets.map((b, i) =>
    `<div class="fp-bullet">
      <span class="fp-num">0${i+1}</span>
      <span class="fp-text">${esc(b)}</span>
    </div>`
  ).join("");

  const allBulletText = bullets.join("\n\n");

  const objectionHtml = handlers.map(h => `
    <div class="fp-objection">
      <div class="fp-obj-q">${esc(h.objection || h.underlying_fear || "")}</div>
      <div class="fp-obj-a">${esc(h.scripted_response || "")}</div>
    </div>`
  ).join("");

  const metaHtml = (meta.trigger_question || meta.best_timing) ? `
    <div class="fp-meta">
      ${meta.trigger_question ? `<div class="fp-meta-row"><span class="fp-meta-l">Trigger question</span><span class="fp-meta-v">${esc(meta.trigger_question)}</span></div>` : ""}
      ${meta.best_timing     ? `<div class="fp-meta-row"><span class="fp-meta-l">Best timing</span><span class="fp-meta-v">${esc(meta.best_timing)}</span></div>` : ""}
    </div>` : "";

  return `
    <div class="result-section" id="founder-pitch">
      <div class="result-section-head">
        <div class="result-section-bar"></div>
        <div class="result-section-title">The pitch</div>
      </div>
      ${renderFounderContextStrip(result.profile)}
      <div class="r-card" style="margin-bottom:16px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
          <span style="font-size:13px;color:var(--ink-muted);">Use these three lines on your founder call.</span>
          <button class="btn btn-ghost" style="height:32px;padding:0 12px;font-size:12px;" data-copy="${esc(allBulletText)}">Copy bullets</button>
        </div>
        <div class="fp-bullets">${bulletText}</div>
        ${metaHtml}
      </div>
      ${handlers.length ? `
      <div class="r-card">
        <div style="font-family:var(--font-head);font-size:15px;font-weight:700;margin-bottom:4px;letter-spacing:-.02em;">If they push back</div>
        <div style="font-size:12px;color:var(--ink-muted);margin-bottom:16px;">${handlers.length} scripted response${handlers.length !== 1 ? "s" : ""}</div>
        <div class="fp-objections">${objectionHtml}</div>
      </div>` : ""}
    </div>`;
}

function renderOutreach(prompts, source, error) {
  _outreachItems = prompts || {};
  const entries = Object.entries(_outreachItems);
  if (!entries.length) return "";

  const sourceText = source === "gemini"
    ? "AI-crafted outreach drafts active."
    : "Using local fallback drafts. Add GEMINI_API_KEY to enable AI-crafted drafts.";

  return `
    <div class="result-section" id="outreach">
      <div class="result-section-head">
        <div class="result-section-bar"></div>
        <div class="result-section-title">Outreach kit</div>
      </div>
      <div class="r-card">
        <p style="font-size:12px;color:var(--ink-muted);margin-bottom:14px;">${esc(sourceText)}</p>
        ${error ? `<p class="notice" style="margin-bottom:12px;">${esc(error)}</p>` : ""}
        ${entries.map(([key, item], i) => {
          const plainEmail = `${item.email_subject}\n\n${item.email_body}`;
          return `
            <details class="outreach-item" ${i===0?"open":""}>
              <summary>${esc(item.email_html_data?.product_name || labelize(key))}</summary>
              <div class="outreach-body">
                <div>
                  <div class="outreach-col-label">Email</div>
                  <pre>${esc(plainEmail)}</pre>
                  <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;">
                    <button class="btn btn-ghost" style="height:36px;padding:0 14px;font-size:12px;" data-copy="${esc(plainEmail)}">Copy text</button>
                    <button class="btn il-send-email-btn" style="height:36px;padding:0 16px;font-size:12px;background:#053C6D;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600;" data-key="${esc(key)}">
                      ✉️ Send email
                    </button>
                  </div>
                </div>
                <div>
                  <div class="outreach-col-label">WhatsApp</div>
                  <pre>${esc(item.whatsapp||"")}</pre>
                  <button class="btn btn-ghost" style="height:36px;padding:0 14px;font-size:12px;margin-top:8px;" data-copy="${esc(item.whatsapp||"")}">Copy WhatsApp</button>
                </div>
              </div>
            </details>`;
        }).join("")}
      </div>
    </div>`;
}

function renderDownstream(opps) {
  if (!opps?.length) return "";
  return `
    <div class="result-section">
      <div class="result-section-head">
        <div class="result-section-bar"></div>
        <div class="result-section-title">Downstream opportunities</div>
      </div>
      <div class="downstream-grid">
        ${opps.map(o=>`
          <div class="r-card">
            <div class="card-label">${esc(o.customer_type)} customers</div>
            <div style="font-family:var(--font-head);font-size:16px;font-weight:700;margin-bottom:8px;letter-spacing:-.02em;">${esc(o.product)}</div>
            <p style="font-size:13px;color:var(--ink-muted);line-height:1.55;">${esc(o.rationale)}</p>
            ${o.total_opportunity_lakhs_min !== undefined ? `
              <div class="notice" style="margin-top:10px;">
                Estimated potential: INR ${o.total_opportunity_lakhs_min} – ${o.total_opportunity_lakhs_max} lakhs
              </div>` : ""}
          </div>`).join("")}
      </div>
    </div>`;
}

function renderGlobalProducts(products) {
  if (!products?.length) return emptyState("🌍", "No global benchmarks", "No global product comparisons matched this profile.");
  const statusLabels = { icici:"ICICI Lombard", india_competitor:"Indian market", not_in_india:"Global only" };
  return products.map(p=>`
    <div class="product-card ${p.label==='not_in_india'?'innovation-card':''}">
      <div class="product-card-flag" style="color:var(--ink-faint);">${p.match_basis==='nearest_risk' ? "Nearest benchmark" : (statusLabels[p.label]||"Global")}</div>
      <div class="product-card-name">${esc(p.name)} <span class="product-tag score">${p.relevance_score}/100</span></div>
      <div class="product-card-desc">${esc(p.what_it_covers||"")}</div>
      <div style="font-size:12px;color:var(--ink-muted);">Providers: ${esc(p.providers||"")}</div>
      ${p.label==='not_in_india'?`<p class="notice" style="margin-top:8px;">Product innovation opportunity — flag to product team.</p>`:""}
    </div>`).join("");
}

function renderBreakdown(items) {
  if (!items?.length) return emptyState("⚙️", "No multipliers applied", "No dynamic score multipliers were material for this profile.");
  return items.map(i=>`
    <div class="callout-item">
      <strong>${esc(labelize(i.key))}</strong>
      <span>${esc(i.applied||"")}</span>
      <span style="font-size:11px;color:var(--ink-faint);display:block;margin-top:3px;">${esc(i.stat||"")}</span>
    </div>`).join("");
}

function renderComparisonTable(recs) {
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Product</th><th>Priority</th><th>Fit</th><th>Baseline</th></tr></thead>
        <tbody>
          ${(recs||[]).map(p=>`
            <tr>
              <td>${esc(p.name||p.key)}</td>
              <td>${esc(p.priority||"Optional")}</td>
              <td>${p.score}</td>
              <td>${p.mandatory?"Yes":"No"}</td>
            </tr>`).join("")}
        </tbody>
      </table>
    </div>`;
}

function renderCustomTriggers(triggers) {
  if (!triggers?.length) return "";
  return `
    <div class="r-card innovation-card" style="margin-bottom:24px;">
      <div class="card-label">Product innovation opportunities</div>
      ${triggers.map(t=>`
        <div class="callout-item" style="margin-bottom:10px;">
          <strong>${esc(t.name||labelize(t.key))}</strong>
          <span>${esc(t.description)}</span>
          <div style="font-size:12px;color:var(--ink-faint);margin-top:4px;">IRDAI path: ${esc(t.irdai_path||"")} · Market: ${esc(t.estimated_market_size||"")}</div>
        </div>`).join("")}
    </div>`;
}

/* ─── REFINE PANEL ───────────────────────────────────────────── */
function renderRefineBody() {
  if (!state.meta) return "";
  const meta = state.meta;
  const p = state.profile;

  const mkSlider = (key, label, min, max, step, decimals=2) => {
    const val = Number(p[key] ?? 0);
    return `
      <div class="adv-slider-row">
        <span class="adv-slider-label">${label}</span>
        <input type="range" class="adv-range" min="${min}" max="${max}" step="${step}" value="${val}" data-rkey="${key}" data-dec="${decimals}"
          oninput="this.nextElementSibling.textContent=Number(this.value).toFixed(${decimals})" />
        <span class="adv-slider-val">${val.toFixed(decimals)}</span>
      </div>`;
  };

  const mkNumber = (key, label, step=1, min=0) => {
    const val = p[key] ?? "";
    return `
      <div class="adv-number-item">
        <label class="adv-select-label">${label}</label>
        <input class="f-input adv-number-input" type="number" min="${min}" step="${step}" value="${esc(val)}" data-rkey="${key}" />
      </div>`;
  };

  const mkSelect = (key, label, opts, nullLabel="") => {
    const cur = p[key];
    return `
      <div class="adv-select-item">
        <label class="adv-select-label">${label}</label>
        <select class="f-select" style="height:38px;font-size:13px;" data-rkey="${key}">
          ${nullLabel?`<option value="">${esc(nullLabel)}</option>`:""}
          ${opts.map(o=>`<option value="${esc(o)}" ${cur===o?"selected":""}>${esc(o)}</option>`).join("")}
        </select>
      </div>`;
  };

  const mkCheck = (key, label) => `
    <label class="adv-check">
      <input type="checkbox" data-rkey="${key}" ${p[key]?"checked":""} />
      <span>${label}</span>
    </label>`;

  return `
    <div class="adv-group">
      <div class="adv-group-title">Governance &amp; capital</div>
      <div class="adv-sliders">
        ${mkSlider("investor_cn_hk_pct","China / HK investor BO",0,1,.01)}
        ${mkSlider("cumulative_fundraising_inr_cr","Total fundraising (INR Cr)",0,10000,10,0)}
        ${mkSlider("founder_equity_pct","Founder equity %",0,1,.01)}
      </div>
      <div class="adv-selects">
        ${mkSelect("holdco_domicile","Holdco domicile",meta.holdcoDomiciles)}
        ${mkSelect("rbi_registration","RBI registration",meta.rbiRegistrations,"None")}
      </div>
      <div class="adv-checks">
        ${mkCheck("dpiit_recognition","DPIIT recognised startup")}
        ${mkCheck("has_independent_directors","Has independent board directors")}
      </div>
    </div>
    <div class="adv-group">
      <div class="adv-group-title">Commercial sizing for pricing</div>
      <div class="adv-number-grid">
        ${mkNumber("annual_revenue_cr","Annual revenue / ARR",0.1)}
        ${mkNumber("total_insurable_asset_value_cr","Total insurable asset value",0.1)}
        ${mkNumber("gross_profit_cr","Gross profit / BI basis",0.1)}
        ${mkNumber("claims_last_3_years","Claims last 3 years",1)}
      </div>
    </div>
    <div class="adv-group">
      <div class="adv-group-title">Data &amp; AI</div>
      <div class="adv-sliders">
        ${mkSlider("hardware_software_split","Hardware revenue share",0,1,.01)}
      </div>
      <div class="adv-selects">
        ${mkSelect("data_localisation_status","Data localisation",["Unknown","Full_onshore","Hybrid","Offshore"])}
        ${mkSelect("ai_tier","AI tier",meta.aiTiers)}
      </div>
      <div class="adv-checks">${mkCheck("sdf_likely","DPDP Act §10 Significant Data Fiduciary designation likely")}</div>
    </div>
    <div class="adv-group" style="border-bottom:none;margin-bottom:0;padding-bottom:0;">
      <div class="adv-group-title">Market &amp; supply chain</div>
      <div class="adv-sliders">
        ${mkSlider("b2b_pct","B2B revenue",0,1,.01)}
        ${mkSlider("export_eu_pct","EU revenue",0,1,.01)}
        ${mkSlider("export_us_pct","US revenue",0,1,.01)}
        ${mkSlider("export_china_pct","China revenue",0,1,.01)}
        ${mkSlider("chinese_supplier_pct_cogs","Chinese supplier COGS",0,1,.01)}
      </div>
      <div class="adv-checks">${mkCheck("listed_customer_brsr_dependency","Listed customers require BRSR")}</div>
    </div>
    <div class="adv-group" style="border-bottom:none;margin-bottom:0;padding-bottom:0;">
      <div class="adv-group-title">Specialty exposure triggers</div>
      <div class="adv-number-grid">
        ${mkNumber("fleet_count","Owned/operated fleet count",1)}
        ${mkNumber("project_value_cr","Project / contract value",0.1)}
      </div>
      <div class="adv-checks">
        ${mkCheck("healthcare_operations","Healthcare/clinical operations")}
        ${mkCheck("payment_or_card_program","Payment/card programme")}
        ${mkCheck("product_recall_exposure","Product recall exposure")}
        ${mkCheck("food_or_pharma_manufacturing","Food/pharma manufacturing")}
        ${mkCheck("contract_bid_or_performance_bond_need","Bid/performance bond need")}
        ${mkCheck("event_or_production_operations","Event/production operations")}
      </div>
    </div>
    <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border);display:flex;gap:10px;align-items:center;">
      <button class="btn btn-primary" id="refine-run-btn" type="button">Recalculate scores</button>
      <span id="refine-status" style="font-size:12px;color:var(--ink-muted);"></span>
    </div>`;
}

function bindRefine() {
  const body = $("refine-body");
  if (!body) return;
  let timer = null;

  // Sliders auto-update profile
  body.querySelectorAll("input[type='range'][data-rkey]").forEach(el => {
    el.addEventListener("input", () => {
      state.profile[el.dataset.rkey] = Number(el.value);
    });
  });

  body.querySelectorAll("input[type='number'][data-rkey]").forEach(el => {
    el.addEventListener("input", () => {
      state.profile[el.dataset.rkey] = Number(el.value || 0);
    });
  });

  body.querySelectorAll("select[data-rkey]").forEach(el => {
    el.addEventListener("change", () => {
      const val = el.value || null;
      state.profile[el.dataset.rkey] = val;
      if (el.dataset.rkey === "ai_tier") state.profile.ai_in_product = val !== "None";
    });
  });

  body.querySelectorAll("input[type='checkbox'][data-rkey]").forEach(el => {
    el.addEventListener("change", () => {
      state.profile[el.dataset.rkey] = el.checked;
    });
  });

  const runBtn = $("refine-run-btn");
  const status = $("refine-status");

  if (runBtn) {
    runBtn.addEventListener("click", async () => {
      runBtn.disabled = true;
      runBtn.textContent = "Recalculating…";
      if (status) status.textContent = "";
      try {
        const res = await fetch("/api/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(buildProfile()),
        });
        const result = await res.json();
        if (!res.ok || result.error) throw new Error(result.error || "Failed");
        renderResults(result);
      } catch (err) {
        if (status) status.textContent = `Error: ${err.message}`;
      } finally {
        if (runBtn) { runBtn.disabled = false; runBtn.textContent = "Recalculate scores"; }
      }
    });
  }
}

/* ─── DOWNLOAD ───────────────────────────────────────────────── */
window.downloadReport = function(result) {
  if (!result) return;
  const lines = [
    `SPARC Risk Report — ${result.profile.startup_name}`,
    `Generated: ${new Date().toLocaleDateString("en-IN")}`,
    "",
    `Sector: ${result.profile.sector}`,
    `Stage: ${result.profile.funding_stage}`,
    `Team size: ${result.profile.team_size}`,
    `Overall risk: ${result.overall}/100`,
    result.bundle_only_pricing_quote?.gross_premium_lakh ? `Bundle price: INR ${result.bundle_only_pricing_quote.gross_premium_lakh} lakhs incl. GST` : "Bundle price: not requested",
    result.pricing_engine_quote?.gross_premium_lakh ? `Full cover price: INR ${result.pricing_engine_quote.gross_premium_lakh} lakhs incl. GST` : "Full cover price: not requested",
    "",
    "TOP RISKS:",
    ...(result.top_risks||[]).map(r => `  · ${r.name}: ${r.score}/100`),
    "",
    "RECOMMENDATIONS:",
    ...(result.recommendations||[]).map(p => `  · ${p.name||p.key}: ${p.priority} (${p.score}/100)`),
    "",
    "MITIGATION ACTIONS:",
    ...(result.mitigations||[]).map(m => `  · ${m.risk}: ${m.action}`),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `${(result.profile.startup_name||"startup").replace(/\s+/g,"-")}-sparc-report.txt`;
  a.click();
  URL.revokeObjectURL(url);
};

/* ─── RADAR CHART ────────────────────────────────────────────── */
function drawRadar(canvasId, data, opts = {}) {
  const canvas = $(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const entries = Object.entries(data || {});
  if (!entries.length) return;

  const W = canvas.width, H = canvas.height;
  const cx = W / 2, cy = H / 2;
  const R = Math.min(W, H) * 0.3;
  const maxLen = opts.maxLabelLength || 14;

  ctx.clearRect(0, 0, W, H);

  // Grid rings
  for (let ring = 1; ring <= 4; ring++) {
    ctx.beginPath();
    entries.forEach((_, i) => {
      const angle = -Math.PI/2 + i * 2*Math.PI / entries.length;
      const r = R * ring / 4;
      const x = cx + Math.cos(angle)*r, y = cy + Math.sin(angle)*r;
      i === 0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
    });
    ctx.closePath();
    ctx.strokeStyle = "#E2E2DC";
    ctx.lineWidth = 1;
    ctx.stroke();
  }

  // Axis lines + labels
  ctx.font = "10px 'DM Sans', system-ui, sans-serif";
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  entries.forEach(([label], i) => {
    const angle = -Math.PI/2 + i * 2*Math.PI / entries.length;
    const x = cx + Math.cos(angle)*R, y = cy + Math.sin(angle)*R;
    ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(x,y);
    ctx.strokeStyle = "#E2E2DC"; ctx.lineWidth = 1; ctx.stroke();
    const lx = cx + Math.cos(angle)*(R+28), ly = cy + Math.sin(angle)*(R+28);
    ctx.fillStyle = "#94A3B8";
    const short = label.length > maxLen ? label.slice(0, maxLen-1)+"…" : label;
    ctx.fillText(short, lx, ly);
  });

  // Data polygon
  ctx.beginPath();
  entries.forEach(([_, score], i) => {
    const angle = -Math.PI/2 + i * 2*Math.PI / entries.length;
    const r = R * Math.min(100, Number(score)) / 100;
    const x = cx + Math.cos(angle)*r, y = cy + Math.sin(angle)*r;
    i === 0 ? ctx.moveTo(x,y) : ctx.lineTo(x,y);
  });
  ctx.closePath();
  ctx.fillStyle = "rgba(173,30,35,.14)";
  ctx.strokeStyle = "#AD1E23";
  ctx.lineWidth = 2;
  ctx.fill(); ctx.stroke();

  // Dots on vertices
  entries.forEach(([_, score], i) => {
    const angle = -Math.PI/2 + i * 2*Math.PI / entries.length;
    const r = R * Math.min(100, Number(score)) / 100;
    const x = cx + Math.cos(angle)*r, y = cy + Math.sin(angle)*r;
    ctx.beginPath(); ctx.arc(x,y,3,0,2*Math.PI);
    ctx.fillStyle = "#AD1E23"; ctx.fill();
  });
}

/* ─── COMMERCE MODE (M1 — Funding Feed only) ────────────────── */
const COMMERCE_RAIL = [
  { id: "opportunity",   label: "Opportunity",   ready: true,  hint: "Territory GWP, funnel, top leads" },
  { id: "funding",       label: "Funding Feed",  ready: true,  hint: "Newly funded startups with auto-valued GWP" },
  { id: "pipeline",      label: "Pipeline",      ready: true,  hint: "Accounts by stage — move deals forward" },
  { id: "renewals",      label: "Renewals",      ready: true,  hint: "Renewal / upsell / at-risk / coverage-gap alerts" },
  { id: "performance",   label: "Performance",   ready: true,  hint: "RM leaderboard, conversion, weekly digest" },
];

const COMMERCE_DEFAULT_RM = "ilom43171@icicilombard.com";

function _setTopbarMode(mode) {
  document.querySelectorAll(".topbar-mode-pill").forEach(b => {
    const isActive = b.getAttribute("data-mode") === mode;
    b.classList.toggle("is-active", isActive);
    b.setAttribute("aria-selected", isActive ? "true" : "false");
  });
}

function enterCommerceMode(railId = "opportunity") {
  _setTopbarMode("commerce");
  renderCommerceShell(railId);
}

function exitCommerceMode() {
  _setTopbarMode("analyse");
  // Return to whatever the user was last on. If a result exists, render it;
  // otherwise return to the landing role selection.
  if (window.__result?.profile?.startup_name) {
    renderResults(window.__result);
  } else {
    renderRoleSelection();
  }
}

function renderCommerceShell(activeRailId) {
  const rail = COMMERCE_RAIL.map(item => {
    const cls = ["cmx-rail-item"];
    if (item.id === activeRailId) cls.push("is-active");
    if (!item.ready) cls.push("is-disabled");
    return `<button type="button" class="${cls.join(" ")}" data-rail="${item.id}" ${item.ready ? "" : "aria-disabled=\"true\""} title="${esc(item.hint)}">
      <span class="cmx-rail-label">${esc(item.label)}</span>
      ${item.ready ? "" : `<span class="cmx-rail-soon">soon</span>`}
    </button>`;
  }).join("");

  $("main-content").innerHTML = `
    <div class="cmx-shell">
      <aside class="cmx-rail" aria-label="Commerce sections">
        <div class="cmx-rail-eyebrow">Commerce</div>
        ${rail}
      </aside>
      <section class="cmx-content" id="cmx-content"></section>
    </div>`;

  document.querySelectorAll(".cmx-rail-item").forEach(btn => {
    btn.addEventListener("click", () => {
      const id = btn.getAttribute("data-rail");
      const item = COMMERCE_RAIL.find(x => x.id === id);
      if (!item || !item.ready) return;
      enterCommerceMode(id);
    });
  });

  if (activeRailId === "funding") {
    renderFundingFeed();
  } else if (activeRailId === "opportunity") {
    renderOpportunity();
  } else if (activeRailId === "performance") {
    renderPerformance();
  } else if (activeRailId === "pipeline") {
    renderPipeline();
  } else if (activeRailId === "renewals") {
    renderRenewals();
  } else {
    $("cmx-content").innerHTML = `
      <div class="cmx-empty">
        <div class="cmx-empty-eyebrow">Coming soon</div>
        <h2 class="cmx-empty-headline">This section ships in a later milestone.</h2>
        <p class="cmx-empty-sub">Funding Feed is live now — claim a lead to seed the pipeline.</p>
        <button type="button" class="btn-primary" onclick="enterCommerceMode('funding')">Open Funding Feed →</button>
      </div>`;
  }
}

/* ── Money formatter — INR rupees → ₹L / ₹Cr ranges ────────── */
function fmtInrRange(low, high) {
  const fmt = v => {
    const n = Number(v) || 0;
    if (n >= 1e7)  return (n / 1e7).toFixed(n >= 1e8 ? 0 : 1).replace(/\.0$/, "") + " Cr";
    if (n >= 1e5)  return Math.round(n / 1e5) + " L";
    return Math.round(n).toLocaleString("en-IN");
  };
  const lo = fmt(low), hi = fmt(high);
  // Same unit suffix → collapse: "₹2–5 Cr" not "₹2 Cr–5 Cr"
  const loParts = lo.split(" "), hiParts = hi.split(" ");
  if (loParts.length === 2 && hiParts.length === 2 && loParts[1] === hiParts[1]) {
    return `₹${loParts[0]}–${hiParts[0]} ${hiParts[1]}`;
  }
  return `₹${lo} – ₹${hi}`;
}

/* ── Opportunity (F1 GWP Dashboard) ─────────────────────────── */
const _oppState = { data: null, scope: { city: "", sector: "", stage: "" }, sort_by: "gwp_high" };

const _FUNNEL_LABELS = {
  prospect:  "Prospect",
  analysed:  "Analysed",
  quoted:    "Quoted",
  converted: "Converted",
  lost:      "Lost",
};

async function renderOpportunity() {
  const target = $("cmx-content");
  if (!target) return;
  target.innerHTML = `
    <div class="opp-hero" id="opp-hero">
      <div class="opp-hero-eyebrow">Territory opportunity</div>
      <div class="opp-hero-headline" id="opp-hero-headline">Loading…</div>
      <div class="opp-hero-sub" id="opp-hero-sub">Aggregating accounts and open leads.</div>
      <div class="opp-hero-scope" id="opp-hero-scope"></div>
      <div class="opp-hero-disclaimer" id="opp-hero-disclaimer">Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.</div>
    </div>
    <h3 class="opp-section-h">Pipeline funnel</h3>
    <div class="opp-funnel" id="opp-funnel"></div>
    <div class="opp-leads-head">
      <h3 class="opp-section-h">Top-value leads</h3>
      <div class="opp-sort">
        <span class="cmx-filter-label">Sort</span>
        <button type="button" class="cmx-chip is-active" data-sort="gwp_high">GWP high</button>
        <button type="button" class="cmx-chip" data-sort="gwp_low">GWP low</button>
        <button type="button" class="cmx-chip" data-sort="sector">Sector</button>
        <button type="button" class="cmx-chip" data-sort="city">City</button>
      </div>
    </div>
    <div class="opp-leads" id="opp-leads"><div class="cmx-skeleton">Loading…</div></div>`;

  document.querySelectorAll(".opp-sort .cmx-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".opp-sort .cmx-chip").forEach(b => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      _oppState.sort_by = btn.getAttribute("data-sort");
      refreshOpportunity();
    });
  });

  await refreshOpportunity();
}

async function refreshOpportunity() {
  const qs = new URLSearchParams();
  const s = _oppState.scope;
  if (s.city)   qs.set("city", s.city);
  if (s.sector) qs.set("sector", s.sector);
  if (s.stage)  qs.set("stage", s.stage);
  qs.set("sort_by", _oppState.sort_by);
  qs.set("limit", "10");
  let data;
  try {
    const res = await fetch("/api/commerce/dashboard?" + qs.toString());
    data = await res.json();
  } catch (e) {
    const leads = $("opp-leads");
    if (leads) leads.innerHTML = `<div class="cmx-error">Failed to load: ${esc(String(e))}</div>`;
    return;
  }
  _oppState.data = data;
  _renderOppHero(data);
  _renderOppFunnel(data.funnel || []);
  _renderOppLeads(data.top_leads || []);
  const d = $("opp-hero-disclaimer");
  if (d && data.disclaimer) d.textContent = data.disclaimer;
}

function _renderOppHero(data) {
  const t = data.territory_gwp || {};
  const h = $("opp-hero-headline");
  const sub = $("opp-hero-sub");
  if (h) {
    h.textContent = (t.low_inr || t.high_inr)
      ? `${fmtInrRange(t.low_inr, t.high_inr)} addressable GWP`
      : "No accounts in scope yet";
  }
  if (sub) {
    const n = (t.account_count || 0) + (t.open_lead_count || 0);
    sub.textContent = n
      ? `${t.account_count} pipeline account${t.account_count === 1 ? "" : "s"} · ${t.open_lead_count} open funded lead${t.open_lead_count === 1 ? "" : "s"}`
      : "Import a funding CSV to size the opportunity.";
  }
}

function _renderOppFunnel(funnel) {
  const node = $("opp-funnel");
  if (!node) return;
  node.innerHTML = funnel.map((row, i) => `
    <div class="opp-funnel-tile" data-stage="${esc(row.stage)}">
      <div class="opp-funnel-label">${esc(_FUNNEL_LABELS[row.stage] || row.stage)}</div>
      <div class="opp-funnel-count">${row.count.toLocaleString("en-IN")}</div>
      <div class="opp-funnel-gwp">${(row.gwp_low_inr || row.gwp_high_inr) ? fmtInrRange(row.gwp_low_inr, row.gwp_high_inr) : "—"}</div>
    </div>
    ${i < funnel.length - 1 ? `<div class="opp-funnel-chev" aria-hidden="true">›</div>` : ""}
  `).join("");
}

function _renderOppLeads(leads) {
  const node = $("opp-leads");
  if (!node) return;
  if (leads.length === 0) {
    node.innerHTML = `
      <div class="cmx-empty-card">
        <div class="cmx-empty-eyebrow">No accounts</div>
        <p>Claim a funding lead to populate the pipeline and surface top-value accounts here.</p>
        <button type="button" class="btn-primary" onclick="enterCommerceMode('funding')">Open Funding Feed →</button>
      </div>`;
    return;
  }
  // Stash leads so the proposal handler can look them up by account_id.
  _oppState.leads_by_id = {};
  leads.forEach(l => { _oppState.leads_by_id[l.account_id] = l; });
  node.innerHTML = leads.map(l => `
    <article class="cmx-lead-card opp-lead">
      <div class="cmx-lead-main">
        <div class="cmx-lead-row1">
          <h3 class="cmx-lead-name">${esc(l.name || "—")}</h3>
          <span class="cmx-lead-meta">${[esc(l.sector || ""), esc(l.stage || ""), esc(l.city || "")].filter(Boolean).join(" · ")}</span>
        </div>
        ${l.rm_email ? `<div class="cmx-lead-source">RM · ${esc(l.rm_email)}</div>` : ""}
        <div class="cmx-lead-bundle">
          <span class="cmx-lead-bundle-label">Stage</span>
          <span class="cmx-lead-bundle-value">${esc((_FUNNEL_LABELS[l.pipeline_stage] || l.pipeline_stage) || "—")}</span>
        </div>
      </div>
      <div class="cmx-lead-side">
        <div class="cmx-lead-gwp-label">Estimated annual GWP</div>
        <div class="cmx-lead-gwp">${fmtInrRange(l.gwp_low_inr, l.gwp_high_inr)}</div>
        <button type="button" class="btn-primary cmx-lead-claim" data-proposal="${esc(l.account_id || "")}">Generate proposal</button>
      </div>
    </article>
  `).join("");
  node.querySelectorAll("[data-proposal]").forEach(btn => {
    btn.addEventListener("click", () => generateProposalForAccount(btn.getAttribute("data-proposal")));
  });
}

/* ── F3 Proposal generation + preview modal ────────────────── */
function _analysisFromLead(lead) {
  // Synthesise a minimal analysis stub from the lead card data. The proposal
  // builder enriches via the account row when account_id is known; the
  // bundle covers come from whatever the engine attached when the lead was
  // ingested (stored on the account/funding_lead row for richer cases).
  return {
    profile: {
      startup_name:  lead.name,
      sector:        lead.sector,
      funding_stage: lead.stage,
      city:          lead.city,
    },
    bundle_match: {
      name: "Recommended bundle",
      // The proposal_builder falls back to top-level recommendations if
      // bundle_match.mandatory_covers is empty.
      mandatory_covers: [],
    },
    recommendations: ["CYBER", "D_AND_O", "GROUP_HEALTH"],
  };
}

async function generateProposalForAccount(accountId) {
  if (!accountId) return;
  const lead = (_oppState.leads_by_id || {})[accountId];
  if (!lead) return;
  const analysis = window.__result?.profile?.startup_name === lead.name
    ? window.__result
    : _analysisFromLead(lead);

  _openProposalModalLoading(lead);
  let data;
  try {
    const res = await fetch("/api/commerce/proposal", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ account_id: accountId, analysis }),
    });
    data = await res.json();
  } catch (e) {
    _setProposalModalError("Network error: " + e);
    return;
  }
  if (!data || data.error) {
    _setProposalModalError(data?.error || "Proposal generation failed.");
    return;
  }
  _renderProposalModalReady(lead, data);
}

function _proposalModalShell(lead) {
  return `
    <div class="cmx-modal cmx-proposal-modal" role="dialog" aria-modal="true" aria-labelledby="cmx-prop-title">
      <header class="cmx-modal-head">
        <h2 id="cmx-prop-title">Proposal · ${esc(lead.name || "—")}</h2>
        <button type="button" class="cmx-modal-x" aria-label="Close" data-close>×</button>
      </header>
      <div class="cmx-modal-body" id="cmx-prop-body">
        <div class="cmx-skeleton">Generating proposal…</div>
      </div>
      <footer class="cmx-modal-foot">
        <button type="button" class="btn-ghost" data-close>Close</button>
        <button type="button" class="btn-primary" id="cmx-prop-open" disabled>Open & save as PDF</button>
      </footer>
    </div>`;
}

function _openProposalModalLoading(lead) {
  closeProposalModal();
  const overlay = document.createElement("div");
  overlay.id = "cmx-prop-modal";
  overlay.className = "cmx-modal-overlay";
  overlay.innerHTML = _proposalModalShell(lead);
  document.body.appendChild(overlay);
  overlay.querySelectorAll("[data-close]").forEach(b => b.addEventListener("click", closeProposalModal));
  overlay.addEventListener("click", e => { if (e.target === overlay) closeProposalModal(); });
}

function _setProposalModalError(msg) {
  const body = document.getElementById("cmx-prop-body");
  if (body) body.innerHTML = `<div class="cmx-error">${esc(msg)}</div>`;
}

function _renderProposalModalReady(lead, data) {
  const body = document.getElementById("cmx-prop-body");
  const openBtn = document.getElementById("cmx-prop-open");
  if (!body) return;
  body.innerHTML = `
    <div class="cmx-prop-meta">
      <div><span class="cmx-prop-label">Proposal</span> <strong>${esc(data.proposal_id)}</strong></div>
      <div><span class="cmx-prop-label">Bundle</span> ${esc(data.bundle || "—")}</div>
      <div><span class="cmx-prop-label">Indicative GWP</span> <strong>${fmtInrRange(data.gwp_low_inr, data.gwp_high_inr)}</strong></div>
    </div>
    <iframe class="cmx-prop-iframe" id="cmx-prop-iframe" title="Proposal preview"></iframe>
    <p class="cmx-prop-disclaimer">${esc(data.disclaimer)}</p>`;
  // Fill iframe with the HTML (srcdoc keeps it inline, no extra request).
  const iframe = document.getElementById("cmx-prop-iframe");
  if (iframe) iframe.srcdoc = data.html;
  if (openBtn) {
    openBtn.disabled = false;
    openBtn.onclick = () => _openProposalInNewTab(data);
  }
}

function _openProposalInNewTab(data) {
  const blob = new Blob([data.html], { type: "text/html" });
  const url = URL.createObjectURL(blob);
  const win = window.open(url, "_blank");
  // Revoke the blob URL after the new tab has a chance to load.
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
  if (!win) {
    // Popup blocked — fall back to download.
    const a = document.createElement("a");
    a.href = url;
    a.download = `${data.proposal_id}.html`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }
}

function closeProposalModal() {
  const node = document.getElementById("cmx-prop-modal");
  if (node) node.remove();
}

window.generateProposalForAccount = generateProposalForAccount;

/* ── F2 RM Performance ─────────────────────────────────────── */
function _fmtPct(rate) {
  return ((rate || 0) * 100).toFixed(0) + "%";
}
function _fmtDays(sec) {
  if (sec == null) return "—";
  const days = sec / 86400;
  if (days >= 1) return `${days.toFixed(1)}d`;
  return `${(sec / 3600).toFixed(1)}h`;
}

async function renderPerformance() {
  const target = $("cmx-content");
  if (!target) return;
  target.innerHTML = `
    <header class="cmx-feed-head">
      <div>
        <div class="cmx-eyebrow">RM intelligence</div>
        <h1 class="cmx-headline">Performance</h1>
        <p class="cmx-sub">Activity, conversion, and weekly digest across the territory.</p>
      </div>
    </header>
    <div id="perf-tiles" class="perf-tiles"></div>
    <h3 class="opp-section-h">RM leaderboard</h3>
    <div id="perf-leaderboard" class="perf-leaderboard"><div class="cmx-skeleton">Loading…</div></div>
    <h3 class="opp-section-h">Sector conversion</h3>
    <div id="perf-sectors" class="perf-sectors"></div>
    <h3 class="opp-section-h">Weekly digest</h3>
    <div id="perf-digest" class="perf-digest"></div>
    <p class="cmx-disclaimer" id="perf-disclaimer">Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.</p>`;
  await refreshPerformance();
}

async function refreshPerformance() {
  let data;
  try {
    const res = await fetch("/api/commerce/metrics");
    data = await res.json();
  } catch (e) {
    const lb = $("perf-leaderboard");
    if (lb) lb.innerHTML = `<div class="cmx-error">Failed to load: ${esc(String(e))}</div>`;
    return;
  }
  _renderPerfTiles(data.speed || {});
  _renderPerfLeaderboard(data.leaderboard || []);
  _renderPerfSectors(data.conversion_by_sector || []);
  _renderPerfDigest(data.digest || {});
  if (data.disclaimer) {
    const d = $("perf-disclaimer"); if (d) d.textContent = data.disclaimer;
  }
}

function _renderPerfTiles(speed) {
  const node = $("perf-tiles");
  if (!node) return;
  const tiles = [
    ["Prospect → Analysed", speed.prospect_to_analysed],
    ["Analysed → Quoted",   speed.analysed_to_quoted],
    ["Quoted → Converted",  speed.quoted_to_converted],
  ];
  node.innerHTML = tiles.map(([label, t]) => `
    <div class="perf-tile">
      <div class="perf-tile-label">${esc(label)}</div>
      <div class="perf-tile-value">${_fmtDays(t && t.median_seconds)}</div>
      <div class="perf-tile-n">${t && t.n ? `n = ${t.n}` : "no transitions yet"}</div>
    </div>`).join("");
}

function _renderPerfLeaderboard(rows) {
  const node = $("perf-leaderboard");
  if (!node) return;
  if (rows.length === 0) {
    node.innerHTML = `<div class="cmx-skeleton">No RM activity yet.</div>`;
    return;
  }
  const head = `
    <div class="perf-lb-row perf-lb-head">
      <div>RM</div>
      <div class="perf-lb-num">Claimed</div>
      <div class="perf-lb-num">Quoted</div>
      <div class="perf-lb-num">Proposals</div>
      <div class="perf-lb-num">Converted</div>
      <div class="perf-lb-conv">Conversion</div>
      <div class="perf-lb-gwp">Pipeline GWP</div>
    </div>`;
  const body = rows.map(r => `
    <div class="perf-lb-row">
      <div>
        <div class="perf-lb-name">${esc(r.name || r.rm_email)}</div>
        <div class="perf-lb-email">${esc(r.rm_email)}</div>
      </div>
      <div class="perf-lb-num">${r.claimed || 0}</div>
      <div class="perf-lb-num">${r.quoted || 0}</div>
      <div class="perf-lb-num">${r.proposals || 0}</div>
      <div class="perf-lb-num">${r.converted || 0}</div>
      <div class="perf-lb-conv">
        <div class="perf-bar" aria-label="${_fmtPct(r.conversion_rate)} conversion">
          <div class="perf-bar-fill" style="width: ${Math.min(100, (r.conversion_rate || 0) * 100)}%"></div>
        </div>
        <span class="perf-bar-text">${_fmtPct(r.conversion_rate)}</span>
      </div>
      <div class="perf-lb-gwp">${(r.pipeline_gwp_low || r.pipeline_gwp_high) ? fmtInrRange(r.pipeline_gwp_low, r.pipeline_gwp_high) : "—"}</div>
    </div>`).join("");
  node.innerHTML = head + body;
}

function _renderPerfSectors(rows) {
  const node = $("perf-sectors");
  if (!node) return;
  if (rows.length === 0) {
    node.innerHTML = `<div class="cmx-skeleton">No sector activity yet.</div>`;
    return;
  }
  const maxQuoted = Math.max(...rows.map(r => r.quoted || 0), 1);
  node.innerHTML = rows.map(r => `
    <div class="perf-sector-row">
      <div class="perf-sector-name">${esc(r.sector)}</div>
      <div class="perf-sector-bars">
        <div class="perf-sector-bar perf-sector-bar-quoted" style="width: ${((r.quoted || 0) / maxQuoted) * 100}%"></div>
        <div class="perf-sector-bar perf-sector-bar-converted" style="width: ${((r.converted || 0) / maxQuoted) * 100}%"></div>
      </div>
      <div class="perf-sector-meta">${r.converted || 0} converted · ${r.quoted || 0} quoted · ${_fmtPct(r.conv_rate)}</div>
    </div>`).join("");
}

function _renderPerfDigest(digest) {
  const node = $("perf-digest");
  if (!node) return;
  if (!digest || !digest.headline) {
    node.innerHTML = `<div class="cmx-skeleton">No digest data yet.</div>`;
    return;
  }
  const t = digest.totals || {};
  const top = digest.top_rm;
  const sectors = digest.best_converting_sectors || [];
  node.innerHTML = `
    <article class="cmx-lead-card perf-digest-card">
      <div class="cmx-lead-main">
        <div class="cmx-eyebrow">SVP weekly summary</div>
        <h3 class="cmx-lead-name perf-digest-h">${esc(digest.headline)}</h3>
        <div class="perf-digest-totals">
          <span>${t.claimed || 0} claimed</span> ·
          <span>${t.quoted || 0} quoted</span> ·
          <span>${t.proposals || 0} proposals</span> ·
          <span>${t.converted || 0} converted</span>
        </div>
        ${top ? `<div class="cmx-lead-source">Top RM · <strong>${esc(top.name || top.rm_email)}</strong> · pipeline ${fmtInrRange(0, top.pipeline_gwp_high_inr)}</div>` : ""}
        ${sectors.length ? `<div class="cmx-lead-source">Best converting · ${sectors.map(s => esc(s.sector) + " (" + _fmtPct(s.conv_rate) + ")").join(" · ")}</div>` : ""}
      </div>
      <div class="cmx-lead-side">
        <button type="button" class="btn-primary" id="perf-send-digest">Send digest</button>
      </div>
    </article>`;
  const btn = $("perf-send-digest");
  if (btn) btn.addEventListener("click", sendWeeklyDigest);
}

async function sendWeeklyDigest() {
  const btn = $("perf-send-digest");
  if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
  let data;
  try {
    const res = await fetch("/api/commerce/metrics", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ action: "send_digest" }),
    });
    data = await res.json();
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = "Send digest"; }
    alert("Send failed: " + e);
    return;
  }
  if (btn) {
    btn.textContent = data.ok ? "✓ Sent" : "Send failed";
    setTimeout(() => { btn.disabled = false; btn.textContent = "Send digest"; }, 2000);
  }
}

/* ── Funding Feed screen ───────────────────────────────────── */
const _cmxState = { leads: [], filters: { city: "", sector: "", stage: "" } };

async function renderFundingFeed() {
  const target = $("cmx-content");
  if (!target) return;
  target.innerHTML = `
    <div class="cmx-feed">
      <header class="cmx-feed-head">
        <div>
          <div class="cmx-eyebrow">New leads</div>
          <h1 class="cmx-headline" id="cmx-feed-headline">Loading funded startups…</h1>
          <p class="cmx-sub" id="cmx-feed-sub">Auto-analysed and valued from the latest ingest.</p>
        </div>
        <div class="cmx-feed-actions">
          <button type="button" class="btn-ghost" onclick="openFundingImportModal()">Import funding CSV</button>
        </div>
      </header>
      <div class="cmx-filters" id="cmx-filters"></div>
      <div class="cmx-feed-list" id="cmx-feed-list">
        <div class="cmx-skeleton">Loading…</div>
      </div>
      <p class="cmx-disclaimer" id="cmx-feed-disclaimer">Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.</p>
    </div>`;

  await refreshFundingFeed();
}

async function refreshFundingFeed() {
  const list = $("cmx-feed-list");
  if (!list) return;
  const f = _cmxState.filters;
  const qs = new URLSearchParams();
  if (f.city)   qs.set("city", f.city);
  if (f.sector) qs.set("sector", f.sector);
  if (f.stage)  qs.set("stage", f.stage);
  let data;
  try {
    const res = await fetch("/api/commerce/funding" + (qs.toString() ? "?" + qs : ""));
    data = await res.json();
  } catch (e) {
    list.innerHTML = `<div class="cmx-error">Failed to load leads: ${esc(String(e))}</div>`;
    return;
  }
  _cmxState.leads = data.leads || [];
  renderFundingFilters();
  renderFundingCards();
  renderFundingHeader(data);
  if (data.disclaimer) {
    const d = $("cmx-feed-disclaimer");
    if (d) d.textContent = data.disclaimer;
  }
}

function renderFundingHeader(data) {
  const leads = _cmxState.leads;
  const sumLo = leads.reduce((a, x) => a + (x.est_gwp_low_inr || 0), 0);
  const sumHi = leads.reduce((a, x) => a + (x.est_gwp_high_inr || 0), 0);
  const byCity = {};
  leads.forEach(x => { const c = x.city || "Unknown"; byCity[c] = (byCity[c] || 0) + 1; });
  const cityStr = Object.entries(byCity)
    .sort((a,b) => b[1]-a[1]).slice(0,3)
    .map(([c,n]) => `${esc(c)} (${n})`).join(" · ");
  const h = $("cmx-feed-headline");
  const s = $("cmx-feed-sub");
  if (leads.length === 0) {
    if (h) h.textContent = "No leads in scope yet.";
    if (s) s.textContent = "Import a funding CSV to size the opportunity.";
    return;
  }
  if (h) h.textContent = `${fmtInrRange(sumLo, sumHi)} surfaced GWP`;
  if (s) s.textContent = `${leads.length} funded startups · ${cityStr || "across India"}`;
}

function _uniq(values) {
  return Array.from(new Set(values.filter(Boolean))).sort();
}

function renderFundingFilters() {
  const node = $("cmx-filters");
  if (!node) return;
  const leads = _cmxState.leads;
  const cities  = _uniq(leads.map(x => x.city));
  const sectors = _uniq(leads.map(x => x.sector));
  const stages  = _uniq(leads.map(x => x.stage));
  const f = _cmxState.filters;
  const mkGroup = (label, key, values) => {
    if (!values.length) return "";
    const pills = ['<button type="button" class="cmx-chip ' + (f[key] ? "" : "is-active") + '" data-filter="' + key + '" data-value="">All</button>']
      .concat(values.map(v => `<button type="button" class="cmx-chip ${f[key] === v ? "is-active" : ""}" data-filter="${key}" data-value="${esc(v)}">${esc(v)}</button>`))
      .join("");
    return `<div class="cmx-filter-group"><span class="cmx-filter-label">${label}</span>${pills}</div>`;
  };
  node.innerHTML = mkGroup("City", "city", cities) + mkGroup("Sector", "sector", sectors) + mkGroup("Stage", "stage", stages);
  node.querySelectorAll(".cmx-chip").forEach(btn => {
    btn.addEventListener("click", () => {
      const key = btn.getAttribute("data-filter");
      _cmxState.filters[key] = btn.getAttribute("data-value") || "";
      refreshFundingFeed();
    });
  });
}

function renderFundingCards() {
  const list = $("cmx-feed-list");
  if (!list) return;
  const leads = _cmxState.leads;
  if (leads.length === 0) {
    list.innerHTML = `
      <div class="cmx-empty-card">
        <div class="cmx-empty-eyebrow">No leads</div>
        <p>Import a funding CSV to populate the feed.</p>
        <button type="button" class="btn-primary" onclick="openFundingImportModal()">Import funding CSV</button>
      </div>`;
    return;
  }
  list.innerHTML = leads.map(lead => _renderLeadCard(lead)).join("");
  list.querySelectorAll("[data-claim]").forEach(btn => {
    btn.addEventListener("click", () => claimFundingLead(btn.getAttribute("data-claim")));
  });
}

function _renderLeadCard(lead) {
  const amount = lead.amount_inr ? `· ${fmtInrRange(lead.amount_inr, lead.amount_inr).replace("–"+fmtInrRange(lead.amount_inr, lead.amount_inr).split("–")[1], "")} raised` : "";
  const round = lead.round ? `· ${esc(lead.round)}` : "";
  const meta  = [lead.source, lead.announced_on].filter(Boolean).map(esc).join(" · ");
  const claimed = lead.status === "claimed";
  return `
    <article class="cmx-lead-card${claimed ? " is-claimed" : ""}" data-lead="${esc(lead.lead_id)}">
      <div class="cmx-lead-main">
        <div class="cmx-lead-row1">
          <h3 class="cmx-lead-name">${esc(lead.company)}</h3>
          <span class="cmx-lead-meta">${[esc(lead.sector||""), esc(lead.stage||""), esc(lead.city||"")].filter(Boolean).join(" · ")} ${round} ${amount}</span>
        </div>
        ${meta ? `<div class="cmx-lead-source">${meta}</div>` : ""}
        <div class="cmx-lead-bundle">
          <span class="cmx-lead-bundle-label">Auto-analysed bundle</span>
          <span class="cmx-lead-bundle-value">${esc(lead.est_bundle || "—")}</span>
        </div>
      </div>
      <div class="cmx-lead-side">
        <div class="cmx-lead-gwp-label">Estimated annual GWP</div>
        <div class="cmx-lead-gwp">${fmtInrRange(lead.est_gwp_low_inr, lead.est_gwp_high_inr)}</div>
        ${claimed
          ? `<div class="cmx-lead-claimed">✓ Claimed${lead.claimed_by ? ` · ${esc(lead.claimed_by)}` : ""}</div>`
          : `<button type="button" class="btn-primary cmx-lead-claim" data-claim="${esc(lead.lead_id)}">Claim lead</button>`}
      </div>
    </article>`;
}

async function claimFundingLead(leadId) {
  if (!leadId) return;
  const rmEmail = (state?.profile?.rm_email) || COMMERCE_DEFAULT_RM;
  const card = document.querySelector(`[data-lead="${leadId}"]`);
  const btn = card?.querySelector("[data-claim]");
  if (btn) { btn.disabled = true; btn.textContent = "Claiming…"; }
  let data;
  try {
    const res = await fetch("/api/commerce/funding", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ action: "claim", lead_id: leadId, rm_email: rmEmail }),
    });
    data = await res.json();
  } catch (e) {
    if (btn) { btn.disabled = false; btn.textContent = "Claim lead"; }
    alert("Claim failed: " + e);
    return;
  }
  if (!data.ok) {
    if (btn) { btn.disabled = false; btn.textContent = "Claim lead"; }
    alert(data.error || "Claim failed");
    return;
  }
  // Optimistically update local state then re-render the card row.
  const lead = _cmxState.leads.find(l => l.lead_id === leadId);
  if (lead) {
    lead.status = "claimed";
    lead.claimed_by = rmEmail;
    lead.account_id = data.account_id;
    renderFundingCards();
  }
}

/* ── Import CSV modal ────────────────────────────────────────── */
function openFundingImportModal() {
  if (document.getElementById("cmx-import-modal")) return;
  const overlay = document.createElement("div");
  overlay.id = "cmx-import-modal";
  overlay.className = "cmx-modal-overlay";
  overlay.innerHTML = `
    <div class="cmx-modal" role="dialog" aria-modal="true" aria-labelledby="cmx-import-title">
      <header class="cmx-modal-head">
        <h2 id="cmx-import-title">Import funding CSV</h2>
        <button type="button" class="cmx-modal-x" aria-label="Close">×</button>
      </header>
      <div class="cmx-modal-body">
        <p class="cmx-modal-hint">Required columns: <code>company, city, sector, stage, amount_inr, round, source, announced_on</code>. Each row is auto-analysed and valued with an indicative GWP range.</p>
        <textarea class="cmx-modal-textarea" id="cmx-import-textarea" placeholder="company,city,sector,stage,amount_inr,round,source,announced_on
Acme HealthTech,Bengaluru,HealthTech,Series A,450000000,Series A,VCCircle,2026-05-22
"></textarea>
        <div class="cmx-modal-or">— or —</div>
        <label class="cmx-modal-file">
          <input type="file" id="cmx-import-file" accept=".csv,text/csv" />
          <span>Choose a .csv file</span>
        </label>
        <div class="cmx-modal-status" id="cmx-import-status"></div>
      </div>
      <footer class="cmx-modal-foot">
        <button type="button" class="btn-ghost" data-close>Cancel</button>
        <button type="button" class="btn-primary" id="cmx-import-go">Ingest leads</button>
      </footer>
    </div>`;
  document.body.appendChild(overlay);
  overlay.querySelector(".cmx-modal-x").addEventListener("click", closeFundingImportModal);
  overlay.querySelector("[data-close]").addEventListener("click", closeFundingImportModal);
  overlay.addEventListener("click", e => { if (e.target === overlay) closeFundingImportModal(); });
  document.getElementById("cmx-import-file").addEventListener("change", async e => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const text = await file.text();
    document.getElementById("cmx-import-textarea").value = text;
  });
  document.getElementById("cmx-import-go").addEventListener("click", submitFundingImport);
}

function closeFundingImportModal() {
  const node = document.getElementById("cmx-import-modal");
  if (node) node.remove();
}

async function submitFundingImport() {
  const status = document.getElementById("cmx-import-status");
  const csv = (document.getElementById("cmx-import-textarea").value || "").trim();
  if (!csv) { if (status) status.textContent = "Paste CSV content or choose a file first."; return; }
  if (status) status.textContent = "Ingesting + auto-analysing (this can take a few seconds per row)…";
  let data;
  try {
    const res = await fetch("/api/commerce/funding", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ action: "import", csv }),
    });
    data = await res.json();
  } catch (e) {
    if (status) status.textContent = "Ingest failed: " + e;
    return;
  }
  if (data.error) {
    if (status) status.textContent = "Ingest failed: " + data.error;
    return;
  }
  const sumLo = (data.leads || []).reduce((a, x) => a + (x.est_gwp_low_inr || 0), 0);
  const sumHi = (data.leads || []).reduce((a, x) => a + (x.est_gwp_high_inr || 0), 0);
  if (status) status.textContent = `Ingested ${data.ingested} lead${data.ingested === 1 ? "" : "s"} · ${fmtInrRange(sumLo, sumHi)} surfaced GWP.`;
  setTimeout(() => {
    closeFundingImportModal();
    refreshFundingFeed();
  }, 1200);
}

/* Expose for inline onclick handlers used above */
window.enterCommerceMode = enterCommerceMode;
window.openFundingImportModal = openFundingImportModal;

/* ── F4 Renewals (alerts queue) ───────────────────────────── */
const _ALERT_BADGE = {
  renewal:      { label: "Renewal",      cls: "alert-badge-blue"  },
  upsell:       { label: "Upsell",       cls: "alert-badge-blue"  },
  at_risk:      { label: "At risk",      cls: "alert-badge-amber" },
  coverage_gap: { label: "Coverage gap", cls: "alert-badge-amber" },
};

async function renderRenewals() {
  const target = $("cmx-content");
  if (!target) return;
  target.innerHTML = `
    <header class="cmx-feed-head">
      <div>
        <div class="cmx-eyebrow">Alerts queue</div>
        <h1 class="cmx-headline">Renewals & upsell</h1>
        <p class="cmx-sub">Sorted by delta-GWP descending. Money first — the SVP's instinct.</p>
      </div>
      <div class="cmx-feed-actions">
        <button type="button" class="btn-ghost" id="renew-sweep">Re-evaluate all</button>
      </div>
    </header>
    <div class="renew-summary" id="renew-summary"></div>
    <div class="renew-list" id="renew-list"><div class="cmx-skeleton">Loading…</div></div>
    <p class="cmx-disclaimer" id="renew-disclaimer">Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.</p>`;
  const sweepBtn = $("renew-sweep");
  if (sweepBtn) sweepBtn.addEventListener("click", sweepAlerts);
  await refreshRenewals();
}

async function refreshRenewals() {
  let data;
  try {
    const res = await fetch("/api/commerce/alerts?status=open");
    data = await res.json();
  } catch (e) {
    const list = $("renew-list");
    if (list) list.innerHTML = `<div class="cmx-error">Failed to load: ${esc(String(e))}</div>`;
    return;
  }
  _renderRenewSummary(data.summary || {});
  _renderRenewList(data.alerts || []);
  const d = $("renew-disclaimer");
  if (d && data.disclaimer) d.textContent = data.disclaimer;
}

function _renderRenewSummary(s) {
  const node = $("renew-summary");
  if (!node) return;
  const atRiskRange = (s.at_risk_gwp_low_inr || s.at_risk_gwp_high_inr)
    ? fmtInrRange(s.at_risk_gwp_low_inr, s.at_risk_gwp_high_inr) : "—";
  const renewRange = (s.renewal_gwp_low_inr || s.renewal_gwp_high_inr)
    ? fmtInrRange(s.renewal_gwp_low_inr, s.renewal_gwp_high_inr) : "—";
  node.innerHTML = `
    <div class="renew-tile renew-tile-warn">
      <div class="perf-tile-label">⚠ GWP at risk ≤60d</div>
      <div class="perf-tile-value">${atRiskRange}</div>
      <div class="perf-tile-n">${s.at_risk_count || 0} account${(s.at_risk_count || 0) === 1 ? "" : "s"}</div>
    </div>
    <div class="renew-tile">
      <div class="perf-tile-label">Renewals due ≤60d</div>
      <div class="perf-tile-value">${renewRange}</div>
      <div class="perf-tile-n">${s.renewal_count || 0} account${(s.renewal_count || 0) === 1 ? "" : "s"}</div>
    </div>`;
}

function _renderRenewList(alerts) {
  const node = $("renew-list");
  if (!node) return;
  if (alerts.length === 0) {
    node.innerHTML = `
      <div class="cmx-empty-card">
        <div class="cmx-empty-eyebrow">No open alerts</div>
        <p>No renewal, upsell, at-risk, or coverage-gap alerts in scope.</p>
        <button type="button" class="btn-primary" onclick="sweepAlerts()">Re-evaluate all accounts</button>
      </div>`;
    return;
  }
  node.innerHTML = alerts.map(a => {
    const badge = _ALERT_BADGE[a.type] || { label: a.type, cls: "" };
    const delta = a.delta_gwp_high_inr || a.delta_gwp_low_inr || 0;
    const signed = delta < 0 ? "− " : "";
    const lo = Math.abs(a.delta_gwp_low_inr || 0);
    const hi = Math.abs(a.delta_gwp_high_inr || 0);
    const rangeStr = fmtInrRange(Math.min(lo, hi), Math.max(lo, hi));
    return `
      <article class="cmx-lead-card alert-card" data-alert="${esc(a.alert_id)}">
        <div class="cmx-lead-main">
          <div class="cmx-lead-row1">
            <span class="alert-badge ${badge.cls}">${esc(badge.label)}</span>
            <h3 class="cmx-lead-name">${esc(a.account_name || a.account_id)}</h3>
            <span class="cmx-lead-meta">${[esc(a.sector || ""), esc(a.stage || ""), esc(a.city || "")].filter(Boolean).join(" · ")}</span>
          </div>
          <div class="alert-reason">${esc(a.reason)}</div>
          ${a.rm_email ? `<div class="cmx-lead-source">RM · ${esc(a.rm_email)}</div>` : ""}
        </div>
        <div class="cmx-lead-side">
          <div class="cmx-lead-gwp-label">${delta < 0 ? "GWP at risk" : "Delta GWP"}</div>
          <div class="cmx-lead-gwp ${delta < 0 ? "alert-delta-neg" : ""}">${signed}${rangeStr}</div>
          <div class="alert-actions">
            <button type="button" class="btn-ghost btn-sm" data-dismiss="${esc(a.alert_id)}">Dismiss</button>
          </div>
        </div>
      </article>`;
  }).join("");
  node.querySelectorAll("[data-dismiss]").forEach(btn => {
    btn.addEventListener("click", () => dismissAlert(btn.getAttribute("data-dismiss")));
  });
}

async function dismissAlert(alertId) {
  if (!alertId) return;
  const rmEmail = (state?.profile?.rm_email) || COMMERCE_DEFAULT_RM;
  try {
    await fetch("/api/commerce/alerts", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ action: "dismiss", alert_id: alertId, rm_email: rmEmail }),
    });
  } catch (e) {
    alert("Dismiss failed: " + e);
    return;
  }
  refreshRenewals();
}

async function sweepAlerts() {
  const btn = $("renew-sweep");
  if (btn) { btn.disabled = true; btn.textContent = "Evaluating…"; }
  try {
    const res = await fetch("/api/commerce/alerts", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ action: "sweep" }),
    });
    const data = await res.json();
    if (btn) { btn.textContent = `Swept ${data.swept || 0} · ${data.created || 0} new`; }
  } catch (e) {
    if (btn) { btn.textContent = "Sweep failed"; }
  }
  setTimeout(() => {
    if (btn) { btn.disabled = false; btn.textContent = "Re-evaluate all"; }
    refreshRenewals();
  }, 1500);
}

window.sweepAlerts = sweepAlerts;

/* ─── F3 PIPELINE ────────────────────────────────────────────── */

const _PIPELINE_STAGES = [
  { id: "prospect",  label: "Prospect" },
  { id: "analysed",  label: "Analysed" },
  { id: "quoted",    label: "Quoted" },
  { id: "proposal",  label: "Proposal" },
  { id: "converted", label: "Converted" },
];

const _NEXT_STAGE = {
  prospect:  "analysed",
  analysed:  "quoted",
  quoted:    "proposal",
  proposal:  "converted",
};

let _pipelineActiveStage = "prospect";
let _cmxPipelineData = null;

async function renderPipeline() {
  const target = $("cmx-content");
  if (!target) return;
  target.innerHTML = `
    <header class="cmx-feed-head">
      <div>
        <div class="cmx-eyebrow">Deal pipeline</div>
        <h1 class="cmx-headline">Pipeline</h1>
        <p class="cmx-sub">Move accounts through stages as deals progress.</p>
      </div>
    </header>
    <div class="pipe-summary" id="pipe-summary"></div>
    <nav class="pipe-tabs" id="pipe-tabs" role="tablist"></nav>
    <div class="pipe-list" id="pipe-list"><div class="cmx-skeleton">Loading…</div></div>
    <p class="cmx-disclaimer">Indicative only under IRDAI File-and-Use detariffed regime. Not a bindable quote.</p>`;
  await refreshPipeline();
}

async function refreshPipeline() {
  let data;
  try {
    const res = await fetch("/api/commerce/pipeline");
    data = await res.json();
  } catch (e) {
    const list = $("pipe-list");
    if (list) list.innerHTML = `<div class="cmx-error">Failed to load: ${esc(String(e))}</div>`;
    return;
  }
  _cmxPipelineData = data;
  _renderPipeSummary(data.summary || {});
  _renderPipeTabs(data.accounts || [], data.summary || {});
  _renderPipeList(data.accounts || []);
}

function _renderPipeSummary(s) {
  const node = $("pipe-summary");
  if (!node) return;
  const counts = s.counts || {};
  const active = _PIPELINE_STAGES.reduce((n, st) => n + (counts[st.id] || 0), 0);
  const gwpLo  = s.pipeline_gwp_low_inr  || 0;
  const gwpHi  = s.pipeline_gwp_high_inr || 0;
  const gwpStr = (gwpLo || gwpHi) ? fmtInrRange(gwpLo, gwpHi) : "—";
  node.innerHTML = `
    <div class="pipe-sum-tile">
      <div class="perf-tile-label">Active accounts</div>
      <div class="perf-tile-value">${active}</div>
    </div>
    <div class="pipe-sum-tile">
      <div class="perf-tile-label">Pipeline GWP</div>
      <div class="perf-tile-value">${gwpStr}</div>
      <div class="perf-tile-n">Indicative range</div>
    </div>`;
}

function _renderPipeTabs(accounts, summary) {
  const tabs = $("pipe-tabs");
  if (!tabs) return;
  const counts = summary.counts || {};
  tabs.innerHTML = _PIPELINE_STAGES.map(st => {
    const n = counts[st.id] || 0;
    const active = st.id === _pipelineActiveStage ? " is-active" : "";
    return `<button type="button" class="pipe-tab${active}" data-stage="${esc(st.id)}" role="tab">
      ${esc(st.label)}<span class="pipe-tab-count">${n}</span>
    </button>`;
  }).join("");
  tabs.querySelectorAll(".pipe-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      _pipelineActiveStage = btn.getAttribute("data-stage");
      tabs.querySelectorAll(".pipe-tab").forEach(b => b.classList.remove("is-active"));
      btn.classList.add("is-active");
      _renderPipeList((_cmxPipelineData || {}).accounts || []);
    });
  });
}

function _renderPipeList(accounts) {
  const node = $("pipe-list");
  if (!node) return;
  const filtered = accounts.filter(a => a.stage === _pipelineActiveStage);
  if (filtered.length === 0) {
    const nextMsg = _pipelineActiveStage === "converted"
      ? "" : ` Move accounts here from <strong>${
        _PIPELINE_STAGES[_PIPELINE_STAGES.findIndex(s => s.id === _pipelineActiveStage) - 1]?.label || "previous"
      }</strong>.`;
    node.innerHTML = `
      <div class="cmx-empty-card">
        <div class="cmx-empty-eyebrow">No accounts</div>
        <p>No accounts in the <strong>${_pipelineActiveStage}</strong> stage.${nextMsg}</p>
      </div>`;
    return;
  }
  node.innerHTML = filtered.map(a => {
    const gwpStr = (a.gwp_low_inr || a.gwp_high_inr)
      ? fmtInrRange(a.gwp_low_inr || 0, a.gwp_high_inr || 0) : "—";
    const nextStage = _NEXT_STAGE[a.stage];
    const nextLabel = nextStage
      ? _PIPELINE_STAGES.find(s => s.id === nextStage)?.label : null;
    return `
      <article class="cmx-lead-card pipe-card" data-account="${esc(a.account_id)}">
        <div class="cmx-lead-main">
          <div class="cmx-lead-row1">
            <h3 class="cmx-lead-name">${esc(a.name || a.account_id)}</h3>
            <span class="cmx-lead-meta">${[a.sector, a.funding_stage, a.city].filter(Boolean).map(esc).join(" · ")}</span>
          </div>
          ${a.rm_email ? `<div class="cmx-lead-source">RM · ${esc(a.rm_email)}</div>` : ""}
        </div>
        <div class="cmx-lead-side">
          <div class="cmx-lead-gwp-label">Est. GWP</div>
          <div class="cmx-lead-gwp">${gwpStr}</div>
          <div class="pipe-card-actions">
            ${nextLabel ? `<button type="button" class="btn-primary btn-sm pipe-advance" data-account="${esc(a.account_id)}" data-to="${esc(nextStage)}">→ ${esc(nextLabel)}</button>` : `<span class="pipe-converted-badge">Converted</span>`}
            ${a.stage !== "converted" ? `<button type="button" class="btn-ghost btn-sm pipe-lose" data-account="${esc(a.account_id)}">Mark lost</button>` : ""}
          </div>
        </div>
      </article>`;
  }).join("");
  node.querySelectorAll(".pipe-advance").forEach(btn => {
    btn.addEventListener("click", () => movePipelineStage(
      btn.getAttribute("data-account"), btn.getAttribute("data-to")
    ));
  });
  node.querySelectorAll(".pipe-lose").forEach(btn => {
    btn.addEventListener("click", () => movePipelineStage(
      btn.getAttribute("data-account"), "lost"
    ));
  });
}

async function movePipelineStage(accountId, toStage) {
  const rmEmail = (state?.profile?.rm_email) || COMMERCE_DEFAULT_RM;
  try {
    const res = await fetch("/api/commerce/pipeline", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "move_stage", account_id: accountId, to_stage: toStage, rm_email: rmEmail }),
    });
    const data = await res.json();
    if (!data.ok) { alert("Move failed: " + (data.error || "unknown")); return; }
  } catch (e) {
    alert("Move failed: " + e); return;
  }
  if (toStage === "lost") _pipelineActiveStage = "prospect";
  refreshPipeline();
}

/* ─── KICK OFF ───────────────────────────────────────────────── */
window.renderForm = renderForm;
init();

/* ─── FOUNDER SUMMARY PDF ────────────────────────────────────── */
window.openSummaryPDF = () => {
  const result = window.__result;
  if (!result) return;
  const html = buildSummaryHTML(result);
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url  = URL.createObjectURL(blob);
  const win  = window.open(url, "_blank");
  if (win) win.focus();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
};

function buildSummaryHTML(result) {
  const bundle   = result.bundle_match || {};
  const rm       = result.rm || {};
  const profile  = result.profile || {};
  const bundleQ  = result.bundle_only_pricing_quote;
  const fullQ    = result.pricing_engine_quote;
  const triggers = (result.display_regulatory_triggers || result.regulatory_triggers_fired || []).slice(0, 6);
  const roadmap  = [...(result.coverage_roadmap || [])].sort((a, b) => {
    const o = ["Pre-seed","Seed","Series A","Series B","Series B+","Growth","Late Stage / Pre-IPO"];
    return (o.indexOf(a.stage||"") + 1 || 99) - (o.indexOf(b.stage||"") + 1 || 99);
  });

  const rmName   = rm.RM_NAME   || "";
  const rmPhone  = rm.RM_PHONE  || "";
  const rmEmail  = rm.RM_EMAIL  || "";
  const rmOffice = rm.RM_OFFICE || "ICICI Lombard General Insurance";

  const mandatory = bundle.mandatory_covers || [];
  const optional  = bundle.optional_covers  || [];

  const coverDesc = {
    cyber_liability:              "Covers data breaches, ransomware, regulatory fines, and breach notification costs.",
    dno_liability:                "Protects directors and officers personally against investor and regulatory claims.",
    professional_indemnity:       "Covers client claims arising from errors, omissions, or technology failures in your product.",
    crime_fidelity:               "Covers financial loss from employee fraud, theft, or unauthorised transactions.",
    employment_practices:         "Covers wrongful termination, discrimination, and harassment claims from employees.",
    product_liability:            "Covers bodily injury and property damage claims arising from product defects.",
    comprehensive_general_liability: "Covers third-party bodily injury and property damage from your operations.",
    public_liability:             "Covers third-party injury or damage claims from visitors or public interactions.",
    property_fire:                "Covers physical assets against fire, explosion, and allied perils.",
    property_all_risk:            "Covers physical assets against all accidental damage including theft and natural perils.",
    business_interruption:        "Covers lost revenue and fixed costs while your operations are disrupted.",
    machinery_breakdown:          "Covers repair and replacement costs for mechanical and electrical equipment failure.",
    electronic_equipment:         "Covers lab and office electronics against breakdown, accidental damage, and theft.",
    group_health:                 "Provides hospitalisation and medical coverage for your employees and their dependants.",
    employees_comp:               "Statutory cover for employee injuries or illness arising in the course of employment.",
    marine_transit:               "Covers goods and equipment in transit against loss, damage, and theft.",
    drone_rpas:                   "Mandatory cover for third-party liability from drone operations under DGCA Rule 44.",
    healthcare_pi:                "Covers professional negligence claims against healthcare practitioners and platforms.",
    financial_services_pi:        "Covers claims from financial mis-advice, settlement errors, or payment processing failures.",
  };

  const hasPremium = isQuoted(bundleQ) || isQuoted(fullQ);
  const bundlePremium = bundleQ?.gross_premium_lakh;
  const fullPremium   = fullQ?.gross_premium_lakh;

  const SIGNAL_PLAIN = {
    handles_pii:         "Your company handles personal data",
    rbi_licensed:        "You hold an RBI licence",
    sebi_regulated:      "You are SEBI-regulated",
    healthtech:          "You process health data",
    fintech:             "You operate in financial services",
    has_investors:       "You have institutional investors",
    ai_in_product:       "Your product uses AI",
    b2b_contracts:       "You have B2B contracts",
    physical_assets:     "You own physical assets",
    gig_workers:         "You employ gig or contract workers",
    export_operations:   "You operate internationally",
    cert_in_obligations: "You have CERT-In reporting obligations",
  };

  const coverRows = (keys, label) => keys.map(k => `
    <tr>
      <td style="padding:10px 16px 10px 0;border-bottom:1px solid #f0f0f0;vertical-align:top;">
        <div style="font-weight:700;font-size:13px;color:#111;">${esc(labelize(k))}</div>
        <div style="font-size:12px;color:#666;margin-top:3px;line-height:1.5;">${esc(coverDesc[k] || "")}</div>
      </td>
      <td style="padding:10px 0 10px 8px;border-bottom:1px solid #f0f0f0;vertical-align:top;white-space:nowrap;">
        <span style="display:inline-block;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;padding:2px 8px;border-radius:4px;${label==="Mandatory"?"background:#fde8e8;color:#AD1E23;border:1px solid rgba(173,30,35,.2)":"background:#f0f4ff;color:#3949ab;border:1px solid #c5cdf0;"}">${label}</span>
      </td>
    </tr>`).join("");

  const claimCards = (() => {
    const sector = profile.sector || "";
    const covers = mandatory.filter(k => CLAIMS_SCENARIOS[k]).slice(0, 3);
    return covers.map(k => {
      const bank = CLAIMS_SCENARIOS[k];
      const s = bank[sector] || bank.default;
      if (!s) return "";
      return `
      <div style="border:1px solid #e8e8e8;border-radius:10px;padding:16px;margin-bottom:12px;">
        <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#AD1E23;margin-bottom:8px;">${esc(labelize(k))}</div>
        <div style="font-size:14px;font-weight:700;color:#111;margin-bottom:10px;line-height:1.4;">${esc(s.event)}</div>
        <div style="background:#fff5f5;border:1px solid rgba(173,30,35,.15);border-radius:6px;padding:8px 12px;display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
          <span style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.04em;color:#888;">${esc(s.exposure_label)}</span>
          <span style="font-size:16px;font-weight:800;color:#AD1E23;font-variant-numeric:tabular-nums;">${esc(s.exposure)}</span>
        </div>
        <ul style="margin:0;padding-left:16px;font-size:12px;color:#555;line-height:1.6;">
          ${s.costs.map(c => `<li style="margin-bottom:4px;">${esc(c)}</li>`).join("")}
        </ul>
        <div style="border-top:1px solid #f0f0f0;margin-top:10px;padding-top:10px;">
          <div style="font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#2e7d32;margin-bottom:4px;">With cover</div>
          <div style="font-size:12px;color:#555;line-height:1.5;">${esc(s.with_cover)}</div>
        </div>
      </div>`;
    }).join("");
  })();

  const triggerRows = triggers.map(t => `
    <tr>
      <td style="padding:8px 12px 8px 0;border-bottom:1px solid #f0f0f0;font-size:13px;color:#555;vertical-align:top;">${esc(SIGNAL_PLAIN[t.signal] || t.signal || "")}</td>
      <td style="padding:8px 12px 8px 0;border-bottom:1px solid #f0f0f0;font-size:13px;font-weight:600;color:#111;vertical-align:top;">${esc(t.product || "")}</td>
      <td style="padding:8px 0 8px 0;border-bottom:1px solid #f0f0f0;font-size:12px;color:#888;vertical-align:top;">${esc(t.regulation || t.reg || "")}</td>
    </tr>`).join("");

  const roadmapSteps = roadmap.map((p, i) => `
    <div style="display:flex;align-items:flex-start;gap:14px;margin-bottom:${i < roadmap.length - 1 ? "16" : "0"}px;">
      <div style="width:28px;height:28px;border-radius:50%;background:#AD1E23;color:white;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0;">${i + 1}</div>
      <div style="padding-top:4px;">
        <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#999;">${esc(p.stage || "")}</div>
        <div style="font-size:14px;font-weight:600;color:#111;">${esc(p.bundle || p.recommendation || "")}</div>
      </div>
    </div>`).join("");

  const today = new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" });
  const companyName = profile.startup_name || profile.company_name || "Your company";

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Insurance summary — ${esc(companyName)}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; background: #f5f5f5; color: #111; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  .page { max-width: 780px; margin: 32px auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 24px rgba(0,0,0,.1); }
  @media print {
    body { background: white; }
    .page { margin: 0; border-radius: 0; box-shadow: none; max-width: 100%; }
    .no-print { display: none !important; }
    h2 { page-break-after: avoid; }
    .section { page-break-inside: avoid; }
  }
  .header { background: #AD1E23; padding: 32px 40px; color: white; }
  .header-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
  .logo-mark { font-size: 22px; font-weight: 800; letter-spacing: -.5px; }
  .logo-sub { font-size: 10px; font-weight: 600; letter-spacing: .14em; text-transform: uppercase; opacity: .7; margin-top: 3px; }
  .date-tag { font-size: 11px; opacity: .7; }
  .header-title { font-size: 26px; font-weight: 800; line-height: 1.2; margin-bottom: 6px; }
  .header-sub { font-size: 14px; opacity: .8; }
  .section { padding: 28px 40px; border-bottom: 1px solid #f0f0f0; }
  .section:last-child { border-bottom: none; }
  h2 { font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: .06em; color: #AD1E23; margin-bottom: 14px; }
  .bundle-name { font-size: 22px; font-weight: 800; color: #111; margin-bottom: 4px; }
  .bundle-desc { font-size: 14px; color: #555; line-height: 1.6; }
  .fit-badge { display: inline-block; background: #fde8e8; color: #AD1E23; border: 1px solid rgba(173,30,35,.2); border-radius: 20px; font-size: 12px; font-weight: 700; padding: 3px 12px; margin-bottom: 12px; }
  .premium-row { display: flex; gap: 16px; margin-top: 16px; flex-wrap: wrap; }
  .premium-box { flex: 1; min-width: 160px; background: #fafafa; border: 1px solid #e8e8e8; border-radius: 8px; padding: 14px 16px; }
  .premium-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .04em; color: #999; margin-bottom: 4px; }
  .premium-val { font-size: 20px; font-weight: 800; color: #AD1E23; font-variant-numeric: tabular-nums; }
  .premium-note { font-size: 11px; color: #999; margin-top: 3px; }
  table { width: 100%; border-collapse: collapse; }
  .footer { background: #fafafa; padding: 24px 40px; display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; flex-wrap: wrap; }
  .rm-name { font-size: 15px; font-weight: 700; color: #111; margin-bottom: 4px; }
  .rm-detail { font-size: 12px; color: #666; margin-bottom: 2px; }
  .rm-office { font-size: 11px; color: #999; margin-top: 4px; }
  .disclaimer { font-size: 10px; color: #bbb; line-height: 1.6; max-width: 340px; }
  .print-btn { display: inline-flex; align-items: center; gap: 8px; background: #AD1E23; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-size: 13px; font-weight: 700; cursor: pointer; margin: 16px 40px; }
  .print-btn:hover { background: #8b1010; }
</style>
</head>
<body>
<div class="no-print" style="text-align:center;padding:20px 0 0;">
  <button class="print-btn" onclick="window.print()">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
    Print / Save as PDF
  </button>
</div>

<div class="page">

  <!-- Header -->
  <div class="header">
    <div class="header-top">
      <div>
        <div class="logo-mark">ICICI Lombard</div>
        <div class="logo-sub">General Insurance · Commercial Lines</div>
      </div>
      <div class="date-tag">${esc(today)}</div>
    </div>
    <div class="header-title">Insurance recommendation for ${esc(companyName)}</div>
    <div class="header-sub">${esc(profile.sector || "")}${profile.funding_stage ? " · " + profile.funding_stage : ""}${profile.team_size ? " · " + profile.team_size + " employees" : ""}</div>
  </div>

  <!-- Recommended bundle -->
  <div class="section">
    <h2>Recommended bundle</h2>
    ${bundle.fit_pct ? `<div class="fit-badge">${bundle.fit_pct}% profile fit</div>` : ""}
    <div class="bundle-name">${esc(bundle.name || "")}</div>
    <div class="bundle-desc">${esc(bundle.description || "")}</div>
    ${hasPremium ? `
    <div class="premium-row">
      ${bundlePremium ? `<div class="premium-box"><div class="premium-label">Bundle price</div><div class="premium-val">INR ${esc(String(bundlePremium))}L</div><div class="premium-note">Incl. 18% GST</div></div>` : ""}
      ${fullPremium  ? `<div class="premium-box"><div class="premium-label">Full cover price</div><div class="premium-val">INR ${esc(String(fullPremium))}L</div><div class="premium-note">All recommended covers · incl. GST</div></div>` : ""}
      <div class="premium-box"><div class="premium-label">Note</div><div style="font-size:12px;color:#666;line-height:1.5;margin-top:4px;">Indicative estimate only. Final premium subject to underwriting.</div></div>
    </div>` : `<p style="font-size:13px;color:#999;margin-top:12px;">Premium estimate not generated. Request a quote from your RM.</p>`}
  </div>

  <!-- What's covered -->
  ${mandatory.length || optional.length ? `
  <div class="section">
    <h2>What's covered</h2>
    <table>
      <tbody>
        ${coverRows(mandatory, "Mandatory")}
        ${coverRows(optional.slice(0, 4), "Recommended")}
      </tbody>
    </table>
  </div>` : ""}

  <!-- Why these covers were flagged -->
  ${triggerRows ? `
  <div class="section">
    <h2>Why these covers apply to you</h2>
    <p style="font-size:13px;color:#666;margin-bottom:14px;line-height:1.6;">These are not general best-practice recommendations — each cover was flagged because a specific regulation or risk profile applies to your company.</p>
    <table>
      <thead>
        <tr>
          <th style="font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#999;font-weight:600;padding-bottom:8px;text-align:left;">Reason</th>
          <th style="font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#999;font-weight:600;padding-bottom:8px;text-align:left;">Cover</th>
          <th style="font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:#999;font-weight:600;padding-bottom:8px;text-align:left;">Regulation</th>
        </tr>
      </thead>
      <tbody>${triggerRows}</tbody>
    </table>
  </div>` : ""}

  <!-- Claim scenarios -->
  ${claimCards ? `
  <div class="section">
    <h2>What happens without these covers</h2>
    <p style="font-size:13px;color:#666;margin-bottom:16px;line-height:1.6;">Real scenarios from Indian startups at your stage and sector.</p>
    ${claimCards}
  </div>` : ""}

  <!-- Coverage roadmap -->
  ${roadmapSteps ? `
  <div class="section">
    <h2>Your coverage roadmap</h2>
    <p style="font-size:13px;color:#666;margin-bottom:16px;line-height:1.6;">As you raise and scale, your risk profile changes. Here is the recommended bundle progression.</p>
    ${roadmapSteps}
  </div>` : ""}

  <!-- Footer / RM contact -->
  <div class="footer">
    <div>
      <div class="rm-name">${esc(rmName)}</div>
      ${rmPhone ? `<div class="rm-detail">📞 ${esc(rmPhone)}</div>` : ""}
      ${rmEmail ? `<div class="rm-detail">✉ ${esc(rmEmail)}</div>` : ""}
      <div class="rm-office">${esc(rmOffice)}</div>
    </div>
    <div class="disclaimer">
      This document is an indicative recommendation generated by SPARC, ICICI Lombard's startup risk classification engine. All premiums shown are estimates subject to underwriting review. Coverage is subject to policy terms and conditions. For a firm quotation, please contact your RM.
    </div>
  </div>

</div>
</body>
</html>`;
}

