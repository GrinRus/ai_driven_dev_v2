const STAGES = ["idea", "research", "plan", "review-spec", "tasklist", "implement", "review", "qa"];
const VALID_TABS = [
  "project-home",
  "overview",
  "questions",
  "validation",
  "timeline",
  "artifacts",
  "recovery",
  "implement-review",
  "review-findings",
  "qa-verdict",
  "logs",
  "approvals",
  "request",
  "history"
];
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
  projectHome: null,
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
  runAccountability: null,
  runAccountabilityError: "",
  runComparison: null,
  runComparisonError: "",
  runComparisonLoading: false,
  runComparisonBaselineInput: "",
  activeArtifactKey: "",
  implementDiffFilter: "all",
  implementDiffPath: "",
  artifactViewMode: "preview",
  selectedEvidenceNodeId: "",
  selectedEvidenceEdgeId: "",
  logFilter: "all",
  logViewMode: "summary",
  rawLogMode: false,
  savedLogText: "",
  setupMode: "new-work-item",
  onboarding: {
    setupRequired: false,
    loading: true,
    error: "",
    projectRootInput: ".",
    project: null,
    configPath: "",
    recentProjects: [],
    inspecting: false,
    inspectError: "",
    workItemInput: "",
    requestText: "",
    forceContext: false,
    projectSetText: "",
    projectSetRows: [{id: "", root: "", role: ""}],
    projectSetResult: null,
    projectSetError: "",
    projectSetLoading: false,
    createError: "",
    creating: false
  },
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
    createdDraft: null,
    launchLoading: false,
    launchError: "",
    archiveRunId: "",
    archiveReason: "",
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
  return ["run-workflow", "run-stage", "resume-stage", "rerun-stale-downstream"].includes(action);
}

function setRunButtonState() {
  if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
  renderNextActionPanel();
}

function activateTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll("[data-tab]").forEach((button) => {
    const isActive = button.dataset.tab === tab;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.setAttribute("tabindex", isActive ? "0" : "-1");
  });
  const content = document.getElementById("cockpitContent");
  if (content) content.setAttribute("aria-labelledby", `tab-${tab}`);
  syncLocationState();
}

function initializeStateFromLocation() {
  const params = new URLSearchParams(window.location.search);
  const requestedStage = params.get("stage");
  if (requestedStage && STAGES.includes(requestedStage)) {
    state.activeStage = requestedStage;
  }
  const requestedRunId = String(params.get("run_id") || "").trim();
  if (requestedRunId) {
    state.activeRunId = requestedRunId;
  }
  const requestedTab = params.get("tab");
  if (requestedTab && VALID_TABS.includes(requestedTab)) {
    state.activeTab = requestedTab;
  }
}

function syncLocationState() {
  const params = new URLSearchParams(window.location.search);
  params.set("stage", state.activeStage);
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  else params.delete("run_id");
  if (state.activeTab && state.activeTab !== "overview") params.set("tab", state.activeTab);
  else params.delete("tab");
  const query = params.toString();
  const next = `${window.location.pathname}${query ? `?${query}` : ""}`;
  const current = `${window.location.pathname}${window.location.search}`;
  if (next !== current) {
    window.history.replaceState(null, "", next);
  }
}

function dashboardUrl() {
  const params = new URLSearchParams({stage: state.activeStage});
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  return `/api/dashboard?${params.toString()}`;
}

function projectHomeUrl(workItem = "") {
  const params = new URLSearchParams();
  if (workItem) params.set("work_item", workItem);
  const query = params.toString();
  return `/api/project-home${query ? `?${query}` : ""}`;
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
  const viewedStage = state.dashboard.active_stage_view?.stage || state.dashboard.active_stage;
  if (viewedStage && STAGES.includes(viewedStage)) {
    state.activeStage = viewedStage;
  }
  state.activeRunId = state.dashboard.run?.run_id || "";
  if (!state.selectedRuntime && state.dashboard.run?.runtime_id) {
    state.selectedRuntime = state.dashboard.run.runtime_id;
  }
}

async function fetchProjectHome(workItem = "") {
  const payload = await api(projectHomeUrl(workItem));
  state.projectHome = payload.project_home || null;
  const version = String(payload.app_version || "").trim();
  document.getElementById("appVersion").textContent = version.startsWith("v") ? version : `v${version || "dev"}`;
}

async function fetchOnboardingState() {
  state.onboarding.loading = true;
  state.onboarding.error = "";
  try {
    const payload = await api("/api/onboarding/state");
    state.onboarding.setupRequired = Boolean(payload.setup_required);
    state.onboarding.recentProjects = payload.recent_projects || [];
    const context = payload.context || null;
    if (context) {
      state.onboarding.projectRootInput = context.project_root || state.onboarding.projectRootInput;
      state.onboarding.workItemInput = context.work_item || state.onboarding.workItemInput;
      state.onboarding.configPath = context.config || state.onboarding.configPath;
    }
    const version = String(payload.app_version || "").trim();
    document.getElementById("appVersion").textContent = version.startsWith("v") ? version : `v${version || "dev"}`;
  } catch (error) {
    state.onboarding.error = error.message || "setup state unavailable";
    state.onboarding.setupRequired = true;
  } finally {
    state.onboarding.loading = false;
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
