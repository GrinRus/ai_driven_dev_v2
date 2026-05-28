const STAGES = ["idea", "research", "plan", "review-spec", "tasklist", "implement", "review", "qa"];
const SETUP_MODES = [
  {
    id: "new-work-item",
    label: "New Work Item",
    detail: "Start without inherited run context.",
    requiresPreviousRun: false
  },
  {
    id: "follow-up-flow",
    label: "Follow-up Flow",
    detail: "Continue from source findings and final QA evidence.",
    requiresPreviousRun: true
  },
  {
    id: "clone-previous-flow",
    label: "Clone Previous Flow",
    detail: "Reuse runtime, prompt pack, contracts, branch, and baseline.",
    requiresPreviousRun: true
  },
  {
    id: "eval-scenario-batch",
    label: "Eval / Scenario Batch",
    detail: "Compare completed-run evidence across scenario executions.",
    requiresPreviousRun: true
  }
];
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

const state = {
  dashboard: null,
  readiness: null,
  readinessLoading: true,
  readinessError: "",
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
  selectedEvidenceNodeId: "",
  selectedEvidenceEdgeId: "",
  logFilter: "all",
  rawLogMode: false,
  savedLogText: "",
  setupMode: "new-work-item",
  nextFlowWizard: {
    active: false,
    action: "",
    step: "sources",
    loading: false,
    error: "",
    sourceFindings: null,
    followUpDraft: null,
    followUpDraftLoading: false,
    followUpDraftError: "",
    preflight: null,
    preflightLoading: false,
    preflightError: "",
    selectedSourceIds: []
  }
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

function sourceFindingsUrl() {
  const params = new URLSearchParams();
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  return `/api/next-flow/source-findings?${params.toString()}`;
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
  state.readinessLoading = true;
  state.readinessError = "";
  try {
    state.readiness = await api("/api/runtime-readiness");
    state.readinessError = "";
  } catch (error) {
    state.readiness = {runtimes: []};
    state.readinessError = error.message || "runtime readiness unavailable";
    toast(`Runtime readiness unavailable: ${error.message}`);
  } finally {
    state.readinessLoading = false;
  }
}
