function dashboardUrl() {
  const params = new URLSearchParams();
  if (state.activeStageExplicit) params.set("stage", state.activeStage);
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  return `/api/dashboard?${params.toString()}`;
}

function projectHomeUrl(workItem = "") {
  const params = new URLSearchParams();
  if (workItem) params.set("work_item", workItem);
  const query = params.toString();
  return `/api/project-home${query ? `?${query}` : ""}`;
}

async function fetchDashboard() {
  const requestGeneration = ++state.dashboardRequestGeneration;
  const payload = await api(dashboardUrl());
  if (requestGeneration !== state.dashboardRequestGeneration) return false;
  state.dashboard = payload.dashboard;
  await recoverActiveJobFromDashboard(payload.active_job);
  const version = String(payload.app_version || "").trim();
  document.getElementById("appVersion").textContent = version.startsWith("v")
    ? version
    : `v${version || "dev"}`;
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
    else if (nextAction === "inspect-validation" || nextAction === "review-intervention") {
      state.recoveryDetail = "validation";
    } else if (nextAction === "inspect-runtime-log") state.recoveryDetail = "logs";
    requestCockpitReveal();
  } else if (
    state.activeTab === "work"
    && state.dashboard.first_failure
    && dashboardRuntimeRecoveryAction()
  ) {
    state.activeTab = "recovery";
    state.recoveryDetail = "summary";
    requestCockpitReveal();
  }
  return true;
}

async function fetchProjectHome(workItem = "") {
  const requestGeneration = ++state.projectHomeRequestGeneration;
  const payload = await api(projectHomeUrl(workItem));
  if (requestGeneration !== state.projectHomeRequestGeneration) return false;
  state.projectHome = payload.project_home || null;
  const version = String(payload.app_version || "").trim();
  document.getElementById("appVersion").textContent = version.startsWith("v")
    ? version
    : `v${version || "dev"}`;
  return true;
}

async function startWorkflow() {
  if (state.onboarding?.setupRequired || !state.dashboard?.work_item) {
    toast("Create or resume a work item before starting the workflow.");
    return;
  }
  if (!ensureRunnableRuntime()) return;
  const payload = {runtime: state.selectedRuntime, log_follow: true};
  if (state.activeRunId) payload.run_id = state.activeRunId;
  const job = await postJson("/api/workflow/run", payload);
  await startJobPolling(job);
}

async function startStage(stage = state.activeStage) {
  if (!ensureRunnableRuntime()) return;
  const payload = {stage, runtime: state.selectedRuntime, log_follow: true};
  if (state.activeRunId) payload.run_id = state.activeRunId;
  const job = await postJson("/api/stage/run", payload);
  await startJobPolling(job);
}

async function startImplementationTask(taskId) {
  if (!ensureRunnableRuntime()) return;
  if (!state.activeRunId) {
    toast("No run selected.");
    return;
  }
  const job = await postJson("/api/tasks/run", {
    task_id: taskId,
    run_id: state.activeRunId,
    runtime: state.selectedRuntime
  });
  await startJobPolling(job);
}

async function startTaskFinalization() {
  if (!ensureRunnableRuntime()) return;
  if (!state.activeRunId) {
    toast("No run selected.");
    return;
  }
  const job = await postJson("/api/tasks/finalize", {
    run_id: state.activeRunId,
    runtime: state.selectedRuntime
  });
  await startJobPolling(job);
}

async function rerunStaleDownstream() {
  if (!ensureRunnableRuntime()) return;
  if (!state.activeRunId) {
    toast("No run selected.");
    return;
  }
  const job = await postJson("/api/remediation/rerun-downstream", {
    runtime: state.selectedRuntime,
    run_id: state.activeRunId,
    log_follow: true
  });
  await startJobPolling(job);
}

async function handleNextAction() {
  const action = state.dashboard?.next_action || {action: "choose-runtime"};
  if (activeJobBlocksNextAction(action)) {
    activateTab("logs");
    await renderCockpit();
    toast("Current job is still running. Inspect logs before starting another action.");
    return;
  }
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
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    await startStage(action.stage || state.activeStage);
    return;
  }
  if (action.action === "rerun-stale-downstream") {
    await rerunStaleDownstream();
    return;
  }
  if (action.action === "answer-questions") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeStageExplicit = true;
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
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    activateTab("validation");
    await renderCockpit();
    return;
  }
  if (action.action === "review-findings" || action.action === "qa-verdict") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    activateTab(action.action);
    await renderCockpit();
    return;
  }
  if (action.action === "review-complete") {
    activateTab("artifacts");
    await renderCockpit();
  }
}
