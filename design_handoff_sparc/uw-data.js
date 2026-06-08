// Underwriter workbench seed data — cases assigned to current UW.
// All names/numbers are illustrative for prototype purposes.

window.UW_DESK = {
  user: { name: "A. Sharma", id: "UW-07" },
  capacity: "₹ 80 Cr / year",
  utilization: 0.62,
  queueDate: new Date().toLocaleDateString("en-GB", { day: "numeric", month: "short" }),
};

// Loadings and exclusions catalogue (UW can apply)
window.UW_LOADINGS = [
  { id: "geo_us",          label: "US/NJ exposure",         pct: 12 },
  { id: "no_retro",        label: "Retro date open",        pct: 8 },
  { id: "ai_in_prod",      label: "AI in product",          pct: 6 },
  { id: "high_growth",     label: "High growth volatility", pct: 5 },
  { id: "first_time",      label: "First-time insured",     pct: 4 },
];

window.UW_DISCOUNTS = [
  { id: "bundle",          label: "Bundle discount",        pct: -8 },
  { id: "long_term",       label: "3-year commitment",      pct: -5 },
  { id: "risk_mgmt",       label: "ISO 27001 certified",    pct: -4 },
  { id: "no_claims",       label: "No prior claims 5yr",    pct: -3 },
];

// Pre-flight checks template
window.UW_CHECKS = [
  { id: "sanctions",  label: "Sanctions screening (OFAC/UN/MHA)", auto: true,  status: "pass" },
  { id: "kyc",        label: "KYC documents on file",             status: "partial", note: "2 of 3 received" },
  { id: "aggregate",  label: "Sector aggregate exposure",         status: "pass", note: "62% of cap used" },
  { id: "retro",      label: "Retro date confirmation",           status: "open", note: "Founder declaration required" },
  { id: "claims",     label: "Prior claims declaration (5 yr)",   status: "pass", note: "Nil declared" },
  { id: "referral",   label: "Senior UW referral",                status: "na",   note: "SI below referral threshold" },
];

// Queue — 7 cases pending this UW today
window.UW_QUEUE = [
  {
    caseId: "SPARC-2401", company: "Razorpay",        rm: "A. Mehta",   rmInitials: "AM",
    sla: 134,  /* minutes remaining */ slaTotal: 240, priority: "high",
    submittedAgo: "just now",  bundle: "Digital Business Shield", indicative: 14.2,
    status: "pending-uw", flagged: ["RBI regulated", "Cross-border"],
  },
  {
    caseId: "SPARC-2398", company: "Niramai",         rm: "K. Patel",   rmInitials: "KP",
    sla: 302, slaTotal: 480, priority: "med",
    submittedAgo: "2h ago",  bundle: "Business Shield SME", indicative: 3.8,
    status: "pending-uw", flagged: ["Health data", "AI in product"],
  },
  {
    caseId: "SPARC-2394", company: "Ather Energy",    rm: "R. Iyer",    rmInitials: "RI",
    sla: 420, slaTotal: 720, priority: "med",
    submittedAgo: "5h ago",  bundle: "Industrial All Risk", indicative: 28.6,
    status: "pending-docs", flagged: ["Hardware"],
  },
  {
    caseId: "SPARC-2389", company: "BrowserStack",    rm: "S. Roy",     rmInitials: "SR",
    sla: 620, slaTotal: 720, priority: "low",
    submittedAgo: "yesterday",  bundle: "Digital Business Shield", indicative: 9.1,
    status: "pending-uw", flagged: ["Cross-border"],
  },
  {
    caseId: "SPARC-2386", company: "Sarvam AI",       rm: "P. Nair",    rmInitials: "PN",
    sla: 90,  slaTotal: 240, priority: "high",
    submittedAgo: "30m ago", bundle: "Digital Business Shield", indicative: 1.9,
    status: "pending-uw", flagged: ["AI in product", "First-time"],
  },
  {
    caseId: "SPARC-2381", company: "Rebel Foods",     rm: "V. Desai",   rmInitials: "VD",
    sla: 1410, slaTotal: 1440, priority: "low",
    submittedAgo: "yesterday", bundle: "MSME Continuity Pack", indicative: 6.4,
    status: "pending-uw", flagged: ["Food safety"],
  },
  {
    caseId: "SPARC-2378", company: "Cred",            rm: "A. Mehta",   rmInitials: "AM",
    sla: 220, slaTotal: 720, priority: "med",
    submittedAgo: "4h ago", bundle: "Corporate Cover II", indicative: 11.7,
    status: "referred", flagged: ["RBI regulated"],
  },
];

// Similar comparable cases — anchor pricing decisions
window.UW_COMPARABLES = {
  "Razorpay": [
    { company: "Cred",       sector: "Fintech",  stage: "Series B+", premium: 12.4, loading: "+8%", outcome: "Approved", date: "Mar 2026" },
    { company: "Slice",      sector: "Fintech",  stage: "Series B+", premium: 13.1, loading: "+10%", outcome: "Approved", date: "Feb 2026" },
    { company: "Jupiter",    sector: "Fintech",  stage: "Series A",  premium: 8.2,  loading: "+4%", outcome: "Approved", date: "Jan 2026" },
  ],
  "Niramai": [
    { company: "DocsApp",    sector: "Healthtech", stage: "Series A", premium: 3.2,  loading: "+6%", outcome: "Approved", date: "Apr 2026" },
    { company: "Pristyn",    sector: "Healthtech", stage: "Series B+", premium: 6.8, loading: "+5%", outcome: "Approved", date: "Feb 2026" },
    { company: "HealthifyMe", sector: "Healthtech", stage: "Series B+", premium: 4.1, loading: "+3%", outcome: "Approved", date: "Jan 2026" },
  ],
  "Ather Energy": [
    { company: "Ola Electric", sector: "Mobility", stage: "Pre-IPO", premium: 32.1, loading: "+12%", outcome: "Approved", date: "Mar 2026" },
    { company: "Yulu",         sector: "Mobility", stage: "Series B+", premium: 8.4, loading: "+6%", outcome: "Approved", date: "Jan 2026" },
  ],
};

// Per-risk driving signals — UW needs to see WHY each score is what it is
window.riskSignals = function (profile, scores) {
  const flags = new Set(profile.flags || []);
  const team = +profile.team || 0;
  const records = +profile.records || 0;
  const out = {};

  const all = {
    cyber: [
      ["Sector profile", `${profile.sector} sector base rate`],
      flags.has("Processes payments") && ["Payment flows", "Cardholder data + PCI-DSS scope"],
      flags.has("Stores health data") && ["Sensitive data", "Health records on file"],
      records > 1_000_000 && ["Record volume", `${(records/1_000_000).toFixed(1)}M customer records`],
      flags.has("Cross-border ops") && ["Geo exposure", "Cross-border data transfers"],
    ],
    dno: [
      profile.equity && ["Equity round", `Outside investors active at ${profile.stage}`],
      profile.listed && ["Listed", "Public-market exposure"],
      ["Stage signal", `${profile.stage} typical D&O floor`],
      flags.has("RBI regulated") && ["Regulator action risk", "RBI-supervised entity"],
    ],
    pi: [
      ["Customer model", profile.model],
      ["Sector", `${profile.sector} contract risk`],
      flags.has("AI in product") && ["AI output liability", "Model output / accuracy claims"],
      team > 100 && ["Delivery scale", `${team} people in delivery`],
    ],
    privacy: [
      flags.has("DPDP fiduciary") && ["DPDP role", "Designated data fiduciary"],
      records > 1_000_000 && ["Record volume", `${(records/1_000_000).toFixed(1)}M records crosses SDF threshold`],
      flags.has("Stores health data") && ["Sensitive category", "Health = SPDI under DPDP"],
      flags.has("Cross-border ops") && ["Data localisation", "Cross-border transfer rules"],
    ],
    ip: [
      flags.has("AI in product") && ["Model IP", "Training-data and output disputes rising"],
      ["Sector", `${profile.sector} IP-litigation base rate`],
      team > 50 && ["Headcount", "Engineering team scale increases trade-secret exposure"],
    ],
    crime: [
      flags.has("Processes payments") && ["Payment ops", "Insider fraud risk on settlements"],
      team > 200 && ["Headcount", `${team} employees = scale fraud exposure`],
      ["Stage", `${profile.stage} typical control maturity`],
    ],
    property: [
      profile.model === "Hardware + Software" && ["Asset class", "Physical inventory + plant"],
      profile.model === "Hybrid" && ["Mixed model", "Some physical premises and inventory"],
      ["Stage", `${profile.stage} premises footprint`],
    ],
    bi: [
      ["Revenue dependency", "Monthly burn × downtime tolerance"],
      profile.model !== "Pure SaaS / API" && ["Model", "Physical operations create stoppage exposure"],
      ["Stage", `${profile.stage} cash position`],
    ],
    public: [
      profile.model === "Hardware + Software" && ["Premises", "Customer / vendor site visits"],
      profile.model === "Marketplace" && ["Marketplace", "Third-party interactions at scale"],
      team > 100 && ["Headcount", "Office footprint scales with team"],
    ],
    product: [
      profile.model === "Hardware + Software" && ["Product type", "Physical product → product liability"],
      ["Sector", `${profile.sector} product-recall base rate`],
    ],
    wc: [
      team > 100 && ["Headcount", `${team} employees`],
      profile.model === "Hardware + Software" && ["Operations", "Manufacturing / field workers"],
      ["Stage", `${profile.stage} typical workforce composition`],
    ],
    epli: [
      team > 200 && ["Headcount", `${team} employees = elevated EPLI exposure`],
      profile.stage === "Series B+" && ["Stage", "Post-Series B reorg / RIF risk"],
      ["Sector", `${profile.sector} EPLI base rate`],
    ],
    key: [
      ["Founder dependency", `${profile.stage} typical key-person concentration`],
      team < 50 && ["Small team", "Founder == institutional knowledge"],
      flags.has("AI in product") && ["Technical co-founder", "Specialist talent at risk"],
    ],
  };

  Object.keys(all).forEach((k) => {
    out[k] = all[k].filter(Boolean).slice(0, 3).map(([label, detail]) => ({ label, detail }));
    // Always have 1 signal at minimum
    if (out[k].length === 0) out[k] = [{ label: "Portfolio base rate", detail: `${profile.sector} default` }];
  });

  return out;
};

// Pricing assumptions — for the UW transparency panel
window.pricingAssumptions = function (profile) {
  const userSupplied = ["sector", "stage", "team", "revenue", "model", "records", "flags"]
    .filter((k) => profile[k] !== "" && profile[k] != null && (Array.isArray(profile[k]) ? profile[k].length > 0 : true));

  const rows = [];
  rows.push({ label: "Sector classification", value: profile.sector, source: "user", inferred: false });
  rows.push({ label: "Funding stage",         value: profile.stage,  source: "user", inferred: false });
  rows.push({ label: "Headcount",             value: `${profile.team} people`, source: "user", inferred: false });
  rows.push({ label: "Operating model",       value: profile.model || "—", source: profile.model ? "user" : "inferred", inferred: !profile.model });
  rows.push({ label: "Annual revenue",        value: profile.revenue ? `₹ ${profile.revenue} Cr` : `≈ ₹ ${Math.round((+profile.team || 0) * 0.25)} Cr (team-scaled)`, source: profile.revenue ? "user" : "estimated", inferred: !profile.revenue });
  rows.push({ label: "Customer records held", value: profile.records ? `${(profile.records/1_000_000).toFixed(1)}M` : `≈ ${(((+profile.team || 0) * 5000)/1_000_000).toFixed(1)}M (team-scaled)`, source: profile.records ? "user" : "estimated", inferred: !profile.records });
  rows.push({ label: "Regulatory flags",      value: (profile.flags || []).length ? (profile.flags || []).join(", ") : "None declared", source: "user", inferred: false });
  rows.push({ label: "Equity-backed",         value: profile.equity ? "Yes" : "No", source: profile.equity != null ? "user" : "default", inferred: false });
  rows.push({ label: "Publicly listed",       value: profile.listed ? "Yes" : "No", source: profile.listed != null ? "user" : "default", inferred: false });
  rows.push({ label: "Climate-risk zone",     value: "Low (default)", source: "default", inferred: true });
  return rows;
};

// Regulatory rule references
window.REG_RULES = {
  dpdp: {
    name: "DPDP Act, 2023",
    section: "§10 — Significant Data Fiduciary",
    refLine: "Designation criteria based on data volume, sensitivity, and risk of harm.",
  },
  rbi_outsourcing: {
    name: "RBI Master Direction",
    section: "Outsourcing — Annex 4",
    refLine: "Reporting obligations for material outsourcing & cyber incidents.",
  },
  rbi_dpsp: {
    name: "RBI Digital Payment Security Controls",
    section: "Master Direction (Apr 2021)",
    refLine: "Card data segregation, incident reporting within 6 hours.",
  },
  pci_dss: {
    name: "PCI-DSS v4.0",
    section: "Req. 3 / Req. 12",
    refLine: "Cardholder data protection scope; quarterly attestation.",
  },
  cert_in: {
    name: "CERT-In Directions (2022)",
    section: "Cyber incident reporting",
    refLine: "Mandatory 6-hour incident reporting; log retention 180 days.",
  },
  ai_acc: {
    name: "IT Rules + DPDP",
    section: "Algorithmic accountability",
    refLine: "Output liability, training-data provenance, redress mechanisms.",
  },
};

window.detectRegTriggers = function (profile) {
  const triggers = [];
  const flags = new Set(profile.flags || []);
  const records = +profile.records || 0;

  if (records > 1_000_000 && flags.has("DPDP fiduciary")) {
    triggers.push({
      key: "dpdp_sdf", severity: "high", ruleKey: "dpdp",
      title: "Significant Data Fiduciary obligations",
      finding: `${(records/1_000_000).toFixed(1)}M records crosses the volume threshold typically used by the Board.`,
      action: "Privacy response cover strongly indicated; appoint DPO.",
    });
  }
  if (flags.has("RBI regulated")) {
    triggers.push({
      key: "rbi_outsourcing", severity: "high", ruleKey: "rbi_outsourcing",
      title: "RBI outsourcing & cyber incident reporting",
      finding: "RBI-supervised entity — reporting timelines and continuity obligations apply.",
      action: "Cyber + BI cover with incident-response SLA. Coordinate with CISO.",
    });
  }
  if (flags.has("Processes payments")) {
    triggers.push({
      key: "pci", severity: "med", ruleKey: "pci_dss",
      title: "PCI-DSS scope",
      finding: "Card data flows present. Scope determines required controls.",
      action: "Confirm tokenisation status; crime + cyber cover with PCI fines extension.",
    });
    triggers.push({
      key: "rbi_dpsp", severity: "med", ruleKey: "rbi_dpsp",
      title: "Digital payment security controls",
      finding: "Reporting and segregation obligations on payment data.",
      action: "Incident-response retainer recommended.",
    });
  }
  if (flags.has("AI in product")) {
    triggers.push({
      key: "ai", severity: "med", ruleKey: "ai_acc",
      title: "Algorithmic accountability",
      finding: "AI in production — output liability and training-data provenance under scrutiny.",
      action: "IP defence cover + extend PI to include model output.",
    });
  }
  if (flags.has("Cross-border ops") || flags.has("Stores health data")) {
    triggers.push({
      key: "cert_in", severity: "low", ruleKey: "cert_in",
      title: "CERT-In cyber incident reporting",
      finding: "Cross-border or sensitive-category data flows in scope.",
      action: "Confirm log retention and 6-hour reporting capability.",
    });
  }

  return triggers;
};

// Inputs needed before firm quote
window.inputsForFirmQuote = function (profile) {
  const needs = [
    { id: "fin",      label: "Last 2 audited financials",       reason: "Final SI calibration and BI cover sizing", critical: true },
    { id: "iso",      label: "ISO 27001 / SOC 2 certificate",   reason: "10% cyber rate discount if produced",     critical: false },
    { id: "captable", label: "Cap table & KMP declarations",    reason: "Required for D&O retro and Side-A",       critical: true },
    { id: "prior",    label: "Prior policy schedules (3 yr)",   reason: "Continuity, sub-limits, exclusions",      critical: true },
    { id: "loss",     label: "Loss-run reports (5 yr)",         reason: "Claims-history loading and credibility",  critical: true },
    { id: "ir",       label: "Incident response retainer letter", reason: "Cyber + privacy bundle prerequisite",  critical: false },
  ];
  if ((+profile.records || 0) > 1_000_000) {
    needs.push({ id: "dpo", label: "DPO appointment letter", reason: "DPDP SDF threshold crossed", critical: true });
  }
  if ((profile.flags || []).includes("AI in product")) {
    needs.push({ id: "ai_doc", label: "Model card / accuracy documentation", reason: "Algorithmic accountability extension", critical: false });
  }
  return needs;
};

// Get a quick result for a queue case — same engine as RM
window.uwGetCase = function (queueItem) {
  const company = window.COMPANIES.find((c) => c.name === queueItem.company);
  if (!company) return null;
  const result = window.runAnalysis(company);
  // Spread queueItem first so queueItem.company (string) doesn't clobber the company object
  return { ...queueItem, company, result };
};
