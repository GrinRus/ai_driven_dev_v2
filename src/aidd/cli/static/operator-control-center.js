function runScopedQuery(stage = null) {
  const params = new URLSearchParams();
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  if (stage) params.set("stage", stage);
  return params.toString();
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

function renderRunningStageNotice(job) {
  const status = String(job?.status || "running");
  const stage = job?.stage || "workflow";
  const logChunkCount = state.activeJobLogChunks?.length || 0;
  const summary = status === "waiting-for-operator"
    ? "Runtime is waiting for an operator approval decision."
    : status === "cancelling"
      ? "Cancel request is in progress; runtime shutdown evidence will appear in logs."
      : "Stage is still running; live logs are the current evidence stream.";
  return `
    <div class="run-progress-notice" role="status" aria-live="polite">
      <div>
        <strong>${escapeHtml(stageTitle(stage))} in progress</strong>
        <p>${escapeHtml(summary)}</p>
      </div>
      <div class="run-progress-meta">
        <span><strong>Elapsed</strong>${escapeHtml(secondsLabel(job?.elapsed_seconds))}</span>
        <span><strong>Runtime output</strong>${escapeHtml(runtimeOutputFreshnessLabel(job))}</span>
        <span><strong>Live log chunks</strong>${escapeHtml(logChunkCount)}</span>
      </div>
    </div>
  `;
}

function renderActiveRunPanel() {
  const panel = document.getElementById("activeRunPanel");
  if (!panel) return;
  const job = state.activeJobStatus;
  const staleStages = (state.dashboard?.stages || []).filter((item) => item.stale);
  if (!job) {
    panel.innerHTML = `
      <div class="panel-title">Active run</div>
      <div class="panel-list">
        <div class="panel-item"><strong>Run</strong><span>${escapeHtml(state.activeRunId || "none")}</span></div>
        <div class="panel-item"><strong>Runtime</strong><span>${escapeHtml(state.selectedRuntime || state.dashboard?.run?.runtime_id || "not selected")}</span></div>
        <div class="panel-item"><strong>Stale downstream</strong><span>${escapeHtml(staleStages.length ? staleStages.map((item) => item.stage).join(", ") : "none")}</span></div>
      </div>
    `;
    return;
  }
  const runtime = selectedRuntimeView();
  const warning = job.silence_warning ? `
    <div class="truncation-notice" role="status">
      <strong>No output for ${escapeHtml(secondsLabel(job.last_output_age_seconds))}</strong>
      <span>Last line: ${escapeHtml(job.last_output_text || "no output captured")}</span>
    </div>
  ` : "";
  panel.innerHTML = `
    <div class="panel-title">Active run <span class="small-badge ${escapeHtml(statusClass(job.status))}">${escapeHtml(job.status || "running")}</span></div>
    ${renderRunningStageNotice(job)}
    <div class="panel-list">
      <div class="panel-item"><strong>Job</strong><span>${escapeHtml(job.job_id || "-")}</span></div>
      <div class="panel-item"><strong>Stage</strong><span>${escapeHtml(job.stage || "workflow")}</span></div>
      <div class="panel-item"><strong>Runner</strong><span>${escapeHtml(state.selectedRuntime || state.dashboard?.run?.runtime_id || "selected runtime")}</span></div>
      <div class="panel-item"><strong>Elapsed</strong><span>${escapeHtml(secondsLabel(job.elapsed_seconds))}</span></div>
      <div class="panel-item"><strong>Last output</strong><span>${escapeHtml(runtimeOutputFreshnessLabel(job))}</span></div>
      <div class="panel-item"><strong>Timeout</strong><span>${escapeHtml(timeoutSummary(runtime))}</span></div>
      <div class="panel-item"><strong>Command</strong><span title="${escapeHtml(runtime?.command || "")}">${escapeHtml(compactPath(runtime?.command || "not reported", 72))}</span></div>
    </div>
    ${warning}
    <div class="panel-actions">
      <button data-tab-shortcut="logs" type="button" class="secondary">Open logs</button>
      <button data-cancel-job="${escapeHtml(job.job_id || "")}" type="button" class="danger" ${activeJobIsTerminal() ? "disabled" : ""}>${escapeHtml(activeJobCancelLabel())}</button>
    </div>
  `;
}

function renderWarnings(warnings) {
  const items = (warnings || []).filter(Boolean);
  if (!items.length) return "";
  return `
    <div class="truncation-notice" role="status">
      <strong>Operator warnings</strong>
      <span>${items.map((item) => escapeHtml(item)).join(" ")}</span>
    </div>
  `;
}

async function renderTimeline() {
  const content = document.getElementById("cockpitContent");
  if (!state.activeRunId) {
    content.innerHTML = `<div class="empty-state">No run is available yet.</div>`;
    return;
  }
  content.innerHTML = `<div class="empty-state loading-state">Loading run timeline...</div>`;
  try {
    const params = runScopedQuery(state.activeStage);
    const view = await api(`/api/run/timeline?${params}`);
    const events = view.events || [];
    content.innerHTML = `
      <section class="surface control-center-screen">
        <div class="surface-title">
          <span>Stage Timeline</span>
          <span class="small-badge">${escapeHtml(events.length)} events</span>
        </div>
        ${renderWarnings(view.warnings)}
        <div class="operator-timeline">
          ${events.length ? events.map((event) => `
            <article class="timeline-event">
              <span class="marker-dot ${escapeHtml(statusClass(event.status || event.kind))}"></span>
              <div>
                <div class="question-head">
                  <strong>${escapeHtml(event.kind)}</strong>
                  <span class="small-badge">${escapeHtml(event.stage || "run")}</span>
                  ${event.attempt_number ? `<span class="small-badge">attempt ${escapeHtml(event.attempt_number)}</span>` : ""}
                </div>
                <div class="question-meta">
                  <span>${escapeHtml(event.time_utc || "time not recorded")}</span>
                  <span>${escapeHtml(event.status || "event")}</span>
                </div>
                <p>${escapeHtml(event.message || "")}</p>
                ${event.path ? pathLine(event.path, 92) : ""}
              </div>
            </article>
          `).join("") : `<div class="empty-state">No timeline events for this stage yet.</div>`}
        </div>
      </section>
    `;
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function diffFileWarning(file) {
  const warnings = [];
  if (file.allowed_scope_status === "outside") warnings.push("outside scope");
  if (file.scope_status === "outside-project-set") warnings.push("outside project set");
  if (!file.mentioned_in_report) warnings.push("not mentioned");
  if (file.truncated) warnings.push("truncated");
  (file.warnings || []).forEach((item) => warnings.push(item));
  return warnings;
}

function filteredDiffFiles(files) {
  const filter = state.implementDiffFilter;
  if (filter === "source") return files.filter((file) => file.category === "source");
  if (filter === "untracked") return files.filter((file) => file.status === "untracked");
  if (filter === "outside-scope") return files.filter((file) => file.allowed_scope_status === "outside");
  if (filter === "not-mentioned") return files.filter((file) => !file.mentioned_in_report);
  return files;
}

function renderDiffFilters(files) {
  const filters = [
    ["all", "All"],
    ["source", "Source"],
    ["untracked", "Untracked"],
    ["outside-scope", "Outside scope"],
    ["not-mentioned", "Not mentioned"]
  ];
  return `
    <div class="filter-row">
      ${filters.map(([id, label]) => `
        <button data-implement-diff-filter="${escapeHtml(id)}" class="${state.implementDiffFilter === id ? "active" : ""}" type="button">${escapeHtml(label)} ${escapeHtml(filteredDiffFiles(files).length && id === state.implementDiffFilter ? filteredDiffFiles(files).length : "")}</button>
      `).join("")}
    </div>
  `;
}

function renderImplementationSummary(implementation) {
  return `
    <section class="surface">
      <div class="surface-title">
        <span>Implementation summary</span>
        <span class="small-badge">${escapeHtml(implementation?.selected_task_id || "task not detected")}</span>
      </div>
      ${renderWarnings(implementation?.warnings)}
      <div class="metric-grid">
        <div class="metric"><span>Touched files</span><strong>${escapeHtml((implementation?.touched_files || []).length)}</strong></div>
        <div class="metric"><span>Verification</span><strong>${escapeHtml((implementation?.verification_commands || []).length)}</strong></div>
        <div class="metric"><span>Skipped checks</span><strong>${escapeHtml((implementation?.skipped_checks || []).length)}</strong></div>
        <div class="metric"><span>Residual risks</span><strong>${escapeHtml((implementation?.residual_risks || []).length)}</strong></div>
      </div>
      <div class="compact-list">
        ${(implementation?.verification_commands || []).slice(0, 4).map((item) => `<span>${escapeHtml(item)}</span>`).join("") || "<span>No verification commands detected.</span>"}
      </div>
    </section>
  `;
}

async function renderImplementReview() {
  const content = document.getElementById("cockpitContent");
  if (!state.activeRunId) {
    content.innerHTML = `<div class="empty-state">Run implement before reviewing repository changes.</div>`;
    return;
  }
  content.innerHTML = `<div class="empty-state loading-state">Loading repository diff...</div>`;
  try {
    const params = runScopedQuery("implement");
    const [diffView, evidence] = await Promise.all([
      api(`/api/repository/diff?${params}`),
      api(`/api/implement/evidence?${runScopedQuery()}`)
    ]);
    const files = diffView.source_files || [];
    const visible = filteredDiffFiles(files);
    if (!state.implementDiffPath && visible[0]) state.implementDiffPath = visible[0].path;
    const selected = visible.find((file) => file.path === state.implementDiffPath) || visible[0] || null;
    const unchanged = diffView.mentioned_but_unchanged || [];
    content.innerHTML = `
      <div class="implement-review-screen">
        ${renderImplementationSummary(evidence)}
        <section class="surface">
          <div class="surface-title">
            <span>Repository diff</span>
            <span class="small-badge">${escapeHtml(files.length)} source changes</span>
          </div>
          ${diffView.project_set_roots?.length ? `
            <div class="compact-list">
              ${diffView.project_set_roots.map((root) => `<span>${escapeHtml(root.root_id)}: ${escapeHtml(root.relative_root)}</span>`).join("")}
            </div>
          ` : ""}
          ${renderWarnings([...(diffView.warnings || []), ...unchanged.map((path) => `Mentioned but unchanged: ${path}`)])}
          ${renderDiffFilters(files)}
          <div class="diff-review-layout">
            <aside class="diff-file-list">
              ${visible.length ? visible.map((file) => {
                const selectedClass = selected && selected.path === file.path ? " selected" : "";
                const warnings = diffFileWarning(file);
                return `
	                  <button data-open-diff-file="${escapeHtml(file.path)}" class="diff-file-card${selectedClass}" type="button">
	                    <strong>${escapeHtml(file.path)}</strong>
	                    <span>${escapeHtml(file.status)} / ${escapeHtml(file.allowed_scope_status)} / ${escapeHtml(file.scope_status || "single-project")}</span>
	                    ${file.root_id ? `<span class="small-badge">${escapeHtml(file.root_label || file.root_id)} ${escapeHtml(file.root_relative_root || "")}</span>` : ""}
	                    <span>${warnings.map((item) => `<span class="small-badge warn">${escapeHtml(item)}</span>`).join("")}</span>
	                  </button>
                `;
              }).join("") : `<div class="empty-state">No files match this filter.</div>`}
            </aside>
            <section class="diff-viewer">
              ${selected ? `
                <div class="surface-title compact">
                  <span>${escapeHtml(selected.path)}</span>
                  <span class="small-badge">${escapeHtml(selected.status)}</span>
                </div>
                <pre class="diff-pre">${escapeHtml(selected.diff || "No textual diff available.")}</pre>
              ` : `<div class="empty-state">No source diff available.</div>`}
            </section>
          </div>
          <div class="wizard-actions">
            <button data-proceed-stage="review" type="button" ${selectedRuntimeReady() ? "" : "disabled"}>Proceed to review</button>
            <button data-rerun-implement type="button" class="secondary" ${selectedRuntimeReady() ? "" : "disabled"}>Rerun implement</button>
            <button data-open-request-tab type="button" class="secondary">Request intervention</button>
          </div>
        </section>
      </div>
    `;
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function checkedRemediationIds(sourceStage) {
  return Array.from(document.querySelectorAll(`[data-remediation-source="${sourceStage}"]:checked`))
    .map((input) => input.value)
    .filter(Boolean);
}

async function launchRemediation(sourceStage) {
  if (!ensureRunnableRuntime()) return;
  const ids = checkedRemediationIds(sourceStage);
  if (!ids.length) {
    toast("Select at least one item to send back to implement.");
    return;
  }
  const noteInput = document.querySelector(`[data-remediation-note="${sourceStage}"]`);
  const operatorNote = String(noteInput?.value || "").trim() || `Fix selected ${sourceStage} findings.`;
  const payload = {
    source_stage: sourceStage,
    source_ids: ids,
    target_stage: "implement",
    operator_note: operatorNote,
    runtime: state.selectedRuntime,
    run_id: state.activeRunId,
    log_follow: true
  };
  const job = await postJson("/api/remediation/launch", payload);
  toast("Remediation implement run started.");
  await startJobPolling(job);
}

async function renderReviewFindings() {
  const content = document.getElementById("cockpitContent");
  content.innerHTML = `<div class="empty-state loading-state">Loading review findings...</div>`;
  try {
    const view = await api(`/api/review/findings?${runScopedQuery()}`);
    const findings = view.findings || [];
    content.innerHTML = `
      <section class="surface findings-screen">
        <div class="surface-title">
          <span>Review Findings</span>
          <span class="small-badge ${view.approval_status === "rejected" ? "bad" : view.approval_status === "approved" ? "good" : "warn"}">${escapeHtml(view.approval_status || "not detected")}</span>
        </div>
        ${renderWarnings(view.warnings)}
        <div class="table-wrap">
          <table class="activity-table">
            <thead><tr><th>Select</th><th>ID</th><th>Severity</th><th>Disposition</th><th>Evidence</th><th>Summary</th></tr></thead>
            <tbody>
              ${findings.length ? findings.map((finding) => `
                <tr>
                  <td><input data-remediation-source="review" type="checkbox" value="${escapeHtml(finding.finding_id)}" ${finding.disposition === "must-fix" ? "checked" : ""}></td>
                  <td>${escapeHtml(finding.finding_id)}</td>
                  <td><span class="small-badge ${finding.severity === "high" || finding.severity === "critical" ? "bad" : finding.severity === "medium" ? "warn" : ""}">${escapeHtml(finding.severity || "-")}</span></td>
                  <td>${escapeHtml(finding.disposition || "-")}</td>
                  <td>${escapeHtml((finding.evidence || []).join(", ") || "-")}</td>
                  <td>${escapeHtml(finding.summary || "")}</td>
                </tr>
              `).join("") : `<tr><td colspan="6">No structured review findings detected.</td></tr>`}
            </tbody>
          </table>
        </div>
        <label class="form-field">
          <span>Operator note for implement</span>
          <textarea data-remediation-note="review" rows="4">Fix the selected review finding(s), update implementation-report.md, and preserve unrelated changes.</textarea>
        </label>
        <div class="wizard-actions">
          <button data-proceed-stage="qa" type="button" ${view.approval_status === "rejected" || !selectedRuntimeReady() ? "disabled" : ""}>Proceed to QA</button>
          <button data-remediation-launch="review" type="button" ${findings.length && selectedRuntimeReady() ? "" : "disabled"}>Send selected to implement</button>
          <button data-open-request-tab type="button" class="secondary">Request review intervention</button>
        </div>
      </section>
    `;
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function renderQaVerdict() {
  const content = document.getElementById("cockpitContent");
  content.innerHTML = `<div class="empty-state loading-state">Loading QA verdict...</div>`;
  try {
    const view = await api(`/api/qa/verdict?${runScopedQuery()}`);
    const risks = view.residual_risks || [];
    const issues = view.known_issues || [];
    const sourceItems = [
      ...risks.map((item, index) => ({id: `risk-${index + 1}`, label: item, kind: "risk"})),
      ...issues.map((item, index) => ({id: `issue-${index + 1}`, label: item, kind: "issue"}))
    ];
    const verdictClass = view.quality_verdict === "ready" ? "good" : view.quality_verdict === "not-ready" ? "bad" : "warn";
    content.innerHTML = `
      <section class="surface verdict-screen">
        <div class="surface-title">
          <span>QA Verdict</span>
          <span class="small-badge ${verdictClass}">${escapeHtml(view.quality_verdict || "not detected")}</span>
        </div>
        ${renderWarnings(view.warnings)}
        <div class="metric-grid">
          <div class="metric"><span>Release recommendation</span><strong>${escapeHtml(view.release_recommendation || "not detected")}</strong></div>
          <div class="metric"><span>Evidence IDs</span><strong>${escapeHtml((view.evidence_ids || []).length)}</strong></div>
          <div class="metric"><span>Residual risks</span><strong>${escapeHtml(risks.length)}</strong></div>
          <div class="metric"><span>Known issues</span><strong>${escapeHtml(issues.length)}</strong></div>
        </div>
        <div class="table-wrap">
          <table class="activity-table">
            <thead><tr><th>Select</th><th>Type</th><th>Item</th></tr></thead>
            <tbody>
              ${sourceItems.length ? sourceItems.map((item) => `
                <tr>
                  <td><input data-remediation-source="qa" type="checkbox" value="${escapeHtml(item.id)}" ${view.quality_verdict === "not-ready" ? "checked" : ""}></td>
                  <td>${escapeHtml(item.kind)}</td>
                  <td>${escapeHtml(item.label)}</td>
                </tr>
              `).join("") : `<tr><td colspan="3">No structured QA risks or issues detected.</td></tr>`}
            </tbody>
          </table>
        </div>
        <label class="form-field">
          <span>Operator note for implement</span>
          <textarea data-remediation-note="qa" rows="4">Fix the selected QA risk(s) or issue(s), rerun verification, and update implementation-report.md.</textarea>
        </label>
        <div class="wizard-actions">
          <button data-accept-qa type="button" ${view.quality_verdict === "not-ready" ? "disabled" : ""}>Accept complete</button>
          <button data-remediation-launch="qa" type="button" ${sourceItems.length && selectedRuntimeReady() ? "" : "disabled"}>Send selected to implement</button>
          <button data-next-flow-start type="button" class="secondary">Start follow-up</button>
          <button data-next-flow-action="archive-run" type="button" class="secondary" ${state.dashboard?.terminal_handoff ? "" : "disabled"}>Archive</button>
        </div>
      </section>
    `;
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}
