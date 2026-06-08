// SPARC seed data — companies, sectors, bundles, risk dimensions
// All data is illustrative for prototype purposes.

window.SECTORS = [
  "Fintech",
  "Healthtech",
  "SaaS / B2B",
  "Deeptech / AI",
  "Edtech",
  "D2C / E-commerce",
  "Logistics / Mobility",
  "Climate / Energy",
  "Foodtech",
  "Other",
];

window.STAGES = ["Pre-seed", "Seed", "Series A", "Series B+", "Pre-IPO"];

window.MODELS = [
  "Pure SaaS / API",
  "Marketplace",
  "Hardware + Software",
  "Services + Tech",
  "Hybrid",
];

window.REG_FLAGS = [
  "RBI regulated",
  "SEBI regulated",
  "IRDAI regulated",
  "Processes payments",
  "Stores health data",
  "Cross-border ops",
  "DPDP fiduciary",
  "AI in product",
];

// Seeded startup database — pre-fills the entire form on selection
window.COMPANIES = [
  { name: "Razorpay", sector: "Fintech", stage: "Series B+", team: 3200, revenue: 2400, model: "Pure SaaS / API", records: 28000000, equity: true, listed: false, flags: ["RBI regulated", "Processes payments", "DPDP fiduciary", "Cross-border ops"] },
  { name: "Practo", sector: "Healthtech", stage: "Series B+", team: 850, revenue: 380, model: "Hybrid", records: 12500000, equity: true, listed: false, flags: ["Stores health data", "DPDP fiduciary"] },
  { name: "Freshworks", sector: "SaaS / B2B", stage: "Pre-IPO", team: 5400, revenue: 5800, model: "Pure SaaS / API", records: 8200000, equity: true, listed: true, flags: ["DPDP fiduciary", "Cross-border ops", "AI in product"] },
  { name: "Zepto", sector: "D2C / E-commerce", stage: "Series B+", team: 4200, revenue: 4600, model: "Hybrid", records: 18000000, equity: true, listed: false, flags: ["DPDP fiduciary", "Processes payments"] },
  { name: "Cred", sector: "Fintech", stage: "Series B+", team: 950, revenue: 1400, model: "Pure SaaS / API", records: 11200000, equity: true, listed: false, flags: ["RBI regulated", "Processes payments", "DPDP fiduciary"] },
  { name: "Postman", sector: "SaaS / B2B", stage: "Series B+", team: 760, revenue: 1200, model: "Pure SaaS / API", records: 4200000, equity: true, listed: false, flags: ["DPDP fiduciary", "Cross-border ops"] },
  { name: "Niramai", sector: "Healthtech", stage: "Series A", team: 95, revenue: 24, model: "Hardware + Software", records: 380000, equity: true, listed: false, flags: ["Stores health data", "DPDP fiduciary", "AI in product"] },
  { name: "Ather Energy", sector: "Climate / Energy", stage: "Pre-IPO", team: 2200, revenue: 1800, model: "Hardware + Software", records: 620000, equity: true, listed: false, flags: ["DPDP fiduciary"] },
  { name: "Shiprocket", sector: "Logistics / Mobility", stage: "Series B+", team: 1800, revenue: 1200, model: "Services + Tech", records: 22000000, equity: true, listed: false, flags: ["DPDP fiduciary", "Processes payments"] },
  { name: "BrowserStack", sector: "SaaS / B2B", stage: "Series B+", team: 1100, revenue: 960, model: "Pure SaaS / API", records: 3400000, equity: true, listed: false, flags: ["DPDP fiduciary", "Cross-border ops"] },
  { name: "Rebel Foods", sector: "Foodtech", stage: "Series B+", team: 3400, revenue: 1600, model: "Hybrid", records: 8200000, equity: true, listed: false, flags: ["DPDP fiduciary"] },
  { name: "Sarvam AI", sector: "Deeptech / AI", stage: "Series A", team: 80, revenue: 12, model: "Pure SaaS / API", records: 1400000, equity: true, listed: false, flags: ["AI in product", "DPDP fiduciary", "Cross-border ops"] },
];

// 13 risk dimensions — the visual grid in results
window.RISK_DIMENSIONS = [
  { key: "cyber",       label: "Cyber & data breach",     short: "Cyber" },
  { key: "dno",         label: "D&O liability",            short: "D&O" },
  { key: "pi",          label: "Professional indemnity",   short: "PI/E&O" },
  { key: "privacy",     label: "Data privacy / DPDP",      short: "Privacy" },
  { key: "ip",          label: "IP infringement",          short: "IP" },
  { key: "crime",       label: "Crime / fidelity",         short: "Crime" },
  { key: "property",    label: "Property / fire",          short: "Property" },
  { key: "bi",          label: "Business interruption",    short: "BI" },
  { key: "public",      label: "Public liability",         short: "Public" },
  { key: "product",     label: "Product liability",        short: "Product" },
  { key: "wc",          label: "Employee comp",            short: "WC" },
  { key: "epli",        label: "Employment practices",     short: "EPLI" },
  { key: "key",         label: "Key person",               short: "Key" },
];

// Bundle catalog — minimal set for the prototype
window.BUNDLES = {
  business_shield_sme: {
    id: "business_shield_sme",
    name: "Digital Business Shield",
    tagline: "Liability-first cover for digital-native teams",
    mandatory: ["cyber", "dno", "pi"],
    optional: ["crime", "epli", "key"],
    sectors: ["SaaS / B2B", "Fintech", "Healthtech", "Edtech", "Deeptech / AI"],
    stages: ["Seed", "Series A", "Series B+"],
  },
  corporate_cover_ii: {
    id: "corporate_cover_ii",
    name: "Corporate Cover II",
    tagline: "Growth-stage package for asset-light operators",
    mandatory: ["property", "bi", "public", "wc"],
    optional: ["cyber", "dno", "pi", "crime"],
    sectors: ["SaaS / B2B", "Fintech", "Healthtech", "D2C / E-commerce"],
    stages: ["Series A", "Series B+"],
  },
  msme_kavach: {
    id: "msme_kavach",
    name: "MSME Continuity Pack",
    tagline: "Foundational physical + liability cover for early operations",
    mandatory: ["property", "bi", "crime"],
    optional: ["cyber", "public", "wc", "product"],
    sectors: ["D2C / E-commerce", "Foodtech", "Logistics / Mobility", "Climate / Energy"],
    stages: ["Pre-seed", "Seed", "Series A"],
  },
  industrial_all_risk: {
    id: "industrial_all_risk",
    name: "Industrial All Risk",
    tagline: "Heavy-asset cover for hardware and supply chains",
    mandatory: ["property", "bi", "product", "public"],
    optional: ["cyber", "crime", "wc"],
    sectors: ["Climate / Energy", "Logistics / Mobility", "Foodtech"],
    stages: ["Series A", "Series B+", "Pre-IPO"],
  },
};

// Per-cover premium model — used to estimate quote
window.COVER_META = {
  cyber:    { label: "Cyber Liability",        siDefault: 50,  rate: 0.0085 },
  dno:      { label: "D&O Liability",          siDefault: 25,  rate: 0.0120 },
  pi:       { label: "Professional Indemnity", siDefault: 30,  rate: 0.0095 },
  crime:    { label: "Crime & Fidelity",       siDefault: 10,  rate: 0.0070 },
  epli:     { label: "Employment Practices",   siDefault: 8,   rate: 0.0060 },
  key:      { label: "Key Person",             siDefault: 15,  rate: 0.0080 },
  property: { label: "Property / Fire",        siDefault: 20,  rate: 0.0040 },
  bi:       { label: "Business Interruption",  siDefault: 15,  rate: 0.0055 },
  public:   { label: "Public Liability",       siDefault: 10,  rate: 0.0050 },
  product:  { label: "Product Liability",      siDefault: 12,  rate: 0.0065 },
  wc:       { label: "Workers Comp",           siDefault: 5,   rate: 0.0035 },
  privacy:  { label: "Privacy Response",       siDefault: 8,   rate: 0.0072 },
  ip:       { label: "IP Defence",             siDefault: 10,  rate: 0.0090 },
};

// --- Deterministic analysis: produce a stable, profile-aware recommendation ---
window.runAnalysis = function (profile) {
  const flags = new Set(profile.flags || []);
  const scores = {};

  // Heuristic scoring per risk dimension based on profile signals
  const base = {
    cyber:    20, dno: 20, pi: 20, privacy: 20, ip: 20, crime: 20,
    property: 20, bi: 20, public: 20, product: 20, wc: 20, epli: 20, key: 20,
  };

  // Stage adds
  const stageBoost = { "Pre-seed": 0, "Seed": 8, "Series A": 16, "Series B+": 28, "Pre-IPO": 36 }[profile.stage] || 10;
  Object.keys(base).forEach((k) => (base[k] += Math.round(stageBoost * 0.4)));
  base.dno += stageBoost;
  base.epli += Math.round(stageBoost * 0.6);
  base.key += Math.round(stageBoost * 0.5);

  // Sector signals
  const s = profile.sector;
  if (["Fintech", "Healthtech", "SaaS / B2B", "Deeptech / AI", "Edtech"].includes(s)) {
    base.cyber += 28; base.privacy += 24; base.pi += 22; base.ip += 14;
  }
  if (["D2C / E-commerce", "Foodtech", "Logistics / Mobility", "Climate / Energy"].includes(s)) {
    base.property += 22; base.bi += 18; base.public += 14; base.product += 16; base.wc += 12;
  }
  if (s === "Healthtech") base.privacy += 14;
  if (s === "Deeptech / AI") base.ip += 18;

  // Flag signals
  if (flags.has("Processes payments")) { base.cyber += 14; base.crime += 16; }
  if (flags.has("Stores health data")) { base.privacy += 18; base.cyber += 8; }
  if (flags.has("RBI regulated") || flags.has("SEBI regulated") || flags.has("IRDAI regulated")) {
    base.dno += 12; base.crime += 8;
  }
  if (flags.has("DPDP fiduciary")) base.privacy += 12;
  if (flags.has("AI in product")) { base.ip += 12; base.pi += 8; }
  if (flags.has("Cross-border ops")) { base.privacy += 8; base.dno += 6; }

  // Team / revenue / records signals
  const team = +profile.team || 0;
  const records = +profile.records || 0;
  if (team > 500) base.epli += 18, base.wc += 14;
  else if (team > 100) base.epli += 10, base.wc += 8;
  if (records > 1_000_000) base.privacy += 12;
  if (records > 10_000_000) base.privacy += 14;
  if (profile.equity) base.dno += 6;
  if (profile.listed) base.dno += 14;

  // Operating model
  if (profile.model === "Hardware + Software") { base.property += 16; base.product += 14; }
  if (profile.model === "Marketplace") { base.pi += 8; base.public += 6; }

  // Clamp 0..100
  Object.keys(base).forEach((k) => (scores[k] = Math.max(8, Math.min(98, base[k]))));

  // Overall = weighted average emphasizing top 5 risks
  const sorted = Object.values(scores).sort((a, b) => b - a);
  const overall = Math.round((sorted.slice(0, 5).reduce((a, b) => a + b, 0) / 5) * 0.7 + (sorted.reduce((a, b) => a + b, 0) / sorted.length) * 0.3);

  // Bundle choice — pick the one whose mandatory covers have highest average score
  let best = null, bestScore = -1, alternatives = [];
  Object.values(window.BUNDLES).forEach((b) => {
    const avg = b.mandatory.reduce((sum, k) => sum + (scores[k] || 30), 0) / b.mandatory.length;
    const sectorBonus = b.sectors.includes(profile.sector) ? 10 : 0;
    const stageBonus = b.stages.includes(profile.stage) ? 8 : 0;
    const total = avg + sectorBonus + stageBonus;
    alternatives.push({ bundle: b, total, avg });
    if (total > bestScore) { bestScore = total; best = b; }
  });
  alternatives.sort((a, b) => b.total - a.total);
  const alt = alternatives.slice(1, 4).map((a) => ({
    ...a.bundle,
    rejectReason: !a.bundle.sectors.includes(profile.sector)
      ? `Optimised for ${a.bundle.sectors[0]} — partial sector fit`
      : !a.bundle.stages.includes(profile.stage)
      ? `Designed for ${a.bundle.stages.join(" / ")} stage profile`
      : `Lower coverage match on top risks (${Math.round(a.avg)}/100 avg)`,
  }));

  // Quote estimate
  const revenue = +profile.revenue || (team * 25); // crude fallback
  const sizeFactor = Math.max(0.6, Math.min(2.4, Math.log10(Math.max(1, revenue)) / 2.5));
  const covers = [...best.mandatory, ...best.optional.slice(0, 2)];
  const quote = covers.map((k) => {
    const meta = window.COVER_META[k];
    const si = meta.siDefault * (0.6 + Math.random() * 0.4);
    const premium = si * meta.rate * sizeFactor * 100; // in lakhs
    return { key: k, label: meta.label, si: Math.round(si), premium: Math.round(premium * 100) / 100, mandatory: best.mandatory.includes(k) };
  });
  const subtotal = quote.reduce((a, b) => a + b.premium, 0);
  const discount = subtotal * 0.08;
  const gst = (subtotal - discount) * 0.18;
  const total = subtotal - discount + gst;

  // Rationale — 3 lines, plain English
  const topRisks = Object.entries(scores).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k]) => k);
  const topRiskLabels = topRisks.map((k) => window.RISK_DIMENSIONS.find((r) => r.key === k)?.short).filter(Boolean);
  const rationale = [
    `${profile.name || "This startup"} shows elevated exposure on ${topRiskLabels.slice(0, 2).join(" and ")} — the bundle's mandatory covers address both directly.`,
    `${profile.stage} ${profile.sector.toLowerCase()} businesses with ${team.toLocaleString()} team and ${(records / 1_000_000).toFixed(1)}M records typically need this exact combination of financial-line and operational covers.`,
    `Two optional add-ons are pre-staged based on regulatory flags — review and confirm before quoting.`,
  ];

  // Regulatory triggers
  const triggers = [];
  if (records > 1_000_000 && flags.has("DPDP fiduciary")) triggers.push({ label: "DPDP Significant Data Fiduciary", note: "Records volume exceeds threshold — privacy response cover strongly indicated." });
  if (flags.has("RBI regulated")) triggers.push({ label: "RBI directions on outsourcing & cyber", note: "Cyber incident reporting timelines apply." });
  if (flags.has("Processes payments")) triggers.push({ label: "PCI-DSS scope", note: "Card data flows trigger crime + cyber exposure." });
  if (flags.has("AI in product")) triggers.push({ label: "IP & algorithmic accountability", note: "Add IP defence — model output liability is rising." });

  // Outreach email
  const email = {
    subject: `${profile.name || "Your"} — proposed insurance bundle and next steps`,
    body: [
      `Hi ${(profile.name || "Founder").split(" ")[0]} team,`,
      ``,
      `We've put together an initial protection bundle tailored to ${profile.name || "your operations"}. Three things worth your attention:`,
      ``,
      `1. Your top exposures right now are ${topRiskLabels.join(", ")}. Standard for ${profile.sector} at ${profile.stage}, but worth structuring cover before your next round / audit.`,
      `2. We're recommending the ${best.name} package — it solves the top three risks in one policy and is priced for your stage.`,
      `3. Estimated annual premium sits at ~₹${Math.round(total).toLocaleString()} L (inclusive of GST). This is indicative; final pricing needs an underwriter call.`,
      ``,
      `Happy to walk through this on a 20-min call. Reply with two slots this week.`,
      ``,
      `Best,`,
      `Your RM`,
    ].join("\n"),
  };

  return {
    overall,
    tier: overall >= 70 ? "High" : overall >= 50 ? "Moderate" : "Low",
    scores,
    bundle: best,
    alternatives: alt,
    quote: { lines: quote, subtotal, discount, gst, total },
    rationale,
    triggers,
    email,
    topRisks: topRiskLabels,
  };
};
