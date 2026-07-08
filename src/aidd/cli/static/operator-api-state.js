const STAGES = ["idea", "research", "plan", "review-spec", "tasklist", "implement", "review", "qa"];
const OPERATOR_MODES = [
  "work",
  "recovery",
  "evidence",
  "history"
];
const LEGACY_TAB_TO_MODE = {
  "project-home": ["work", "project-home"],
  "overview": ["work", "overview"],
  "implement-review": ["work", "implement-review"],
  "review-findings": ["work", "review-findings"],
  "qa-verdict": ["work", "qa-verdict"],
  "questions": ["recovery", "questions"],
  "validation": ["recovery", "validation"],
  "approvals": ["recovery", "approvals"],
  "request": ["recovery", "request"],
  "recovery": ["recovery", "summary"],
  "artifacts": ["evidence", "artifacts"],
  "logs": ["evidence", "logs"],
  "timeline": ["history", "timeline"],
  "history": ["history", "history"]
};
const VALID_TABS = [
  ...OPERATOR_MODES,
  ...Object.keys(LEGACY_TAB_TO_MODE)
];
const RECOVERY_NEXT_ACTIONS = new Set([
  "answer-questions",
  "inspect-validation",
  "review-intervention",
  "inspect-runtime-log"
]);
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
  activeTab: "work",
  workDetail: "overview",
  recoveryDetail: "summary",
  evidenceDetail: "artifacts",
  historyDetail: "history",
  selectedRuntime: "",
  bottomDockUserCollapsed: null,
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
  reviewFindingsView: null,
  reviewFindingsRunId: "",
  qaVerdictView: null,
  qaVerdictRunId: "",
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

function validationFindingLocation(finding) {
  if (!finding) return "unknown location";
  const path = finding.path || "unknown location";
  return finding.line_number ? `${path}:${finding.line_number}` : path;
}

function renderValidationFindingSummary(finding, {compact = false} = {}) {
  if (!finding) return "";
  const location = validationFindingLocation(finding);
  const occurrenceCount = Number(finding.occurrence_count || 1);
  const repeatBadge = occurrenceCount > 1
    ? `<span class="small-badge warn">x${escapeHtml(occurrenceCount)}</span>`
    : "";
  const hint = finding.operator_hint
    ? `<span class="validation-finding-hint"><strong>What to do</strong>${escapeHtml(finding.operator_hint)}</span>`
    : "";
  return `
    <div class="validation-finding-summary ${compact ? "compact" : ""}">
      <span class="small-badge bad">${escapeHtml(finding.code || "validation")}</span>
      <span class="small-badge">${escapeHtml(finding.severity || "issue")}</span>
      ${repeatBadge}
      <strong>${escapeHtml(compactPath(location, compact ? 54 : 86))}</strong>
      <span>${escapeHtml(finding.message || "Validation failed.")}</span>
      ${hint}
    </div>
  `;
}

function primaryValidationFinding() {
  return state.dashboard?.primary_validation_finding
    || activeStageView()?.diagnostics?.validation?.primary_validation_finding
    || null;
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

function secondsLabel(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "not available";
  const seconds = Math.max(0, Number(value));
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.floor(seconds % 60);
  if (minutes < 60) return `${minutes}m ${remainder}s`;
  const hours = Math.floor(minutes / 60);
  return `${hours}h ${minutes % 60}m`;
}

function runtimeOutputFreshnessLabel(job) {
  if (job?.last_output_age_seconds === null || job?.last_output_age_seconds === undefined) {
    return "No runtime output captured yet";
  }
  return `Last output ${secondsLabel(job.last_output_age_seconds)} ago`;
}

function activeStageItem() {
  return (state.dashboard?.stages || []).find((item) => item.stage === state.activeStage) || null;
}

function activeStageView() {
  return state.dashboard?.active_stage_view || null;
}

function stageRetrySummary(item) {
  const attemptCount = Number(item?.attempt_count || 0);
  if (attemptCount <= 1) return null;
  const retryCount = attemptCount - 1;
  const retryLabel = retryCount === 1 ? "1 retry" : `${retryCount} retries`;
  return {
    attemptCount,
    retryCount,
    label: `retry ${attemptCount}x`,
    title: `${retryLabel} after the first attempt; open Recovery for repair and retry history`
  };
}

function needsRuntime(action) {
  return ["run-workflow", "run-stage", "resume-stage", "rerun-stale-downstream"].includes(action);
}

function normalizeOperatorMode(tab) {
  const requested = String(tab || "work");
  if (OPERATOR_MODES.includes(requested)) {
    return {
      mode: requested,
      detail: requested === "work"
        ? "overview"
        : requested === "recovery"
          ? "summary"
          : requested === "evidence"
            ? "artifacts"
            : "history"
    };
  }
  const legacy = LEGACY_TAB_TO_MODE[requested];
  if (legacy) return {mode: legacy[0], detail: legacy[1]};
  return {mode: "work", detail: "overview"};
}

function setOperatorMode(tab) {
  const normalized = normalizeOperatorMode(tab);
  state.activeTab = normalized.mode;
  if (normalized.mode === "work") state.workDetail = normalized.detail;
  if (normalized.mode === "recovery") state.recoveryDetail = normalized.detail;
  if (normalized.mode === "evidence") state.evidenceDetail = normalized.detail;
  if (normalized.mode === "history") state.historyDetail = normalized.detail;
}

function isRecoveryNextAction(action) {
  return RECOVERY_NEXT_ACTIONS.has(String(action || ""));
}

function activeModeIsEvidenceLog() {
  return state.activeTab === "evidence" && state.evidenceDetail === "logs";
}

function activeJobIsLive(job = state.activeJobStatus) {
  if (!state.activeJobId || !job) return false;
  return ["running", "waiting-for-operator", "cancelling"].includes(job.status || "running");
}

function syncLiveJobBodyClass() {
  document.body.classList.toggle("live-job-mode", activeJobIsLive());
}

function applyOperatorModeBodyClass() {
  document.body.dataset.operatorMode = state.activeTab;
  const recoveryActive = state.activeTab === "recovery";
  const decisionDetailActive = state.activeTab === "work"
    && ["review-findings", "qa-verdict"].includes(state.workDetail);
  document.body.classList.toggle("recovery-mode", recoveryActive);
  document.body.classList.toggle("decision-detail-mode", decisionDetailActive);
  syncLiveJobBodyClass();
}

function setRunButtonState() {
  if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
  renderNextActionPanel();
}

function activateTab(tab, {preserveDetail = false} = {}) {
  const requested = String(tab || "work");
  if (!(preserveDetail && OPERATOR_MODES.includes(requested) && state.activeTab === requested)) {
    setOperatorMode(requested);
  }
  document.querySelectorAll("[data-tab]").forEach((button) => {
    const isActive = button.dataset.tab === state.activeTab;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
    button.setAttribute("tabindex", isActive ? "0" : "-1");
  });
  const content = document.getElementById("cockpitContent");
  if (content) content.setAttribute("aria-labelledby", `tab-${state.activeTab}`);
  applyOperatorModeBodyClass();
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
    setOperatorMode(requestedTab);
  }
}

function syncLocationState() {
  const params = new URLSearchParams(window.location.search);
  params.set("stage", state.activeStage);
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  else params.delete("run_id");
  if (state.activeTab && state.activeTab !== "work") params.set("tab", state.activeTab);
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
  const previousRunId = state.activeRunId;
  state.activeRunId = state.dashboard.run?.run_id || "";
  if (state.activeRunId !== previousRunId) {
    state.reviewFindingsView = null;
    state.reviewFindingsRunId = "";
    state.qaVerdictView = null;
    state.qaVerdictRunId = "";
  }
  if (!state.selectedRuntime && state.dashboard.run?.runtime_id) {
    state.selectedRuntime = state.dashboard.run.runtime_id;
  }
  const nextAction = state.dashboard.next_action?.action || "";
  if (isRecoveryNextAction(nextAction) && state.activeTab === "work") {
    state.activeTab = "recovery";
    if (nextAction === "answer-questions") state.recoveryDetail = "questions";
    else if (nextAction === "inspect-validation" || nextAction === "review-intervention") state.recoveryDetail = "validation";
    else if (nextAction === "inspect-runtime-log") state.recoveryDetail = "logs";
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
