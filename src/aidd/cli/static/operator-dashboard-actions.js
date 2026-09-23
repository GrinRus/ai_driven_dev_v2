function dashboardUrl({includeRunId = true} = {}) {
  const params = new URLSearchParams();
  if (state.activeStageExplicit) params.set("stage", state.activeStage);
  if (includeRunId && state.activeRunId) params.set("run_id", state.activeRunId);
  return `/api/dashboard?${params.toString()}`;
}

function projectHomeUrl(workItem = "") {
  const params = new URLSearchParams();
  if (workItem) params.set("work_item", workItem);
  const query = params.toString();
  return `/api/project-home${query ? `?${query}` : ""}`;
}

async function fetchInbox() {
  const requestGeneration = ++state.inboxRequestGeneration;
  const payload = await api("/api/inbox");
  if (requestGeneration !== state.inboxRequestGeneration) return false;
  state.inbox = payload.inbox || null;
  return true;
}

async function fetchDashboard() {
  const requestGeneration = ++state.dashboardRequestGeneration;
  state.dashboardAbortController?.abort();
  const controller = new AbortController();
  state.dashboardAbortController = controller;
  const requestedRunId = state.activeRunId;
  let recoveredFromStaleRun = false;
  let payload;
  try {
    payload = await api(dashboardUrl(), {signal: controller.signal});
  } catch (error) {
    if (controller.signal.aborted || error?.name === "AbortError") return false;
    if (error?.status !== 400 || !requestedRunId) throw error;
    state.activeRunId = "";
    recoveredFromStaleRun = true;
    payload = await api(dashboardUrl({includeRunId: false}), {signal: controller.signal});
  } finally {
    if (state.dashboardAbortController === controller) {
      state.dashboardAbortController = null;
    }
  }
  if (requestGeneration !== state.dashboardRequestGeneration) return false;
  state.dashboard = payload.dashboard;
  state.dashboardActiveJob = payload.active_job || null;
  await recoverActiveJobFromDashboard(payload.active_job);
  if (requestGeneration !== state.dashboardRequestGeneration) return false;
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
    state.activeAttempt = null;
    state.activeTaskAttempt = null;
    state.selectedTaskId = "";
    state.activeArtifactKey = "";
    state.activeArtifactWorkbench = null;
    state.activeArtifactComparison = null;
    state.activeStudioWorkbench = null;
    state.activeStudioWorkbenchError = "";
    state.selectedEvidenceNodeId = "";
    state.selectedEvidenceEdgeId = "";
    state.implementDiffPath = "";
    state.runAccountability = null;
    state.runAccountabilityError = "";
    state.runComparison = null;
    state.runComparisonRequestGeneration += 1;
    state.runComparisonError = "";
    state.runComparisonLoading = false;
    state.runComparisonBaselineInput = "";
    state.historyTimeline = null;
    state.historySelectedFrame = "";
    state.reviewFindingsView = null;
    state.reviewFindingsRunId = "";
    state.qaVerdictView = null;
    state.qaVerdictRunId = "";
    state.terminalOtherActionsIdentity = "";
    state.terminalOtherActionsOpen = false;
    state.archivePresentationIdentity = "";
    state.archivePresentationPromise = null;
  }
  if (!state.selectedRuntime && state.dashboard.run?.runtime_id) {
    state.selectedRuntime = state.dashboard.run.runtime_id;
  }
  const nextAction = state.dashboard.next_action?.action || "";
  const route = typeof decodeOperatorRoute === "function"
    ? decodeOperatorRoute(window.location.search).value
    : {view: ""};
  const explicitRecoveryRoute = route.view === "recovery"
    && state.activeTab === "recovery"
    && state.recoveryDetail === "summary";
  if (explicitRecoveryRoute && nextAction === "review-findings") {
    // A recovery deep link is an explicit request to land on the durable
    // finding surface. Do not leave the operator at the generic summary when
    // the server already knows that Review findings is the next action.
    if (state.dashboard.next_action?.stage && STAGES.includes(state.dashboard.next_action.stage)) {
      state.activeStage = state.dashboard.next_action.stage;
      state.activeStageExplicit = true;
    }
    state.activeTab = "work";
    state.workDetail = "review-findings";
    state.workItemTab = "tasks";
    requestCockpitReveal();
  } else if (
    nextAction === "qa-verdict"
    && state.dashboard?.terminal_handoff
    && state.dashboard.terminal_handoff.status === "blocked"
    && state.activeTab === "work"
  ) {
    // A terminal run with a non-ready QA report is a decision surface, not a
    // completed-flow overview. Keep the operator on the QA verdict workbench
    // so the recorded risks and remediation route are actionable.
    if (state.dashboard.next_action?.stage && STAGES.includes(state.dashboard.next_action.stage)) {
      state.activeStage = state.dashboard.next_action.stage;
      state.activeStageExplicit = true;
    }
    state.activeTab = "work";
    state.workDetail = "qa-verdict";
    state.workItemTab = "tasks";
    requestCockpitReveal();
  } else if (isRecoveryNextAction(nextAction) && (state.activeTab === "work" || explicitRecoveryRoute)) {
    state.activeTab = "recovery";
    if (state.dashboard.next_action?.stage && STAGES.includes(state.dashboard.next_action.stage)) {
      state.activeStage = state.dashboard.next_action.stage;
      state.activeStageExplicit = true;
    }
    if (nextAction === "answer-questions") state.recoveryDetail = "questions";
    else if (nextAction === "inspect-validation" || nextAction === "review-intervention") {
      state.recoveryDetail = "validation";
    } else if (nextAction === "inspect-runtime-log") state.recoveryDetail = "logs";
    requestCockpitReveal();
  } else if (
    nextAction === "resume-stage"
    && state.dashboard?.terminal_handoff
    && state.activeTab === "work"
  ) {
    // A blocked terminal handoff is not a completed handoff: keep the
    // recovery action visible in the terminal Studio workspace instead of
    // leaving the operator on a read-only Flow Complete overview. The
    // workspace renders the same bounded Resume action without changing the
    // operator's context to a separate recovery document.
    state.activeTab = "work";
    state.workDetail = "overview";
    if (state.dashboard.next_action?.stage && STAGES.includes(state.dashboard.next_action.stage)) {
      state.activeStage = state.dashboard.next_action.stage;
      state.activeStageExplicit = true;
    }
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
  if (recoveredFromStaleRun && typeof syncLocationState === "function") {
    syncLocationState({historyMode: "replace"});
  }
  return true;
}

function cancelDashboardRequest() {
  state.dashboardRequestGeneration += 1;
  state.dashboardAbortController?.abort();
  state.dashboardAbortController = null;
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
  if (workItem) {
    const requestGeneration = ++state.requestContextRequestGeneration;
    state.requestContextError = "";
    try {
      const requestPayload = await api("/api/work-item/request");
      if (requestGeneration === state.requestContextRequestGeneration) {
        state.requestContext = requestPayload.request || requestPayload;
      }
    } catch (error) {
      if (requestGeneration === state.requestContextRequestGeneration) {
        state.requestContext = null;
        state.requestContextError = error.message || "Request context unavailable.";
      }
    }
  } else {
    state.requestContext = null;
    state.requestContextError = "";
  }
  return true;
}

function setMutationControlsPending(selectors, pending) {
  document.querySelectorAll(selectors.join(",")).forEach((control) => {
    if (pending) {
      control.dataset.mutationWasDisabled = control.disabled ? "true" : "false";
      control.disabled = true;
      control.setAttribute("aria-busy", "true");
      return;
    }
    if (control.dataset.mutationWasDisabled === "false") control.disabled = false;
    delete control.dataset.mutationWasDisabled;
    control.removeAttribute("aria-busy");
  });
}

async function readRunMutationWinner() {
  await fetchDashboard();
  await fetchProjectHome(state.dashboard?.work_item || "");
  await fetchInbox();
  await renderAll();
  return {
    work_item: state.dashboard?.work_item || "",
    run_id: state.dashboard?.run?.run_id || "",
    active_stage: state.dashboard?.active_stage || "",
    next_action: state.dashboard?.next_action || null
  };
}

async function guardedJobLaunch({kind, components, controls, execute}) {
  const key = operatorMutationKey(
    kind,
    state.dashboard?.work_item || state.activeRouteWorkItem || "no-work-item",
    ...components
  );
  const guarded = await runGuardedMutation({
    key,
    execute: async () => {
      const job = await execute();
      await startJobPolling(job);
      return job;
    },
    readWinner: readRunMutationWinner,
    onState: (mutation) => setMutationControlsPending(controls, mutation.status === "pending")
  });
  if (guarded.status === "conflict") {
    toast("Another request already won. Showing the durable server state.");
    return null;
  }
  return guarded.result;
}

async function startWorkflow() {
  if (state.onboarding?.setupRequired || !state.dashboard?.work_item) {
    toast("Create or resume a Work Item before starting the workflow.");
    return;
  }
  if (!ensureRunnableRuntime()) return;
  const payload = {runtime: state.selectedRuntime, log_follow: true, ...runtimeSelectorPayload()};
  if (state.activeRunId) payload.run_id = state.activeRunId;
  await guardedJobLaunch({
    kind: "workflow-run",
    components: [state.activeRunId || "new-run"],
    controls: ["#nextActionButton", "#globalNextActionButton", "[data-first-launch-run]", '[data-guided-launch="workflow"]'],
    execute: () => postJson("/api/workflow/run", payload)
  });
}

async function startStage(
  stage = state.activeStage,
  {skipClientReadiness = false} = {}
) {
  // Resume-after-answer uses the server's authoritative, selected-Runner
  // revalidation. The recovery surface may be rendered before the scoped
  // readiness refresh completes, so a stale client snapshot must not hide the
  // action; normal launches retain the immediate client guard.
  if (!skipClientReadiness && !ensureRunnableRuntime()) return;
  const payload = {stage, runtime: state.selectedRuntime, log_follow: true, ...runtimeSelectorPayload()};
  if (state.activeRunId) payload.run_id = state.activeRunId;
  await guardedJobLaunch({
    kind: "stage-run",
    components: [state.activeRunId || "new-run", stage],
    controls: ["#nextActionButton", "#globalNextActionButton", `[data-proceed-stage="${stage}"]`, "[data-first-launch-stage]", '[data-guided-launch="stage"]', "[data-run-repair]", "[data-rerun-implement]"],
    execute: () => postJson("/api/stage/run", payload)
  });
}

async function resumeStageOrImplementationTarget(stage = state.activeStage) {
  if (stage !== "implement" || !state.activeRunId) {
    await startStage(stage);
    return;
  }
  const targetContext = {
    workItem: state.dashboard?.work_item || "",
    routeWorkItem: state.activeRouteWorkItem || "",
    runId: state.activeRunId,
    stage
  };
  const targetContextIsCurrent = () => (
    (state.dashboard?.work_item || "") === targetContext.workItem
    && (state.activeRouteWorkItem || "") === targetContext.routeWorkItem
    && state.activeRunId === targetContext.runId
    && state.activeStage === targetContext.stage
  );
  let taskView;
  try {
    taskView = await api(`/api/tasks?${runScopedQuery("implement")}`);
  } catch (error) {
    if (!targetContextIsCurrent()) return;
    toast(`Implementation recovery target unavailable: ${error.message}`);
    return;
  }
  if (!targetContextIsCurrent()) return;
  const target = typeof implementationRecoveryTarget === "function"
    ? implementationRecoveryTarget(taskView)
    : null;
  if (target?.kind === "task" && target.taskId) {
    await startImplementationTask(target.taskId);
    return;
  }
  if (target?.kind === "finalization") {
    await startTaskFinalization();
    return;
  }
  await startStage(stage);
}

async function startRepairExtension(stage = state.activeStage) {
  if (!ensureRunnableRuntime()) return;
  if (!state.activeRunId) {
    toast("No run selected.");
    return;
  }
  await guardedJobLaunch({
    kind: "repair-extension",
    components: [state.activeRunId, stage],
    controls: ["[data-repair-extension]"],
    execute: () => postJson("/api/stage/repair-extension", {
      stage,
      runtime: state.selectedRuntime,
      run_id: state.activeRunId,
      log_follow: true,
      ...runtimeSelectorPayload()
    })
  });
}

async function dispatchTaskAwareLaunch(intent, stage = state.activeStage) {
  if (intent === "workflow") return startWorkflow();
  if (intent === "stage") return startStage(stage);
  throw new Error(`Unsupported launch action: ${intent || "missing"}`);
}

async function startImplementationTask(taskId) {
  if (!ensureRunnableRuntime()) return;
  if (!state.activeRunId) {
    toast("No run selected.");
    return;
  }
  await guardedJobLaunch({
    kind: "task-run",
    components: [state.activeRunId, taskId],
    controls: [`[data-run-task="${taskId}"]`],
    execute: () => postJson("/api/tasks/run", {
      task_id: taskId,
      run_id: state.activeRunId,
      runtime: state.selectedRuntime,
      ...runtimeSelectorPayload()
    })
  });
}

async function startTaskFinalization() {
  if (!ensureRunnableRuntime()) return;
  if (!state.activeRunId) {
    toast("No run selected.");
    return;
  }
  await guardedJobLaunch({
    kind: "task-finalize",
    components: [state.activeRunId, "aggregate"],
    controls: ["[data-finalize-tasks]"],
    execute: () => postJson("/api/tasks/finalize", {
      run_id: state.activeRunId,
      runtime: state.selectedRuntime,
      ...runtimeSelectorPayload()
    })
  });
}

async function rerunStaleDownstream() {
  if (!ensureRunnableRuntime()) return;
  if (!state.activeRunId) {
    toast("No run selected.");
    return;
  }
  await guardedJobLaunch({
    kind: "remediation-rerun",
    components: [state.activeRunId, "stale-downstream"],
    controls: ["#nextActionButton", "#globalNextActionButton", '[data-recovery-action="rerun-stale-downstream"]'],
    execute: () => postJson("/api/remediation/rerun-downstream", {
      runtime: state.selectedRuntime,
      run_id: state.activeRunId,
      log_follow: true,
      ...runtimeSelectorPayload()
    })
  });
}

async function handleNextAction() {
  const action = state.dashboard?.next_action || {action: "choose-runtime"};
  const targetContext = {
    workItem: state.dashboard?.work_item || "",
    routeWorkItem: state.activeRouteWorkItem || "",
    runId: state.activeRunId || ""
  };
  const targetContextIsCurrent = () => (
    (state.dashboard?.work_item || "") === targetContext.workItem
    && (state.activeRouteWorkItem || "") === targetContext.routeWorkItem
    && (state.activeRunId || "") === targetContext.runId
  );
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
      focusRuntimeSelector();
      toast("Select runtime first.");
    }
    return;
  }
  if (action.action === "run-workflow") {
    await startWorkflow();
    return;
  }
  if (action.action === "run-stage") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      await fetchDashboard();
      if (!targetContextIsCurrent()) return;
      await renderAll();
      if (!targetContextIsCurrent()) return;
    }
    if (!targetContextIsCurrent()) return;
    await startStage(action.stage || state.activeStage);
    return;
  }
  if (action.action === "resume-stage") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      await fetchDashboard();
      if (!targetContextIsCurrent()) return;
      await renderAll();
      if (!targetContextIsCurrent()) return;
    }
    if (!targetContextIsCurrent()) return;
    await resumeStageOrImplementationTarget(action.stage || state.activeStage);
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
      if (!targetContextIsCurrent()) return;
      await renderAll();
      if (!targetContextIsCurrent()) return;
    }
    if (!targetContextIsCurrent()) return;
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
      if (!targetContextIsCurrent()) return;
      await renderAll();
      if (!targetContextIsCurrent()) return;
    }
    if (!targetContextIsCurrent()) return;
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
      if (!targetContextIsCurrent()) return;
      await renderAll();
      if (!targetContextIsCurrent()) return;
    }
    if (!targetContextIsCurrent()) return;
    activateTab(action.action);
    await renderCockpit();
    return;
  }
  if (action.action === "review-complete") {
    activateTab("artifacts");
    await renderCockpit();
    return;
  }
  if (action.action === "open-terminal-handoff") {
    activateTab("artifacts");
    await renderCockpit();
    return;
  }
  if (action.action === "open-running-job" || action.action === "wait-for-stage" || action.action === "inspect-runtime-log") {
    activateTab("logs");
    await renderCockpit();
    return;
  }
  toast(`Unsupported next action: ${action.action || "missing"}`);
}
