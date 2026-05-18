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
    const parsed = extractProfileJson(input?.value || "");
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
  updateProfileImportStatus(`Loaded database record for ${profile.startup_name}. Review inferred fields before quoting.`, "success");
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
            <button type="button" class="btn btn-ghost" onclick="loadCompanyProfile('${esc(item.name)}', false)">Load</button>
            <button type="button" class="btn btn-primary" onclick="loadCompanyProfile('${esc(item.name)}', true)">Analyse</button>
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
      <button class="company-profile-option" type="button" data-company-name="${esc(item.name)}" onclick="loadCompanyProfileFromOption(this, true)">
        <span>
          <strong>${esc(item.name)}</strong>
          <em>${esc(item.sector)} · ${esc(item.funding_stage)} · ${esc(item.team_size)} people</em>
        </span>
        <b>Analyse</b>
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

window.loadCompanyProfileFromOption = (button, analyse = true) => {
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
      </header>
      <div id="main-content"></div>
    </div>`;
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

function renderRoleSelection() {
  state.view = "role";
  $("main-content").innerHTML = `
    <main class="role-shell">
      <section class="role-panel">
        <div class="role-copy">
          <div class="intake-eyebrow">Choose experience</div>
          <h1>Start with the input view that fits your role</h1>
          <p>Select the customer route for a short business-friendly recommendation. Select the underwriter route for the full SPARC intake and risk report.</p>
        </div>
        <div class="role-options">
          <button class="role-card role-card-primary" type="button" id="customer-role-btn">
            <span class="role-card-kicker">Customer End Input</span>
            <strong>Quick recommendation</strong>
            <span>Short profile questions, simple language, and an RM-ready recommendation screen.</span>
          </button>
          <button class="role-card" type="button" id="underwriter-role-btn">
            <span class="role-card-kicker">Underwriter End Input</span>
            <strong>Full underwriting analysis</strong>
            <span>Use the existing detailed intake, scoring model, pricing views, and report output.</span>
          </button>
        </div>
      </section>
    </main>`;

  $("customer-role-btn").onclick = () => {
    if (!state.customerProfile?.industry) resetCustomerProfile();
    renderCustomerInput();
  };
  $("underwriter-role-btn").onclick = () => renderForm();
}

function renderCustomerInput() {
  state.view = "customer";
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
          <h2>Talk with your RM</h2>
          <p>${esc(customerNudge(result))}</p>
        </div>
        <button class="btn btn-primary btn-lg" type="button">Talk with RM</button>
      </section>

      <div class="customer-result-actions">
        <button class="btn btn-ghost" type="button" onclick="renderRoleSelection()">Back to role selection</button>
        <button class="btn btn-ghost" type="button" onclick="renderForm()">Open underwriter view</button>
      </div>
    </main>`;

  state.profile = structuredClone(p);
  window.__customerResult = result;
}

function renderForm() {
  state.view = "underwriter";
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

function renderResults(result) {
  result = normalizeGroupSafeguardCompanion(result);
  state.profile = structuredClone(result.profile || state.profile);
  const p = result.profile;

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
          </div>
        </div>
        <div class="hero-actions">
          <button class="btn-hero-primary" onclick="downloadReport(window.__result)">Download report</button>
          <button class="btn-hero-ghost" onclick="renderForm()">Edit inputs</button>
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
        ${renderKPI("Premium range", result.premium_summary ? `INR ${result.premium_summary.min_lakh}-${result.premium_summary.max_lakh}L` : "N/A")}
        ${renderKPI("Risk clusters", Object.keys(result.clusters||{}).length + " analysed")}
      </div>

      <!-- ── TAB: Bundle ── -->
      <div class="tab-panel" id="tab-bundle">
        <div class="result-section">
          <div class="result-section-head">
            <div class="result-section-bar"></div>
            <div class="result-section-title">Bundle recommendation</div>
            <button class="pdf-trigger-btn" type="button" onclick="openSummaryPDF()" title="Download founder summary">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Download summary
            </button>
          </div>
          ${renderGenAIStatus(result)}
          ${renderBundleHero(result.bundle_match, result.recommendations, result.why_it_matters)}
          ${renderBundleAlternatives(result.bundle_alternatives)}
          ${renderV2Insights(result)}
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
        ${renderOutreach(result.outreach_prompts, result.outreach_source, result.outreach_error)}
      </div>

      <!-- ── TAB: Estimated Quote ── -->
      <div class="tab-panel" id="tab-quote" style="display:none">
        ${renderMethodologyModal()}
        <div style="display:flex;justify-content:flex-end;margin-bottom:12px;">
          <button class="hc-trigger-btn" type="button" onclick="toggleHowCalculated(true)">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
            How is this calculated?
          </button>
        </div>
        ${renderDualPricingPanel(result)}
        ${result.premium_summary ? `
        <div class="premium-card">
          <div class="premium-card-label">Total premium potential</div>
          <div class="premium-card-value">INR ${result.premium_summary.min_lakh} - ${result.premium_summary.max_lakh} lakhs</div>
          <div class="premium-card-note">Across ${result.premium_summary.count} products · ${esc(result.premium_footnote||"Indicative estimates only.")}</div>
        </div>` : ""}
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

  // Bind product row expand/collapse
  window.toggleProductRow = (i) => {
    const row = document.getElementById(`prow-${i}`);
    if (row) row.classList.toggle('expanded');
  };

  // Bind refine
  bindRefine();
  bindPolicyWordingUpload();

  // Bind outreach copy buttons
  document.querySelectorAll("[data-copy]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await navigator.clipboard?.writeText(btn.dataset.copy || "");
      const orig = btn.textContent;
      btn.textContent = "Copied ✓";
      setTimeout(() => btn.textContent = orig, 1800);
    });
  });

  // Bind Send Email buttons
  document.querySelectorAll(".il-send-email-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const item = _outreachItems[btn.dataset.key] || {};
      openEmailModal(item.email_subject || "", item.email_body || "", item.email_html_data);
    });
  });

  // Draw radar — deferred so the canvas exists in DOM
  setTimeout(() => drawRadar("risk-radar", result.scores, { maxLabelLength: 16 }), 100);

  // Activate default tab
  showTab("bundle");
}

/* ─── TAB NAVIGATION ─────────────────────────────────────────── */
window.showTab = (id) => {
  document.querySelectorAll(".tab-panel").forEach(p => { p.style.display = "none"; });
  document.querySelectorAll(".snav-pill").forEach(p => p.classList.remove("snav-active"));
  const panel = document.getElementById("tab-" + id);
  if (panel) panel.style.display = "";
  const btn = document.getElementById("snav-" + id);
  if (btn) btn.classList.add("snav-active");
  // Redraw radar if switching to risk tab
  if (id === "risk" && window.__result) {
    setTimeout(() => drawRadar("risk-radar", window.__result.scores, { maxLabelLength: 16 }), 50);
  }
};

/* ─── METHODOLOGY PANEL ──────────────────────────────────────────── */
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
  return `
    <div class="kpi-card">
      <div class="kpi-label">${esc(label)}</div>
      <div class="kpi-value">${esc(String(value))}</div>
    </div>`;
}

function renderGenAIStatus(result) {
  const mode = result.recommendation_mode || "off";
  const source = result.genai_source || (result.genai_enabled ? "unknown" : "disabled");
  const enabled = result.genai_enabled === true;
  const err = result.genai_error;
  const diff = result.genai_shadow_diff || {};
  const genaiBundle = result.genai_bundle_match?.name || "none";
  const genaiProducts = (result.genai_recommendations || []).map(r => r.name || r.product_key).slice(0, 4);
  const statusClass = source === "gemini" ? "good" : source === "fallback" ? "warn" : "neutral";
  const statusText = source === "gemini"
    ? (mode === "primary" ? "GenAI primary reranker applied" : "GenAI shadow reranker ran")
    : source === "fallback"
      ? "Deterministic fallback served"
      : "GenAI recommendation disabled";

  return `
    <div class="genai-status-card ${statusClass}">
      <div class="genai-status-top">
        <div>
          <div class="genai-status-label">Recommendation engine</div>
          <div class="genai-status-title">${esc(statusText)}</div>
        </div>
        <div class="genai-status-pills">
          <span>mode: ${esc(mode)}</span>
          <span>source: ${esc(source)}</span>
          <span>${enabled ? "model enabled" : "model not used"}</span>
        </div>
      </div>
      ${err ? `<div class="genai-status-error">${esc(err)}</div>` : ""}
      ${source === "gemini" ? `
        <div class="genai-status-grid">
          <div><strong>GenAI bundle</strong><span>${esc(genaiBundle)}</span></div>
          <div><strong>GenAI product order</strong><span>${esc(genaiProducts.join(", ") || "not returned")}</span></div>
          <div><strong>Changed vs deterministic</strong><span>${diff.changed ? "Yes" : "No"}</span></div>
        </div>` : ""}
    </div>`;
}

function isQuoted(q) {
  return q?.covers_priced?.length > 0;
}

function renderPricePanel(quote, tagLabel, tagClass, subtitle) {
  if (!quote || !isQuoted(quote)) return "";
  const covers = quote.covers_priced || [];
  const flags  = quote.underwriter_referral_flags || [];
  return `
    <div class="pricing-card">
      <span class="pricing-panel-tag ${tagClass}">${esc(tagLabel)}</span>
      <div class="pricing-head">
        <div>
          <div class="pricing-title">INR ${esc(quote.gross_premium_lakh)} lakhs</div>
          <div class="premium-card-note">${esc(subtitle)} &nbsp;·&nbsp; incl. 18% GST</div>
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
            <div class="pricing-cover-name">${esc(c.cover_name || labelize(c.cover_key))}</div>
            <div class="pricing-cover-premium">INR ${esc(c.premium_lakh)}L</div>
            <div class="pricing-cover-basis">${esc(c.exposure_label || "")} | risk ${esc(c.average_risk_score ?? "n/a")}/100</div>
          </div>`).join("")}
      </div>
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
  const isCount = row.unit === "count";
  return `
    <div class="ls-row">
      <div class="ls-label-row">
        <span class="ls-label">${esc(row.label)}</span>
        <div class="ls-value-wrap">
          <input type="number" class="ls-num" id="qs-input-${esc(row.key)}"
            min="${range.min}" max="${range.max}" step="${range.step}"
            value="${esc(String(val))}"
            oninput="syncSlider('${esc(row.key)}', this.value)">
          <span class="ls-unit">${esc(row.unit || "Cr")}</span>
        </div>
      </div>
      <input type="range" class="ls-range" id="qs-slider-${esc(row.key)}"
        min="${range.min}" max="${range.max}" step="${range.step}"
        value="${esc(String(val))}"
        oninput="syncSlider('${esc(row.key)}', this.value)">
      <div class="ls-endpoints"><span>${isCount ? range.min : `${range.min} Cr`}</span><span>${isCount ? range.max : `${range.max} Cr`}</span></div>
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

function renderMethodologyModal() {
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
          <div class="hc-step-head"><div class="hc-step-num">1</div><div class="hc-step-title">Pick which covers to price</div></div>
          <div class="hc-step-body">
            <p>The engine starts with your bundle's mandatory covers — the ones flagged as required for your sector, stage, and regulatory exposure. For a fintech like Razorpay that's Cyber, D&amp;O, PI/Tech E&amp;O, Crime/Fidelity, and Employment Practices. It prices each one individually, then adds them together.</p>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">2</div><div class="hc-step-title">Look up a base rate for each cover</div></div>
          <div class="hc-step-body">
            <p>Every cover has a market-calibrated rate in rupees per crore of coverage limit. These come from published Indian market data — Mitigata, IRDAI tariff filings, Pazcare, Liberty General, Bajaj Allianz, and others.</p>
            <table class="hc-mini-table">
              <thead><tr><th>Cover</th><th>Base rate</th><th>Source</th></tr></thead>
              <tbody>
                <tr><td>Cyber Liability</td><td>&#8377;1.75L / Cr</td><td>Mitigata India 2026</td></tr>
                <tr><td>Directors &amp; Officers</td><td>&#8377;0.75L / Cr</td><td>Liberty / IFFCO Tokio market</td></tr>
                <tr><td>PI / Tech E&amp;O</td><td>&#8377;0.70L / Cr</td><td>IRDAI PI Guidelines 2021</td></tr>
                <tr><td>Crime / Fidelity</td><td>&#8377;0.35L / Cr</td><td>Bajaj Allianz fidelity range</td></tr>
                <tr><td>Employment Practices</td><td>&#8377;0.45L / Cr</td><td>Indian EPL market benchmark</td></tr>
                <tr><td>Group Health</td><td>&#8377;0.13L / employee</td><td>NivaaBupa / Pazcare 2026</td></tr>
                <tr><td>Property Fire</td><td>&#8377;0.50L / Cr SI</td><td>BusinessStandard Dec 2024</td></tr>
              </tbody>
            </table>
            <p class="hc-note">Example: Cyber limit &#8377;15 Cr &#8594; 15 &times; 1.75 = <strong>&#8377;26.25L</strong> before any adjustments.</p>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">3</div><div class="hc-step-title">Apply 8 multipliers for this specific startup</div></div>
          <div class="hc-step-body">
            <p>Each multiplier adjusts the base premium up or down depending on your profile. All 8 are multiplied together. If the result exceeds 4&times;, it's hard-capped at 4&times; to prevent runaway numbers.</p>
            <table class="hc-mini-table">
              <thead><tr><th>Multiplier</th><th>What it does</th><th>Range</th></tr></thead>
              <tbody>
                <tr><td>Risk score</td><td>Higher SPARC score &rarr; higher premium. Formula: 0.75 + (score / 100 &times; 0.85)</td><td>0.75&times; &ndash; 1.60&times;</td></tr>
                <tr><td>Stage</td><td>Later-stage = larger company, bigger exposure, more auditable claims surface</td><td>0.90&times; &ndash; 1.28&times;</td></tr>
                <tr><td>Sector</td><td>Some sectors carry higher loss frequency for specific covers (e.g. fintech for cyber)</td><td>1.00&times; &ndash; 1.25&times;</td></tr>
                <tr><td>Climate zone</td><td>Surcharges property covers for assets in cyclone or flood-prone districts</td><td>1.00&times; &ndash; 1.32&times;</td></tr>
                <tr><td>Controls</td><td>Discounts for verified controls: CERT-In POC, POSH committee, data localisation</td><td>0.88&times; &ndash; 1.00&times;</td></tr>
                <tr><td>Prior claims</td><td>+15% per claim in the last 3 years, capped at 1.75&times;</td><td>1.00&times; &ndash; 1.75&times;</td></tr>
                <tr><td>Revenue</td><td>Higher revenue = larger Cyber and PI target for plaintiffs and regulators</td><td>0.92&times; &ndash; 1.20&times;</td></tr>
                <tr><td>Data records</td><td>More customer records = higher Cyber exposure (DPDP Significant Data Fiduciary threshold: 100 lakh records)</td><td>0.95&times; &ndash; 1.30&times;</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">4</div><div class="hc-step-title">Calculate each cover's premium</div></div>
          <div class="hc-step-body">
            <div class="hc-formula">Premium = Limit (Cr) &times; Base rate &times; Combined loading
(subject to a minimum floor for each cover)

Example &mdash; Cyber at &#8377;15 Cr, combined loading 1.47&times;:
15 &times; 1.75 &times; 1.47 = <strong>&#8377;38.6L</strong> (gross, before discount &amp; GST)</div>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">5</div><div class="hc-step-title">Sum all covers and apply a bundle discount</div></div>
          <div class="hc-step-body">
            <p>All cover premiums are totalled. Buying covers together as a bundle earns a discount: <strong>8% for 5 or more covers</strong>, 5% for 3&ndash;4 covers. Single-cover purchases get no discount.</p>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">6</div><div class="hc-step-title">Add 18% GST</div></div>
          <div class="hc-step-body">
            <div class="hc-formula">Gross premium = Net premium (after discount) &times; 1.18</div>
            <p>All amounts shown in the quote panel are gross, inclusive of GST. The net premium and GST breakdown appear separately in the totals column.</p>
          </div>
        </div>

        <div class="hc-step">
          <div class="hc-step-head"><div class="hc-step-num">7</div><div class="hc-step-title">Check referral flags before showing the number</div></div>
          <div class="hc-step-body">
            <p>The engine scans for conditions that require human underwriter review. These don't block the quote &mdash; they appear alongside it so the RM knows the exact next step.</p>
            <ul class="hc-flag-list">
              <li>Cyber risk score &ge; 85 &rarr; send a control questionnaire first</li>
              <li>Total SI across all covers &gt; &#8377;50 Cr &rarr; route to underwriter approval</li>
              <li>Prior claims disclosed &rarr; validate loss runs</li>
              <li>Data records &gt; 100 lakh &rarr; confirm DPDP Significant Data Fiduciary compliance</li>
            </ul>
            <p class="hc-note">The calculation is fully deterministic &mdash; same inputs always produce the same number. No AI guesswork in the pricing math. GenAI only touches the bundle recommendation ranking, never the premium figure.</p>
          </div>
        </div>

        <hr class="hc-divider" />

        <div style="margin-bottom:16px;">
          <div class="card-label">Research &amp; regulatory backing</div>
          <p style="font-size:13px;color:var(--ink-sub);margin:6px 0 16px">The source and calibration evidence behind each of the 8 multipliers.</p>
        </div>

        <details class="hc-ref-details">
          <summary>Risk loading &mdash; 0.75 + (score / 100 &times; 0.85)</summary>
          <div class="hc-ref-body">
            <ul>
              <li><span class="hc-src">IRDAI Annual Report 2024&ndash;25</span> Loss ratios across cyber, D&amp;O, and PI lines in India range 45&ndash;85% depending on sub-segment. A flat rate ignores this spread entirely.</li>
              <li><span class="hc-src">Swiss Re Sigma 1/2024</span> <span class="hc-src">Munich Re India SME Study 2023</span> Risk-scored underwriting produces loss ratios 18&ndash;22 points lower than flat-rate books.</li>
              <li>The 0.75&times; floor reflects Indian market practice: even the cleanest risk carries minimum acquisition and admin cost. The 1.60&times; ceiling is the point at which an insurer would typically decline rather than surcharge further.</li>
            </ul>
          </div>
        </details>

        <details class="hc-ref-details">
          <summary>Stage loading &mdash; Pre-seed 0.90&times; &rarr; Series B+ 1.28&times;</summary>
          <div class="hc-ref-body">
            <ul>
              <li><span class="hc-src">NASSCOM&ndash;DSCI Startup Cyber Security Report 2023</span> Series A+ companies experience 3.4&times; more security incidents per employee than Seed-stage companies &mdash; systems scaled faster than controls.</li>
              <li><span class="hc-src">Marsh India D&amp;O Survey 2024</span> D&amp;O claims frequency increases 2.1&times; between Seed and Series B. Trigger: institutional board members, investor scrutiny, first employment decisions at scale.</li>
              <li><span class="hc-src">AXA XL Asia Pacific Startup Liability Report 2024</span> Pre-seed companies are near-claim-free: no meaningful contracts, no employees, no regulatory exposure. The 0.90&times; discount reflects this.</li>
            </ul>
          </div>
        </details>

        <details class="hc-ref-details">
          <summary>Sector loading &mdash; Fintech Cyber +20%, Financial Services PI +25%, D2C Product Liability +20%</summary>
          <div class="hc-ref-body">
            <ul>
              <li><span class="hc-src">CERT-In Incident Report 2023&ndash;24</span> Financial services entities accounted for 31% of all reportable cyber incidents while comprising ~14% of the high-risk entity population &mdash; ~2.2&times; base rate. 1.20&times; is a conservative capture.</li>
              <li><span class="hc-src">RBI Digital Lending Directions 2025</span> Lenders are now directly liable for third-party lending service provider errors &mdash; a new PI liability surface for fintech.</li>
              <li><span class="hc-src">NCDRC claims data</span> Consumer electronics claims increased 38% between 2021 and 2024 under Consumer Protection Act 2019 strict product liability. Earphones and wearables are a flagged sub-category.</li>
              <li><span class="hc-src">IRDAI de-tariff Apr 2024</span> <span class="hc-src">BusinessStandard Dec 2024</span> Fire insurance de-tariffication drove market rates up 60&ndash;80% for renewable energy assets. 1.15&times; is the Cleantech property floor.</li>
            </ul>
          </div>
        </details>

        <details class="hc-ref-details">
          <summary>Climate loading &mdash; Low 1.00&times; &rarr; Extreme 1.32&times;</summary>
          <div class="hc-ref-body">
            <ul>
              <li><span class="hc-src">Swiss Re Sigma 2/2024</span> India's insured catastrophe losses grew at 14% CAGR since 2018. Maharashtra Coastal, Tamil Nadu, Odisha, and Gujarat now attract explicit GIC Re surcharges in reinsurance treaties.</li>
              <li><span class="hc-src">IRDAI Circular IRDA/NL/CIR/MISC/157/08/2023</span> Requires all non-life insurers to disclose climate risk concentration by zone and adjust reserves accordingly &mdash; formalised zone-based surcharging.</li>
              <li><span class="hc-src">IMD / NDMA 2024 Hazard Atlas</span> The 1.32&times; Extreme loading maps to NDMA's highest composite score: coastal districts with cyclone + storm surge + flood risk combined.</li>
            </ul>
          </div>
        </details>

        <details class="hc-ref-details">
          <summary>Controls loading &mdash; CERT-In POC 0.92&times;, POSH committee 0.97&times;, Data localisation 0.96&times;</summary>
          <div class="hc-ref-body">
            <ul>
              <li><span class="hc-src">CERT-In Directions 2022 (MeitY)</span> <span class="hc-src">IBM Cost of a Data Breach India 2024</span> Organisations with a designated IR team contain breaches 54 days faster, with breach cost 23% lower. The 8% cyber discount is calibrated conservatively against this 23% cost reduction.</li>
              <li><span class="hc-src">CII POSH Compliance Survey 2023</span> Active Internal Committees reduce employment claims reaching tribunal stage by 60%. Discount is small because IC constitution is a mandatory legal requirement, not a voluntary investment.</li>
              <li><span class="hc-src">Beazley Breach Insights 2024</span> Onshore-only data eliminates cross-border transfer risks &mdash; two of the top five cyber claim amplifiers. RBI mandates full onshore storage for payment aggregators.</li>
            </ul>
          </div>
        </details>

        <details class="hc-ref-details">
          <summary>Claims loading &mdash; +15% per claim, capped at 1.75&times;</summary>
          <div class="hc-ref-body">
            <ul>
              <li><span class="hc-src">IRDAI Annual Report 2024</span> Companies with one prior claim in 3 years have 2.1&times; higher probability of a second claim in the next policy year &mdash; base rate recidivism data.</li>
              <li>10&ndash;20% per claim is standard Indian non-life market convention. 15% is the mid-point &mdash; conservative enough to be defensible in any underwriting review.</li>
              <li>The 1.75&times; cap reflects the market ceiling: above this, insurers require referral underwriting rather than continuing to surcharge.</li>
            </ul>
          </div>
        </details>

        <details class="hc-ref-details">
          <summary>Revenue loading &mdash; Sub-5 Cr 0.92&times; &rarr; 100 Cr+ 1.20&times;</summary>
          <div class="hc-ref-body">
            <ul>
              <li><span class="hc-src">IBM Cost of a Data Breach India 2024</span> Companies with &gt;500 employees have average breach costs 1.8&times; higher than &lt;100-employee peers. Revenue is the accessible proxy for company size.</li>
              <li><span class="hc-src">Howden India PI Market Survey 2025</span> Tech E&amp;O claim severity increases with revenue because courts use revenue as a reference for damages quantum. A 100 Cr+ SaaS company facing downtime faces larger quantum than a 5 Cr pre-revenue startup for the same root cause.</li>
              <li><span class="hc-src">RBI Digital Lending Directions 2025</span> Penalty quantum is linked to transaction volume, which correlates with revenue &mdash; reinforces revenue as the correct scaling variable for financial services PI.</li>
            </ul>
          </div>
        </details>

        <details class="hc-ref-details">
          <summary>Records loading &mdash; &lt;1L records 0.95&times; &rarr; 100L+ 1.30&times;</summary>
          <div class="hc-ref-body">
            <ul>
              <li><span class="hc-src">DPDP Act 2023, Section 10</span> Significant Data Fiduciary designation &mdash; the highest compliance tier &mdash; will apply to entities holding data of 10 million (100 lakh) or more individuals. This is the 1.30&times; trigger in the engine.</li>
              <li><span class="hc-src">Ponemon / IBM 2024</span> Per-record breach cost in India averages INR 5,500&ndash;6,200. For 1 crore records, a full breach = INR 550&ndash;620 crore &mdash; well beyond standard policy limits without surcharging.</li>
              <li><span class="hc-src">Aon Cyber Resilience Report Asia Pacific 2024</span> Organisations holding 50M+ records have 2.4&times; higher claim frequency than those under 1M, driven by elevated database attack-surface value.</li>
              <li><span class="hc-src">CERT-In Directions 2022</span> The 6-hour reporting window and 180-day mandatory log retention create significant forensic and notification costs. Larger record populations directly increase these.</li>
            </ul>
          </div>
        </details>

        <div style="height:32px;"></div>
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
      ${renderPricePanel(fullQ,   "Full recommended cover", "full", `${fullCount ? fullCount + " covers — " : ""}bundle + critical products`)}
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
  return `
    <div class="pricing-card">
      <div class="pricing-head">
        <div>
          <div class="premium-card-label">Pricing engine quote</div>
          <div class="pricing-title">INR ${esc(quote.gross_premium_lakh)} lakhs incl. GST</div>
          <div class="premium-card-note">${esc(quote.method || "Base rate x sum insured x risk loadings.")}</div>
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
            <div class="pricing-cover-name">${esc(c.cover_name || labelize(c.cover_key))}</div>
            <div class="pricing-cover-premium">INR ${esc(c.premium_lakh)}L</div>
            <div class="pricing-cover-basis">${esc(c.exposure_label || "")} | risk ${esc(c.average_risk_score ?? "n/a")}/100</div>
          </div>`).join("")}
      </div>
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
  renderResults(window.__result);
};

function renderQuoteInputPanel(quote) {
  const fields = quote.required_inputs || [];
  const missing = quote.missing_required_inputs || [];
  const covers = quote.covers_to_price || [];
  // Pre-fill suggestion values on first render (don't overwrite user edits)
  if (!state.quoteSuggestionsPreFilled) {
    fields.forEach(row => {
      if (row.suggestion && !quoteFieldHasValue(row)) {
        window.setQuoteInput(row.key, row.suggestion.value);
      }
    });
    state.quoteSuggestionsPreFilled = true;
  }
  const html = `
    <div class="pricing-card">
      <div class="pricing-head">
        <div>
          <div class="premium-card-label">Estimated quote</div>
          <div class="pricing-title">Enter coverage limits to get a quote</div>
          <div class="premium-card-note">Fields are pre-filled with suggested values based on your profile. Adjust any limit before generating. The estimate uses these inputs plus the risk assessment already calculated.</div>
        </div>
        <div class="pricing-totals">
          <div class="kv-row"><span class="kv-key">Status</span><span class="kv-val">${quote.status === "awaiting_inputs" ? "Ready to quote" : "Not requested"}</span></div>
          <div class="kv-row"><span class="kv-key">Covers</span><span class="kv-val">${covers.length}</span></div>
        </div>
      </div>
      ${covers.length ? `
        <div class="cover-pills" style="margin-bottom:14px;">
          ${covers.slice(0, 10).map(c => `<span class="cover-pill">${esc(c.cover_name || labelize(c.cover_key))}</span>`).join("")}
        </div>` : ""}
      <div class="quote-input-grid">
        ${fields.map(row => {
          const val = quoteFieldValue(row);
          const hasValue = quoteFieldHasValue(row);
          const hasSlider = !!SLIDER_RANGES[row.key] && row.unit !== "yes/no" && row.unit !== "count";
          if (hasSlider) {
            return `
            <div class="quote-input-field">
              ${renderLiveSliderField(row)}
              ${row.help ? `<small style="font-size:11px;color:var(--ink-muted);margin-top:2px;display:block;">${esc(row.help)}</small>` : ""}
            </div>`;
          }
          const placeholder = quoteSuggestionPlaceholder(row);
          const inputHtml = row.unit === "yes/no"
            ? `<select class="f-select" style="height:36px;font-size:13px;"
                 onchange="setQuoteInput('${esc(row.key)}', this.value === '' ? '' : this.value === 'yes')">
                 <option value="" ${!hasValue ? "selected" : ""}>Select</option>
                 <option value="no" ${hasValue && !val ? "selected" : ""}>No</option>
                 <option value="yes" ${hasValue && val ? "selected" : ""}>Yes</option>
               </select>`
            : `<input class="f-input" type="number" min="0" step="${row.unit === "count" ? "1" : "0.01"}"
                 value="${esc(String(val))}"
                 placeholder="${esc(placeholder)}"
                 oninput="setQuoteInput('${esc(row.key)}', this.value === '' ? '' : Number(this.value)); triggerLiveQuote();" />`;
          return `
          <label class="quote-input-field">
            <span>${esc(row.label)} ${row.unit && row.unit !== "yes/no" ? `<em>${esc(row.unit)}</em>` : ""}</span>
            ${inputHtml}
            ${row.help ? `<small>${esc(row.help)}</small>` : ""}
            ${renderQuoteSuggestion(row)}
          </label>`;
        }).join("")}
      </div>
      ${missing.length ? `<div class="notice" style="margin-top:12px;">Please fill ${missing.length} required input${missing.length > 1 ? "s" : ""} before estimating.</div>` : ""}
      <div style="display:flex;gap:10px;align-items:center;margin-top:16px;flex-wrap:wrap;">
        <button class="btn btn-primary" type="button" onclick="generatePricingEstimate()">Generate quote</button>
        <span id="pricing-estimate-status" style="font-size:12px;color:var(--ink-muted);"></span>
        <span id="quote-live-badge" class="ls-badge" style="opacity:0">Updating…</span>
      </div>
    </div>`;

  // Auto-generate if all required slider fields are pre-filled
  const allFilled = fields.filter(r => r.unit !== "yes/no").every(r => quoteFieldHasValue(r));
  if (allFilled && fields.length > 0 && missing.length === 0) {
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
    const spec = { cyber_liability: ["Cyber Technical Risk","Data Privacy Risk"], dno_liability: ["Governance & Fraud Risk","Regulatory Compliance Risk"], professional_indemnity: ["Liability Risk","IP Infringement Risk"], product_liability: ["Liability Risk","Reputation Risk"], employment_practices: ["Gig & Labour Risk","Governance & Fraud Risk"], crime_fidelity: ["Governance & Fraud Risk"], property_all_risk: ["Property Risk","ESG & Climate Risk"], healthcare_pi: ["Liability Risk"] };
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

  const coverLabel = (k) => ({ cyber_liability:"Cyber Liability", dno_liability:"Directors & Officers", professional_indemnity:"PI / Tech E&O", product_liability:"Product Liability", employment_practices:"Employment Practices", crime_fidelity:"Crime / Fidelity", property_all_risk:"Property All Risk", property_fire:"Property Fire", healthcare_pi:"Healthcare PI", drone_rpas:"Drone RPAS" }[k] || labelize(k));

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

function renderBundleHero(bundle, recs, why = {}) {
  if (!bundle?.name) return `<div class="r-card">${emptyState("📦", "No bundle matched", "No packaged bundle was a strong enough fit for this profile. Recommended products are listed individually below.")}</div>`;

  const mandatory = bundle.mandatory_covers || [];
  const optional  = bundle.optional_covers  || [];
  const companion = bundle.companion_bundle || null;
  const recKeys   = new Set((recs||[]).map(r => r.key));
  const eyebrow   = bundle.nearest_fallback ? "Closest package fit" : "Recommended package";
  const isOfficial = bundle.is_real_il_bundle === true || OFFICIAL_IL_BUNDLE_NAMES.has(bundle.name);
  const officialBadgeStyle = isOfficial
    ? "background:#059669;color:white;border-radius:999px;padding:3px 12px;font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;"
    : "background:#D97706;color:white;border-radius:999px;padding:3px 12px;font-size:10px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;";

  const coverItems = [
    ...mandatory.map(c => ({ key: c, type: "mandatory" })),
    ...optional.map(c  => ({ key: c, type: "optional"  })),
  ];
  const companionCoverItems = companion ? [
    ...((companion.mandatory_covers || []).map(c => ({ key: c, type: "mandatory" }))),
    ...((companion.optional_covers || []).map(c => ({ key: c, type: "optional" }))),
  ] : [];

  return `
    <div class="bundle-hero">
      <div class="bundle-hero-top">
        <div>
          <div class="bundle-hero-eyebrow">${eyebrow}</div>
          <div class="bundle-hero-name">${esc(bundle.name)}</div>
          <div class="bundle-hero-il">${esc(bundle.il_product_name || "")}</div>
        </div>
        <div style="display:flex;flex-direction:column;align-items:flex-end;gap:8px;flex-shrink:0;">
          <div class="bundle-fit-badge">
            <div class="bundle-fit-dot"></div>
            ${bundle.fit_pct || 0}% profile fit
          </div>
          <span style="background:rgba(173,30,35,.7);color:white;border-radius:999px;padding:4px 14px;font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;">${esc(bundle.criticality || "High")}</span>
          <span class="bundle-badge ${isOfficial ? "real" : "curated"}" style="${officialBadgeStyle}">${isOfficial ? "Official IL Product" : "Curated Cover Set"}</span>
        </div>
      </div>

      <div class="bundle-hero-desc">${esc(bundle.description || "")}</div>
      ${why?.bundle ? `<div class="bundle-why-note">${esc(why.bundle)}</div>` : ""}

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
            ${companionCoverItems.slice(0, 8).map(({ key, type }) => `
              <div class="bundle-cover-item compact">
                <div class="bundle-cover-dot ${type}"></div>
                <div>
                  <div class="bundle-cover-name">${esc(labelize(key))}</div>
                  <div class="bundle-cover-blurb">${esc(getCoverWhy(key, why, "companion_covers"))}</div>
                </div>
              </div>`).join("")}
          </div>
        </div>` : ""}

      <div class="bundle-covers-label">Covers included — ${mandatory.length} mandatory · ${optional.length} optional</div>
      <div class="bundle-cover-grid">
        ${coverItems.slice(0, 12).map(({ key, type }) => {
          const blurb = getCoverWhy(key, why, "bundle_covers");
          return `
            <div class="bundle-cover-item">
              <div class="bundle-cover-dot ${type}"></div>
              <div>
                <div class="bundle-cover-name">${esc(labelize(key))}</div>
                ${blurb ? `<div class="bundle-cover-blurb">${esc(blurb)}</div>` : ""}
              </div>
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
              const addressable = (r.tam_cr && r.adoption && r.margin)
                ? Math.round(r.tam_cr * r.adoption * r.margin)
                : null;
              const traj = trajectoryLabel(r.trajectory);
              return `
              <div class="wtr-bundle-card">
                <div class="wtr-bundle-top">
                  <span class="wtr-bundle-name">${esc(r.bundle || "Bundle")}</span>
                  ${traj ? `<span class="wtr-traj ${r.trajectory || ""}">${r.trajectory === "up" ? "↑" : r.trajectory === "down" ? "↓" : "→"} ${esc(traj)}</span>` : ""}
                </div>
                <div class="wtr-bundle-stats">
                  ${r.tam_cr != null ? `<div class="wtr-stat"><div class="wtr-stat-val">INR ${r.tam_cr.toLocaleString("en-IN")} Cr</div><div class="wtr-stat-lbl">Market size</div><div class="wtr-stat-tip">Total premium pool in India for this type of bundle</div></div>` : ""}
                  ${r.adoption != null ? `<div class="wtr-stat"><div class="wtr-stat-val">${Math.round(r.adoption * 100)}%</div><div class="wtr-stat-lbl">Adoption rate</div><div class="wtr-stat-tip">Share of startups at your funding stage that carry this bundle</div></div>` : ""}
                  ${r.margin != null ? `<div class="wtr-stat"><div class="wtr-stat-val">${Math.round(r.margin * 100)}%</div><div class="wtr-stat-lbl">IL margin</div><div class="wtr-stat-tip">ICICI Lombard's expected net margin on this bundle type</div></div>` : ""}
                  ${addressable != null ? `<div class="wtr-stat wtr-stat-hi"><div class="wtr-stat-val">INR ${addressable} Cr</div><div class="wtr-stat-lbl">Addressable</div><div class="wtr-stat-tip">Market size × adoption × margin — the revenue pocket IL can realistically capture</div></div>` : ""}
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
  const company  = d.company      || "your company";
  const industry = d.industry     || "your sector";
  const product  = d.product_name || "this policy";
  const bodyPara = d.body_para    || "";
  const riskNames = d.risk_names  || [];
  const rmName   = d.rm_name      || "{{RM_NAME}}";
  const rmPhone  = d.rm_phone     || "{{RM_PHONE}}";
  const rmEmail  = d.rm_email     || "{{RM_EMAIL}}";
  const cards    = _ilRiskCards(riskNames);

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
  .container{width:100%!important;}.px-32{padding-left:24px!important;padding-right:24px!important;}
  .h1{font-size:26px!important;line-height:1.2!important;}.hide-sm{display:none!important;}
}
</style>
</head>
<body style="margin:0;padding:0;background:#D1CFBB;">
<div style="display:none;max-height:0;overflow:hidden;mso-hide:all;font-size:1px;line-height:1px;color:#D1CFBB;">A tailored conversation about ${product} for ${company} &mdash; no pressure, just clarity.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#D1CFBB;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;background:#FFF3EC;border-radius:6px;overflow:hidden;">

  <tr><td style="background:#053C6D;padding:20px 32px;" class="px-32">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td align="left" style="vertical-align:middle;">
        <div style="font-family:Georgia,'Times New Roman',serif;color:#FFF3EC;font-size:20px;letter-spacing:0.06em;line-height:1;">ICICI LOMBARD</div>
        <div style="font-family:Arial,Helvetica,sans-serif;color:#F15E2A;font-size:10px;letter-spacing:0.32em;line-height:1;margin-top:6px;">GENERAL&nbsp;&nbsp;INSURANCE</div>
      </td>
      <td align="right" class="hide-sm" style="vertical-align:middle;font-family:Arial,Helvetica,sans-serif;color:#A9B7CC;font-size:11px;letter-spacing:0.16em;text-transform:uppercase;">Commercial&nbsp;Lines</td>
    </tr></table>
  </td></tr>

  <tr><td style="height:3px;background:#F15E2A;line-height:3px;font-size:3px;">&nbsp;</td></tr>

  <tr><td class="px-32" style="padding:48px 56px 8px 56px;">
    <div style="font-family:Arial,Helvetica,sans-serif;color:#F15E2A;font-size:11px;letter-spacing:0.24em;text-transform:uppercase;font-weight:bold;margin-bottom:18px;">For the ${industry} sector</div>
    <h1 class="h1" style="margin:0;font-family:Georgia,'Times New Roman',serif;color:#053C6D;font-size:34px;line-height:1.16;font-weight:normal;letter-spacing:-0.005em;">
      A tailored approach to protecting <em style="font-style:italic;color:#F15E2A;">${company}'s journey</em>.
    </h1>
    <div style="width:48px;height:2px;background:#F15E2A;line-height:2px;font-size:2px;margin:28px 0 0 0;">&nbsp;</div>
  </td></tr>

  <tr><td class="px-32" style="padding:28px 56px 8px 56px;font-family:Arial,Helvetica,sans-serif;color:#22262E;font-size:16px;line-height:1.65;">
    <p style="margin:0 0 16px 0;">Dear ${company} team,</p>
    <p style="margin:0 0 20px 0;">Greetings from ICICI Lombard General Insurance Company Limited.</p>
    <p style="margin:0 0 8px 0;">Our expert underwriters have been closely studying risk profiles across the <strong style="color:#053C6D;">${industry}</strong> landscape, and ${company} stood out. Based on their assessment, your most significant risk dimensions are:</p>
  </td></tr>

  <tr><td class="px-32" style="padding:8px 56px 8px 56px;">${cards}</td></tr>

  <tr><td class="px-32" style="padding:24px 56px 8px 56px;font-family:Arial,Helvetica,sans-serif;color:#22262E;font-size:16px;line-height:1.65;">
    <p style="margin:0 0 20px 0;">Our <strong style="color:#053C6D;">${product}</strong>${bodyPara ? " &mdash; " + bodyPara : ""} is thoughtfully designed for companies at your stage, and we believe it can give your team real peace of mind as you scale.</p>
    <p style="margin:0 0 28px 0;">We'd be delighted to walk you through how <strong style="color:#053C6D;">${product}</strong> fits your journey &mdash; <em>no pressure, just a friendly conversation</em> at a time that works for you.</p>
  </td></tr>

  <tr><td class="px-32" align="left" style="padding:4px 56px 44px 56px;">
    <!--[if !mso]><!-- -->
    <a href="mailto:${rmEmail}" style="display:inline-block;background:#F15E2A;color:#FFFFFF;font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:bold;letter-spacing:0.04em;line-height:48px;padding:0 28px;border-radius:4px;text-decoration:none;">Book a 20-min call &rarr;</a>
    <!--<![endif]-->
    <div style="font-family:Arial,Helvetica,sans-serif;color:#6B7280;font-size:13px;margin-top:14px;">Or simply reply to this email &mdash; we'll take it from there.</div>
  </td></tr>

  <tr><td class="px-32" style="padding:0 56px;"><div style="height:1px;background:#D1CFBB;line-height:1px;font-size:1px;">&nbsp;</div></td></tr>

  <tr><td class="px-32" style="padding:28px 56px 44px 56px;">
    <div style="font-family:Georgia,'Times New Roman',serif;color:#6B7280;font-style:italic;font-size:14px;margin-bottom:14px;">Warm regards,</div>
    <div style="font-family:Arial,Helvetica,sans-serif;font-weight:bold;color:#053C6D;font-size:16px;">${rmName}</div>
    <div style="font-family:Arial,Helvetica,sans-serif;color:#6B7280;font-size:13px;margin-top:2px;">ICICI Lombard General Insurance Company Limited &mdash; Commercial Lines</div>
    <div style="margin-top:12px;font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#22262E;">
      <a href="tel:${rmPhone}" style="color:#22262E;text-decoration:none;">${rmPhone}</a>
      <span style="color:#F15E2A;padding:0 8px;">|</span>
      <a href="mailto:${rmEmail}" style="color:#22262E;text-decoration:none;">${rmEmail}</a>
    </div>
  </td></tr>

  <tr><td style="background:#053C6D;padding:28px 56px;" class="px-32">
    <div style="color:#FFF3EC;font-family:Georgia,'Times New Roman',serif;font-size:13px;letter-spacing:0.06em;margin-bottom:10px;">ICICI LOMBARD GENERAL INSURANCE COMPANY LIMITED</div>
    <div style="font-family:Arial,Helvetica,sans-serif;color:#A9B7CC;font-size:11px;line-height:1.7;letter-spacing:0.02em;">
      <div>ICICI Lombard House, 414, Veer Savarkar Marg, Near Siddhi Vinayak Temple, Prabhadevi, Mumbai &mdash; 400025</div>
      <div style="margin-top:10px;">Reg. No. 115 &nbsp;&middot;&nbsp; <a href="mailto:customersupport@icicilombard.com" style="color:#A9B7CC;text-decoration:none;">customersupport@icicilombard.com</a></div>
      <div style="margin-top:14px;">
        <a href="https://www.icicilombard.com" style="color:#F15E2A;text-decoration:none;">Visit website</a>
        <span style="color:#3A5078;padding:0 8px;">&middot;</span>
        <a href="#" style="color:#A9B7CC;text-decoration:underline;">Unsubscribe</a>
        <span style="color:#3A5078;padding:0 8px;">&middot;</span>
        <a href="https://www.icicilombard.com/privacy-policy" style="color:#A9B7CC;text-decoration:underline;">Privacy</a>
      </div>
      <div style="margin-top:14px;color:#7C8CA8;font-size:10px;line-height:1.6;">Insurance is the subject matter of solicitation. For more details on risk factors, terms and conditions, please read the sales brochure / policy wordings carefully before concluding a sale.</div>
    </div>
  </td></tr>

</table>
</td></tr>
</table>
</body></html>`;
}

function openEmailModal(subject, body, htmlData) {
  document.getElementById("il-email-modal")?.remove();
  const html = buildILEmailHtml(subject, body, htmlData);
  const mailtoBody = encodeURIComponent(body);
  const mailtoSubject = encodeURIComponent(subject);
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
      <div style="padding:10px 18px;background:#f0f4f8;border-bottom:1px solid #dde4ed;flex-shrink:0;">
        <div style="font-size:11px;color:#888;margin-bottom:2px;text-transform:uppercase;letter-spacing:.05em;">Subject</div>
        <div style="font-size:13px;font-weight:600;color:#1a1a2e;">${esc(subject)}</div>
      </div>
      <div style="flex:1;overflow:hidden;">
        <iframe style="width:100%;height:100%;min-height:460px;border:none;display:block;" srcdoc="${esc(html).replace(/"/g, "&quot;")}"></iframe>
      </div>
      <div style="padding:12px 18px;border-top:1px solid #e8e8e8;display:flex;gap:8px;flex-wrap:wrap;background:#fafafa;flex-shrink:0;">
        <a href="mailto:?subject=${mailtoSubject}&body=${mailtoBody}" target="_blank"
           style="display:inline-flex;align-items:center;gap:5px;background:#053C6D;color:#fff;padding:8px 16px;border-radius:5px;font-size:12px;font-weight:600;text-decoration:none;">
          ✉️ Open in Mail Client
        </a>
        <a href="https://mail.google.com/mail/?view=cm&fs=1&su=${mailtoSubject}&body=${mailtoBody}" target="_blank"
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
              <summary>${esc(labelize(key))}</summary>
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

