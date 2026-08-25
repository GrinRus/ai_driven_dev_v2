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
  const panel = document.getElementById("technicalActiveRun");
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
    return commands.slice(0, 8).map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  }
  const skipped = implementation?.skipped_checks || [];
  if (skipped.length) {
    return skipped.slice(0, 8).map((item) => `<span>Skipped: ${escapeHtml(item)}</span>`).join("");
  }
  return "<span>Verification evidence missing.</span>";
}

function renderImplementationEvidenceList(items, emptyLabel) {
  const values = (items || []).filter(Boolean);
  if (!values.length) return `<span class="muted">${escapeHtml(emptyLabel)}</span>`;
  return values.map((item) => `<span>${escapeHtml(item)}</span>`).join("");
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
    <section class="surface target-implementation-summary" data-implementation-review-summary>
      <div class="target-implementation-summary-heading">
        <div>
          <p class="eyebrow">Repository truth</p>
          <h2>Implementation Review</h2>
          <p>Compare the recorded implementation claims with the actual repository diff before opening Review.</p>
        </div>
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
      <div class="compact-list" data-implementation-verification>
        <strong>Actual verification commands/results</strong>
        ${renderImplementationVerificationItems(implementation)}
      </div>
      <div class="compact-list" data-implementation-task-claims>
        <strong>Completed task claim</strong>
        <span>${escapeHtml(implementation?.selected_task_id || "No selected task claim recorded.")}</span>
        <span>Reported touched files: ${escapeHtml((implementation?.touched_files || []).join(", ") || "none")}</span>
      </div>
      <div class="compact-list" data-implementation-risks>
        <strong>Residual risks</strong>
        ${renderImplementationEvidenceList(implementation?.residual_risks, "No residual risks recorded.")}
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

function renderTargetImplementationReviewGate({diffView, evidence, taskView, files, reviewEnabled}) {
  const completed = (taskView?.tasks || []).filter((task) => task.status === "succeeded");
  const insideScope = files.filter((file) => file.allowed_scope_status === "inside");
  const outsideScope = files.filter((file) => file.allowed_scope_status === "outside");
  const tests = files.filter((file) => file.category === "test");
  const docs = files.filter((file) => file.category === "documentation");
  const commands = evidence?.verification_commands || [];
  const risks = evidence?.residual_risks || [];
  const claims = evidence?.touched_files || [];
  const reviewBlocker = taskView?.review_blocker || "Review remains blocked until implementation evidence is complete.";
  const runner = reviewEnabled && typeof renderContextualRunnerControl === "function"
    ? renderContextualRunnerControl({actionLabel: "review"})
    : "";
  return `
    <aside class="target-review-gate" data-target-review-gate aria-label="Review gate">
      <div class="target-review-gate-heading">
        <h3>Review gate</h3>
        <span class="small-badge ${reviewEnabled ? "good" : "bad"}">${reviewEnabled ? "Ready" : "Blocked"}</span>
      </div>
      <section class="target-review-gate-section" data-review-scope-coverage>
        <h4>Scope coverage</h4>
        <div class="target-review-checks">
          <span><b class="target-check ${insideScope.length ? "good" : "bad"}">✓</b> Source files <strong>${escapeHtml(insideScope.length)} of ${escapeHtml(files.length)}</strong></span>
          <span><b class="target-check ${tests.length ? "good" : "warn"}">✓</b> Test files <strong>${escapeHtml(tests.length)} of ${escapeHtml(tests.length)}</strong></span>
          <span><b class="target-check ${docs.length ? "good" : "warn"}">✓</b> Docs <strong>${escapeHtml(docs.length)} of ${escapeHtml(docs.length)}</strong></span>
          <span><b class="target-check ${outsideScope.length ? "bad" : "good"}">${outsideScope.length ? "!" : "✓"}</b> Outside scope <strong>${escapeHtml(outsideScope.length)}</strong></span>
        </div>
      </section>
      <section class="target-review-gate-section" data-review-claims-evidence>
        <h4>Claims and evidence</h4>
        ${claims.length ? `<ul>${claims.slice(0, 6).map((path) => `<li>${escapeHtml(path)}</li>`).join("")}</ul>` : `<p class="muted">No changed files were claimed.</p>`}
        <p class="target-review-gate-meta">${escapeHtml(completed.length)} completed task${completed.length === 1 ? "" : "s"} from the canonical ledger</p>
      </section>
      <section class="target-review-gate-section" data-review-verification>
        <h4>Verification commands run</h4>
        ${commands.length ? `<div class="target-review-command-list">${commands.slice(0, 5).map((command) => `<span><b class="target-check good">✓</b><code>${escapeHtml(command)}</code></span>`).join("")}</div>` : `<p class="form-error">No executable verification evidence recorded.</p>`}
      </section>
      <section class="target-review-gate-section" data-review-risks>
        <h4>Risks</h4>
        ${risks.length ? `<ul>${risks.slice(0, 4).map((risk) => `<li>${escapeHtml(risk)}</li>`).join("")}</ul>` : `<p class="target-review-risk-low"><b class="target-check good">✓</b> No residual risks recorded.</p>`}
      </section>
      ${reviewEnabled && runner ? `<div class="target-review-runner">${runner}</div>` : ""}
      ${!reviewEnabled ? `<p class="form-error" data-target-review-blocker>${escapeHtml(reviewBlocker)}</p>` : ""}
      <div class="target-review-gate-actions">
        <button data-proceed-stage="review" data-aidd-primary-action aria-label="Open Review stage" type="button" ${reviewEnabled ? "" : "disabled aria-disabled=\"true\""}>Proceed to Review</button>
        <button data-open-request-tab type="button" class="secondary">Request change</button>
      </div>
      <p class="target-review-gate-note">This launches the Review stage and moves this Work Item forward.</p>
      ${diffView?.aidd_artifacts?.length ? `<small class="muted">${escapeHtml(diffView.aidd_artifacts.length)} core-owned evidence artifact(s) remain read-only.</small>` : ""}
    </aside>
  `;
}

async function renderImplementReview() {
  const content = document.getElementById("intentContent");
  if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
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
      <div class="implement-review-screen target-implementation-review" data-target-implementation-review>
        ${renderImplementationSummary(evidence)}
        ${renderImplementationTaskGate(taskView)}
        <div class="target-implementation-workspace">
          ${renderImplementationRepositoryGate({
            diffView, evidence, taskView, files, visible, selected, unchanged, verificationReady
          })}
          ${renderTargetImplementationReviewGate({diffView, evidence, taskView, files, reviewEnabled: verificationReady && taskView.review_eligible && selectedRuntimeReady()})}
        </div>
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

function remediationDraftIdentity(sourceStage) {
  if (typeof operatorPurposeDraftIdentity === "function") {
    return operatorPurposeDraftIdentity("remediation", sourceStage);
  }
  return operatorDraftIdentity("intervention", sourceStage);
}

function readRemediationDraft(sourceStage) {
  if (typeof readOperatorDraft !== "function") return null;
  try {
    return readOperatorDraft(remediationDraftIdentity(sourceStage));
  } catch (_error) {
    return null;
  }
}

function remediationDraftDestination() {
  return `.aidd/workitems/${state.dashboard?.work_item || state.activeRouteWorkItem || "no-work-item"}/remediations/${state.activeRunId || "no-run"}/request-####.md`;
}

function remediationPreviewMarkdown(sourceStage, ids, note) {
  const sourceLabel = sourceStage === "review" ? "Review finding" : "QA risk or issue";
  return [
    "# Remediation Request",
    "",
    `- Source stage: ${sourceStage}`,
    `- Target stage: implement`,
    "",
    "## Selected source ids",
    "",
    ...(ids.length ? ids.map((id) => `- ${id}`) : ["- none selected"]),
    "",
    "## Operator note",
    "",
    note || `Select at least one ${sourceLabel.toLowerCase()} before writing.`,
    "",
    "## Runtime instruction",
    "",
    "Fix only the selected findings or risks and record verification evidence in implementation-report.md.",
    ""
  ].join("\n");
}

function renderRemediationDraftPreview(sourceStage, {destination = null} = {}) {
  const draft = readRemediationDraft(sourceStage);
  const ids = draft?.value?.source_ids || [];
  const note = draft?.value?.text || "";
  return `
    <details class="remediation-draft-preview" data-remediation-write-preview open>
      <summary>Markdown Write/Preview</summary>
      <div class="compact-list" data-remediation-destination>
        <span>Destination: ${escapeHtml(destination || remediationDraftDestination())}</span>
        <span>Durable destination is assigned by the service on write; generated stage documents remain read-only.</span>
      </div>
      <pre data-remediation-preview>${escapeHtml(remediationPreviewMarkdown(sourceStage, ids, note))}</pre>
    </details>
  `;
}

function persistRemediationDraft(sourceStage) {
  if (typeof writeOperatorDraft !== "function") return;
  const noteInput = document.querySelector(`[data-remediation-note="${sourceStage}"]`);
  const value = typeof operatorPurposeDraftValue === "function"
    ? operatorPurposeDraftValue("remediation", {
      text: String(noteInput?.value || ""),
      source_ids: checkedRemediationIds(sourceStage),
      source_stage: sourceStage,
      destination: remediationDraftDestination(),
      source_evidence: checkedRemediationIds(sourceStage)
    })
    : {
      text: String(noteInput?.value || ""),
      source_ids: checkedRemediationIds(sourceStage),
      source_stage: sourceStage,
      destination: remediationDraftDestination()
    };
  try {
    writeOperatorDraft(remediationDraftIdentity(sourceStage), value);
  } catch (_error) {
    // Keep the in-memory form usable if a bounded browser-session store is unavailable.
  }
}

function updateRemediationPreview(sourceStage) {
  const preview = document.querySelector("[data-remediation-preview]");
  if (!preview) return;
  const noteInput = document.querySelector(`[data-remediation-note="${sourceStage}"]`);
  preview.textContent = remediationPreviewMarkdown(
    sourceStage,
    checkedRemediationIds(sourceStage),
    String(noteInput?.value || "").trim()
  );
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
  persistRemediationDraft(sourceStage);
  const payload = {
    source_stage: sourceStage,
    source_ids: ids,
    target_stage: "implement",
    operator_note: operatorNote,
    runtime: state.selectedRuntime,
    run_id: state.activeRunId,
    log_follow: true,
    ...runtimeSelectorPayload()
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
  const content = document.getElementById("intentContent");
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
  const content = document.getElementById("intentContent");
  content.innerHTML = `<div class="empty-state loading-state">Loading QA verdict...</div>`;
  try {
    const view = await api(`/api/qa/verdict?${runScopedQuery()}`);
    state.qaVerdictView = view;
    state.qaVerdictRunId = state.activeRunId;
    if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
    const risks = view.residual_risks || [];
    const issues = view.known_issues || [];
    const sourceItems = [
      ...risks.map((item, index) => ({
        id: `risk-${index + 1}`,
        label: item,
        kind: "risk",
        evidence: view.evidence_references || view.evidence_ids || []
      })),
      ...issues.map((item, index) => ({
        id: `issue-${index + 1}`,
        label: item,
        kind: "issue",
        evidence: view.evidence_references || view.evidence_ids || []
      }))
    ];
    content.innerHTML = renderStudioQaQualityGate(view, sourceItems);
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}
