function parsePrefixedLogLine(text, fallbackStream) {
  const rawText = String(text ?? "");
  const matched = rawText.match(/^\[([^:\]]+):([^:\]]+):(stdout|stderr|system)\]\s?(.*)$/i);
  if (matched) {
    return {
      stream: matched[3].toLowerCase(),
      source: `${matched[1]} / ${matched[2]}`,
      text: matched[4]
    };
  }
  const simple = rawText.match(/^\[(stdout|stderr|system)\]\s?(.*)$/i);
  if (simple) {
    const stream = simple[1].toLowerCase();
    return {
      stream,
      source: stream === "system" ? "system" : "runtime",
      text: simple[2]
    };
  }
  if (!matched) {
    return {
      stream: fallbackStream || "stdout",
      source: fallbackStream || "runtime",
      text: rawText
    };
  }
}

function logEntriesFromChunks(chunks) {
  const entries = [];
  for (const chunk of chunks || []) {
    const stream = String(chunk.stream || "stdout");
    const lines = String(chunk.text || "").split(/\r?\n/);
    lines.forEach((line, index) => {
      if (!line && index === lines.length - 1) return;
      entries.push(parsePrefixedLogLine(line, stream));
    });
  }
  return entries;
}

function logEntriesFromText(text) {
  return String(text ?? "").split(/\r?\n/).filter((line, index, lines) => line || index < lines.length - 1).map((line) => parsePrefixedLogLine(line, "stdout"));
}

function filteredLogEntries(entries) {
  if (state.logFilter === "all") return entries;
  return entries.filter((entry) => String(entry.stream || "").toLowerCase() === state.logFilter);
}

function rawTextFromEntries(entries) {
  return entries.map((entry) => `[${entry.stream}] ${entry.source ? `${entry.source}: ` : ""}${entry.text}`).join("\n");
}

function renderLogPanel({title, meta, entries, rawText, emptyText, actions = "", truncation = null}) {
  const filtered = filteredLogEntries(entries);
  const rawBody = state.logFilter === "all" && rawText ? rawText : rawTextFromEntries(filtered);
  const filterButtons = ["all", "stdout", "stderr", "system"].map((filter) => (
    `<button data-log-filter="${filter}" class="${state.logFilter === filter ? "active" : ""}" type="button">${filter}</button>`
  )).join("");
  const rows = state.rawLogMode
    ? `<pre>${escapeHtml(rawBody)}</pre>`
    : filtered.length
      ? `<div class="log-rows">${filtered.map((entry) => `
          <div class="log-row">
            <span class="log-badge ${escapeHtml(String(entry.stream || "").toLowerCase())}">${escapeHtml(entry.stream)}</span>
            <span class="log-source">${escapeHtml(entry.source)}</span>
            <span class="log-text">${escapeHtml(entry.text)}</span>
          </div>
        `).join("")}</div>`
      : `<div class="empty-state" style="padding:18px 12px">${escapeHtml(emptyText)}</div>`;
  return `
    <section class="log-panel">
      <div class="log-toolbar">
        <div>
          <strong>${escapeHtml(title)}</strong>
          ${pathLine(meta.filter(Boolean).join(" / "), 72)}
        </div>
        <div class="log-actions">
          ${actions}
          <div class="log-filter">
            ${filterButtons}
            <button data-log-raw="toggle" class="${state.rawLogMode ? "active" : ""}" type="button">Raw</button>
          </div>
        </div>
      </div>
      ${renderTruncationNotice("log", truncation)}
      ${rows}
    </section>
  `;
}

function liveJobMatchesStage() {
  if (!state.activeJobStatus) return false;
  return state.activeJobStatus.kind === "workflow" || state.activeJobStatus.stage === state.activeStage;
}

function activeJobStatusClass() {
  return statusClass(state.activeJobStatus?.status || "running");
}

function activeJobIsTerminal() {
  return ["cancelled", "completed", "failed"].includes(state.activeJobStatus?.status || "");
}

function activeJobCancelLabel() {
  const status = state.activeJobStatus?.status || "running";
  if (status === "cancelling") return "Cancelling...";
  if (status === "cancelled") return "Cancelled";
  if (status === "completed") return "Completed";
  if (status === "failed") return "Stopped";
  return "Cancel job";
}

function renderLiveJobActions() {
  if (!state.activeJobId || !state.activeJobStatus) return "";
  const status = state.activeJobStatus.status || "running";
  const disabled = activeJobIsTerminal() || status === "cancelling";
  return `
    <span class="small-badge ${escapeHtml(activeJobStatusClass())}">${escapeHtml(status)}</span>
    <button data-cancel-job="${escapeHtml(state.activeJobId)}" class="danger" type="button" ${disabled ? "disabled" : ""}>${escapeHtml(activeJobCancelLabel())}</button>
  `;
}

async function renderLogs() {
  if (state.activeJobId && liveJobMatchesStage() && (state.activeJobStatus?.status === "running" || state.activeJobStatus?.status === "waiting-for-operator" || state.activeJobStatus?.status === "cancelling" || state.activeJobLogChunks.length)) {
    const entries = logEntriesFromChunks(state.activeJobLogChunks);
    document.getElementById("cockpitContent").innerHTML = renderLogPanel({
      title: `Live job ${state.activeJobId}`,
      meta: [state.activeJobStatus?.status || "running", state.activeJobStatus?.stage || "workflow"],
      entries,
      rawText: rawTextFromEntries(entries),
      emptyText: "Waiting for runtime output...",
      actions: renderLiveJobActions()
    });
    return;
  }
  const item = activeStageItem();
  if (!item || Number(item.attempt_count || 0) <= 0) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">No runtime log for this stage yet.</div>`;
    return;
  }
  try {
    const params = new URLSearchParams({stage: state.activeStage});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    const view = await api(`/api/logs?${params.toString()}`);
    state.savedLogText = view.text || "";
    const summary = view.summary || {};
    document.getElementById("cockpitContent").innerHTML = renderLogPanel({
      title: "Saved runtime.log",
      meta: [summary.run_id ? `run ${summary.run_id}` : "", summary.stage ? `stage ${summary.stage}` : "", summary.attempt_number ? `attempt ${summary.attempt_number}` : ""],
      entries: logEntriesFromText(state.savedLogText),
      rawText: state.savedLogText,
      emptyText: "Saved runtime log is empty",
      truncation: view
    });
  } catch (error) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function cancelActiveJob() {
  if (!state.activeJobId) return;
  const result = await postJson(`/api/jobs/${encodeURIComponent(state.activeJobId)}/cancel`, {});
  state.activeJobStatus = result;
  if (result.already_finished) {
    toast("Job already finished.");
  } else if (result.status === "cancelled") {
    toast("Job cancelled.");
  } else {
    toast("Cancel requested.");
  }
  renderActivityTable();
  if (state.activeTab === "logs") await renderLogs();
  const activeStatuses = new Set(["running", "waiting-for-operator", "cancelling"]);
  if (!state.activeJobTimer && activeStatuses.has(result.status)) {
    state.activeJobTimer = setInterval(pollActiveJob, 1000);
  }
}

async function pollActiveJob() {
  if (!state.activeJobId) return;
  try {
    const activeStatuses = new Set(["running", "waiting-for-operator", "cancelling"]);
    const logs = await api(`/api/jobs/${encodeURIComponent(state.activeJobId)}/logs?cursor=${state.activeJobCursor}`);
    state.activeJobCursor = Number(logs.cursor || state.activeJobCursor);
    state.activeJobLogChunks.push(...(logs.chunks || []));
    state.activeJobStatus = await api(`/api/jobs/${encodeURIComponent(state.activeJobId)}`);
    renderActivityTable();
    if (state.activeTab === "logs") await renderLogs();
    if (state.activeJobStatus.status === "waiting-for-operator") {
      activateTab("approvals");
      await renderApprovals();
    }
    if (!activeStatuses.has(state.activeJobStatus.status)) {
      if (state.activeJobTimer) clearInterval(state.activeJobTimer);
      state.activeJobTimer = null;
      await fetchDashboard();
      await renderAll();
    }
  } catch (error) {
    state.activeJobLogChunks.push({stream: "system", text: `[ui] ${error.message}\n`});
    if (state.activeJobTimer) clearInterval(state.activeJobTimer);
    state.activeJobTimer = null;
    renderActivityTable();
    if (state.activeTab === "logs") await renderLogs();
  }
}

async function startJobPolling(job) {
  state.activeJobId = job.job_id;
  state.activeJobCursor = 0;
  state.activeJobLogChunks = [];
  state.activeJobStatus = {job_id: job.job_id, kind: job.kind, stage: job.stage, status: "running"};
  if (state.activeJobTimer) clearInterval(state.activeJobTimer);
  activateTab("logs");
  await renderLogs();
  await pollActiveJob();
  state.activeJobTimer = setInterval(pollActiveJob, 1000);
}
