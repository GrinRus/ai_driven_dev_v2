function historyFrameLabel(frame) {
  if (frame.kind === "task-attempt") {
    return `${frame.task_id} · attempt ${frame.attempt_number}`;
  }
  if (frame.kind === "finalization-attempt") {
    return `Aggregate finalization · attempt ${frame.attempt_number}`;
  }
  if (frame.kind === "stage-attempt") {
    return `${stageTitle(frame.stage)} · attempt ${frame.attempt_number}`;
  }
  return `${stageTitle(frame.stage || "run")} · ${frame.status}`;
}

function historyFrameTone(status) {
  if (["succeeded", "success", "present", "indexed"].includes(status)) return "good";
  if (["failed", "blocked", "cancelled", "timeout"].includes(status)) return "bad";
  return "warn";
}

async function loadStudioHistoryTimeline() {
  if (!state.activeRunId) {
    state.historyTimeline = null;
    return null;
  }
  const timeline = await api(`/api/run/timeline?${runScopedQuery()}`);
  state.historyTimeline = timeline;
  if (state.historyAutoFollow && (timeline.frames || []).length) {
    state.historySelectedFrame = timeline.frames.at(-1).identity;
  }
  return timeline;
}

function selectedHistoryFrame(timeline) {
  const frames = timeline?.frames || [];
  return frames.find((frame) => frame.identity === state.historySelectedFrame)
    || frames.at(-1)
    || null;
}

function renderHistoryFrameButton(frame) {
  const selected = frame.identity === state.historySelectedFrame;
  return `
    <button class="history-frame ${selected ? "selected" : ""}" data-history-frame="${escapeHtml(frame.identity)}" type="button" aria-pressed="${selected ? "true" : "false"}">
      <span class="small-badge ${historyFrameTone(frame.status)}">${escapeHtml(frame.status)}</span>
      <strong>${escapeHtml(historyFrameLabel(frame))}</strong>
      <span>${escapeHtml(frame.time_utc || "time not authored")}</span>
    </button>
  `;
}

function renderHistoryEvidence(frame) {
  const refs = frame?.evidence_refs || [];
  if (!refs.length) {
    return `<div class="empty-state">No retained evidence is attached to this frame.</div>`;
  }
  return refs.map((path) => `
    <button data-history-evidence-path="${escapeHtml(path)}" data-history-evidence-stage="${escapeHtml(frame.stage || state.activeStage)}" type="button" class="artifact-row">
      <span>${escapeHtml(path)}</span>
      <span class="small-badge">${path.endsWith("runtime.log") ? "log" : "artifact"}</span>
    </button>
  `).join("");
}

function historyComparisonReference(path, label) {
  return path
    ? `<span data-comparison-evidence-path="${escapeHtml(path)}">${escapeHtml(path)}</span>`
    : `<span class="small-badge warn">${escapeHtml(label)} snapshot unavailable</span>`;
}

function renderStudioComparisonDelta(kind, item) {
  if (kind === "prompt") {
    return `<span><strong>${escapeHtml(item.path)}</strong> · ${escapeHtml(item.status)}</span>`;
  }
  if (kind === "stage") {
    return `
      <span><strong>${escapeHtml(stageTitle(item.stage))}</strong> · ${escapeHtml(item.status)}</span>
      ${historyComparisonReference(null, item.baseline_status ? "stage evidence" : "baseline")}
      ${historyComparisonReference(null, item.target_status ? "stage evidence" : "target")}
    `;
  }
  const baselinePath = item.baseline_path || null;
  const targetPath = item.target_path || null;
  return `
    <span><strong>${escapeHtml(item.key || item.stage)}</strong> · ${escapeHtml(item.status)}</span>
    ${historyComparisonReference(baselinePath, "baseline")}
    ${historyComparisonReference(targetPath, "target")}
  `;
}

function renderStudioComparisonGroup(label, kind, items) {
  const deltas = (items || []).filter((item) => item.status !== "same");
  return `
    <section data-comparison-group="${escapeHtml(kind)}">
      <div class="surface-title compact">${escapeHtml(label)}</div>
      <div class="compact-list">
        ${deltas.length
          ? deltas.map((item) => `<article class="panel-item">${renderStudioComparisonDelta(kind, item)}</article>`).join("")
          : `<span>No retained ${escapeHtml(label.toLowerCase())} delta.</span>`}
      </div>
    </section>
  `;
}

function renderStudioRunComparisonPanel() {
  const run = state.dashboard?.run || {};
  if (!run.run_id) return "";
  const lineage = run.lineage || {};
  const baselineRunId = comparisonBaselineRunId(run, lineage);
  const comparison = state.runComparison;
  return `
    <section id="runComparisonPanel" class="surface studio-run-comparison" data-studio-run-comparison>
      <div class="surface-title">
        <span>Retained-evidence comparison</span>
        <span class="small-badge">${escapeHtml(baselineRunId || "baseline missing")} → ${escapeHtml(run.run_id)}</span>
      </div>
      <div class="comparison-controls">
        <label for="runComparisonBaseline"><span>Baseline run id</span><input id="runComparisonBaseline" name="comparison_baseline_run" type="text" value="${escapeHtml(baselineRunId)}"></label>
        <button data-run-comparison-refresh type="button" ${state.runComparisonLoading ? "disabled" : ""}>Refresh comparison</button>
      </div>
      ${state.runComparisonError ? `<div class="empty-state bad">${escapeHtml(state.runComparisonError)}. Snapshot unavailable; History will not reconstruct it.</div>` : ""}
      ${state.runComparisonLoading ? `<div class="empty-state loading-state">Loading retained comparison...</div>` : ""}
      ${comparison ? `
        ${renderWarnings(comparison.warnings || [])}
        <div class="terminal-summary-grid">
          ${renderStudioComparisonGroup("Prompt evidence", "prompt", comparison.prompt_hash_deltas)}
          ${renderStudioComparisonGroup("Stage evidence", "stage", comparison.stage_status_deltas)}
          ${renderStudioComparisonGroup("Artifact evidence", "artifact", comparison.artifact_hash_deltas)}
          ${renderStudioComparisonGroup("Validator evidence", "validator", comparison.validator_outcome_deltas)}
        </div>
      ` : !state.runComparisonLoading && !state.runComparisonError
        ? `<div class="empty-state">Choose a retained baseline; no snapshot is reconstructed.</div>`
        : ""}
    </section>
  `;
}

function renderActiveRunComparisonPanel() {
  return resolveSurfaceRenderer("history").presentation === "studio"
    ? renderStudioRunComparisonPanel()
    : renderRunComparisonPanel();
}

function renderStudioHistoryLineageCandidate(candidate, currentRunId) {
  return `
    <article class="lineage-node child" data-history-lineage-child="${escapeHtml(candidate.work_item_id)}">
      <span class="small-badge good">${escapeHtml(candidate.relationship || "child")}</span>
      <strong>${escapeHtml(candidate.label || candidate.work_item_id)}</strong>
      <span>Source run: ${escapeHtml(candidate.source_run_id || currentRunId || "not recorded")}</span>
      <button data-operator-route-intent="child-work-item" data-route-work-item="${escapeHtml(candidate.work_item_id)}" type="button">Open child work item</button>
    </article>
  `;
}

function renderStudioHistoryLineage() {
  const run = state.dashboard?.run || {};
  const lineage = run.lineage || {};
  const candidates = lineage.child_work_item_candidates || [];
  const sourceRun = lineage.source_run_id || "";
  const sourceWorkItem = lineage.source_work_item_id || state.dashboard?.work_item || "";
  const hasParent = Boolean(sourceRun && sourceRun !== run.run_id);
  return `
    <section class="surface studio-history-lineage" data-studio-history-lineage>
      <div class="surface-title">
        <span>Immutable run lineage</span>
        <span class="small-badge">navigation only</span>
      </div>
      <div class="lineage-flow">
        ${hasParent ? `
          <article class="lineage-node parent" data-history-lineage-parent="${escapeHtml(sourceRun)}">
            <span class="small-badge">parent</span>
            <strong>${escapeHtml(sourceRun)}</strong>
            <span>${escapeHtml(lineage.baseline_label || lineage.baseline_id || "source run")}</span>
            <button data-operator-route-intent="parent-run" data-route-work-item="${escapeHtml(sourceWorkItem)}" data-route-run-id="${escapeHtml(sourceRun)}" type="button">Inspect parent run</button>
          </article>
        ` : ""}
        <article class="lineage-node current" data-history-lineage-current="${escapeHtml(run.run_id || "")}">
          <span class="small-badge good">current</span>
          <strong>${escapeHtml(run.run_id || "No selected run")}</strong>
          <span>${escapeHtml(state.dashboard?.work_item || "work item not recorded")}</span>
          ${run.run_id ? `<button data-operator-route-intent="historical-run" data-route-work-item="${escapeHtml(state.dashboard?.work_item || "")}" data-route-run-id="${escapeHtml(run.run_id)}" type="button">Inspect current run</button>` : ""}
        </article>
        <div class="lineage-children">
          ${candidates.length
            ? candidates.map((candidate) => renderStudioHistoryLineageCandidate(candidate, run.run_id)).join("")
            : `<article class="lineage-node pending"><span class="small-badge warn">child</span><strong>No retained child relation</strong><span>History does not infer future lineage.</span></article>`}
        </div>
      </div>
    </section>
  `;
}

function renderStudioHistory(timeline) {
  const frames = timeline?.frames || [];
  if (!frames.length) {
    return `<div class="empty-state">No durable History frames are available for this run.</div>`;
  }
  const selected = selectedHistoryFrame(timeline);
  return `
    <section class="surface studio-history" data-studio-history data-history-auto-follow="${state.historyAutoFollow ? "true" : "false"}">
      <div class="surface-title">
        <span>History Filmstrip</span>
        <span class="small-badge">${escapeHtml(frames.length)} frames</span>
      </div>
      <div class="history-filmstrip-frames" aria-label="Durable run frames">
        ${frames.map(renderHistoryFrameButton).join("")}
      </div>
      <div class="history-selection" data-history-selection="${escapeHtml(selected?.identity || "")}">
        <div class="surface-title compact">
          <strong>${escapeHtml(selected ? historyFrameLabel(selected) : "No frame selected")}</strong>
          <button data-history-return-live type="button" class="secondary" ${state.historyAutoFollow ? "disabled aria-disabled=\"true\"" : ""}>Return to live</button>
        </div>
        <span>Historical selection pauses browser auto-follow only; the active runtime is not stopped.</span>
        <div class="recent-artifacts">${renderHistoryEvidence(selected)}</div>
      </div>
    </section>
    ${renderStudioRunComparisonPanel()}
    ${renderStudioHistoryLineage()}
  `;
}
