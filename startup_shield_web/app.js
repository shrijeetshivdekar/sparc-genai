/* \u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090
   SPARC 4.0 \u2014 Unified 3-stage intake + 3-panel results
   \u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090\u00E2\u2022\u0090 */

/* \u2500\u2500\u2500 CONSTANTS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
const FLOW_STEP_LABELS = ["Anchor", "Size", "Assumptions", "Results"];

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

const BUSINESS_MODEL_ICONS = {
  "B2B SaaS / API":         "⬡",
  "B2C Consumer App":       "👤",
  "Marketplace / Platform": "🔀",
  "Physical Product / D2C": "📦",
  "Hardware / IoT":         "🔧",
  "Regulated Finance":      "🏦",
  "Offline / Physical Ops": "🏢",
};

const BUSINESS_MODEL_MAP = {
  "B2B SaaS / API":         { operations: "Digital-only",  b2b_pct: 0.9, hardware_software_split: 0.0 },
  "B2C Consumer App":       { operations: "Digital-only",  b2b_pct: 0.1, hardware_software_split: 0.0 },
  "Marketplace / Platform": { operations: "Digital-only",  b2b_pct: 0.5, gig_headcount_pct: 0.3 },
  "Physical Product / D2C": { operations: "Hybrid",        b2b_pct: 0.2, hardware_software_split: 0.4 },
  "Hardware / IoT":         { operations: "Hybrid",        b2b_pct: 0.6, hardware_software_split: 0.7 },
  "Regulated Finance":      { operations: "Digital-only",  b2b_pct: 0.8, hardware_software_split: 0.0 },
  "Offline / Physical Ops": { operations: "Physical-only", b2b_pct: 0.3, hardware_software_split: 0.3 },
};

const FUNDING_ICONS = {
  "Pre-seed":  "P0",
  "Seed":      "S",
  "Series A":  "A",
  "Series B+": "B+",
};

/* \u2500\u2500\u2500 STATE \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
const state = {
  meta: null,
  view: "flow",
  flowStep: 0,      // 0=Anchor 1=Size 2=Assumptions 3=Results
  assumptions: null,
  saveTimer: null,
  profile: {},
};

/* \u2500\u2500\u2500 UTILS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;");
const labelize = (k) => k.replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());

/* \u2500\u2500\u2500 FLOW DRAFT STORAGE \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
const FLOW_STORAGE_KEY = "sparc_flow_draft_v1";

function saveDraftFlow() {
  try {
    localStorage.setItem(FLOW_STORAGE_KEY, JSON.stringify({
      flowStep: state.flowStep,
      assumptions: state.assumptions,
      profile: state.profile,
    }));
  } catch (e) {}
}

function loadDraftFlow() {
  try {
    const raw = localStorage.getItem(FLOW_STORAGE_KEY);
    if (!raw) return;
    const saved = JSON.parse(raw);
    state.flowStep = Math.min(2, Math.max(0, Number(saved.flowStep || 0)));
    state.assumptions = saved.assumptions || null;
    if (saved.profile) state.profile = { ...(state.meta?.defaults || {}), ...saved.profile };
  } catch (e) {}
}

function afterProfileChange() {
  saveDraftFlow();
}

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

const PRODUCT_BLURBS = {
  "CYBER":                            "Covers data breach response, ransomware recovery, and regulatory penalties \u2014 directly required by CERT-In Directions 2022 and the DPDP Act.",
  "D_AND_O":                          "Protects founders and directors personally if investors, regulators, or employees file suit over decisions made on the company's behalf.",
  "PI_TECH_EO":                       "Pays legal defence and client claims if your software, API, or professional services cause a customer a financial loss or system failure.",
  "CRIME_FIDELITY":                   "Reimburses losses from employee fraud, theft, or forgery \u2014 critical once you have a finance team, vendor access, or payment flows.",
  "GROUP_HEALTH":                     "Medical cover for your entire team \u2014 a key hiring benefit and an IRDAI-regulated expectation once your headcount crosses 20.",
  "GROUP_PA":                         "Accidental death and disability cover for your workforce, and mandatory for aggregator platforms under the Code on Social Security 2020.",
  "EMPLOYERS_COMP":                   "Statutory payout if an employee is injured or dies at work \u2014 required under the Employees' Compensation Act 1923.",
  "PRODUCT_LIABILITY":                "Covers legal defence and settlements if your physical product causes injury or property damage to a customer or third party.",
  "PUBLIC_LIABILITY":                 "Covers third-party bodily injury or property damage claims arising from your premises, events, or day-to-day operations.",
  "BHARAT_SOOKSHMA":                  "IRDAI-standardised product for micro enterprises. Covers building, plant, machinery, furniture, raw materials, and stock at one business location up to INR 5 Cr sum insured.",
  "MARINE_CARGO":                     "Covers goods in transit against loss or damage while your products move between warehouses, ports, or last-mile customers.",
  "TRADE_CREDIT":                     "Pays you when a B2B buyer defaults on an invoice \u2014 essential for startups extending credit terms to distributors or enterprise clients.",
  "ENGINEERING_CAR_EAR_CPM_MBD_EEI": "Covers physical damage to machinery, equipment under erection, and electronics \u2014 essential for hardware, robotics, and manufacturing startups.",
  "SURETY":                           "A performance bond required for government contracts, guaranteeing project completion and protecting against contractor default.",
  "PRAKRITIK_PARAMETRIC":             "Pays out automatically when a climate trigger \u2014 flood index, wind speed \u2014 is breached. No claims investigation; instant liquidity for climate-exposed ops.",
  "Drone_RPAS":                       "DGCA-mandated insurance for drone operations, covering hull damage and third-party liability arising from aerial activities under Drone Rules 2021.",
  "CGL_I_ELITE":                      "Comprehensive general liability for bodily injury, property damage, and personal injury claims from any third party \u2014 the corporate liability cornerstone.",
  "EMPLOYMENT_PRACTICES":             "Covers legal defence and settlements if an employee sues the company for wrongful termination, discrimination, harassment, or POSH Act violations. Mandatory in any startup approaching 50+ headcount with active hiring and termination activity.",
  "employment_practices":             "Covers legal defence and settlements if an employee sues the company for wrongful termination, discrimination, harassment, or POSH Act violations. Mandatory in any startup approaching 50+ headcount with active hiring and termination activity.",
  "EPL":                              "Covers legal defence and settlements if an employee sues the company for wrongful termination, discrimination, harassment, or POSH Act violations. Mandatory in any startup approaching 50+ headcount with active hiring and termination activity.",
  "GROUP_CRITI_SHIELD":               "Pays a lump-sum benefit to employees diagnosed with a covered critical illness (cancer, heart attack, stroke, organ failure). Supplements group health when treatment costs exceed hospitalisation \u2014 a strong retention benefit for senior hires.",
  "group_criti_shield":               "Pays a lump-sum benefit to employees diagnosed with a covered critical illness (cancer, heart attack, stroke, organ failure). Supplements group health when treatment costs exceed hospitalisation \u2014 a strong retention benefit for senior hires.",
  "GROUP_HOSPISHIELD":                "Daily hospital cash benefit that pays a fixed amount per day of hospitalisation regardless of actual medical bills \u2014 covers incidentals, loss of income, and recovery costs not reimbursed by the primary group health policy.",
  "group_hospishield":                "Daily hospital cash benefit that pays a fixed amount per day of hospitalisation regardless of actual medical bills \u2014 covers incidentals, loss of income, and recovery costs not reimbursed by the primary group health policy.",
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

function buildProfile(sourceProfile = state.profile) {
  const profile = structuredClone(sourceProfile || {});
  profile.operations = API_OPERATION_MAP[profile.operations] || profile.operations;
  if (profile.data_sensitivity === "Very High") profile.data_sensitivity = "High";
  const founderEquity = Number(profile.founder_equity_pct ?? 0.5);
  profile.founder_concentration_index = founderEquity * (1 - (profile.has_independent_directors ? 0.4 : 0));
  profile.sdf_probability = profile.sdf_likely ? 0.75 : 0.05;
  return profile;
}

/* \u2500\u2500\u2500 INIT \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
async function init() {
  renderApp();
  const stub = buildStubMeta();
  try {
    const res = await fetch("/api/meta");
    if (!res.ok) throw new Error("no meta");
    const ct = res.headers.get("content-type") || "";
    if (!ct.includes("json")) throw new Error("not json");
    const serverMeta = await res.json();
    state.meta = { ...stub, ...serverMeta };
  } catch (e) {
    state.meta = stub;
  }
  state.profile = structuredClone(state.meta.defaults);
  loadDraftFlow();
  renderFlow();
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

/* \u2500\u2500\u2500 TOP BAR \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
function renderApp() {
  document.getElementById("app").innerHTML = `
    <div class="app-wrap">
      <header class="topbar">
        <div class="topbar-brand">
          <div class="brand-mark">S</div>
          <span class="topbar-name">SPARC</span>
        </div>
        <div class="topbar-sep"></div>
        <span class="topbar-sub">ICICI Lombard \u00B7 Startup Risk Intelligence</span>
      </header>
      <div id="main-content"></div>
    </div>`;
}

/* \u2500\u2500\u2500 FLOW SHELL \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
function renderFlow() {
  state.view = "flow";
  $("main-content").innerHTML = `
    <div class="flow-shell">
      <aside class="flow-sidebar" id="flow-sidebar"></aside>
      <main class="flow-main" id="flow-main"></main>
    </div>`;
  renderFlowStep();
}

function renderFlowStep() {
  updateFlowSidebar();
  const step = state.flowStep;
  const main = $("flow-main");
  if (!main) return;
  if (step === 0) main.innerHTML = renderStepAnchor();
  else if (step === 1) main.innerHTML = renderStepSize();
  else if (step === 2) {
    if (!state.assumptions) state.assumptions = deriveAssumptions();
    main.innerHTML = renderStepAssumptions();
  }
  updateFlowNav();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateFlowSidebar() {
  const sidebar = $("flow-sidebar");
  if (!sidebar) return;
  sidebar.innerHTML = `
    <div class="flow-sidebar-brand">
      <div class="flow-sidebar-title">SPARC</div>
      <div class="flow-sidebar-sub">Startup Risk Intelligence</div>
    </div>
    <nav class="flow-step-list">
      ${FLOW_STEP_LABELS.map((label, i) => {
        const done = i < state.flowStep;
        const active = i === state.flowStep;
        const locked = i > state.flowStep;
        return `
          <div class="flow-step-item ${done ? "done" : ""} ${active ? "active" : ""} ${locked ? "locked" : ""}">
            <div class="flow-step-dot">${done ? "OK" : i + 1}</div>
            <span class="flow-step-label">${esc(label)}</span>
          </div>`;
      }).join("")}
    </nav>`;
}

function updateFlowNav() {
  const main = $("flow-main");
  if (!main) return;
  const isFirst = state.flowStep === 0;
  const isFinal = state.flowStep === 2;
  let existing = $("flow-nav");
  const navHtml = `
    <div class="flow-nav" id="flow-nav">
      <button class="btn btn-ghost" id="flow-back-btn" type="button" ${isFirst ? "disabled" : ""}>&lt; Back</button>
      <div class="nav-spacer"></div>
      <button class="btn btn-primary btn-lg" id="flow-next-btn" type="button">
        ${isFinal ? "Analyse >" : "Continue >"}
      </button>
    </div>`;
  if (existing) existing.outerHTML = navHtml;
  else main.insertAdjacentHTML("beforeend", navHtml);
  const backBtn = $("flow-back-btn");
  const nextBtn = $("flow-next-btn");
  if (backBtn) backBtn.onclick = () => {
    if (state.flowStep > 0) { state.flowStep--; renderFlowStep(); }
  };
  if (nextBtn) nextBtn.onclick = () => {
    if (!validateFlowStep()) return;
    if (state.flowStep < 2) { state.flowStep++; saveDraftFlow(); renderFlowStep(); }
    else { applyAssumptionsToProfile(); runFlowAnalysis(); }
  };
}

function validateFlowStep() {
  const step = state.flowStep;
  const p = state.profile;
  if (step === 0) {
    const missing = [];
    if (!p.sector) missing.push("sector");
    if (!p.funding_stage) missing.push("funding_stage");
    if (!p.business_model) missing.push("business_model");
    if (missing.length) {
      missing.forEach(key => {
        document.querySelectorAll(`[data-validate="${key}"]`).forEach(el => {
          el.style.outline = "2px solid var(--red,#ad1e23)";
          setTimeout(() => (el.style.outline = ""), 2000);
        });
      });
      return false;
    }
  }
  return true;
}

/* \u2500\u2500\u2500 STEP 0: ANCHOR \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
function renderStepAnchor() {
  const p = state.profile;
  const sectors = (state.meta?.sectors || []).map(s => s.name);
  const stages = state.meta?.fundingStages || ["Pre-seed", "Seed", "Series A", "Series B+"];

  const sectorCards = sectors.map(s => `
    <button class="choice-card ${p.sector === s ? "active" : ""}" type="button"
      data-validate="sector"
      onclick="flowPickSector('${esc(s)}',this)">
      <div class="cc-icon">${esc(SECTOR_ICONS[s] || "GEN")}</div>
      <div class="cc-label">${esc(s)}</div>
    </button>`).join("");

  const stageCards = stages.map(s => `
    <button class="choice-card ${p.funding_stage === s ? "active" : ""}" type="button"
      data-validate="funding_stage"
      onclick="flowPickStage('${esc(s)}',this)">
      <div class="cc-icon">${esc(FUNDING_ICONS[s] || "STG")}</div>
      <div class="cc-label">${esc(s)}</div>
    </button>`).join("");

  const bizCards = Object.keys(BUSINESS_MODEL_ICONS).map(m => `
    <button class="choice-card ${p.business_model === m ? "active" : ""}" type="button"
      data-validate="business_model"
      onclick="flowPickBizModel('${esc(m)}',this)">
      <div class="cc-icon">${esc(BUSINESS_MODEL_ICONS[m])}</div>
      <div class="cc-label">${esc(m)}</div>
    </button>`).join("");

  return `
    <div class="flow-step-content">
      <div class="flow-step-head">
        <div class="flow-eyebrow">Step 1 of 3</div>
        <h1>Tell us about your startup</h1>
        <p>Three choices that tell the engine who you are, where you are in your journey, and how you operate.</p>
      </div>
      <div class="field-group">
        <label>What sector are you in?</label>
        <div class="card-grid">${sectorCards}</div>
      </div>
      <div class="field-group">
        <label>Funding stage</label>
        <div class="card-grid">${stageCards}</div>
      </div>
      <div class="field-group">
        <label>How does your business operate?</label>
        <div class="card-grid">${bizCards}</div>
      </div>
    </div>`;
}

window.flowPickSector = (val, el) => {
  state.profile.sector = val;
  state.assumptions = null;
  document.querySelectorAll('[data-validate="sector"]').forEach(b => b.classList.toggle("active", b === el));
  saveDraftFlow();
};
window.flowPickStage = (val, el) => {
  state.profile.funding_stage = val;
  state.assumptions = null;
  document.querySelectorAll('[data-validate="funding_stage"]').forEach(b => b.classList.toggle("active", b === el));
  saveDraftFlow();
};
window.flowPickBizModel = (val, el) => {
  state.profile.business_model = val;
  state.assumptions = null;
  const mapped = BUSINESS_MODEL_MAP[val] || {};
  Object.assign(state.profile, mapped);
  document.querySelectorAll('[data-validate="business_model"]').forEach(b => b.classList.toggle("active", b === el));
  saveDraftFlow();
};

/* \u2500\u2500\u2500 STEP 1: SIZE \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
function renderStepSize() {
  const p = state.profile;
  const teamSize = Number(p.team_size || 20);
  const revenue = Number(p.annual_revenue_cr || 0);
  const sensitivity = p.data_sensitivity || "Medium";

  const sensitivityPills = ["Low", "Medium", "High"].map(v => `
    <button class="pill ${sensitivity === v ? "active" : ""}" type="button" data-sens="${esc(v)}"
      onclick="flowPickSensitivity('${esc(v)}',this)">${esc(v)}</button>`).join("");

  return `
    <div class="flow-step-content">
      <div class="flow-step-head">
        <div class="flow-eyebrow">Step 2 of 3</div>
        <h1>Scale &amp; sensitivity</h1>
        <p>These inputs drive premium sizing and your data exposure score.</p>
      </div>
      <div class="field-group">
        <label>Annual revenue / ARR (INR Cr)</label>
        <input class="f-input" type="number" min="0" step="0.5" value="${esc(String(revenue))}"
          placeholder="0 if pre-revenue"
          oninput="state.profile.annual_revenue_cr=Number(this.value||0);saveDraftFlow()" />
        <small>Used for premium sizing only \u2014 enter 0 if pre-revenue.</small>
      </div>
      <div class="field-group">
        <label>Team size (full-time) \u2014 <span id="team-size-bubble">${teamSize}</span></label>
        <div class="range-wrap">
          <input type="range" min="1" max="500" step="1" value="${teamSize}"
            oninput="state.profile.team_size=Number(this.value);$('team-size-bubble').textContent=this.value;saveDraftFlow()" />
        </div>
      </div>
      <div class="field-group">
        <label>Data sensitivity</label>
        <div class="pill-grid">${sensitivityPills}</div>
        <small>How sensitive is the data your business handles?</small>
      </div>
    </div>`;
}

window.flowPickSensitivity = (val, el) => {
  state.profile.data_sensitivity = val;
  document.querySelectorAll("[data-sens]").forEach(b => b.classList.toggle("active", b === el));
  saveDraftFlow();
};

/* \u2500\u2500\u2500 STEP 2: ASSUMPTIONS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
function deriveAssumptions() {
  const p = state.profile;
  const sector = p.sector || "";
  const model = p.business_model || "";
  const isFintech   = ["Fintech", "Insurtech"].some(s => sector.includes(s));
  const isHealth    = sector.includes("Healthtech");
  const isLogistics = sector.includes("Logistics");
  const isD2C       = sector.includes("D2C") || sector.includes("Consumer");
  const isDeeptech  = sector.includes("Deeptech") || sector.includes("AI");
  const isMarketplace = model.includes("Marketplace");
  const isPhysical  = model.includes("Physical") || model.includes("Offline") || model.includes("Hardware");
  const hasB2B      = model.includes("B2B") || model.includes("Regulated") || model.includes("Finance");

  return {
    A: { label: "Your startup handles customer personal data (PII / KYC / payments)", value: isFintech || isHealth || hasB2B },
    B: { label: "Your startup has institutional investors (VCs / Angels / PE)", value: p.funding_stage !== "Pre-seed" },
    C: { label: "Your startup has active B2B customer contracts", value: hasB2B || isFintech },
    D: { label: "Your startup operates physical spaces (office / warehouse / lab)", value: isPhysical || isD2C || isLogistics },
    E: {
      label: "Your startup employs gig / contract workers",
      value: isMarketplace || isLogistics,
      sub: { label: "Approx. % of workforce who are gig / contractors", key: "gig_headcount_pct", type: "slider", value: isLogistics ? 0.5 : 0.2 },
    },
    F: {
      label: "Your startup is licensed by RBI / SEBI / IRDAI",
      value: isFintech,
      sub: { label: "Registration type", key: "rbi_registration", type: "select",
             options: ["None","PA (Payment Aggregator)","PG (Payment Gateway)","NBFC","NBFC-AA","Prepaid Instruments"], value: "None" },
    },
    G: { label: "Your startup uses AI / ML in its core product", value: isDeeptech || model.includes("B2B SaaS") },
    H: { label: "Your startup has drone or UAV operations", value: false },
  };
}

function renderStepAssumptions() {
  const assumptions = state.assumptions;
  const p = state.profile;

  const rows = Object.entries(assumptions).map(([key, a], idx) => {
    const isYes = !!a.value;
    let subHtml = "";
    if (a.sub) {
      const sub = a.sub;
      if (sub.type === "slider") {
        const val = Number(p[sub.key] ?? sub.value ?? 0);
        subHtml = `
          <div class="assumption-sub ${isYes ? "visible" : ""}" id="asub-${esc(key)}">
            <label>${esc(sub.label)} \u2014 <span id="asub-val-${esc(key)}">${Math.round(val * 100)}%</span></label>
            <div class="range-wrap">
              <input type="range" min="0" max="1" step="0.01" value="${val}"
                oninput="setAssumptionProp('${esc(key)}',Number(this.value));$('asub-val-${esc(key)}').textContent=Math.round(this.value*100)+'%'" />
            </div>
          </div>`;
      } else if (sub.type === "select") {
        const cur = p[sub.key] || sub.value || "";
        subHtml = `
          <div class="assumption-sub ${isYes ? "visible" : ""}" id="asub-${esc(key)}">
            <label>${esc(sub.label)}</label>
            <select class="f-select" style="height:36px;font-size:13px;max-width:280px;"
              onchange="setAssumptionProp('${esc(key)}',this.value)">
              ${(sub.options || []).map(o => `<option value="${esc(o)}" ${cur===o?"selected":""}>${esc(o)}</option>`).join("")}
            </select>
          </div>`;
      }
    }
    return `
      <div class="assumption-row" id="arow-${esc(key)}">
        <div class="assumption-main">
          <span class="assumption-label">${esc(a.label)}</span>
          <div class="assumption-toggle">
            <button class="pill ${!isYes ? "active" : ""}" type="button" onclick="setAssumption('${esc(key)}',false)">No</button>
            <button class="pill ${isYes  ? "active" : ""}" type="button" onclick="setAssumption('${esc(key)}',true)">Yes</button>
          </div>
        </div>
        ${subHtml}
      </div>`;
  }).join("");

  return `
    <div class="flow-step-content">
      <div class="flow-step-head">
        <div class="flow-eyebrow">Step 3 of 3</div>
        <h1>Confirm your profile</h1>
        <p>We derived these from your sector and business model. Correct anything that doesn't apply \u2014 each toggle changes the risk score.</p>
      </div>
      <div class="assumptions-list">${rows}</div>
    </div>`;
}

window.setAssumption = (key, val) => {
  if (!state.assumptions?.[key]) return;
  state.assumptions[key].value = val;
  saveDraftFlow();
  const row = $(`arow-${key}`);
  if (!row) return;
  const pills = row.querySelectorAll(".assumption-toggle .pill");
  pills.forEach((p, i) => p.classList.toggle("active", i === (val ? 1 : 0)));
  const sub = $(`asub-${key}`);
  if (sub) sub.classList.toggle("visible", val);
};

window.setAssumptionProp = (key, val) => {
  if (!state.assumptions?.[key]?.sub) return;
  state.assumptions[key].sub.value = val;
  const subKey = state.assumptions[key].sub.key;
  if (subKey) state.profile[subKey] = val;
  saveDraftFlow();
};

function applyAssumptionsToProfile() {
  const a = state.assumptions;
  if (!a) return;
  const p = state.profile;

  if (a.A.value) {
    p.data_handled = p.data_handled || [];
    if (!p.data_handled.includes("Personal identity data (KYC / Aadhaar)"))
      p.data_handled.push("Personal identity data (KYC / Aadhaar)");
  }

  p.has_investors = a.B.value ? "Yes" : "No";
  p.b2b_pct = a.C.value ? Math.max(p.b2b_pct || 0, 0.6) : (p.b2b_pct || 0.2);

  if (a.D.value) {
    p.physical_assets = p.physical_assets || [];
    if (!p.physical_assets.includes("Office / coworking space"))
      p.physical_assets.push("Office / coworking space");
  }

  if (a.E.value) {
    p.gig_headcount_pct = a.E.sub?.value ?? 0.2;
    p.regulatory = p.regulatory || [];
    if (!p.regulatory.includes("Labour Codes / gig worker regulations"))
      p.regulatory.push("Labour Codes / gig worker regulations");
  }

  if (a.F.value) {
    p.regulatory = p.regulatory || [];
    if (!p.regulatory.includes("RBI / SEBI / IRDAI licensed"))
      p.regulatory.push("RBI / SEBI / IRDAI licensed");
    p.rbi_registration = a.F.sub?.value || "None";
  }

  p.ai_in_product = a.G.value;
  if (a.G.value && (!p.ai_tier || p.ai_tier === "None")) p.ai_tier = "Applied";

  if (a.H.value) {
    p.physical_assets = p.physical_assets || [];
    if (!p.physical_assets.includes("Drones / UAV equipment"))
      p.physical_assets.push("Drones / UAV equipment");
    p.regulatory = p.regulatory || [];
    if (!p.regulatory.includes("DGCA / drone operations"))
      p.regulatory.push("DGCA / drone operations");
  }
}

/* \u2500\u2500\u2500 FLOW ANALYSIS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
async function runFlowAnalysis() {
  $("main-content").innerHTML = `
    <div class="loading-screen">
      <div class="loading-ring"></div>
      <div class="loading-text">Analysing your startup</div>
      <div class="loading-sub">Running 13 risk models against your profile</div>
      <div class="loading-steps">
        <div class="loading-step"><div class="loading-step-dot"></div>Scoring digital &amp; data exposure\u2026</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Mapping regulatory triggers\u2026</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Matching ICICI Lombard products\u2026</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Estimating premium ranges\u2026</div>
      </div>
    </div>`;
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
    try {
      const demoRes = await fetch("./demo-response.json");
      const demo = await demoRes.json();
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
          <button class="btn btn-ghost" style="margin-top:16px;" onclick="renderFlow()">&lt; Edit inputs</button>
        </div>`;
    }
  }
}

// Global helpers \u2014 used by refine panel
window.setVal = (key, val) => {
  state.profile[key] = val;
  if (key === "ai_tier") state.profile.ai_in_product = val !== "None";
  afterProfileChange();
};

window.setAI = (v) => {
  state.profile.ai_in_product = v === "Yes";
  state.profile.ai_tier = v === "Yes" ? "Applied" : "None";
  document.querySelectorAll(`.pill[data-key="ai_toggle"]`).forEach(btn => {
    btn.classList.toggle("active", btn.dataset.value === v);
  });
  afterProfileChange();
};

window.chooseCard = (el, key, multi) => {
  const val = el.dataset.value;
  if (!multi) {
    document.querySelectorAll(`.choice-card[data-key="${key}"]`).forEach(b => b.classList.remove("active"));
    el.classList.add("active");
    state.profile[key] = val;
  } else {
    el.classList.toggle("active");
    const cur = new Set(state.profile[key] || []);
    cur.has(val) ? cur.delete(val) : cur.add(val);
    state.profile[key] = [...cur];
  }
  afterProfileChange();
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


/* \u2500\u2500\u2500 ANALYSIS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
async function runAnalysis() {
  renderLoading();
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
          <button class="btn btn-ghost" style="margin-top:16px;" onclick="renderFlow()">&lt; Edit inputs</button>
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
        <div class="loading-step"><div class="loading-step-dot"></div>Scoring digital &amp; data exposure\u2026</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Mapping regulatory triggers\u2026</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Matching ICICI Lombard products\u2026</div>
        <div class="loading-step"><div class="loading-step-dot"></div>Estimating premium ranges\u2026</div>
      </div>
    </div>`;
}

/* \u2500\u2500\u2500 PANEL HELPERS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */

function generateRMBullets(result) {
  const p = result.profile || {};
  const recs = result.recommendations || [];
  const triggers = result.regulatory_triggers || [];
  const topRisks = result.top_risks || [];
  const sector = (p.sector || "").toLowerCase();
  const stage = (p.funding_stage || "").toLowerCase();
  const bullets = [];

  // 1. Contract / PI bullet
  const b2bSectors = ["fintech", "saas", "healthtech", "edtech", "legaltech", "insurtech"];
  const piRec = recs.find(r => ["PI_TECH_EO", "I_SELECT_LIABILITY", "PROFESSIONAL_INDEMNITY"].includes(r.key));
  if ((p.b2b_pct || 0) >= 0.5 || b2bSectors.some(s => sector.includes(s))) {
    const productName = piRec ? (piRec.name || labelize(piRec.key)) : "Professional Indemnity cover";
    bullets.push(`Have you signed any enterprise contracts that require ${productName} as a condition? Most Series A SaaS and fintech deals mandate it \u2014 worth checking the MSA template before renewal.`);
  }

  // 2. Regulatory / cyber bullet
  const cyberTrigger = triggers.find(t => t.product === "CYBER");
  const cyberRisk = topRisks.find(r => r.key === "cyber_technical");
  if (cyberTrigger || cyberRisk) {
    const scoreStr = cyberRisk?.score ? `${Math.round(cyberRisk.score)}/100` : "elevated";
    bullets.push(`Your sector scores ${scoreStr} on cyber breach exposure \u2014 has the team run a CERT-In drill? The 6-hour mandatory incident reporting window catches most founding teams off guard at first event.`);
  } else {
    const topRisk = topRisks[0];
    if (topRisk) bullets.push(`Your top risk driver is ${(topRisk.name || "").replace(" Risk", "") || labelize(topRisk.key || "")} at ${topRisk.score}/100 \u2014 worth centering the next review on this before board reporting.`);
  }

  // 3. Threshold / stage bullet
  const team = p.team_size || 0;
  const gigPct = p.gig_headcount_pct || 0;
  if (team > 0 && team < 50) {
    bullets.push(`You\u2019re at ${team} people \u2014 once you cross 50 headcount, POSH Internal Committee constitution becomes a legal requirement. Getting the policy in place now keeps it off the diligence checklist at the next raise.`);
  } else if (stage.includes("series_a") || stage.includes("series a")) {
    bullets.push(`At Series A, D&O is becoming standard in term sheets \u2014 investors increasingly want liability cover in place before wiring funds. Better to get ahead of it than negotiate it as a condition precedent.`);
  } else if (gigPct > 0.2) {
    bullets.push(`With ${Math.round(gigPct * 100)}% gig workers, Code on Social Security 2020 Schedule 7 applies \u2014 Group PA becomes a compliance cost, not an optional benefit. We should price this into the renewal.`);
  } else {
    const dnoRec = recs.find(r => r.key === "D_AND_O");
    bullets.push(dnoRec
      ? `Your investors will likely ask for D&O cover before the next round \u2014 getting it in place now means it\u2019s not a condition precedent that delays close.`
      : `This profile\u2019s top exposure sits outside standard product boundaries \u2014 flag to the product team for a bespoke cover note before the next renewal conversation.`);
  }

  return bullets.slice(0, 3);
}

function renderPanelA(result) {
  const recs = result.recommendations || [];
  const critical = recs.find(r => r.priority === "Critical") || recs[0];
  if (!critical) return `<div class="panel panel-a"><div class="panel-label">Priority cover</div><p style="color:var(--ink-muted);font-size:13px;line-height:1.6;margin:0;">No critical covers flagged for this profile.</p></div>`;

  const trigger = (result.regulatory_triggers || []).find(t => t.product === critical.key);
  const bundleName = result.bundle_match?.name || "ICICI Lombard";
  const productLabel = critical.name || labelize(critical.key);
  const reason = critical.reason || `Highest-materiality uncovered risk for this profile.`;

  return `
    <div class="panel panel-a">
      <div class="panel-label">Priority cover</div>
      <div class="anchor-product">${esc(productLabel)}</div>
      <p class="anchor-sentence">${esc(reason)}${trigger ? ` <span class="anchor-reg">${esc(trigger.regulation)}</span> applies.` : ""} ${esc(bundleName)} covers this.</p>
      <div class="anchor-footer">Materiality: ${critical.materiality_score || critical.score || "\u2014"}/100 &middot; Priority: ${esc(critical.priority || "High")}</div>
    </div>`;
}

function renderPanelB(result) {
  const bundle = result.bundle_match;
  const premSummary = result.premium_summary;
  const bundleQ = result.bundle_only_pricing_quote;
  const flags = (bundleQ?.underwriter_referral_flags || []).filter(Boolean);

  if (!bundle?.name) return `<div class="panel panel-b"><div class="panel-label">Bundle recommendation</div><p style="color:var(--ink-muted);font-size:13px;line-height:1.6;margin:0;">No bundle matched this profile. Products recommended individually below.</p></div>`;

  const mandatory = bundle.mandatory_covers || [];
  const optional  = bundle.optional_covers  || [];
  const totalShown = 6;
  const overflow = Math.max(0, mandatory.length + optional.length - totalShown);

  let premHTML = "";
  if (bundleQ?.gross_premium_lakh) {
    premHTML = `<div class="panel-b-premium"><div class="panel-b-premium-range">INR ${esc(String(bundleQ.gross_premium_lakh))}L</div><div class="panel-b-premium-note">Bundle gross premium &middot; indicative</div></div>`;
  } else if (premSummary) {
    premHTML = `<div class="panel-b-premium"><div class="panel-b-premium-range">INR ${esc(String(premSummary.min_lakh))}&ndash;${esc(String(premSummary.max_lakh))}L</div><div class="panel-b-premium-note">${premSummary.count} covers &middot; indicative range</div></div>`;
  }

  return `
    <div class="panel panel-b">
      <div class="panel-label">Bundle recommendation</div>
      <div>
        <div class="panel-b-name">${esc(bundle.name)}</div>
        <div class="panel-b-fit">${bundle.fit_pct || 0}% profile fit</div>
      </div>
      <div class="panel-b-covers">
        ${mandatory.slice(0, 4).map(c => `<div class="panel-b-cover"><div class="panel-b-dot mandatory"></div>${esc(labelize(c))}</div>`).join("")}
        ${optional.slice(0, 2).map(c => `<div class="panel-b-cover"><div class="panel-b-dot optional"></div>${esc(labelize(c))} <span style="font-size:10px;color:var(--ink-faint);">optional</span></div>`).join("")}
        ${overflow > 0 ? `<div style="font-size:11px;color:var(--ink-faint);padding-left:14px;">+${overflow} more covers</div>` : ""}
      </div>
      ${flags.length ? `<div class="panel-b-flags">${flags.slice(0, 2).map(f => `<div class="panel-b-flag">\u26a0 Referral: ${esc(String(f))}</div>`).join("")}</div>` : ""}
      ${premHTML}
    </div>`;
}

function renderPanelC(result) {
  const bullets = generateRMBullets(result);
  return `
    <div class="panel panel-c">
      <div class="panel-label">RM conversation starters</div>
      <div class="rm-bullets">
        ${bullets.map((b, i) => `
          <div class="rm-bullet" id="rm-b-${i}">${esc(b)}<button class="rm-copy-btn" onclick="(function(el,btn){var txt=(el.childNodes[0]?.nodeValue||el.textContent||'').replace(/\\s*Copy\\s*|\\s*Done\\s*/g,'').trim();navigator.clipboard?.writeText(txt).then(()=>{btn.textContent='Done';setTimeout(()=>btn.textContent='Copy',1600)})})(document.getElementById('rm-b-${i}'),this)">Copy</button></div>`).join("")}
      </div>
    </div>`;
}

function renderHeroChips(p) {
  const sectors = Object.keys(SECTOR_ICONS);
  const stages  = ["Pre-seed", "Seed", "Series A", "Series B+"];
  const ops     = ["Digital-only", "Hybrid", "Physical-only"];

  const chip = (key, label, display, type, opts, rawVal) => {
    const o = JSON.stringify(opts  || []).replace(/"/g, "&quot;");
    const v = JSON.stringify(rawVal !== undefined ? rawVal : display).replace(/"/g, "&quot;");
    return `<span class="hero-chip" id="chip-${key}" onclick="startChipEdit('${key}','${type}',JSON.parse(this.dataset.opts),JSON.parse(this.dataset.val))" data-opts="${o}" data-val="${v}" title="Click to edit"><span class="chip-key">${label}:&nbsp;</span>${esc(String(display))}<span class="chip-pencil">&#9998;</span></span>`;
  };

  return [
    chip("sector",        "sector",  p.sector        || "\u2014", "select", sectors),
    chip("funding_stage", "stage",   p.funding_stage || "\u2014", "select", stages),
    chip("team_size",     "team",    p.team_size ? `${p.team_size} people` : "\u2014", "number", [], p.team_size),
    p.revenue_cr ? chip("revenue_cr", "revenue", `\u20b9${p.revenue_cr} Cr`, "number", [], p.revenue_cr) : "",
    chip("operations",    "ops",     p.operations    || "\u2014", "select", ops),
  ].join("");
}

/* \u2500\u2500\u2500 RESULTS RENDER \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
function renderResults(result) {
  state.profile = structuredClone(result.profile || state.profile);
  const p = result.profile;

  const gaugeClass = result.overall >= 70 ? "gauge-critical" : result.overall >= 45 ? "gauge-moderate" : "gauge-low";
  const gaugeColor = result.overall >= 70 ? "var(--red)" : result.overall >= 45 ? "var(--amber)" : "var(--green)";

  $("main-content").innerHTML = `
    <div class="results-wrap">

      <!-- Hero with inline-edit chips -->
      <div class="results-hero">
        <div>
          <div class="hero-eyebrow">Risk Report</div>
          <div class="hero-title">${esc(p.startup_name)} \u2014 ${result.overall}/100 overall risk</div>
          <div class="hero-chips" id="hero-chips-wrap">${renderHeroChips(p)}</div>
        </div>
        <div class="hero-actions">
          <button class="btn-hero-primary" onclick="downloadReport(window.__result)">Download report</button>
        </div>
      </div>

      <!-- 3-panel dashboard (always visible) -->
      <div class="dashboard-panels">
        ${renderPanelA(result)}
        ${renderPanelB(result)}
        ${renderPanelC(result)}
      </div>

      <!-- Bundle detail + V2 insights -->
      ${renderBundleAlternatives(result.bundle_alternatives)}
      ${renderV2Insights(result)}

      <!-- Section nav -->
      <nav class="section-nav">
        ${[["#products","Products"],["#risk","Risk scores"],["#timeline","Timeline"],["#triggers","Actions"],["#outreach","Outreach"]].map(([h,l])=>`<a class="snav-pill" href="${h}">${l}</a>`).join("")}
      </nav>

      <!-- Recommended products \u2014 secondary -->
      <div class="result-section" id="products">
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
            ].map(normalise));
            const additionalRecs = (result.recommendations || []).filter(r => !bundleKeys.has(normalise(r.key)));
            if (!additionalRecs.length) {
              return `<div class="r-card">${emptyState("OK", "All recommended products are in your bundle", "The engine has no additional products to recommend outside the selected bundle.")}</div>`;
            }
            return renderProductRows(additionalRecs, result.product_mapping);
          })()}
        </div>
        ${renderBadProducts(result.not_preferred_recommendations)}
      </div>

      <!-- Risk scores -->
      <div class="result-section" id="risk">
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

      <!-- Top risk drivers -->
      <div class="result-section">
        <div class="result-section-head">
          <div class="result-section-bar"></div>
          <div class="result-section-title">Top risk drivers</div>
        </div>
        <div class="drivers-grid">
          ${renderDriverCards((result.top_risks||[]).slice(0,3))}
        </div>
      </div>

      <!-- Timeline -->
      <div class="result-section" id="timeline">
        <div class="result-section-head">
          <div class="result-section-bar"></div>
          <div class="result-section-title">Coverage timeline</div>
        </div>
        <div class="r-card">
          <div class="timeline">${renderTimeline(result.bundles)}</div>
        </div>
      </div>

      <!-- Regulatory triggers + Mitigations -->
      <div class="result-section two-col" id="triggers">
        <div class="r-card">
          <div class="card-label">Regulatory triggers</div>
          ${renderTriggers(result.regulatory_triggers)}
        </div>
        <div class="r-card">
          <div class="card-label">Non-insurance actions</div>
          ${renderMitigations(result.mitigations)}
        </div>
      </div>

      <!-- Assumptions -->
      <details class="expander-card" style="margin-bottom:24px;">
        <summary>Assumptions used</summary>
        <div class="expander-body">
          <div class="kv-grid">${renderAssumptions(result.assumptions)}</div>
        </div>
      </details>

      <!-- Refine panel -->
      <details class="refine-panel-wrap" style="margin-bottom:24px;">
        <summary>Advanced profile adjustments</summary>
        <div class="refine-body" id="refine-body">
          ${renderRefineBody()}
        </div>
      </details>

      <!-- Outreach -->
      ${renderOutreach(result.outreach_prompts, result.outreach_source, result.outreach_error)}

      <!-- Downstream -->
      ${renderDownstream(result.downstream_opportunities)}

      <!-- Expanders -->
      <details class="expander-card" style="margin-bottom:14px;">
        <summary>Global products \u2014 how SPARC compares</summary>
        <div class="expander-body">
          <div class="products-grid">${renderGlobalProducts(result.global_products)}</div>
        </div>
      </details>

      <details class="expander-card" style="margin-bottom:14px;">
        <summary>Score breakdown \u2014 multipliers applied</summary>
        <div class="expander-body">${renderBreakdown(result.multiplier_breakdown)}</div>
      </details>

      <details class="expander-card" style="margin-bottom:14px;">
        <summary>Product comparison table</summary>
        <div class="expander-body">${renderComparisonTable(result.recommendations)}</div>
      </details>

      ${renderCustomTriggers(result.custom_triggers)}

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

  // Bind outreach copy buttons
  document.querySelectorAll("[data-copy]").forEach(btn => {
    btn.addEventListener("click", async () => {
      await navigator.clipboard?.writeText(btn.dataset.copy || "");
      const orig = btn.textContent;
      btn.textContent = "Copied";
      setTimeout(() => btn.textContent = orig, 1800);
    });
  });

  // Draw radar
  setTimeout(() => drawRadar("risk-radar", result.scores, { maxLabelLength: 16 }), 100);
}

/* \u2500\u2500\u2500 INLINE CHIP EDIT (Stage 5) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
window.startChipEdit = (key, type, options, currentVal) => {
  const el = document.getElementById(`chip-${key}`);
  if (!el || el.querySelector("input,select")) return;
  el.dataset.original = el.innerHTML;
  el.classList.add("editing");
  const prefix = `<span class="chip-key">${key.replace(/_/g," ")}:&nbsp;</span>`;

  if (type === "select") {
    const sel = document.createElement("select");
    (options || []).forEach(o => {
      const opt = document.createElement("option");
      opt.value = o; opt.textContent = o;
      if (o === currentVal || o === state.profile[key]) opt.selected = true;
      sel.appendChild(opt);
    });
    el.innerHTML = prefix;
    el.appendChild(sel);
    sel.focus();
    const commit = () => window.commitChipEdit(key, sel.value);
    sel.onchange = commit;
    sel.onblur   = commit;
  } else {
    const inp = document.createElement("input");
    inp.type = "number"; inp.min = "0";
    inp.value = currentVal ?? "";
    inp.style.width = "60px";
    el.innerHTML = prefix;
    el.appendChild(inp);
    inp.focus(); inp.select();
    inp.onblur    = () => window.commitChipEdit(key, inp.value);
    inp.onkeydown = e => {
      if (e.key === "Enter")  { e.preventDefault(); inp.blur(); }
      if (e.key === "Escape") { el.innerHTML = el.dataset.original; el.classList.remove("editing"); }
    };
  }
};

window.commitChipEdit = async (key, val) => {
  const numericKeys = new Set(["team_size","revenue_cr","prior_claims","data_records_mn"]);
  if (val === "" || val == null) return;
  const parsed = numericKeys.has(key) ? Number(val) : val;
  if (numericKeys.has(key) && (!Number.isFinite(parsed) || parsed < 0)) return;
  state.profile[key] = parsed;
  saveDraftFlow();
  applyAssumptionsToProfile();
  await runFlowAnalysis();
};

/* \u2500\u2500\u2500 RESULT HELPERS \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
function renderKPI(label, value) {
  return `
    <div class="kpi-card">
      <div class="kpi-label">${esc(label)}</div>
      <div class="kpi-value">${esc(String(value))}</div>
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
          <div class="premium-card-note">${esc(subtitle)} &nbsp;\u00B7&nbsp; incl. 18% GST</div>
        </div>
        <div class="pricing-totals">
          <div class="kv-row"><span class="kv-key">Net premium</span><span class="kv-val">INR ${esc(quote.net_premium_lakh)}L</span></div>
          <div class="kv-row"><span class="kv-key">GST (18%)</span><span class="kv-val">INR ${esc(quote.gst_lakh)}L</span></div>
          <div class="kv-row"><span class="kv-key">${quote.cover_count} cover${quote.cover_count !== 1 ? "s" : ""}</span><span class="kv-val">INR ${esc(quote.total_sum_insured_cr)}Cr SI</span></div>
          ${quote.bundle_discount_lakh > 0 ? `<div class="kv-row"><span class="kv-key">Bundle discount</span><span class="kv-val" style="color:var(--green,#2e7d32)">\u2212INR ${esc(quote.bundle_discount_lakh)}L</span></div>` : ""}
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

function renderDualPricingPanel(result) {
  const bundleQ = result.bundle_only_pricing_quote;
  const fullQ   = result.pricing_engine_quote;
  const bundleName = result.bundle_match?.name || "Recommended bundle";
  const fullCount  = fullQ?.covers_to_price?.length || fullQ?.cover_count || "";

  if ((!isQuoted(bundleQ) && !isQuoted(fullQ)) || state.quotePanelMode === "edit") {
    state.quotePanelMode = null;
    return renderQuoteInputPanel(fullQ || bundleQ);
  }

  return `
    <div class="pricing-split">
      ${renderPricePanel(bundleQ, "Bundle price", "bundle", bundleName)}
      ${renderPricePanel(fullQ,   "Full recommended cover", "full", `${fullCount ? fullCount + " covers \u2014 " : ""}bundle + critical products`)}
    </div>
    <div style="margin-top:10px;text-align:right;">
      <button class="btn btn-ghost" type="button" onclick="reviseQuoteInputs()">Edit underwriting inputs</button>
    </div>`;
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
  for (const key of (row.aliases || [row.key])) {
    const val = state.profile[key];
    if (val !== undefined && val !== null && val !== "") return val;
  }
  return "";
}

function renderQuoteInputPanel(quote) {
  const fields = quote.required_inputs || [];
  const missing = quote.missing_required_inputs || [];
  const covers = quote.covers_to_price || [];
  // Pre-set boolean fields to false so the default "No" counts as provided
  // without requiring the user to interact with the select first.
  fields.filter(f => f.unit === "yes/no").forEach(f => {
    if (state.profile[f.key] === undefined || state.profile[f.key] === null) {
      state.profile[f.key] = false;
    }
  });
  return `
    <div class="pricing-card">
      <div class="pricing-head">
        <div>
          <div class="premium-card-label">Estimated quote</div>
          <div class="pricing-title">Want to see an estimated quote?</div>
          <div class="premium-card-note">No premium is calculated until you provide the underwriting inputs below. The estimate will use only these submitted values plus the risk assessment already shown.</div>
        </div>
        <div class="pricing-totals">
          <div class="kv-row"><span class="kv-key">Status</span><span class="kv-val">${quote.status === "awaiting_inputs" ? "Waiting for inputs" : "Not requested"}</span></div>
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
          const inputHtml = row.unit === "yes/no"
            ? `<select class="f-select" style="height:36px;font-size:13px;"
                 onchange="setVal('${esc(row.key)}', this.value === 'yes')">
                 <option value="no" ${!val ? "selected" : ""}>No</option>
                 <option value="yes" ${val ? "selected" : ""}>Yes</option>
               </select>`
            : `<input class="f-input" type="number" min="0" step="${row.unit === "count" ? "1" : "0.01"}"
                 value="${esc(String(val))}"
                 oninput="setVal('${esc(row.key)}', Number(this.value))" />`;
          return `
          <label class="quote-input-field">
            <span>${esc(row.label)} ${row.unit && row.unit !== "yes/no" ? `<em>${esc(row.unit)}</em>` : ""}</span>
            ${inputHtml}
            ${row.help ? `<small>${esc(row.help)}</small>` : ""}
          </label>`;
        }).join("")}
      </div>
      ${missing.length ? `<div class="notice" style="margin-top:12px;">Please fill ${missing.length} required input${missing.length > 1 ? "s" : ""} before estimating.</div>` : ""}
      <div style="display:flex;gap:10px;align-items:center;margin-top:16px;flex-wrap:wrap;">
        <button class="btn btn-primary" type="button" onclick="generatePricingEstimate()">Generate estimated quote</button>
        <span id="pricing-estimate-status" style="font-size:12px;color:var(--ink-muted);"></span>
      </div>
    </div>`;
}

async function generatePricingEstimate() {
  const status = $("pricing-estimate-status");
  if (status) status.textContent = "Calculating from submitted inputs...";
  state.profile.quote_requested = true;
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
  }
}

function overallLabel(score) {
  if (score >= 70) return "High exposure \u2014 prioritise critical covers and governance actions now.";
  if (score >= 45) return "Moderate exposure \u2014 buy essentials first and review quarterly.";
  return "Lower exposure \u2014 start with baseline covers and revisit as you scale.";
}

function renderActionBanner(recs) {
  if (!recs?.length) return "";
  const critical = recs.filter(r => r.priority === "Critical").slice(0, 3);
  if (!critical.length) return "";
  return `
    <div class="action-banner">
      <div class="action-banner-title">Buy now \u2014 ${critical.length} critical cover${critical.length>1?"s":""} for your profile</div>
      ${critical.map(r => `
        <div class="action-item-row">
          <span class="action-item-name">${esc(r.name||r.key)}</span>
          ${r.premium ? `<span class="action-price-tag">INR ${r.premium.min_lakh.toFixed(1)}-${r.premium.max_lakh.toFixed(1)}L</span>` : ""}
          <span class="action-why">${esc(r.nudge||"")}</span>
        </div>`).join("")}
    </div>`;
}

function renderScoreBars(scores) {
  return Object.entries(scores)
    .sort((a,b) => b[1]-a[1])
    .map(([name, score]) => {
      const lvl = score >= 70 ? "critical" : score >= 40 ? "watch" : "low";
      const badgeLabel = score >= 70 ? "Critical" : score >= 40 ? "Watch" : "Low";
      return `
        <div class="score-bar-item">
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
    }).join("");
}

const emptyState = (icon, title, sub="") => `
  <div class="empty-state">
    <div class="empty-state-icon">${icon}</div>
    <div class="empty-state-title">${title}</div>
    ${sub ? `<div class="empty-state-sub">${sub}</div>` : ""}
  </div>`;

function renderDriverCards(risks) {
  if (!risks?.length) return emptyState("RISK", "No risk drivers available", "Run the analysis to see your top risk drivers.");
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

function renderProductCards(recs, mapping) {
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
        <div class="product-card-nudge">${esc(p.nudge||"")}</div>
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

function renderBundleHero(bundle, recs) {
  if (!bundle?.name) return `<div class="r-card">${emptyState("PKG", "No bundle matched", "No packaged bundle was a strong enough fit for this profile. Recommended products are listed individually below.")}</div>`;

  const mandatory = bundle.mandatory_covers || [];
  const optional  = bundle.optional_covers  || [];
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

      <div class="bundle-covers-label">Covers included \u2014 ${mandatory.length} mandatory \u00B7 ${optional.length} optional</div>
      <div class="bundle-cover-grid">
        ${coverItems.slice(0, 12).map(({ key, type }) => {
          const blurb = PRODUCT_BLURBS[key] || "";
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
              <div class="product-card-flag">${statusLabel(b)} \u00B7 Rank ${b.rank}</div>
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

function renderV2Insights(result) {
  const isV2 = Boolean(result?.config_version || result?.graduation_map || result?.compliance_flags);
  if (!isV2) return "";
  const revenue = result.revenue_breakdown || [];
  const risk = result.risk_multiplier_breakdown || {};
  const graduation = result.graduation_map || {};
  const stageKey = (result.profile?.funding_stage || "Seed")
    .toLowerCase().replace("+", "").replace(/\s+/g, "_").replace("pre-seed", "seed");
  const path = Array.isArray(graduation) ? graduation : (graduation[stageKey] || graduation.seed || []);
  const triggers = result.regulatory_triggers_fired || [];

  const riskItems = Object.entries(risk)
    .filter(([k, v]) => RISK_FACTOR_LABELS[k] != null && v != null)
    .map(([k, v]) => [RISK_FACTOR_LABELS[k], v]);

  const trajectoryLabel = (t) => ({ up: "Growing market", down: "Declining market", stable: "Stable market" }[t] || t || "");

  return `
    <details class="expander-card" style="margin-top:14px;">
      <summary>Why this was recommended</summary>
      <div class="expander-body">
        <div class="two-col">
          <div>
            <div class="card-label">Bundle fit for your profile</div>
            ${revenue.length ? revenue.slice(0, 3).map(r => `
              <div class="callout-item">
                <strong>${esc(r.bundle || "Bundle")}</strong>
                <span>${r.why ? esc(r.why) : `About ${pct(r.adoption)} of businesses at your stage carry this bundle.`}${r.trajectory ? ` ${esc(trajectoryLabel(r.trajectory))}.` : ""}</span>
              </div>`).join("") : emptyState("-", "No fit data available")}
          </div>
          <div>
            <div class="card-label">Market risk factors for this cover</div>
            ${riskItems.length ? riskItems.map(([label, value]) => `
              <div class="kv-row">
                <span class="kv-key">${esc(label)}</span>
                <span class="kv-val">${pct(value)}</span>
              </div>`).join("") : `<div style="color:var(--ink-faint);font-size:13px;">No risk factor data.</div>`}
          </div>
        </div>
        ${path.length ? `
          <div style="margin-top:18px;">
            <div class="card-label">Your coverage roadmap as you grow</div>
            <div class="timeline">${path.map((p, i) => `
              <div class="timeline-item">
                <div class="tl-dot">${i + 1}</div>
                <div class="tl-time">${esc(p.stage || `Step ${i + 1}`)}</div>
                <div class="tl-name">${esc(p.bundle || p.recommendation || "")}</div>
              </div>`).join("")}</div>
          </div>` : ""}
        ${triggers.length ? `
          <div style="margin-top:18px;">
            <div class="card-label">Why certain covers were flagged for you</div>
            <div class="two-col">
              ${triggers.map(t => `
                <div class="callout-item">
                  <strong>${esc(SIGNAL_LABELS[t.signal] || t.signal || "Trigger")} -> ${esc(t.product || "")}</strong>
                  <span>${t.citation_url
                    ? `<a href="${esc(t.citation_url)}" target="_blank" rel="noopener noreferrer">${esc(t.regulation || t.reg || "")}</a>`
                    : esc(t.regulation || t.reg || "")}</span>
                </div>`).join("")}
            </div>
          </div>` : ""}
      </div>
    </details>`;
}

function renderProductRows(recs, mapping) {
  const byKey = Object.fromEntries((mapping || []).map(r => [r.key, r]));
  if (!recs?.length) return emptyState("PROD", "No products recommended", "The engine found no matching ICICI Lombard products for this profile. Try adjusting your inputs.");
  const appetiteLabels = { good: "Good risk", moderate: "Moderate", bad: "Not preferred", tbd: "Under review" };

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
          </div>
        </div>
        <div class="product-row-nudge">${esc(p.nudge || "")}</div>
        <div class="product-row-right">
          ${p.premium ? `<div class="product-row-premium">INR ${p.premium.min_lakh.toFixed(1)}-${p.premium.max_lakh.toFixed(1)}L</div>
          <div style="font-size:11px;color:var(--ink-faint);text-align:right;">${esc(p.premium.basis)}</div>` : ""}
          <button class="product-row-expand" onclick="toggleProductRow(${i})" title="Expand">&gt;</button>
        </div>
      </div>`;
  }).join("");
}

function renderTimeline(bundles) {
  if (!bundles?.length) return emptyState("TIME", "No timeline data", "Coverage timeline will appear once products are recommended.");
  return bundles.map((b,i) => `
    <div class="timeline-item">
      <div class="tl-dot">${i+1}</div>
      <div class="tl-time">${esc(b.timeline)}</div>
      <div class="tl-name">${esc(b.name)}</div>
      <div class="tl-count">${b.products.length} product${b.products.length!==1?"s":""}</div>
    </div>`).join("");
}

function renderTriggers(triggers) {
  if (!triggers?.length) return emptyState("OK", "No regulatory triggers", "No major regulatory flags were detected for this profile.");
  return triggers.map(t=>`
    <div class="callout-item">
      <strong>${esc(t.name)}</strong>
      <span>${esc(t.detail)}</span>
    </div>`).join("");
}

function renderMitigations(items) {
  if (!items?.length) return emptyState("OK", "No actions required", "No non-insurance mitigation actions were flagged for this profile.");
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

function renderOutreach(prompts, source, error) {
  const entries = Object.entries(prompts||{});
  if (!entries.length) return "";
  const sourceText = source === "gemini"
    ? "AI-generated outreach drafts active."
    : "Using local fallback drafts. Add GEMINI_API_KEY to enable AI-generated drafts.";
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
          const email = `${item.email_subject}\n\n${item.email_body}`;
          return `
            <details class="outreach-item" ${i===0?"open":""}>
              <summary>${esc(labelize(key))}</summary>
              <div class="outreach-body">
                <div>
                  <div class="outreach-col-label">Email</div>
                  <pre>${esc(email)}</pre>
                  <button class="btn btn-ghost" style="height:36px;padding:0 14px;font-size:12px;margin-top:8px;" data-copy="${esc(email)}">Copy email</button>
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
                Estimated potential: INR ${o.total_opportunity_lakhs_min} \u2013 ${o.total_opportunity_lakhs_max} lakhs
              </div>` : ""}
          </div>`).join("")}
      </div>
    </div>`;
}

function renderGlobalProducts(products) {
  if (!products?.length) return emptyState("GLOB", "No global benchmarks", "No global product comparisons matched this profile.");
  const statusLabels = { icici:"ICICI Lombard", india_competitor:"Indian market", not_in_india:"Global only" };
  return products.map(p=>`
    <div class="product-card ${p.label==='not_in_india'?'innovation-card':''}">
      <div class="product-card-flag" style="color:var(--ink-faint);">${p.match_basis==='nearest_risk' ? "Nearest benchmark" : (statusLabels[p.label]||"Global")}</div>
      <div class="product-card-name">${esc(p.name)} <span class="product-tag score">${p.relevance_score}/100</span></div>
      <div class="product-card-desc">${esc(p.what_it_covers||"")}</div>
      <div style="font-size:12px;color:var(--ink-muted);">Providers: ${esc(p.providers||"")}</div>
      ${p.label==='not_in_india'?`<p class="notice" style="margin-top:8px;">Product innovation opportunity \u2014 flag to product team.</p>`:""}
    </div>`).join("");
}

function renderBreakdown(items) {
  if (!items?.length) return emptyState("CFG", "No multipliers applied", "No dynamic score multipliers were material for this profile.");
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
          <div style="font-size:12px;color:var(--ink-faint);margin-top:4px;">IRDAI path: ${esc(t.irdai_path||"")} \u00B7 Market: ${esc(t.estimated_market_size||"")}</div>
        </div>`).join("")}
    </div>`;
}

/* \u2500\u2500\u2500 REFINE PANEL \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
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
      <div class="adv-checks">${mkCheck("sdf_likely","DPDP Act \u00A710 Significant Data Fiduciary designation likely")}</div>
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
      runBtn.textContent = "Recalculating\u2026";
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

/* \u2500\u2500\u2500 DOWNLOAD \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
window.downloadReport = function(result) {
  if (!result) return;
  const lines = [
    `SPARC Risk Report \u2014 ${result.profile.startup_name}`,
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
    ...(result.top_risks||[]).map(r => `  \u00B7 ${r.name}: ${r.score}/100`),
    "",
    "RECOMMENDATIONS:",
    ...(result.recommendations||[]).map(p => `  \u00B7 ${p.name||p.key}: ${p.priority} (${p.score}/100)`),
    "",
    "MITIGATION ACTIONS:",
    ...(result.mitigations||[]).map(m => `  \u00B7 ${m.risk}: ${m.action}`),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `${(result.profile.startup_name||"startup").replace(/\s+/g,"-")}-sparc-report.txt`;
  a.click();
  URL.revokeObjectURL(url);
};

/* \u2500\u2500\u2500 RADAR CHART \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
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
  ctx.font = "10px 'Inter', sans-serif";
  ctx.textAlign = "center"; ctx.textBaseline = "middle";
  entries.forEach(([label], i) => {
    const angle = -Math.PI/2 + i * 2*Math.PI / entries.length;
    const x = cx + Math.cos(angle)*R, y = cy + Math.sin(angle)*R;
    ctx.beginPath(); ctx.moveTo(cx,cy); ctx.lineTo(x,y);
    ctx.strokeStyle = "#E2E2DC"; ctx.lineWidth = 1; ctx.stroke();
    const lx = cx + Math.cos(angle)*(R+28), ly = cy + Math.sin(angle)*(R+28);
    ctx.fillStyle = "#94A3B8";
    const short = label.length > maxLen ? label.slice(0, maxLen-1)+"\u2026" : label;
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

/* \u2500\u2500\u2500 KICK OFF \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 */
window.renderFlow = renderFlow;
init();

