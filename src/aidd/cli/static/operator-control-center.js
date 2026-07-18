function runScopedQuery(stage = null) {
  const params = new URLSearchParams();
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  if (stage) params.set("stage", stage);
  return params.toString();
}
function renderRunningStageNotice(job) {
  const status = String(job?.status || "running");
  const stage = job?.stage || "workflow";
  const logChunkSummary = activeJobLiveLogChunkSummary(job);
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
        <span><strong>Live log chunks</strong>${escapeHtml(logChunkSummary)}</span>
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
      <strong>${escapeHtml(runtimeOutputMissingLabel(job))}</strong>
      <span>Last runtime line: ${escapeHtml(activeJobRuntimeOutputText(job) || "no runtime output captured")}</span>
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
      <div class="panel-item"><strong>Last runtime output</strong><span>${escapeHtml(runtimeOutputFreshnessLabel(job))}</span></div>
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
    <div class="filter-row" role="group" aria-label="Implementation diff filter">
      ${filters.map(([id, label]) => `
        <button data-implement-diff-filter="${escapeHtml(id)}" class="${state.implementDiffFilter === id ? "active" : ""}" type="button" aria-pressed="${state.implementDiffFilter === id ? "true" : "false"}">${escapeHtml(label)} ${escapeHtml(filteredDiffFiles(files).length && id === state.implementDiffFilter ? filteredDiffFiles(files).length : "")}</button>
      `).join("")}
    </div>
  `;
}

function renderImplementationVerificationGap(implementation) {
  const commands = implementation?.verification_commands || [];
  if (commands.length) return "";
  const skipped = implementation?.skipped_checks || [];
  const skippedLabel = skipped.length === 1 ? "1 skipped check" : `${skipped.length} skipped checks`;
  const skippedVerb = skipped.length === 1 ? "was" : "were";
  const body = skipped.length
    ? `${skippedLabel} ${skippedVerb} recorded, but no executable command evidence was parsed from implementation-report.md. Review cannot trust readiness until implementation records what ran.`
    : "No executable command evidence was parsed from implementation-report.md. Review cannot trust readiness until implementation records what ran.";
  return renderDecisionSummary({
    kind: "implementation-verification",
    tone: "bad",
    badge: "verification missing",
    title: "Implementation verification evidence is missing",
    body,
    primary: "Primary action: Rerun implement or request intervention",
    metrics: [
      {label: "Commands", value: "0", tone: "bad"},
      {label: "Skipped", value: String(skipped.length), tone: skipped.length ? "warn" : ""},
      {label: "Touched files", value: String((implementation?.touched_files || []).length)},
      {label: "Residual risks", value: String((implementation?.residual_risks || []).length)}
    ]
  });
}

function implementationSummaryWarnings(implementation) {
  const warnings = implementation?.warnings || [];
  if ((implementation?.verification_commands || []).length) return warnings;
  return warnings.filter((warning) =>
    !String(warning || "").includes("No executable verification commands")
  );
}

function renderImplementationVerificationItems(implementation) {
  const commands = implementation?.verification_commands || [];
  if (commands.length) {
    return commands.slice(0, 4).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  }
  const skipped = implementation?.skipped_checks || [];
  if (skipped.length) {
    return skipped.slice(0, 4).map((item) => `<span>Skipped: ${escapeHtml(item)}</span>`).join("");
  }
  return "<span>Verification evidence missing.</span>";
}

function implementationVerificationReady(implementation) {
  return Boolean((implementation?.verification_commands || []).length);
}

function renderImplementationProceedGuard(implementation) {
  if (implementationVerificationReady(implementation)) return "";
  return `
    <p class="form-error" role="status">
      Proceed to review is blocked until implementation records executable verification evidence.
    </p>
  `;
}

function renderImplementationSummary(implementation) {
  return `
    <section class="surface">
      <div class="surface-title">
        <span>Implementation summary</span>
        <span class="small-badge">${escapeHtml(implementation?.selected_task_id || "task not detected")}</span>
      </div>
      ${renderWarnings(implementationSummaryWarnings(implementation))}
      ${renderImplementationVerificationGap(implementation)}
      <div class="metric-grid">
        <div class="metric"><span>Touched files</span><strong>${escapeHtml((implementation?.touched_files || []).length)}</strong></div>
        <div class="metric"><span>Verification</span><strong>${escapeHtml((implementation?.verification_commands || []).length)}</strong></div>
        <div class="metric"><span>Skipped checks</span><strong>${escapeHtml((implementation?.skipped_checks || []).length)}</strong></div>
        <div class="metric"><span>Residual risks</span><strong>${escapeHtml((implementation?.residual_risks || []).length)}</strong></div>
      </div>
      <div class="compact-list">
        ${renderImplementationVerificationItems(implementation)}
      </div>
    </section>
  `;
}

function renderImplementationTaskGate(taskView) {
  return renderStudioImplementationQualityGate(taskView);
}

function renderImplementationRepositoryGate(context) {
  return renderStudioRepositoryEvidence({
    ...context,
    reviewEnabled: context.verificationReady
      && context.taskView.review_eligible
      && selectedRuntimeReady()
  });
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
    const [diffView, evidence, taskView] = await Promise.all([
      api(`/api/repository/diff?${params}`),
      api(`/api/implement/evidence?${runScopedQuery()}`),
      api(`/api/tasks?${runScopedQuery()}`).catch(() => ({tasks: []}))
    ]);
    const files = diffView.source_files || [];
    const visible = filteredDiffFiles(files);
    if (!state.implementDiffPath && visible[0]) state.implementDiffPath = visible[0].path;
    const selected = visible.find((file) => file.path === state.implementDiffPath) || visible[0] || null;
    const unchanged = diffView.mentioned_but_unchanged || [];
    const verificationReady = implementationVerificationReady(evidence);
    content.innerHTML = `
      <div class="implement-review-screen">
        ${renderImplementationSummary(evidence)}
        ${renderImplementationTaskGate(taskView)}
        ${renderImplementationRepositoryGate({
          diffView, evidence, taskView, files, visible, selected, unchanged, verificationReady
        })}
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

function countLabel(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function renderRemediationRuntimeGuard(sourceStage, hasRemediationItems) {
  if (!hasRemediationItems || selectedRuntimeReady()) return "";
  const label = sourceStage === "review" ? "review findings" : "QA risks or issues";
  return `
    <p class="form-error" role="status">
      Runtime readiness is required before sending ${escapeHtml(label)} back to implement.
    </p>
  `;
}

function renderQaCompletionGuard(view, hasRemediationItems) {
  if (view.quality_verdict !== "not-ready") return "";
  const nextStep = hasRemediationItems
    ? "Send selected QA risks or issues back to implement, then rerun verification and QA."
    : "Inspect the QA report or start a follow-up before completing this run.";
  return `
    <p class="form-error" role="status">
      Accept complete is disabled while QA is not-ready. ${escapeHtml(nextStep)}
    </p>
  `;
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
  const job = await guardedJobLaunch({
    kind: "remediation-launch",
    components: [state.activeRunId, sourceStage, ids.slice().sort().join("+")],
    controls: [`[data-remediation-launch="${sourceStage}"]`],
    execute: () => postJson("/api/remediation/launch", payload)
  });
  if (job) toast("Remediation implement run started.");
}

async function renderReviewFindings() {
  const content = document.getElementById("cockpitContent");
  content.innerHTML = `<div class="empty-state loading-state">Loading review findings...</div>`;
  try {
    const view = await api(`/api/review/findings?${runScopedQuery()}`);
    state.reviewFindingsView = view;
    state.reviewFindingsRunId = state.activeRunId;
    if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
    content.innerHTML = renderStudioReviewQualityGate(view);
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function renderQaVerdict() {
  const content = document.getElementById("cockpitContent");
  content.innerHTML = `<div class="empty-state loading-state">Loading QA verdict...</div>`;
  try {
    const view = await api(`/api/qa/verdict?${runScopedQuery()}`);
    state.qaVerdictView = view;
    state.qaVerdictRunId = state.activeRunId;
    if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
    const risks = view.residual_risks || [];
    const issues = view.known_issues || [];
    const sourceItems = [
      ...risks.map((item, index) => ({id: `risk-${index + 1}`, label: item, kind: "risk"})),
      ...issues.map((item, index) => ({id: `issue-${index + 1}`, label: item, kind: "issue"}))
    ];
    content.innerHTML = renderStudioQaQualityGate(view, sourceItems);
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}
