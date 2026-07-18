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

function renderStudioReviewQualityGate(view) {
  const findings = view?.findings || [];
  const status = view?.approval_status || "missing";
  const blocked = status !== "approved";
  return `
    <section class="surface studio-quality-gate" data-studio-quality-gate="review" data-review-status="${escapeHtml(status)}">
      <div class="surface-title">
        <span>Review quality gate</span>
        <span class="small-badge ${status === "approved" ? "good" : "bad"}">${escapeHtml(status)}</span>
      </div>
      ${renderWarnings(view?.warnings || [])}
      ${studioRemediationReadback("review")}
      ${blocked ? `<div class="next-action-blocker" data-quality-gate-blocker>Review is ${escapeHtml(status)}; QA progression remains blocked by the canonical report.</div>` : ""}
      <div class="compact-list" data-review-findings>
        ${findings.length ? findings.map((finding, index) => `
          <article class="panel-item" data-review-finding="${escapeHtml(finding.finding_id)}">
            <div class="surface-title compact">
              <strong>${escapeHtml(finding.finding_id)}</strong>
              <span class="small-badge ${["critical", "high"].includes(finding.severity) ? "bad" : "warn"}">${escapeHtml(finding.severity || "missing severity")}</span>
              <span class="small-badge">${escapeHtml(finding.disposition || "missing disposition")}</span>
            </div>
            <p>${escapeHtml(finding.summary || "Finding summary is missing.")}</p>
            <span>Acceptance: ${escapeHtml((finding.acceptance_ids || []).join(", ") || "not referenced")}</span>
            <span>Evidence: ${escapeHtml((finding.evidence || []).join(" · ") || "not referenced")}</span>
            <span>Paths: ${escapeHtml((finding.related_paths || []).join(", ") || "not referenced")}</span>
            <label><input id="studio-review-remediation-${index}" name="review_remediation" data-remediation-source="review" type="checkbox" value="${escapeHtml(finding.finding_id)}" ${finding.disposition === "must-fix" ? "checked" : ""}> Select for remediation</label>
          </article>
        `).join("") : `<div class="empty-state">No structured Review findings were published.</div>`}
      </div>
      <label class="form-field" for="reviewRemediationNote">
        <span>Operator note for implement</span>
        <textarea id="reviewRemediationNote" name="review_remediation_note" data-remediation-note="review" rows="4">Fix the selected review finding(s), update implementation-report.md, and preserve unrelated changes.</textarea>
      </label>
      ${renderRemediationRuntimeGuard("review", Boolean(findings.length))}
      <div class="wizard-actions">
        <button data-proceed-stage="qa" type="button" ${status === "approved" && selectedRuntimeReady() ? "" : "disabled aria-disabled=\"true\""}>Proceed to QA</button>
        <button data-remediation-launch="review" type="button" ${findings.length && selectedRuntimeReady() ? "" : "disabled"}>Send selected to implement</button>
        <button data-open-request-tab type="button" class="secondary">Request review intervention</button>
      </div>
    </section>
  `;
}

function renderStudioQaQualityGate(view, sourceItems) {
  const verdict = view?.quality_verdict || "missing";
  const risks = view?.residual_risks || [];
  const issues = view?.known_issues || [];
  const blocked = !["ready", "ready-with-risks"].includes(verdict);
  return `
    <section class="surface studio-quality-gate" data-studio-quality-gate="qa" data-qa-verdict="${escapeHtml(verdict)}">
      <div class="surface-title">
        <span>QA quality gate</span>
        <span class="small-badge ${blocked ? "bad" : risks.length || issues.length ? "warn" : "good"}">${escapeHtml(verdict)}</span>
      </div>
      ${renderWarnings(view?.warnings || [])}
      ${studioRemediationReadback("qa")}
      ${blocked ? `<div class="next-action-blocker" data-quality-gate-blocker>QA verdict is ${escapeHtml(verdict)}; terminal progression remains blocked by the canonical report.</div>` : ""}
      <div class="metric-grid">
        <div class="metric"><span>Recommendation</span><strong>${escapeHtml(view?.release_recommendation || "missing")}</strong></div>
        <div class="metric"><span>Residual risks</span><strong>${escapeHtml(risks.length)}</strong></div>
        <div class="metric"><span>Known issues</span><strong>${escapeHtml(issues.length)}</strong></div>
        <div class="metric"><span>Acceptance IDs</span><strong>${escapeHtml((view?.acceptance_ids || []).length)}</strong></div>
      </div>
      <div class="compact-list" data-qa-upstream-references>
        <span>Acceptance: ${escapeHtml((view?.acceptance_ids || []).join(", ") || "not referenced")}</span>
        <span>Evidence: ${escapeHtml((view?.evidence_references || view?.evidence_ids || []).join(", ") || "not referenced")}</span>
      </div>
      <div class="compact-list" data-qa-risks>
        ${risks.map((risk) => `<span>Residual risk · ${escapeHtml(risk)}</span>`).join("") || "<span>No residual risks published.</span>"}
        ${issues.map((issue) => `<span>Known issue · ${escapeHtml(issue)}</span>`).join("") || "<span>No known issues published.</span>"}
      </div>
      <div class="compact-list" data-qa-remediation-items>
        ${sourceItems.map((item, index) => `<label><input id="studio-qa-remediation-${index}" name="qa_remediation" data-remediation-source="qa" type="checkbox" value="${escapeHtml(item.id)}" ${verdict === "not-ready" ? "checked" : ""}> ${escapeHtml(item.kind)} · ${escapeHtml(item.label)}</label>`).join("")}
      </div>
      <label class="form-field" for="qaRemediationNote">
        <span>Operator note for implement</span>
        <textarea id="qaRemediationNote" name="qa_remediation_note" data-remediation-note="qa" rows="4">Fix the selected QA risk(s) or issue(s), rerun verification, and update implementation-report.md.</textarea>
      </label>
      ${renderRemediationRuntimeGuard("qa", Boolean(sourceItems.length))}
      ${renderQaCompletionGuard(view, Boolean(sourceItems.length))}
      <div class="wizard-actions">
        <button data-accept-qa type="button" ${blocked ? "disabled aria-disabled=\"true\"" : ""}>Accept complete</button>
        <button data-remediation-launch="qa" type="button" ${sourceItems.length && selectedRuntimeReady() ? "" : "disabled"}>Send selected to implement</button>
        <button data-next-flow-start type="button" class="secondary">Start follow-up</button>
      </div>
    </section>
  `;
}
