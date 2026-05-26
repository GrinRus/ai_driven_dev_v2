
const STAGES = ["idea", "research", "plan", "review-spec", "tasklist", "implement", "review", "qa"];
const STAGE_COPY = {
  "idea": ["Idea", "Clarify the request"],
  "research": ["Research", "Gather context"],
  "plan": ["Plan", "Design the approach"],
  "review-spec": ["Review Spec", "Check the plan"],
  "tasklist": ["Tasklist", "Break down work"],
  "implement": ["Implement", "Make changes"],
  "review": ["Review", "Inspect quality"],
  "qa": ["QA", "Verify outcomes"]
};
const PREFERRED_ARTIFACT_KEYS = [
  "idea_brief",
  "research_notes",
  "plan",
  "review_spec_report",
  "tasklist",
  "implementation_report",
  "review_report",
  "qa_report",
  "stage_result",
  "validator_report",
  "questions",
  "input_bundle",
  "stage_brief",
  "repair_brief",
  "operator_request",
  "answers"
];
const MAX_ARTIFACT_READ_BYTES = 262144;
const state = {
  dashboard: null,
  readiness: null,
  activeStage: "idea",
  activeTab: "overview",
  selectedRuntime: "",
  activeRunId: "",
  activeJobId: "",
  activeJobCursor: 0,
  activeJobLogChunks: [],
  activeJobStatus: null,
  activeJobTimer: null,
  activeArtifactKey: "",
  artifactViewMode: "preview",
  logFilter: "all",
  rawLogMode: false,
  savedLogText: ""
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
}

function questionControlId(prefix, questionId, index) {
  const safeQuestionId = String(questionId ?? "")
    .trim()
    .replace(/[^A-Za-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `${prefix}-${index + 1}-${safeQuestionId || "question"}`;
}

function compactPath(value, maxLength = 56) {
  const text = String(value ?? "");
  if (text.length <= maxLength) return text;
  const parts = text.split("/").filter(Boolean);
  if (parts.length >= 3) {
    const tail = parts.slice(-3).join("/");
    if (tail.length + 4 <= maxLength) return `.../${tail}`;
  }
  const keep = Math.max(8, maxLength - 3);
  return `${text.slice(0, keep)}...`;
}

function pathLine(value, maxLength = 56) {
  const text = String(value ?? "");
  return `<span class="path-line" title="${escapeHtml(text)}">${escapeHtml(compactPath(text, maxLength))}</span>`;
}

function byteRangeSummary(view) {
  const start = Number(view?.start_byte || 0);
  const end = Number(view?.end_byte || 0);
  const total = Number(view?.byte_size || 0);
  return `${start}-${end} of ${total} bytes`;
}

function renderTruncationNotice(kind, view, mode = "") {
  if (!view?.truncated) return "";
  const direction = view.truncated_head && view.truncated_tail
    ? "selected range"
    : view.truncated_head
      ? "latest content"
      : "first content";
  const subject = kind === "artifact" ? "Artifact view truncated" : "Runtime log truncated";
  const artifactHint = mode === "preview"
    ? "Switch to Source for a larger bounded read, or open the folder for the full file."
    : "Source view is bounded. Open the folder for the full file.";
  const logHint = "Full runtime.log remains on disk and available through CLI log inspection.";
  const hint = kind === "artifact" ? artifactHint : logHint;
  return `
    <div class="truncation-notice" role="status">
      <strong>${subject}</strong>
      <span>Showing ${escapeHtml(direction)} (${escapeHtml(byteRangeSummary(view))}). ${escapeHtml(hint)}</span>
    </div>
  `;
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok || payload.error) throw new Error(payload.error || response.statusText);
  return payload;
}

async function postJson(path, payload = {}) {
  return api(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });
}

function toast(message) {
  const element = document.getElementById("toast");
  element.textContent = message;
  element.classList.add("visible");
  window.clearTimeout(toast.timer);
  toast.timer = window.setTimeout(() => {
    element.classList.remove("visible");
    if (element.textContent === message) element.textContent = "";
  }, 2800);
}

function stageTitle(stage) {
  return STAGE_COPY[stage]?.[0] || stage;
}

function stageSubtitle(stage) {
  return STAGE_COPY[stage]?.[1] || "";
}

function statusClass(status) {
  return String(status || "pending").toLowerCase().replace(/_/g, "-");
}

function activeStageItem() {
  return (state.dashboard?.stages || []).find((item) => item.stage === state.activeStage) || null;
}

function activeStageView() {
  return state.dashboard?.active_stage_view || null;
}

function needsRuntime(action) {
  return ["run-workflow", "run-stage", "resume-stage"].includes(action);
}

function setRunButtonState() {
  renderNextActionPanel();
}

function activateTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll("[data-tab]").forEach((button) => {
    const isActive = button.dataset.tab === tab;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  const content = document.getElementById("cockpitContent");
  if (content) content.setAttribute("aria-labelledby", `tab-${tab}`);
}

function dashboardUrl() {
  const params = new URLSearchParams({stage: state.activeStage});
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  return `/api/dashboard?${params.toString()}`;
}

async function fetchDashboard() {
  const payload = await api(dashboardUrl());
  state.dashboard = payload.dashboard;
  const version = String(payload.app_version || "").trim();
  document.getElementById("appVersion").textContent = version.startsWith("v") ? version : `v${version || "dev"}`;
  state.activeStage = state.dashboard.active_stage || state.activeStage;
  state.activeRunId = state.dashboard.run?.run_id || "";
  if (!state.selectedRuntime && state.dashboard.run?.runtime_id) {
    state.selectedRuntime = state.dashboard.run.runtime_id;
  }
}

async function fetchReadiness() {
  try {
    state.readiness = await api("/api/runtime-readiness");
  } catch (error) {
    state.readiness = {runtimes: []};
    toast(`Runtime readiness unavailable: ${error.message}`);
  }
}

function renderRuntimeSelector() {
  const select = document.getElementById("runtimeSelect");
  const runtimes = state.readiness?.runtimes || [];
  const runtimeIds = runtimes.map((runtime) => String(runtime.runtime_id || ""));
  if (state.selectedRuntime && !runtimeIds.includes(state.selectedRuntime)) {
    state.selectedRuntime = "";
  }
  select.innerHTML = [
    `<option value="">Select runtime</option>`,
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
  return (state.readiness?.runtimes || []).find((runtime) => runtime.runtime_id === state.selectedRuntime) || null;
}

function selectedRuntimeReady() {
  const runtime = selectedRuntimeView();
  return Boolean(runtime && runtime.provider_available && runtime.execution_command_available);
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
  document.getElementById("localStatus").textContent = runtime
    ? `${state.selectedRuntime}: ${ready ? "ready" : "needs check"}`
    : "Local control-plane connected";
  document.getElementById("localStatus").className = ready || !runtime ? "status-chip good" : "status-chip";
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
    `<span class="status-badge">Attempts ${escapeHtml(item?.attempt_count || 0)}</span>`,
    `<span class="status-badge">Validation ${escapeHtml(item?.validator_pass_count || 0)}/${escapeHtml(item?.validator_fail_count || 0)}</span>`
  ].join("");
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

function renderPrimaryArtifact() {
  const artifact = state.dashboard?.primary_artifact;
  if (!artifact) {
    return `<div class="empty-state">No primary artifact for this stage yet.</div>`;
  }
  const truncated = artifact.truncated ? `<p class="muted">Preview truncated at ${escapeHtml(artifact.excerpt.length)} characters.</p>` : "";
  const body = artifact.content_type === "text/markdown"
    ? `<div class="markdown-preview">${renderMarkdown(artifact.excerpt)}</div>`
    : `<pre>${escapeHtml(artifact.excerpt)}</pre>`;
  return `
    <div class="viewer-header">
      <div>
        <strong>${escapeHtml(artifact.key)}</strong>
        ${pathLine(`${artifact.path} / ${artifact.byte_size} bytes`, 72)}
      </div>
      <button data-open-artifact="${escapeHtml(artifact.path)}" class="secondary" type="button">Open folder</button>
    </div>
    <div class="primary-artifact">${body}${truncated}</div>
  `;
}

function renderQuestionCards({showResume}) {
  const view = activeStageView()?.questions;
  const questions = view?.questions || [];
  if (!questions.length) {
    return `<div class="empty-state">No questions for this stage.</div>`;
  }
  return `
    <div class="question-list">
      ${questions.map((question, index) => {
        const resolved = question.status === "resolved";
        const questionLabel = question.question_id || `question ${index + 1}`;
        const questionTextId = questionControlId("question-text", question.question_id, index);
        const answerId = questionControlId("answer", question.question_id, index);
        const resolutionId = questionControlId("resolution", question.question_id, index);
        const savedAnswer = resolved && question.answer_text
          ? `<div class="saved-answer"><span class="saved-answer-label">Saved answer</span><span class="saved-answer-text">${escapeHtml(question.answer_text)}</span></div>`
          : "";
        return `
          <article class="question-card">
            <div class="question-head">
              <strong>${escapeHtml(question.question_id)}</strong>
              <span class="small-badge ${question.status === "pending-blocking" ? "warn" : resolved ? "good" : ""}">${escapeHtml(question.status)}</span>
            </div>
            <p id="${questionTextId}">${escapeHtml(question.text)}</p>
            ${savedAnswer}
            <label class="sr-only" for="${answerId}">Answer for ${escapeHtml(questionLabel)}</label>
            <textarea id="${answerId}" name="${answerId}" aria-describedby="${questionTextId}" data-question-text="${escapeHtml(question.question_id)}" ${resolved ? "disabled" : ""}></textarea>
            <div class="question-actions">
              <label class="sr-only" for="${resolutionId}">Resolution for ${escapeHtml(questionLabel)}</label>
              <select id="${resolutionId}" name="${resolutionId}" aria-describedby="${questionTextId}" data-question-resolution="${escapeHtml(question.question_id)}" ${resolved ? "disabled" : ""}>
                <option value="resolved">resolved</option>
                <option value="partial">partial</option>
                <option value="deferred">deferred</option>
              </select>
              <button data-save-answer="${escapeHtml(question.question_id)}" type="button" ${resolved ? "disabled" : ""}>Save answer</button>
              ${showResume ? `<button data-answer-resume="${escapeHtml(question.question_id)}" type="button" ${resolved ? "disabled" : ""}>Answer & resume</button>` : ""}
            </div>
          </article>
        `;
      }).join("")}
    </div>
  `;
}

function renderFirstLaunchState() {
  const runtime = selectedRuntimeView();
  const ready = selectedRuntimeReady();
  const detail = !state.selectedRuntime
    ? "Select a runtime to start the first governed workflow run."
    : ready
      ? `${state.selectedRuntime} is ready to start the workflow.`
      : `${state.selectedRuntime} needs a passing readiness check before the first run.`;
  return `
    <section class="surface first-launch-state">
      <div class="surface-title">
        <span>First launch</span>
        <span class="small-badge">no run yet</span>
      </div>
      <p>${escapeHtml(detail)}</p>
      <button data-first-launch-run type="button" ${ready && runtime ? "" : "disabled"}>Run workflow</button>
    </section>
  `;
}

function renderOverview() {
  if (!state.dashboard?.run?.run_id) {
    return renderFirstLaunchState();
  }
  const item = activeStageItem();
  const view = activeStageView();
  const unresolved = view?.questions?.unresolved_blocking_question_ids || [];
  if (unresolved.length) {
    return `
      <section class="surface">
        <div class="surface-title">
          <span>Blocking questions</span>
          <span class="small-badge warn">${escapeHtml(unresolved.length)} blocking</span>
        </div>
        ${renderQuestionCards({showResume: true})}
      </section>
    `;
  }
  const result = view?.result;
  return `
    <div class="overview-grid">
      <section class="surface">
        <div class="surface-title">
          <span>Primary artifact</span>
          <span class="small-badge">${escapeHtml(state.activeStage)}</span>
        </div>
        ${renderPrimaryArtifact()}
      </section>
      <aside class="surface">
        <div class="surface-title">Stage health</div>
        <div class="metric-grid">
          <div class="metric"><span>State</span><strong>${escapeHtml(item?.status || "pending")}</strong></div>
          <div class="metric"><span>Attempts</span><strong>${escapeHtml(item?.attempt_count || 0)}</strong></div>
          <div class="metric"><span>Questions</span><strong>${escapeHtml(item?.unresolved_blocking_count || 0)}/${escapeHtml(item?.question_count || 0)}</strong></div>
          <div class="metric"><span>Validation</span><strong>${escapeHtml(item?.validator_pass_count || 0)}/${escapeHtml(item?.validator_fail_count || 0)}</strong></div>
        </div>
        <div class="panel-item">
          <strong>Eligibility</strong>
          <span>${escapeHtml(item?.reason || "not started")}</span>
        </div>
        <div class="panel-item">
          <strong>Validator report</strong>
          ${pathLine(result?.validator_report_path || "not available")}
        </div>
      </aside>
    </div>
  `;
}

function renderQuestions() {
  return `<section class="surface">${renderQuestionCards({showResume: true})}</section>`;
}

function renderValidation() {
  const result = activeStageView()?.result;
  if (!result) return `<div class="empty-state">No validation evidence for this stage yet.</div>`;
  const repairs = (result.repair_output_paths || []).map((path) => `
    <button class="artifact-row" data-open-artifact="${escapeHtml(path)}" type="button">
      <span><strong>${escapeHtml(path.split("/").pop())}</strong>${pathLine(path)}</span>
      <span class="small-badge warn">repair</span>
    </button>
  `).join("") || `<div class="empty-state">No repair outputs recorded.</div>`;
  return `
    <section class="surface">
      <div class="surface-title">Validation</div>
      <div class="metric-grid">
        <div class="metric"><span>Pass</span><strong>${escapeHtml(result.validator_pass_count)}</strong></div>
        <div class="metric"><span>Fail</span><strong>${escapeHtml(result.validator_fail_count)}</strong></div>
        <div class="metric"><span>Final state</span><strong>${escapeHtml(result.final_state)}</strong></div>
        <div class="metric"><span>Attempts</span><strong>${escapeHtml(result.attempt_count)}</strong></div>
      </div>
      <div class="panel-item">
        <strong>Validator report</strong>
        ${pathLine(result.validator_report_path)}
      </div>
      <div class="panel-item">
        <strong>Repair evidence</strong>
        <div class="recent-artifacts">${repairs}</div>
      </div>
    </section>
  `;
}

function preferredArtifactKey(documents) {
  for (const key of PREFERRED_ARTIFACT_KEYS) {
    if (Object.prototype.hasOwnProperty.call(documents, key)) return key;
  }
  return Object.keys(documents)[0] || "";
}

async function loadArtifactDocument(key) {
  const viewer = document.getElementById("artifactViewer");
  if (!viewer) return;
  try {
    const params = new URLSearchParams({stage: state.activeStage, key});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    params.set("mode", state.artifactViewMode);
    if (state.artifactViewMode === "source") params.set("limit", String(MAX_ARTIFACT_READ_BYTES));
    const documentView = await api(`/api/artifacts/document?${params.toString()}`);
    const previewActive = state.artifactViewMode === "preview" ? " active" : "";
    const sourceActive = state.artifactViewMode === "source" ? " active" : "";
    const body = state.artifactViewMode === "source"
      ? `<pre>${escapeHtml(documentView.text)}</pre>`
      : `<div class="markdown-preview">${renderMarkdown(documentView.text)}</div>`;
    const truncation = renderTruncationNotice("artifact", documentView, state.artifactViewMode);
    viewer.innerHTML = `
      <div class="viewer-header">
        <div>
          <strong>${escapeHtml(documentView.key)}</strong>
          ${pathLine(`${documentView.path} / ${documentView.byte_size} bytes`, 72)}
        </div>
        <div class="viewer-modes">
          <button data-artifact-mode="preview" class="${previewActive}" type="button">Preview</button>
          <button data-artifact-mode="source" class="${sourceActive}" type="button">Source</button>
          <button data-open-artifact="${escapeHtml(documentView.path)}" class="secondary" type="button">Open folder</button>
        </div>
      </div>
      ${truncation}
      ${body}
    `;
  } catch (error) {
    viewer.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function renderArtifacts() {
  const item = activeStageItem();
  if (!item || Number(item.attempt_count || 0) <= 0) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">No artifacts for this stage yet.</div>`;
    return;
  }
  const params = new URLSearchParams({stage: state.activeStage});
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  const view = await api(`/api/artifacts?${params.toString()}`);
  const documents = view.documents || {};
  if (!state.activeArtifactKey || !Object.prototype.hasOwnProperty.call(documents, state.activeArtifactKey)) {
    state.activeArtifactKey = preferredArtifactKey(documents);
  }
  const docs = Object.entries(documents).map(([key, path]) => `
    <button class="artifact-doc ${key === state.activeArtifactKey ? "active" : ""}" data-artifact-key="${escapeHtml(key)}" type="button">
      ${escapeHtml(key)}
      <small title="${escapeHtml(path)}">${escapeHtml(compactPath(path, 64))}</small>
    </button>
  `).join("") || `<div class="empty-state">No document artifacts.</div>`;
  const logs = Object.entries(view.logs || {}).map(([key, path]) => `
    <button class="artifact-doc" data-open-artifact="${escapeHtml(path)}" type="button">
      ${escapeHtml(key)}
      <small title="${escapeHtml(path)}">${escapeHtml(compactPath(path, 64))}</small>
    </button>
  `).join("") || `<div class="empty-state">No log artifacts.</div>`;
  document.getElementById("cockpitContent").innerHTML = `
    <div class="artifact-layout">
      <aside class="surface">
        <div class="surface-title">Documents</div>
        <div class="artifact-list">${docs}</div>
        <div class="surface-title" style="margin-top:12px">Logs</div>
        <div class="artifact-list">${logs}</div>
      </aside>
      <section id="artifactViewer" class="artifact-viewer">Select a document</section>
    </div>
  `;
  if (state.activeArtifactKey) await loadArtifactDocument(state.activeArtifactKey);
}

function interventionTargetEntries(documents) {
  const excluded = new Set([
    "answers",
    "input_bundle",
    "operator_request",
    "questions",
    "repair_brief",
    "repair_context",
    "stage_brief",
    "validator_report"
  ]);
  const blockedNames = new Set([
    "answers.md",
    "input-bundle.md",
    "questions.md",
    "repair-brief.md",
    "stage-brief.md",
    "validator-report.md"
  ]);
  return Object.entries(documents || {}).filter(([key, path]) => {
    const textPath = String(path || "");
    return !excluded.has(key)
      && textPath.includes(`/stages/${state.activeStage}/`)
      && !textPath.includes("/operator-requests/")
      && !blockedNames.has(textPath.split("/").pop())
      && textPath.endsWith(".md");
  });
}

function interventionTargetLabel(key) {
  return String(key || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function updateSubmitInterventionState() {
  const textarea = document.getElementById("operatorRequestText");
  const button = document.getElementById("submitInterventionButton");
  if (!button) return;
  button.disabled = !selectedRuntimeReady() || !String(textarea?.value || "").trim();
}

async function renderRequestChange() {
  let documents = {};
  const item = activeStageItem();
  if (item && Number(item.attempt_count || 0) > 0) {
    try {
      const params = new URLSearchParams({stage: state.activeStage});
      if (state.activeRunId) params.set("run_id", state.activeRunId);
      const artifacts = await api(`/api/artifacts?${params.toString()}`);
      documents = artifacts.documents || {};
    } catch (error) {
      documents = {};
    }
  }
  const targets = interventionTargetEntries(documents);
  const targetBody = targets.length ? targets.map(([key, path]) => `
    <label class="target-option">
      <input type="checkbox" data-intervention-target="${escapeHtml(path)}">
      <span><strong>${escapeHtml(interventionTargetLabel(key))}</strong>${pathLine(path, 82)}</span>
    </label>
  `).join("") : `<div class="empty-state">No current-stage target documents available yet. The request can still run against the stage scope.</div>`;
  document.getElementById("cockpitContent").innerHTML = `
    <section class="surface">
      <div class="surface-title">
        <span>Request change</span>
        <span class="small-badge">${escapeHtml(state.activeStage)}</span>
      </div>
      <div class="intervention-form">
        <div class="form-field">
          <label for="operatorRequestText">Operator request</label>
          <textarea id="operatorRequestText" placeholder="Add rollback risks to the plan and update stage-result evidence."></textarea>
        </div>
        <div class="form-field">
          <div class="target-documents-title">Target documents</div>
          <div class="target-documents">${targetBody}</div>
        </div>
        <div class="question-actions">
          <button id="submitInterventionButton" type="button">Submit & run</button>
        </div>
      </div>
    </section>
  `;
  updateSubmitInterventionState();
}

function renderApprovalRequestCard(request, decision, pendingIds) {
  const payload = request.payload || {};
  const command = payload.command || payload.cmd || "";
  const paths = request.paths || [];
  const pending = pendingIds.has(request.id);
  const decisionBadge = decision
    ? `<span class="small-badge ${decision.action === "deny" || decision.action === "cancel" ? "bad" : "good"}">${escapeHtml(decision.action)}</span>`
    : pending ? `<span class="small-badge warn">pending</span>` : `<span class="small-badge">recorded</span>`;
  const pathBody = paths.length
    ? paths.map((path) => pathLine(path, 86)).join("")
    : `<span class="muted">No normalized paths</span>`;
  const actions = pending ? `
    <div class="approval-actions">
      <button data-operator-request="${escapeHtml(request.id)}" data-operator-action="allow_once" type="button">Allow once</button>
      <button data-operator-request="${escapeHtml(request.id)}" data-operator-action="allow_for_session" type="button">Allow session</button>
      <button data-operator-request="${escapeHtml(request.id)}" data-operator-action="deny" class="secondary" type="button">Deny</button>
      <button data-operator-request="${escapeHtml(request.id)}" data-operator-action="cancel" class="danger" type="button">Cancel</button>
    </div>
  ` : "";
  return `
    <article class="approval-card">
      <div class="question-head">
        <strong>${escapeHtml(request.kind || "unknown")} / ${escapeHtml(request.tool_name || "runtime")}</strong>
        ${decisionBadge}
      </div>
      <div class="panel-list">
        <div class="panel-item"><strong>Request</strong><span>${escapeHtml(request.id)}</span></div>
        <div class="panel-item"><strong>Runtime / stage</strong><span>${escapeHtml(request.runtime_id)} / ${escapeHtml(request.stage)}</span></div>
        ${command ? `<div class="panel-item"><strong>Command</strong><code>${escapeHtml(command)}</code></div>` : ""}
        <div class="panel-item"><strong>CWD</strong>${pathLine(request.cwd || "not provided", 86)}</div>
        <div class="panel-item"><strong>Paths</strong><span>${pathBody}</span></div>
        <div class="panel-item"><strong>Payload</strong><pre class="payload-preview">${escapeHtml(JSON.stringify(payload, null, 2))}</pre></div>
        ${decision ? `<div class="panel-item"><strong>Decision</strong><span>${escapeHtml(decision.source)} / ${escapeHtml(decision.reason || "no reason")}</span></div>` : ""}
      </div>
      ${actions}
    </article>
  `;
}

async function renderApprovals() {
  const content = document.getElementById("cockpitContent");
  if (!state.activeJobId) {
    content.innerHTML = `<div class="empty-state">No active runtime approval job.</div>`;
    return;
  }
  try {
    const view = await api(`/api/jobs/${encodeURIComponent(state.activeJobId)}/operator-requests`);
    const requests = view.requests || [];
    const decisions = view.decisions || [];
    const pendingIds = new Set(view.pending_request_ids || []);
    const decisionByRequest = new Map();
    decisions.forEach((decision) => decisionByRequest.set(decision.request_id, decision));
    const cards = requests.length
      ? requests.map((request) => renderApprovalRequestCard(request, decisionByRequest.get(request.id), pendingIds)).join("")
      : `<div class="empty-state">No runtime operator requests for this job.</div>`;
    content.innerHTML = `
      <section class="surface">
        <div class="surface-title">
          <span>Runtime approvals</span>
          <span class="small-badge ${pendingIds.size ? "warn" : "good"}">${escapeHtml(pendingIds.size)} pending</span>
        </div>
        <div class="question-list">${cards}</div>
      </section>
    `;
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function submitApproval(requestId, action) {
  if (!state.activeJobId) return;
  await postJson(`/api/jobs/${encodeURIComponent(state.activeJobId)}/operator-requests/${encodeURIComponent(requestId)}/decision`, {action});
  toast(`Runtime approval ${action}.`);
  await renderApprovals();
}

function parsePrefixedLogLine(text, fallbackStream) {
  const rawText = String(text ?? "");
  const matched = rawText.match(/^\[([^:\]]+):([^:\]]+):(stdout|stderr|system)\]\s?(.*)$/i);
  if (matched) {
    return {
      stream: matched[3].toLowerCase(),
      source: `${matched[1]} / ${matched[2]}`,
      text: matched[4]
    };
  }
  const simple = rawText.match(/^\[(stdout|stderr|system)\]\s?(.*)$/i);
  if (simple) {
    const stream = simple[1].toLowerCase();
    return {
      stream,
      source: stream === "system" ? "system" : "runtime",
      text: simple[2]
    };
  }
  if (!matched) {
    return {
      stream: fallbackStream || "stdout",
      source: fallbackStream || "runtime",
      text: rawText
    };
  }
}

function logEntriesFromChunks(chunks) {
  const entries = [];
  for (const chunk of chunks || []) {
    const stream = String(chunk.stream || "stdout");
    const lines = String(chunk.text || "").split(/\r?\n/);
    lines.forEach((line, index) => {
      if (!line && index === lines.length - 1) return;
      entries.push(parsePrefixedLogLine(line, stream));
    });
  }
  return entries;
}

function logEntriesFromText(text) {
  return String(text ?? "").split(/\r?\n/).filter((line, index, lines) => line || index < lines.length - 1).map((line) => parsePrefixedLogLine(line, "stdout"));
}

function filteredLogEntries(entries) {
  if (state.logFilter === "all") return entries;
  return entries.filter((entry) => String(entry.stream || "").toLowerCase() === state.logFilter);
}

function rawTextFromEntries(entries) {
  return entries.map((entry) => `[${entry.stream}] ${entry.source ? `${entry.source}: ` : ""}${entry.text}`).join("\n");
}

function renderLogPanel({title, meta, entries, rawText, emptyText, actions = "", truncation = null}) {
  const filtered = filteredLogEntries(entries);
  const rawBody = state.logFilter === "all" && rawText ? rawText : rawTextFromEntries(filtered);
  const filterButtons = ["all", "stdout", "stderr", "system"].map((filter) => (
    `<button data-log-filter="${filter}" class="${state.logFilter === filter ? "active" : ""}" type="button">${filter}</button>`
  )).join("");
  const rows = state.rawLogMode
    ? `<pre>${escapeHtml(rawBody)}</pre>`
    : filtered.length
      ? `<div class="log-rows">${filtered.map((entry) => `
          <div class="log-row">
            <span class="log-badge ${escapeHtml(String(entry.stream || "").toLowerCase())}">${escapeHtml(entry.stream)}</span>
            <span class="log-source">${escapeHtml(entry.source)}</span>
            <span class="log-text">${escapeHtml(entry.text)}</span>
          </div>
        `).join("")}</div>`
      : `<div class="empty-state" style="padding:18px 12px">${escapeHtml(emptyText)}</div>`;
  return `
    <section class="log-panel">
      <div class="log-toolbar">
        <div>
          <strong>${escapeHtml(title)}</strong>
          ${pathLine(meta.filter(Boolean).join(" / "), 72)}
        </div>
        <div class="log-actions">
          ${actions}
          <div class="log-filter">
            ${filterButtons}
            <button data-log-raw="toggle" class="${state.rawLogMode ? "active" : ""}" type="button">Raw</button>
          </div>
        </div>
      </div>
      ${renderTruncationNotice("log", truncation)}
      ${rows}
    </section>
  `;
}

function liveJobMatchesStage() {
  if (!state.activeJobStatus) return false;
  return state.activeJobStatus.kind === "workflow" || state.activeJobStatus.stage === state.activeStage;
}

function activeJobStatusClass() {
  return statusClass(state.activeJobStatus?.status || "running");
}

function activeJobIsTerminal() {
  return ["cancelled", "completed", "failed"].includes(state.activeJobStatus?.status || "");
}

function activeJobCancelLabel() {
  const status = state.activeJobStatus?.status || "running";
  if (status === "cancelling") return "Cancelling...";
  if (status === "cancelled") return "Cancelled";
  if (status === "completed") return "Completed";
  if (status === "failed") return "Stopped";
  return "Cancel job";
}

function renderLiveJobActions() {
  if (!state.activeJobId || !state.activeJobStatus) return "";
  const status = state.activeJobStatus.status || "running";
  const disabled = activeJobIsTerminal() || status === "cancelling";
  return `
    <span class="small-badge ${escapeHtml(activeJobStatusClass())}">${escapeHtml(status)}</span>
    <button data-cancel-job="${escapeHtml(state.activeJobId)}" class="danger" type="button" ${disabled ? "disabled" : ""}>${escapeHtml(activeJobCancelLabel())}</button>
  `;
}

async function renderLogs() {
  if (state.activeJobId && liveJobMatchesStage() && (state.activeJobStatus?.status === "running" || state.activeJobStatus?.status === "waiting-for-operator" || state.activeJobStatus?.status === "cancelling" || state.activeJobLogChunks.length)) {
    const entries = logEntriesFromChunks(state.activeJobLogChunks);
    document.getElementById("cockpitContent").innerHTML = renderLogPanel({
      title: `Live job ${state.activeJobId}`,
      meta: [state.activeJobStatus?.status || "running", state.activeJobStatus?.stage || "workflow"],
      entries,
      rawText: rawTextFromEntries(entries),
      emptyText: "Waiting for runtime output...",
      actions: renderLiveJobActions()
    });
    return;
  }
  const item = activeStageItem();
  if (!item || Number(item.attempt_count || 0) <= 0) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">No runtime log for this stage yet.</div>`;
    return;
  }
  try {
    const params = new URLSearchParams({stage: state.activeStage});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    const view = await api(`/api/logs?${params.toString()}`);
    state.savedLogText = view.text || "";
    const summary = view.summary || {};
    document.getElementById("cockpitContent").innerHTML = renderLogPanel({
      title: "Saved runtime.log",
      meta: [summary.run_id ? `run ${summary.run_id}` : "", summary.stage ? `stage ${summary.stage}` : "", summary.attempt_number ? `attempt ${summary.attempt_number}` : ""],
      entries: logEntriesFromText(state.savedLogText),
      rawText: state.savedLogText,
      emptyText: "Saved runtime log is empty",
      truncation: view
    });
  } catch (error) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function renderCockpit() {
  const content = document.getElementById("cockpitContent");
  if (state.activeTab === "overview") content.innerHTML = renderOverview();
  if (state.activeTab === "questions") content.innerHTML = renderQuestions();
  if (state.activeTab === "validation") content.innerHTML = renderValidation();
  if (state.activeTab === "artifacts") await renderArtifacts();
  if (state.activeTab === "logs") await renderLogs();
  if (state.activeTab === "approvals") await renderApprovals();
  if (state.activeTab === "request") await renderRequestChange();
}

function renderNextActionPanel() {
  const action = state.dashboard?.next_action || {action: "choose-runtime", label: "Select runtime", detail: "Choose a runtime.", enabled: false};
  const noRunWithRuntime = action.action === "choose-runtime" && state.selectedRuntime;
  const runtimeNeeded = needsRuntime(action.action) || noRunWithRuntime;
  const runtimeBlocked = runtimeNeeded && (!state.selectedRuntime || !selectedRuntimeReady());
  const disabled = !(action.enabled || noRunWithRuntime) || runtimeBlocked;
  const label = noRunWithRuntime ? "Run workflow" : action.label;
  const detail = runtimeBlocked && state.selectedRuntime
    ? `${action.detail} Selected runtime is not ready.`
    : action.detail;
  document.getElementById("nextActionPanel").innerHTML = `
    <div class="panel-title">Next action</div>
    <p>${escapeHtml(detail)}</p>
    <button id="nextActionButton" class="next-button" data-next-action="${escapeHtml(action.action)}" type="button" ${disabled ? "disabled" : ""}>${escapeHtml(label)}</button>
  `;
}

function renderBlockersPanel() {
  const blockers = state.dashboard?.blockers || [];
  const body = blockers.length ? blockers.map((blocker) => `
    <button class="artifact-row" data-blocker-stage="${escapeHtml(blocker.stage || state.activeStage)}" data-blocker-kind="${escapeHtml(blocker.kind)}" type="button">
      <span>
        <strong>${escapeHtml(blocker.title)}</strong>
        <span>${escapeHtml(blocker.detail)}</span>
        ${blocker.path ? pathLine(blocker.path) : ""}
      </span>
      <span class="small-badge ${blocker.severity === "error" ? "bad" : "warn"}">${escapeHtml(blocker.kind)}</span>
    </button>
  `).join("") : `<p>No blockers detected for the selected stage.</p>`;
  document.getElementById("blockersPanel").innerHTML = `
    <div class="panel-title">Blockers <span class="small-badge ${blockers.length ? "warn" : "good"}">${escapeHtml(blockers.length)}</span></div>
    <div class="panel-list">${body}</div>
  `;
}

function renderEvidencePanel() {
  const refs = state.dashboard?.evidence_refs || [];
  const body = refs.length ? refs.slice(0, 6).map((ref) => `
    <button class="artifact-row" data-evidence-stage="${escapeHtml(ref.stage || state.activeStage)}" data-evidence-path="${escapeHtml(ref.path)}" data-evidence-kind="${escapeHtml(ref.kind)}" type="button">
      <span><strong>${escapeHtml(ref.label)}</strong>${pathLine(ref.path)}</span>
      <span class="small-badge">${escapeHtml(ref.kind)}</span>
    </button>
  `).join("") : `<p>No evidence refs yet.</p>`;
  document.getElementById("evidencePanel").innerHTML = `
    <div class="panel-title">Evidence refs <span class="small-badge">${escapeHtml(refs.length)}</span></div>
    <div class="panel-list">${body}</div>
  `;
}

function renderRuntimeRootPanel() {
  const workspace = state.dashboard?.workspace_root || "";
  document.getElementById("runtimeRootPanel").innerHTML = `
    <div class="panel-title">Runtime root</div>
    <p><code>.aidd/</code></p>
    ${pathLine(workspace)}
    <button data-open-folder="workspace" class="next-button secondary" type="button">Open folder</button>
  `;
}

function renderSafetyPanel() {
  const runtime = selectedRuntimeView();
  const provider = runtime ? (runtime.provider_available ? "provider available" : "provider unavailable") : "runtime not selected";
  const exec = runtime ? (runtime.execution_command_available ? "execution command available" : "execution command unavailable") : "select runtime";
  const readinessClass = runtime && runtime.provider_available && runtime.execution_command_available ? "good" : runtime ? "warn" : "";
  document.getElementById("safetyPanel").innerHTML = `
    <div class="panel-title">Safety / Readiness <span class="small-badge ${readinessClass}">${runtime ? escapeHtml(runtime.runtime_id) : "none"}</span></div>
    <div class="panel-list">
      <div class="panel-item"><strong>No upstream write</strong><span>UI actions stay inside local AIDD workspace and normal runner boundaries.</span></div>
      <div class="panel-item"><strong>Provider</strong><span>${escapeHtml(provider)}</span></div>
      <div class="panel-item"><strong>Execution</strong><span>${escapeHtml(exec)}</span></div>
    </div>
  `;
}

function renderSidebar() {
  renderNextActionPanel();
  renderBlockersPanel();
  renderEvidencePanel();
  renderRuntimeRootPanel();
  renderSafetyPanel();
}

function liveJobActivityEvents() {
  if (!state.activeJobStatus) return [];
  const status = state.activeJobStatus.status || "running";
  const events = [{
    time_utc: state.activeJobStatus.updated_at_utc || "live",
    level: status === "failed" ? "error" : status === "running" ? "info" : "info",
    source: state.activeJobStatus.stage || state.activeJobStatus.kind || "job",
    event: `job.${status}`,
    details: state.activeJobStatus.message || `UI-started ${state.activeJobStatus.kind || "job"} is ${status}.`
  }];
  const entries = logEntriesFromChunks(state.activeJobLogChunks).slice(-10).reverse();
  for (const entry of entries) {
    events.push({
      time_utc: "live",
      level: entry.stream === "stderr" ? "warn" : "info",
      source: entry.source || entry.stream || "runtime",
      event: `job.${entry.stream || "output"}`,
      details: entry.text
    });
  }
  return events;
}

function activityEvents() {
  return [
    ...liveJobActivityEvents(),
    ...(state.dashboard?.activity || [])
  ];
}

function renderActivityTable() {
  const events = activityEvents();
  if (!events.length) {
    document.getElementById("activityTable").innerHTML = `<div class="empty-state">No activity for this run yet.</div>`;
    return;
  }
  document.getElementById("activityTable").innerHTML = `
    <table class="activity-table">
      <thead><tr><th>Time</th><th>Level</th><th>Event</th><th>Details</th></tr></thead>
      <tbody>
        ${events.map((event) => `
          <tr>
            <td>${escapeHtml(event.time_utc || "-")}</td>
            <td><span class="small-badge ${event.level === "error" ? "bad" : event.level === "warn" ? "warn" : ""}">${escapeHtml(event.level)}</span></td>
            <td>${escapeHtml(event.source)} / ${escapeHtml(event.event)}</td>
            <td>${escapeHtml(event.details)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderRecentArtifacts() {
  const refs = state.dashboard?.recent_artifacts || [];
  document.getElementById("recentArtifacts").innerHTML = refs.length ? refs.map((ref) => `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(ref.stage)}" data-artifact-key="${escapeHtml(ref.key)}" data-artifact-kind="${escapeHtml(ref.kind)}" type="button">
      <span><strong>${escapeHtml(ref.stage)} / ${escapeHtml(ref.key)}</strong>${pathLine(ref.path)}</span>
      <span class="small-badge">${escapeHtml(ref.kind)}</span>
    </button>
  `).join("") : `<div class="empty-state">No artifacts yet.</div>`;
}

function renderBottomDock() {
  renderActivityTable();
  renderRecentArtifacts();
}

async function renderAll() {
  renderRuntimeSelector();
  renderTopbar();
  renderStageRail();
  renderStageHeader();
  renderSidebar();
  renderBottomDock();
  activateTab(state.activeTab);
  await renderCockpit();
}

async function refresh() {
  try {
    await Promise.all([fetchDashboard(), fetchReadiness()]);
    await renderAll();
  } catch (error) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function saveAnswer(questionId) {
  const textarea = document.querySelector(`[data-question-text="${CSS.escape(questionId)}"]`);
  const resolution = document.querySelector(`[data-question-resolution="${CSS.escape(questionId)}"]`);
  const text = textarea?.value?.trim() || "";
  if (!text) {
    toast("Answer text is required.");
    return false;
  }
  await postJson("/api/answers", {
    stage: state.activeStage,
    question_id: questionId,
    text,
    resolution: resolution?.value || "resolved"
  });
  toast("Answer saved.");
  return true;
}

async function startWorkflow() {
  if (!ensureRunnableRuntime()) return;
  const job = await postJson("/api/workflow/run", {runtime: state.selectedRuntime, log_follow: true});
  await startJobPolling(job);
}

async function startStage(stage = state.activeStage) {
  if (!ensureRunnableRuntime()) return;
  const payload = {stage, runtime: state.selectedRuntime, log_follow: true};
  if (state.activeRunId) payload.run_id = state.activeRunId;
  const job = await postJson("/api/stage/run", payload);
  await startJobPolling(job);
}

async function submitIntervention() {
  if (!ensureRunnableRuntime()) return;
  const textarea = document.getElementById("operatorRequestText");
  const request = textarea?.value?.trim() || "";
  if (!request) {
    toast("Request text is required.");
    return;
  }
  const targetDocuments = Array.from(document.querySelectorAll("[data-intervention-target]:checked"))
    .map((input) => input.dataset.interventionTarget)
    .filter(Boolean);
  const payload = {
    stage: state.activeStage,
    runtime: state.selectedRuntime,
    request,
    target_documents: targetDocuments,
    log_follow: true
  };
  if (state.activeRunId) payload.run_id = state.activeRunId;
  const job = await postJson("/api/stage/interact", payload);
  await startJobPolling(job);
}

async function answerAndResume(questionId) {
  const saved = await saveAnswer(questionId);
  if (!saved) return;
  await fetchDashboard();
  const unresolved = state.dashboard?.active_stage_view?.questions?.unresolved_blocking_question_ids || [];
  if (unresolved.length) {
    await renderAll();
    toast("Answer saved; remaining blocking questions must be resolved before resume.");
    return;
  }
  await startStage(state.activeStage);
}

async function openFolder(payload) {
  const result = await postJson("/api/open-folder", payload);
  toast(`Opened ${result.target} folder.`);
}

function artifactKeyForPath(path, stage) {
  const refs = state.dashboard?.recent_artifacts || [];
  const match = refs.find((ref) => ref.path === path && (!stage || ref.stage === stage));
  return match?.key || "";
}

async function inspectArtifactReference({stage, key, path, kind}) {
  const targetStage = stage || state.activeStage;
  state.activeStage = targetStage;
  state.activeArtifactKey = key || artifactKeyForPath(path, targetStage);
  state.activeTab = kind === "log" ? "logs" : "artifacts";
  await fetchDashboard();
  activateTab(state.activeTab);
  await renderAll();
}

async function stopServer() {
  const result = await postJson("/api/server/stop", {});
  document.getElementById("stopServerButton").disabled = true;
  toast(result.message || "Stopping local UI server.");
}

async function cancelActiveJob() {
  if (!state.activeJobId) return;
  const result = await postJson(`/api/jobs/${encodeURIComponent(state.activeJobId)}/cancel`, {});
  state.activeJobStatus = result;
  if (result.already_finished) {
    toast("Job already finished.");
  } else if (result.status === "cancelled") {
    toast("Job cancelled.");
  } else {
    toast("Cancel requested.");
  }
  renderActivityTable();
  if (state.activeTab === "logs") await renderLogs();
  const activeStatuses = new Set(["running", "waiting-for-operator", "cancelling"]);
  if (!state.activeJobTimer && activeStatuses.has(result.status)) {
    state.activeJobTimer = setInterval(pollActiveJob, 1000);
  }
}

async function pollActiveJob() {
  if (!state.activeJobId) return;
  try {
    const activeStatuses = new Set(["running", "waiting-for-operator", "cancelling"]);
    const logs = await api(`/api/jobs/${encodeURIComponent(state.activeJobId)}/logs?cursor=${state.activeJobCursor}`);
    state.activeJobCursor = Number(logs.cursor || state.activeJobCursor);
    state.activeJobLogChunks.push(...(logs.chunks || []));
    state.activeJobStatus = await api(`/api/jobs/${encodeURIComponent(state.activeJobId)}`);
    renderActivityTable();
    if (state.activeTab === "logs") await renderLogs();
    if (state.activeJobStatus.status === "waiting-for-operator") {
      activateTab("approvals");
      await renderApprovals();
    }
    if (!activeStatuses.has(state.activeJobStatus.status)) {
      if (state.activeJobTimer) clearInterval(state.activeJobTimer);
      state.activeJobTimer = null;
      await fetchDashboard();
      await renderAll();
    }
  } catch (error) {
    state.activeJobLogChunks.push({stream: "system", text: `[ui] ${error.message}\n`});
    if (state.activeJobTimer) clearInterval(state.activeJobTimer);
    state.activeJobTimer = null;
    renderActivityTable();
    if (state.activeTab === "logs") await renderLogs();
  }
}

async function startJobPolling(job) {
  state.activeJobId = job.job_id;
  state.activeJobCursor = 0;
  state.activeJobLogChunks = [];
  state.activeJobStatus = {job_id: job.job_id, kind: job.kind, stage: job.stage, status: "running"};
  if (state.activeJobTimer) clearInterval(state.activeJobTimer);
  activateTab("logs");
  await renderLogs();
  await pollActiveJob();
  state.activeJobTimer = setInterval(pollActiveJob, 1000);
}

async function handleNextAction() {
  const action = state.dashboard?.next_action || {action: "choose-runtime"};
  if (action.action === "choose-runtime") {
    if (state.selectedRuntime) {
      await startWorkflow();
    } else {
      document.getElementById("runtimeSelect").focus();
      toast("Select runtime first.");
    }
    return;
  }
  if (action.action === "run-workflow") {
    await startWorkflow();
    return;
  }
  if (action.action === "run-stage" || action.action === "resume-stage") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    await startStage(action.stage || state.activeStage);
    return;
  }
  if (action.action === "answer-questions") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    activateTab("questions");
    await renderCockpit();
    return;
  }
  if (action.action === "inspect-validation" || action.action === "review-intervention") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    activateTab("validation");
    await renderCockpit();
    return;
  }
  if (action.action === "review-complete") {
    activateTab("artifacts");
    await renderCockpit();
  }
}

document.addEventListener("click", async (event) => {
  try {
    const stageButton = event.target.closest("[data-stage]");
    if (stageButton) {
      state.activeStage = stageButton.dataset.stage;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
      return;
    }
    const tab = event.target.closest("[data-tab]")?.dataset.tab;
    if (tab) {
      activateTab(tab);
      await renderCockpit();
      return;
    }
    const tabShortcut = event.target.closest("[data-tab-shortcut]")?.dataset.tabShortcut;
    if (tabShortcut) {
      activateTab(tabShortcut);
      await renderCockpit();
      return;
    }
    const cancelJob = event.target.closest("[data-cancel-job]");
    if (cancelJob) {
      await cancelActiveJob();
      return;
    }
    const approvalButton = event.target.closest("[data-operator-request][data-operator-action]");
    if (approvalButton) {
      await submitApproval(approvalButton.dataset.operatorRequest, approvalButton.dataset.operatorAction);
      return;
    }
    const artifactReference = event.target.closest("[data-artifact-stage]");
    if (artifactReference) {
      await inspectArtifactReference({
        stage: artifactReference.dataset.artifactStage,
        key: artifactReference.dataset.artifactKey,
        kind: artifactReference.dataset.artifactKind
      });
      return;
    }
    const artifactKey = event.target.closest("[data-artifact-key]")?.dataset.artifactKey;
    if (artifactKey) {
      state.activeArtifactKey = artifactKey;
      await renderArtifacts();
      return;
    }
    const artifactMode = event.target.closest("[data-artifact-mode]")?.dataset.artifactMode;
    if (artifactMode) {
      state.artifactViewMode = artifactMode;
      if (state.activeArtifactKey) await loadArtifactDocument(state.activeArtifactKey);
      return;
    }
    const evidenceReference = event.target.closest("[data-evidence-path]");
    if (evidenceReference) {
      await inspectArtifactReference({
        stage: evidenceReference.dataset.evidenceStage,
        path: evidenceReference.dataset.evidencePath,
        kind: evidenceReference.dataset.evidenceKind
      });
      return;
    }
    const openArtifact = event.target.closest("[data-open-artifact]")?.dataset.openArtifact;
    if (openArtifact) {
      await openFolder({target: "artifact", path: openArtifact});
      return;
    }
    const openFolderTarget = event.target.closest("[data-open-folder]")?.dataset.openFolder;
    if (openFolderTarget === "workspace") {
      await openFolder({target: "workspace"});
      return;
    }
    const blockerReference = event.target.closest("[data-blocker-stage]");
    if (blockerReference) {
      state.activeStage = blockerReference.dataset.blockerStage;
      state.activeArtifactKey = "";
      const kind = blockerReference.dataset.blockerKind;
      state.activeTab = kind === "questions" ? "questions" : kind === "validation" ? "validation" : "overview";
      await fetchDashboard();
      await renderAll();
      return;
    }
    const saveAnswerButton = event.target.closest("[data-save-answer]");
    if (saveAnswerButton) {
      await saveAnswer(saveAnswerButton.dataset.saveAnswer);
      await fetchDashboard();
      await renderAll();
      return;
    }
    const answerResumeButton = event.target.closest("[data-answer-resume]");
    if (answerResumeButton) {
      await answerAndResume(answerResumeButton.dataset.answerResume);
      return;
    }
    if (event.target.id === "refreshButton") {
      await refresh();
      return;
    }
    if (event.target.id === "openWorkspaceButton") {
      await openFolder({target: "workspace"});
      return;
    }
    if (event.target.id === "openStageFolderButton") {
      await openFolder({target: "stage", stage: state.activeStage});
      return;
    }
    if (event.target.id === "stopServerButton") {
      await stopServer();
      return;
    }
    if (event.target.id === "nextActionButton") {
      await handleNextAction();
      return;
    }
    if (event.target.closest("[data-first-launch-run]")) {
      await startWorkflow();
      return;
    }
    if (event.target.id === "submitInterventionButton") {
      await submitIntervention();
      return;
    }
    if (event.target.id === "viewFullLogButton") {
      activateTab("logs");
      await renderCockpit();
      return;
    }
    const logFilter = event.target.closest("[data-log-filter]")?.dataset.logFilter;
    if (logFilter) {
      state.logFilter = logFilter;
      await renderLogs();
      return;
    }
    if (event.target.closest("[data-log-raw]")) {
      state.rawLogMode = !state.rawLogMode;
      await renderLogs();
    }
  } catch (error) {
    toast(error.message);
  }
});

document.addEventListener("change", async (event) => {
  if (event.target.id === "runtimeSelect") {
    state.selectedRuntime = event.target.value;
    setRunButtonState();
    updateSubmitInterventionState();
    renderTopbar();
    renderSidebar();
    if (state.activeTab === "overview") await renderCockpit();
  }
});

document.addEventListener("input", (event) => {
  if (event.target.id === "operatorRequestText") {
    updateSubmitInterventionState();
  }
});

refresh();
