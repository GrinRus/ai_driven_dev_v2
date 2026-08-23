function activeStudioState() {
  if (!state.dashboard?.run?.run_id) return "no-run";
  if (state.dashboard?.terminal_handoff) return "terminal";
  const active = activeStageItem();
  if (["blocked", "failed", "cancelled"].includes(active?.status)) return "blocked";
  return active?.status === "executing" ? "active" : "stage";
}

function activeStudioStateLabel(studioState, item) {
  return {
    "no-run": "Ready for first launch",
    active: "Stage running",
    blocked: "Decision required",
    terminal: "Terminal evidence available",
    stage: item?.status || "Stage selected"
  }[studioState];
}

const INTENT_PHASES = Object.freeze([
  Object.freeze({id: "understand", label: "Understand", stages: ["idea", "research"]}),
  Object.freeze({id: "decide", label: "Decide", stages: ["plan", "review-spec"]}),
  Object.freeze({id: "deliver", label: "Deliver", stages: ["tasklist", "implement"]}),
  Object.freeze({id: "prove", label: "Prove", stages: ["review", "qa"]})
]);

function activeIntentSummary() {
  const workItem = state.dashboard?.work_item || state.activeRouteWorkItem || "";
  return state.projectHome?.selected_work_item_resume?.intent
    || (state.projectHome?.work_items || []).find((item) => item.work_item === workItem)?.intent
    || null;
}

function phaseStatus(phase, stages) {
  const items = phase.stages.map((stage) => stages.find((item) => item.stage === stage)).filter(Boolean);
  if (!items.length) return "pending";
  if (items.some((item) => ["blocked", "failed", "cancelled"].includes(item.status))) return "blocked";
  if (items.some((item) => ["preparing", "executing", "validating"].includes(item.status))) return "active";
  if (items.every((item) => item.status === "succeeded")) return "complete";
  if (items.some((item) => item.status !== "pending")) return "ready";
  return "pending";
}

function phaseFocusStage(phase, stages) {
  const active = phase.stages.find((stage) => stage === state.activeStage);
  if (active) return active;
  const current = [...phase.stages].reverse().find((stage) => {
    const item = stages.find((candidate) => candidate.stage === stage);
    return item && item.status !== "pending";
  });
  return current || phase.stages[0];
}

function renderIntentPhaseStepper() {
  const stages = state.dashboard?.stages || [];
  let stageNumber = 0;
  return `
    <section class="surface intent-phase-stepper canonical-stage-strip" data-intent-phase-stepper aria-label="Work Item delivery stages">
      <div class="surface-title"><span>Delivery path</span><span class="small-badge">8 stages</span></div>
      <div class="canonical-stage-groups">
        ${INTENT_PHASES.map((phase) => `
          <section class="canonical-stage-group" data-stage-group="${escapeHtml(phase.id)}" aria-label="${escapeHtml(phase.label)} stages">
            <h3>${escapeHtml(phase.label)}</h3>
            <ol class="intent-phase-list">
              ${phase.stages.map((stage) => {
                stageNumber += 1;
                const item = stages.find((candidate) => candidate.stage === stage);
                const status = item?.status || "pending";
                const stale = Boolean(item?.stale);
                const statusLabel = stale ? `${status} · stale` : status;
                const current = stage === state.activeStage;
                const selectable = current || status !== "pending";
                const label = `${stageTitle(stage)} — ${statusLabel}`;
                return `
                  <li>
                    <button class="intent-phase-step canonical-stage-step ${escapeHtml(String(status).toLowerCase().replace(/_/g, "-"))}${stale ? " stale" : ""}${current ? " active" : ""}" data-stage="${escapeHtml(stage)}" data-canonical-stage="${escapeHtml(stage)}" data-stage-stale="${stale ? "true" : "false"}" type="button" aria-current="${current ? "step" : "false"}" aria-label="${escapeHtml(label)}" ${selectable ? "" : "disabled"}>
                      <span class="intent-phase-index">${stageNumber}</span>
                      <span><strong>${escapeHtml(stageTitle(stage))}</strong><small>${escapeHtml(statusLabel)}</small></span>
                    </button>
                  </li>
                `;
              }).join("")}
            </ol>
          </section>
        `).join("")}
      </div>
    </section>
  `;
}

function renderActiveStudioContextBar(studioState, item) {
  const dashboard = state.dashboard || {};
  const intent = activeIntentSummary();
  const intentExcerpt = intent?.excerpt || "Capture the desired outcome before starting delivery.";
  const currentPhase = INTENT_PHASES.find((phase) => phase.stages.includes(state.activeStage));
  return `
    <header class="surface studio-context-bar" data-studio-context-bar>
      <div>
        <p class="eyebrow">Work Item Workspace</p>
        <h2>${escapeHtml(intentExcerpt)}</h2>
        <p class="muted">${escapeHtml(currentPhase?.label || "Capture")} · ${escapeHtml(activeStudioStateLabel(studioState, item))}</p>
      </div>
      <dl class="studio-context-identity">
        <div><dt>Current status</dt><dd>${escapeHtml(activeStudioStateLabel(studioState, item))}</dd></div>
      </dl>
    </header>
  `;
}

function renderActiveStudioDocumentSlot(studioState) {
  if (studioState === "no-run") {
    return renderStateSurface({
      kind: "studio-document",
      state: "empty",
      title: "No run evidence yet",
      consequence: "Use the single decision above to select a runtime or start the governed flow."
    });
  }
  return `
    <section class="surface studio-document-canvas" data-studio-document-slot>
      <div class="surface-title"><span>Document Canvas</span><span class="small-badge">${escapeHtml(state.activeStage)}</span></div>
      <div id="studioDocumentCanvas" class="artifact-viewer" aria-live="polite">
        <div class="empty-state loading-state">Loading bounded document view...</div>
      </div>
    </section>
  `;
}

function renderWorkItemTabPlaceholder(tab) {
  const item = activeStageItem();
  const studioState = activeStudioState();
  const title = WORK_ITEM_TAB_LABELS[tab] || tab;
  const copy = tab === "tasks"
    ? "Task Workspace is the next surface in the Work Item flow. Its dependency-aware ledger will appear here without changing the canonical stage or run state."
    : "Run history will appear here with retained attempts and lineage. Existing History routes remain available while this Work Item surface is introduced.";
  return `
    <section class="active-studio" data-studio-surface="active-studio" data-state="${escapeHtml(studioState)}" data-work-item-tab-surface="${escapeHtml(tab)}">
      ${renderActiveStudioContextBar(studioState, item)}
      ${renderIntentPhaseStepper()}
      <section class="surface work-item-tab-placeholder" data-work-item-placeholder="${escapeHtml(tab)}">
        <p class="eyebrow">Work Item / ${escapeHtml(title)}</p>
        <h2>${escapeHtml(title)}</h2>
        <p>${escapeHtml(copy)}</p>
      </section>
    </section>
  `;
}

async function renderWorkItemRuns() {
  const content = document.getElementById("intentContent");
  content.innerHTML = `<section class="surface" data-work-item-runs><div class="empty-state loading-state">Loading retained runs...</div></section>`;
  try {
    await loadStudioHistoryTimeline();
    content.innerHTML = renderStudioHistory(state.historyTimeline);
    if (typeof loadRunComparisonPanel === "function") void loadRunComparisonPanel();
  } catch (error) {
    content.innerHTML = `<section class="surface" data-work-item-runs><div class="empty-state bad">${escapeHtml(error.message || "Run history unavailable")}</div></section>`;
  }
}

function renderTaskWorkspace(taskView) {
  const allTasks = taskView?.task_list || [];
  const filter = String(state.taskWorkspaceFilter || "").trim().toLowerCase();
  const visible = allTasks.filter((task) => !filter
    || String(task.id || "").toLowerCase().includes(filter)
    || String(task.title || "").toLowerCase().includes(filter));
  const groups = ["Ready", "Running", "Blocked", "Done"];
  const selected = taskView?.selected_task || null;
  const actionProjection = selected?.action_projection || taskView?.selected_task_actions || null;
  const actionStates = actionProjection?.states || {};
  const actionName = actionProjection?.recommended || actionProjection?.core_recommended || null;
  const actionState = actionName ? actionStates[actionName] || null : null;
  const actionLabel = actionName === "run"
    ? "Run"
    : actionName === "resume"
      ? "Resume"
      : actionName === "finalize"
        ? "Finalize"
        : "No action available";
  const actionReason = actionState?.disabled_reason
    || (actionName ? "This task action is not currently eligible." : "No task action is currently eligible.");
  const activeJob = state.activeJobStatus;
  const activeTaskJob = activeJob && ["task", "task-finalize"].includes(activeJob.kind);
  const attempts = selected?.attempts || [];
  const latestAttempt = attempts.length ? attempts[attempts.length - 1] : null;
  const attemptIdentity = activeTaskJob
    ? (activeJob.attempt_path || activeJob.job_id || "active attempt")
    : (latestAttempt?.path || "not available");
  const attemptStatus = activeTaskJob ? activeJob.status : (latestAttempt?.status || "not started");
  const attemptElapsed = activeTaskJob && activeJob.elapsed_seconds !== undefined
    ? secondsLabel(activeJob.elapsed_seconds)
    : "not available";
  const attemptOutputAge = activeTaskJob
    ? runtimeOutputFreshnessLabel(activeJob)
    : (latestAttempt ? "Persisted runtime evidence available" : "No output evidence recorded");
  const attemptMilestone = activeTaskJob
    ? (activeJob.message || `${selected?.status || "task"} / ${attemptStatus}`)
    : (latestAttempt ? `${selected?.status || "recorded"} / attempt ${latestAttempt.number}` : "No durable milestone");
  const attemptConnection = activeTaskJob
    ? (state.activeJobConnection?.state || "unknown")
    : "durable";
  const rawOutput = activeTaskJob ? rawTextFromEntries(logEntriesFromChunks(state.activeJobLogChunks || [])) : "";
  const scopePaths = Array.isArray(selected?.scope_paths) ? selected.scope_paths : [];
  const acceptanceCriteria = Array.isArray(selected?.acceptance_criteria)
    ? selected.acceptance_criteria
    : [];
  const evidenceLinks = Array.isArray(selected?.evidence_links) ? selected.evidence_links : [];
  const attemptsMarkup = attempts.length
    ? `<ul class="task-contract-list">${attempts.map((attempt) => `
        <li><strong>Attempt ${escapeHtml(attempt.number || "?")}</strong><span>${escapeHtml(attempt.status || "unknown")}</span><code>${escapeHtml(attempt.path || "not recorded")}</code></li>
      `).join("")}</ul>`
    : `<p class="muted">No durable attempts recorded.</p>`;
  const acceptanceMarkup = acceptanceCriteria.length
    ? `<ul class="task-contract-list">${acceptanceCriteria.map((criterion) => `
        <li><strong>${escapeHtml(criterion.id || "criterion")}</strong><span>${escapeHtml(criterion.text || "")}</span></li>
      `).join("")}</ul>`
    : `<p class="muted">No acceptance criteria recorded.</p>`;
  const evidenceMarkup = evidenceLinks.length
    ? `<ul class="task-contract-list">${evidenceLinks.map((link) => `<li><code>${escapeHtml(link)}</code></li>`).join("")}</ul>`
    : `<p class="muted">No evidence links recorded.</p>`;
  const actionButton = actionName
    ? `<button data-task-action="${escapeHtml(actionName)}"${actionName === "run" || actionName === "resume" ? ` data-task-action-id="${escapeHtml(selected.id)}"` : ""} type="button" ${actionState?.eligible === true ? "" : "disabled aria-disabled=\"true\""}>${escapeHtml(actionLabel)}</button>`
    : "";
  return `
    <section class="active-studio" data-studio-surface="task-workspace" data-state="ready">
      ${renderActiveStudioContextBar(activeStudioState(), activeStageItem())}
      ${renderIntentPhaseStepper()}
      <section class="surface task-workspace" data-task-workspace>
        <div class="surface-title"><span>Task Workspace</span><span class="small-badge">${escapeHtml(allTasks.length)} tasks</span></div>
        <p class="muted">Groups, order, readiness, and next task are authoritative from the core ledger.</p>
        <label class="task-workspace-filter">Search tasks
          <input data-task-filter type="search" value="${escapeHtml(state.taskWorkspaceFilter)}" placeholder="Task id or title" autocomplete="off">
        </label>
        <div class="task-workspace-meta">
          <span>Next ready: <strong>${escapeHtml(taskView?.next_ready_task || "none")}</strong></span>
          <span>Critical path: <strong>${escapeHtml((taskView?.critical_path || []).join(" → ") || "none")}</strong></span>
        </div>
        <div class="task-workspace-groups">
          ${groups.map((group) => {
            const tasks = visible.filter((task) => task.group === group);
            return `<section class="task-workspace-group" data-task-group="${group}">
              <div class="surface-title compact"><h3>${group}</h3><span class="small-badge">${tasks.length}</span></div>
              ${tasks.length ? `<div class="compact-list">${tasks.map((task) => `
                <button class="panel-item task-workspace-item${task.id === state.selectedTaskId ? " selected" : ""}" data-task-select="${escapeHtml(task.id)}" type="button" aria-pressed="${task.id === state.selectedTaskId ? "true" : "false"}">
                  <strong>${escapeHtml(task.id)} · ${escapeHtml(task.title || "Untitled task")}</strong>
                  <span>${escapeHtml(task.status || "unknown")} · ${escapeHtml(task.attempt_count || 0)} attempts</span>
                  <span>Dependencies: ${escapeHtml((task.dependencies || []).join(", ") || "none")}</span>
                  ${task.id === taskView?.next_ready_task ? `<span class="small-badge good">Next ready</span>` : ""}
                </button>`).join("")}</div>` : `<p class="muted" data-task-group-empty>No ${group.toLowerCase()} tasks.</p>`}
            </section>`;
          }).join("")}
        </div>
      </section>
      <section class="surface task-workspace-detail" data-task-detail>
        ${selected ? `<div class="surface-title"><span>Selected task</span><span class="small-badge">${escapeHtml(selected.status || "unknown")}</span></div>
          <h3>${escapeHtml(selected.id)} · ${escapeHtml(selected.title || "Untitled task")}</h3>
          <p class="task-contract-outcome">${escapeHtml(selected.outcome || "Outcome is recorded in the task contract.")}</p>
          <div class="task-contract-grid">
            <section class="task-contract-section"><h4>Scope</h4><p>${escapeHtml(selected.dominant_deliverable || "No dominant deliverable recorded.")}</p>${scopePaths.length ? `<ul class="task-contract-list">${scopePaths.map((path) => `<li><code>${escapeHtml(path)}</code></li>`).join("")}</ul>` : `<p class="muted">No expected files recorded.</p>`}</section>
            <section class="task-contract-section"><h4>Acceptance</h4>${acceptanceMarkup}</section>
            <section class="task-contract-section"><h4>Dependencies</h4><p>${escapeHtml((selected.dependencies || []).join(", ") || "none")}</p>${selected.missing_dependencies?.length ? `<p class="task-contract-blocker">Missing: ${escapeHtml(selected.missing_dependencies.join(", "))}</p>` : ""}</section>
            <section class="task-contract-section"><h4>Verification</h4><p>${escapeHtml(selected.verification || "No verification command recorded.")}</p></section>
            <section class="task-contract-section"><h4>Evidence</h4>${evidenceMarkup}</section>
            <section class="task-contract-section"><h4>Attempts</h4>${attemptsMarkup}</section>
          </div>
          <section class="task-contract-section task-contract-blockers"><h4>Blockers</h4><p>${escapeHtml(selected.blocker || "none")}</p></section>
          <section class="task-action-bar" data-task-action-bar data-action-recommended="${escapeHtml(actionProjection?.recommended || "none")}">
            <div><p class="eyebrow">Next task action</p><strong>${escapeHtml(actionLabel)}</strong><p class="task-action-reason" data-task-action-reason>${escapeHtml(actionReason)}</p></div>
            <div class="task-action-controls">${actionButton}${actionName && typeof renderContextualRunnerControl === "function" ? renderContextualRunnerControl({actionLabel: actionLabel.toLowerCase()}) : ""}</div>
          </section>` : `<p class="muted">Select a task to inspect its bounded detail.</p>`}
      </section>
      ${(selected || activeTaskJob) ? `<section class="surface task-attempt-tray" data-task-attempt-tray data-attempt-status="${escapeHtml(attemptStatus)}">
        <div class="surface-title"><span>Active attempt</span><span class="small-badge">${escapeHtml(attemptStatus)}</span></div>
        <dl class="task-attempt-facts">
          <div><dt>Identity</dt><dd>${escapeHtml(attemptIdentity)}</dd></div>
          <div><dt>Elapsed</dt><dd>${escapeHtml(attemptElapsed)}</dd></div>
          <div><dt>Last output</dt><dd>${escapeHtml(attemptOutputAge)}</dd></div>
          <div><dt>Milestone</dt><dd>${escapeHtml(attemptMilestone)}</dd></div>
          <div><dt>Connection</dt><dd>${escapeHtml(attemptConnection)}</dd></div>
          <div><dt>Reconnect cursor</dt><dd>${escapeHtml(state.activeJobCursor || 0)}</dd></div>
        </dl>
        ${activeTaskJob && ["running", "waiting-for-operator", "cancelling"].includes(activeJob.status) ? `<button data-cancel-job="${escapeHtml(activeJob.job_id)}" type="button" ${activeJob.status === "cancelling" ? "disabled" : ""}>${activeJob.status === "cancelling" ? "Cancelling..." : "Cancel attempt"}</button>` : ""}
        <details class="task-attempt-output"><summary>Raw output</summary><pre>${escapeHtml(rawOutput || "No runtime output captured yet.")}</pre></details>
        ${activeTaskJob ? renderActiveJobConnectionSurface() : ""}
      </section>` : ""}
    </section>
  `;
}

async function renderWorkItemTasks() {
  const content = document.getElementById("intentContent");
  content.innerHTML = renderWorkItemTabPlaceholder("tasks");
  try {
    const query = runScopedQuery();
    const taskParams = new URLSearchParams(query);
    if (state.selectedRuntime) taskParams.set("runtime", state.selectedRuntime);
    const taskId = state.selectedTaskId ? `&task_id=${encodeURIComponent(state.selectedTaskId)}` : "";
    const payload = await api(`/api/tasks?${taskParams.toString()}${taskId}`);
    state.taskWorkspace = payload;
    state.taskWorkspaceError = "";
    content.innerHTML = renderTaskWorkspace(payload);
  } catch (error) {
    state.taskWorkspaceError = error.message || "Task Workspace unavailable";
    content.innerHTML = `<section class="surface task-workspace" data-task-workspace-state="error"><div class="empty-state">${escapeHtml(state.taskWorkspaceError)}</div></section>`;
  }
}

function renderStudioDocumentRail(studioState) {
  if (studioState === "no-run") return "";
  const refs = (state.dashboard?.recent_artifacts || [])
    .filter((ref) => !ref.stage || ref.stage === state.activeStage)
    .slice(0, 8);
  return `
    <aside class="studio-document-rail" aria-label="Stage documents">
      <div class="studio-document-rail-header">
        <span>Documents</span>
        <span class="small-badge">${escapeHtml(refs.length)}</span>
      </div>
      <div class="studio-document-list">
        ${refs.length ? refs.map((ref) => `
          <button class="studio-document-item${ref.key === state.activeArtifactKey ? " active" : ""}" data-artifact-stage="${escapeHtml(ref.stage || state.activeStage)}" data-artifact-key="${escapeHtml(ref.key)}" data-artifact-kind="${escapeHtml(ref.kind || "document")}" type="button">
            <span class="studio-document-icon" aria-hidden="true">▤</span>
            <span><strong>${escapeHtml(ref.label || ref.key || "Document")}</strong><small>${escapeHtml(ref.path || ref.kind || "stage document")}</small></span>
          </button>
        `).join("") : `<p class="muted studio-document-empty">No stage documents yet.</p>`}
      </div>
      <details class="studio-document-details">
        <summary>Technical details</summary>
        <p>Canonical Markdown, validator evidence, and runtime provenance remain available through the evidence view.</p>
      </details>
    </aside>
  `;
}

function renderActiveStudioStageSummary(item) {
  const result = activeStageView()?.result || {};
  return `
    <aside class="surface" data-studio-stage-summary>
      <div class="surface-title">Stage context</div>
      <div class="metric-grid compact">
        <div class="metric"><span>Status</span><strong>${escapeHtml(item?.status || "pending")}</strong></div>
        <div class="metric"><span>Attempts</span><strong>${escapeHtml(item?.attempt_count || 0)}</strong></div>
        <div class="metric"><span>Questions</span><strong>${escapeHtml(item?.unresolved_blocking_count || 0)}/${escapeHtml(item?.question_count || 0)}</strong></div>
        <div class="metric"><span>Validation</span><strong>${escapeHtml(item?.validator_pass_count || 0)}/${escapeHtml(item?.validator_fail_count || 0)}</strong></div>
      </div>
      <div class="panel-item"><strong>Eligibility</strong><span>${escapeHtml(item?.reason || "not started")}</span></div>
      <div class="panel-item"><strong>Validator report</strong>${pathLine(result.validator_report_path || "not available")}</div>
    </aside>
  `;
}

function renderActiveStudioRuntimeReadiness() {
  const runtime = selectedRuntimeView();
  return `
    <section class="surface studio-runtime-readiness" data-studio-runtime-readiness>
      <div class="surface-title"><span>Runtime launch context</span><span class="small-badge">${escapeHtml(runtime?.runtime_id || "not selected")}</span></div>
      ${runtime
        ? renderRuntimeReadinessDimensions(runtime)
        : '<p class="muted">Select a runtime to inspect launch dimensions.</p>'}
      ${renderProtectedWriteScope()}
    </section>
  `;
}

function studioObservationModel(job = state.activeJobStatus, item = activeStageItem()) {
  const attemptCount = Number(item?.attempt_count || 0);
  if (!job && !attemptCount && !["executing", "preparing", "validating"].includes(item?.status)) {
    return null;
  }
  if (job) {
    const cancelling = job.status === "cancelling" || job.cancel_state === "cancelling";
    return {
      source: "ui-job",
      status: job.status || "running",
      stage: job.stage || state.activeStage,
      elapsed: secondsLabel(job.elapsed_seconds),
      outputAge: runtimeOutputFreshnessLabel(job),
      milestone: `${stageTitle(job.stage || state.activeStage)} / ${item?.status || job.status || "running"}`,
      notice: cancelling
        ? "Cancellation requested; waiting for terminal runtime evidence."
        : job.silence_warning
          ? runtimeOutputMissingLabel(job)
          : "Live runtime evidence is updating.",
      tone: cancelling || job.silence_warning ? "warn" : "good",
      actionLabel: "Open live output"
    };
  }
  const externallyRunning = ["executing", "preparing", "validating"].includes(item?.status);
  return {
    source: externallyRunning ? "durable-external" : "durable-attempt",
    status: item?.status || "recorded",
    stage: item?.stage || state.activeStage,
    elapsed: "not available",
    outputAge: attemptCount ? "Persisted runtime evidence available" : "No output evidence recorded",
    milestone: `${stageTitle(item?.stage || state.activeStage)} / ${item?.status || "recorded"} / attempt ${attemptCount || "pending"}`,
    notice: externallyRunning
      ? "The stage is executing outside this browser session; durable state is authoritative."
      : "The latest terminal stage state is reconstructed from persisted evidence.",
    tone: ["failed", "blocked", "cancelled"].includes(item?.status) ? "warn" : "good",
    actionLabel: "Open persisted logs"
  };
}

function renderStudioLiveObservation() {
  const observation = studioObservationModel();
  if (!observation) return "";
  return `
    <section class="surface studio-live-observation" data-studio-observation="${escapeHtml(observation.source)}" role="status" aria-live="polite">
      <div class="surface-title">
        <span>Runtime observation</span>
        <span class="small-badge ${escapeHtml(observation.tone)}">${escapeHtml(observation.status)}</span>
      </div>
      <div class="metric-grid compact">
        <div class="metric"><span>Elapsed</span><strong>${escapeHtml(observation.elapsed)}</strong></div>
        <div class="metric"><span>Last output</span><strong>${escapeHtml(observation.outputAge)}</strong></div>
        <div class="metric"><span>Milestone</span><strong>${escapeHtml(observation.milestone)}</strong></div>
        <div class="metric"><span>Connection</span><strong>${escapeHtml(state.activeJobConnection?.state || "durable")}</strong></div>
      </div>
      <p>${escapeHtml(observation.notice)}</p>
      <button data-tab-shortcut="logs" type="button" class="secondary">${escapeHtml(observation.actionLabel)}</button>
    </section>
  `;
}

function updateStudioLiveObservation() {
  const host = document.getElementById("studioLiveObservation");
  if (!host) return;
  const markup = renderStudioLiveObservation();
  host.hidden = !markup;
  host.innerHTML = markup;
}

function renderActiveStudio() {
  if (state.nextFlowWizard.active) {
    return renderStudioNextFlowWizard();
  }
  if (state.dashboard?.terminal_handoff) {
    const {eligible} = studioFlowCompleteEligibility();
    if (eligible) {
      return renderStudioFlowCompleteState();
    }
  }
  const item = activeStageItem();
  const studioState = activeStudioState();
  return `
    <section class="active-studio" data-studio-surface="active-studio" data-state="${escapeHtml(studioState)}">
      ${renderActiveStudioContextBar(studioState, item)}
      ${renderIntentPhaseStepper()}
      ${typeof workflowProgressSummary === "function" ? workflowProgressSummary({collapsed: true}) : ""}
      <div class="active-studio-grid">
        ${renderStudioDocumentRail(studioState)}
        ${renderActiveStudioDocumentSlot(studioState)}
        ${studioState === "no-run" ? "" : `
          <div class="studio-reading-sidebar">
            ${renderActiveStudioStageSummary(item)}
            <aside id="studioEvidenceInspector" class="surface studio-evidence-inspector" hidden></aside>
          </div>
        `}
      </div>
      <div id="studioLiveObservation">${renderStudioLiveObservation()}</div>
      ${renderActiveStudioRuntimeReadiness()}
    </section>
  `;
}

function applyActiveStudioShellPresentation() {
  const content = document.getElementById("intentContent");
  const phases = document.getElementById("intentPhaseStepper");
  const decision = document.getElementById("intentDecisionSurface");
  if (content) content.dataset.activeStudio = "true";
  if (phases) phases.dataset.studioPhaseNavigation = "true";
  if (decision) decision.dataset.studioDecisionSlot = "true";
}
