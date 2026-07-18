function studioTaskStatusClass(status) {
  if (status === "succeeded") return "good";
  if (["failed", "blocked"].includes(status)) return "bad";
  return "warn";
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
  return `
    <section class="surface studio-implementation-gate" data-studio-quality-gate="implement" data-review-eligible="${taskView.review_eligible ? "true" : "false"}">
      <div class="surface-title">
        <span>Implementation quality gate</span>
        <span class="small-badge">${escapeHtml(tasks.filter((task) => task.status === "succeeded").length)} / ${escapeHtml(tasks.length)} tasks</span>
      </div>
      <p>Task readiness, attempts, blockers, and aggregate finalization come from the canonical task ledger.</p>
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
  files,
  visible,
  selected,
  unchanged,
  reviewEnabled
}) {
  const aiddArtifacts = diffView.aidd_artifacts || [];
  const mismatchWarnings = [
    ...(diffView.warnings || []),
    ...unchanged.map((path) => `Claim mismatch: ${path} was mentioned but unchanged.`),
    ...files.filter((file) => !file.mentioned_in_report).map(
      (file) => `Claim mismatch: ${file.path} changed but is absent from implementation-report.md.`
    )
  ];
  return `
    <section class="surface studio-repository-evidence" data-document-canvas="implementation-evidence">
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
      ${renderImplementationProceedGuard(evidence)}
      <div class="wizard-actions">
        <button data-proceed-stage="review" type="button" ${reviewEnabled ? "" : "disabled aria-disabled=\"true\""}>Proceed to review</button>
        <button data-rerun-implement type="button" class="secondary" ${selectedRuntimeReady() ? "" : "disabled"}>Rerun implement</button>
        <button data-open-request-tab type="button" class="secondary">Request intervention</button>
      </div>
    </section>
  `;
}
