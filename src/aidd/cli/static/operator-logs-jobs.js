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
                <td>${typeof renderActivityDetail === "function" ? renderActivityDetail(event.details) : escapeHtml(event.details || "")}</td>
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
    `<button data-log-filter="${filter}" class="${state.logFilter === filter ? "active" : ""}" type="button" aria-pressed="${state.logFilter === filter ? "true" : "false"}" aria-label="Show ${filter} source filter">${filter}</button>`
  )).join("");
  const viewButtons = [
    ["summary", "Summary"],
    ["timeline", "Timeline"],
    ["raw", "Raw Runtime Log"]
  ].map(([mode, label]) => (
    `<button data-log-view="${mode}" class="${state.logViewMode === mode ? "active" : ""}" type="button" aria-pressed="${state.logViewMode === mode ? "true" : "false"}">${label}</button>`
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
  const counts = logEntryCounts(entries);
  const summary = `
    <section class="surface log-summary-panel">
      <div class="metric-grid compact">
        <div class="metric"><span>Total</span><strong>${escapeHtml(counts.total)}</strong></div>
        <div class="metric"><span>STDOUT</span><strong>${escapeHtml(counts.stdout)}</strong></div>
        <div class="metric"><span>STDERR</span><strong>${escapeHtml(counts.stderr)}</strong></div>
        <div class="metric"><span>System</span><strong>${escapeHtml(counts.system)}</strong></div>
      </div>
      ${renderLogBoundedNotice(truncation)}
      <div class="compact-list">
        ${filtered.slice(-5).reverse().map((entry) => `<span>${escapeHtml(entry.stream)} / ${escapeHtml(entry.text)}</span>`).join("") || `<span>${escapeHtml(emptyText)}</span>`}
      </div>
    </section>
  `;
  const rawRuntimeLog = `
    <section class="log-panel">
      <div class="log-toolbar">
        <div>
          <strong>${escapeHtml(title)}</strong>
          ${pathLine(meta.filter(Boolean).join(" / "), 72)}
        </div>
        <div class="log-actions">
          ${actions}
          <div class="log-filter" role="group" aria-label="Log source filter">
            ${filterButtons}
            <button data-log-raw="toggle" class="${state.rawLogMode ? "active" : ""}" type="button" aria-pressed="${state.rawLogMode ? "true" : "false"}">Raw</button>
          </div>
        </div>
      </div>
      ${renderLogBoundedNotice(truncation)}
      ${rows}
    </section>
  `;
  const modeBody = state.logViewMode === "timeline"
    ? renderLogAuditLog(filtered, sourceLabel, truncation)
    : state.logViewMode === "raw"
      ? rawRuntimeLog
      : summary;
  return `
    <section class="log-console-screen">
      <div class="surface-title">
        <span>Runtime Logs / Live Console</span>
        <span class="small-badge">${escapeHtml(sourceLabel)}</span>
      </div>
      ${renderLogSourceStrip(entries, truncation)}
      <div class="filter-row log-view-tabs" role="group" aria-label="Log presentation">${viewButtons}</div>
      ${modeBody}
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

const ACTIVE_JOB_POLL_INTERVAL_MS = 1000;
const ACTIVE_JOB_RETRY_BASE_MS = 500;
const ACTIVE_JOB_RETRY_MAX_MS = 8000;
const ACTIVE_JOB_RETRY_LIMIT = 5;

function clearActiveJobPollTimer() {
  if (state.activeJobTimer) clearTimeout(state.activeJobTimer);
  state.activeJobTimer = null;
}

function resetActiveJobConnection() {
  state.activeJobConnection = {
    state: "unknown",
    failureCount: 0,
    lastError: "",
    retryDelayMs: null,
    recovered: false,
    expired: false
  };
}

function scheduleActiveJobPoll(delayMs = ACTIVE_JOB_POLL_INTERVAL_MS) {
  clearActiveJobPollTimer();
  const generation = state.activeJobPollGeneration;
  state.activeJobTimer = setTimeout(() => {
    state.activeJobTimer = null;
    if (generation !== state.activeJobPollGeneration) return;
    void pollActiveJob();
  }, delayMs);
}

function activeJobRetryDelay(failureCount) {
  return Math.min(
    ACTIVE_JOB_RETRY_BASE_MS * (2 ** Math.max(0, failureCount - 1)),
    ACTIVE_JOB_RETRY_MAX_MS
  );
}

function clearReconciledActiveJob({preserveConnection = true} = {}) {
  clearActiveJobPollTimer();
  state.activeJobPollGeneration += 1;
  state.activeJobId = "";
  state.activeJobStatus = null;
  state.activeJobCursor = 0;
  state.activeJobLogChunks = [];
  state.approvalSessionConfirmation = null;
  if (!preserveConnection) resetActiveJobConnection();
}

async function reconcileRecoveredActiveJob(jobId, status) {
  if (status?.stage && STAGES.includes(status.stage)) {
    state.activeStage = status.stage;
    state.activeStageExplicit = true;
  }
  const cursor = state.activeJobCursor;
  const chunks = state.activeJobLogChunks;
  await fetchDashboard();
  if (state.activeJobId === jobId) {
    state.activeJobCursor = cursor;
    state.activeJobLogChunks = chunks;
  }
  await fetchProjectHome(state.dashboard?.work_item || "");
  await fetchInbox();
}

async function reconcileExpiredActiveJob(jobId) {
  try {
    await fetchDashboard();
    if (state.dashboardActiveJob?.job_id === jobId) return false;
    if (!state.dashboardActiveJob) clearReconciledActiveJob({preserveConnection: true});
    await fetchProjectHome(state.dashboard?.work_item || "");
    await fetchInbox();
    await renderAll();
    return true;
  } catch (_error) {
    return false;
  }
}

async function reconcileTerminalActiveJob(jobId) {
  await fetchDashboard();
  if (!state.dashboardActiveJob || state.dashboardActiveJob.job_id === jobId) {
    clearReconciledActiveJob({preserveConnection: false});
  }
  await fetchProjectHome(state.dashboard?.work_item || "");
  await fetchInbox();
  await renderAll();
}

function renderActiveJobConnectionSurface() {
  const connection = state.activeJobConnection;
  if (!connection || connection.state === "unknown" || (
    connection.state === "online" && !connection.recovered
  )) return "";
  if (connection.state === "online" && connection.recovered) {
    return `<div data-connection-state="recovered" data-connection-cursor="${escapeHtml(state.activeJobCursor)}" data-runtime-terminal-observed="false" data-durable-log="runtime.log">${renderStateSurface({
      kind: "live-connection",
      state: "empty",
      title: "Live connection recovered",
      consequence: "Polling resumed from the last accepted log cursor; runtime state remained server-authoritative."
    })}</div>`;
  }
  if (connection.expired) {
    return `<div data-connection-state="expired-job" data-connection-cursor="${escapeHtml(state.activeJobCursor)}" data-runtime-terminal-observed="false" data-durable-log="runtime.log">${renderStateSurface({
      kind: "live-connection",
      state: "unavailable",
      title: "Live job is no longer retained",
      consequence: "The UI job record expired. Refresh durable dashboard and runtime.log evidence; this does not mean the runtime failed.",
      recovery: {action: "refresh-expired-job", label: "Refresh durable state"}
    })}</div>`;
  }
  if (connection.state === "offline") {
    return `<div data-connection-state="offline" data-connection-cursor="${escapeHtml(state.activeJobCursor)}" data-runtime-terminal-observed="false" data-durable-log="runtime.log">${renderStateSurface({
      kind: "live-connection",
      state: "unavailable",
      title: "Live connection is offline",
      consequence: "The runtime may still be running. No terminal status was observed and the log cursor is preserved.",
      recovery: {action: "reconnect-live-job", label: "Reconnect"}
    })}</div>`;
  }
  return `<div data-connection-state="reconnecting" data-connection-cursor="${escapeHtml(state.activeJobCursor)}" data-runtime-terminal-observed="false" data-durable-log="runtime.log">${renderStateSurface({
    kind: "live-connection",
    state: "reconnecting",
    title: "Reconnecting to live output",
    consequence: `Attempt ${connection.failureCount} failed; retrying in ${connection.retryDelayMs} ms from the preserved cursor.`
  })}</div>`;
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
  const item = activeStageItem();
  const liveLogAvailable = Boolean(
    state.activeJobId
    && liveJobMatchesStage()
    && (state.activeJobStatus?.status === "running" || state.activeJobStatus?.status === "waiting-for-operator" || state.activeJobStatus?.status === "cancelling" || state.activeJobLogChunks.length)
  );
  const visibility = resolveStudioEvidenceVisibility({
    logEvidenceAvailable: liveLogAvailable || Number(item?.attempt_count || 0) > 0,
    requestedSurface: "logs"
  });
  if (!visibility.logs) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">No runtime log for this stage yet.</div>`;
    return;
  }
  if (liveLogAvailable) {
    const entries = logEntriesFromChunks(state.activeJobLogChunks);
    document.getElementById("cockpitContent").innerHTML = `${renderActiveJobConnectionSurface()}${renderLogPanel({
      title: `Live job ${state.activeJobId}`,
      meta: [state.activeJobStatus?.status || "running", state.activeJobStatus?.stage || "workflow"],
      entries,
      rawText: rawTextFromEntries(entries),
      emptyText: "Waiting for runtime output...",
      actions: renderLiveJobActions()
    })}`;
    return;
  }
  try {
    const params = new URLSearchParams({stage: state.activeStage});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    const view = await api(`/api/logs?${params.toString()}`);
    state.savedLogText = view.text || "";
    const summary = view.summary || {};
    const logAvailable = view.available !== false;
    document.getElementById("cockpitContent").innerHTML = `${renderActiveJobConnectionSurface()}${renderLogPanel({
      title: logAvailable ? "Saved runtime.log" : "Saved runtime.log (pending)",
      meta: [summary.run_id ? `run ${summary.run_id}` : "", summary.stage ? `stage ${summary.stage}` : "", summary.attempt_number ? `attempt ${summary.attempt_number}` : ""],
      entries: logEntriesFromText(state.savedLogText),
      rawText: state.savedLogText,
      emptyText: logAvailable ? "Saved runtime log is empty" : (view.message || "Runtime log is not available yet."),
      truncation: view
    })}`;
  } catch (error) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function cancelActiveJob() {
  if (!state.activeJobId) return;
  state.activeJobPollGeneration += 1;
  clearActiveJobPollTimer();
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
  if (typeof updateStudioLiveObservation === "function") updateStudioLiveObservation();
  if (activeModeIsEvidenceLog()) await renderLogs();
  const activeStatuses = new Set(["running", "waiting-for-operator", "cancelling"]);
  if (activeStatuses.has(result.status)) scheduleActiveJobPoll(0);
}

async function reconnectActiveJob() {
  if (!state.activeJobId || activeJobIsTerminal()) return;
  state.activeJobPollGeneration += 1;
  clearActiveJobPollTimer();
  resetActiveJobConnection();
  state.activeJobConnection.state = "reconnecting";
  await renderLogs();
  await pollActiveJob();
}

async function pollActiveJob() {
  if (!state.activeJobId) return;
  const jobId = state.activeJobId;
  const pollGeneration = state.activeJobPollGeneration;
  try {
    const activeStatuses = new Set(["running", "waiting-for-operator", "cancelling"]);
    const logs = await api(`/api/jobs/${encodeURIComponent(jobId)}/logs?cursor=${state.activeJobCursor}`);
    if (
      state.activeJobId !== jobId
      || state.activeJobPollGeneration !== pollGeneration
    ) return;
    if (logs.truncated) {
      state.activeJobLogChunks.push({
        stream: "system",
        text: `[ui] Live log tail was truncated before cursor ${logs.oldest_cursor}; use the durable runtime log for complete evidence.\n`
      });
    }
    const nextCursor = Number(logs.cursor);
    if (Number.isFinite(nextCursor)) state.activeJobCursor = nextCursor;
    state.activeJobLogChunks.push(...(logs.chunks || []));
    const status = await api(`/api/jobs/${encodeURIComponent(jobId)}`);
    if (
      state.activeJobId !== jobId
      || state.activeJobPollGeneration !== pollGeneration
    ) return;
    state.activeJobStatus = status;
    const wasDisconnected = state.activeJobConnection.failureCount > 0;
    state.activeJobConnection = {
      state: "online",
      failureCount: 0,
      lastError: "",
      retryDelayMs: null,
      recovered: wasDisconnected,
      expired: false
    };
    if (wasDisconnected) await reconcileRecoveredActiveJob(jobId, status);
    renderActiveRunPanel();
    if (typeof renderNextActionPanel === "function") renderNextActionPanel();
    if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
    if (typeof updateStudioLiveObservation === "function") updateStudioLiveObservation();
    renderActivityTable();
    if (activeModeIsEvidenceLog()) await renderLogs();
    if (state.activeJobStatus.status === "waiting-for-operator") {
      activateTab("approvals");
      await renderApprovals();
    }
    if (!activeStatuses.has(state.activeJobStatus.status)) {
      clearActiveJobPollTimer();
      await reconcileTerminalActiveJob(jobId);
    } else {
      scheduleActiveJobPoll();
    }
  } catch (error) {
    if (
      state.activeJobId !== jobId
      || state.activeJobPollGeneration !== pollGeneration
    ) return;
    const expired = error.status === 404 || error.status === 410;
    const failureCount = state.activeJobConnection.failureCount + 1;
    const retryDelayMs = activeJobRetryDelay(failureCount);
    state.activeJobConnection = {
      state: expired || failureCount >= ACTIVE_JOB_RETRY_LIMIT ? "offline" : "reconnecting",
      failureCount,
      lastError: error.message,
      retryDelayMs: expired || failureCount >= ACTIVE_JOB_RETRY_LIMIT ? null : retryDelayMs,
      recovered: false,
      expired
    };
    state.activeJobLogChunks.push({stream: "system", text: `[ui] ${error.message}\n`});
    renderActivityTable();
    if (activeModeIsEvidenceLog()) await renderLogs();
    if (expired && await reconcileExpiredActiveJob(jobId)) return;
    if (!expired && failureCount < ACTIVE_JOB_RETRY_LIMIT) scheduleActiveJobPoll(retryDelayMs);
    else clearActiveJobPollTimer();
  }
}

async function startJobPolling(job) {
  clearActiveJobPollTimer();
  state.activeJobPollGeneration += 1;
  state.approvalSessionConfirmation = null;
  state.activeJobId = job.job_id;
  state.activeJobCursor = 0;
  state.activeJobLogChunks = [];
  state.activeJobStatus = {
    job_id: job.job_id,
    kind: job.kind,
    stage: job.stage,
    status: "running",
    message: "job started"
  };
  resetActiveJobConnection();
  renderActiveRunPanel();
  if (typeof renderNextActionPanel === "function") renderNextActionPanel();
  if (typeof renderGlobalNextActionStrip === "function") renderGlobalNextActionStrip();
  activateTab("logs");
  await renderLogs();
  await pollActiveJob();
}
