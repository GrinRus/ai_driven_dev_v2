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
  `;
}
