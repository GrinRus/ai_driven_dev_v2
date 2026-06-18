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
  const projectPath = document.getElementById("projectPath");
  const workItemChip = document.getElementById("workItemChip");
  const runChip = document.getElementById("runChip");
  const projectRoot = dashboard.project_root || "...";
  const workItemLabel = `Work item: ${dashboard.work_item || "unknown"}`;
  const runLabel = run.run_id ? `Run: ${run.run_id}` : "Run: none";
  projectPath.textContent = projectRoot;
  projectPath.title = projectRoot;
  workItemChip.textContent = workItemLabel;
  workItemChip.title = workItemLabel;
  runChip.textContent = runLabel;
  runChip.title = runLabel;
  const runtime = selectedRuntimeView();
  const ready = runtime ? runtime.provider_available && runtime.execution_command_available : false;
  const localStatus = document.getElementById("localStatus");
  if (state.readinessLoading) {
    localStatus.textContent = "Checking runtime readiness...";
    localStatus.className = "status-chip";
    return;
  }
  if (runtime) {
    const localStatusLabel = `${state.selectedRuntime}: ${ready ? "ready" : "needs check"}`;
    localStatus.textContent = localStatusLabel;
    localStatus.title = localStatusLabel;
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

function workItemStatusClass(item) {
  const stateName = String(item?.terminal_state || "ready");
  if (stateName === "completed") return "good";
  if (stateName === "blocked") return "warn";
  if (stateName === "running") return "running";
  return "";
}

function projectHomeWorkItems() {
  return state.projectHome?.work_items || [];
}

function currentWorkItemSummary() {
  const workItem = state.dashboard?.work_item || state.projectHome?.selected_work_item || "";
  return projectHomeWorkItems().find((item) => item.work_item === workItem) || null;
}

function renderProjectSetRootChips(item) {
  const roots = item?.project_set_roots || [];
  if (!roots.length) return `<span class="small-badge">single root</span>`;
  return roots.slice(0, 3).map((root) => (
    `<span class="small-badge" title="${escapeHtml(root.root)}">${escapeHtml(root.root_id)}:${escapeHtml(root.relative_root)}</span>`
  )).join("");
}

function renderProjectHomeRail() {
  const host = document.getElementById("projectHomeRail");
  if (!host) return;
  const home = state.projectHome;
  if (!home) {
    host.innerHTML = `<div class="empty-state compact">Project Home loading...</div>`;
    return;
  }
  const current = currentWorkItemSummary();
  const items = projectHomeWorkItems();
  host.innerHTML = `
    <div class="project-home-tabs" role="group" aria-label="Project and work item navigation">
      <button data-tab-shortcut="project-home" class="${state.activeTab === "project-home" ? "active" : ""}" type="button">Projects</button>
      <button data-tab-shortcut="project-home" class="${state.activeTab === "project-home" ? "active" : ""}" type="button">Work items</button>
    </div>
    <div class="rail-header small">
      <span>Active work items</span>
      <span class="counter">${escapeHtml(items.length)}</span>
    </div>
    <div class="work-item-board-rail">
      ${items.length ? items.slice(0, 6).map((item) => `
        <button class="work-item-card ${item.work_item === current?.work_item ? "active" : ""}" data-project-home-resume="${escapeHtml(item.work_item)}" type="button">
          <span>
            <strong>${escapeHtml(item.work_item)}</strong>
            <small>${escapeHtml(item.active_stage)} / ${escapeHtml(item.stage_progress_label)}</small>
          </span>
          <span class="small-badge ${workItemStatusClass(item)}">${escapeHtml(item.terminal_state)}</span>
        </button>
      `).join("") : `<div class="empty-state compact">No work items in this project.</div>`}
    </div>
  `;
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

function stageHasEvidence(stage) {
  return (state.dashboard?.stages || []).some((item) => item.stage === stage && Number(item.attempt_count || 0) > 0);
}

function updateContextualTabs() {
  const alwaysVisible = new Set([
    "project-home",
    "overview",
    "questions",
    "validation",
    "timeline",
    "artifacts",
    "recovery",
    "logs",
    "approvals",
    "request",
    "history"
  ]);
  const visible = new Set(alwaysVisible);
  if (state.activeStage === "implement" || stageHasEvidence("implement")) visible.add("implement-review");
  if (state.activeStage === "review" || stageHasEvidence("review")) visible.add("review-findings");
  if (state.activeStage === "qa" || stageHasEvidence("qa") || state.dashboard?.terminal_handoff) visible.add("qa-verdict");
  document.querySelectorAll("[data-tab]").forEach((button) => {
    const tab = button.dataset.tab;
    const isVisible = visible.has(tab);
    button.hidden = !isVisible;
  });
  if (!visible.has(state.activeTab)) {
    state.activeTab = "overview";
  }
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
