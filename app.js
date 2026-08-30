let currentAnalysisData = null;
let waterfallChartInstance = null;
let activeFeedbackType = "CONFIRMED";
let selectedActionToExecute = null;

// Initialize on DOM Load
document.addEventListener("DOMContentLoaded", () => {
  initLucide();
  setupEventListeners();
  fetchAnalysis();
});

function initLucide() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

function setupEventListeners() {
  const scenarioSelect = document.getElementById("scenarioSelect");
  const personaSelect = document.getElementById("personaSelect");
  const runBtn = document.getElementById("runAnalysisBtn");

  if (scenarioSelect) scenarioSelect.addEventListener("change", fetchAnalysis);
  if (personaSelect) personaSelect.addEventListener("change", fetchAnalysis);
  if (runBtn) runBtn.addEventListener("click", fetchAnalysis);

  // Feedback type buttons
  document.querySelectorAll(".fb-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".fb-btn").forEach(b => {
        b.classList.remove("active", "border-indigo-500", "bg-indigo-950/50", "text-indigo-300");
      });
      btn.classList.add("active", "border-indigo-500", "bg-indigo-950/50", "text-indigo-300");
      activeFeedbackType = btn.getAttribute("data-type");
    });
  });

  // Feedback form submit
  const feedbackForm = document.getElementById("feedbackForm");
  if (feedbackForm) {
    feedbackForm.addEventListener("submit", handleFeedbackSubmit);
  }

  // Modal actions
  const closeModalBtn = document.getElementById("closeModalBtn");
  const cancelModalBtn = document.getElementById("cancelModalBtn");
  const confirmExecuteBtn = document.getElementById("confirmExecuteBtn");

  if (closeModalBtn) closeModalBtn.addEventListener("click", hideModal);
  if (cancelModalBtn) cancelModalBtn.addEventListener("click", hideModal);
  if (confirmExecuteBtn) confirmExecuteBtn.addEventListener("click", executeSelectedAction);
}

async function fetchAnalysis() {
  const scenarioId = document.getElementById("scenarioSelect").value;
  const roleId = document.getElementById("personaSelect").value;

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ scenario_id: scenarioId, role_id: roleId })
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    currentAnalysisData = data;
    renderDashboard(data);
  } catch (err) {
    console.error("Failed to load analysis:", err);
  }
}

function renderDashboard(data) {
  // 1. Scenario & Role Banner
  document.getElementById("scenarioTitle").textContent = data.scenario.name;
  document.getElementById("scenarioDesc").textContent = data.scenario.description;
  document.getElementById("roleBadge").textContent = `Role: ${data.role_profile.display_name}`;
  document.getElementById("narrativePersonaLabel").textContent = `Tailored for ${data.role_profile.display_name}`;

  // 2. Abstention Banner
  const abstentionBox = document.getElementById("abstentionBox");
  if (data.abstention && data.abstention.status === "ABSTAINED_FROM_DEFINITIVE_CLAIM") {
    abstentionBox.classList.remove("hidden");
    document.getElementById("abstentionReason").textContent = data.abstention.reason;
    document.getElementById("abstentionClarification").textContent = data.abstention.clarification_request;
  } else {
    abstentionBox.classList.add("hidden");
  }

  // 3. Render KPI Grid
  renderKPICards(data.kpis);

  // 4. Render Waterfall Chart & Drivers
  renderWaterfall(data.drivers);
  renderDriversList(data.drivers, data.cold_start_meta);

  // 5. Render Narrative
  renderNarrative(data.narrative);

  // 6. Render Actions
  renderActions(data.recommended_actions);

  // 7. Render Telemetry HUD
  renderTelemetry(data.telemetry);

  initLucide();
}

function renderKPICards(kpis) {
  const grid = document.getElementById("kpiGrid");
  grid.innerHTML = "";

  const kpiOrder = ["net_revenue", "checkout_conversion_rate", "stockout_rate", "customer_nps", "gross_margin_pct"];

  kpiOrder.forEach(key => {
    const kpi = kpis[key];
    if (!kpi) return;

    const card = document.createElement("div");
    card.className = "bg-slate-950/70 border border-slate-800 rounded-xl p-4 flex flex-col justify-between space-y-3 transition-all hover:border-slate-700";

    let statusBadge = "";
    if (kpi.status === "CRITICAL_ALERT") {
      statusBadge = `<span class="px-2 py-0.5 text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded-full flex items-center space-x-1"><span class="w-1.5 h-1.5 rounded-full bg-rose-400"></span><span>Critical Alert</span></span>`;
    } else if (kpi.status === "WARNING") {
      statusBadge = `<span class="px-2 py-0.5 text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full">Warning</span>`;
    } else if (kpi.status === "DATA_SPARSE") {
      statusBadge = `<span class="px-2 py-0.5 text-[10px] font-bold bg-purple-500/20 text-purple-400 border border-purple-500/30 rounded-full">Sparse Prior</span>`;
    } else {
      statusBadge = `<span class="px-2 py-0.5 text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full">Healthy</span>`;
    }

    let valDisplay = "";
    let deltaDisplay = "";

    if (kpi.is_masked) {
      valDisplay = `<span class="text-xs font-mono text-amber-400/80 tracking-tight block py-1">[CONFIDENTIAL RBAC MASKED]</span>`;
      deltaDisplay = `<span class="text-[11px] text-slate-500">Finance clearance required</span>`;
    } else {
      const formattedVal = typeof kpi.current_value === "number" ? kpi.current_value.toLocaleString() : kpi.current_value;
      const unitSym = kpi.unit === "EUR" ? "€" : (kpi.unit === "%" ? "%" : "");
      valDisplay = `<span class="text-xl font-extrabold text-white font-mono">${kpi.unit === "EUR" ? "€" : ""}${formattedVal}${kpi.unit === "%" ? "%" : ""}</span>`;

      const deltaSign = kpi.delta_pct >= 0 ? "+" : "";
      const deltaColor = kpi.delta_pct < 0 ? "text-rose-400" : "text-emerald-400";
      deltaDisplay = `
        <span class="text-xs font-bold ${deltaColor} font-mono">${deltaSign}${kpi.delta_pct}%</span>
        <span class="text-[11px] text-slate-500 ml-1.5">vs ${kpi.unit === "EUR" ? "€" : ""}${typeof kpi.baseline_value === "number" ? kpi.baseline_value.toLocaleString() : kpi.baseline_value}</span>
      `;
    }

    card.innerHTML = `
      <div class="flex items-start justify-between">
        <span class="text-xs font-semibold text-slate-400 line-clamp-1">${kpi.name}</span>
        ${statusBadge}
      </div>
      <div>
        ${valDisplay}
        <div class="flex items-center mt-1">
          ${deltaDisplay}
        </div>
      </div>
      <div class="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500 font-mono">
        <span>${kpi.grain || "Daily"}</span>
        <span>Z=${kpi.z_score || 0.0}</span>
      </div>
    `;

    grid.appendChild(card);
  });
}

function renderWaterfall(drivers) {
  const ctx = document.getElementById("waterfallChart");
  if (!ctx) return;

  if (waterfallChartInstance) {
    waterfallChartInstance.destroy();
  }

  const labels = drivers.map(d => d.name);
  const dataValues = drivers.map(d => Math.abs(d.revenue_impact_eur));
  const percentages = drivers.map(d => `${d.percentage_contribution}%`);

  waterfallChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Variance Loss (€)",
        data: dataValues,
        backgroundColor: [
          "rgba(244, 63, 94, 0.85)",   // Rose
          "rgba(245, 158, 11, 0.85)",  // Amber
          "rgba(99, 102, 241, 0.85)",  // Indigo
          "rgba(20, 184, 166, 0.85)"   // Teal
        ],
        borderColor: [
          "rgba(244, 63, 94, 1)",
          "rgba(245, 158, 11, 1)",
          "rgba(99, 102, 241, 1)",
          "rgba(20, 184, 166, 1)"
        ],
        borderWidth: 1,
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Impact: -€${ctx.raw.toLocaleString()} (${percentages[ctx.dataIndex]} total delta)`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: "#94a3b8", font: { size: 10 } },
          grid: { display: false }
        },
        y: {
          ticks: { color: "#94a3b8", font: { size: 10 }, callback: val => `€${(val/1000).toFixed(0)}k` },
          grid: { color: "rgba(51, 65, 85, 0.4)" }
        }
      }
    }
  });
}

function renderDriversList(drivers, coldStartMeta) {
  const container = document.getElementById("driversList");
  container.innerHTML = "";

  if (coldStartMeta) {
    const coldBox = document.createElement("div");
    coldBox.className = "p-3 rounded-lg bg-purple-950/40 border border-purple-800/50 mb-3 space-y-1 text-xs";
    coldBox.innerHTML = `
      <div class="flex items-center justify-between text-purple-300 font-bold">
        <span>🔬 Empirical Bayes Prior Shrinkage (N=${coldStartMeta.n_days} Days)</span>
        <span class="font-mono text-[11px]">Confidence: ${(coldStartMeta.confidence_score * 100).toFixed(0)}%</span>
      </div>
      <div class="grid grid-cols-2 gap-2 text-slate-300 text-[11px] pt-1">
        <div>Category Prior Mean: <b class="font-mono text-purple-300">${coldStartMeta.prior_category_mean}%</b> (Weight: ${coldStartMeta.weight_prior_pct}%)</div>
        <div>Observed Mean: <b class="font-mono text-slate-200">${coldStartMeta.observed_mean}%</b> (Weight: ${coldStartMeta.weight_observed_pct}%)</div>
      </div>
      <div class="text-[11px] text-purple-200/80 pt-1">Calibrated Posterior Expectation: <b class="font-mono text-emerald-400">${coldStartMeta.posterior_calibrated_mean}%</b></div>
    `;
    container.appendChild(coldBox);
  }

  drivers.forEach((d, idx) => {
    const item = document.createElement("div");
    item.className = "p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2 hover:border-slate-700 transition-all";

    const evidenceKeys = Object.keys(d.source_evidence || {});
    let evidenceHTML = "";
    evidenceKeys.forEach(k => {
      evidenceHTML += `<div class="text-[11px] text-slate-400"><span class="text-slate-500 font-mono">${k}:</span> <span class="text-slate-300">${d.source_evidence[k]}</span></div>`;
    });

    item.innerHTML = `
      <div class="flex items-start justify-between">
        <div>
          <span class="text-xs font-bold text-white">${idx + 1}. ${d.name}</span>
          <div class="text-[11px] text-indigo-400 font-mono">${d.category}</div>
        </div>
        <div class="text-right font-mono">
          <div class="text-xs font-bold text-rose-400">-€${Math.abs(d.revenue_impact_eur).toLocaleString()}</div>
          <div class="text-[10px] text-slate-400">${d.percentage_contribution}% contribution</div>
        </div>
      </div>

      <div class="pt-2 border-t border-slate-800 space-y-1">
        <div class="flex items-center justify-between text-[10px] text-slate-500 font-mono">
          <span>Method: <b class="text-slate-400">${d.analytical_method}</b></span>
          <span>Confidence: <b class="text-emerald-400">${(d.confidence_score * 100).toFixed(0)}%</b></span>
        </div>
        <div class="mt-1 p-2 bg-slate-950 rounded border border-slate-800/80 space-y-0.5">
          ${evidenceHTML}
        </div>
      </div>
    `;

    container.appendChild(item);
  });
}

function renderNarrative(narrative) {
  const container = document.getElementById("narrativeContainer");
  container.innerHTML = "";

  const headline = document.createElement("div");
  headline.className = "p-3 rounded-lg bg-indigo-950/40 border border-indigo-800/40 font-semibold text-white text-xs";
  headline.textContent = narrative.headline;
  container.appendChild(headline);

  const summary = document.createElement("p");
  summary.className = "text-slate-300 leading-relaxed";
  summary.textContent = narrative.executive_summary;
  container.appendChild(summary);

  (narrative.narrative_blocks || []).forEach(b => {
    const block = document.createElement("div");
    block.className = "p-3 bg-slate-900 rounded-lg border border-slate-800 space-y-1";
    block.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="font-bold text-slate-200 text-xs">${b.title}</span>
        <span class="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40">${b.provenance}</span>
      </div>
      <p class="text-slate-400 text-xs whitespace-pre-line">${b.text}</p>
    `;
    container.appendChild(block);
  });
}

function renderActions(actions) {
  const container = document.getElementById("actionsList");
  container.innerHTML = "";

  actions.forEach(act => {
    const card = document.createElement("div");
    card.className = "p-3.5 rounded-lg bg-slate-900/90 border border-slate-800 space-y-2.5 hover:border-slate-700 transition-all";

    let authBadge = "";
    let triggerBtn = "";

    if (act.is_user_authorized) {
      authBadge = `<span class="px-2 py-0.5 text-[10px] font-semibold bg-emerald-500/20 text-emerald-400 rounded border border-emerald-500/30">Authorized Owner</span>`;
      triggerBtn = `<button onclick="openActionModal('${act.action_id}')" class="px-3 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded text-xs transition-colors flex items-center space-x-1"><i data-lucide="play" class="w-3 h-3 fill-current"></i><span>Execute Action</span></button>`;
    } else {
      authBadge = `<span class="px-2 py-0.5 text-[10px] font-semibold bg-slate-800 text-slate-400 rounded border border-slate-700">Requires Elevated Rights</span>`;
      triggerBtn = `<button disabled class="px-3 py-1.5 bg-slate-800 text-slate-500 font-semibold rounded text-xs cursor-not-allowed">Restricted</button>`;
    }

    card.innerHTML = `
      <div class="flex items-start justify-between">
        <div>
          <span class="text-xs font-bold text-white">${act.action_title}</span>
          <div class="text-[11px] text-amber-400/90 font-mono">${act.action_id} • Lever: ${act.controllable_lever}</div>
        </div>
        ${authBadge}
      </div>

      <p class="text-xs text-slate-400">${act.detailed_description}</p>

      <div class="grid grid-cols-2 gap-2 text-[11px] bg-slate-950 p-2 rounded border border-slate-800/80">
        <div>Impact: <b class="text-emerald-400 font-mono">${act.expected_kpi_lift}</b></div>
        <div>Owner: <b class="text-indigo-300 font-mono">${act.owner_role}</b></div>
      </div>

      <div class="flex items-center justify-between pt-1">
        <span class="text-[10px] text-slate-500 font-mono">Time: ${act.implementation_time} • Conf: ${(act.confidence_score*100).toFixed(0)}%</span>
        ${triggerBtn}
      </div>
    `;

    container.appendChild(card);
  });
}

function renderTelemetry(tel) {
  if (!tel) return;
  document.getElementById("telemetryQueryId").textContent = tel.query_id;
  document.getElementById("telLatency").textContent = `${tel.total_latency_ms} ms`;
  document.getElementById("telTokens").textContent = `${tel.token_economics.total_tokens} tok`;
  document.getElementById("telCost").textContent = `$${tel.token_economics.total_cost_per_insight_usd.toFixed(5)}`;
  document.getElementById("telSavings").textContent = `${tel.token_economics.cost_savings_vs_full_llm_pct}%`;
}

function openActionModal(actionId) {
  const act = currentAnalysisData.recommended_actions.find(a => a.action_id === actionId);
  if (!act) return;

  selectedActionToExecute = act;
  document.getElementById("modalActionCode").textContent = `${act.action_id} • ${act.controllable_lever}`;
  document.getElementById("modalActionTitle").textContent = act.action_title;
  document.getElementById("modalActionImpact").textContent = act.expected_kpi_lift;
  document.getElementById("modalActionOwner").textContent = act.owner_role;
  document.getElementById("modalActionMonitoring").textContent = act.monitoring_plan;

  document.getElementById("actionModal").classList.remove("hidden");
  initLucide();
}

function hideModal() {
  document.getElementById("actionModal").classList.add("hidden");
  selectedActionToExecute = null;
}

async function executeSelectedAction() {
  if (!selectedActionToExecute) return;
  const roleId = document.getElementById("personaSelect").value;

  try {
    const res = await fetch("/api/action/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action_id: selectedActionToExecute.action_id,
        role_id: roleId,
        decision_right_code: selectedActionToExecute.decision_right_code
      })
    });

    const data = await res.json();
    alert(`Action Dispatched Successfully!\n\nStatus: ${data.status}\n${data.message}`);
    hideModal();
  } catch (err) {
    alert(`Execution failed: ${err.message}`);
  }
}

async function handleFeedbackSubmit(e) {
  e.preventDefault();
  const scenarioId = document.getElementById("scenarioSelect").value;
  const persona = document.getElementById("personaSelect").value;
  const comment = document.getElementById("feedbackComment").value;

  try {
    const res = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_id: scenarioId,
        persona: persona,
        driver_id: "checkout_api_outage",
        feedback_type: activeFeedbackType,
        rating: 5,
        comment: comment
      })
    });

    const data = await res.json();
    document.getElementById("feedbackStatus").textContent = `✓ Prior updated! New multiplier: ${data.new_calibrated_multiplier}x (Total Confs: ${data.total_confirmations})`;
    document.getElementById("feedbackStatus").classList.add("text-emerald-400");
    document.getElementById("feedbackComment").value = "";
  } catch (err) {
    console.error("Feedback error:", err);
  }
}

window.openActionModal = openActionModal;
