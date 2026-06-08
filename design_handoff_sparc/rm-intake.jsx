// SPARC Intake v2 — RM-first
// Recents strip → typeahead → minimum-viable fields → analyze.

const { useState, useMemo, useRef, useEffect } = React;

function Intake({ profile, setProfile, onAnalyze, seedCompany }) {
  const [query, setQuery] = useState("");
  const [showResults, setShowResults] = useState(false);

  const matches = useMemo(() => {
    if (!query) return [];
    const q = query.toLowerCase();
    return window.COMPANIES.filter((c) => c.name.toLowerCase().includes(q)).slice(0, 6);
  }, [query]);

  // RM recents — the muscle memory of the role
  const recents = useMemo(() => [
    window.COMPANIES[0], window.COMPANIES[6], window.COMPANIES[7], window.COMPANIES[2], window.COMPANIES[3]
  ], []);

  const update = (patch) => setProfile({ ...profile, ...patch });
  const toggleFlag = (f) => {
    const next = new Set(profile.flags || []);
    next.has(f) ? next.delete(f) : next.add(f);
    update({ flags: [...next] });
  };

  const canAnalyze = profile.name && profile.sector && profile.stage && profile.team;

  return (
    <div className="intake">
      {/* ── Tactical header — RM tools, no editorial framing ──────── */}
      <header className="rm-header">
        <div className="rm-brand">
          <a href="index.html" className="back-btn" title="All views"><svg viewBox="0 0 24 24" width="14" height="14"><path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg></a>
          <div className="rm-mark"><svg viewBox="0 0 32 32" width="20" height="20"><circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="1.5"/><circle cx="16" cy="16" r="5" fill="currentColor"/></svg></div>
          <div className="rm-wordmark">SPARC</div>
          <div className="rm-divider" />
          <div className="rm-context">RM workspace · New analysis</div>
        </div>
        <div className="rm-header-actions">
          <button className="rm-link">Last 30 days</button>
          <button className="rm-link">My pipeline</button>
          <button className="rm-link">Templates</button>
        </div>
      </header>

      <main className="intake-narrow">
        <div className="intake-eyebrow">
          <span>Step 1 of 1</span>
          <span className="dot">·</span>
          <span>Roughly 30 seconds</span>
        </div>
        <h1 className="intake-h1">Who are you quoting?</h1>

        {/* ── Recents strip — RM one-click muscle memory ──────────── */}
        <div className="recents-block">
          <div className="recents-label">Recent &amp; suggested</div>
          <div className="recents-row">
            {recents.map((c) => (
              <button key={c.name} className="recent-chip" onClick={() => seedCompany(c)}>
                <span className="recent-name">{c.name}</span>
                <span className="recent-meta">{c.sector.split(" / ")[0]} · {c.stage}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ── Typeahead ─────────────────────────────────────────── */}
        <div className="search-block">
          <label className="lbl">Or search a company</label>
          <div className="search-wrap">
            <svg viewBox="0 0 24 24" width="18" height="18" className="search-icon"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="1.5"/><path d="M20 20l-4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
            <input
              className="search-input"
              placeholder="Type the company name…"
              value={profile.name || query}
              onChange={(e) => { setQuery(e.target.value); setShowResults(true); update({ name: e.target.value }); }}
              onFocus={() => setShowResults(true)}
              onBlur={() => setTimeout(() => setShowResults(false), 150)}
            />
            {profile.name ? (
              <button className="search-clear" onClick={() => { update({ name: "" }); setQuery(""); }} aria-label="clear">×</button>
            ) : (
              <span className="search-kbd">⌘K</span>
            )}
          </div>
          {showResults && matches.length > 0 && (
            <div className="typeahead">
              {matches.map((m) => (
                <button key={m.name} className="ta-row" onMouseDown={(e) => { e.preventDefault(); seedCompany(m); setQuery(""); setShowResults(false); }}>
                  <span className="ta-name">{m.name}</span>
                  <span className="ta-meta">{m.sector} · {m.stage} · {m.team.toLocaleString()} team</span>
                  <span className="ta-arrow">↵</span>
                </button>
              ))}
              <div className="ta-foot">Pre-fills sector, stage, team, regulatory flags. Editable below.</div>
            </div>
          )}
        </div>

        {/* ── Just the essentials — no expandable sections ──────── */}
        {(profile.name) && (
          <>
            <div className="field-grid">
              <Field label="Sector">
                <Select value={profile.sector} onChange={(v) => update({ sector: v })} options={window.SECTORS} placeholder="Select sector" />
              </Field>
              <Field label="Stage">
                <Segmented value={profile.stage} onChange={(v) => update({ stage: v })} options={window.STAGES} />
              </Field>
              <Field label="Team">
                <NumberInput value={profile.team} onChange={(v) => update({ team: v })} suffix="people" />
              </Field>
              <Field label="Revenue">
                <NumberInput value={profile.revenue} onChange={(v) => update({ revenue: v })} suffix="₹ Cr" />
              </Field>
            </div>

            {/* Optional details — chip-style, no headers */}
            <div className="optional-row">
              <span className="opt-label">Add if known:</span>
              <div className="chip-grid inline-chips">
                {window.REG_FLAGS.map((f) => {
                  const on = (profile.flags || []).includes(f);
                  return (
                    <button key={f} className={"chip" + (on ? " chip-on" : "")} onClick={() => toggleFlag(f)}>
                      <span className="chip-dot" />
                      {f}
                    </button>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* ── The primary action — disabled until ready ─────────── */}
        <div className="intake-actions">
          <button className="cta-btn cta-lg" disabled={!canAnalyze} onClick={onAnalyze}>
            Generate pitch
            <svg viewBox="0 0 24 24" width="16" height="16"><path d="M5 12h14M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>
          <div className="intake-hint">
            {canAnalyze
              ? `Bundle, price band, talking points, and a draft message — in 1.3 seconds.`
              : "Pick a company above to begin. Most fields auto-fill."}
          </div>
        </div>
      </main>
    </div>
  );
}

// ── Form atoms ────────────────────────────────────────────────────────
function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span className="lbl">{label}</span>
      {children}
      {hint && <span className="hint">{hint}</span>}
    </label>
  );
}

function Select({ value, onChange, options, placeholder }) {
  return (
    <div className="select-wrap">
      <select className="select" value={value || ""} onChange={(e) => onChange(e.target.value)}>
        <option value="" disabled>{placeholder || "Select"}</option>
        {options.map((o) => <option key={o} value={o}>{o}</option>)}
      </select>
      <svg viewBox="0 0 24 24" className="select-chev" width="14" height="14"><path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="1.6" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
    </div>
  );
}

function Segmented({ value, onChange, options }) {
  return (
    <div className="segmented">
      {options.map((o) => (
        <button key={o} className={"seg" + (value === o ? " seg-on" : "")} onClick={() => onChange(o)} type="button">
          {o}
        </button>
      ))}
    </div>
  );
}

function NumberInput({ value, onChange, suffix }) {
  const display = value === "" || value == null ? "" : value;
  return (
    <div className="num-wrap">
      <input
        className="num"
        type="number"
        value={display}
        onChange={(e) => onChange(e.target.value === "" ? "" : +e.target.value)}
        placeholder="0"
      />
      {suffix && <span className="num-suffix">{suffix}</span>}
    </div>
  );
}

function formatCompact(n) {
  if (n == null || n === "") return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, "") + "K";
  return String(n);
}

Object.assign(window, { Intake, formatCompact });
