function studioTaskStatusClass(status) {
  if (status === "succeeded") return "good";
  if (["failed", "blocked"].includes(status)) return "bad";
  return "warn";
}

function studioRemediationReadback(sourceStage) {
  const job = state.activeJobStatus || {};
  const pending = job.kind === "remediation" && job.stage === "implement"
    && !["completed", "failed", "cancelled"].includes(job.status || "running");
  const staleStages = (state.dashboard?.stages || []).filter((item) => item.stale);
  if (!pending && !staleStages.length) return "";
  const staleLabels = staleStages.map((item) => stageTitle(item.stage)).join(" → ");
  const invalidators = [...new Set(staleStages.map((item) => item.stale_invalidated_by).filter(Boolean))];
  return `
    <aside class="panel-item studio-remediation-readback" data-remediation-readback="${escapeHtml(sourceStage)}" aria-live="polite">
      <div class="surface-title compact">
        <strong>Remediation readback</strong>
        <span class="small-badge ${pending ? "warn" : "bad"}">${pending ? "implement pending" : "downstream stale"}</span>
      </div>
      ${pending ? `<span>Implement remediation is running for ${escapeHtml(state.activeRunId || "the selected run")}. Durable task and finalization evidence remains authoritative.</span>` : ""}
      ${staleStages.length ? `
        <span>Stale stages: ${escapeHtml(staleLabels)}.</span>
        <span>Invalidated by: ${escapeHtml(invalidators.join(", ") || "durable remediation status")}.</span>
        <span class="form-error">Terminal handoff stays blocked until Review and QA are rerun from fresh evidence.</span>
        <button data-recovery-action="rerun-stale-downstream" type="button" ${selectedRuntimeReady() ? "" : "disabled aria-disabled=\"true\""}>Rerun stale downstream</button>
      ` : ""}
    </aside>
  `;
}

function remediationDraftNote(sourceStage, fallback) {
  if (typeof readRemediationDraft !== "function") return fallback;
  return String(readRemediationDraft(sourceStage)?.value?.text || fallback);
}

function remediationDraftSelection(sourceStage) {
  if (typeof readRemediationDraft !== "function") return new Set();
  return new Set(readRemediationDraft(sourceStage)?.value?.source_ids || []);
}

function renderStudioImplementationTask(task) {
  const attempts = task.attempts || [];
  const runnable = task.ready && task.status !== "succeeded";
  return `
    <article class="panel-item studio-implementation-task" data-task-id="${escapeHtml(task.id)}" data-task-ready="${task.ready ? "true" : "false"}" data-task-status="${escapeHtml(task.status)}">
      <div class="surface-title compact">
        <strong>${escapeHtml(task.id)} · ${escapeHtml(task.title)}</strong>
        <span class="small-badge ${studioTaskStatusClass(task.status)}">${escapeHtml(task.status)}</span>
      </div>
      <span>Dependencies: ${escapeHtml((task.dependencies || []).join(", ") || "none")}</span>
      <span>Attempts: ${escapeHtml(task.attempt_count || 0)}</span>
      ${task.outcome ? `<span>Outcome: ${escapeHtml(task.outcome)}</span>` : ""}
      ${attempts.map((attempt) => `<span data-task-attempt="${escapeHtml(attempt.number)}">Attempt ${escapeHtml(attempt.number)} · ${escapeHtml(attempt.status)} · ${escapeHtml(attempt.path)}</span>`).join("")}
      ${task.blocker ? `<span class="form-error" data-task-blocker>Blocker: ${escapeHtml(task.blocker)}</span>` : ""}
      ${runnable ? `<button data-run-task="${escapeHtml(task.id)}" type="button" ${task.ready && selectedRuntimeReady() ? "" : "disabled aria-disabled=\"true\""}>${task.status === "pending" ? "Run" : "Resume"}</button>` : ""}
    </article>
  `;
}

function renderStudioImplementationQualityGate(taskView) {
  const tasks = taskView?.tasks || [];
  if (!tasks.length) return "";
  const finalization = taskView.finalization || {status: "pending", attempts: []};
  const runnableTasks = tasks.filter((task) => task.ready && task.status !== "succeeded");
  const runnerAction = runnableTasks.length
    ? runnableTasks.length === 1 ? "task run or resume" : "task actions"
    : "implementation finalization";
  return `
    <section class="surface studio-implementation-gate target-implementation-ledger" data-studio-quality-gate="implement" data-review-eligible="${taskView.review_eligible ? "true" : "false"}">
      <div class="target-implementation-ledger-heading">
        <div>
          <p class="eyebrow">Canonical task ledger</p>
          <strong>${escapeHtml(tasks.filter((task) => task.status === "succeeded").length)} tasks completed</strong>
        </div>
        <span class="small-badge">${escapeHtml(tasks.length)} total</span>
      </div>
      <p class="target-implementation-ledger-copy">Task readiness, attempts, blockers, and aggregate finalization come from the canonical task ledger.</p>
      ${(runnableTasks.length || (taskView.finalization_eligible && finalization.status !== "succeeded")) && typeof renderContextualRunnerControl === "function" ? renderContextualRunnerControl({actionLabel: runnerAction}) : ""}
      <details class="target-implementation-ledger-details" open>
        <summary>Task attempts and finalization</summary>
        <div class="compact-list">
          ${tasks.map(renderStudioImplementationTask).join("")}
          <article class="panel-item" data-aggregate-finalization="${escapeHtml(finalization.status || "pending")}">
            <div class="surface-title compact">
              <strong>Aggregate finalization</strong>
              <span class="small-badge ${studioTaskStatusClass(finalization.status)}">${escapeHtml(finalization.status || "pending")}</span>
            </div>
            <span>Attempts: ${escapeHtml(finalization.attempt_count || 0)}</span>
            ${(finalization.attempts || []).map((attempt) => `<span>Finalize ${escapeHtml(attempt.number)} · ${escapeHtml(attempt.status)} · ${escapeHtml(attempt.path)}</span>`).join("")}
            ${finalization.blocker ? `<span class="form-error">Blocker: ${escapeHtml(finalization.blocker)}</span>` : ""}
            ${taskView.finalization_eligible && finalization.status !== "succeeded" ? `<button data-finalize-tasks type="button" ${selectedRuntimeReady() ? "" : "disabled aria-disabled=\"true\""}>${finalization.status === "failed" ? "Resume finalization" : "Finalize"}</button>` : ""}
          </article>
        </div>
      </details>
      ${taskView.review_eligible ? "" : `<div class="next-action-blocker" data-implementation-review-blocker>${escapeHtml(taskView.review_blocker || "Review remains blocked until aggregate finalization succeeds.")}</div>`}
    </section>
  `;
}

function studioRepositoryChangeLabel(status) {
  if (status === "untracked" || status === "added") return "Added";
  if (status === "deleted" || status === "removed") return "Removed";
  return "Changed";
}

function renderStudioRepositoryEvidence({
  diffView,
  evidence,
  taskView,
  files,
  visible,
  selected,
  unchanged,
  reviewEnabled
}) {
  const aiddArtifacts = diffView.aidd_artifacts || [];
  const completedTasks = (taskView?.tasks || []).filter((task) => task.status === "succeeded");
  const insideScope = files.filter((file) => file.allowed_scope_status === "inside");
  const outsideScope = files.filter((file) => file.allowed_scope_status === "outside");
  const scopeNotAuthored = files.filter((file) => file.allowed_scope_status === "not-authored");
  const outsideProjectSet = files.filter((file) => file.scope_status === "outside-project-set");
  const unmentioned = files.filter((file) => !file.mentioned_in_report);
  const truncated = files.filter((file) => file.truncated);
  const mismatchWarnings = [
    ...(diffView.warnings || []),
    ...unchanged.map((path) => `Claim mismatch: ${path} was mentioned but unchanged.`),
    ...files.filter((file) => !file.mentioned_in_report).map(
      (file) => `Claim mismatch: ${file.path} changed but is absent from implementation-report.md.`
    )
  ];
  return `
    <section class="surface studio-repository-evidence" data-document-canvas="implementation-evidence" data-implementation-review>
      <div class="surface-title">
        <span>Repository evidence</span>
        <span class="small-badge">${escapeHtml(files.length)} source changes</span>
      </div>
      <p>Source changes are separated from ${escapeHtml(aiddArtifacts.length)} core-owned <code>.aidd/</code> evidence artifact(s).</p>
      ${diffView.project_set_roots?.length ? `
        <div class="compact-list">
          ${diffView.project_set_roots.map((root) => `<span>${escapeHtml(root.root_id)}: ${escapeHtml(root.relative_root)}</span>`).join("")}
        </div>
      ` : ""}
      ${renderWarnings(mismatchWarnings)}
      ${renderDiffFilters(files)}
      <div class="diff-review-layout">
        <aside class="diff-file-list" aria-label="Changed source files">
          ${visible.length ? visible.map((file) => {
            const selectedClass = selected && selected.path === file.path ? " selected" : "";
            const warnings = diffFileWarning(file);
            const changeLabel = studioRepositoryChangeLabel(file.status);
            return `
              <button data-open-diff-file="${escapeHtml(file.path)}" class="diff-file-card${selectedClass}" type="button">
                <strong>${escapeHtml(file.path)}</strong>
                <span class="repository-change-marker" data-change-kind="${escapeHtml(changeLabel.toLowerCase())}">${escapeHtml(changeLabel)} · ${escapeHtml(file.status)}</span>
                <span>Allowed scope: ${escapeHtml(file.allowed_scope_status)} · Project scope: ${escapeHtml(file.scope_status || "single-project")}</span>
                ${warnings.length ? `<span>${warnings.map((item) => `<span class="small-badge warn">${escapeHtml(item)}</span>`).join("")}</span>` : ""}
              </button>
            `;
          }).join("") : `<div class="empty-state">No files match this filter.</div>`}
        </aside>
        <section class="diff-viewer" aria-label="Selected repository diff">
          ${selected ? `
            <div class="surface-title compact">
              <span>${escapeHtml(selected.path)}</span>
              <span class="small-badge">${escapeHtml(studioRepositoryChangeLabel(selected.status))}</span>
            </div>
            <pre class="diff-pre">${escapeHtml(selected.diff || "No textual diff available.")}</pre>
          ` : `<div class="empty-state">No source diff available.</div>`}
        </section>
      </div>
      <div class="compact-list" data-implementation-claims>
        <span>Report task: ${escapeHtml(evidence?.selected_task_id || "not declared")}</span>
        <span>Reported touched files: ${escapeHtml((evidence?.touched_files || []).length)}</span>
        <span>Repository changed files: ${escapeHtml(files.length)}</span>
      </div>
      <div class="compact-list" data-implementation-completed-claims>
        <strong>Completed task claims from canonical ledger</strong>
        ${completedTasks.length
          ? completedTasks.map((task) => `<span>${escapeHtml(task.id)} · ${escapeHtml(task.title || "completed")}</span>`).join("")
          : `<span class="muted">No completed task claims recorded.</span>`}
      </div>
      <div class="compact-list" data-implementation-scope-coverage>
        <strong>Scope coverage from repository truth</strong>
        <span>Inside allowed scope: ${escapeHtml(insideScope.length)}</span>
        <span>Outside allowed scope: ${escapeHtml(outsideScope.length)}</span>
        <span>Allowed scope not authored: ${escapeHtml(scopeNotAuthored.length)}</span>
        <span>Outside project set: ${escapeHtml(outsideProjectSet.length)}</span>
        <span>Not mentioned in report: ${escapeHtml(unmentioned.length)}</span>
        <span>Truncated previews: ${escapeHtml(truncated.length)}</span>
      </div>
      ${renderImplementationProceedGuard(evidence)}
      <div class="wizard-actions">
        <button data-proceed-stage="review" type="button" ${reviewEnabled ? "" : "disabled aria-disabled=\"true\""}>Proceed to review</button>
        <button data-rerun-implement type="button" class="secondary" ${selectedRuntimeReady() ? "" : "disabled"}>Rerun implement</button>
        <button data-open-request-tab type="button" class="secondary">Request intervention</button>
      </div>
    </section>
  `;
}

function renderStudioReviewQualityGate(view) {
  const findings = view?.findings || [];
  const status = view?.approval_status || "missing";
  const blocked = status !== "approved";
  const findingSummary = (finding) => String(
    finding?.summary || "Finding summary is missing."
  ).replace(/^#{1,6}\s*/, "").trim();
  // Keep canonical upstream fields explicit: finding.acceptance_ids, finding.evidence,
  // and finding.related_paths are never inferred from rendered copy.
  const findingEvidence = (finding) => (finding?.evidence || [])
    .map((item) => String(item)
      .replace(/^(?:[-*]\s*)?Evidence:\s*/i, "")
      .replace(/[\r\n]+/g, " ")
      .replace(/[`]/g, "")
      .replace(/\s+/g, " ")
      .replace(/[.]$/, "")
      .trim())
    .filter(Boolean)
    .join(" · ");
  const draftSelection = remediationDraftSelection("review");
  const defaultNote = "Fix the selected review finding(s), update implementation-report.md, and preserve unrelated changes.";
  const selectedFinding = (finding) => draftSelection.size
    ? draftSelection.has(finding.finding_id)
    : finding.disposition === "must-fix";
  const selectedCount = findings.filter(selectedFinding).length;
  const blockingCount = findings.filter((finding) => ["critical", "high"].includes(finding.severity) || finding.disposition === "must-fix").length;
  const filter = typeof state !== "undefined" ? state.remediationFindingFilter || "all" : "all";
  const visibleFindings = findings.filter((finding) => filter === "selected"
    ? selectedFinding(finding)
    : filter === "blocking"
      ? ["critical", "high"].includes(finding.severity) || finding.disposition === "must-fix"
      : true);
  const paths = [...new Set(findings.flatMap((finding) => finding.related_paths || []))];
  return `
    <section class="surface studio-quality-gate target-remediation-surface" data-studio-quality-gate="review" data-target-remediation-surface="review" data-review-status="${escapeHtml(status)}">
      <div class="target-remediation-heading">
        <div>
          <p class="eyebrow">Review</p>
          <h2>Review findings</h2>
          <p>Inspect source evidence, select the findings that need implementation changes, and keep the remediation request durable.</p>
        </div>
        <span class="small-badge ${status === "approved" ? "good" : "bad"}">${escapeHtml(status)}</span>
      </div>
      ${renderWarnings(view?.warnings || [])}
      ${studioRemediationReadback("review")}
      ${blocked ? `<div class="next-action-blocker" data-quality-gate-blocker>Review is ${escapeHtml(status)}; QA progression remains blocked by the canonical report.</div>` : ""}
      <div class="target-remediation-layout">
        <main class="target-remediation-main" aria-label="Review findings and source evidence">
          <div class="target-remediation-filters" role="group" aria-label="Review finding filters">
            <button type="button" data-remediation-filter="all" aria-pressed="${filter === "all" ? "true" : "false"}">All <span>${escapeHtml(findings.length)}</span></button>
            <button type="button" data-remediation-filter="selected" aria-pressed="${filter === "selected" ? "true" : "false"}">Selected <span>${escapeHtml(selectedCount)}</span></button>
            <button type="button" data-remediation-filter="blocking" aria-pressed="${filter === "blocking" ? "true" : "false"}">Blocking <span>${escapeHtml(blockingCount)}</span></button>
          </div>
          <section class="target-findings-table" data-review-findings aria-label="Review findings">
            <div class="target-findings-table-head" aria-hidden="true"><span></span><span>Finding</span><span>Severity</span><span>Source</span><span>Reviewer evidence</span></div>
            ${visibleFindings.length ? visibleFindings.map((finding, index) => `
              <article class="target-finding-row panel-item" data-review-finding="${escapeHtml(finding.finding_id)}" data-finding-severity="${escapeHtml(finding.severity || "unknown")}" data-finding-selected="${selectedFinding(finding) ? "true" : "false"}">
                <label class="target-finding-select"><input id="studio-review-remediation-${index}" name="review_remediation" data-remediation-source="review" type="checkbox" value="${escapeHtml(finding.finding_id)}" ${selectedFinding(finding) ? "checked" : ""}><span class="sr-only">Select ${escapeHtml(finding.finding_id)} for remediation</span></label>
                <div class="target-finding-copy"><strong>${escapeHtml(findingSummary(finding))}</strong><small>${escapeHtml(finding.disposition || "Disposition not recorded")}</small></div>
                <span class="target-finding-severity"><span class="small-badge ${["critical", "high"].includes(finding.severity) ? "bad" : "warn"}">${escapeHtml(finding.severity || "missing severity")}</span></span>
                <a href="#${escapeHtml(finding.finding_id)}" class="target-finding-source">${escapeHtml((finding.related_paths || [])[0] || "source unavailable")}</a>
                <span class="target-finding-evidence">${escapeHtml(findingEvidence(finding) || "not referenced")} · Acceptance: ${escapeHtml((finding.acceptance_ids || []).join(", ") || "not referenced")}</span>
                <div class="target-finding-details" id="${escapeHtml(finding.finding_id)}" data-remediation-source-evidence><span>Source evidence: ${escapeHtml(findingEvidence(finding) || "not referenced")}</span><span>Evidence: ${escapeHtml(findingEvidence(finding) || "not referenced")}</span><span>Related paths: ${escapeHtml((finding.related_paths || []).join(", ") || "not referenced")}</span><span>Acceptance: ${escapeHtml((finding.acceptance_ids || []).join(", ") || "not referenced")}</span></div>
              </article>
            `).join("") : `<div class="empty-state">No structured Review findings were published.</div>`}
          </section>
          <div class="target-remediation-evidence-grid" data-remediation-evidence-canvas>
            <section class="target-evidence-card" aria-label="Source evidence"><h3>Source evidence</h3>${paths.length ? paths.map((path) => `<span>▧ ${escapeHtml(path)}</span>`).join("") : `<span class="muted">No source paths recorded.</span>`}</section>
            <section class="target-evidence-card" aria-label="Relevant evidence"><h3>Relevant evidence</h3>${findings.length ? findings.slice(0, 6).map((finding) => `<span>${escapeHtml(finding.finding_id)} · ${escapeHtml(findingEvidence(finding) || "not referenced")}</span>`).join("") : `<span class="muted">No retained finding evidence.</span>`}</section>
          </div>
        </main>
        <aside class="target-remediation-request" aria-label="Remediation request">
          <div class="target-remediation-request-heading"><h3>Remediation request</h3><span class="small-badge">${escapeHtml(selectedCount)} selected</span></div>
          <div class="target-editor-tabs" role="tablist" aria-label="Remediation draft mode"><button class="target-editor-tab active" type="button" role="tab" aria-selected="true">Write</button><button class="target-editor-tab" type="button" role="tab" aria-selected="false">Preview</button></div>
          <label class="form-field" for="reviewRemediationNote"><span>Markdown</span><textarea id="reviewRemediationNote" name="review_remediation_note" data-remediation-note="review" rows="8">${escapeHtml(remediationDraftNote("review", defaultNote))}</textarea></label>
          ${typeof renderRemediationDraftPreview === "function" ? renderRemediationDraftPreview("review", {destination: typeof remediationDraftDestination === "function" ? remediationDraftDestination() : "remediations/<run>/request-####.md"}) : ""}
          <div class="target-remediation-destination"><span>Destination</span><code>${escapeHtml(typeof remediationDraftDestination === "function" ? remediationDraftDestination() : "remediations/<run>/request-####.md")}</code><small>Draft is retained in this browser session until it is written.</small></div>
          <div class="target-remediation-impact"><strong>Downstream impact</strong><span>Sending this request marks Review and QA stale until Implement is rerun from fresh evidence.</span><span>Request Change stays separate from remediation.</span></div>
          ${renderRemediationRuntimeGuard("review", Boolean(findings.length))}
          ${findings.length && typeof renderContextualRunnerControl === "function" ? renderContextualRunnerControl({actionLabel: "review remediation"}) : ""}
          <div class="target-remediation-actions">
            <button data-remediation-launch="review" data-aidd-primary-action type="button" ${findings.length && selectedRuntimeReady() ? "" : "disabled"}>Send selected to Implement</button>
            <button data-proceed-stage="qa" type="button" class="secondary" ${status === "approved" && selectedRuntimeReady() ? "" : "disabled aria-disabled=\"true\""}>Proceed to QA</button>
            <button data-open-request-tab type="button" class="link-button">Request change</button>
          </div>
        </aside>
      </div>
    </section>
  `;
}

function renderStudioQaQualityGate(view, sourceItems) {
  const verdict = view?.quality_verdict || "missing";
  const risks = view?.residual_risks || [];
  const issues = view?.known_issues || [];
  const blocked = !["ready", "ready-with-risks"].includes(verdict);
  const draftSelection = remediationDraftSelection("qa");
  const defaultNote = "Fix the selected QA risk(s) or issue(s), rerun verification, and update implementation-report.md.";
  const selectedItem = (item) => draftSelection.size
    ? draftSelection.has(item.id)
    : verdict === "not-ready";
  const selectedCount = sourceItems.filter(selectedItem).length;
  const blockingCount = sourceItems.filter((item) => item.kind === "risk").length;
  const filter = typeof state !== "undefined" ? state.remediationFindingFilter || "all" : "all";
  const visibleItems = sourceItems.filter((item) => filter === "selected"
    ? selectedItem(item)
    : filter === "blocking"
      ? item.kind === "risk"
      : true);
  return `
    <section class="surface studio-quality-gate target-remediation-surface" data-studio-quality-gate="qa" data-target-remediation-surface="qa" data-qa-verdict="${escapeHtml(verdict)}">
      <div class="target-remediation-heading">
        <div>
          <p class="eyebrow">Quality assurance</p>
          <h2>QA findings</h2>
          <p>Keep risks, known issues, source evidence, and the next remediation action in one bounded decision surface.</p>
        </div>
        <span class="small-badge ${blocked ? "bad" : risks.length || issues.length ? "warn" : "good"}">${escapeHtml(verdict)}</span>
      </div>
      ${renderWarnings(view?.warnings || [])}
      ${studioRemediationReadback("qa")}
      ${blocked ? `<div class="next-action-blocker" data-quality-gate-blocker>QA verdict is ${escapeHtml(verdict)}; terminal progression remains blocked by the canonical report.</div>` : ""}
      <div class="target-qa-summary" data-qa-summary>
        <div><span>Recommendation</span><strong>${escapeHtml(view?.release_recommendation || "missing")}</strong></div>
        <div><span>Residual risks</span><strong>${escapeHtml(risks.length)}</strong></div>
        <div><span>Known issues</span><strong>${escapeHtml(issues.length)}</strong></div>
        <div><span>Acceptance IDs</span><strong>${escapeHtml((view?.acceptance_ids || []).length)}</strong></div>
      </div>
      <div class="target-remediation-layout target-qa-remediation-layout">
        <main class="target-remediation-main" aria-label="QA findings and evidence">
          <div class="target-remediation-filters" role="group" aria-label="QA finding filters">
            <button type="button" data-remediation-filter="all" aria-pressed="${filter === "all" ? "true" : "false"}">All <span>${escapeHtml(sourceItems.length)}</span></button>
            <button type="button" data-remediation-filter="selected" aria-pressed="${filter === "selected" ? "true" : "false"}">Selected <span>${escapeHtml(selectedCount)}</span></button>
            <button type="button" data-remediation-filter="blocking" aria-pressed="${filter === "blocking" ? "true" : "false"}">Blocking <span>${escapeHtml(blockingCount)}</span></button>
          </div>
          <section class="target-findings-table" data-qa-remediation-items aria-label="QA findings">
            <div class="target-findings-table-head" aria-hidden="true"><span></span><span>Finding</span><span>Type</span><span>Source</span><span>Evidence</span></div>
            ${visibleItems.length ? visibleItems.map((item, index) => `
              <article class="target-finding-row panel-item" data-qa-remediation-item="${escapeHtml(item.id)}" data-finding-selected="${selectedItem(item) ? "true" : "false"}">
                <label class="target-finding-select"><input id="studio-qa-remediation-${index}" name="qa_remediation" data-remediation-source="qa" type="checkbox" value="${escapeHtml(item.id)}" ${selectedItem(item) ? "checked" : ""}><span class="sr-only">Select ${escapeHtml(item.label)} for remediation</span></label>
                <div class="target-finding-copy"><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(item.kind)}</small></div>
                <span class="target-finding-severity"><span class="small-badge ${item.kind === "risk" ? "bad" : "warn"}">${escapeHtml(item.kind)}</span></span>
                <span class="target-finding-source">QA report</span>
                <span class="target-finding-evidence" data-remediation-source-evidence>Source evidence: ${escapeHtml((item.evidence || []).join(", ") || "not referenced")}</span>
              </article>
            `).join("") : `<div class="empty-state">No QA risks or known issues were published.</div>`}
          </section>
          <section class="target-evidence-card target-qa-upstream" data-qa-upstream-references data-remediation-evidence-canvas aria-label="QA evidence"><h3>Acceptance and evidence</h3><span>Acceptance: ${escapeHtml((view?.acceptance_ids || []).join(", ") || "not referenced")}</span><span>Evidence: ${escapeHtml((view?.evidence_references || view?.evidence_ids || []).join(", ") || "not referenced")}</span></section>
          <div class="sr-only" data-qa-risks>${risks.map((risk) => `<span>Residual risk · ${escapeHtml(risk)}</span>`).join("")} ${issues.map((issue) => `<span>Known issue · ${escapeHtml(issue)}</span>`).join("")}</div>
        </main>
        <aside class="target-remediation-request" aria-label="QA remediation request">
          <div class="target-remediation-request-heading"><h3>Remediation request</h3><span class="small-badge">${escapeHtml(selectedCount)} selected</span></div>
          <div class="target-editor-tabs" role="tablist" aria-label="QA remediation draft mode"><button class="target-editor-tab active" type="button" role="tab" aria-selected="true">Write</button><button class="target-editor-tab" type="button" role="tab" aria-selected="false">Preview</button></div>
          <label class="form-field" for="qaRemediationNote"><span>Markdown</span><textarea id="qaRemediationNote" name="qa_remediation_note" data-remediation-note="qa" rows="8">${escapeHtml(remediationDraftNote("qa", defaultNote))}</textarea></label>
          ${typeof renderRemediationDraftPreview === "function" ? renderRemediationDraftPreview("qa", {destination: typeof remediationDraftDestination === "function" ? remediationDraftDestination() : "remediations/<run>/request-####.md"}) : ""}
          <div class="target-remediation-destination"><span>Destination</span><code>${escapeHtml(typeof remediationDraftDestination === "function" ? remediationDraftDestination() : "remediations/<run>/request-####.md")}</code><small>Draft is retained in this browser session until it is written.</small></div>
          <div class="target-remediation-impact"><strong>Downstream impact</strong><span>Sending this request returns the Work Item to Implement and makes fresh QA evidence necessary.</span></div>
          ${renderRemediationRuntimeGuard("qa", Boolean(sourceItems.length))}
          ${renderQaCompletionGuard(view, Boolean(sourceItems.length))}
          ${sourceItems.length && typeof renderContextualRunnerControl === "function" ? renderContextualRunnerControl({actionLabel: "QA remediation"}) : ""}
          <div class="target-remediation-actions">
            <button data-remediation-launch="qa" data-aidd-primary-action type="button" ${sourceItems.length && selectedRuntimeReady() ? "" : "disabled"}>Send selected to Implement</button>
            <button data-accept-qa type="button" class="secondary" ${blocked ? "disabled aria-disabled=\"true\"" : ""}>Accept complete</button>
            <button data-next-flow-start type="button" class="link-button">Start follow-up</button>
          </div>
        </aside>
      </div>
    </section>
  `;
}
