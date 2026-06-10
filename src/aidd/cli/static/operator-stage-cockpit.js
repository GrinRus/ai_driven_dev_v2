function renderOverview() {
  if (!state.dashboard?.run?.run_id) {
    return renderFirstLaunchState();
  }
  if (state.nextFlowWizard.active) {
    return renderNextFlowSourceSelection();
  }
  if (state.dashboard?.terminal_handoff) {
    return renderFlowCompleteState();
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
      <section id="runAccountabilityCard" class="surface run-accountability-card">
        ${renderRunAccountabilityCard()}
      </section>
    </div>
  `;
}

function renderRunAccountabilityCard() {
  const view = state.runAccountability;
  if (state.runAccountabilityError) {
    return `<div class="empty-state bad">${escapeHtml(state.runAccountabilityError)}</div>`;
  }
  if (!view) {
    return `<div class="empty-state loading-state">Loading run provenance...</div>`;
  }
  const prompts = view.prompt_pack_provenance || [];
  const configKeys = Object.keys(view.config_snapshot || {});
  return `
    <div class="surface-title">
      <span>Run provenance</span>
      <span class="small-badge">${escapeHtml(prompts.length)} prompts</span>
    </div>
    ${renderWarnings(view.warnings)}
    <div class="metric-grid">
      <div class="metric"><span>Runtime</span><strong>${escapeHtml(view.runtime_id)}</strong></div>
      <div class="metric"><span>Adapter</span><strong>${escapeHtml(view.adapter_id || "unknown")}</strong></div>
      <div class="metric"><span>Resource</span><strong>${escapeHtml(view.resource_source || "unknown")}</strong></div>
      <div class="metric"><span>Config keys</span><strong>${escapeHtml(configKeys.length)}</strong></div>
    </div>
    <div class="panel-item">
      <strong>Git SHA</strong>
      <span>${escapeHtml(view.repository_git_sha || "not recorded")}</span>
    </div>
    <div class="panel-item">
      <strong>Resource revision</strong>
      <span>${escapeHtml(view.resource_revision || "not recorded")}</span>
    </div>
    <div class="panel-item">
      <strong>Stage graph</strong>
      <span>${escapeHtml((view.stage_graph || []).join(" -> "))}</span>
    </div>
    <div class="compact-list">
      ${prompts.slice(0, 4).map((entry) => `<span>${escapeHtml(entry.path)} ${escapeHtml(entry.sha256.slice(0, 12))}</span>`).join("") || "<span>No prompt provenance recorded.</span>"}
    </div>
  `;
}

async function loadRunAccountabilityCard() {
  const card = document.getElementById("runAccountabilityCard");
  if (!card || !state.activeRunId) return;
  try {
    state.runAccountabilityError = "";
    state.runAccountability = await api(`/api/run/accountability?${runScopedQuery()}`);
  } catch (error) {
    state.runAccountability = null;
    state.runAccountabilityError = error.message || "run provenance unavailable";
  }
  card.innerHTML = renderRunAccountabilityCard();
}

function repairCenterStatus(validation, stopped) {
  if (stopped?.stopped) return "explicit-stop";
  if (validation?.validator_fail_count && validation?.final_state === "failed" && (validation.repair_attempts || []).length) {
    return "repair-exhausted";
  }
  return validation?.status || "clear";
}

function renderRecoveryActionBand(diagnostics) {
  const validation = diagnostics?.validation;
  const stopped = diagnostics?.stopped;
  const status = repairCenterStatus(validation, stopped);
  const repairAvailable = status === "repair-available";
  const stoppedMessage = stopped?.stopped ? stopped.detail || "Stage stopped." : "";
  return `
    <section class="repair-action-band ${repairAvailable ? "repair-available" : ""}">
      <div>
        <div class="surface-title">
          <span>${repairAvailable ? "Repair Available" : status === "repair-exhausted" ? "Repair Exhausted" : status === "explicit-stop" ? "Explicit Stop" : "Repair Center"}</span>
          <span class="small-badge ${status === "clear" ? "good" : status === "explicit-stop" || status === "repair-exhausted" ? "bad" : "warn"}">${escapeHtml(status)}</span>
        </div>
        <p>${escapeHtml(stoppedMessage || (repairAvailable ? "Validation failed. Run Repair starts the selected stage through the normal stage runner." : "Review validation evidence, repair history, and recovery actions before continuing."))}</p>
      </div>
      <div class="repair-actions">
        <button data-run-repair type="button" ${repairAvailable ? "" : "disabled"}>Run Repair</button>
        <button data-stop-run type="button" class="danger">Stop Run</button>
        <button data-tab-shortcut="request" type="button" class="secondary">Request Change</button>
      </div>
    </section>
  `;
}

function renderRepairTimeline(validation) {
  const attempts = validation?.repair_attempts || [];
  if (!attempts.length) {
    return `<div class="empty-state">No repair attempts recorded.</div>`;
  }
  return `
    <div class="repair-timeline">
      ${attempts.map((attempt) => `
        <article class="repair-timeline-card">
          <div class="question-head">
            <strong>Attempt ${escapeHtml(attempt.attempt_number)}</strong>
            <span class="small-badge ${attempt.outcome === "succeeded" ? "good" : "warn"}">${escapeHtml(attempt.outcome)}</span>
          </div>
          <div class="question-meta">
            <span>${escapeHtml(attempt.trigger)}</span>
            <span>${escapeHtml(attempt.recorded_at_utc)}</span>
          </div>
          ${attempt.validator_report_path ? pathLine(attempt.validator_report_path, 78) : ""}
          ${attempt.repair_brief_path ? pathLine(attempt.repair_brief_path, 78) : ""}
        </article>
      `).join("")}
    </div>
  `;
}

function renderBlockedStageRecovery(diagnostics) {
  const blocking = diagnostics?.blocking_questions;
  const stopped = diagnostics?.stopped;
  const requestChange = diagnostics?.request_change;
  return `
    <aside class="surface repair-context-panel">
      <div class="surface-title">Recovery context</div>
      <div class="panel-item">
        <strong>Blocked questions</strong>
        <span>${escapeHtml(blocking?.unresolved_question_ids?.join(", ") || "none")}</span>
      </div>
      <div class="panel-item">
        <strong>Answers path</strong>
        ${pathLine(blocking?.answers_path || "not available", 78)}
      </div>
      <div class="panel-item">
        <strong>Stopped state</strong>
        <span>${escapeHtml(stopped?.stopped ? stopped.detail || "stopped" : "not stopped")}</span>
      </div>
      <div class="panel-item">
        <strong>Request change</strong>
        <span>${escapeHtml(requestChange?.reason || "Stage-scoped intervention can be opened from Request Change.")}</span>
      </div>
    </aside>
  `;
}

function renderValidation() {
  const view = activeStageView();
  const result = view?.result;
  const diagnostics = view?.diagnostics;
  const validation = diagnostics?.validation;
  if (!result) return `<div class="empty-state">No validation evidence for this stage yet.</div>`;
  const repairs = (result.repair_output_paths || []).map((path) => `
    <button class="artifact-row" data-open-artifact="${escapeHtml(path)}" type="button">
      <span><strong>${escapeHtml(path.split("/").pop())}</strong>${pathLine(path)}</span>
      <span class="small-badge warn">repair</span>
    </button>
  `).join("") || `<div class="empty-state">No repair outputs recorded.</div>`;
  return `
    <div class="validation-repair-center">
      <section class="surface">
        <div class="surface-title">
          <span>Validation / Repair Center</span>
          <span class="small-badge ${result.validator_fail_count ? "bad" : "good"}">${escapeHtml(repairCenterStatus(validation, diagnostics?.stopped))}</span>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>Pass</span><strong>${escapeHtml(result.validator_pass_count)}</strong></div>
          <div class="metric"><span>Fail</span><strong>${escapeHtml(result.validator_fail_count)}</strong></div>
          <div class="metric"><span>Final state</span><strong>${escapeHtml(result.final_state)}</strong></div>
          <div class="metric"><span>Attempts</span><strong>${escapeHtml(result.attempt_count)}</strong></div>
        </div>
        ${renderRecoveryActionBand(diagnostics)}
        <div class="panel-item">
          <strong>Validator report</strong>
          ${pathLine(result.validator_report_path)}
        </div>
        <div class="panel-item">
          <strong>Repair evidence</strong>
          <div class="recent-artifacts">${repairs}</div>
        </div>
        <div class="surface-title compact">Validation attempt timeline</div>
        ${renderRepairTimeline(validation)}
      </section>
      ${renderBlockedStageRecovery(diagnostics)}
    </div>
  `;
}

async function renderCockpit() {
  const content = document.getElementById("cockpitContent");
  if (state.activeTab === "project-home") {
    content.innerHTML = renderProjectHome();
    return;
  }
  if (state.activeTab === "overview") {
    content.innerHTML = renderOverview();
    void loadRunAccountabilityCard();
  }
  if (state.activeTab === "questions") content.innerHTML = renderQuestions();
  if (state.activeTab === "validation") content.innerHTML = renderValidation();
  if (state.activeTab === "timeline") await renderTimeline();
  if (state.activeTab === "artifacts") await renderArtifacts();
  if (state.activeTab === "recovery") content.innerHTML = renderRecoveryScreen();
  if (state.activeTab === "implement-review") await renderImplementReview();
  if (state.activeTab === "review-findings") await renderReviewFindings();
  if (state.activeTab === "qa-verdict") await renderQaVerdict();
  if (state.activeTab === "logs") await renderLogs();
  if (state.activeTab === "approvals") await renderApprovals();
  if (state.activeTab === "request") await renderRequestChange();
  if (state.activeTab === "history") {
    content.innerHTML = renderRunHistory();
    void loadRunComparisonPanel();
  }
}

function renderProjectHomeWorkItemCard(item) {
  const selected = item.work_item === state.dashboard?.work_item;
  const run = item.latest_run || {};
  const rootChips = renderProjectSetRootChips(item);
  const blockerBadge = item.blocker_count
    ? `<span class="small-badge warn">${escapeHtml(item.blocker_count)} blocker${item.blocker_count === 1 ? "" : "s"}</span>`
    : `<span class="small-badge good">clear</span>`;
  return `
    <article class="project-work-item-card ${selected ? "selected" : ""}">
      <div class="surface-title compact">
        <span>${escapeHtml(item.work_item)}</span>
        <span class="small-badge ${workItemStatusClass(item)}">${escapeHtml(item.terminal_state)}</span>
      </div>
      <p>${escapeHtml(item.has_request_context ? "Request context ready" : "Request context missing")}</p>
      <div class="metric-grid compact">
        <div class="metric"><span>Stage</span><strong>${escapeHtml(item.active_stage)}</strong></div>
        <div class="metric"><span>Progress</span><strong>${escapeHtml(item.stage_progress_label)}</strong></div>
        <div class="metric"><span>Run</span><strong>${escapeHtml(run.run_id || "none")}</strong></div>
        <div class="metric"><span>Runtime</span><strong>${escapeHtml(run.runtime_id || "not selected")}</strong></div>
      </div>
      <div class="badge-row">${rootChips}${blockerBadge}</div>
      <div class="wizard-actions">
        <button data-project-home-resume="${escapeHtml(item.work_item)}" type="button">${selected ? "Open workbench" : "Resume"}</button>
        ${run.run_id ? `<button data-project-home-open-run="${escapeHtml(item.work_item)}" class="secondary" type="button">Open latest run</button>` : ""}
      </div>
    </article>
  `;
}

function renderProjectHome() {
  const home = state.projectHome;
  if (!home) return `<div class="empty-state loading-state">Loading Project Home...</div>`;
  const items = projectHomeWorkItems();
  const selected = currentWorkItemSummary();
  const blocked = items.filter((item) => item.blocker_count);
  const running = items.filter((item) => item.terminal_state === "running");
  const complete = items.filter((item) => item.terminal_state === "completed");
  return `
    <section class="project-home-screen">
      <div class="surface project-home-hero">
        <div>
          <p class="eyebrow">Project Home</p>
          <h2>Work item console</h2>
          <p class="muted">Project, work item, run, stage progress, blockers, and project-set roots are rebuilt from the selected local <code>.aidd</code> workspace.</p>
        </div>
        <div class="panel-list compact">
          <div class="panel-item"><strong>Project root</strong>${pathLine(home.project_root, 82)}</div>
          <div class="panel-item"><strong>.aidd root</strong>${pathLine(home.workspace_root, 82)}</div>
          <div class="panel-item"><strong>Selected</strong><span>${escapeHtml(selected?.work_item || "none")}</span></div>
        </div>
      </div>
      <div class="project-home-grid">
        <section class="surface">
          <div class="surface-title">
            <span>Work Item Board</span>
            <span class="small-badge">${escapeHtml(items.length)} total</span>
          </div>
          <div class="metric-grid compact">
            <div class="metric"><span>Running</span><strong>${escapeHtml(running.length)}</strong></div>
            <div class="metric"><span>Blocked</span><strong>${escapeHtml(blocked.length)}</strong></div>
            <div class="metric"><span>Done</span><strong>${escapeHtml(complete.length)}</strong></div>
            <div class="metric"><span>Workspace</span><strong>${home.workspace_exists ? "exists" : "new"}</strong></div>
          </div>
          <div class="project-work-item-grid">
            ${items.length ? items.map(renderProjectHomeWorkItemCard).join("") : `<div class="empty-state">No work items in this project yet.</div>`}
          </div>
        </section>
        <aside class="surface">
          <div class="surface-title">
            <span>Resume context</span>
            <span class="small-badge">${escapeHtml(selected?.terminal_state || "none")}</span>
          </div>
          ${selected ? `
            <div class="panel-list">
              <div class="panel-item"><strong>Work item</strong><span>${escapeHtml(selected.work_item)}</span></div>
              <div class="panel-item"><strong>Latest run</strong><span>${escapeHtml(selected.latest_run?.run_id || "none")}</span></div>
              <div class="panel-item"><strong>Next stage</strong><span>${escapeHtml(selected.active_stage)}</span></div>
              <div class="panel-item"><strong>Blockers</strong><span>${escapeHtml(selected.blocker_count)}</span></div>
            </div>
            <div class="surface-title compact">Project-set roots</div>
            <div class="compact-list">
              ${(selected.project_set_roots || []).map((root) => `<span title="${escapeHtml(root.root)}">${escapeHtml(root.root_id)} / ${escapeHtml(root.relative_root)}${root.role ? ` / ${escapeHtml(root.role)}` : ""}</span>`).join("") || "<span>Single project root</span>"}
            </div>
          ` : `<div class="empty-state">Select a work item to inspect resume context.</div>`}
        </aside>
      </div>
    </section>
  `;
}

function renderRecoveryScreen() {
  const firstFailure = state.dashboard?.first_failure || null;
  const actions = state.dashboard?.recovery_actions || [];
  return `
    <section class="recovery-assistant-screen">
      <div class="surface">
        <div class="surface-title">
          <span>Recovery Assistant</span>
          <span class="small-badge">${escapeHtml(actions.length)} suggestions</span>
        </div>
        ${firstFailure ? `
          <article class="recovery-card failure">
            <div class="question-head">
              <strong>${escapeHtml(firstFailure.title)}</strong>
              <span class="small-badge bad">${escapeHtml(firstFailure.kind)}</span>
            </div>
            <p>${escapeHtml(firstFailure.detail)}</p>
            ${firstFailure.path ? pathLine(firstFailure.path, 88) : ""}
          </article>
        ` : `<div class="empty-state">No decisive failure signal detected.</div>`}
        <div class="project-work-item-grid">
          ${actions.length ? actions.map((action) => `
            <article class="project-work-item-card">
              <div class="surface-title compact">
                <span>${escapeHtml(action.label)}</span>
                <span class="small-badge">${escapeHtml(action.action)}</span>
              </div>
              <p>${escapeHtml(action.detail)}</p>
              <div class="wizard-actions">
                <button data-recovery-action="${escapeHtml(action.action)}" data-recovery-stage="${escapeHtml(action.stage || state.activeStage)}" type="button" ${action.enabled ? "" : "disabled"}>Open</button>
              </div>
            </article>
          `).join("") : `<div class="empty-state">No guided recovery actions for this state.</div>`}
        </div>
      </div>
    </section>
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

function renderRecoveryAssistantPanel() {
  const host = document.getElementById("recoveryAssistantPanel");
  if (!host) return;
  const firstFailure = state.dashboard?.first_failure || null;
  const actions = state.dashboard?.recovery_actions || [];
  const questionCount = (state.dashboard?.stages || []).reduce((total, item) => total + Number(item.unresolved_blocking_count || 0), 0);
  const failureCount = firstFailure ? 1 : 0;
  const actionRows = actions.length ? actions.map((action) => `
    <button class="artifact-row" data-recovery-action="${escapeHtml(action.action)}" data-recovery-stage="${escapeHtml(action.stage || state.activeStage)}" type="button" ${action.enabled ? "" : "disabled"}>
      <span>
        <strong>${escapeHtml(action.label)}</strong>
        <span>${escapeHtml(action.detail)}</span>
      </span>
      <span class="small-badge">${escapeHtml(action.action)}</span>
    </button>
  `).join("") : `<div class="empty-state compact">No recovery action needed for the current state.</div>`;
  const failure = firstFailure ? `
    <article class="recovery-card failure">
      <div class="question-head">
        <strong>${escapeHtml(firstFailure.title)}</strong>
        <span class="small-badge bad">${escapeHtml(firstFailure.kind)}</span>
      </div>
      <p>${escapeHtml(firstFailure.detail)}</p>
      ${firstFailure.path ? pathLine(firstFailure.path, 72) : ""}
    </article>
  ` : `<div class="empty-state compact">No decisive failure signal detected.</div>`;
  host.innerHTML = `
    <div class="panel-title">Recovery Assistant</div>
    <div class="filter-row compact">
      <span class="small-badge ${questionCount ? "warn" : ""}">Questions ${escapeHtml(questionCount)}</span>
      <span class="small-badge ${failureCount ? "bad" : ""}">Failures ${escapeHtml(failureCount)}</span>
      <span class="small-badge">Suggestions ${escapeHtml(actions.length)}</span>
    </div>
    ${failure}
    <div class="panel-list">${actionRows}</div>
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
  const readinessClass = runtime && runtime.provider_available && runtime.execution_command_available ? "good" : runtime || state.readinessError ? "warn" : "";
  const badge = runtime
    ? runtime.runtime_id
    : state.readinessLoading
      ? "checking"
      : state.readinessError
        ? "error"
        : "none";
  let details = "";
  if (state.readinessLoading) {
    details = readinessDetail("Status", "checking runtimes");
  } else if (!runtime && state.readinessError) {
    details = readinessDetail("Status", `readiness unavailable: ${state.readinessError}`);
  } else if (!runtime) {
    details = readinessDetail("Status", "select a runtime to view readiness");
  } else {
    details = [
      readinessDetail("Support tier", runtime.support_tier),
      readinessDetail("Command source", runtime.command_source),
      readinessDetail("Command", runtime.command, 86),
      readinessDetail("Execution mode", runtime.execution_mode),
      readinessDetail("Permission policy", runtime.permission_policy),
      readinessDetail("Interaction mode", runtime.interaction_mode),
      readinessDetail("Auto approval", runtime.auto_approval_preset),
      readinessDetail("Timeouts", timeoutSummary(runtime), 96),
      readinessDetail("Provider", runtime.provider_available ? "available" : "unavailable"),
      readinessDetail("Provider version", runtime.provider_version),
      readinessDetail("Provider command", runtime.provider_command, 86),
      readinessDetail("Execution command", runtime.execution_command_available ? "available" : "unavailable")
    ].join("");
  }
  document.getElementById("safetyPanel").innerHTML = `
    <div class="panel-title">Safety / Readiness <span class="small-badge ${readinessClass}">${escapeHtml(badge)}</span></div>
    <div class="panel-list">
      <div class="panel-item"><strong>No upstream write</strong><span>UI actions stay inside local AIDD workspace and normal runner boundaries.</span></div>
      ${details}
    </div>
  `;
}

function renderSidebar() {
  if (typeof renderActiveRunPanel === "function") renderActiveRunPanel();
  renderNextActionPanel();
  renderBlockersPanel();
  renderRecoveryAssistantPanel();
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
  document.body.classList.remove("setup-active");
  document.getElementById("openWorkspaceButton").disabled = false;
  renderRuntimeSelector();
  renderTopbar();
  renderProjectHomeRail();
  renderStageRail();
  renderStageHeader();
  renderGlobalNextActionStrip();
  updateContextualTabs();
  renderSidebar();
  renderBottomDock();
  activateTab(state.activeTab);
  await renderCockpit();
}
