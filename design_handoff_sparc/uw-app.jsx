// Underwriter workbench — root + queue (left pane) + top bar.

const { useState: useSU, useMemo: useMU, useEffect: useEU } = React;

function UWApp() {
  const [queue, setQueue] = useSU(window.UW_QUEUE);
  const [activeId, setActiveId] = useSU(queue[0].caseId);
  const [filter, setFilter] = useSU("all"); // all | mine | high
  const [resolutions, setResolutions] = useSU({}); // { [caseId]: { decision, premium, note } }

  const tweaks = window.useTweaks ? window.useTweaks({ palette: "default", density: "comfortable", displayFont: "Space Grotesk" }) : [{ palette: "default", density: "comfortable", displayFont: "Space Grotesk" }, () => {}];
  const [t, setTweak] = tweaks;

  useEU(() => {
    const root = document.documentElement;
    if (t.palette && t.palette !== "default") {
      root.setAttribute("data-palette", t.palette);
    } else {
      root.removeAttribute("data-palette");
    }
    root.setAttribute("data-density", t.density);
  }, [t]);

  const filtered = useMU(() => {
    if (filter === "high") return queue.filter((c) => c.priority === "high");
    return queue;
  }, [queue, filter]);

  const activeCase = useMU(() => {
    const item = queue.find((c) => c.caseId === activeId);
    if (!item) return null;
    return window.uwGetCase(item);
  }, [queue, activeId]);

  const pendingCount = queue.filter((c) => c.status === "pending-uw").length;
  const highCount = queue.filter((c) => c.priority === "high").length;

  const resolveCase = (caseId, decision, note, premium) => {
    setResolutions({ ...resolutions, [caseId]: { decision, note, premium, at: new Date() } });
    // remove from queue
    setQueue((q) => q.filter((c) => c.caseId !== caseId));
    const next = filtered.find((c) => c.caseId !== caseId);
    if (next) setActiveId(next.caseId);
  };

  const TweaksPanel = window.TweaksPanel;
  const TweakSection = window.TweakSection;
  const TweakRadio = window.TweakRadio;

  return (
    <div className="uw-shell">
      {/* ── Top bar ─────────────────────────────────────────────── */}
      <header className="uw-topbar">
        <div className="uw-tb-left">
          <div className="rm-mark"><svg viewBox="0 0 32 32" width="20" height="20"><circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="1.5"/><circle cx="16" cy="16" r="5" fill="currentColor"/></svg></div>
          <div className="uw-tb-wordmark">
            <div className="rm-wordmark">SPARC</div>
            <div className="uw-tb-context">Underwriting workbench</div>
          </div>
          <div className="rm-divider" />
          <div className="uw-tb-stats">
            <span className="uw-tb-stat"><span className="uw-tb-num">{pendingCount}</span> pending</span>
            <span className="uw-tb-stat"><span className="uw-tb-num">{highCount}</span> high priority</span>
            <span className="uw-tb-stat"><span className="uw-tb-num">{(window.UW_DESK.utilization * 100).toFixed(0)}%</span> capacity</span>
          </div>
        </div>
        <div className="uw-tb-right">
          <div className="uw-tb-search">
            <svg viewBox="0 0 24 24" width="14" height="14"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="1.5"/><path d="M20 20l-4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>
            <input placeholder="Search cases, companies, RMs…" />
            <span className="uw-tb-kbd">/</span>
          </div>
          <a href="SPARC Redesign.html" className="rm-link">RM view ↗</a>
          <div className="uw-tb-user">
            <div className="uw-avatar">{window.UW_DESK.user.name.split(" ").map((p) => p[0]).join("")}</div>
            <div className="uw-tb-user-meta">
              <div className="uw-tb-user-name">{window.UW_DESK.user.name}</div>
              <div className="uw-tb-user-id">{window.UW_DESK.user.id}</div>
            </div>
          </div>
        </div>
      </header>

      {/* ── 3-pane workspace ───────────────────────────────────── */}
      <div className="uw-workspace">
        {/* Left: queue */}
        <aside className="uw-queue">
          <div className="uw-queue-head">
            <span className="uw-queue-title">Queue</span>
            <span className="uw-queue-count">{filtered.length}</span>
          </div>
          <div className="uw-filters">
            <button className={"uw-filter" + (filter === "all" ? " on" : "")} onClick={() => setFilter("all")}>All</button>
            <button className={"uw-filter" + (filter === "high" ? " on" : "")} onClick={() => setFilter("high")}>High</button>
            <button className={"uw-filter" + (filter === "mine" ? " on" : "")} onClick={() => setFilter("mine")}>Mine</button>
          </div>
          <div className="uw-queue-list">
            {filtered.length === 0 ? (
              <div className="uw-queue-empty">
                <div className="uw-queue-empty-mark">✓</div>
                Queue clear.<br />Take a break.
              </div>
            ) : (
              filtered.map((c) => (
                <QueueItem
                  key={c.caseId}
                  item={c}
                  active={c.caseId === activeId}
                  onClick={() => setActiveId(c.caseId)}
                />
              ))
            )}
          </div>
          <div className="uw-queue-foot">
            <div className="uw-foot-row">
              <span>Today's resolved</span>
              <span className="uw-foot-num">{Object.keys(resolutions).length}</span>
            </div>
            <div className="uw-foot-row">
              <span>SLA at risk</span>
              <span className="uw-foot-num uw-num-warn">2</span>
            </div>
          </div>
        </aside>

        {/* Center + right: case + decision */}
        {activeCase ? (
          <UWCase
            key={activeCase.caseId}
            caseData={activeCase}
            onResolve={(decision, note, premium) => resolveCase(activeCase.caseId, decision, note, premium)}
          />
        ) : (
          <div className="uw-empty">
            <div className="uw-empty-title">No case selected</div>
            <div className="uw-empty-sub">Pick one from the queue.</div>
          </div>
        )}
      </div>

      {TweaksPanel && (
        <TweaksPanel title="Tweaks">
          <TweakSection title="Palette">
            <TweakRadio label="Surface" value={t.palette} options={["default", "midnight", "obsidian", "mono"]} onChange={(v) => setTweak("palette", v)} />
            <TweakRadio label="Density" value={t.density} options={["comfortable", "compact"]} onChange={(v) => setTweak("density", v)} />
          </TweakSection>
        </TweaksPanel>
      )}
    </div>
  );
}

// ── Queue item ────────────────────────────────────────────────────────
function QueueItem({ item, active, onClick }) {
  const slaPct = item.sla / item.slaTotal;
  const slaTier = slaPct < 0.2 ? "crit" : slaPct < 0.4 ? "warn" : "ok";
  const fmtSla = (m) => m < 60 ? `${m}m` : `${Math.floor(m/60)}h ${m%60}m`;

  return (
    <button className={"uw-queue-item" + (active ? " active" : "") + (item.status === "referred" ? " referred" : "")} onClick={onClick}>
      <div className="uqi-top">
        <span className="uqi-id">{item.caseId}</span>
        <span className={"uqi-sla uqi-sla-" + slaTier}>
          {item.status === "referred" ? "REF" : fmtSla(item.sla)}
        </span>
      </div>
      <div className="uqi-company">{item.company}</div>
      <div className="uqi-bundle">{item.bundle}</div>
      <div className="uqi-meta">
        <span className="uqi-amount">₹ {item.indicative} L</span>
        <span className="uqi-dot">·</span>
        <span className="uqi-rm">{item.rmInitials}</span>
        <span className="uqi-time">{item.submittedAgo}</span>
      </div>
      {item.priority === "high" && <span className="uqi-prio" />}
    </button>
  );
}

const root = ReactDOM.createRoot(document.getElementById("app"));
root.render(<UWApp />);
