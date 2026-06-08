(function () {
  const app = document.getElementById("app");
  const defaultBookPath = "C:\\Users\\shrij\\Downloads\\Book5.xlsx";
  const defaultDictPath = "C:\\Users\\shrij\\Downloads\\E.LIABILITY Data Dictionary FY2024-25 (1).xlsx";

  const state = {
    payload: null,
    sourceMode: "live",
    filters: {
      product: "all",
      state: "all",
      bookType: "all",
    },
    sort: {
      accounts: { key: "priority", dir: "desc" },
      renewals: { key: "days_to_renewal", dir: "asc" },
    },
  };

  function safeText(value) {
    return String(value == null ? "" : value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatINR(value) {
    if (value == null || Number.isNaN(Number(value))) return "Not available";
    const amount = Number(value);
    const sign = amount < 0 ? "-" : "";
    const absolute = Math.abs(amount);
    if (absolute >= 10000000) return `${sign}₹ ${(absolute / 10000000).toFixed(2)} Cr`;
    if (absolute >= 100000) return `${sign}₹ ${(absolute / 100000).toFixed(2)} L`;
    return `${sign}₹ ${absolute.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;
  }

  function formatDate(value) {
    if (!value) return "—";
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
  }

  function toneTag(tone) {
    const map = {
      critical: "rm-tag rm-tag--critical",
      high: "rm-tag rm-tag--critical",
      warning: "rm-tag rm-tag--warning",
      positive: "rm-tag rm-tag--positive",
      accent: "rm-tag rm-tag--accent",
      neutral: "rm-tag rm-tag--neutral",
      blue: "tone-blue",
      red: "tone-red",
      amber: "tone-amber",
      green: "tone-green",
      slate: "tone-slate",
      muted: "rm-tag rm-tag--neutral",
    };
    return map[tone] || "rm-tag rm-tag--neutral";
  }

  function currentAsOf() {
    return new Date((state.payload && state.payload.meta && state.payload.meta.as_of) || new Date().toISOString().slice(0, 10));
  }

  function getPolicies() {
    if (!state.payload) return [];
    const policies = state.payload.accounts || [];
    return policies.filter((row) => {
      if (state.filters.product !== "all" && row.product !== state.filters.product) return false;
      if (state.filters.state !== "all" && row.state !== state.filters.state) return false;
      if (state.filters.bookType !== "all" && row.book_type !== state.filters.bookType) return false;
      return true;
    });
  }

  function summarizePolicies(policies) {
    const asOf = currentAsOf();
    const renewals = policies.filter((row) => row.days_to_renewal != null && row.days_to_renewal >= 0 && row.days_to_renewal <= 90);
    const renewals45 = policies.filter((row) => row.days_to_renewal != null && row.days_to_renewal >= 0 && row.days_to_renewal <= 45);
    const crossSell = policies.filter((row) => Array.isArray(row.cross_sell) && row.cross_sell.length);
    const escalations = policies.filter((row) => row.action === "Refer to underwriting");
    const multiLoc = policies.filter((row) => Number(row.locations || 0) > 1);
    const highSI = policies.filter((row) => Number(row.sum_insured || 0) >= 20000000);
    const totalPremium = policies.reduce((sum, row) => sum + Number(row.premium || 0), 0);
    const topState = Object.entries(
      policies.reduce((acc, row) => {
        const key = row.state || "Unknown";
        acc[key] = (acc[key] || 0) + Number(row.premium || 0);
        return acc;
      }, {})
    ).sort((a, b) => b[1] - a[1])[0];
    const insight = policies.length
      ? `This cut of the book is strongest as a renewal and portfolio-shaping view rather than a claims profitability view. ${renewals.length} renewals fall inside the next 90 days, ${crossSell.length} accounts show adjacent-cover potential worth ${formatINR(crossSell.reduce((sum, row) => sum + Number(row.cross_sell_value || 0), 0))}, and ${escalations.length} accounts need underwriting attention from endorsement signals.${topState ? ` ${topState[0]} carries the largest premium concentration in this filtered view.` : ""}`
      : "No policies match the current filters.";
    return {
      asOf,
      totalPremium,
      renewals,
      renewals45,
      crossSell,
      escalations,
      multiLoc,
      highSI,
      topState,
      insight,
    };
  }

  function productRollup(policies) {
    const map = new Map();
    policies.forEach((row) => {
      const key = row.product || "Unknown product";
      if (!map.has(key)) {
        map.set(key, { product: key, policy_count: 0, premium: 0, renewals_90d: 0, cross_sell_potential: 0 });
      }
      const item = map.get(key);
      item.policy_count += 1;
      item.premium += Number(row.premium || 0);
      item.cross_sell_potential += Number(row.cross_sell_value || 0);
      if (row.days_to_renewal != null && row.days_to_renewal >= 0 && row.days_to_renewal <= 90) item.renewals_90d += 1;
    });
    return [...map.values()].sort((a, b) => b.premium - a.premium);
  }

  function geographyRollup(policies) {
    const map = new Map();
    policies.forEach((row) => {
      const key = row.state || "Unknown";
      if (!map.has(key)) {
        map.set(key, { state: key, policy_count: 0, premium: 0, renewals_90d: 0, cross_sell_potential: 0 });
      }
      const item = map.get(key);
      item.policy_count += 1;
      item.premium += Number(row.premium || 0);
      item.cross_sell_potential += Number(row.cross_sell_value || 0);
      if (row.days_to_renewal != null && row.days_to_renewal >= 0 && row.days_to_renewal <= 90) item.renewals_90d += 1;
    });
    return [...map.values()].sort((a, b) => b.premium - a.premium);
  }

  function occupancyRollup(policies) {
    const map = new Map();
    policies.forEach((row) => {
      const key = row.occupancy || "Unknown occupancy";
      if (!map.has(key)) {
        map.set(key, { occupancy: key, policy_count: 0, premium: 0, high_priority: 0 });
      }
      const item = map.get(key);
      item.policy_count += 1;
      item.premium += Number(row.premium || 0);
      if (Number(row.priority || 0) >= 80) item.high_priority += 1;
    });
    return [...map.values()].sort((a, b) => b.premium - a.premium).slice(0, 8);
  }

  function focusStripFromPolicies(policies) {
    const summary = summarizePolicies(policies);
    return [
      {
        rank: 1,
        title: `Renew ${summary.renewals45.length} near-term accounts`,
        metric: formatINR(summary.renewals45.reduce((sum, row) => sum + Number(row.premium || 0), 0)),
        detail: "Premium exposed in the next 45 days.",
        tone: "blue",
      },
      {
        rank: 2,
        title: `Escalate ${summary.escalations.length} accounts to UW`,
        metric: formatINR(summary.escalations.reduce((sum, row) => sum + Math.abs(Number(row.premium || 0)), 0)),
        detail: "Cancellation or adverse endorsement signal.",
        tone: "red",
      },
      {
        rank: 3,
        title: `Cross-sell ${summary.crossSell.length} accounts`,
        metric: formatINR(summary.crossSell.reduce((sum, row) => sum + Number(row.cross_sell_value || 0), 0)),
        detail: "Indicative adjacent-cover opportunity.",
        tone: "amber",
      },
      {
        rank: 4,
        title: `Review ${summary.highSI.length} large SI risks`,
        metric: formatINR(summary.highSI.reduce((sum, row) => sum + Number(row.sum_insured || 0), 0)),
        detail: "High value property exposures in the current cut.",
        tone: "slate",
      },
      {
        rank: 5,
        title: `Monitor ${summary.multiLoc.length} multi-location risks`,
        metric: formatINR(summary.multiLoc.reduce((sum, row) => sum + Number(row.premium || 0), 0)),
        detail: "Broader footprint can justify service and bundle expansion.",
        tone: "green",
      },
    ];
  }

  function footerActionsFromPolicies(policies) {
    const summary = summarizePolicies(policies);
    const storage = policies.filter((row) => /storage|hazardous/i.test(row.occupancy || ""));
    const dataOps = policies.filter((row) => /data processing|call center|business pro/i.test(row.occupancy || ""));
    const multiLoc = policies.filter((row) => Number(row.locations || 0) > 1);
    return [
      {
        title: "Lock in near-term renewals",
        impact: formatINR(summary.renewals.reduce((sum, row) => sum + Number(row.premium || 0), 0)),
        detail: `${summary.renewals.length} accounts expire inside 90 days in the current filtered view.`,
      },
      {
        title: "Escalate adverse endorsements",
        impact: formatINR(summary.escalations.reduce((sum, row) => sum + Math.abs(Number(row.premium || 0)), 0)),
        detail: `${summary.escalations.length} accounts show cancellation, negative premium, or corrective term signals.`,
      },
      {
        title: "Cross-sell storage and hazardous occupancies",
        impact: formatINR(storage.reduce((sum, row) => sum + Number(row.cross_sell_value || 0), 0)),
        detail: "Lead with liability, burglary, and business interruption extensions where the exposure warrants it.",
      },
      {
        title: "Convert digital occupancies into cyber conversations",
        impact: formatINR(dataOps.reduce((sum, row) => sum + Number(row.cross_sell_value || 0), 0)),
        detail: "Data-processing signals are the cleanest basis for cyber, D&O, and crime protection outreach.",
      },
      {
        title: "Bundle multi-location accounts earlier",
        impact: formatINR(multiLoc.reduce((sum, row) => sum + Number(row.premium || 0), 0)),
        detail: `${multiLoc.length} multi-location risks justify earlier bundle review and service planning.`,
      },
    ];
  }

  function buildKpis(policies) {
    const summary = summarizePolicies(policies);
    return [
      {
        label: "Net Written Premium",
        value: formatINR(summary.totalPremium),
        subtext: `${policies.length} policies in filtered view`,
        note: "Exact from Policy_Premium.",
      },
      {
        label: "Renewals Next 90 Days",
        value: String(summary.renewals.length),
        subtext: formatINR(summary.renewals.reduce((sum, row) => sum + Number(row.premium || 0), 0)),
        note: `As of ${formatDate(summary.asOf.toISOString())}.`,
      },
      {
        label: "Accounts to Escalate",
        value: String(summary.escalations.length),
        subtext: formatINR(summary.escalations.reduce((sum, row) => sum + Math.abs(Number(row.premium || 0)), 0)),
        note: "Rule-driven from endorsement and cancellation markers.",
      },
      {
        label: "Cross-sell Opportunities",
        value: String(summary.crossSell.length),
        subtext: formatINR(summary.crossSell.reduce((sum, row) => sum + Number(row.cross_sell_value || 0), 0)),
        note: "Indicative, inferred from occupancy and scale.",
      },
      {
        label: "Overall Loss Ratio",
        value: "Not available",
        subtext: "Claims extract missing",
        note: "Needs incurred and claims tables.",
      },
      {
        label: "Claim Frequency",
        value: "Not available",
        subtext: "Claims extract missing",
        note: "Cannot derive without claim rows.",
      },
    ];
  }

  function sortRows(rows, config) {
    const dir = config.dir === "asc" ? 1 : -1;
    const sorted = [...rows];
    sorted.sort((a, b) => {
      const av = a[config.key];
      const bv = b[config.key];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir;
      return String(av).localeCompare(String(bv)) * dir;
    });
    return sorted;
  }

  function buildCsv(rows) {
    const headers = ["account_name", "policy_number", "product", "state", "district", "premium", "sum_insured", "end_date", "days_to_renewal", "action", "cross_sell"];
    const lines = [headers.join(",")];
    rows.forEach((row) => {
      lines.push(
        headers
          .map((header) => {
            const value = Array.isArray(row[header]) ? row[header].join(" | ") : row[header];
            const cell = String(value == null ? "" : value).replace(/"/g, '""');
            return `"${cell}"`;
          })
          .join(",")
      );
    });
    return lines.join("\n");
  }

  function downloadText(filename, text, type) {
    const blob = new Blob([text], { type: type || "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function fetchDashboard() {
    const bookPath = document.getElementById("bookPath") ? document.getElementById("bookPath").value.trim() : defaultBookPath;
    const dictPath = document.getElementById("dictPath") ? document.getElementById("dictPath").value.trim() : defaultDictPath;
    renderLoading();
    const url = `/api/iib/rm-dashboard?book_path=${encodeURIComponent(bookPath)}&dictionary_path=${encodeURIComponent(dictPath)}`;
    try {
      const res = await fetch(url);
      const contentType = (res.headers.get("content-type") || "").toLowerCase();
      if (!contentType.includes("application/json")) {
        const raw = await res.text();
        const isHtml = raw.includes("<!DOCTYPE") || raw.includes("<html");
        throw new Error(
          isHtml
            ? "The server returned HTML instead of JSON."
            : `Unexpected response from server: ${raw.slice(0, 220)}`
        );
      }
      const payload = await res.json();
      if (!res.ok) throw new Error(payload.error || `Dashboard load failed (${res.status})`);
      state.payload = payload;
      state.sourceMode = "live";
      render();
      return;
    } catch (error) {
      const fallback = await fetch("iib_rm_dashboard_data.json");
      if (!fallback.ok) {
        throw new Error(`${error.message} Static fallback snapshot is also unavailable.`);
      }
      state.payload = await fallback.json();
      state.sourceMode = "snapshot";
      render();
      return;
    }
  }

  function renderLoading() {
    app.innerHTML = `
      <div class="rm-loading">
        <div class="rm-loading__ring"></div>
        <div>
          <strong>Loading RM dashboard</strong>
          <p>Reading workbook structure and compiling decision signals.</p>
        </div>
      </div>
    `;
  }

  function renderError(message) {
    app.innerHTML = `
      <div class="rm-shell">
        <div class="rm-empty">
          <h2>Could not load workbook intelligence</h2>
          <p>${safeText(message)}</p>
          <p class="rm-small">Check the workbook paths and make sure the local server process can read those files.</p>
        </div>
      </div>
    `;
  }

  function render() {
    const payload = state.payload;
    const policies = getPolicies();
    const summary = summarizePolicies(policies);
    const focus = focusStripFromPolicies(policies);
    const kpis = buildKpis(policies);
    const products = productRollup(policies);
    const geographies = geographyRollup(policies);
    const occupancy = occupancyRollup(policies);
    const crossSell = policies.filter((row) => Array.isArray(row.cross_sell) && row.cross_sell.length).slice(0, 8);
    const accountRows = sortRows(policies, state.sort.accounts).slice(0, 12);
    const renewalRows = sortRows(
      policies.filter((row) => row.days_to_renewal != null && row.days_to_renewal >= 0),
      state.sort.renewals
    ).slice(0, 12);
    const footerActions = footerActionsFromPolicies(policies);

    const productsOptions = [...new Set((payload.accounts || []).map((row) => row.product).filter(Boolean))].sort();
    const stateOptions = [...new Set((payload.accounts || []).map((row) => row.state).filter(Boolean))].sort();
    const bookTypeOptions = [...new Set((payload.accounts || []).map((row) => row.book_type).filter(Boolean))].sort();
    const dictSheets = payload.dictionary_workbook.sheets || [];

    app.innerHTML = `
      <div class="rm-topbar">
        <div>
          <div class="rm-brand">
            <div class="rm-brand__mark">IL</div>
            <div class="rm-brand__copy">
              <span>ICICI Lombard x SPARC</span>
              <strong>RM Decision Intelligence Dashboard</strong>
            </div>
          </div>
          <h1 class="rm-title">Workbook intelligence for relationship managers</h1>
          <p class="rm-subtitle">
            This dashboard reads the actual ICICI / IIB workbook structure, converts the policy book into an RM-ready operating view,
            and is explicit about which outputs are exact, inferred, or currently unavailable.
          </p>
        </div>
        <div class="rm-topbar__meta">
          <div class="rm-status-grid">
            <div class="rm-mini-stat">
              <span>Sample workbook</span>
              <strong>${safeText(payload.sample_workbook.workbook)}</strong>
              <p>${payload.sample_workbook.row_count} rows · ${payload.sample_workbook.column_count} fields</p>
            </div>
            <div class="rm-mini-stat">
              <span>Dictionary workbook</span>
              <strong>${safeText(payload.dictionary_workbook.workbook)}</strong>
              <p>${dictSheets.length} sheets · ${payload.dictionary_workbook.policy_fields.length} policy fields mapped</p>
            </div>
            <div class="rm-mini-stat">
              <span>Filtered premium</span>
              <strong>${formatINR(summary.totalPremium)}</strong>
              <p>${policies.length} policies · ${state.filters.product === "all" ? "all products" : safeText(state.filters.product)}</p>
            </div>
            <div class="rm-mini-stat">
              <span>Claims readiness</span>
              <strong>${safeText(payload.claims_section.available ? "Available" : "Pending")}</strong>
              <p>${safeText(payload.claims_section.available ? "Claims metrics can be computed." : "Claims extract needed for loss metrics.")}</p>
            </div>
            <div class="rm-mini-stat">
              <span>Data source</span>
              <strong>${state.sourceMode === "live" ? "Live API" : "Static snapshot"}</strong>
              <p>${state.sourceMode === "live" ? "Reading workbook intelligence through the local API." : "Loaded from a prebuilt snapshot because the live API route is unavailable on this server."}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="rm-controls">
        <div class="rm-controls__grid">
          <label class="rm-control rm-control--wide">
            <span class="rm-label">Sample workbook path</span>
            <input id="bookPath" class="rm-input" value="${safeText(payload.meta.book_path || defaultBookPath)}" />
          </label>
          <label class="rm-control rm-control--wide">
            <span class="rm-label">Dictionary workbook path</span>
            <input id="dictPath" class="rm-input" value="${safeText(payload.meta.dictionary_path || defaultDictPath)}" />
          </label>
          <label class="rm-control">
            <span class="rm-label">Product / LOB</span>
            <select id="filterProduct" class="rm-select">
              <option value="all">All</option>
              ${productsOptions.map((item) => `<option value="${safeText(item)}" ${state.filters.product === item ? "selected" : ""}>${safeText(item)}</option>`).join("")}
            </select>
          </label>
          <label class="rm-control">
            <span class="rm-label">State / territory</span>
            <select id="filterState" class="rm-select">
              <option value="all">All</option>
              ${stateOptions.map((item) => `<option value="${safeText(item)}" ${state.filters.state === item ? "selected" : ""}>${safeText(item)}</option>`).join("")}
            </select>
          </label>
          <label class="rm-control">
            <span class="rm-label">Book type</span>
            <select id="filterBookType" class="rm-select">
              <option value="all">All</option>
              ${bookTypeOptions.map((item) => `<option value="${safeText(item)}" ${state.filters.bookType === item ? "selected" : ""}>${safeText(item)}</option>`).join("")}
            </select>
          </label>
          <div class="rm-control">
            <span class="rm-label">As of</span>
            <input class="rm-input" value="${safeText(formatDate(payload.meta.as_of))}" disabled />
          </div>
        </div>
        <div class="rm-actions">
          <button class="rm-btn rm-btn--primary" id="reloadDashboard">Reload workbook</button>
          <button class="rm-btn rm-btn--secondary" id="downloadAccounts">Download filtered accounts CSV</button>
          <button class="rm-btn" id="downloadSummary">Download summary JSON</button>
          <button class="rm-btn" id="printDashboard">Print / Save PDF</button>
          <button class="rm-btn" id="resetFilters">Reset filters</button>
        </div>
      </div>

      <div class="rm-banner">
        <div class="rm-banner__badge">AI</div>
        <div>
          <h2>RM insight banner</h2>
          <p>${safeText(summary.insight)}</p>
        </div>
      </div>

      <section class="rm-focus">
        <div class="rm-focus__title">
          <div>
            <h3>Today’s RM focus</h3>
            <p>Priority actions generated deterministically from premium, renewal timing, occupancy, sum insured, geography, and endorsement signals.</p>
          </div>
          <div class="rm-pill-list">
            <span class="rm-pill">Exact: premium / renewal / geography</span>
            <span class="rm-pill">Inferred: cross-sell / escalation</span>
          </div>
        </div>
        <div class="rm-focus__grid">
          ${focus.map((item) => `
            <article class="rm-focus-card">
              <div class="rm-focus-card__rank ${toneTag(item.tone)}">${item.rank}</div>
              <strong>${safeText(item.title)}</strong>
              <div class="rm-focus-card__metric">${safeText(item.metric)}</div>
              <p>${safeText(item.detail)}</p>
            </article>
          `).join("")}
        </div>
      </section>

      <section class="rm-kpis">
        ${kpis.map((kpi) => `
          <article class="rm-kpi">
            <div class="rm-kpi__label">${safeText(kpi.label)}</div>
            <div class="rm-kpi__value">${safeText(kpi.value)}</div>
            <div class="rm-kpi__subtext">${safeText(kpi.subtext)}</div>
            <div class="rm-kpi__note">${safeText(kpi.note)}</div>
          </article>
        `).join("")}
      </section>

      <section class="rm-grid">
        <div class="rm-stack">
          <div class="rm-section">
            <div class="rm-section__header">
              <div>
                <h3>Account prioritization</h3>
                <p>Ranked for RM action with clear reasons. Where client name is absent in the sample, the risk location becomes the account label.</p>
              </div>
              <div class="rm-pill-list">
                <span class="rm-pill">Sorted by ${safeText(state.sort.accounts.key)}</span>
              </div>
            </div>
            <div class="rm-table-wrap">
              <table class="rm-table" id="accountsTable">
                <thead>
                  <tr>
                    <th data-sort="account_name">Account / policy</th>
                    <th data-sort="product">Product</th>
                    <th data-sort="premium">Premium</th>
                    <th data-sort="state">State</th>
                    <th data-sort="days_to_renewal">Renewal</th>
                    <th>Suggested RM action</th>
                  </tr>
                </thead>
                <tbody>
                  ${accountRows.map((row) => `
                    <tr>
                      <td>
                        <div class="rm-account">
                          <strong>${safeText(row.account_name)}</strong>
                          <span class="rm-mono">${safeText(row.policy_number)}</span>
                          <span>${safeText(row.occupancy)}</span>
                        </div>
                      </td>
                      <td>${safeText(row.product)}</td>
                      <td class="rm-mono">${safeText(formatINR(row.premium))}</td>
                      <td>${safeText(row.state)}</td>
                      <td>
                        <div class="rm-account">
                          <strong>${safeText(formatDate(row.end_date))}</strong>
                          <span>${row.days_to_renewal == null ? "No renewal date" : `${row.days_to_renewal} days`}</span>
                        </div>
                      </td>
                      <td>
                        <span class="${toneTag(row.tone)}">${safeText(row.action)}</span>
                        <div class="rm-subtle" style="margin-top:8px;">${safeText(row.rationale)}</div>
                      </td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          </div>

          <div class="rm-section">
            <div class="rm-section__header">
              <div>
                <h3>Renewal radar</h3>
                <p>Upcoming renewals are ranked by urgency first, then by premium size.</p>
              </div>
              <div class="rm-pill-list">
                <span class="rm-pill">${renewalRows.length} visible renewals</span>
              </div>
            </div>
            <div class="rm-table-wrap">
              <table class="rm-table" id="renewalsTable">
                <thead>
                  <tr>
                    <th data-sort="account_name">Account</th>
                    <th data-sort="end_date">Expiry</th>
                    <th data-sort="premium">Premium</th>
                    <th data-sort="days_to_renewal">Days</th>
                    <th>Best next action</th>
                  </tr>
                </thead>
                <tbody>
                  ${renewalRows.map((row) => `
                    <tr>
                      <td>
                        <div class="rm-account">
                          <strong>${safeText(row.account_name)}</strong>
                          <span>${safeText(row.product)}</span>
                        </div>
                      </td>
                      <td class="rm-mono">${safeText(formatDate(row.end_date))}</td>
                      <td class="rm-mono">${safeText(formatINR(row.premium))}</td>
                      <td>${row.days_to_renewal == null ? "—" : row.days_to_renewal}</td>
                      <td>
                        <span class="${toneTag(row.tone)}">${safeText(row.action)}</span>
                      </td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="rm-stack">
          <div class="rm-section">
            <div class="rm-section__header">
              <div>
                <h3>Product / LOB view</h3>
                <p>Profitability ratios are intentionally withheld until claim rows exist.</p>
              </div>
            </div>
            <div class="rm-table-wrap">
              <table class="rm-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Policies</th>
                    <th>Premium</th>
                    <th>Renewals</th>
                    <th>Cross-sell potential</th>
                  </tr>
                </thead>
                <tbody>
                  ${products.slice(0, 8).map((row) => `
                    <tr>
                      <td>${safeText(row.product)}</td>
                      <td>${row.policy_count}</td>
                      <td class="rm-mono">${safeText(formatINR(row.premium))}</td>
                      <td>${row.renewals_90d}</td>
                      <td class="rm-mono">${safeText(formatINR(row.cross_sell_potential))}</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          </div>

          <div class="rm-section">
            <div class="rm-section__header">
              <div>
                <h3>Cross-sell and bundle openings</h3>
                <p>Rule-driven product gaps derived from occupancy, scale, geography, and renewal timing.</p>
              </div>
            </div>
            <div class="rm-note-list">
              ${crossSell.length ? crossSell.map((row) => `
                <article class="rm-note">
                  <strong>${safeText(row.account_name)}</strong>
                  <p>${safeText(row.cross_sell.join(" · "))} · ${safeText(formatINR(row.cross_sell_value))} indicative potential</p>
                  <p class="rm-small" style="margin-top:6px;">${safeText(row.rationale)}</p>
                </article>
              `).join("") : `<div class="rm-empty"><p>No cross-sell opportunities in the current filtered view.</p></div>`}
            </div>
          </div>
        </div>
      </section>

      <section class="rm-grid">
        <div class="rm-stack">
          <div class="rm-section">
            <div class="rm-section__header">
              <div>
                <h3>Geography and occupancy concentration</h3>
                <p>Maps are intentionally avoided unless the location fidelity is strong enough; this sample is more reliable as ranked state and occupancy tables.</p>
              </div>
            </div>
            <div class="rm-data-list" style="margin-bottom:14px;">
              ${geographies.slice(0, 3).map((row) => `
                <article class="rm-data-card">
                  <span>${safeText(row.state)}</span>
                  <strong>${safeText(formatINR(row.premium))}</strong>
                  <div class="rm-small">${row.policy_count} policies · ${row.renewals_90d} renewals inside 90 days</div>
                </article>
              `).join("")}
            </div>
            <div class="rm-table-wrap">
              <table class="rm-table">
                <thead>
                  <tr>
                    <th>State</th>
                    <th>Policies</th>
                    <th>Premium</th>
                    <th>Renewals</th>
                    <th>Cross-sell potential</th>
                  </tr>
                </thead>
                <tbody>
                  ${geographies.map((row) => `
                    <tr>
                      <td>${safeText(row.state)}</td>
                      <td>${row.policy_count}</td>
                      <td class="rm-mono">${safeText(formatINR(row.premium))}</td>
                      <td>${row.renewals_90d}</td>
                      <td class="rm-mono">${safeText(formatINR(row.cross_sell_potential))}</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          </div>

          <div class="rm-section">
            <div class="rm-section__header">
              <div>
                <h3>Claims leakage and adverse claims</h3>
                <p>Rendered honestly from current availability.</p>
              </div>
            </div>
            <div class="rm-empty">
              <p>${safeText(payload.claims_section.message)}</p>
              <p class="rm-small">The liability dictionary already exposes a future Claims sheet. Once claim extracts arrive, this section can be upgraded to loss ratio, reserve pressure, severe claim clustering, and litigation alerts without redesigning the dashboard shell.</p>
            </div>
          </div>
        </div>

        <div class="rm-stack">
          <div class="rm-section">
            <div class="rm-section__header">
              <div>
                <h3>Occupancy / industry risk view</h3>
                <p>The sample workbook carries occupancy descriptions and industry codes more reliably than a clean client-segment taxonomy.</p>
              </div>
            </div>
            <div class="rm-table-wrap">
              <table class="rm-table">
                <thead>
                  <tr>
                    <th>Occupancy</th>
                    <th>Policies</th>
                    <th>Premium</th>
                    <th>High-priority accounts</th>
                  </tr>
                </thead>
                <tbody>
                  ${occupancy.map((row) => `
                    <tr>
                      <td>${safeText(row.occupancy)}</td>
                      <td>${row.policy_count}</td>
                      <td class="rm-mono">${safeText(formatINR(row.premium))}</td>
                      <td>${row.high_priority}</td>
                    </tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          </div>

          <div class="rm-section">
            <div class="rm-section__header">
              <div>
                <h3>Data readiness</h3>
                <p>Separates exact outputs from inferred actioning so the RM knows what is defensible.</p>
              </div>
            </div>
            <div class="rm-note-list">
              <article class="rm-note">
                <strong>Exact from workbook</strong>
                <p>${safeText(payload.metrics_meta.exact_metrics.join(" · "))}</p>
              </article>
              <article class="rm-note">
                <strong>Inferred for RM actioning</strong>
                <p>${safeText(payload.metrics_meta.inferred_metrics.join(" · "))}</p>
              </article>
              <article class="rm-note">
                <strong>Unavailable until claims arrive</strong>
                <p>${safeText(payload.metrics_meta.unavailable_metrics.join(" · "))}</p>
              </article>
            </div>
          </div>
        </div>
      </section>

      <section class="rm-section">
        <div class="rm-section__header">
          <div>
            <h3>Workbook and schema mapping</h3>
            <p>Transformation layer inputs are explicit so future IIB drops can reuse the same dashboard shell.</p>
          </div>
        </div>
        <div class="rm-schema">
          <div class="rm-schema-block">
            <h4>Sample workbook summary</h4>
            <div class="rm-schema-list">
              <div class="rm-schema-item">
                <strong>${safeText(payload.sample_workbook.workbook)}</strong>
                <div class="rm-small">Sheet: ${safeText(payload.sample_workbook.active_sheet)} · header row ${payload.sample_workbook.header_row} · ${payload.sample_workbook.row_count} records</div>
              </div>
              <div class="rm-schema-item">
                <strong>Dimensions found</strong>
                <div class="rm-small">${safeText(payload.sample_workbook.dimensions.join(" · "))}</div>
              </div>
              <div class="rm-schema-item">
                <strong>Measures found</strong>
                <div class="rm-small">${safeText(payload.sample_workbook.measures.join(" · "))}</div>
              </div>
              <div class="rm-schema-item">
                <strong>Header sample</strong>
                <div class="rm-small">${safeText(payload.sample_workbook.headers.slice(0, 12).join(" · "))}</div>
              </div>
            </div>
          </div>
          <div class="rm-schema-block">
            <h4>Liability dictionary summary</h4>
            <div class="rm-schema-list">
              ${dictSheets.map((sheet) => `
                <div class="rm-schema-item">
                  <strong>${safeText(sheet.name)}</strong>
                  <div class="rm-small">Header row ${sheet.header_row} · ${sheet.field_count} mapped fields</div>
                  <div class="rm-small" style="margin-top:6px;">${safeText((sheet.sample_fields || []).map((item) => `${item.field_name}${item.type ? ` (${item.type})` : ""}`).join(" · "))}</div>
                </div>
              `).join("")}
            </div>
          </div>
        </div>
      </section>

      <section class="rm-footer-actions">
        <div class="rm-section__header">
          <div>
            <h3>RM recommendations footer</h3>
            <p>Bottom-line action board for the current filtered cut of the workbook.</p>
          </div>
        </div>
        <div class="rm-footer-actions__grid">
          ${footerActions.map((item) => `
            <article class="rm-footer-card">
              <strong>${safeText(item.title)}</strong>
              <div class="rm-footer-card__impact">${safeText(item.impact)}</div>
              <div class="rm-small">${safeText(item.detail)}</div>
            </article>
          `).join("")}
        </div>
      </section>
    `;

    bindEvents();
  }

  function bindEvents() {
    const product = document.getElementById("filterProduct");
    const stateSelect = document.getElementById("filterState");
    const bookType = document.getElementById("filterBookType");
    const reload = document.getElementById("reloadDashboard");
    const reset = document.getElementById("resetFilters");
    const printBtn = document.getElementById("printDashboard");
    const downloadAccounts = document.getElementById("downloadAccounts");
    const downloadSummary = document.getElementById("downloadSummary");

    if (product) {
      product.addEventListener("change", (event) => {
        state.filters.product = event.target.value;
        render();
      });
    }
    if (stateSelect) {
      stateSelect.addEventListener("change", (event) => {
        state.filters.state = event.target.value;
        render();
      });
    }
    if (bookType) {
      bookType.addEventListener("change", (event) => {
        state.filters.bookType = event.target.value;
        render();
      });
    }
    if (reload) reload.addEventListener("click", fetchDashboard);
    if (reset) {
      reset.addEventListener("click", () => {
        state.filters = { product: "all", state: "all", bookType: "all" };
        render();
      });
    }
    if (printBtn) printBtn.addEventListener("click", () => window.print());
    if (downloadAccounts) {
      downloadAccounts.addEventListener("click", () => {
        downloadText("rm_dashboard_accounts.csv", buildCsv(getPolicies()), "text/csv;charset=utf-8");
      });
    }
    if (downloadSummary) {
      downloadSummary.addEventListener("click", () => {
        const policies = getPolicies();
        const summary = summarizePolicies(policies);
        downloadText(
          "rm_dashboard_summary.json",
          JSON.stringify(
            {
              meta: state.payload.meta,
              filters: state.filters,
              summary: {
                totalPremium: summary.totalPremium,
                renewalCount90: summary.renewals.length,
                crossSellCount: summary.crossSell.length,
                escalationCount: summary.escalations.length,
              },
              policies,
            },
            null,
            2
          ),
          "application/json;charset=utf-8"
        );
      });
    }

    document.querySelectorAll("#accountsTable th[data-sort]").forEach((node) => {
      node.addEventListener("click", () => {
        const key = node.getAttribute("data-sort");
        state.sort.accounts.dir = state.sort.accounts.key === key && state.sort.accounts.dir === "desc" ? "asc" : "desc";
        state.sort.accounts.key = key;
        render();
      });
    });

    document.querySelectorAll("#renewalsTable th[data-sort]").forEach((node) => {
      node.addEventListener("click", () => {
        const key = node.getAttribute("data-sort");
        state.sort.renewals.dir = state.sort.renewals.key === key && state.sort.renewals.dir === "asc" ? "desc" : "asc";
        state.sort.renewals.key = key;
        render();
      });
    });
  }

  fetchDashboard().catch((error) => renderError(error.message || String(error)));
})();
