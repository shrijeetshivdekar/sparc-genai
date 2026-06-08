// SPARC — root App
// Orchestrates intake → loading → results.

const { useState: useS, useEffect: useE, useMemo: useM } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "palette": "default",
  "density": "comfortable",
  "displayFont": "Space Grotesk"
}/*EDITMODE-END*/;

function App() {
  const [stage, setStage] = useS("intake"); // intake | loading | results
  const [profile, setProfile] = useS({
    name: "",
    sector: "",
    stage: "",
    team: "",
    revenue: "",
    model: "",
    records: "",
    equity: false,
    listed: false,
    flags: [],
  });
  const [result, setResult] = useS(null);
  const [tweaks, setTweak] = window.useTweaks ? window.useTweaks(TWEAK_DEFAULTS) : [TWEAK_DEFAULTS, () => {}];

  // Apply palette CSS vars (only if non-default)
  useE(() => {
    const root = document.documentElement;
    if (tweaks.palette && tweaks.palette !== "default") {
      root.setAttribute("data-palette", tweaks.palette);
    } else {
      root.removeAttribute("data-palette");
    }
    root.setAttribute("data-density", tweaks.density);
    if (tweaks.displayFont && tweaks.displayFont !== "Space Grotesk") {
      root.style.setProperty("--font-display", `'${tweaks.displayFont}', 'Space Grotesk', sans-serif`);
    }
  }, [tweaks]);

  const seedCompany = (c) => {
    setProfile({
      name: c.name,
      sector: c.sector,
      stage: c.stage,
      team: c.team,
      revenue: c.revenue,
      model: c.model,
      records: c.records,
      equity: c.equity,
      listed: c.listed,
      flags: c.flags || [],
    });
  };

  const onAnalyze = () => {
    setStage("loading");
    setTimeout(() => {
      const r = window.runAnalysis(profile);
      setResult(r);
      setStage("results");
      window.scrollTo({ top: 0 });
    }, 1300);
  };

  const onBack = () => {
    setStage("intake");
    window.scrollTo({ top: 0 });
  };

  // Tweaks panel
  const TweaksPanel = window.TweaksPanel;
  const TweakSection = window.TweakSection;
  const TweakRadio = window.TweakRadio;
  const TweakSelect = window.TweakSelect;
  const TweakButton = window.TweakButton;

  return (
    <React.Fragment>
      {stage === "intake" && (
        <Intake
          profile={profile}
          setProfile={setProfile}
          onAnalyze={onAnalyze}
          seedCompany={seedCompany}
        />
      )}
      {stage === "loading" && <LoadingScreen profile={profile} />}
      {stage === "results" && result && (
        <Results profile={profile} result={result} onBack={onBack} />
      )}

      {TweaksPanel && (
        <TweaksPanel title="Tweaks">
          <TweakSection title="Palette">
            <TweakRadio label="Surface" value={tweaks.palette} options={["default", "midnight", "obsidian", "mono"]} onChange={(v) => setTweak("palette", v)} />
            <TweakRadio label="Density" value={tweaks.density} options={["comfortable", "compact"]} onChange={(v) => setTweak("density", v)} />
          </TweakSection>
          <TweakSection title="Type">
            <TweakSelect
              label="Display font"
              value={tweaks.displayFont}
              options={["Instrument Serif", "Fraunces", "GT Sectra", "PP Editorial New"].map((f) => ({ value: f, label: f }))}
              onChange={(v) => setTweak("displayFont", v)}
            />
          </TweakSection>
          <TweakSection title="Demo flow">
            <TweakButton onClick={() => { seedCompany(window.COMPANIES[2]); }}>Pre-fill: Freshworks</TweakButton>
            <TweakButton onClick={() => { seedCompany(window.COMPANIES[0]); }}>Pre-fill: Razorpay</TweakButton>
            <TweakButton onClick={() => { seedCompany(window.COMPANIES[6]); }}>Pre-fill: Niramai (healthtech)</TweakButton>
            <TweakButton onClick={() => { seedCompany(window.COMPANIES[7]); }}>Pre-fill: Ather (hardware)</TweakButton>
            <TweakButton onClick={() => { setProfile({ name: "", sector: "", stage: "", team: "", revenue: "", model: "", records: "", equity: false, listed: false, flags: [] }); setStage("intake"); }}>Reset</TweakButton>
            {stage === "intake" && profile.name && profile.sector && profile.stage && profile.team && (
              <TweakButton onClick={onAnalyze}>→ Jump to results</TweakButton>
            )}
            {stage === "results" && (
              <TweakButton onClick={onBack}>← Back to intake</TweakButton>
            )}
          </TweakSection>
        </TweaksPanel>
      )}
    </React.Fragment>
  );
}

function LoadingScreen({ profile }) {
  const [step, setStep] = useS(0);
  const steps = [
    "Reading profile signals",
    "Scoring 13 risk dimensions",
    "Matching against bundle catalog",
    "Drafting outreach",
  ];
  useE(() => {
    const id = setInterval(() => setStep((s) => Math.min(s + 1, steps.length - 1)), 280);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="loading-screen">
      <div className="load-mark">
        <svg viewBox="0 0 80 80" width="80" height="80">
          <circle cx="40" cy="40" r="32" fill="none" stroke="currentColor" strokeWidth="1.2" opacity="0.18" />
          <circle cx="40" cy="40" r="32" fill="none" stroke="currentColor" strokeWidth="1.6" strokeDasharray="50 200" strokeLinecap="round" className="load-spin"/>
          <circle cx="40" cy="40" r="8" fill="currentColor" />
        </svg>
      </div>
      <div className="load-title">Analysing {profile.name || "this profile"}</div>
      <div className="load-sub">SPARC underwriting protocol · v2026.05</div>
      <ul className="load-steps">
        {steps.map((s, i) => (
          <li key={s} className={"load-step" + (i <= step ? " load-step-done" : "")}>
            <span className="load-step-dot" />
            <span>{s}</span>
            <span className="load-step-status">{i < step ? "done" : i === step ? "…" : ""}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("app"));
root.render(<App />);
