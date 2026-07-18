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

function renderActiveStudioContextBar(studioState, item) {
  const dashboard = state.dashboard || {};
  const run = dashboard.run || {};
  return `
    <header class="surface studio-context-bar" data-studio-context-bar>
      <div>
        <p class="eyebrow">Document &amp; Evidence Studio</p>
        <h2>${escapeHtml(stageTitle(state.activeStage))}</h2>
        <p class="muted">${escapeHtml(item?.subtitle || stageSubtitle(state.activeStage))}</p>
      </div>
      <dl class="studio-context-identity">
        <div><dt>Work item</dt><dd>${escapeHtml(dashboard.work_item || "unknown")}</dd></div>
        <div><dt>Run</dt><dd>${escapeHtml(run.run_id || "not started")}</dd></div>
        <div><dt>Stage</dt><dd>${escapeHtml(state.activeStage)}</dd></div>
        <div><dt>Status</dt><dd>${escapeHtml(activeStudioStateLabel(studioState, item))}</dd></div>
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

function renderActiveStudio() {
  const item = activeStageItem();
  const studioState = activeStudioState();
  return `
    <section class="active-studio" data-studio-surface="active-studio" data-state="${escapeHtml(studioState)}">
      ${renderActiveStudioContextBar(studioState, item)}
      <div class="active-studio-grid">
        ${renderActiveStudioDocumentSlot(studioState)}
        ${renderActiveStudioStageSummary(item)}
      </div>
    </section>
  `;
}

function applyActiveStudioShellPresentation() {
  const resolution = resolveSurfaceRenderer("active-studio");
  const studio = resolution.presentation === "studio";
  const cockpit = document.querySelector(".cockpit");
  const stageRail = document.getElementById("stageRail");
  const decision = document.getElementById("globalNextActionStrip");
  if (cockpit) cockpit.dataset.activeStudio = studio ? "true" : "false";
  if (stageRail) stageRail.dataset.studioStageNavigation = studio ? "true" : "false";
  if (decision) decision.dataset.studioDecisionSlot = studio ? "true" : "false";
}
