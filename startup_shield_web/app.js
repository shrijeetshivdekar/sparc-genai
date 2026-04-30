const state = {
  meta: null,
  step: 0,
  profile: {},
};

const screens = [
  { section: "Identity", key: "startup_name", title: "What is your startup called?", type: "text", placeholder: "Acme Labs" },
  { section: "Identity", key: "sector", title: "Which sector best describes your startup?", type: "select", options: "sectors" },
  { section: "Identity", key: "sub_sector", title: "Do you have a specific sub-sector?", type: "subsector" },
  { section: "Identity", key: "funding_stage", title: "What funding stage are you at?", type: "choices", options: "fundingStages" },
  { section: "Shape", key: "team_size", title: "How many full-time team members do you have?", type: "range", min: 1, max: 500, step: 1 },
  { section: "Shape", key: "operations", title: "What does your operating model look like?", type: "choices", options: "operations" },
  { section: "Shape", key: "data_sensitivity", title: "How sensitive is the customer data you handle?", type: "choices", options: "dataSensitivity" },
  { section: "Shape", key: "ai_in_product", title: "Is AI / ML part of your core product?", type: "booleanChoice", options: ["No", "Yes"] },
  { section: "Shape", key: "customer_type", title: "Who are your customers?", type: "multi", options: "customerTypeOptions" },
  { section: "Shape", key: "has_investors", title: "Do you have institutional investors on board?", type: "choices", options: ["Yes", "No"] },
  { section: "Shape", key: "product_description", title: "What does your product or service do?", type: "textarea", placeholder: "Example: We build a UPI payment gateway for SMBs, processing 10k+ transactions/day." },
  { section: "Exposure", key: "data_handled", title: "What sensitive data or assets do you handle?", type: "multi", options: "dataHandledOptions" },
  { section: "Exposure", key: "regulatory", title: "Which regulatory exposures apply?", type: "multi", options: "regulatoryOptions" },
  { section: "Exposure", key: "physical_assets", title: "Which physical assets do you own?", type: "multi", options: "physicalAssetOptions" },
  { section: "Exposure", key: "biggest_fear", title: "What is your biggest risk fear?", type: "textarea", placeholder: "Example: A data breach that damages customer trust." },
];

const $ = (id) => document.getElementById(id);

async function init() {
  const response = await fetch("/api/meta");
  state.meta = await response.json();
  state.profile = structuredClone(state.meta.defaults);
  render();
}

function getOptions(source) {
  if (Array.isArray(source)) return source;
  if (source === "sectors") return state.meta.sectors.map((item) => item.name);
  return state.meta[source] || [];
}

function setValue(key, value) {
  state.profile[key] = value;
  renderSummary();
}

function render() {
  const screen = screens[state.step];
  $("section-label").textContent = screen.section;
  $("step-label").textContent = `${state.step + 1} of ${screens.length}`;
  $("progress-fill").style.width = `${((state.step + 1) / screens.length) * 100}%`;
  $("back-btn").disabled = state.step === 0;
  $("next-btn").textContent = state.step === screens.length - 1 ? "Analyse my startup" : "Next";

  $("screen").innerHTML = `<div class="question"><h2>${screen.title}</h2><p>${helperText(screen)}</p><div id="control"></div></div>`;
  renderControl(screen, $("control"));
  renderSummary();
}

function helperText(screen) {
  const copy = {
    Identity: "These basics set the sector profile and regulatory baseline.",
    Shape: "This tells the engine how your operating model changes risk exposure.",
    Exposure: "These inputs sharpen product triggers and AI bundle context.",
    Advanced: "Optional precision inputs. Leave defaults if you are not sure.",
  };
  return copy[screen.section] || "";
}

function renderControl(screen, root) {
  if (screen.type === "text") {
    root.innerHTML = `<input class="field" value="${escapeAttr(state.profile[screen.key] || "")}" placeholder="${screen.placeholder || ""}" />`;
    root.querySelector("input").addEventListener("input", (event) => setValue(screen.key, event.target.value));
    return;
  }

  if (screen.type === "textarea") {
    root.innerHTML = `<textarea class="textarea" placeholder="${screen.placeholder || ""}">${escapeHtml(state.profile[screen.key] || "")}</textarea>`;
    root.querySelector("textarea").addEventListener("input", (event) => setValue(screen.key, event.target.value));
    return;
  }

  if (screen.type === "select") {
    const options = getOptions(screen.options);
    root.innerHTML = `<select class="select">${options.map((option) => optionHtml(option, state.profile[screen.key])).join("")}</select>`;
    root.querySelector("select").addEventListener("change", (event) => {
      setValue(screen.key, event.target.value);
      state.profile.sub_sector = null;
      render();
    });
    return;
  }

  if (screen.type === "subsector") {
    const options = [null, ...(state.meta.subSectorOptions[state.profile.sector] || [])];
    root.innerHTML = `<select class="select">${options.map((option) => optionHtml(option, state.profile.sub_sector, "General")).join("")}</select>`;
    root.querySelector("select").addEventListener("change", (event) => setValue("sub_sector", event.target.value || null));
    return;
  }

  if (screen.type === "choices") {
    renderChoices(root, screen.key, getOptions(screen.options), false);
    return;
  }

  if (screen.type === "multi") {
    renderChoices(root, screen.key, getOptions(screen.options), true);
    return;
  }

  if (screen.type === "booleanChoice") {
    renderBooleanChoices(root, screen.key, screen.options);
    return;
  }

  if (screen.type === "range") {
    renderRange(root, screen.key, screen.min, screen.max, screen.step);
    return;
  }

  renderAdvanced(screen.type, root);
}

function renderBooleanChoices(root, key, options) {
  const selected = state.profile[key] ? "Yes" : "No";
  root.innerHTML = `<div class="choice-grid">${options.map((option) => {
    const active = selected === option;
    return `<button class="choice ${active ? "active" : ""}" type="button" data-value="${escapeAttr(option)}">${escapeHtml(option)}</button>`;
  }).join("")}</div>`;
  root.querySelectorAll(".choice").forEach((button) => {
    button.addEventListener("click", () => {
      state.profile[key] = button.dataset.value === "Yes";
      state.profile.ai_tier = state.profile[key] ? "Applied" : "None";
      render();
    });
  });
}

function renderChoices(root, key, options, multi) {
  const selected = multi ? state.profile[key] || [] : state.profile[key];
  root.innerHTML = `<div class="choice-grid ${options.length > 6 ? "compact" : ""}">${options.map((option) => {
    const active = multi ? selected.includes(option) : selected === option;
    return `<button class="choice ${active ? "active" : ""}" type="button" data-value="${escapeAttr(option)}">${active && multi ? "✓ " : ""}${escapeHtml(String(option))}</button>`;
  }).join("")}</div>`;

  root.querySelectorAll(".choice").forEach((button) => {
    button.addEventListener("click", () => {
      const value = button.dataset.value;
      if (multi) {
        const next = new Set(state.profile[key] || []);
        next.has(value) ? next.delete(value) : next.add(value);
        state.profile[key] = [...next];
      } else {
        state.profile[key] = value;
      }
      render();
    });
  });
}

function renderRange(root, key, min, max, step) {
  const value = Number(state.profile[key] ?? min);
  root.innerHTML = `
    <div class="range-row">
      <input type="range" min="${min}" max="${max}" step="${step}" value="${value}" />
      <div class="range-value">${value}</div>
    </div>`;
  root.querySelector("input").addEventListener("input", (event) => {
    state.profile[key] = Number(event.target.value);
    root.querySelector(".range-value").textContent = event.target.value;
    renderSummary();
  });
}

function renderAdvanced(type, root) {
  if (type === "advancedGovernance") {
    root.innerHTML = advancedGrid([
      numberField("investor_cn_hk_pct", "China / HK investor BO", 0, 1, 0.01),
      numberField("cumulative_fundraising_inr_cr", "Total fundraising, INR Cr", 0, 10000, 10),
      selectField("holdco_domicile", "Holdco domicile", state.meta.holdcoDomiciles),
      numberField("founder_concentration_index", "Founder concentration index", 0, 1, 0.01),
      checkboxField("dpiit_recognition", "DPIIT recognised startup"),
      selectField("rbi_registration", "RBI registration", state.meta.rbiRegistrations, "None"),
    ]);
  } else if (type === "advancedWorkforce") {
    root.innerHTML = advancedGrid([
      numberField("gig_headcount_pct", "Gig / contractor workforce", 0, 1, 0.01),
      checkboxField("posh_ic_constituted", "POSH IC constituted"),
      checkboxField("cert_in_poc_designated", "CERT-In POC designated"),
    ]) + `<div class="choice-grid compact">${state.meta.states.map((item) => choiceHtml("state_footprint", item, true)).join("")}</div>`;
  } else if (type === "advancedDataAi") {
    root.innerHTML = advancedGrid([
      numberField("sdf_probability", "SDF likelihood", 0, 1, 0.01),
      selectField("data_localisation_status", "Data localisation", ["Unknown", "Full_onshore", "Hybrid", "Offshore"]),
      checkboxField("ai_in_product", "AI / ML in core product"),
      numberField("hardware_software_split", "Hardware revenue", 0, 1, 0.01),
    ]);
  } else if (type === "advancedMarket") {
    root.innerHTML = advancedGrid([
      numberField("b2b_pct", "B2B revenue", 0, 1, 0.01),
      numberField("export_eu_pct", "EU revenue", 0, 1, 0.01),
      numberField("export_us_pct", "US revenue", 0, 1, 0.01),
      numberField("export_china_pct", "China revenue", 0, 1, 0.01),
      numberField("chinese_supplier_pct_cogs", "Chinese supplier COGS", 0, 1, 0.01),
      checkboxField("listed_customer_brsr_dependency", "Listed customers require BRSR data"),
    ]);
  } else {
    root.innerHTML = advancedGrid([
      selectField("facility_climate_risk_zone", "Facility climate risk zone", state.meta.climateZones),
    ]);
  }
  bindAdvanced(root);
}

function advancedGrid(items) {
  return `<div class="choice-grid">${items.join("")}</div>`;
}

function numberField(key, label, min, max, step) {
  if (min === 0 && max === 1) {
    const value = Number(state.profile[key] ?? 0);
    return `
      <label class="slider-field">
        <span class="card-label">${label}</span>
        <div class="range-row">
          <input type="range" data-key="${key}" min="0" max="1" step="${step}" value="${value}" />
          <div class="range-value">${value.toFixed(2)}</div>
        </div>
      </label>`;
  }
  return `<label><span class="card-label">${label}</span><input class="field" type="number" data-key="${key}" min="${min}" max="${max}" step="${step}" value="${state.profile[key] ?? 0}" /></label>`;
}

function selectField(key, label, options, nullLabel) {
  return `<label><span class="card-label">${label}</span><select class="select" data-key="${key}">${options.map((option) => optionHtml(option, state.profile[key], nullLabel)).join("")}</select></label>`;
}

function checkboxField(key, label) {
  return `<label class="choice ${state.profile[key] ? "active" : ""}"><input type="checkbox" data-key="${key}" ${state.profile[key] ? "checked" : ""} /> ${label}</label>`;
}

function choiceHtml(key, value, multi) {
  const selected = multi ? (state.profile[key] || []).includes(value) : state.profile[key] === value;
  return `<button class="choice ${selected ? "active" : ""}" type="button" data-multi="${multi}" data-key="${key}" data-value="${escapeAttr(value)}">${selected && multi ? "✓ " : ""}${escapeHtml(value)}</button>`;
}

function bindAdvanced(root) {
  root.querySelectorAll("input[type='range']").forEach((field) => {
    field.addEventListener("input", () => {
      const value = Number(field.value);
      state.profile[field.dataset.key] = value;
      const valueEl = field.closest(".range-row")?.querySelector(".range-value");
      if (valueEl) valueEl.textContent = value.toFixed(2);
      renderSummary();
    });
  });
  root.querySelectorAll("input[type='number']").forEach((field) => {
    field.addEventListener("input", () => setValue(field.dataset.key, Number(field.value)));
  });
  root.querySelectorAll("select").forEach((field) => {
    field.addEventListener("change", () => setValue(field.dataset.key, field.value || null));
  });
  root.querySelectorAll("input[type='checkbox']").forEach((field) => {
    field.addEventListener("change", () => {
      state.profile[field.dataset.key] = field.checked;
      render();
    });
  });
  root.querySelectorAll("button.choice[data-multi='true']").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.key;
      const value = button.dataset.value;
      const next = new Set(state.profile[key] || []);
      next.has(value) ? next.delete(value) : next.add(value);
      state.profile[key] = [...next];
      render();
    });
  });
}

function optionHtml(option, selected, nullLabel) {
  const value = option ?? "";
  const label = option ?? nullLabel ?? "";
  return `<option value="${escapeAttr(value)}" ${selected === option ? "selected" : ""}>${escapeHtml(String(label))}</option>`;
}

function renderSummary() {
  $("summary-body").innerHTML = [
    ["Name", state.profile.startup_name || "Not set"],
    ["Sector", state.profile.sector || "Not set"],
    ["Stage", state.profile.funding_stage || "Not set"],
    ["Team", `${state.profile.team_size || 0} FTEs`],
    ["Operations", state.profile.operations || "Not set"],
  ].map(([label, value]) => `<div class="summary-item"><strong>${label}</strong><span>${escapeHtml(String(value))}</span></div>`).join("");
}

async function analyze() {
  $("next-btn").disabled = true;
  $("next-btn").textContent = "Analysing...";
  try {
    const result = await fetchAnalysis();
    renderResults(result);
  } catch (error) {
    $("screen").innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
  } finally {
    $("next-btn").disabled = false;
  }
}

async function fetchAnalysis() {
  const response = await fetch("/api/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(state.profile),
  });
  const result = await response.json();
  if (!response.ok || result.error) throw new Error(result.error || "Analysis failed");
  return result;
}

function renderSectionNav() {
  const links = [
    ["#risk-scores", "Risk scores"],
    ["#bundle", "Bundle"],
    ["#products", "Products"],
    ["#timeline", "Timeline"],
    ["#outreach", "Outreach kit"],
    ["#assumptions", "Assumptions"],
  ];
  return `<nav class="section-nav" aria-label="Jump to section">${links.map(([href, label]) => `<a href="${href}">${escapeHtml(label)}</a>`).join("")}</nav>`;
}

function renderActionBanner(recommendations) {
  if (!recommendations?.length) return "";
  const critical = recommendations.filter((p) => p.priority === "Critical").slice(0, 3);
  if (!critical.length) return "";
  return `
    <div class="action-banner">
      <div class="action-banner-title">Buy now — ${critical.length} critical cover${critical.length > 1 ? "s" : ""} for your profile</div>
      ${critical.map((p) => `
        <div class="action-mini-row">
          <strong>${escapeHtml(p.name || p.key)}</strong>
          ${p.premium ? `<span class="action-mini-tag">₹${p.premium.min_lakh.toFixed(1)}–${p.premium.max_lakh.toFixed(1)}L</span>` : ""}
          <span class="action-mini-why">${escapeHtml(p.nudge || "")}</span>
        </div>`).join("")}
    </div>`;
}

async function rerunFromRefine() {
  const body = document.getElementById("results-body");
  if (body) body.classList.add("loading");
  try {
    const result = await fetchAnalysis();
    renderResults(result);
  } catch (error) {
    if (body) body.insertAdjacentHTML("afterbegin", `<div class="error">${escapeHtml(error.message)}</div>`);
  }
}

function renderResults(result) {
  state.profile = structuredClone(result.profile || state.profile);
  document.body.innerHTML = "";
  const wrapper = document.createElement("main");
  wrapper.className = "app-shell";
  wrapper.style.display = "block";
  wrapper.innerHTML = `
    <section class="results">
      <div class="results-hero">
        <div class="hero-actions">
          <div>
            <div class="eyebrow">Recommendation output</div>
            <h1 id="result-title"></h1>
            <p id="result-subtitle"></p>
          </div>
          <div class="action-row">
            <button id="download-btn" class="btn btn-primary" type="button">Download report</button>
            <button id="edit-btn" class="btn btn-ghost" type="button">Edit inputs</button>
          </div>
        </div>
      </div>
      <div id="results-body"></div>
    </section>`;
  document.body.appendChild(wrapper);

  if (result.decline) {
    document.querySelector(".results").innerHTML = `<div class="error">Coverage unavailable: ${escapeHtml(result.decline)}</div><button id="edit-btn" class="btn btn-ghost" type="button">Edit inputs</button>`;
    document.getElementById("edit-btn").addEventListener("click", () => window.location.reload());
    return;
  }

  document.getElementById("result-title").textContent = `${result.profile.startup_name} risk profile`;
  document.getElementById("result-subtitle").textContent = `${result.profile.sector} | ${result.profile.funding_stage} | ${result.profile.team_size} people`;

  const gaugeClass = result.overall >= 70 ? "gauge-critical" : result.overall >= 45 ? "gauge-moderate" : "gauge-low";

  try {
  document.getElementById("results-body").innerHTML = `
    ${renderRefinePanel(result.profile)}
    ${renderSectionNav()}
    ${renderProfileStrip(result.profile)}
    ${renderPremiumSummary(result.premium_summary, result.premium_footnote)}
    ${renderActionBanner(result.recommendations)}

    <div class="section-heading" id="risk-scores"><span class="section-heading-bar"></span>Risk overview</div>
    <div class="kpi-grid">
      <div class="result-card gauge-card">
        <div class="card-label">Overall risk</div>
        <div class="gauge-shell">
          <div class="gauge-ring ${escapeAttr(gaugeClass)}" style="--score:${Math.min(100, result.overall)};">
            <div>
              <strong>${result.overall}</strong>
              <span>/100</span>
            </div>
          </div>
          <p>${overallLabel(result.overall)}</p>
        </div>
      </div>
      <div class="result-card">
        <div class="card-label">4-cluster radar</div>
        <canvas id="cluster-radar" class="radar-canvas" width="360" height="280"></canvas>
      </div>
      <div class="result-card">
        <div class="card-label">13-category spider graph</div>
        <canvas id="risk-radar" class="radar-canvas" width="420" height="320"></canvas>
      </div>
    </div>

    <div class="result-grid">
      <div class="result-card">
        <div class="card-label">All risk scores</div>
        ${renderScoreBars(result.scores, result.score_rationales)}
      </div>
      <div class="result-card">
        <div class="card-label">Top 3 risk drivers</div>
        ${renderRiskDrivers((result.top_risks || []).slice(0, 3))}
      </div>
    </div>

    <div class="section-heading" id="bundle"><span class="section-heading-bar"></span>Bundle recommendation</div>
    <div class="result-card">
      ${renderBundleMatch(result.bundle_match)}
    </div>

    <div class="section-heading" id="products"><span class="section-heading-bar"></span>Recommended ICICI Lombard products</div>
    <div class="result-card">
      <div class="product-grid">${renderRecommendationCards(result.recommendations, result.product_mapping)}</div>
      ${renderBadProducts(result.not_preferred_recommendations)}
    </div>

    <details class="result-card expander">
      <summary>Top 5 global products — how SPARC compares</summary>
      ${renderGlobalProducts(result.global_products)}
    </details>

    <details class="result-card expander">
      <summary>Score breakdown</summary>
      ${renderScoreBreakdown(result.multiplier_breakdown)}
    </details>

    <div class="section-heading" id="timeline"><span class="section-heading-bar"></span>Coverage timeline</div>
    <div class="result-card">
      ${renderTimeline(result.bundles)}
    </div>

    <div class="result-grid">
      <div class="result-card">
        <div class="card-label">Product comparison</div>
        ${renderComparison(result.recommendations)}
      </div>
      <div class="result-card">
        <div class="card-label">Risk-to-product mapping</div>
        ${renderProductMapping(result.product_mapping)}
      </div>
    </div>

    <div class="result-grid">
      <div class="result-card">
        <div class="card-label">Regulatory trigger callouts</div>
        ${renderTriggers(result.regulatory_triggers)}
      </div>
      <div class="result-card">
        <div class="card-label">Non-insurance mitigation actions</div>
        ${renderMitigations(result.mitigations)}
      </div>
    </div>

    <div class="result-card" id="assumptions">
      <div class="card-label">Assumptions used by the engine</div>
      ${renderAssumptions(result.assumptions)}
    </div>

    ${renderOutreachKit(result.outreach_prompts, result.outreach_source, result.outreach_error)}
    ${renderDownstream(result.downstream_opportunities)}
    ${renderCustomTriggers(result.custom_triggers)}
  `;
  } catch (err) {
    document.getElementById("results-body").innerHTML = `<div class="error" style="padding:2rem;color:var(--red);">Render error: ${escapeHtml(String(err))}</div>`;
    console.error("results-body render failed:", err);
    return;
  }

  document.getElementById("edit-btn").addEventListener("click", () => window.location.reload());
  document.getElementById("download-btn").addEventListener("click", () => downloadReport(result));
  bindRefinePanel();
  document.querySelectorAll(".copy-trigger").forEach((button) => {
    button.addEventListener("click", async () => {
      await navigator.clipboard?.writeText(button.dataset.copy || "");
      button.textContent = "Copied";
    });
  });
  document.querySelectorAll(".copy-outreach").forEach((button) => {
    button.addEventListener("click", async () => {
      await navigator.clipboard?.writeText(button.dataset.copy || "");
      button.textContent = "Copied";
    });
  });
  drawRadar("cluster-radar", result.clusters, { maxLabelLength: 18 });
  drawRadar("risk-radar", result.scores, { maxLabelLength: 14 });
}

function overallLabel(score) {
  if (score >= 70) return "High exposure: prioritise critical covers and governance actions now.";
  if (score >= 45) return "Moderate exposure: buy essential covers first and review quarterly.";
  return "Lower exposure: start with baseline covers and revisit as you scale.";
}

function renderRefinePanel(profile) {
  return `
    <details class="result-card refine-panel">
      <summary>Refine your profile - adjust these to sharpen your risk scores</summary>
      <p class="muted">Changing any field below recalculates scores, recommendations, premium potential, and product opportunities.</p>
      <div class="refine-section">
        <h3>Governance & capital</h3>
        ${advancedGrid([
          numberField("investor_cn_hk_pct", "China / HK investor BO", 0, 1, 0.01),
          numberField("cumulative_fundraising_inr_cr", "Total fundraising, INR Cr", 0, 10000, 10),
          selectField("holdco_domicile", "Holdco domicile", state.meta.holdcoDomiciles),
          numberField("founder_concentration_index", "Founder concentration index", 0, 1, 0.01),
          checkboxField("dpiit_recognition", "DPIIT recognised startup"),
          selectField("rbi_registration", "RBI registration", state.meta.rbiRegistrations, "None"),
        ])}
      </div>
      <div class="refine-section">
        <h3>Workforce & gig risk</h3>
        ${advancedGrid([
          numberField("gig_headcount_pct", "Gig / contractor workforce", 0, 1, 0.01),
          checkboxField("posh_ic_constituted", "POSH IC constituted"),
          checkboxField("cert_in_poc_designated", "CERT-In POC designated"),
        ])}
        <div class="choice-grid compact">${state.meta.states.map((item) => choiceHtml("state_footprint", item, true)).join("")}</div>
      </div>
      <div class="refine-section">
        <h3>Data & AI risk</h3>
        ${advancedGrid([
          numberField("sdf_probability", "SDF likelihood", 0, 1, 0.01),
          selectField("data_localisation_status", "Data localisation", ["Unknown", "Full_onshore", "Hybrid", "Offshore"]),
          selectField("ai_tier", "AI tier", state.meta.aiTiers),
          numberField("hardware_software_split", "Hardware revenue", 0, 1, 0.01),
        ])}
      </div>
      <div class="refine-section">
        <h3>Market & supply chain</h3>
        ${advancedGrid([
          numberField("b2b_pct", "B2B revenue", 0, 1, 0.01),
          numberField("export_eu_pct", "EU revenue", 0, 1, 0.01),
          numberField("export_us_pct", "US revenue", 0, 1, 0.01),
          numberField("export_china_pct", "China revenue", 0, 1, 0.01),
          numberField("chinese_supplier_pct_cogs", "Chinese supplier COGS", 0, 1, 0.01),
          checkboxField("listed_customer_brsr_dependency", "Listed customers require BRSR data"),
        ])}
      </div>
      <div class="refine-section">
        <h3>Physical & environmental</h3>
        ${advancedGrid([
          selectField("facility_climate_risk_zone", "Facility climate risk zone", state.meta.climateZones),
        ])}
      </div>
    </details>
  `;
}

function bindRefinePanel() {
  const root = document.querySelector(".refine-panel");
  if (!root) return;
  let timer = null;
  const schedule = () => {
    clearTimeout(timer);
    timer = setTimeout(rerunFromRefine, 180);
  };
  root.querySelectorAll("input[type='range']").forEach((field) => {
    field.addEventListener("input", () => {
      const value = Number(field.value);
      state.profile[field.dataset.key] = value;
      const valueEl = field.closest(".range-row")?.querySelector(".range-value");
      if (valueEl) valueEl.textContent = value.toFixed(2);
      schedule();
    });
  });
  root.querySelectorAll("input[type='number']").forEach((field) => {
    field.addEventListener("change", () => {
      state.profile[field.dataset.key] = Number(field.value);
      schedule();
    });
  });
  root.querySelectorAll("select").forEach((field) => {
    field.addEventListener("change", () => {
      const value = field.value || null;
      state.profile[field.dataset.key] = value;
      if (field.dataset.key === "ai_tier") state.profile.ai_in_product = value !== "None";
      schedule();
    });
  });
  root.querySelectorAll("input[type='checkbox']").forEach((field) => {
    field.addEventListener("change", () => {
      state.profile[field.dataset.key] = field.checked;
      schedule();
    });
  });
  root.querySelectorAll("button.choice[data-multi='true']").forEach((button) => {
    button.addEventListener("click", () => {
      const key = button.dataset.key;
      const value = button.dataset.value;
      const next = new Set(state.profile[key] || []);
      next.has(value) ? next.delete(value) : next.add(value);
      state.profile[key] = [...next];
      button.classList.toggle("active");
      schedule();
    });
  });
}

function renderProfileStrip(profile) {
  const items = [
    ["Sector", profile.sector],
    ["Stage", profile.funding_stage],
    ["Team", `${profile.team_size} people`],
    ["Ops", profile.operations],
    ["Size", profile.size_bucket || ""],
  ];
  return `<div class="profile-strip">${items.map(([label, value]) => `
    <div><strong>${escapeHtml(label)}</strong><span>${escapeHtml(value || "Not set")}</span></div>
  `).join("")}</div>`;
}

function renderPremiumSummary(summary, footnote) {
  if (!summary) return "";
  return `
    <div class="result-card premium-card">
      <div class="card-label">Premium potential summary</div>
      <h2>Total estimated premium potential: INR ${summary.min_lakh} - ${summary.max_lakh} lakhs across ${summary.count} products</h2>
      <p class="muted">${escapeHtml(footnote || "")}</p>
    </div>
  `;
}

function renderScoreBars(scores, rationales = {}) {
  return Object.entries(scores)
    .sort((a, b) => b[1] - a[1])
    .map(([name, score]) => {
      const lvl = score >= 70 ? "critical" : score >= 40 ? "watch" : "low";
      const lvlLabel = score >= 70 ? "Critical" : score >= 40 ? "Watch" : "Low";
      return `
        <div class="bar-row">
          <span>
            <b>${escapeHtml(name)}</b>
            <span style="display:flex;align-items:center;gap:5px;">
              <b>${score}</b>
              <span class="bar-level ${lvl}">${lvlLabel}</span>
            </span>
          </span>
          <div class="bar"><div class="${riskClass(score)}" style="width:${Math.min(100, score)}%"></div></div>
          ${renderScoreRationale(name, rationales[name])}
        </div>`;
    }).join("");
}

function renderScoreRationale(name, rationale) {
  if (!rationale) return "";
  return `
    <details class="why-score">
      <summary>Why this score? - ${escapeHtml(name)}</summary>
      <p><strong>Weight:</strong> ${escapeHtml(rationale.weight)}</p>
      <p><strong>Evidence:</strong> ${escapeHtml(rationale.stat)}</p>
      <p><strong>Outlook:</strong> ${escapeHtml(rationale.forecast)}</p>
      <p><strong>Source:</strong> ${escapeHtml(rationale.source)}</p>
    </details>
  `;
}

function renderRiskDrivers(risks) {
  if (!risks?.length) return `<p class="muted">No risk drivers available.</p>`;
  return risks.map((risk) => `
    <article class="driver-card">
      <div class="risk-pill"><span>${escapeHtml(risk.name)}</span><span>${risk.score}</span></div>
      <p>${riskExplanation(risk.name)}</p>
    </article>
  `).join("");
}

function riskExplanation(name) {
  if (name.includes("Cyber")) return "Your digital footprint, data sensitivity, and sector profile make breach response and continuity important.";
  if (name.includes("Data Privacy")) return "Personal or sensitive data creates consent, fiduciary, retention, and notification obligations.";
  if (name.includes("Regulatory")) return "Your sector or selected exposure carries licensing, audit, reporting, or statutory compliance pressure.";
  if (name.includes("Governance")) return "Investors, controls, fraud exposure, and board accountability can drive D&O and crime coverage needs.";
  if (name.includes("Liability")) return "Customer contracts, product/service failures, and negligence claims can create third-party loss exposure.";
  if (name.includes("Property")) return "Physical assets, sites, equipment, or inventory can create fire, theft, climate, or interruption losses.";
  return "This category is above the rest of your profile and should be reviewed with controls and coverage.";
}

function renderBundles(bundles) {
  if (!bundles?.length) return `<p class="muted">No bundle grouping was required.</p>`;
  return bundles.map((bundle) => `
    <article class="bundle-card">
      <div class="bundle-head">
        <h3>${escapeHtml(bundle.name)}</h3>
        <span class="tag">${escapeHtml(bundle.timeline)}</span>
      </div>
      <ul>${bundle.products.map((product) => `<li>${escapeHtml(product.name || product.key)} <span>${product.score}/100</span></li>`).join("")}</ul>
    </article>
  `).join("");
}

function renderBundleMatch(bundle) {
  if (!bundle?.name) return `<p class="muted">No packaged bundle matched this profile strongly enough.</p>`;
  const covers = [...(bundle.mandatory_covers || []), ...(bundle.optional_covers || [])];
  return `
    <article class="bundle-card featured-bundle">
      <div class="bundle-head">
        <div>
          <h3>${escapeHtml(bundle.name)} <span class="tag">${bundle.fit_pct || 0}% fit</span></h3>
          <p><strong>ICICI Lombard:</strong> ${escapeHtml(bundle.il_product_name || "")}</p>
        </div>
        <span class="tag">${escapeHtml(bundle.criticality || "Recommended")}</span>
      </div>
      <p>${escapeHtml(bundle.description || "")}</p>
      <div class="mini-risk-row">${covers.slice(0, 10).map((cover) => `<span>${escapeHtml(labelize(cover))}</span>`).join("")}</div>
      ${(bundle.prerequisite_notes || []).map((note) => `<p class="notice">${escapeHtml(note)}</p>`).join("")}
      ${bundle.fire_awareness_note ? `<p class="notice">${escapeHtml(bundle.fire_awareness_note)}</p>` : ""}
    </article>
  `;
}

function renderRecommendationCards(recommendations, mapping) {
  const byKey = Object.fromEntries((mapping || []).map((row) => [row.key, row]));
  if (!recommendations?.length) return `<p class="muted">No preferred ICICI products remain after appetite filtering.</p>`;
  return recommendations.map((product) => {
    const drivers = byKey[product.key]?.top_risks || [];
    const prio = product.priority || "Optional";
    const prioClass = prio === "Critical" ? "priority-critical" : prio === "Recommended" ? "priority-recommended" : "";
    const prioFlag = prio === "Critical"
      ? `<div class="product-flag critical">Critical cover</div>`
      : prio === "Recommended"
        ? `<div class="product-flag recommended">Recommended</div>`
        : "";
    const premiumHtml = product.premium
      ? `<div class="product-premium"><span class="product-premium-icon">₹</span> <strong>INR ${product.premium.min_lakh.toFixed(1)} – ${product.premium.max_lakh.toFixed(1)} lakhs</strong> <span style="color:var(--ink-faint)">· ${escapeHtml(product.premium.basis)}</span></div>`
      : "";
    return `
      <article class="product ${escapeAttr(prioClass)}">
        ${prioFlag}
        <h3>${escapeHtml(product.name || product.key)} ${renderAppetiteBadge(product.appetite)} <span class="tag">${escapeHtml(prio)} ${product.score}/100</span>${product.mandatory ? '<span class="tag">Baseline</span>' : ""}</h3>
        <p><strong>ICICI Lombard:</strong> ${escapeHtml(product.il_product || "")}</p>
        <p><strong>What it covers:</strong> ${escapeHtml(product.what_it_covers || "")}</p>
        <p><strong>Why this was recommended:</strong> ${escapeHtml(product.nudge || "")}</p>
        ${premiumHtml}
        <div class="mini-risk-row">${drivers.map((driver) => `<span>${escapeHtml(driver.risk)} ${driver.score}</span>`).join("")}</div>
      </article>`;
  }).join("");
}

function renderAppetiteBadge(appetite) {
  const labels = {
    good: "Good Risk",
    moderate: "Moderate",
    bad: "Not Preferred",
    tbd: "Appetite Under Review",
  };
  return `<span class="appetite ${escapeAttr(appetite || "tbd")}">${labels[appetite] || labels.tbd}</span>`;
}

function renderBadProducts(products) {
  if (!products?.length) return "";
  return `
    <details class="bad-products">
      <summary>Available but not preferred for this sector (${products.length} products)</summary>
      <div class="product-grid">${products.map((product) => `
        <article class="product">
          <h3>${escapeHtml(product.name || product.key)} ${renderAppetiteBadge("bad")}</h3>
          <p>${escapeHtml(product.what_it_covers || "")}</p>
          ${product.premium ? `<p class="premium-line">Estimated premium: INR ${product.premium.min_lakh.toFixed(1)} - ${product.premium.max_lakh.toFixed(1)} lakhs · ${escapeHtml(product.premium.basis)}</p>` : ""}
          <p class="muted"><em>${escapeHtml(product.bad_reason || "Not preferred for this sector.")}</em></p>
        </article>
      `).join("")}</div>
    </details>
  `;
}

function renderGlobalProducts(products) {
  if (!products?.length) return `<p class="muted">No global product benchmark matched this profile.</p>`;
  const status = {
    icici: "ICICI Lombard - Available now",
    india_competitor: "Indian market - Competitor",
    not_in_india: "Global - Not yet in India",
  };
  return `<div class="product-grid">${products.map((product) => `
    <article class="product">
      <h3>${escapeHtml(product.name)} <span class="tag">${product.relevance_score}/100</span></h3>
      <p><strong>${escapeHtml(status[product.label] || "Global product")}</strong></p>
      <p>${escapeHtml(product.what_it_covers || "")}</p>
      <p><strong>Providers:</strong> ${escapeHtml(product.providers || "")}</p>
      ${product.premium_range ? `<p class="premium-line">Indicative premium: INR ${product.premium_range.min_lakh.toFixed(1)} - ${product.premium_range.max_lakh.toFixed(1)} lakhs</p>` : ""}
      ${product.label === "not_in_india" ? `<p class="notice">Product development opportunity - flag to ICICI Lombard product team.</p>` : ""}
    </article>
  `).join("")}</div>`;
}

function renderScoreBreakdown(items) {
  if (!items?.length) return `<p class="muted">No dynamic score multipliers were material for this profile.</p>`;
  return `<div class="action-list">${items.map((item) => `
    <div class="action-item">
      <strong>${escapeHtml(labelize(item.key))}</strong>
      <span>${escapeHtml(item.applied || item.formula || "")}</span>
      <span class="muted">${escapeHtml(item.stat || "")}</span>
      <span class="muted"><strong>Source:</strong> ${escapeHtml(item.source || "")}</span>
    </div>
  `).join("")}</div>`;
}

function renderComparison(recommendations) {
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Product</th><th>Priority</th><th>Fit</th><th>Baseline</th></tr></thead>
        <tbody>
          ${(recommendations || []).map((product) => `
            <tr>
              <td>${escapeHtml(product.name || product.key)}</td>
              <td>${escapeHtml(product.priority || "Optional")}</td>
              <td>${product.score}</td>
              <td>${product.mandatory ? "Yes" : "No"}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderTimeline(bundles) {
  return `<div class="timeline">${(bundles || []).map((bundle, index) => `
    <div class="timeline-item">
      <div class="timeline-dot">${index + 1}</div>
      <div><strong>${escapeHtml(bundle.timeline)}</strong><span>${escapeHtml(bundle.name)}: ${bundle.products.length} products</span></div>
    </div>
  `).join("")}</div>`;
}

function renderProductMapping(mapping) {
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>Product</th><th>Fit</th><th>Risk drivers</th></tr></thead>
        <tbody>
          ${(mapping || []).map((row) => `
            <tr>
              <td>${escapeHtml(row.product)}</td>
              <td>${row.score}</td>
              <td>${row.top_risks.map((risk) => `${escapeHtml(risk.risk)} (${risk.score})`).join(", ")}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderTriggers(triggers) {
  if (!triggers?.length) return `<p class="muted">No major regulatory trigger was detected from the current inputs.</p>`;
  return triggers.map((trigger) => `
    <article class="callout">
      <strong>${escapeHtml(trigger.name)}</strong>
      <span>${escapeHtml(trigger.detail)}</span>
    </article>
  `).join("");
}

function renderMitigations(mitigations) {
  return `<div class="action-list">${(mitigations || []).map((item) => `
    <div class="action-item">
      <strong>${escapeHtml(item.risk)}</strong>
      <span>${escapeHtml(item.action)}</span>
    </div>
  `).join("")}</div>`;
}

function renderAssumptions(assumptions) {
  return `<div class="assumption-grid">${Object.entries(assumptions || {}).map(([key, value]) => `
    <div class="assumption">
      <strong>${escapeHtml(labelize(key))}</strong>
      <span>${escapeHtml(formatValue(value))}</span>
    </div>
  `).join("")}</div>`;
}

function renderOutreachKit(prompts, source, error) {
  const entries = Object.entries(prompts || {});
  if (!entries.length) return "";
  const sourceText = source === "gemini"
    ? "AI-generated outreach drafts are active."
    : "Using local fallback drafts. Add GEMINI_API_KEY in Vercel to enable AI-generated drafts.";
  const items = entries.map(([key, item], index) => {
    const email = `${item.email_subject}\n\n${item.email_body}`;
    return `
      <details class="outreach-item" ${index === 0 ? "open" : ""}>
        <summary>${escapeHtml(labelize(key))}</summary>
        <div class="outreach-item-body">
          <div class="outreach-cols">
            <div>
              <div class="outreach-col-label">Email</div>
              <pre>${escapeHtml(email)}</pre>
              <button class="btn btn-ghost copy-outreach" data-copy="${escapeAttr(email)}" type="button">Copy email</button>
            </div>
            <div>
              <div class="outreach-col-label">WhatsApp</div>
              <pre>${escapeHtml(item.whatsapp || "")}</pre>
              <button class="btn btn-ghost copy-outreach" data-copy="${escapeAttr(item.whatsapp || "")}" type="button">Copy WhatsApp</button>
            </div>
          </div>
        </div>
      </details>`;
  }).join("");
  return `
    <details class="result-card expander" id="outreach">
      <summary>Outreach Kit</summary>
      <p class="muted">${escapeHtml(sourceText)}</p>
      ${error ? `<p class="notice">Gemini fallback reason: ${escapeHtml(error)}</p>` : ""}
      <div style="margin-top:10px;">${items}</div>
    </details>`;
}

function renderDownstream(opportunities) {
  if (!opportunities?.length) return "";
  return `
    <div class="result-card">
      <div class="card-label">Downstream opportunity</div>
      <div class="product-grid">${opportunities.map((opp) => `
        <article class="product">
          <h3>${escapeHtml(opp.product)}</h3>
          <p>Your ${escapeHtml(opp.customer_type)} customers may need <strong>${escapeHtml(opp.product)}</strong>. As their service provider, you are already in the relationship.</p>
          <p>${escapeHtml(opp.rationale)}</p>
          <p class="premium-line">Estimated premium per downstream customer: ${escapeHtml(opp.premium_per_customer)}</p>
          ${opp.penetration_count !== undefined ? `<p class="muted">Assuming ${opp.penetration_count} converted customers from the current rough customer-base proxy. Actual opportunity requires customer count verification.</p>` : ""}
          ${opp.total_opportunity_lakhs_min !== undefined ? `<p class="notice">Estimated downstream potential: INR ${opp.total_opportunity_lakhs_min} - ${opp.total_opportunity_lakhs_max} lakhs</p>` : ""}
        </article>
      `).join("")}</div>
    </div>
  `;
}

function renderCustomTriggers(triggers) {
  if (!triggers?.length) return "";
  return `
    <div class="result-card innovation-card">
      <div class="card-label">Product innovation opportunity</div>
      ${triggers.map((trigger) => `
        <article class="product">
          <h3>Product Innovation Opportunity - ${escapeHtml(trigger.name || labelize(trigger.key))}</h3>
          <p>No existing ICICI Lombard product fully covers this emerging risk for the current profile.</p>
          <p><strong>What it is:</strong> ${escapeHtml(trigger.description)}</p>
          <p><strong>Global precedent:</strong> ${escapeHtml(trigger.global_precedent)}</p>
          <p><strong>IRDAI path:</strong> ${escapeHtml(trigger.irdai_path)}</p>
          <p><strong>Estimated Indian market:</strong> ${escapeHtml(trigger.estimated_market_size)}</p>
          <ul>${(trigger.triggered_by || []).map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>
          <button class="btn btn-ghost copy-trigger" data-copy="${escapeAttr(`${trigger.name || labelize(trigger.key)}\n${trigger.description}\n${trigger.irdai_path}`)}" type="button">Copy product-development summary</button>
        </article>
      `).join("")}
    </div>
  `;
}

function downloadReport(result) {
  const lines = [
    `SPARC Risk Report - ${result.profile.startup_name}`,
    "",
    `Sector: ${result.profile.sector}`,
    `Stage: ${result.profile.funding_stage}`,
    `Team size: ${result.profile.team_size}`,
    `Overall risk: ${result.overall}/100`,
    "",
    "Top risks:",
    ...result.top_risks.map((risk) => `- ${risk.name}: ${risk.score}/100`),
    "",
    "Recommendations:",
    ...result.recommendations.map((product) => `- ${product.name || product.key}: ${product.priority} (${product.score}/100)`),
    "",
    "Mitigation actions:",
    ...result.mitigations.map((item) => `- ${item.risk}: ${item.action}`),
  ];
  const blob = new Blob([lines.join("\n")], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${result.profile.startup_name || "startup"}-risk-report.txt`.replaceAll(" ", "-");
  link.click();
  URL.revokeObjectURL(url);
}

function drawRadar(canvasId, data, options = {}) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const entries = Object.entries(data || {});
  const width = canvas.width;
  const height = canvas.height;
  const cx = width / 2;
  const cy = height / 2;
  const radius = Math.min(width, height) * 0.32;
  ctx.clearRect(0, 0, width, height);
  ctx.font = "11px Inter, system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  for (let ring = 1; ring <= 4; ring++) {
    ctx.beginPath();
    entries.forEach((_, index) => {
      const angle = (-Math.PI / 2) + (index * 2 * Math.PI / entries.length);
      const r = radius * ring / 4;
      const x = cx + Math.cos(angle) * r;
      const y = cy + Math.sin(angle) * r;
      index === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.strokeStyle = "#E5E5E0";
    ctx.stroke();
  }

  ctx.beginPath();
  entries.forEach(([label, score], index) => {
    const angle = (-Math.PI / 2) + (index * 2 * Math.PI / entries.length);
    const x = cx + Math.cos(angle) * radius;
    const y = cy + Math.sin(angle) * radius;
    ctx.moveTo(cx, cy);
    ctx.lineTo(x, y);
    const shortLabel = truncateLabel(label, options.maxLabelLength || 14);
    ctx.fillStyle = "#475569";
    ctx.fillText(shortLabel, cx + Math.cos(angle) * (radius + 34), cy + Math.sin(angle) * (radius + 34));
  });
  ctx.strokeStyle = "#E5E5E0";
  ctx.stroke();

  ctx.beginPath();
  entries.forEach(([_, score], index) => {
    const angle = (-Math.PI / 2) + (index * 2 * Math.PI / entries.length);
    const r = radius * Math.min(100, Number(score)) / 100;
    const x = cx + Math.cos(angle) * r;
    const y = cy + Math.sin(angle) * r;
    index === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = "rgba(173, 30, 35, 0.16)";
  ctx.strokeStyle = "#AD1E23";
  ctx.lineWidth = 2;
  ctx.fill();
  ctx.stroke();
}

function truncateLabel(label, maxLength) {
  return label.length > maxLength ? `${label.slice(0, maxLength - 1)}...` : label;
}

function riskClass(score) {
  if (score >= 70) return "bar-critical";
  if (score >= 40) return "bar-watch";
  return "bar-low";
}

function labelize(key) {
  return key.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatValue(value) {
  if (Array.isArray(value)) return value.length ? value.join(", ") : "None";
  if (value === null || value === undefined || value === "") return "None";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

$("back-btn").addEventListener("click", () => {
  state.step = Math.max(0, state.step - 1);
  render();
});

$("next-btn").addEventListener("click", () => {
  if (state.step < screens.length - 1) {
    state.step += 1;
    render();
  } else {
    analyze();
  }
});

init().catch((error) => {
  $("screen").innerHTML = `<div class="error">${escapeHtml(error.message)}</div>`;
});
