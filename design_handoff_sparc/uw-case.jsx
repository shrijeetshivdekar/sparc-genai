// UW case workspace — 6 spec'd panels: risk grid, assumptions, pre-flight,
// reg triggers, pricing builder, inputs-needed. Plus supplemental aggregate + comparables.

const { useState: useSC, useMemo: useMC, useEffect: useEC, useRef: useRC } = React;

function UWCase({ caseData, onResolve }) {
  const { company, result, caseId, rm, bundle, indicative, flagged, status } = caseData;

  // Editable per-cover pricing
  const [lines, setLines] = useSC(() => result.quote.lines.map((l) => ({
    ...l,
    loading: 0,
    excluded: false,
  })));

  const [appliedLoadings, setAppliedLoadings] = useSC([]);
  const [appliedDiscounts, setAppliedDiscounts] = useSC(["bundle"]);
  const [auditNote, setAuditNote] = useSC("");
  const [activePanel, setActivePanel] = useSC("risk"); // for top nav scrollspy

  // Pre-flight checks state
  const [checkOverrides, setCheckOverrides] = useSC({});
  const checks = window.UW_CHECKS.map((c) => ({ ...c, status: checkOverrides[c.id] || c.status }));
  const allCleared = checks.every((c) => c.status === "pass" || c.status === "na");

  // Derived data
  const signals = useMC(() => window.riskSignals(company, result.scores), [company, result]);
  const assumptions = useMC(() => window.pricingAssumptions(company), [company]);
  const triggers = useMC(() => window.detectRegTriggers(company), [company]);
  const inputsNeeded = useMC(() => window.inputsForFirmQuote(company), [company]);

  // Totals
  const totals = useMC(() => {
    const activeLines = lines.filter((l) => !l.excluded);
    const subtotal = activeLines.reduce((s, l) => s + l.premium * (1 + l.loading / 100), 0);
    const loadPct = appliedLoadings.reduce((s, id) => s + (window.UW_LOADINGS.find((x) => x.id === id)?.pct || 0), 0);
    const discPct = appliedDiscounts.reduce((s, id) => s + (window.UW_DISCOUNTS.find((x) => x.id === id)?.pct || 0), 0);
    const netPct = loadPct + discPct;
    const adjusted = subtotal * (1 + netPct / 100);
    const gst = adjusted * 0.18;
    const total = adjusted + gst;
    return { subtotal, loadPct, discPct, netPct, adjusted, gst, total };
  }, [lines, appliedLoadings, appliedDiscounts]);

  const updateLine = (key, patch) => setLines(lines.map((l) => l.key === key ? { ...l, ...patch } : l));
  const toggleLoading = (id) => setAppliedLoadings(appliedLoadings.includes(id) ? appliedLoadings.filter((x) => x !== id) : [...appliedLoadings, id]);
  const toggleDiscount = (id) => setAppliedDiscounts(appliedDiscounts.includes(id) ? appliedDiscounts.filter((x) => x !== id) : [...appliedDiscounts, id]);

  const canApprove = allCleared && auditNote.trim().length >= 12;

  const aggregate = useMC(() => {
    const before = 62;
    const bump = Math.round((indicative / 100) * 100);
    return { before, after: Math.min(98, before + bump), cap: 100 };
  }, [indicative]);

  const comparables = window.UW_COMPARABLES[company.name] || [];

  const handleResolve = (decision) => {
    if (decision === "approve" && !canApprove) return;
    if (!auditNote.trim()) return;
    onResolve(decision, auditNote, totals.total);
  };

  // Panel jump nav
  const panels = [
    { id: "risk",         label: "Risk",        letter: "A" },
    { id: "assumptions",  label: "Assumptions", letter: "B" },
    { id: "checks",       label: "Pre-flight",  letter: "C" },
    { id: "triggers",     label: "Triggers",    letter: "D" },
    { id: "pricing",      label: "Pricing",     letter: "E" },
    { id: "inputs",       label: "Inputs",      letter: "F" },
    { id: "context",      label: "Context",     letter: "G" },
  ];

  return (
    <main className="uw-case">
      <header className="uc-header">
        <div className="uc-h-left">
          <div className="uc-h-id">{caseId}</div>
          <h2 className="uc-h-company">{company.name}</h2>
          <div className="uc-h-meta">
            <span>{company.sector}</span>
            <span className="uc-h-dot">·</span>
            <span>{company.stage}</span>
            <span className="uc-h-dot">·</span>
            <span>{(+company.team).toLocaleString()} team</span>
            <span className="uc-h-dot">·</span>
            <span>{(company.records / 1_000_000).toFixed(1)}M records</span>
          </div>
        </div>
        <div className="uc-h-right">
          <div className="uc-h-rm">
            <div className="uc-h-rm-l">Submitted by</div>
            <div className="uc-h-rm-v">{rm}</div>
          </div>
          <div className={"uc-h-status uc-status-" + (status === "referred" ? "ref" : "pending")}>
            {status === "referred" ? "Referred up" : "Pending UW"}
          </div>
        </div>
      </header>

      <div className="uc-rm-strip">
        <span className="uc-strip-eyebrow">RM recommended</span>
        <span className="uc-strip-bundle">{bundle}</span>
        <span className="uc-strip-dot">·</span>
        <span className="uc-strip-indicative">₹ {indicative} L indicative</span>
        <span className="uc-strip-dot">·</span>
        <span className="uc-strip-risk">Risk {result.overall} / {result.tier}</span>
        <div className="uc-strip-flags">
          {flagged.map((f) => <span key={f} className="uc-strip-flag">{f}</span>)}
        </div>
      </div>

      {/* Panel jump nav */}
      <nav className="uc-panelnav">
        {panels.map((p) => (
          <a key={p.id} href={"#uc-" + p.id} className="uc-panelnav-link">
            <span className="uc-panelnav-letter">{p.letter}</span>
            <span>{p.label}</span>
          </a>
        ))}
      </nav>

      <div className="uc-body">
        <div className="uc-workspace">

          {/* === A. Risk Score Grid (13 dims with signals) === */}
          <section className="uc-section" id="uc-risk">
            <PanelHead letter="A" title="Risk score" meta={`${Object.keys(result.scores).length} dimensions · top signals per dimension`} />
            <RiskGrid scores={result.scores} signals={signals} />
          </section>

          {/* === B. Pricing assumptions === */}
          <section className="uc-section" id="uc-assumptions">
            <PanelHead letter="B" title="Pricing assumptions" meta="Every input the engine used, with source." />
            <AssumptionsTable rows={assumptions} />
          </section>

          {/* === C. Pre-flight checks === */}
          <section className="uc-section" id="uc-checks">
            <PanelHead letter="C" title="Underwriter checks" meta={`${checks.filter((c) => c.status === "pass" || c.status === "na").length} / ${checks.length} cleared`} metaTone={allCleared ? "ok" : ""} />
            <div className="uc-checks">
              {checks.map((c) => (
                <CheckRow key={c.id} check={c} onResolve={() => setCheckOverrides({ ...checkOverrides, [c.id]: "pass" })} />
              ))}
            </div>
          </section>

          {/* === D. Regulatory triggers === */}
          <section className="uc-section" id="uc-triggers">
            <PanelHead letter="D" title="Regulatory triggers" meta={`${triggers.length} detected · rule references`} />
            <TriggersTable triggers={triggers} />
          </section>

          {/* === E. Cover pricing builder === */}
          <section className="uc-section" id="uc-pricing">
            <PanelHead letter="E" title="Cover-level pricing" meta="Edit SI, apply loading, exclude covers." />
            <div className="uc-pricing">
              <div className="up-head">
                <span>Cover</span>
                <span>SI limit</span>
                <span>ROL</span>
                <span>UW loading</span>
                <span className="up-h-right">Gross premium</span>
                <span></span>
              </div>
              {lines.map((l) => {
                const meta = window.COVER_META[l.key];
                const adjusted = l.premium * (1 + l.loading / 100);
                return (
                  <div key={l.key} className={"up-row" + (l.excluded ? " excluded" : "")}>
                    <span className="up-cover">
                      <span className={"up-dot " + (l.mandatory ? "up-dot-m" : "up-dot-o")} />
                      {l.label}
                      {!l.mandatory && <span className="qt-opt-tag">opt.</span>}
                    </span>
                    <span className="up-si">
                      <input type="number" value={l.si} onChange={(e) => updateLine(l.key, { si: +e.target.value, premium: +e.target.value * meta.rate * 100 })} />
                      <span className="up-suffix">Cr</span>
                    </span>
                    <span className="up-rate">{(meta.rate * 100).toFixed(2)}%</span>
                    <span className="up-load">
                      <input type="number" value={l.loading} onChange={(e) => updateLine(l.key, { loading: +e.target.value })} />
                      <span className="up-suffix">%</span>
                    </span>
                    <span className="up-prem">₹ {adjusted.toFixed(2)} L</span>
                    <button className="up-x" onClick={() => updateLine(l.key, { excluded: !l.excluded })} title={l.excluded ? "Include" : "Exclude"}>
                      {l.excluded ? "+" : "×"}
                    </button>
                  </div>
                );
              })}
            </div>

            <div className="up-modifiers">
              <div className="up-mod-col">
                <div className="up-mod-head">Loadings</div>
                <div className="up-mod-chips">
                  {window.UW_LOADINGS.map((m) => (
                    <button key={m.id} className={"up-mod-chip" + (appliedLoadings.includes(m.id) ? " on load" : "")} onClick={() => toggleLoading(m.id)}>
                      <span>{m.label}</span>
                      <span className="up-mod-pct">+{m.pct}%</span>
                    </button>
                  ))}
                </div>
              </div>
              <div className="up-mod-col">
                <div className="up-mod-head">Discounts</div>
                <div className="up-mod-chips">
                  {window.UW_DISCOUNTS.map((m) => (
                    <button key={m.id} className={"up-mod-chip" + (appliedDiscounts.includes(m.id) ? " on disc" : "")} onClick={() => toggleDiscount(m.id)}>
                      <span>{m.label}</span>
                      <span className="up-mod-pct">{m.pct}%</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* === F. Inputs needed for firm quote === */}
          <section className="uc-section" id="uc-inputs">
            <PanelHead letter="F" title="Inputs required for firm quote" meta={`${inputsNeeded.filter((i) => i.critical).length} critical · ${inputsNeeded.filter((i) => !i.critical).length} nice-to-have`} />
            <InputsList items={inputsNeeded} />
          </section>

          {/* === G. Context (supplemental: aggregate + comparables) === */}
          <section className="uc-section uc-context-section" id="uc-context">
            <PanelHead letter="G" title="Context" meta="Aggregate exposure and comparable cases." />

            <div className="uc-subsection">
              <div className="uc-subsec-label">Sector aggregate exposure</div>
              <div className="uc-aggregate-flat">
                <div className="ua-bar-wrap">
                  <div className="ua-bar">
                    <div className="ua-bar-fill ua-bar-before" style={{ width: aggregate.before + "%" }} />
                    <div className="ua-bar-fill ua-bar-bump" style={{ left: aggregate.before + "%", width: (aggregate.after - aggregate.before) + "%" }} />
                    <div className="ua-bar-cap" />
                  </div>
                  <div className="ua-bar-labels">
                    <span>0</span>
                    <span className="ua-mark" style={{ left: aggregate.before + "%" }}>● Today {aggregate.before}%</span>
                    <span className="ua-mark ua-mark-bump" style={{ left: aggregate.after + "%" }}>+ This case {aggregate.after}%</span>
                    <span>Cap</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="uc-subsection">
              <div className="uc-subsec-label">Comparable cases — same sector + stage</div>
              {comparables.length === 0 ? (
                <div className="uc-comp-empty">No close comparables in the last 12 months.</div>
              ) : (
                <div className="uc-comp-table">
                  <div className="ucm-head">
                    <span>Company</span><span>Stage</span><span>Premium</span><span>Loading</span><span>Outcome</span><span>Date</span>
                  </div>
                  {comparables.map((c) => (
                    <div key={c.company} className="ucm-row">
                      <span className="ucm-name">{c.company}</span>
                      <span>{c.stage}</span>
                      <span className="ucm-num">₹ {c.premium} L</span>
                      <span className="ucm-num">{c.loading}</span>
                      <span className={"ucm-outcome ucm-" + c.outcome.toLowerCase()}>{c.outcome}</span>
                      <span className="ucm-date">{c.date}</span>
                    </div>
                  ))}
                  <div className="ucm-anchor">
                    This case pricing band: <strong>₹ {(totals.total * 0.92).toFixed(1)} – ₹ {(totals.total * 1.08).toFixed(1)} L</strong>
                    {comparables.length > 0 && <> · sector median: ₹ {(comparables.reduce((s, c) => s + c.premium, 0) / comparables.length).toFixed(1)} L</>}
                  </div>
                </div>
              )}
            </div>
          </section>

        </div>

        {/* ── Decision pane (right) ──────────────────────── */}
        <aside className="uc-decision">
          <div className="ud-sticky">
            <div className="ud-block">
              <div className="ud-eyebrow">Live premium</div>
              <div className="ud-total">
                <span className="ud-cur">₹</span>
                <span className="ud-num">{totals.total.toFixed(2)}</span>
                <span className="ud-unit">L / year</span>
              </div>
              <div className="ud-vs-rm">
                vs RM indicative ₹ {indicative} L
                <span className={"ud-delta " + (totals.total > indicative ? "ud-up" : "ud-dn")}>
                  {totals.total > indicative ? "▲" : "▼"} {Math.abs(((totals.total - indicative) / indicative) * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            <div className="ud-breakdown">
              <div className="ud-bk-row"><span>Subtotal</span><span>₹ {totals.subtotal.toFixed(2)} L</span></div>
              <div className="ud-bk-row"><span>Net adjustment</span><span className={totals.netPct > 0 ? "ud-load" : "ud-disc"}>{totals.netPct > 0 ? "+" : ""}{totals.netPct}%</span></div>
              <div className="ud-bk-row"><span>GST (18%)</span><span>+ ₹ {totals.gst.toFixed(2)} L</span></div>
              <div className="ud-bk-row ud-bk-final"><span>Final payable</span><span>₹ {totals.total.toFixed(2)} L</span></div>
            </div>

            <div className="ud-meta-grid">
              <div className="ud-m"><div className="ud-m-l">Validity</div><div className="ud-m-v">30 days</div></div>
              <div className="ud-m"><div className="ud-m-l">Commission</div><div className="ud-m-v">12%</div></div>
              <div className="ud-m"><div className="ud-m-l">Authority</div><div className="ud-m-v">Within</div></div>
              <div className="ud-m"><div className="ud-m-l">SI total</div><div className="ud-m-v">₹ {lines.filter((l) => !l.excluded).reduce((s, l) => s + l.si, 0)} Cr</div></div>
            </div>

            <div className="ud-audit">
              <label className="ud-audit-label">
                Audit note
                <span className={"ud-audit-req" + (auditNote.length >= 12 ? " met" : "")}>
                  {auditNote.length >= 12 ? "✓ recorded" : `${Math.max(0, 12 - auditNote.length)} chars required`}
                </span>
              </label>
              <textarea
                className="ud-audit-input"
                placeholder="Brief rationale for this decision — goes on file."
                value={auditNote}
                onChange={(e) => setAuditNote(e.target.value)}
                rows={4}
              />
            </div>

            <div className="ud-actions">
              <button className={"ud-btn ud-approve" + (canApprove ? "" : " disabled")} disabled={!canApprove} onClick={() => handleResolve("approve")}>
                <span className="ud-btn-l">Approve &amp; quote</span>
                <span className="ud-btn-kbd">⌘ ↵</span>
              </button>
              <button className="ud-btn ud-modify" disabled={!auditNote.trim()} onClick={() => handleResolve("modify")}>
                <span className="ud-btn-l">Modify &amp; approve</span>
              </button>
              <button className="ud-btn ud-refer" disabled={!auditNote.trim()} onClick={() => handleResolve("refer")}>
                <span className="ud-btn-l">Refer to senior</span>
              </button>
              <button className="ud-btn ud-decline" disabled={!auditNote.trim()} onClick={() => handleResolve("decline")}>
                <span className="ud-btn-l">Decline</span>
              </button>
            </div>

            <div className="ud-foot">
              Approval locks pricing for 30 days and notifies <strong>{rm}</strong>.
              {!allCleared && <div className="ud-foot-warn">Clear all pre-flight checks before approving.</div>}
              {auditNote.length < 12 && <div className="ud-foot-warn">Audit note is mandatory.</div>}
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}

// ── PanelHead — consistent section header ────────────────────────────
function PanelHead({ letter, title, meta, metaTone }) {
  return (
    <div className="uc-sec-head">
      <span className="uc-sec-letter">{letter}</span>
      <span className="uc-sec-title">{title}</span>
      <span className={"uc-sec-meta" + (metaTone === "ok" ? " uc-sec-meta-ok" : "")}>{meta}</span>
    </div>
  );
}

// ── Risk Grid — 13 dims, score + signals per dim ─────────────────────
function RiskGrid({ scores, signals }) {
  const dims = window.RISK_DIMENSIONS;
  return (
    <div className="risk-grid-uw">
      {dims.map((d) => {
        const v = scores[d.key] || 0;
        const tier = v >= 70 ? "high" : v >= 50 ? "mid" : v >= 30 ? "low" : "min";
        const sigs = signals[d.key] || [];
        return (
          <div key={d.key} className="risk-uw-cell">
            <div className="ruc-top">
              <div className="ruc-name">{d.label}</div>
              <div className={"ruc-score ruc-tier-" + tier}>{v}</div>
            </div>
            <ul className="ruc-signals">
              {sigs.map((s, i) => (
                <li key={i} className="ruc-sig">
                  <span className="ruc-sig-l">{s.label}</span>
                  <span className="ruc-sig-d">{s.detail}</span>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </div>
  );
}

// ── Assumptions table ─────────────────────────────────────────────────
function AssumptionsTable({ rows }) {
  return (
    <div className="uw-assumptions">
      <div className="uat-head">
        <span>Input</span><span>Value used</span><span>Source</span>
      </div>
      {rows.map((r, i) => (
        <div key={i} className="uat-row">
          <span className="uat-l">{r.label}</span>
          <span className="uat-v">{r.value}</span>
          <span className={"uat-src uat-src-" + r.source}>
            <span className="uat-src-dot" />
            {r.source === "user" ? "User-supplied" : r.source === "estimated" ? "Estimated" : r.source === "inferred" ? "Inferred" : "Default"}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Pre-flight check row ──────────────────────────────────────────────
function CheckRow({ check, onResolve }) {
  const statusMap = {
    pass:    { l: "Pass",    cls: "ok" },
    partial: { l: "Partial", cls: "warn" },
    open:    { l: "Open",    cls: "open" },
    fail:    { l: "Fail",    cls: "fail" },
    na:      { l: "N/A",     cls: "na" },
  };
  const s = statusMap[check.status];
  return (
    <div className={"uc-check uc-check-" + s.cls}>
      <span className="uc-check-pin" />
      <div className="uc-check-body">
        <div className="uc-check-label">{check.label}</div>
        {check.note && <div className="uc-check-note">{check.note}</div>}
      </div>
      <div className="uc-check-right">
        <span className={"uc-check-status status-" + s.cls}>{s.l}</span>
        {(check.status === "open" || check.status === "partial") && (
          <button className="uc-check-action" onClick={onResolve}>Resolve</button>
        )}
      </div>
    </div>
  );
}

// ── Reg triggers table ────────────────────────────────────────────────
function TriggersTable({ triggers }) {
  if (triggers.length === 0) {
    return <div className="uc-trig-empty">No regulatory triggers detected on this profile.</div>;
  }
  return (
    <div className="uw-triggers">
      {triggers.map((t) => {
        const rule = window.REG_RULES[t.ruleKey];
        return (
          <div key={t.key} className={"uwt-row uwt-sev-" + t.severity}>
            <div className="uwt-sev">
              <span className="uwt-sev-pin" />
              <span className="uwt-sev-l">{t.severity}</span>
            </div>
            <div className="uwt-body">
              <div className="uwt-title">{t.title}</div>
              <div className="uwt-finding">{t.finding}</div>
              <div className="uwt-action">
                <span className="uwt-action-l">Action</span>
                {t.action}
              </div>
            </div>
            <div className="uwt-rule">
              <div className="uwt-rule-name">{rule.name}</div>
              <div className="uwt-rule-section">{rule.section}</div>
              <div className="uwt-rule-text">{rule.refLine}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ── Inputs needed list ────────────────────────────────────────────────
function InputsList({ items }) {
  return (
    <div className="uw-inputs">
      {items.map((it) => (
        <div key={it.id} className={"uwi-row" + (it.critical ? " uwi-critical" : "")}>
          <span className="uwi-tag">{it.critical ? "Critical" : "Optional"}</span>
          <div className="uwi-body">
            <div className="uwi-label">{it.label}</div>
            <div className="uwi-reason">{it.reason}</div>
          </div>
          <button className="uwi-action">Request</button>
        </div>
      ))}
    </div>
  );
}

window.UWCase = UWCase;
