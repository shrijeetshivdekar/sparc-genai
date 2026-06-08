// SPARC Results v2 — RM-first
// Verdict bar at top, pitch + message above the fold, proof in collapsibles.

const { useState: useStateR, useMemo: useMemoR, useEffect: useEffectR, useRef: useRefR } = React;

function Results({ profile, result, onBack }) {
  const [editingEmail, setEditingEmail] = useStateR(false);
  const [emailBody, setEmailBody] = useStateR(result.email.body);
  const [openDrawer, setOpenDrawer] = useStateR(null); // 'rationale' | 'risk' | 'uw' | 'covers'
  const [copied, setCopied] = useStateR(null);

  const copy = (what, text) => {
    navigator.clipboard?.writeText(text);
    setCopied(what);
    setTimeout(() => setCopied(null), 1400);
  };

  const pushbackPrep = [
    {
      q: "We're too early to need D&O.",
      a: `Seed-to-Series A is exactly when D&O matters — investor votes, board decisions, IP assignments. Coverage now is a fraction of the price post-Series B.`,
    },
    {
      q: "We already have cyber via our SOC2 vendor.",
      a: `Cyber insurance ≠ cyber security. SOC2 vendors prevent incidents; insurance pays for the breach response, regulator fines, and customer notification — none of which your security stack covers.`,
    },
    {
      q: "Can we just buy the mandatory three?",
      a: `Yes, and we'd start there. The two optional add-ons are flagged because your regulatory profile (${(profile.flags || []).slice(0,2).join(", ") || "current setup"}) makes them likely to be requested by an enterprise customer or auditor within 12 months.`,
    },
  ];

  return (
    <div className="results-v2">
      {/* ── Verdict bar — the headline, always visible ─────────── */}
      <header className="verdict-bar">
        <div className="vb-left">
          <button className="back-btn" onClick={onBack} aria-label="back">
            <svg viewBox="0 0 24 24" width="16" height="16"><path d="M19 12H5M11 6l-6 6 6 6" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
          </button>
          <div className="vb-company">
            <div className="vb-company-name">{profile.name}</div>
            <div className="vb-company-meta">{profile.sector} · {profile.stage} · {(+profile.team).toLocaleString()} team</div>
          </div>
        </div>
        <div className="vb-mid">
          <div className="vb-stat">
            <div className="vb-stat-lab">Recommendation</div>
            <div className="vb-stat-val vb-bundle">{result.bundle.name}</div>
          </div>
          <div className="vb-stat">
            <div className="vb-stat-lab">Annual band</div>
            <div className="vb-stat-val">
              ₹{Math.round(result.quote.total * 0.85).toLocaleString()}<span className="vb-dash">–</span>₹{Math.round(result.quote.total * 1.15).toLocaleString()}<span className="vb-unit"> L</span>
            </div>
          </div>
          <div className="vb-stat">
            <div className="vb-stat-lab">Risk</div>
            <div className="vb-stat-val">
              <span className={"vb-risk tier-" + result.tier.toLowerCase()}>{result.overall}</span>
              <span className="vb-risk-tier">{result.tier}</span>
            </div>
          </div>
        </div>
        <div className="vb-right">
          <a href="UW Workbench.html" className="rm-link">Hand to UW desk ↗</a>
          <button className="rm-link">Edit intake</button>
          <button className="rm-link">Save to pipeline</button>
        </div>
      </header>

      <div className="rm-page">

        {/* ── THE PITCH — talking points + pushback prep ─────── */}
        <section className="block pitch-block">
          <div className="block-head">
            <span className="block-num">A</span>
            <span className="block-label">The pitch</span>
            <span className="block-hint">Use these three lines on your founder call.</span>
            <button className="block-action" onClick={() => copy("pitch", result.rationale.map((r, i) => `${i+1}. ${r}`).join("\n\n"))}>
              {copied === "pitch" ? "Copied" : "Copy bullets"}
            </button>
          </div>

          <div className="pitch-bullets">
            {result.rationale.map((line, i) => (
              <div key={i} className="pitch-line">
                <span className="pitch-num">{String(i + 1).padStart(2, "0")}</span>
                <p>{line}</p>
              </div>
            ))}
          </div>

          <div className="pushback">
            <div className="pushback-head">
              <span className="pushback-dot" />
              <span className="pushback-title">If they push back</span>
              <span className="pushback-sub">3 scripted responses</span>
            </div>
            <div className="pushback-grid">
              {pushbackPrep.map((p, i) => (
                <div key={i} className="pushback-card">
                  <div className="pb-q">"{p.q}"</div>
                  <div className="pb-a">{p.a}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── THE MESSAGE — pre-drafted, ready to fire ────────── */}
        <section className="block message-block">
          <div className="block-head">
            <span className="block-num">B</span>
            <span className="block-label">The message</span>
            <span className="block-hint">Pre-drafted. Edit inline or send as-is.</span>
            <div className="block-actions">
              <button className="rm-link sm" onClick={() => setEditingEmail(!editingEmail)}>
                {editingEmail ? "Done editing" : "Edit"}
              </button>
              <button className="rm-link sm" onClick={() => copy("email", emailBody)}>
                {copied === "email" ? "Copied" : "Copy"}
              </button>
            </div>
          </div>

          <div className="message-card">
            <div className="msg-meta-row">
              <span className="msg-meta-l">To</span>
              <span className="msg-meta-v">{(profile.name || "founder").toLowerCase().replace(/\s+/g, "")}@founder.co</span>
            </div>
            <div className="msg-meta-row">
              <span className="msg-meta-l">Subject</span>
              <span className="msg-meta-v msg-subject">{result.email.subject}</span>
            </div>
            <div className="msg-divider" />
            {editingEmail ? (
              <textarea
                className="msg-textarea"
                value={emailBody}
                onChange={(e) => setEmailBody(e.target.value)}
                rows={emailBody.split("\n").length + 1}
              />
            ) : (
              <pre className="msg-body">{emailBody}</pre>
            )}
          </div>

          <div className="send-bar">
            <button className="cta-btn cta-lg">
              Send email
              <svg viewBox="0 0 24 24" width="16" height="16"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4z" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
            </button>
            <button className="rm-link">Send via WhatsApp</button>
            <button className="rm-link">Schedule for tomorrow 9 AM</button>
          </div>
        </section>

        {/* ── PROOF DRAWERS — supporting evidence, collapsed ──── */}
        <section className="proof-block">
          <div className="proof-head">
            <span className="block-num">C</span>
            <span className="block-label">The proof</span>
            <span className="block-hint">Expand only when you need the detail.</span>
          </div>

          <div className="drawers">
            <Drawer
              open={openDrawer === "rationale"}
              onToggle={() => setOpenDrawer(openDrawer === "rationale" ? null : "rationale")}
              title="Why this bundle, not another"
              summary={`${result.alternatives.length} alternatives evaluated`}
            >
              <div className="alt-grid">
                <div className="alt-card alt-winner">
                  <div className="alt-tag">Chosen</div>
                  <div className="alt-name">{result.bundle.name}</div>
                  <div className="alt-reason">{result.bundle.tagline} · matches top {result.topRisks.length} exposures.</div>
                </div>
                {result.alternatives.map((a) => (
                  <div key={a.id} className="alt-card">
                    <div className="alt-tag alt-tag-rej">Not chosen</div>
                    <div className="alt-name">{a.name}</div>
                    <div className="alt-reason">{a.rejectReason}</div>
                  </div>
                ))}
              </div>
            </Drawer>

            <Drawer
              open={openDrawer === "risk"}
              onToggle={() => setOpenDrawer(openDrawer === "risk" ? null : "risk")}
              title="Full risk profile"
              summary={`13 dimensions · top exposures: ${result.topRisks.slice(0, 3).join(", ")}`}
            >
              <RiskHeatmap scores={result.scores} />
              {result.triggers.length > 0 && (
                <div className="triggers-inline">
                  <div className="trig-head">Regulatory triggers detected</div>
                  <ul className="trig-list">
                    {result.triggers.map((t, i) => (
                      <li key={i} className="trig-item">
                        <span className="trig-pin" />
                        <div>
                          <div className="trig-label">{t.label}</div>
                          <div className="trig-note">{t.note}</div>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </Drawer>

            <Drawer
              open={openDrawer === "covers"}
              onToggle={() => setOpenDrawer(openDrawer === "covers" ? null : "covers")}
              title="Cover-by-cover pricing"
              summary={`${result.quote.lines.length} covers · ₹${result.quote.total.toFixed(2)} L total`}
            >
              <div className="quote-table compact">
                <div className="qt-head">
                  <span>Cover</span>
                  <span>Sum insured</span>
                  <span>Annual premium</span>
                </div>
                {result.quote.lines.map((l) => (
                  <div key={l.key} className={"qt-row" + (l.mandatory ? "" : " qt-opt")}>
                    <span className="qt-cell qt-name">
                      <span className={"qt-dot " + (l.mandatory ? "qt-dot-m" : "qt-dot-o")} />
                      {l.label}
                      {!l.mandatory && <span className="qt-opt-tag">opt.</span>}
                    </span>
                    <span className="qt-cell qt-si">₹{l.si} Cr</span>
                    <span className="qt-cell qt-prem">₹{l.premium.toFixed(2)} L</span>
                  </div>
                ))}
                <div className="qt-tot"><span>Subtotal</span><span></span><span>₹{result.quote.subtotal.toFixed(2)} L</span></div>
                <div className="qt-tot qt-tot-discount"><span>Bundle discount (8%)</span><span></span><span>− ₹{result.quote.discount.toFixed(2)} L</span></div>
                <div className="qt-tot"><span>GST (18%)</span><span></span><span>+ ₹{result.quote.gst.toFixed(2)} L</span></div>
                <div className="qt-final"><span>Total payable</span><span></span><span>₹{result.quote.total.toFixed(2)} L</span></div>
              </div>
            </Drawer>

            <Drawer
              open={openDrawer === "uw"}
              onToggle={() => setOpenDrawer(openDrawer === "uw" ? null : "uw")}
              title="Hand off to underwriter"
              summary="1 warning · 2 declarations needed"
              action={<button className="rm-link sm">Send to UW desk</button>}
            >
              <div className="uw-grid">
                <div className="uw-row uw-clean-row">
                  <span className="uw-pin uw-clean">●</span>
                  <div>
                    <div className="uw-row-title">Cyber SI within delegated authority</div>
                    <div className="uw-row-sub">No referral needed.</div>
                  </div>
                </div>
                <div className="uw-row uw-warn-row">
                  <span className="uw-pin uw-warn">●</span>
                  <div>
                    <div className="uw-row-title">D&amp;O retro date confirmation needed</div>
                    <div className="uw-row-sub">Founder needs to provide first incorporation date.</div>
                  </div>
                </div>
                <div className="uw-row uw-clean-row">
                  <span className="uw-pin uw-clean">●</span>
                  <div>
                    <div className="uw-row-title">No aggregate exposure breach</div>
                    <div className="uw-row-sub">Sector and stage caps healthy.</div>
                  </div>
                </div>
                <div className="uw-row uw-info-row">
                  <span className="uw-pin uw-info">●</span>
                  <div>
                    <div className="uw-row-title">Founder share-cap declaration recommended</div>
                    <div className="uw-row-sub">Standard ask for Series A+.</div>
                  </div>
                </div>
              </div>
            </Drawer>
          </div>
        </section>

        <footer className="rm-foot">
          <span>Indicative output · not a binding quote · pending UW review</span>
          <span>{new Date().toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" })}</span>
        </footer>
      </div>
    </div>
  );
}

// ── Drawer ─────────────────────────────────────────────────────────────
function Drawer({ open, onToggle, title, summary, action, children }) {
  return (
    <div className={"drawer" + (open ? " drawer-open" : "")}>
      <button className="drawer-head" onClick={onToggle}>
        <span className={"drawer-chev" + (open ? " open" : "")}>
          <svg viewBox="0 0 24 24" width="14" height="14"><path d="M9 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </span>
        <span className="drawer-title">{title}</span>
        <span className="drawer-summary">{summary}</span>
        {action && <span onClick={(e) => e.stopPropagation()}>{action}</span>}
      </button>
      {open && <div className="drawer-body">{children}</div>}
    </div>
  );
}

// ── Risk Heatmap ──────────────────────────────────────────────────────
function RiskHeatmap({ scores }) {
  const dims = window.RISK_DIMENSIONS;
  return (
    <div className="heatmap">
      {dims.map((d) => {
        const v = scores[d.key] || 0;
        const tier = v >= 70 ? "high" : v >= 50 ? "mid" : v >= 30 ? "low" : "min";
        return (
          <div key={d.key} className={"heat-cell heat-" + tier}>
            <div className="heat-num">{v}</div>
            <div className="heat-lab">{d.label}</div>
            <div className="heat-short">{d.short}</div>
          </div>
        );
      })}
    </div>
  );
}

Object.assign(window, { Results });
