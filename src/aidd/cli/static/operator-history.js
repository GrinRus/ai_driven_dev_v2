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
  if (frame.kind === "event-marker") {
    return frame.event_message || `${stageTitle(frame.stage || "run")} event`;
  }
  return `${stageTitle(frame.stage || "run")} · ${frame.status}`;
}

function historyFrameTone(status) {
  if (["succeeded", "success", "present", "indexed"].includes(status)) return "good";
  if (["failed", "blocked", "cancelled", "timeout"].includes(status)) return "bad";
  return "warn";
}

function primaryHistoryFrames(timeline) {
  const frames = Array.isArray(timeline?.frames) ? timeline.frames : [];
  return frames.filter((frame) => frame.kind !== "event-marker");
}

function historyEventMarkers(timeline) {
  const frames = Array.isArray(timeline?.frames) ? timeline.frames : [];
  return frames.filter((frame) => frame.kind === "event-marker");
}

function historyRunQuery() {
  const params = new URLSearchParams(runScopedQuery());
  if (state.historyStatusFilter) params.set("status", state.historyStatusFilter);
  if (state.historyAttemptModeFilter) params.set("attempt_mode", state.historyAttemptModeFilter);
  return params.toString();
}

function selectedHistoryRun() {
  const runs = Array.isArray(state.historyRuns) ? state.historyRuns : [];
  return runs.find((run) => run.run_id === state.activeRunId) || runs[0] || null;
}

async function loadStudioRunHistory() {
  try {
    const payload = await api(`/api/run/history?${historyRunQuery()}`);
    state.historyRuns = Array.isArray(payload?.runs) ? payload.runs : [];
    state.historyRunsError = "";
    if (!state.activeRunId && payload?.selected_run_id) state.activeRunId = payload.selected_run_id;
  } catch (error) {
    state.historyRuns = [];
    state.historyRunsError = error.message || "Run history unavailable";
  }
  return state.historyRuns;
}

async function loadStudioHistoryTimeline() {
  if (!state.activeRunId) {
    state.historyTimeline = null;
    await loadStudioRunHistory();
    return null;
  }
  const timeline = await api(`/api/run/timeline?${runScopedQuery()}`);
  state.historyTimeline = timeline;
  await loadStudioRunHistory();
  const frames = primaryHistoryFrames(timeline);
  if (state.historyAutoFollow && frames.length) {
    state.historySelectedFrame = frames.at(-1).identity;
  }
  return timeline;
}

function renderHistoryRunList() {
  const runs = Array.isArray(state.historyRuns) ? state.historyRuns : [];
  const modes = [...new Set(runs.flatMap((run) => run.attempt_modes || []))].filter(Boolean);
  return `
    <section class="surface history-run-list" data-history-run-list>
      <div class="surface-title">
        <span>Runs<span class="sr-only"> and Attempts</span></span>
        <span class="small-badge">${escapeHtml(runs.length)} retained runs</span>
      </div>
      <div class="filter-row history-filters" role="group" aria-label="Run history filters">
        <label for="historyStatusFilter"><span>Status</span><select id="historyStatusFilter" data-history-filter="status">
          ${["", "running", "failed", "completed", "created"].map((value) => `<option value="${value}"${state.historyStatusFilter === value ? " selected" : ""}>${value || "All statuses"}</option>`).join("")}
        </select></label>
        <label for="historyAttemptModeFilter"><span>Attempt mode</span><select id="historyAttemptModeFilter" data-history-filter="attempt-mode">
          ${["", ...modes].map((value) => `<option value="${escapeHtml(value)}"${state.historyAttemptModeFilter === value ? " selected" : ""}>${escapeHtml(value || "All modes")}</option>`).join("")}
        </select></label>
      </div>
      ${state.historyRunsError ? `<div class="empty-state bad">${escapeHtml(state.historyRunsError)}</div>` : ""}
      <div class="history-run-table-head" aria-hidden="true"><span>Run ID</span><span>Stage</span><span>Status</span><span>Updated</span><span>Attempts</span></div>
      <div class="history-run-list-items">
        ${runs.length ? runs.map((run) => `
          <button class="history-run-row${run.run_id === state.activeRunId ? " selected" : ""}" data-history-run="${escapeHtml(run.run_id)}" type="button" aria-pressed="${run.run_id === state.activeRunId ? "true" : "false"}">
            <strong class="history-run-id">${escapeHtml(run.run_id)}</strong>
            <span class="history-run-stage">${escapeHtml(stageTitle(run.stage_target || state.activeStage || "run"))}</span>
            <span class="small-badge ${historyFrameTone(run.status)}">${escapeHtml(run.status)}</span>
            <span class="history-run-date">${escapeHtml(run.updated_at_utc || "Timestamp unavailable")}</span>
            <span class="history-run-attempts">${escapeHtml(run.attempt_count || 0)} <small>/ ${escapeHtml(run.retained_attempt_count || 0)} retained</small></span>
            <span class="history-run-runtime">${escapeHtml(run.runtime_id || "runtime unavailable")}</span>
          </button>
        `).join("") : `<div class="empty-state">No retained runs are available for this Work Item.</div>`}
      </div>
    </section>
  `;
}

function selectedHistoryFrame(timeline) {
  const frames = primaryHistoryFrames(timeline);
  return frames.find((frame) => frame.identity === state.historySelectedFrame)
    || frames.at(-1)
    || null;
}

function historyAttemptGroups(frames) {
  const groups = new Map();
  for (const frame of frames || []) {
    const number = Number.isFinite(frame.attempt_number) ? frame.attempt_number : null;
    const key = number === null ? frame.identity : String(number);
    const existing = groups.get(key) || {key, attempt_number: number, frames: []};
    existing.frames.push(frame);
    groups.set(key, existing);
  }
  return [...groups.values()].map((group) => ({
    ...group,
    representative: group.frames.find((frame) => frame.identity === state.historySelectedFrame)
      || group.frames.at(-1),
    statuses: [...new Set(group.frames.map((frame) => frame.status).filter(Boolean))]
  }));
}

function renderHistoryAttemptTabs(frames, selected) {
  const groups = historyAttemptGroups(frames);
  if (!groups.length) return "";
  return `
    <div class="history-attempt-tabs" role="tablist" aria-label="Retained attempts">
      ${groups.map((group, index) => {
        const active = group.frames.some((frame) => frame.identity === selected?.identity);
        const label = group.attempt_number === null ? `Frame ${index + 1}` : `Attempt ${group.attempt_number}`;
        const status = group.statuses.length === 1 ? group.statuses[0] : `${group.statuses.length} states`;
        return `<button class="history-attempt-tab${active ? " active" : ""}" data-history-frame="${escapeHtml(group.representative.identity)}" type="button" role="tab" aria-selected="${active ? "true" : "false"}"><span>${escapeHtml(label)}</span><small class="small-badge ${historyFrameTone(group.representative.status)}">${escapeHtml(status)}</small></button>`;
      }).join("")}
    </div>
  `;
}

function historyFrameDescription(frame) {
  if (!frame) return "No retained attempt selected.";
  if (frame.first_decisive_failure) return frame.first_decisive_failure;
  if (frame.kind === "task-attempt") return `Task ${frame.task_id || "not recorded"} attempt ${frame.attempt_number || "not recorded"} was retained.`;
  if (frame.kind === "finalization-attempt") return `Aggregate finalization attempt ${frame.attempt_number || "not recorded"} was retained.`;
  return `${stageTitle(frame.stage || "run")} attempt ${frame.attempt_number || "not recorded"} was retained.`;
}

function historyFrameTime(frame) {
  const timestamp = frame?.time_utc || frame?.updated_at_utc || frame?.started_at_utc || "Timestamp unavailable";
  const duration = Number.isFinite(frame?.duration_seconds) ? ` · ${Number(frame.duration_seconds).toFixed(1)}s` : "";
  return `${timestamp}${duration}`;
}

function renderHistoryTimeline(timeline, frames, selected) {
  const markers = historyEventMarkers(timeline);
  return `
    <div class="history-timeline-view" data-history-timeline>
      <div class="history-filmstrip-frames history-timeline-list" aria-label="Durable run chronology">
        ${frames.map((frame) => {
          const active = frame.identity === selected?.identity;
          return `<button class="history-frame history-timeline-entry${active ? " selected" : ""}" data-history-frame="${escapeHtml(frame.identity)}" type="button" aria-pressed="${active ? "true" : "false"}"><span class="history-timeline-marker ${historyFrameTone(frame.status)}" aria-hidden="true">${frame.status === "succeeded" || frame.status === "success" ? "✓" : frame.status === "failed" ? "!" : "•"}</span><span class="history-timeline-copy"><strong>${escapeHtml(historyFrameLabel(frame))}</strong><span>${escapeHtml(historyFrameDescription(frame))}</span><small>${escapeHtml(historyFrameTime(frame))}</small></span><span class="small-badge ${historyFrameTone(frame.status)}">${escapeHtml(frame.status)}</span></button>`;
        }).join("")}
      </div>
      ${markers.length ? `
        <details class="history-technical-events">
          <summary>Technical events (${escapeHtml(markers.length)})</summary>
          <div class="history-technical-event-list">
            ${markers.map((frame) => `<button class="history-frame" data-history-frame="${escapeHtml(frame.identity)}" type="button"><strong>${escapeHtml(frame.event_message || historyFrameLabel(frame))}</strong><span>${escapeHtml(frame.time_utc || "Timestamp unavailable")}</span></button>`).join("")}
          </div>
        </details>
      ` : ""}
    </div>
  `;
}

function renderHistoryViewTabs() {
  const activeView = state.historyView || "timeline";
  return `
    <div class="history-view-tabs" role="tablist" aria-label="Selected attempt evidence view">
      ${[["timeline", "Timeline"], ["raw-log", "Raw log"], ["artifacts", "Artifacts"]].map(([value, label]) => `<button class="history-view-tab${activeView === value ? " active" : ""}" data-history-view="${value}" type="button" role="tab" aria-selected="${activeView === value ? "true" : "false"}">${label}</button>`).join("")}
    </div>
  `;
}

function renderSelectedHistoryView(timeline, frames, selected) {
  const refs = selected?.evidence_refs || [];
  const activeView = state.historyView || "timeline";
  if (activeView === "raw-log") {
    const logs = refs.filter((path) => path.endsWith("runtime.log"));
    return `<section class="history-evidence-view" data-history-raw-log><div class="history-view-lead"><strong>Raw runtime log</strong><span>Read-only retained evidence; full output remains available through the log surface and CLI.</span></div>${logs.length ? renderHistoryEvidence({...selected, evidence_refs: logs}) : `<div class="empty-state">No retained runtime.log is attached to this attempt.</div>`}</section>`;
  }
  if (activeView === "artifacts") {
    const artifacts = refs.filter((path) => !path.endsWith("runtime.log"));
    return `<section class="history-evidence-view" data-history-artifacts><div class="history-view-lead"><strong>Retained artifacts</strong><span>Exact paths and hashes remain read-only; no artifact is reconstructed.</span></div>${artifacts.length ? renderHistoryEvidence({...selected, evidence_refs: artifacts}) : `<div class="empty-state">No retained artifacts are attached to this attempt.</div>`}</section>`;
  }
  return renderHistoryTimeline(timeline, frames, selected);
}

function renderHistoryFrameButton(frame) {
  const selected = frame.identity === state.historySelectedFrame;
  const mode = frame.attempt_mode && frame.attempt_mode !== "unknown" ? ` · ${frame.attempt_mode}` : "";
  const duration = Number.isFinite(frame.duration_seconds) ? ` · ${Number(frame.duration_seconds).toFixed(1)}s` : "";
  return `
    <button class="history-frame ${selected ? "selected" : ""}" data-history-frame="${escapeHtml(frame.identity)}" type="button" aria-pressed="${selected ? "true" : "false"}">
      <span class="small-badge ${historyFrameTone(frame.status)}">${escapeHtml(frame.status)}</span>
      <strong>${escapeHtml(historyFrameLabel(frame))}</strong>
      <span>${escapeHtml(frame.time_utc || frame.updated_at_utc || "Timestamp unavailable")}${escapeHtml(mode)}${escapeHtml(duration)}</span>
    </button>
  `;
}

function renderHistoryFrameDetails(frame) {
  if (!frame) return `<div class="empty-state">No retained attempt selected.</div>`;
  const value = (item, fallback = "not recorded") => escapeHtml(item || fallback);
  const hash = (item) => item ? escapeHtml(String(item).slice(0, 16)) : "not recorded";
  return `
    <div class="terminal-summary-grid" data-history-attempt-details>
      <div class="metric"><span>Runtime</span><strong>${value(frame.runtime_id)}</strong></div>
      <div class="metric"><span>Attempt mode</span><strong>${value(frame.attempt_mode, "unknown")}</strong></div>
      <div class="metric"><span>Started</span><strong>${value(frame.started_at_utc || frame.time_utc)}</strong></div>
      <div class="metric"><span>Duration</span><strong>${Number.isFinite(frame.duration_seconds) ? `${Number(frame.duration_seconds).toFixed(1)}s` : "not recorded"}</strong></div>
      <div class="metric"><span>Validator</span><strong>${value(frame.validator_outcome)}</strong></div>
      <div class="metric"><span>Retained</span><strong>${frame.retained === false ? "no" : "yes"}</strong></div>
    </div>
    <div class="compact-list">
      <span>First decisive failure: ${value(frame.first_decisive_failure)}</span>
      <span>Primary artifact: ${value(frame.primary_artifact)}</span>
      <span>Input hash: ${hash(frame.input_hash)}</span>
      <span>Output hash: ${hash(frame.output_hash)}</span>
      <span>Copy id: ${value(frame.copy_id)}</span>
    </div>
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
  const retainedFrames = primaryHistoryFrames(state.historyTimeline).filter((frame) => frame.retained !== false);
  const compareEligible = retainedFrames.length >= 2 && Boolean(baselineRunId);
  return `
    <section id="runComparisonPanel" class="surface studio-run-comparison" data-studio-run-comparison>
      <div class="surface-title">
        <span>Retained-evidence comparison</span>
        <span class="small-badge">${escapeHtml(baselineRunId || "baseline missing")} → ${escapeHtml(run.run_id)}</span>
      </div>
      ${compareEligible ? `<div class="comparison-controls">
        <label for="runComparisonBaseline"><span>Baseline run id</span><input id="runComparisonBaseline" name="comparison_baseline_run" type="text" value="${escapeHtml(baselineRunId)}"></label>
        <button data-run-comparison-refresh type="button" ${state.runComparisonLoading ? "disabled" : ""}>Refresh comparison</button>
      </div>` : `<div class="empty-state">Compare is unavailable until two retained attempts are present; no snapshot is reconstructed.</div>`}
      ${state.runComparisonError ? `<div class="empty-state bad">${escapeHtml(state.runComparisonError)}. Snapshot unavailable; History will not reconstruct it.</div>` : ""}
      ${state.runComparisonLoading ? `<div class="empty-state loading-state">Loading retained comparison...</div>` : ""}
      ${compareEligible && comparison ? `
        ${renderWarnings(comparison.warnings || [])}
        <div class="terminal-summary-grid">
          ${renderStudioComparisonGroup("Prompt evidence", "prompt", comparison.prompt_hash_deltas)}
          ${renderStudioComparisonGroup("Stage evidence", "stage", comparison.stage_status_deltas)}
          ${renderStudioComparisonGroup("Artifact evidence", "artifact", comparison.artifact_hash_deltas)}
          ${renderStudioComparisonGroup("Validator evidence", "validator", comparison.validator_outcome_deltas)}
        </div>
      ` : compareEligible && !state.runComparisonLoading && !state.runComparisonError
        ? `<div class="empty-state">Choose a retained baseline; no snapshot is reconstructed.</div>`
        : ""}
    </section>
  `;
}

function renderActiveRunComparisonPanel() {
  return renderStudioRunComparisonPanel();
}

function renderStudioHistoryLineageCandidate(candidate, currentRunId) {
  return `
    <article class="lineage-node child" data-history-lineage-child="${escapeHtml(candidate.work_item_id)}">
      <span class="small-badge good">${escapeHtml(candidate.relationship || "child")}</span>
      <strong>${escapeHtml(candidate.label || candidate.work_item_id)}</strong>
      <span>Source run: ${escapeHtml(candidate.source_run_id || currentRunId || "not recorded")}</span>
      <button data-operator-route-intent="child-work-item" data-route-work-item="${escapeHtml(candidate.work_item_id)}" type="button">Open child Work Item</button>
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
          <span>${escapeHtml(state.dashboard?.work_item || "Work Item not recorded")}</span>
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

function renderStudioHistoryArchive() {
  const run = state.dashboard?.run || {};
  const archive = run.archive || {};
  const workItem = state.dashboard?.work_item || "";
  return `
    <section class="surface studio-history-archive" data-studio-history-archive data-archive-state="${archive.archived ? "archived" : "current"}">
      <div class="surface-title">
        <span>Archive disposition</span>
        <span class="small-badge ${archive.archived ? "warn" : "good"}">${archive.archived ? "archived" : "current"}</span>
      </div>
      ${archive.archived ? `
        <div class="terminal-summary-grid">
          <div class="panel-item"><strong>Recorded</strong><span>${escapeHtml(archive.archived_at_utc || "timestamp unavailable")}</span></div>
          <div class="panel-item"><strong>Reason</strong><span>${escapeHtml(archive.reason || "no reason recorded")}</span></div>
          <div class="panel-item"><strong>Source</strong><span>${escapeHtml(archive.source || "legacy manifest fallback")}</span></div>
        </div>
        <p>Archive is an append-only visibility disposition. Completed run evidence and lineage remain immutable and inspectable.</p>
      ` : `<p>No archive overlay is recorded for this run.</p>`}
      ${run.run_id ? `
        <div class="lineage-actions">
          <button data-operator-route-intent="historical-run" data-route-work-item="${escapeHtml(workItem)}" data-route-run-id="${escapeHtml(run.run_id)}" type="button">Inspect retained History</button>
          <button data-operator-route-intent="run-artifacts" data-route-work-item="${escapeHtml(workItem)}" data-route-run-id="${escapeHtml(run.run_id)}" type="button" class="secondary">Inspect retained artifacts and logs</button>
        </div>
      ` : ""}
    </section>
  `;
}

function renderTargetHistoryLineage(run) {
  const lineage = run?.lineage || {};
  const currentRun = run?.run_id || state.activeRunId || "";
  const sourceRun = lineage.source_run_id || "";
  const sourceWorkItem = lineage.source_work_item_id || state.dashboard?.work_item || "";
  const candidates = lineage.child_work_item_candidates || [];
  return `
    <section class="target-history-lineage" data-studio-history-lineage aria-label="Run lineage">
      <div class="surface-title compact"><span>Lineage<span class="sr-only"> — Immutable run lineage</span></span><span class="small-badge">read-only</span></div>
      <div class="target-history-lineage-list">
        ${sourceRun && sourceRun !== currentRun ? `<article class="target-lineage-row" data-history-lineage-parent="${escapeHtml(sourceRun)}"><span class="small-badge">parent</span><strong>${escapeHtml(sourceRun)}</strong><button data-operator-route-intent="parent-run" data-route-work-item="${escapeHtml(sourceWorkItem)}" data-route-run-id="${escapeHtml(sourceRun)}" type="button" class="link-button">Inspect parent run</button></article>` : ""}
        <article class="target-lineage-row current" data-history-lineage-current="${escapeHtml(currentRun)}"><span class="small-badge good">current</span><strong>${escapeHtml(currentRun || "No selected run")}</strong><span>${escapeHtml(state.dashboard?.work_item || "Work Item not recorded")}</span></article>
        ${candidates.length ? candidates.map((candidate) => `<article class="target-lineage-row" data-history-lineage-child="${escapeHtml(candidate.work_item_id)}"><span class="small-badge good">${escapeHtml(candidate.relationship || "child")}</span><strong>${escapeHtml(candidate.label || candidate.work_item_id)}</strong><button data-operator-route-intent="child-work-item" data-route-work-item="${escapeHtml(candidate.work_item_id)}" type="button" class="link-button">Open child</button></article>`).join("") : `<span class="muted">No retained child relation.</span>`}
      </div>
    </section>
  `;
}

function renderTargetHistoryRetention(run) {
  const archive = run?.archive || {};
  return `
    <section class="target-history-retention" data-studio-history-archive data-archive-state="${archive.archived ? "archived" : "current"}">
      <div class="surface-title compact"><span>Retained status</span><span class="small-badge ${archive.archived ? "warn" : "good"}">${archive.archived ? "archived" : "retained"}</span></div>
      <p>${archive.archived ? `Archived ${escapeHtml(archive.archived_at_utc || "timestamp unavailable")}. ${escapeHtml(archive.reason || "Append-only visibility disposition.")}` : "Retained evidence remains immutable and inspectable."}</p>
      <small>append-only visibility disposition; source run history is never rewritten.</small>
      ${run?.run_id ? `<div class="lineage-actions target-history-retention-actions"><button data-operator-route-intent="historical-run" data-route-work-item="${escapeHtml(state.dashboard?.work_item || "")}" data-route-run-id="${escapeHtml(run.run_id)}" type="button">Inspect retained History</button><button data-operator-route-intent="run-artifacts" data-route-work-item="${escapeHtml(state.dashboard?.work_item || "")}" data-route-run-id="${escapeHtml(run.run_id)}" type="button" class="secondary">Inspect retained artifacts and logs</button></div>` : ""}
    </section>
  `;
}

function renderTargetHistoryInspector(selected, run) {
  const selectedLabel = selected ? historyFrameLabel(selected) : "No attempt selected";
  const retainedRefs = selected?.evidence_refs || [];
  const compareEligible = primaryHistoryFrames(state.historyTimeline).filter((frame) => frame.retained !== false).length >= 2;
  return `
    <aside class="target-history-inspector" data-history-selected-inspector aria-label="Selected attempt inspector">
      <div class="target-panel-heading"><strong>Evidence and lineage</strong><span class="small-badge">read-only</span></div>
      <div class="target-history-attempt-heading">
        <p class="eyebrow">Selected attempt</p>
        <h3>${escapeHtml(selectedLabel)}</h3>
        <div class="target-history-inspector-actions"><button class="primary" data-history-open-attempt type="button">Open selected attempt</button></div>
      </div>
      ${renderHistoryFrameDetails(selected).replace("data-history-attempt-details", "data-history-attempt-details data-target-history-attempt-details")}
      <section class="target-history-evidence" aria-label="Selected attempt evidence">
        <div class="surface-title compact"><span>Retained evidence</span><span class="small-badge">${escapeHtml(retainedRefs.length)}</span></div>
        <div class="recent-artifacts">${renderHistoryEvidence(selected)}</div>
      </section>
      ${renderTargetHistoryLineage(run)}
      ${renderTargetHistoryRetention(run)}
      ${compareEligible ? `<button class="secondary target-history-compare" data-history-compare type="button">Compare retained attempts</button>` : `<p class="muted">Compare appears only when two retained attempts are available.</p>`}
    </aside>
  `;
}

function renderStudioHistory(timeline) {
  const frames = primaryHistoryFrames(timeline);
  const selected = selectedHistoryFrame(timeline);
  const run = {...(state.dashboard?.run || {}), ...(selectedHistoryRun() || {})};
  const targetInspector = renderTargetHistoryInspector(selected, run);
  if (!frames.length) {
    return `
      <section class="target-history-surface" data-target-history-surface>
        <div class="target-history-heading"><div><p class="eyebrow">Runs and Attempts</p><h2>Runs</h2><p>Inspect retained chronology, selected evidence, and immutable lineage.</p></div></div>
        <div class="target-history-grid">${renderHistoryRunList()}<div class="target-history-main"><div class="empty-state">No durable attempt History frames are available for this run.</div></div>${targetInspector}</div>
      </section>
    `;
  }
  return `
    <section class="target-history-surface" data-target-history-surface>
      <div class="target-history-heading"><div><p class="eyebrow">Runs and Attempts</p><h2>Runs</h2><p>Inspect retained chronology, selected evidence, and immutable lineage.</p></div><span class="small-badge">${escapeHtml(frames.length)} retained frames</span></div>
      <div class="target-history-grid">
        ${renderHistoryRunList()}
        <div class="target-history-main">
          <section class="surface studio-history" data-studio-history data-history-auto-follow="${state.historyAutoFollow ? "true" : "false"}">
            <div class="target-history-run-heading"><div><p class="eyebrow">Run</p><h3>${escapeHtml(run.run_id || state.activeRunId || "Selected run")}</h3></div><button class="link-button" data-copy-history-run type="button">Copy run ID</button></div>
            ${renderHistoryAttemptTabs(frames, selected)}
            ${renderHistoryViewTabs()}
            ${renderSelectedHistoryView(timeline, frames, selected)}
            <div class="history-selection" data-history-selection="${escapeHtml(selected?.identity || "")}">
              <div class="surface-title compact">
                <strong>${escapeHtml(selected ? historyFrameLabel(selected) : "No frame selected")}</strong>
                <button data-history-return-live type="button" class="secondary" ${state.historyAutoFollow ? "disabled aria-disabled=\"true\"" : ""}>Return to live</button>
              </div>
              <span>Historical selection pauses browser auto-follow only; the active runtime is not stopped.</span>
            </div>
          </section>
          ${renderStudioRunComparisonPanel()}
        </div>
        ${targetInspector}
      </div>
    </section>
  `;
}
