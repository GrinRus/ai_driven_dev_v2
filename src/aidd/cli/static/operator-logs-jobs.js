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

function logEntryCounts(entries) {
  return entries.reduce((counts, entry) => {
    const stream = String(entry.stream || "stdout").toLowerCase();
    counts.total += 1;
    counts[stream] = (counts[stream] || 0) + 1;
    return counts;
  }, {total: 0, stdout: 0, stderr: 0, system: 0});
}

function renderLogBoundedNotice(view) {
  if (!view) return "";
  const truncated = renderTruncationNotice("log", view);
  if (truncated) return truncated;
  return `
    <div class="truncation-notice bounded-log-notice" role="status">
      <strong>Runtime log bounded read</strong>
      <span>Showing API read window (${escapeHtml(byteRangeSummary(view))}). Full runtime.log remains on disk and available through CLI log inspection.</span>
    </div>
  `;
}

function renderLogSourceStrip(entries, truncation) {
  const counts = logEntryCounts(entries);
  const source = truncation ? "saved runtime.log" : "live UI job stream";
  const windowLabel = truncation
    ? `${byteRangeSummary(truncation)}${truncation.truncated ? " / bounded" : ""}`
    : "unbounded live buffer";
  return `
    <div class="log-source-strip" aria-label="Runtime log source filter summary">
      <div class="log-source-pill">
        <span>Source</span>
        <strong>${escapeHtml(source)}</strong>
      </div>
      <div class="log-source-pill">
        <span>Filter</span>
        <strong>${escapeHtml(state.logFilter)}</strong>
      </div>
      <div class="log-source-pill">
        <span>Entries</span>
        <strong>${escapeHtml(counts.total)}</strong>
      </div>
      <div class="log-source-pill">
        <span>STDOUT</span>
        <strong>${escapeHtml(counts.stdout)}</strong>
      </div>
      <div class="log-source-pill">
        <span>STDERR</span>
        <strong>${escapeHtml(counts.stderr)}</strong>
      </div>
      <div class="log-source-pill">
        <span>System</span>
        <strong>${escapeHtml(counts.system)}</strong>
      </div>
      <div class="log-source-pill wide">
        <span>Window</span>
        <strong>${escapeHtml(windowLabel)}</strong>
      </div>
    </div>
  `;
}

function renderLogAuditLog(entries, sourceLabel, truncation) {
  const dashboardEvents = typeof activityEvents === "function" ? activityEvents().slice(0, 6) : [];
  const streamEvents = entries.slice(-6).reverse().map((entry) => ({
    time_utc: "visible window",
    level: entry.stream === "stderr" ? "warn" : "info",
    source: entry.source || entry.stream || sourceLabel,
    event: `log.${entry.stream || "stdout"}`,
    details: entry.text
  }));
  const boundedEvent = truncation ? [{
    time_utc: "api window",
    level: truncation.truncated ? "warn" : "info",
    source: sourceLabel,
    event: truncation.truncated ? "log.bounded-truncated" : "log.bounded-read",
    details: byteRangeSummary(truncation)
  }] : [];
  const rows = [...boundedEvent, ...streamEvents, ...dashboardEvents].slice(0, 10);
  if (!rows.length) {
    return `<section class="surface audit-log-panel"><div class="surface-title"><span>Correlated Events / Audit Log</span></div><div class="empty-state">No log events available yet.</div></section>`;
  }
  return `
    <section class="surface audit-log-panel">
      <div class="surface-title">
        <span>Correlated Events / Audit Log</span>
        <span class="small-badge">${escapeHtml(rows.length)} events</span>
      </div>
      <div class="table-wrap log-audit-wrap">
        <table class="activity-table log-audit-table">
          <thead><tr><th>Time</th><th>Level</th><th>Source / event</th><th>Details</th></tr></thead>
          <tbody>
            ${rows.map((event) => `
              <tr>
                <td>${escapeHtml(event.time_utc || "-")}</td>
                <td><span class="small-badge ${event.level === "error" ? "bad" : event.level === "warn" ? "warn" : ""}">${escapeHtml(event.level || "info")}</span></td>
                <td>${escapeHtml(event.source || sourceLabel)} / ${escapeHtml(event.event || "log")}</td>
                <td>${escapeHtml(event.details || "")}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderLogPanel({title, meta, entries, rawText, emptyText, actions = "", truncation = null}) {
  const filtered = filteredLogEntries(entries);
  const rawBody = state.logFilter === "all" && rawText ? rawText : rawTextFromEntries(filtered);
  const sourceLabel = truncation ? "saved runtime.log" : "live console";
  const filterButtons = ["all", "stdout", "stderr", "system"].map((filter) => (
    `<button data-log-filter="${filter}" class="${state.logFilter === filter ? "active" : ""}" type="button" aria-label="Show ${filter} source filter">${filter}</button>`
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
    <section class="log-console-screen">
      <div class="surface-title">
        <span>Runtime Logs / Live Console</span>
        <span class="small-badge">${escapeHtml(sourceLabel)}</span>
      </div>
      ${renderLogSourceStrip(entries, truncation)}
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
        ${renderLogBoundedNotice(truncation)}
        ${rows}
      </section>
      ${renderLogAuditLog(filtered, sourceLabel, truncation)}
    </section>
  `;
}

function liveJobMatchesStage() {
  if (!state.activeJobStatus) return false;
  return state.activeJobStatus.kind === "workflow"
    || state.activeJobStatus.kind === "next-flow-launch"
    || state.activeJobStatus.stage === state.activeStage;
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
