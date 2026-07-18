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
