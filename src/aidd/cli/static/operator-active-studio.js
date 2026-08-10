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

const INTENT_PHASES = Object.freeze([
  Object.freeze({id: "understand", label: "Understand", stages: ["idea", "research"]}),
  Object.freeze({id: "decide", label: "Decide", stages: ["plan", "review-spec"]}),
  Object.freeze({id: "deliver", label: "Deliver", stages: ["tasklist", "implement"]}),
  Object.freeze({id: "prove", label: "Prove", stages: ["review", "qa"]})
]);

function activeIntentSummary() {
  const workItem = state.dashboard?.work_item || state.activeRouteWorkItem || "";
  return state.projectHome?.selected_work_item_resume?.intent
    || (state.projectHome?.work_items || []).find((item) => item.work_item === workItem)?.intent
    || null;
}

function phaseStatus(phase, stages) {
  const items = phase.stages.map((stage) => stages.find((item) => item.stage === stage)).filter(Boolean);
  if (!items.length) return "pending";
  if (items.some((item) => ["blocked", "failed", "cancelled"].includes(item.status))) return "blocked";
  if (items.some((item) => ["preparing", "executing", "validating"].includes(item.status))) return "active";
  if (items.every((item) => item.status === "succeeded")) return "complete";
  if (items.some((item) => item.status !== "pending")) return "ready";
  return "pending";
}

function phaseFocusStage(phase, stages) {
  const active = phase.stages.find((stage) => stage === state.activeStage);
  if (active) return active;
  const current = [...phase.stages].reverse().find((stage) => {
    const item = stages.find((candidate) => candidate.stage === stage);
    return item && item.status !== "pending";
  });
  return current || phase.stages[0];
}

function renderIntentPhaseStepper() {
  const stages = state.dashboard?.stages || [];
  const phases = state.dashboard?.phases?.length
    ? state.dashboard.phases
    : INTENT_PHASES.map((phase) => ({...phase, phase_id: phase.id}));
  return `
    <section class="surface intent-phase-stepper" data-intent-phase-stepper aria-label="Intent delivery phases">
      <div class="surface-title"><span>Delivery path</span><span class="small-badge">4 phases</span></div>
      <ol class="intent-phase-list">
        ${phases.map((phase, index) => {
          const status = phase.status || phaseStatus(phase, stages);
          const focusStage = phaseFocusStage(phase, stages);
          const current = phase.stages.includes(state.activeStage);
          return `
            <li>
              <button class="intent-phase-step ${escapeHtml(status)}${current ? " active" : ""}" data-stage="${escapeHtml(focusStage)}" type="button" aria-current="${current ? "step" : "false"}">
                <span class="intent-phase-index">${index + 1}</span>
                <span><strong>${escapeHtml(phase.label)}</strong><small>${escapeHtml(phase.stages.map(stageTitle).join(" · "))}</small></span>
              </button>
            </li>
          `;
        }).join("")}
      </ol>
    </section>
  `;
}

function renderActiveStudioContextBar(studioState, item) {
  const dashboard = state.dashboard || {};
  const intent = activeIntentSummary();
  const intentExcerpt = intent?.excerpt || "Capture the desired outcome before starting delivery.";
  const currentPhase = INTENT_PHASES.find((phase) => phase.stages.includes(state.activeStage));
  return `
    <header class="surface studio-context-bar" data-studio-context-bar>
      <div>
        <p class="eyebrow">Intent Workspace</p>
        <h2>${escapeHtml(intentExcerpt)}</h2>
        <p class="muted">${escapeHtml(currentPhase?.label || "Capture")} · ${escapeHtml(activeStudioStateLabel(studioState, item))}</p>
      </div>
      <dl class="studio-context-identity">
        <div><dt>Current status</dt><dd>${escapeHtml(activeStudioStateLabel(studioState, item))}</dd></div>
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

function renderStudioDocumentRail(studioState) {
  if (studioState === "no-run") return "";
  const refs = (state.dashboard?.recent_artifacts || [])
    .filter((ref) => !ref.stage || ref.stage === state.activeStage)
    .slice(0, 8);
  return `
    <aside class="studio-document-rail" aria-label="Stage documents">
      <div class="studio-document-rail-header">
        <span>Documents</span>
        <span class="small-badge">${escapeHtml(refs.length)}</span>
      </div>
      <div class="studio-document-list">
        ${refs.length ? refs.map((ref) => `
          <button class="studio-document-item${ref.key === state.activeArtifactKey ? " active" : ""}" data-artifact-stage="${escapeHtml(ref.stage || state.activeStage)}" data-artifact-key="${escapeHtml(ref.key)}" data-artifact-kind="${escapeHtml(ref.kind || "document")}" type="button">
            <span class="studio-document-icon" aria-hidden="true">▤</span>
            <span><strong>${escapeHtml(ref.label || ref.key || "Document")}</strong><small>${escapeHtml(ref.path || ref.kind || "stage document")}</small></span>
          </button>
        `).join("") : `<p class="muted studio-document-empty">No stage documents yet.</p>`}
      </div>
      <details class="studio-document-details">
        <summary>Technical details</summary>
        <p>Canonical Markdown, validator evidence, and runtime provenance remain available through the evidence view.</p>
      </details>
    </aside>
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

function renderActiveStudioRuntimeReadiness() {
  const runtime = selectedRuntimeView();
  return `
    <section class="surface studio-runtime-readiness" data-studio-runtime-readiness>
      <div class="surface-title"><span>Runtime launch context</span><span class="small-badge">${escapeHtml(runtime?.runtime_id || "not selected")}</span></div>
      ${runtime
        ? renderRuntimeReadinessDimensions(runtime)
        : '<p class="muted">Select a runtime to inspect launch dimensions.</p>'}
      ${renderProtectedWriteScope()}
    </section>
  `;
}

function studioObservationModel(job = state.activeJobStatus, item = activeStageItem()) {
  const attemptCount = Number(item?.attempt_count || 0);
  if (!job && !attemptCount && !["executing", "preparing", "validating"].includes(item?.status)) {
    return null;
  }
  if (job) {
    const cancelling = job.status === "cancelling" || job.cancel_state === "cancelling";
    return {
      source: "ui-job",
      status: job.status || "running",
      stage: job.stage || state.activeStage,
      elapsed: secondsLabel(job.elapsed_seconds),
      outputAge: runtimeOutputFreshnessLabel(job),
      milestone: `${stageTitle(job.stage || state.activeStage)} / ${item?.status || job.status || "running"}`,
      notice: cancelling
        ? "Cancellation requested; waiting for terminal runtime evidence."
        : job.silence_warning
          ? runtimeOutputMissingLabel(job)
          : "Live runtime evidence is updating.",
      tone: cancelling || job.silence_warning ? "warn" : "good",
      actionLabel: "Open live output"
    };
  }
  const externallyRunning = ["executing", "preparing", "validating"].includes(item?.status);
  return {
    source: externallyRunning ? "durable-external" : "durable-attempt",
    status: item?.status || "recorded",
    stage: item?.stage || state.activeStage,
    elapsed: "not available",
    outputAge: attemptCount ? "Persisted runtime evidence available" : "No output evidence recorded",
    milestone: `${stageTitle(item?.stage || state.activeStage)} / ${item?.status || "recorded"} / attempt ${attemptCount || "pending"}`,
    notice: externallyRunning
      ? "The stage is executing outside this browser session; durable state is authoritative."
      : "The latest terminal stage state is reconstructed from persisted evidence.",
    tone: ["failed", "blocked", "cancelled"].includes(item?.status) ? "warn" : "good",
    actionLabel: "Open persisted logs"
  };
}

function renderStudioLiveObservation() {
  const observation = studioObservationModel();
  if (!observation) return "";
  return `
    <section class="surface studio-live-observation" data-studio-observation="${escapeHtml(observation.source)}" role="status" aria-live="polite">
      <div class="surface-title">
        <span>Runtime observation</span>
        <span class="small-badge ${escapeHtml(observation.tone)}">${escapeHtml(observation.status)}</span>
      </div>
      <div class="metric-grid compact">
        <div class="metric"><span>Elapsed</span><strong>${escapeHtml(observation.elapsed)}</strong></div>
        <div class="metric"><span>Last output</span><strong>${escapeHtml(observation.outputAge)}</strong></div>
        <div class="metric"><span>Milestone</span><strong>${escapeHtml(observation.milestone)}</strong></div>
        <div class="metric"><span>Connection</span><strong>${escapeHtml(state.activeJobConnection?.state || "durable")}</strong></div>
      </div>
      <p>${escapeHtml(observation.notice)}</p>
      <button data-tab-shortcut="logs" type="button" class="secondary">${escapeHtml(observation.actionLabel)}</button>
    </section>
  `;
}

function updateStudioLiveObservation() {
  const host = document.getElementById("studioLiveObservation");
  if (!host) return;
  const markup = renderStudioLiveObservation();
  host.hidden = !markup;
  host.innerHTML = markup;
}

function renderActiveStudio() {
  if (state.nextFlowWizard.active) {
    return renderStudioNextFlowWizard();
  }
  if (state.dashboard?.terminal_handoff) {
    const {eligible} = studioFlowCompleteEligibility();
    if (eligible) {
      return renderStudioFlowCompleteState();
    }
  }
  const item = activeStageItem();
  const studioState = activeStudioState();
  return `
    <section class="active-studio" data-studio-surface="active-studio" data-state="${escapeHtml(studioState)}">
      ${renderActiveStudioContextBar(studioState, item)}
      ${renderIntentPhaseStepper()}
      ${typeof workflowProgressSummary === "function" ? workflowProgressSummary({collapsed: true}) : ""}
      <div class="active-studio-grid">
        ${renderStudioDocumentRail(studioState)}
        ${renderActiveStudioDocumentSlot(studioState)}
        ${studioState === "no-run" ? "" : `
          <div class="studio-reading-sidebar">
            ${renderActiveStudioStageSummary(item)}
            <aside id="studioEvidenceInspector" class="surface studio-evidence-inspector" hidden></aside>
          </div>
        `}
      </div>
      <div id="studioLiveObservation">${renderStudioLiveObservation()}</div>
      ${renderActiveStudioRuntimeReadiness()}
    </section>
  `;
}

function applyActiveStudioShellPresentation() {
  const content = document.getElementById("intentContent");
  const phases = document.getElementById("intentPhaseStepper");
  const decision = document.getElementById("intentDecisionSurface");
  if (content) content.dataset.activeStudio = "true";
  if (phases) phases.dataset.studioPhaseNavigation = "true";
  if (decision) decision.dataset.studioDecisionSlot = "true";
}
