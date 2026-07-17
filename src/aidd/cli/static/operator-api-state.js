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
const NON_BLOCKING_VALIDATION_NOTICE_CODES = new Set([
  "STRUCT-OUTPUT-PROMOTED"
]);

const state = {
  presentationSelector: window.aiddPresentation?.requested || "legacy",
  presentationEffective: window.aiddPresentation?.effective || "legacy",
  dashboard: null,
  dashboardRequestGeneration: 0,
  projectHome: null,
  projectHomeRequestGeneration: 0,
  readiness: null,
  readinessLoading: true,
  readinessError: "",
  activeStage: "idea",
  activeStageExplicit: false,
  activeTab: "work",
  workDetail: "overview",
  recoveryDetail: "summary",
  evidenceDetail: "artifacts",
  historyDetail: "history",
  selectedRuntime: "",
  bottomDockUserCollapsed: null,
  activeRunId: "",
  activeRouteWorkItem: "",
  activeAttempt: null,
  activeTaskAttempt: null,
  activeJobId: "",
  activeJobCursor: 0,
  activeJobLogChunks: [],
  activeJobStatus: null,
  activeJobTimer: null,
  activeJobPollGeneration: 0,
  activeJobConnection: {
    state: "unknown",
    failureCount: 0,
    lastError: "",
    retryDelayMs: null,
    recovered: false
  },
  pendingCockpitReveal: false,
  pendingNextFlowWizardReveal: false,
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
    definitionErrors: [],
    createdDraft: null,
    launchLoading: false,
    launchError: "",
    launchReadinessChecking: false,
    launchReadinessError: "",
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

function isNonBlockingValidationNotice(finding) {
  return NON_BLOCKING_VALIDATION_NOTICE_CODES.has(
    String(finding?.code || "").trim().toUpperCase()
  );
}

function actionableValidationFindings(validation) {
  return (validation?.validation_findings || []).filter(
    (finding) => !isNonBlockingValidationNotice(finding)
  );
}

function nonBlockingValidationNotices(validation) {
  return (validation?.validation_findings || []).filter(isNonBlockingValidationNotice);
}

function primaryValidationFindingForValidation(validation) {
  const primary = validation?.primary_validation_finding || null;
  if (primary && !isNonBlockingValidationNotice(primary)) return primary;
  return actionableValidationFindings(validation)[0] || null;
}

function renderValidationFindingSummary(finding, {compact = false} = {}) {
  if (!finding) return "";
  const location = validationFindingLocation(finding);
  const occurrenceCount = Number(finding.occurrence_count || 1);
  const notice = isNonBlockingValidationNotice(finding);
  const repeatBadge = occurrenceCount > 1
    ? `<span class="small-badge warn">x${escapeHtml(occurrenceCount)}</span>`
    : "";
  const hint = finding.operator_hint
    ? `<span class="validation-finding-hint"><strong>What to do</strong>${escapeHtml(finding.operator_hint)}</span>`
    : "";
  return `
    <div class="validation-finding-summary ${compact ? "compact" : ""} ${notice ? "notice" : ""}">
      <span class="small-badge ${notice ? "good" : "bad"}">${escapeHtml(finding.code || "validation")}</span>
      <span class="small-badge">${escapeHtml(finding.severity || "issue")}</span>
      ${repeatBadge}
      <strong>${escapeHtml(compactPath(location, compact ? 54 : 86))}</strong>
      <span>${escapeHtml(finding.message || "Validation failed.")}</span>
      ${hint}
    </div>
  `;
}

function primaryValidationFinding() {
  const dashboardPrimary = state.dashboard?.primary_validation_finding || null;
  if (dashboardPrimary && !isNonBlockingValidationNotice(dashboardPrimary)) {
    return dashboardPrimary;
  }
  const dashboardFallback = (state.dashboard?.validation_findings || []).find(
    (finding) => !isNonBlockingValidationNotice(finding)
  );
  if (dashboardFallback) return dashboardFallback;
  return primaryValidationFindingForValidation(activeStageView()?.diagnostics?.validation);
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
  const runtimeAge = job?.runtime_output_age_seconds;
  if (runtimeAge !== null && runtimeAge !== undefined) {
    return `Last runtime output ${secondsLabel(runtimeAge)} ago`;
  }
  const hasRuntimeField = job && Object.prototype.hasOwnProperty.call(job, "runtime_output_age_seconds");
  if (!hasRuntimeField && job?.last_output_age_seconds !== null && job?.last_output_age_seconds !== undefined) {
    return `Last output ${secondsLabel(job.last_output_age_seconds)} ago`;
  }
  return "No runtime output captured yet";
}

function runtimeLogChunkCount() {
  return (state.activeJobLogChunks || []).filter((chunk) => {
    const stream = String(chunk?.stream || "stdout").toLowerCase();
    return stream !== "system";
  }).length;
}

function activeJobRuntimeLogChunkCount(job = state.activeJobStatus) {
  const reportedCount = Number(job?.runtime_log_chunk_count);
  if (Number.isFinite(reportedCount)) return reportedCount;
  return runtimeLogChunkCount();
}

function activeJobLiveLogChunkSummary(job = state.activeJobStatus) {
  const totalCount = state.activeJobLogChunks?.length || 0;
  const runtimeCount = activeJobRuntimeLogChunkCount(job);
  if (totalCount === runtimeCount) return String(totalCount);
  return `${runtimeCount} runtime / ${totalCount} total`;
}

function activeJobRuntimeSilenceAge(job = state.activeJobStatus) {
  if (job?.runtime_output_age_seconds !== null && job?.runtime_output_age_seconds !== undefined) {
    return job.runtime_output_age_seconds;
  }
  if (job?.runtime_output_at_utc === null || job?.runtime_output_at_utc === undefined) {
    return job?.elapsed_seconds;
  }
  return null;
}

function activeJobRuntimeOutputText(job = state.activeJobStatus) {
  if (job?.runtime_output_text) return job.runtime_output_text;
  if (job && !Object.prototype.hasOwnProperty.call(job, "runtime_output_text")) {
    return job.last_output_text || "";
  }
  return "";
}

function activeJobHasRuntimeOutput(job = state.activeJobStatus) {
  if (job?.runtime_output_at_utc !== null && job?.runtime_output_at_utc !== undefined) return true;
  if (job && Object.prototype.hasOwnProperty.call(job, "runtime_output_at_utc")) return false;
  return activeJobRuntimeLogChunkCount(job) > 0 || Boolean(job?.last_output_at_utc);
}

function activeJobHasNoRuntimeOutput(job = state.activeJobStatus) {
  return !activeJobHasRuntimeOutput(job) && activeJobRuntimeLogChunkCount(job) === 0;
}

function runtimeOutputMissingLabel(job = state.activeJobStatus) {
  const age = activeJobRuntimeSilenceAge(job);
  if (age !== null && age !== undefined) {
    return `No runtime output for ${secondsLabel(age)}`;
  }
  return "No runtime output captured yet";
}

function runtimeOutputMissingDetail() {
  return "System control messages may exist, but stdout/stderr runtime evidence has not arrived yet.";
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

function dashboardRuntimeRecoveryAction() {
  return (state.dashboard?.recovery_actions || []).find((action) =>
    action?.action === "inspect-runtime-log" && action.enabled !== false
  ) || null;
}

function activeModeIsEvidenceLog() {
  return state.activeTab === "evidence" && state.evidenceDetail === "logs";
}

function requestCockpitReveal() {
  state.pendingCockpitReveal = true;
}

function requestNextFlowWizardReveal() {
  state.pendingNextFlowWizardReveal = true;
}

function scrollCockpitToTopOnMobile() {
  if (!window.matchMedia("(max-width: 760px)").matches) return;
  const cockpit = document.querySelector(".cockpit");
  if (!cockpit) return;
  const topbar = document.querySelector(".topbar");
  const topbarHeight = topbar ? topbar.getBoundingClientRect().height : 0;
  const target = cockpit.getBoundingClientRect().top + window.scrollY - topbarHeight;
  window.scrollTo({top: Math.max(0, target), behavior: "auto"});
}

function revealCockpitOnMobile() {
  if (!state.pendingCockpitReveal) return;
  state.pendingCockpitReveal = false;
  scrollCockpitToTopOnMobile();
  window.requestAnimationFrame(scrollCockpitToTopOnMobile);
  window.setTimeout(scrollCockpitToTopOnMobile, 80);
}

function scrollNextFlowWizardToTopOnMobile() {
  if (!window.matchMedia("(max-width: 760px)").matches) return;
  const wizard = document.querySelector(".next-flow-wizard");
  if (!wizard) return;
  const topbar = document.querySelector(".topbar");
  const topbarHeight = topbar ? topbar.getBoundingClientRect().height : 0;
  const target = wizard.getBoundingClientRect().top + window.scrollY - topbarHeight - 8;
  window.scrollTo({top: Math.max(0, target), behavior: "auto"});
}

function revealNextFlowWizardOnMobile() {
  if (!state.pendingNextFlowWizardReveal) return;
  state.pendingNextFlowWizardReveal = false;
  scrollNextFlowWizardToTopOnMobile();
  window.requestAnimationFrame(scrollNextFlowWizardToTopOnMobile);
  window.setTimeout(scrollNextFlowWizardToTopOnMobile, 80);
}

function activeJobIsLive(job = state.activeJobStatus) {
  if (!state.activeJobId || !job) return false;
  return ["running", "waiting-for-operator", "cancelling"].includes(job.status || "running");
}

function activeJobPayloadIsLive(job) {
  if (!job?.job_id) return false;
  return ["running", "waiting-for-operator", "cancelling"].includes(job.status || "running");
}

async function recoverActiveJobFromDashboard(job) {
  if (!activeJobPayloadIsLive(job)) return;
  if (state.activeJobId === job.job_id && state.activeJobStatus) {
    state.activeJobStatus = {...state.activeJobStatus, ...job};
    return;
  }
  state.activeJobId = job.job_id;
  state.activeJobCursor = 0;
  state.activeJobLogChunks = [];
  state.activeJobStatus = job;
  clearActiveJobPollTimer();
  state.activeJobPollGeneration += 1;
  resetActiveJobConnection();
  await pollActiveJob();
}

function syncLiveJobBodyClass() {
  document.body.classList.toggle("live-job-mode", activeJobIsLive());
}

function externalRunningStageItem(action = state.dashboard?.next_action) {
  if (activeJobIsLive() || action?.action !== "wait-for-stage") return null;
  const stage = action.stage || state.activeStage;
  return (state.dashboard?.stages || []).find((item) => item.stage === stage)
    || (state.dashboard?.stages || []).find((item) => ["preparing", "executing", "validating"].includes(item.status))
    || null;
}

function syncExternalRunningBodyClass() {
  document.body.classList.toggle("external-running-stage-mode", Boolean(externalRunningStageItem()));
}

function postStageNextActionIsPrimary(action = state.dashboard?.next_action) {
  return Boolean(
    state.activeTab === "work"
    && state.workDetail === "overview"
    && state.activeRunId
    && action?.action === "run-stage"
    && action.enabled
    && !state.dashboard?.terminal_handoff
    && !activeJobIsLive()
    && !externalRunningStageItem(action)
  );
}

function applyOperatorModeBodyClass() {
  document.body.dataset.operatorMode = state.activeTab;
  const recoveryActive = state.activeTab === "recovery";
  const evidenceLogActive = activeModeIsEvidenceLog();
  const decisionDetailActive = state.activeTab === "work"
    && ["review-findings", "qa-verdict"].includes(state.workDetail);
  const staleDownstreamActive = state.dashboard?.next_action?.action === "rerun-stale-downstream"
    || (state.dashboard?.stages || []).some((item) => item.stale);
  const terminalRepairActive = Boolean(
    state.dashboard?.terminal_handoff?.repair_highlights?.length
  );
  const terminalHandoffActive = Boolean(state.dashboard?.terminal_handoff);
  const postStageNextActionActive = postStageNextActionIsPrimary();
  document.body.classList.toggle("recovery-mode", recoveryActive);
  document.body.classList.toggle("evidence-log-mode", evidenceLogActive);
  document.body.classList.toggle("decision-detail-mode", decisionDetailActive);
  document.body.classList.toggle("stale-downstream-mode", staleDownstreamActive);
  document.body.classList.toggle("terminal-handoff-mode", terminalHandoffActive);
  document.body.classList.toggle("terminal-repair-mode", terminalRepairActive);
  document.body.classList.toggle("post-stage-next-action-mode", postStageNextActionActive);
  syncLiveJobBodyClass();
  syncExternalRunningBodyClass();
}

function setRunButtonState() {
  if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
  renderNextActionPanel();
}

function activateTab(tab, {preserveDetail = false, historyMode = "replace"} = {}) {
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
  syncLocationState({historyMode});
}

function operatorRouteView() {
  if (state.activeTab === "evidence") return state.evidenceDetail === "logs" ? "logs" : "artifacts";
  if (state.activeTab === "recovery") return "recovery";
  return "overview";
}

function operatorRouteSnapshot() {
  return {
    mode: state.activeTab === "history"
      ? "history"
      : state.activeRunId || state.activeRouteWorkItem || state.dashboard?.work_item
        ? "studio"
        : "inbox",
    view: operatorRouteView(),
    workItem: state.dashboard?.work_item || state.activeRouteWorkItem || "",
    runId: state.activeRunId,
    stage: state.activeStage,
    attempt: state.activeAttempt,
    taskAttempt: state.activeTaskAttempt,
    artifact: state.activeArtifactKey
  };
}

function applyOperatorRoute(route) {
  state.activeRouteWorkItem = route.workItem || "";
  state.activeRunId = route.runId || "";
  state.activeAttempt = route.attempt;
  state.activeTaskAttempt = route.taskAttempt;
  state.activeArtifactKey = route.artifact || "";
  if (route.stage && STAGES.includes(route.stage)) {
    state.activeStage = route.stage;
    state.activeStageExplicit = true;
  }
  if (route.mode === "history") {
    setOperatorMode("history");
  } else if (route.mode === "studio" && ["logs", "artifacts"].includes(route.view)) {
    setOperatorMode(route.view);
  } else if (route.mode === "studio" && route.view === "recovery") {
    setOperatorMode("recovery");
  } else {
    setOperatorMode("work");
  }
}

function initializeStateFromLocation() {
  applyOperatorRoute(decodeOperatorRoute(window.location.search).value);
}

let restoringOperatorRoute = false;

function syncLocationState({historyMode = "replace"} = {}) {
  if (restoringOperatorRoute) return;
  const next = `${window.location.pathname}${encodeOperatorRoute(operatorRouteSnapshot())}`;
  const current = `${window.location.pathname}${window.location.search}`;
  if (next !== current) {
    const method = historyMode === "push" ? "pushState" : "replaceState";
    window.history[method]({aiddOperatorRoute: true}, "", next);
  }
}

async function restoreOperatorRouteFromLocation() {
  restoringOperatorRoute = true;
  try {
    applyOperatorRoute(decodeOperatorRoute(window.location.search).value);
    await refresh();
  } finally {
    restoringOperatorRoute = false;
  }
}

async function navigateOperatorRouteIntent(intent, context) {
  const resolved = resolveOperatorRouteIntent(intent, context);
  const next = `${window.location.pathname}${encodeOperatorRoute(resolved.route)}`;
  restoringOperatorRoute = true;
  try {
    window.history.pushState({aiddOperatorRoute: true, intent}, "", next);
    applyOperatorRoute(resolved.route);
    await refresh();
  } finally {
    restoringOperatorRoute = false;
  }
}

function sourceFindingsUrl() {
  const params = new URLSearchParams();
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  return `/api/next-flow/source-findings?${params.toString()}`;
}

function operatorDraftIdentity(form, sourceId) {
  return {
    project: String(
      state.dashboard?.project_root
      || state.projectHome?.project_root
      || state.onboarding.projectRootInput
      || "none"
    ),
    workItem: String(state.dashboard?.work_item || state.activeRouteWorkItem || "none"),
    run: String(state.activeRunId || "none"),
    stage: String(state.activeStage || "none"),
    form,
    sourceId: String(sourceId || "none")
  };
}

function currentOperatorDraftProject() {
  return operatorDraftIdentity("question", "current-project").project;
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
