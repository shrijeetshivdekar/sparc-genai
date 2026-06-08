// Founder view — extremely minimal, plain-English.
// 5-field intake → 3 reassuring result screens.

const { useState: useSf, useMemo: useMf, useEffect: useEf } = React;

// ── Plain-English translations ────────────────────────────────────────
const RISK_PLAIN = {
  cyber:    { head: "Your data is a target", sentence: "Hackers go after digital businesses that hold customer info or process payments. A single breach can take weeks to recover from and cost lakhs in legal and notification fees.", icon: "lock" },
  dno:      { head: "Founders can be personally sued", sentence: "Once you take outside money, your decisions as a founder open you up to investor and board disputes. Personal assets are at stake.", icon: "scale" },
  pi:       { head: "Customers can claim you didn't deliver", sentence: "If a client says your product caused them loss — downtime, bad output, missed timelines — they can demand compensation. Common for B2B and services.", icon: "doc" },
  privacy:  { head: "Regulators care about user data", sentence: "DPDP and sector regulators expect you to handle personal data responsibly. Penalties for non-compliance can be steep.", icon: "shield" },
  crime:    { head: "Insiders can steal", sentence: "When employees handle money, payment systems, or sensitive systems, the risk of internal fraud is real — and gets bigger as you grow.", icon: "alert" },
  property: { head: "Office or inventory damage", sentence: "Fire, flood, or theft at your premises can pause your business and destroy equipment. Often required by landlords and lenders.", icon: "home" },
  bi:       { head: "When you stop, your bills don't", sentence: "If an incident shuts you down for weeks, your salaries, rent, and obligations keep running. This cover replaces lost income.", icon: "clock" },
  ip:       { head: "IP fights are expensive", sentence: "Someone may claim you copied them, or you may need to defend your own work. Legal fees alone can be ruinous.", icon: "spark" },
  public:   { head: "Visitors get hurt on your premises", sentence: "If a customer, vendor, or guest is injured at your office or event, you're liable for medical costs and damages.", icon: "people" },
  product:  { head: "Your product harms a customer", sentence: "If a physical product malfunctions and causes injury or property damage, claims can follow — particularly for hardware and consumer goods.", icon: "box" },
  wc:       { head: "Employees get hurt on the job", sentence: "Field workers, delivery teams, and factory staff need protection — and it's mandated by law in most cases.", icon: "person" },
  epli:     { head: "Wrongful termination claims", sentence: "As headcount grows, so does the chance of an employment dispute — harassment, discrimination, or wrongful exit.", icon: "people" },
  key:      { head: "A key founder leaves", sentence: "If a critical co-founder exits or becomes unable to work, the business takes a hit. This cover bridges the gap.", icon: "person" },
};

const BUNDLE_CONCEPT = {
  business_shield_sme: {
    headline: "Liability protection for digital-first teams",
    concept: "A single policy covering the three risks every SaaS, fintech, or healthtech faces: a data breach, a customer dispute, and personal liability for founders and the board.",
    benefits: [
      { name: "If your data is breached", desc: "We handle the breach response, customer notification, and any regulatory fines." },
      { name: "If a customer claims loss", desc: "We defend you and pay valid claims for service failures or contractual disputes." },
      { name: "If you or the board are sued personally", desc: "Investor disputes, employment claims, regulatory actions — your personal assets stay protected." },
    ],
  },
  corporate_cover_ii: {
    headline: "Growth-stage protection across the business",
    concept: "Once you have an office, employees, and enterprise customers, your exposure widens. This package covers property, business continuity, and the liability lines that come with scale.",
    benefits: [
      { name: "Your office and operations", desc: "Fire, theft, equipment damage — and the income you lose while you recover." },
      { name: "Public and employee safety", desc: "Visitors at your office or employees on the job — medical and legal costs covered." },
      { name: "Founders and contracts", desc: "Personal director liability plus professional indemnity for your customer commitments." },
    ],
  },
  msme_kavach: {
    headline: "Foundation cover for early operations",
    concept: "Before you have venture capital or enterprise customers, you still have a business worth protecting. This is the baseline — your premises, your stock, and your continuity.",
    benefits: [
      { name: "Premises and inventory", desc: "Fire and theft cover for your store, kitchen, or workspace and everything in it." },
      { name: "Business continuity", desc: "If you have to close for repairs, this keeps your fixed costs paid." },
      { name: "Operational liability", desc: "Public liability and crime cover for the basics of running a small business." },
    ],
  },
  industrial_all_risk: {
    headline: "Hardware and supply-chain protection",
    concept: "When your business runs on physical assets — factories, vehicles, inventory in transit — your exposure looks different. This package is built for that.",
    benefits: [
      { name: "All your physical assets", desc: "Plant, equipment, raw materials, finished goods — covered against the full range of perils." },
      { name: "If your product harms someone", desc: "Product liability for physical goods sold to consumers or businesses." },
      { name: "Things in motion", desc: "Inventory in transit, goods at suppliers, machinery in operation." },
    ],
  },
};

// Map 5-field founder intake → full profile that runAnalysis can process
function buildProfile(intake) {
  // Infer sector heuristically from "what does your company do" text
  const what = (intake.what || "").toLowerCase();
  let sector = "SaaS / B2B";
  if (/fintech|payment|lend|banking|wallet|nbfc/.test(what)) sector = "Fintech";
  else if (/health|medical|clinic|hospital|doctor|patient/.test(what)) sector = "Healthtech";
  else if (/edu|learn|school|college|tutor/.test(what)) sector = "Edtech";
  else if (/ai|model|llm|gen.?ai/.test(what)) sector = "Deeptech / AI";
  else if (/food|kitchen|restaurant|cloud kitchen/.test(what)) sector = "Foodtech";
  else if (/logistic|deliver|fleet|mobility|ev/.test(what)) sector = "Logistics / Mobility";
  else if (/energ|climate|solar|battery|carbon/.test(what)) sector = "Climate / Energy";
  else if (/d2c|brand|consumer|retail|ecommerce|shop/.test(what)) sector = "D2C / E-commerce";

  const flags = [];
  if (intake.payments_data === "yes") {
    flags.push("Processes payments");
    flags.push("DPDP fiduciary");
  }
  if (intake.regulated === "yes") {
    flags.push("RBI regulated");
  }
  if (sector === "Healthtech") flags.push("Stores health data");
  if (sector === "Deeptech / AI") flags.push("AI in product");

  const team = +intake.team || 10;
  const records = team * 5000; // crude estimate

  return {
    name: (intake.what || "your company").split(/[,.]/)[0].trim().slice(0, 40),
    sector,
    stage: intake.stage,
    team,
    revenue: "",
    model: sector === "D2C / E-commerce" || sector === "Foodtech" ? "Hybrid" : "Pure SaaS / API",
    records,
    equity: intake.stage !== "Pre-seed",
    listed: false,
    flags,
  };
}

// Pick top 3 risks for plain English display
function topThreeRisks(scores) {
  return Object.entries(scores).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k]) => k);
}

// ── Founder app ──────────────────────────────────────────────────────
function FounderApp() {
  const initialStage = ["result-1", "result-2", "result-3"].includes(window.location.hash.slice(1))
    ? window.location.hash.slice(1)
    : "intake";
  const [stage, setStage] = useSf(initialStage); // intake | loading | result-1 | result-2 | result-3
  const [intake, setIntake] = useSf({
    what: "",
    team: "",
    stage: "",
    payments_data: "",
    regulated: "",
  });
  const [result, setResult] = useSf(null);
  const [profile, setProfile] = useSf(null);

  const canSubmit = intake.what.trim().length > 4 && intake.team && intake.stage && intake.payments_data && intake.regulated;
  const goTo = (nextStage) => {
    if (["result-1", "result-2", "result-3"].includes(nextStage)) {
      window.location.hash = nextStage;
    }
    setStage(nextStage);
    requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "smooth" }));
  };

  useEf(() => {
    const onHashChange = () => {
      const hashStage = window.location.hash.slice(1);
      if (["result-1", "result-2", "result-3"].includes(hashStage) && result && profile) {
        setStage(hashStage);
        requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "smooth" }));
      }
    };
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, [result, profile]);

  const submit = () => {
    const p = buildProfile(intake);
    setProfile(p);
    setStage("loading");
    setTimeout(() => {
      const r = window.runAnalysis(p);
      setResult(r);
      setStage("result-1");
      window.location.hash = "result-1";
      window.scrollTo({ top: 0, behavior: "smooth" });
    }, 1100);
  };

  const update = (patch) => setIntake({ ...intake, ...patch });

  return (
    <div className="fd-shell">
      <header className="fd-top">
        <a href="index.html" className="fd-back">← All views</a>
        <div className="fd-brand">
          <div className="ld-mark">SP</div>
          <span className="fd-brand-name">SPARC</span>
        </div>
        <div className="fd-step-marker">
          {stage === "intake" ? "Quick check" :
           stage === "loading" ? "Analysing" :
           `${stage.replace("result-", "")} of 3`}
        </div>
      </header>

      <main className="fd-main">
        {stage === "intake" && <Intake intake={intake} update={update} canSubmit={canSubmit} submit={submit} />}
        {stage === "loading" && <Loading what={intake.what} />}
        {stage !== "intake" && !result && <Intake intake={intake} update={update} canSubmit={canSubmit} submit={submit} />}
        {stage === "result-1" && result && <ResultRisks profile={profile} result={result} next={() => goTo("result-2")} />}
        {stage === "result-2" && result && <ResultBundle profile={profile} result={result} prev={() => goTo("result-1")} next={() => goTo("result-3")} />}
        {stage === "result-3" && result && <ResultCost profile={profile} result={result} prev={() => goTo("result-2")} />}
      </main>
    </div>
  );
}

// ── Intake (5 fields) ────────────────────────────────────────────────
function Intake({ intake, update, canSubmit, submit }) {
  return (
    <div className="fd-intake">
      <div className="fd-intake-eyebrow">Five questions. About a minute.</div>
      <h1 className="fd-h1">Let's see what protection you actually need.</h1>
      <p className="fd-lede">No jargon. No upsell. Just an honest read on your top three risks and a rough sense of cost.</p>

      <div className="fd-fields">
        <FdField num="01" label="What does your company do?" hint="A sentence is plenty.">
          <input
            className="fd-input"
            placeholder="We make AI tools for hospitals…"
            value={intake.what}
            onChange={(e) => update({ what: e.target.value })}
          />
        </FdField>

        <FdField num="02" label="How many people are on the team?">
          <input
            className="fd-input fd-input-num"
            type="number"
            placeholder="12"
            value={intake.team}
            onChange={(e) => update({ team: e.target.value })}
          />
        </FdField>

        <FdField num="03" label="What stage are you at?">
          <div className="fd-options">
            {["Pre-seed", "Seed", "Series A", "Series B+"].map((s) => (
              <button type="button" key={s} className={"fd-option" + (intake.stage === s ? " on" : "")} onClick={() => update({ stage: s })}>
                {s}
              </button>
            ))}
          </div>
        </FdField>

        <FdField num="04" label="Do you handle customer payments or personal data?">
          <div className="fd-yesno">
            <button type="button" className={"fd-yn" + (intake.payments_data === "yes" ? " on" : "")} onClick={() => update({ payments_data: "yes" })}>Yes</button>
            <button type="button" className={"fd-yn" + (intake.payments_data === "no" ? " on" : "")} onClick={() => update({ payments_data: "no" })}>Not really</button>
          </div>
        </FdField>

        <FdField num="05" label="Are you regulated (RBI, SEBI, IRDAI, etc.)?">
          <div className="fd-yesno">
            <button type="button" className={"fd-yn" + (intake.regulated === "yes" ? " on" : "")} onClick={() => update({ regulated: "yes" })}>Yes</button>
            <button type="button" className={"fd-yn" + (intake.regulated === "no" ? " on" : "")} onClick={() => update({ regulated: "no" })}>No</button>
          </div>
        </FdField>
      </div>

      <button type="button" className="fd-submit" disabled={!canSubmit} onClick={submit}>
        See my risk profile
        <svg viewBox="0 0 24 24" width="18" height="18"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
      </button>

      <div className="fd-trust">
        <span>Your answers stay private. No account needed.</span>
      </div>
    </div>
  );
}

function FdField({ num, label, hint, children }) {
  return (
    <div className="fd-field">
      <div className="fd-field-head">
        <span className="fd-field-num">{num}</span>
        <span className="fd-field-label">{label}</span>
      </div>
      {children}
      {hint && <div className="fd-field-hint">{hint}</div>}
    </div>
  );
}

// ── Loading ──────────────────────────────────────────────────────────
function Loading({ what }) {
  return (
    <div className="fd-loading">
      <div className="fd-loading-mark">
        <svg viewBox="0 0 60 60" width="60" height="60"><circle cx="30" cy="30" r="22" fill="none" stroke="currentColor" strokeWidth="1.5" opacity="0.2"/><circle cx="30" cy="30" r="22" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="30 110" strokeLinecap="round" className="load-spin"/></svg>
      </div>
      <div className="fd-loading-title">Reading your profile</div>
      <div className="fd-loading-sub">Looking at "{what}" against 13 risk dimensions…</div>
    </div>
  );
}

// ── Screen 1: Your risk profile ──────────────────────────────────────
function ResultRisks({ profile, result, next }) {
  const top3 = topThreeRisks(result.scores);
  return (
    <div className="fd-result">
      <div className="fd-r-eyebrow">Step 1 of 3 · Your risks</div>
      <h1 className="fd-h1">Here's what we noticed.</h1>
      <p className="fd-lede">A {profile.stage.toLowerCase()} {profile.sector.toLowerCase()} business with {profile.team} people typically faces a familiar pattern of exposures. Yours look like this.</p>

      <div className="fd-risks">
        {top3.map((k, i) => {
          const risk = RISK_PLAIN[k];
          if (!risk) return null;
          return (
            <div key={k} className="fd-risk">
              <div className="fd-risk-num">{String(i + 1).padStart(2, "0")}</div>
              <div className="fd-risk-icon"><RiskIcon name={risk.icon} /></div>
              <div className="fd-risk-body">
                <h2 className="fd-risk-head">{risk.head}</h2>
                <p className="fd-risk-text">{risk.sentence}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="fd-nav">
        <div className="fd-progress">
          <div className="fd-progress-dot active" />
          <div className="fd-progress-dot" />
          <div className="fd-progress-dot" />
        </div>
        <a className="fd-submit fd-submit-sm" href="#result-2" onClick={next}>
          What can I do about it?
          <svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </a>
      </div>
    </div>
  );
}

// ── Screen 2: What you need ──────────────────────────────────────────
function ResultBundle({ profile, result, prev, next }) {
  const bundle = result?.bundle || window.BUNDLES?.business_shield_sme || {};
  const concept = BUNDLE_CONCEPT[bundle.id] || BUNDLE_CONCEPT.business_shield_sme;
  const coverRows = [...(bundle.mandatory || []), ...(bundle.optional || []).slice(0, 2)]
    .map((key) => window.COVER_META?.[key])
    .filter(Boolean);
  return (
    <div className="fd-result">
      <div className="fd-r-eyebrow">Step 2 of 3 · The answer</div>
      <h1 className="fd-h1">{concept.headline}.</h1>
      <p className="fd-lede">{concept.concept}</p>

      <div className="fd-answer-card">
        <div className="fd-answer-label">Recommended package</div>
        <h2>{bundle.name || "Digital Business Shield"}</h2>
        <p>{bundle.tagline || "A practical insurance package matched to your current risk profile."}</p>
        <div className="fd-answer-covers">
          {coverRows.map((cover) => (
            <span key={cover.label}>{cover.label}</span>
          ))}
        </div>
      </div>

      <div className="fd-benefits">
        {concept.benefits.map((b, i) => (
          <div key={i} className="fd-benefit">
            <div className="fd-benefit-check">
              <svg viewBox="0 0 24 24" width="22" height="22"><path d="M5 12l5 5L20 7" stroke="currentColor" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </div>
            <div>
              <h3 className="fd-benefit-name">{b.name}</h3>
              <p className="fd-benefit-desc">{b.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="fd-nav">
        <button type="button" className="fd-back-btn" onClick={prev}>
          <svg viewBox="0 0 24 24" width="14" height="14"><path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back
        </button>
        <div className="fd-progress">
          <div className="fd-progress-dot" />
          <div className="fd-progress-dot active" />
          <div className="fd-progress-dot" />
        </div>
        <a className="fd-submit fd-submit-sm" href="#result-3" onClick={next}>
          What does it cost?
          <svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </a>
      </div>
    </div>
  );
}

// ── Screen 3: Cost + next step ───────────────────────────────────────
function ResultCost({ profile, result, prev }) {
  const low = Math.round(result.quote.total * 0.78);
  const high = Math.round(result.quote.total * 1.22);
  return (
    <div className="fd-result">
      <div className="fd-r-eyebrow">Step 3 of 3 · Cost</div>
      <h1 className="fd-h1">A rough estimate, not a quote.</h1>
      <p className="fd-lede">Final pricing depends on a few more details a human will walk you through. But for a business shaped like yours, here's the typical range.</p>

      <div className="fd-cost-card">
        <div className="fd-cost-eyebrow">Indicative annual premium</div>
        <div className="fd-cost-range">
          <span className="fd-cost-amount">₹ {low.toLocaleString()}</span>
          <span className="fd-cost-dash">to</span>
          <span className="fd-cost-amount">₹ {high.toLocaleString()}</span>
        </div>
        <div className="fd-cost-unit">Lakhs per year, all-inclusive</div>
        <div className="fd-cost-bar">
          <div className="fd-cost-bar-track">
            <div className="fd-cost-bar-fill" />
            <div className="fd-cost-bar-mark" style={{ left: "50%" }} />
          </div>
          <div className="fd-cost-bar-labels">
            <span>Lean cover</span>
            <span>Typical fit</span>
            <span>Comprehensive</span>
          </div>
        </div>
        <div className="fd-cost-note">
          Why a range? Because the exact premium depends on your sum insured, deductibles, and a few risk-management practices you may already have in place. The conversation with our team usually moves this number lower.
        </div>
      </div>

      <div className="fd-cta">
        <h3>Want a real number?</h3>
        <p>A relationship manager will walk you through it — 20 minutes, no obligation.</p>
        <button type="button" className="fd-cta-btn">
          Talk to ICICI Lombard
          <svg viewBox="0 0 24 24" width="18" height="18"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </button>
        <div className="fd-cta-second">
          <button type="button" className="fd-cta-secondary">Email me the summary</button>
        </div>
      </div>

      <div className="fd-nav fd-nav-end">
        <button type="button" className="fd-back-btn" onClick={prev}>
          <svg viewBox="0 0 24 24" width="14" height="14"><path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
          Back
        </button>
        <div className="fd-progress">
          <div className="fd-progress-dot" />
          <div className="fd-progress-dot" />
          <div className="fd-progress-dot active" />
        </div>
        <div className="fd-spacer" />
      </div>
    </div>
  );
}

// ── Simple inline icons (no external deps) ────────────────────────────
function RiskIcon({ name }) {
  const props = { viewBox: "0 0 32 32", width: 28, height: 28, fill: "none", stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case "lock":   return <svg {...props}><rect x="7" y="14" width="18" height="13" rx="2"/><path d="M11 14v-3a5 5 0 0 1 10 0v3"/></svg>;
    case "scale":  return <svg {...props}><path d="M16 5v22M8 9h16M5 19l3-10 3 10c-1 1.5-5 1.5-6 0zM21 19l3-10 3 10c-1 1.5-5 1.5-6 0z"/></svg>;
    case "doc":    return <svg {...props}><path d="M9 4h10l4 4v20H9zM19 4v4h4"/><path d="M12 14h8M12 18h8M12 22h5"/></svg>;
    case "shield": return <svg {...props}><path d="M16 4l11 4v7c0 7-5 12-11 13-6-1-11-6-11-13V8l11-4z"/></svg>;
    case "alert":  return <svg {...props}><path d="M16 5l13 23H3z"/><path d="M16 14v6M16 24v0.5"/></svg>;
    case "home":   return <svg {...props}><path d="M4 14l12-10 12 10v13H4z"/><path d="M13 27v-8h6v8"/></svg>;
    case "clock":  return <svg {...props}><circle cx="16" cy="16" r="12"/><path d="M16 9v7l5 3"/></svg>;
    case "spark":  return <svg {...props}><path d="M16 4l3 9 9 3-9 3-3 9-3-9-9-3 9-3z"/></svg>;
    case "people": return <svg {...props}><circle cx="12" cy="12" r="4"/><circle cx="22" cy="13" r="3"/><path d="M5 24c0-4 3-7 7-7s7 3 7 7M19 24c0-3 2-5 5-5s5 2 5 5"/></svg>;
    case "box":    return <svg {...props}><path d="M16 4l11 5v14l-11 5-11-5V9z"/><path d="M5 9l11 5 11-5M16 14v15"/></svg>;
    case "person": return <svg {...props}><circle cx="16" cy="10" r="5"/><path d="M5 28c0-6 5-10 11-10s11 4 11 10"/></svg>;
    default:       return <svg {...props}><circle cx="16" cy="16" r="11"/></svg>;
  }
}

const root = ReactDOM.createRoot(document.getElementById("app"));
root.render(<FounderApp />);
