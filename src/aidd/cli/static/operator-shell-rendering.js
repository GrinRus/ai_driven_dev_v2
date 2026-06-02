function renderRuntimeSelector() {
  const select = document.getElementById("runtimeSelect");
  const runtimes = state.readinessLoading ? [] : (state.readiness?.runtimes || []);
  const runtimeIds = runtimes.map((runtime) => String(runtime.runtime_id || ""));
  const options = [
    `<option value="">${state.readinessLoading ? "Checking runtimes..." : "Select runtime"}</option>`
  ];
  if (state.selectedRuntime && !runtimeIds.includes(state.selectedRuntime)) {
    const label = state.readinessLoading
      ? "checking"
      : state.readinessError
        ? "unverified"
        : "not listed";
    options.push(
      `<option value="${escapeHtml(state.selectedRuntime)}" selected>${escapeHtml(state.selectedRuntime)} (${label})</option>`
    );
  }
  select.innerHTML = [
    ...options,
    ...runtimes.map((runtime) => {
      const runtimeId = String(runtime.runtime_id || "");
      const selected = runtimeId === state.selectedRuntime ? " selected" : "";
      const ready = runtime.provider_available && runtime.execution_command_available;
      const label = ready ? "ready" : "check";
      return `<option value="${escapeHtml(runtimeId)}"${selected}>${escapeHtml(runtimeId)} (${label})</option>`;
    })
  ].join("");
  setRunButtonState();
}

function scrollActiveStageIntoView() {
  const rail = document.getElementById("stageRail");
  if (!rail || !window.matchMedia("(max-width: 760px)").matches) return;
  const active = rail.querySelector(`[data-stage="${CSS.escape(state.activeStage)}"]`);
  active?.scrollIntoView({behavior: "auto", block: "nearest", inline: "center"});
}

function selectedRuntimeView() {
  if (state.readinessLoading) return null;
  return (state.readiness?.runtimes || []).find((runtime) => runtime.runtime_id === state.selectedRuntime) || null;
}

function selectedRuntimeReady() {
  const runtime = selectedRuntimeView();
  return Boolean(runtime && runtime.provider_available && runtime.execution_command_available);
}

function readinessText(value, fallback = "not reported") {
  const text = String(value ?? "").trim();
  return text || fallback;
}

function timeoutSummary(runtime) {
  if (!runtime) return "not reported";
  const defaultTimeout = runtime.default_timeout_seconds ?? "";
  const defaultText = defaultTimeout === "" ? "default: inherited" : `default: ${defaultTimeout}s`;
  const stageTimeouts = Object.entries(runtime.stage_timeout_seconds || {});
  const stageText = stageTimeouts.length
    ? `stages: ${stageTimeouts.map(([stage, seconds]) => `${stage} ${seconds}s`).join(", ")}`
    : "stages: none";
  return `${defaultText}; ${stageText}`;
}

function readinessDetail(label, value, maxLength = 72) {
  const text = readinessText(value);
  return `
    <div class="panel-item">
      <strong>${escapeHtml(label)}</strong>
      <span title="${escapeHtml(text)}">${escapeHtml(compactPath(text, maxLength))}</span>
    </div>
  `;
}

function ensureRunnableRuntime() {
  if (!state.selectedRuntime) {
    document.getElementById("runtimeSelect").focus();
    toast("Select runtime first.");
    return false;
  }
  if (!selectedRuntimeReady()) {
    document.getElementById("runtimeSelect").focus();
    toast("Selected runtime is not ready.");
    return false;
  }
  return true;
}

function renderTopbar() {
  const dashboard = state.dashboard || {};
  const run = dashboard.run || {};
  document.getElementById("projectPath").textContent = dashboard.project_root || "...";
  document.getElementById("workItemChip").textContent = `Work item: ${dashboard.work_item || "unknown"}`;
  document.getElementById("runChip").textContent = run.run_id ? `Run: ${run.run_id}` : "Run: none";
  const runtime = selectedRuntimeView();
  const ready = runtime ? runtime.provider_available && runtime.execution_command_available : false;
  const localStatus = document.getElementById("localStatus");
  if (state.readinessLoading) {
    localStatus.textContent = "Checking runtime readiness...";
    localStatus.className = "status-chip";
    return;
  }
  if (runtime) {
    localStatus.textContent = `${state.selectedRuntime}: ${ready ? "ready" : "needs check"}`;
    localStatus.className = ready ? "status-chip good" : "status-chip";
    return;
  }
  localStatus.textContent = state.readinessError ? "Runtime readiness unavailable" : "Local control-plane connected";
  localStatus.className = state.readinessError ? "status-chip" : "status-chip good";
}

function renderStageRail() {
  const stages = state.dashboard?.stages || [];
  const done = stages.filter((item) => item.status === "succeeded").length;
  document.getElementById("stageCounter").textContent = `${done}/${STAGES.length}`;
  document.getElementById("stageRail").innerHTML = stages.map((item, index) => {
    const isActive = item.stage === state.activeStage;
    const active = isActive ? " active" : "";
    const status = statusClass(item.status);
    const markers = [
      item.stale ? `<span class="small-badge warn" title="${escapeHtml(item.stale_reason || "downstream evidence is stale")}">stale</span>` : "",
      item.unresolved_blocking_count ? `<span class="small-badge warn">Q${item.unresolved_blocking_count}</span>` : "",
      item.validator_fail_count ? `<span class="small-badge bad">V${item.validator_fail_count}</span>` : "",
      item.attempt_count ? `<span class="small-badge">${escapeHtml(item.attempt_count)}x</span>` : ""
    ].filter(Boolean).join("");
    return `
      <button class="stage-card${active}" data-stage="${escapeHtml(item.stage)}" type="button" aria-current="${isActive ? "step" : "false"}">
        <span class="stage-index">${index + 1}</span>
        <span class="stage-copy">
          <span class="stage-name">${escapeHtml(item.title)}</span>
          <span class="stage-subtitle">${escapeHtml(item.subtitle)}</span>
        </span>
        <span class="stage-markers">
          <span class="marker-dot ${escapeHtml(status)}" title="${escapeHtml(item.status)}"></span>
          ${markers}
        </span>
      </button>
    `;
  }).join("");
  requestAnimationFrame(scrollActiveStageIntoView);
}

function renderStageHeader() {
  const item = activeStageItem();
  document.getElementById("stageTitle").textContent = item?.title || stageTitle(state.activeStage);
  document.getElementById("stageSubtitle").textContent = item?.subtitle || stageSubtitle(state.activeStage);
  document.getElementById("stageBadges").innerHTML = [
    `<span class="status-badge ${escapeHtml(statusClass(item?.status))}">${escapeHtml(item?.status || "pending")}</span>`,
    item?.stale ? `<span class="status-badge warn" title="${escapeHtml(item.stale_reason || "downstream evidence is stale")}">stale</span>` : "",
    `<span class="status-badge">Attempts ${escapeHtml(item?.attempt_count || 0)}</span>`,
    `<span class="status-badge">Validation ${escapeHtml(item?.validator_pass_count || 0)}/${escapeHtml(item?.validator_fail_count || 0)}</span>`
  ].filter(Boolean).join("");
}

function renderInlineMarkdown(value) {
  return escapeHtml(value).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function renderMarkdown(text) {
  const lines = String(text ?? "").split(/\r?\n/);
  let html = "";
  let inCode = false;
  let inList = false;
  const closeList = () => {
    if (inList) {
      html += "</ul>";
      inList = false;
    }
  };
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("```")) {
      if (inCode) {
        html += "</code></pre>";
        inCode = false;
      } else {
        closeList();
        html += "<pre><code>";
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      html += `${escapeHtml(line)}\n`;
      continue;
    }
    if (!trimmed) {
      closeList();
      continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      closeList();
      const level = Math.min(heading[1].length, 6);
      html += `<h${level}>${renderInlineMarkdown(heading[2])}</h${level}>`;
      continue;
    }
    const bullet = line.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      if (!inList) {
        html += "<ul>";
        inList = true;
      }
      html += `<li>${renderInlineMarkdown(bullet[1])}</li>`;
      continue;
    }
    closeList();
    html += `<p>${renderInlineMarkdown(line)}</p>`;
  }
  closeList();
  if (inCode) html += "</code></pre>";
  return html || "<p>Empty document</p>";
}
