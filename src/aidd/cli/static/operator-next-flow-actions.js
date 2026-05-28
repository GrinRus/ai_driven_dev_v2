function setupPreviousRunContext() {
  const dashboard = state.dashboard || {};
  const run = dashboard.run || {};
  const lineage = run.lineage || {};
  const handoff = dashboard.terminal_handoff || null;
  const sourceRunId = lineage.source_run_id || (handoff && run.run_id ? run.run_id : "");
  const sourceWorkItem = lineage.source_work_item_id || (sourceRunId ? dashboard.work_item : "");
  const baseline = lineage.baseline_label || lineage.baseline_id || "";
  const finalArtifacts = handoff?.final_artifacts || [];
  const blockers = handoff?.blockers || [];
  const approvalCounts = handoff?.approval_counts || null;
  return {
    available: Boolean(sourceRunId || baseline || finalArtifacts.length || blockers.length),
    sourceRunId,
    sourceWorkItem,
    baseline,
    finalArtifacts,
    blockers,
    approvalCounts
  };
}

function setupModeView(context = null) {
  const mode = SETUP_MODES.find((candidate) => candidate.id === state.setupMode) || SETUP_MODES[0];
  if (context && mode.requiresPreviousRun && !context.available) return SETUP_MODES[0];
  return mode;
}

function renderSetupModeSelector(context) {
  const activeMode = setupModeView(context);
  return `
    <div class="setup-mode-grid" role="radiogroup" aria-label="Execution mode">
      ${SETUP_MODES.map((mode) => {
        const selected = mode.id === activeMode.id;
        const blocked = mode.requiresPreviousRun && !context.available;
        return `
          <button
            class="setup-mode-card${selected ? " selected" : ""}"
            data-setup-mode="${escapeHtml(mode.id)}"
            type="button"
            role="radio"
            aria-checked="${selected ? "true" : "false"}"
            ${blocked ? 'aria-disabled="true" disabled' : ""}
          >
            <strong>${escapeHtml(mode.label)}</strong>
            <span>${escapeHtml(mode.detail)}</span>
            <em>${blocked ? "needs previous run" : selected ? "selected" : "available"}</em>
          </button>
        `;
      }).join("")}
    </div>
  `;
}

function renderPreviousRunContext(context) {
  if (!context.available) {
    return `
      <div class="empty-state previous-run-context">
        No previous-run context selected for this workspace.
      </div>
    `;
  }
  const artifacts = context.finalArtifacts.slice(0, 4).map((artifact) => `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(artifact.stage)}" data-artifact-key="${escapeHtml(artifact.key)}" data-artifact-kind="${escapeHtml(artifact.kind)}" type="button">
      <span><strong>${escapeHtml(artifact.key)}</strong>${pathLine(artifact.path)}</span>
      <span class="small-badge">${escapeHtml(artifact.kind)}</span>
    </button>
  `).join("");
  const approvals = context.approvalCounts
    ? `${context.approvalCounts.approved}/${context.approvalCounts.requested} approved`
    : "not recorded";
  return `
    <div class="previous-run-context">
      <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(context.sourceRunId || "not recorded")}</span></div>
      <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(context.sourceWorkItem || "not recorded")}</span></div>
      <div class="panel-item"><strong>Baseline</strong><span>${escapeHtml(context.baseline || "source run")}</span></div>
      <div class="panel-item"><strong>Approval evidence</strong><span>${escapeHtml(approvals)}</span></div>
      <div class="panel-item"><strong>Blockers</strong><span>${escapeHtml(context.blockers.length)}</span></div>
      <div class="recent-artifacts">${artifacts || '<div class="empty-state">No final artifacts recorded.</div>'}</div>
    </div>
  `;
}

function renderFirstLaunchState() {
  const runtime = selectedRuntimeView();
  const ready = selectedRuntimeReady();
  const context = setupPreviousRunContext();
  const mode = setupModeView(context);
  const detail = !state.selectedRuntime
    ? "Select a runtime to start the first governed workflow run."
    : ready
      ? `${state.selectedRuntime} is ready to start the workflow.`
      : `${state.selectedRuntime} needs a passing readiness check before the first run.`;
  return `
    <section class="surface first-launch-state project-setup-state">
      <div class="surface-title">
        <span>Project Setup</span>
        <span class="small-badge">${escapeHtml(mode.label)}</span>
      </div>
      <div class="project-setup-grid">
        <div class="setup-primary">
          <p>${escapeHtml(detail)}</p>
          ${renderSetupModeSelector(context)}
          <div class="setup-actions">
            <button data-first-launch-run type="button" ${ready && runtime ? "" : "disabled"}>Run workflow</button>
            <span class="muted">Work item ${escapeHtml(state.dashboard?.work_item || "unknown")}</span>
          </div>
        </div>
        <aside class="setup-context" aria-label="Previous-run context">
          <div class="surface-title">
            <span>Previous-run context</span>
            <span class="small-badge ${context.available ? "good" : ""}">${context.available ? "available" : "none"}</span>
          </div>
          ${renderPreviousRunContext(context)}
        </aside>
      </div>
    </section>
  `;
}

function renderNextActionPanel() {
  const action = state.dashboard?.next_action || {action: "choose-runtime", label: "Select runtime", detail: "Choose a runtime.", enabled: false};
  const noRunWithRuntime = action.action === "choose-runtime" && state.selectedRuntime;
  const runStageResume = action.action === "run-stage" && state.activeRunId && action.enabled;
  const runtimeNeeded = needsRuntime(action.action) || noRunWithRuntime;
  const runtimeBlocked = runtimeNeeded && (!state.selectedRuntime || !selectedRuntimeReady());
  const disabled = !(action.enabled || noRunWithRuntime) || runtimeBlocked;
  const label = noRunWithRuntime
    ? (state.activeRunId ? "Resume workflow" : "Run workflow")
    : runStageResume
      ? `Continue with ${stageTitle(action.stage || state.activeStage)}`
      : action.label;
  const detail = runtimeBlocked && state.selectedRuntime
    ? `${action.detail} ${state.readinessLoading ? "Checking runtime readiness." : "Selected runtime is not ready."}`
    : action.detail;
  document.getElementById("nextActionPanel").innerHTML = `
    <div class="panel-title">Next action</div>
    <p>${escapeHtml(detail)}</p>
    <button id="nextActionButton" class="next-button" data-next-action="${escapeHtml(action.action)}" type="button" ${disabled ? "disabled" : ""}>${escapeHtml(label)}</button>
  `;
}

async function startWorkflow() {
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
