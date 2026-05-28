function renderOverview() {
  if (!state.dashboard?.run?.run_id) {
    return renderFirstLaunchState();
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
    </div>
  `;
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
