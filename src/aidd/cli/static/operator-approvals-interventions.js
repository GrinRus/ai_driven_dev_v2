function interventionTargetEntries(documents) {
  const excluded = new Set([
    "answers",
    "input_bundle",
    "operator_request",
    "questions",
    "repair_brief",
    "repair_context",
    "stage_brief",
    "validator_report"
  ]);
  const blockedNames = new Set([
    "answers.md",
    "input-bundle.md",
    "questions.md",
    "repair-brief.md",
    "stage-brief.md",
    "validator-report.md"
  ]);
  return Object.entries(documents || {}).filter(([key, path]) => {
    const textPath = String(path || "");
    return !excluded.has(key)
      && textPath.includes(`/stages/${state.activeStage}/`)
      && !textPath.includes("/operator-requests/")
      && !blockedNames.has(textPath.split("/").pop())
      && textPath.endsWith(".md");
  });
}

function interventionTargetLabel(key) {
  return String(key || "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function requestChangeTargetEntries(documents, context) {
  const artifactTargets = interventionTargetEntries(documents);
  if (artifactTargets.length) return artifactTargets;
  return (context?.target_documents || []).map((path, index) => [`target_${index + 1}`, path]);
}

function selectedInterventionTargets() {
  return Array.from(document.querySelectorAll("[data-intervention-target]:checked"))
    .map((input) => input.dataset.interventionTarget)
    .filter(Boolean);
}

function updateSubmitInterventionState() {
  const textarea = document.getElementById("operatorRequestText");
  const button = document.getElementById("submitInterventionButton");
  const note = document.getElementById("interventionReadinessNote");
  const readinessReason = runtimeReadinessMessage();
  if (note) {
    note.textContent = readinessReason;
    note.hidden = !readinessReason;
  }
  if (!button) return;
  button.disabled = Boolean(readinessReason) || !String(textarea?.value || "").trim();
}

function renderInterventionDiffPreview(requestText, targetDocuments) {
  const request = String(requestText || "").trim();
  const targets = targetDocuments || [];
  const targetBody = targets.length
    ? targets.map((target) => `<li>${escapeHtml(target)}</li>`).join("")
    : `<li>Stage scope only; the runtime will receive the request without pinned document targets.</li>`;
  const requestBody = request
    ? request
    : "No operator request text entered yet.";
  return `
    <div class="intervention-diff-preview-body">
      <div class="diff-preview-row">
        <strong>Operator request markdown</strong>
        <span>${escapeHtml(requestBody)}</span>
      </div>
      <div class="diff-preview-row">
        <strong>Target scope</strong>
        <ul>${targetBody}</ul>
      </div>
      <div class="diff-preview-row">
        <strong>Execution preview</strong>
        <span>Creates a stage-scoped operator request and launches the normal runtime intervention path. No stage document is mutated until that job runs.</span>
      </div>
    </div>
  `;
}

function updateInterventionPreview() {
  const preview = document.getElementById("interventionDiffPreview");
  if (preview) {
    const textarea = document.getElementById("operatorRequestText");
    preview.innerHTML = renderInterventionDiffPreview(textarea?.value || "", selectedInterventionTargets());
  }
  updateSubmitInterventionState();
}

function renderRequestChangeAuditLog(context) {
  const targets = context?.target_documents || [];
  const targetSummary = targets.length ? targets.join(", ") : "stage scope only";
  const latest = context?.latest_request_id ? `
    <div class="audit-row">
      <span class="small-badge good">latest</span>
      <div>
        <strong>${escapeHtml(context.latest_request_id)}</strong>
        ${context.latest_request_path ? pathLine(context.latest_request_path, 82) : ""}
        <p>${escapeHtml(context.latest_request_excerpt || "")}</p>
      </div>
    </div>
  ` : `
    <div class="audit-row">
      <span class="small-badge">ready</span>
      <div>
        <strong>No saved operator request yet</strong>
        <p>${escapeHtml(context?.reason || "Submit a request to create the first durable intervention document.")}</p>
      </div>
    </div>
  `;
  return `
    <section class="surface audit-log-panel">
      <div class="surface-title">
        <span>Request Change Audit Log</span>
        <span class="small-badge">${escapeHtml(context?.status || "ready")}</span>
      </div>
      <div class="audit-list">
        ${latest}
        <div class="audit-row">
          <span class="small-badge">scope</span>
          <div>
            <strong>Current target documents</strong>
            <p>${escapeHtml(targetSummary)}</p>
          </div>
        </div>
      </div>
    </section>
  `;
}

function renderLatestRequestSummary(context) {
  if (!context?.latest_request_id) return "";
  return `
    <section class="latest-request-summary" aria-label="Latest request">
      <span class="small-badge good">Latest request</span>
      <div>
        <strong>${escapeHtml(context.latest_request_id)}</strong>
        ${context.latest_request_path ? pathLine(context.latest_request_path, 88) : ""}
        <p>${escapeHtml(context.latest_request_excerpt || "Latest submitted operator request is saved for this stage.")}</p>
      </div>
    </section>
  `;
}

async function renderRequestChange() {
  let documents = {};
  const context = activeStageView()?.diagnostics?.request_change || {};
  const item = activeStageItem();
  if (item && Number(item.attempt_count || 0) > 0) {
    try {
      const params = new URLSearchParams({stage: state.activeStage});
      if (state.activeRunId) params.set("run_id", state.activeRunId);
      const artifacts = await api(`/api/artifacts?${params.toString()}`);
      documents = artifacts.documents || {};
    } catch (error) {
      documents = {};
    }
  }
  const targets = requestChangeTargetEntries(documents, context);
  const targetBody = targets.length ? targets.map(([key, path]) => `
    <label class="target-option">
      <input type="checkbox" data-intervention-target="${escapeHtml(path)}">
      <span><strong>${escapeHtml(interventionTargetLabel(key))}</strong>${pathLine(path, 82)}</span>
    </label>
  `).join("") : `<div class="empty-state">No current-stage target documents available yet. The request can still run against the stage scope.</div>`;
  document.getElementById("cockpitContent").innerHTML = `
    <section class="request-change-screen">
      <section class="surface">
        <div class="surface-title">
          <span>Request Change / Intervention Composer</span>
          <span class="small-badge">${escapeHtml(context.status || state.activeStage)}</span>
        </div>
        ${renderLatestRequestSummary(context)}
        <div class="request-change-grid">
          <div class="intervention-form">
            <div class="form-field">
              <label for="operatorRequestText">Operator request</label>
              <textarea id="operatorRequestText" placeholder="Add rollback risks to the plan and update stage-result evidence."></textarea>
            </div>
            <div class="form-field">
              <div class="target-documents-title">Target documents</div>
              <div class="target-documents">${targetBody}</div>
            </div>
            <div class="question-actions">
              <button id="submitInterventionButton" type="button">Submit & run</button>
              <p id="interventionReadinessNote" class="form-readiness-note" role="status"></p>
            </div>
          </div>
          <aside class="intervention-preview-column">
            <div class="intervention-diff-preview">
              <div class="surface-title">
                <span>Diff Preview</span>
                <span class="small-badge">pre-run</span>
              </div>
              <div id="interventionDiffPreview">
                ${renderInterventionDiffPreview("", [])}
              </div>
            </div>
          </aside>
        </div>
      </section>
      ${renderRequestChangeAuditLog(context)}
    </section>
  `;
  updateInterventionPreview();
}

function renderApprovalQueueSummary({requests, decisions, pendingIds, diagnostics}) {
  const approved = decisions.filter(
    (decision) => decision.action === "allow_once" || decision.action === "allow_for_session"
  ).length;
  const denied = decisions.filter((decision) => decision.action === "deny").length;
  const cancelled = decisions.filter((decision) => decision.action === "cancel").length;
  const metrics = [
    ["Requested", diagnostics?.requested_count ?? requests.length],
    ["Pending", diagnostics?.pending_count ?? pendingIds.size],
    ["Approved", diagnostics?.approved_count ?? approved],
    ["Denied", diagnostics?.denied_count ?? denied],
    ["Cancelled", diagnostics?.cancelled_count ?? cancelled]
  ];
  return `
    <div class="approval-summary-grid">
      ${metrics.map(([label, value]) => `
        <div class="metric approval-summary-metric">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `).join("")}
    </div>
  `;
}

function approvalAuditCounts({requests, decisions, pendingIds, diagnostics, auditHistory}) {
  const rows = Array.isArray(auditHistory) ? auditHistory : [];
  const rowCount = (status) => rows.filter((row) => row.status === status).length;
  const countValue = (diagnosticValue, rowValue, fallbackValue = 0) =>
    diagnosticValue ?? (rowValue || fallbackValue);
  const approved = decisions.filter((decision) => decision.action === "allow_once" || decision.action === "allow_for_session").length;
  const denied = decisions.filter((decision) => decision.action === "deny").length;
  const cancelled = decisions.filter((decision) => decision.action === "cancel").length;
  return {
    requested: countValue(diagnostics?.requested_count, rows.length, requests.length),
    pending: countValue(diagnostics?.pending_count, rowCount("pending"), pendingIds.size),
    approved: countValue(diagnostics?.approved_count, rowCount("approved"), approved),
    denied: countValue(diagnostics?.denied_count, rowCount("denied"), denied),
    cancelled: countValue(diagnostics?.cancelled_count, rowCount("cancelled"), cancelled),
    policyBlocked: countValue(diagnostics?.policy_blocked_count, rowCount("policy-blocked"))
  };
}

function renderApprovalDecisionSpotlight({requests, decisions, pendingIds, diagnostics, auditHistory}) {
  const counts = approvalAuditCounts({requests, decisions, pendingIds, diagnostics, auditHistory});
  let tone = "good";
  let title = "No runtime approvals are waiting";
  let body = (
    "Runtime approval history is available for audit, but the current job is not blocked "
    + "on an operator decision."
  );
  let primary = "Primary action: inspect audit log when reviewing safety evidence";
  if (counts.pending) {
    tone = "warn";
    title = "Runtime approval required";
    body = (
      `${counts.pending} request${counts.pending === 1 ? "" : "s"} must be decided before `
      + "the runtime can continue. Review command, cwd, paths, and diff preview before "
      + "allowing or denying."
    );
    primary = "Primary action: decide pending request";
  } else if (counts.policyBlocked) {
    tone = "bad";
    title = "Runtime request blocked by policy";
    body = (
      `${counts.policyBlocked} request${counts.policyBlocked === 1 ? "" : "s"} were `
      + "blocked by policy. Inspect the audit log and adjust scope or runtime policy "
      + "before rerunning."
    );
    primary = "Primary action: inspect policy-blocked audit row";
  } else if (counts.denied || counts.cancelled) {
    tone = "bad";
    title = "Runtime approval stopped";
    body = (
      `${counts.denied} denied and ${counts.cancelled} cancelled decision`
      + `${counts.denied + counts.cancelled === 1 ? "" : "s"} are recorded. `
      + "Inspect the reason before rerunning this stage."
    );
    primary = "Primary action: inspect decision reason";
  } else if (counts.approved) {
    title = "Runtime approvals recorded";
    body = (
      `${counts.approved} approved decision${counts.approved === 1 ? "" : "s"} are saved `
      + "in the audit ledger for this run."
    );
    primary = "Primary action: continue reviewing evidence";
  }
  return `
    <div class="approval-decision-spotlight ${escapeHtml(tone)}"
      data-approval-decision-spotlight role="status" aria-live="polite">
      <div class="approval-decision-copy">
        <span class="small-badge ${escapeHtml(tone)}">approval audit</span>
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(body)}</p>
        <small>${escapeHtml(primary)}</small>
      </div>
      <div class="approval-decision-facts">
        <span><strong>Pending</strong>${escapeHtml(counts.pending)}</span>
        <span><strong>Approved</strong>${escapeHtml(counts.approved)}</span>
        <span><strong>Denied</strong>${escapeHtml(counts.denied)}</span>
        <span><strong>Cancelled</strong>${escapeHtml(counts.cancelled)}</span>
        <span><strong>Policy blocked</strong>${escapeHtml(counts.policyBlocked)}</span>
      </div>
    </div>
  `;
}

function renderApprovalDiffPreview(request) {
  const payload = request.payload || {};
  const diff = payload.diff || payload.patch || payload.unified_diff || payload.preview || payload.changes;
  if (diff) {
    return `
      <div class="approval-diff-preview">
        <div class="surface-title compact"><span>Diff Preview</span><span class="small-badge">runtime</span></div>
        <pre class="diff-preview">${escapeHtml(typeof diff === "string" ? diff : JSON.stringify(diff, null, 2))}</pre>
      </div>
    `;
  }
  const paths = request.paths || [];
  const pathBody = paths.length
    ? paths.map((path) => pathLine(path, 86)).join("")
    : `<span class="muted">No normalized paths supplied by runtime.</span>`;
  return `
    <div class="approval-diff-preview">
      <div class="surface-title compact"><span>Diff Preview</span><span class="small-badge">not supplied</span></div>
      <div class="diff-preview-empty">
        <p>The runtime did not provide a unified diff. Review command, payload, cwd, and affected paths before deciding.</p>
        ${pathBody}
      </div>
    </div>
  `;
}

function renderApprovalRequestCard(request, decision, pendingIds) {
  const payload = request.payload || {};
  const command = payload.command || payload.cmd || "";
  const paths = request.paths || [];
  const pending = pendingIds.has(request.id);
  const decisionBadge = decision
    ? `<span class="small-badge ${decision.action === "deny" || decision.action === "cancel" ? "bad" : "good"}">${escapeHtml(decision.action)}</span>`
    : pending ? `<span class="small-badge warn">pending</span>` : `<span class="small-badge">recorded</span>`;
  const pathBody = paths.length
    ? paths.map((path) => pathLine(path, 86)).join("")
    : `<span class="muted">No normalized paths</span>`;
  const actions = pending ? `
    <div class="approval-actions">
      <button data-operator-request="${escapeHtml(request.id)}" data-operator-action="allow_once" type="button">Allow once</button>
      <button data-operator-request="${escapeHtml(request.id)}" data-operator-action="allow_for_session" type="button">Allow session</button>
      <button data-operator-request="${escapeHtml(request.id)}" data-operator-action="deny" class="secondary" type="button">Deny</button>
      <button data-operator-request="${escapeHtml(request.id)}" data-operator-action="cancel" class="danger" type="button">Cancel</button>
    </div>
  ` : "";
  return `
    <article class="approval-card ${pending ? "pending" : ""}">
      <div class="question-head">
        <strong>${escapeHtml(request.kind || "unknown")} / ${escapeHtml(request.tool_name || "runtime")}</strong>
        ${decisionBadge}
      </div>
      <div class="approval-meta-grid">
        <div><span>Risk</span><strong>${escapeHtml(request.risk || "unknown")}</strong></div>
        <div><span>Created</span><strong>${escapeHtml(request.created_at_utc || "-")}</strong></div>
        <div><span>Suggestions</span><strong>${escapeHtml((request.suggestions || []).join(", ") || "operator decision")}</strong></div>
      </div>
      <div class="panel-list">
        <div class="panel-item"><strong>Request</strong><span>${escapeHtml(request.id)}</span></div>
        <div class="panel-item"><strong>Runtime / stage</strong><span>${escapeHtml(request.runtime_id)} / ${escapeHtml(request.stage)}</span></div>
        ${command ? `<div class="panel-item"><strong>Command</strong><code>${escapeHtml(command)}</code></div>` : ""}
        <div class="panel-item"><strong>CWD</strong>${pathLine(request.cwd || "not provided", 86)}</div>
        <div class="panel-item"><strong>Paths</strong><span>${pathBody}</span></div>
        <div class="panel-item"><strong>Payload</strong><pre class="payload-preview">${escapeHtml(JSON.stringify(payload, null, 2))}</pre></div>
        ${decision ? `<div class="panel-item"><strong>Decision</strong><span>${escapeHtml(decision.source)} / ${escapeHtml(decision.reason || "no reason")}</span></div>` : ""}
      </div>
      ${renderApprovalDiffPreview(request)}
      ${actions}
    </article>
  `;
}

function renderApprovalAuditLog(requests, decisions, pendingIds, diagnostics = null, auditHistory = null) {
  const serverRows = Array.isArray(auditHistory) ? auditHistory : [];
  if (serverRows.length) {
    return `
      <section class="surface audit-log-panel">
        <div class="surface-title">
          <span>Approval Audit Log</span>
          <span class="small-badge">${escapeHtml(serverRows.length)} records</span>
        </div>
        <div class="table-wrap approval-audit-wrap">
          <table class="activity-table approval-audit-table">
            <thead><tr><th>Requested</th><th>Status</th><th>Runtime / stage</th><th>Command / scope</th><th>Decision</th></tr></thead>
            <tbody>
              ${serverRows.map((row) => {
                const status = row.status || "recorded";
                const tone = status === "pending" ? "warn" : status === "denied" || status === "cancelled" || status === "policy-blocked" ? "bad" : "good";
                const command = row.command || row.tool_name || row.kind || "runtime request";
                const scope = [row.cwd, ...(Array.isArray(row.paths) ? row.paths : [])].filter(Boolean).join(" / ");
                return `
                  <tr>
                    <td>${escapeHtml(row.created_at_utc || "-")}</td>
                    <td><span class="small-badge ${tone}">${escapeHtml(status)}</span></td>
                    <td>${escapeHtml(row.runtime_id || "-")} / ${escapeHtml(row.stage || "-")}</td>
                    <td><strong>${escapeHtml(command)}</strong>${scope ? `<br><span class="muted">${escapeHtml(scope)}</span>` : ""}</td>
                    <td>${escapeHtml(row.decision_action || "-")} ${row.decision_source ? `by ${escapeHtml(row.decision_source)}` : ""}${row.decision_reason ? `<br><span class="muted">${escapeHtml(row.decision_reason)}</span>` : ""}</td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      </section>
    `;
  }
  const decisionByRequest = new Map();
  decisions.forEach((decision) => decisionByRequest.set(decision.request_id, decision));
  const rows = requests.map((request) => {
    const decision = decisionByRequest.get(request.id);
    const status = decision ? decision.action : pendingIds.has(request.id) ? "pending" : "recorded";
    return {request, decision, status};
  });
  if (!rows.length && diagnostics?.requested_count) {
    return `
      <section class="surface audit-log-panel">
        <div class="surface-title">
          <span>Approval Audit Log</span>
          <span class="small-badge">${escapeHtml(diagnostics.requested_count)} saved</span>
        </div>
        <div class="audit-list">
          <div class="audit-row">
            <span class="small-badge ${diagnostics.pending_count ? "warn" : "good"}">${escapeHtml(diagnostics.status || "saved")}</span>
            <div>
              <strong>Saved approval ledger</strong>
              <p>${escapeHtml(diagnostics.requested_count)} requested, ${escapeHtml(diagnostics.pending_count)} pending, ${escapeHtml(diagnostics.approved_count)} approved, ${escapeHtml(diagnostics.denied_count)} denied, ${escapeHtml(diagnostics.cancelled_count)} cancelled.</p>
              ${diagnostics.requests_path ? pathLine(diagnostics.requests_path, 92) : ""}
              ${diagnostics.decisions_path ? pathLine(diagnostics.decisions_path, 92) : ""}
            </div>
          </div>
        </div>
      </section>
    `;
  }
  if (!rows.length) {
    return `<section class="surface audit-log-panel"><div class="surface-title"><span>Approval Audit Log</span></div><div class="empty-state">No runtime approval records for this job.</div></section>`;
  }
  return `
    <section class="surface audit-log-panel">
      <div class="surface-title">
        <span>Approval Audit Log</span>
        <span class="small-badge">${escapeHtml(rows.length)} records</span>
      </div>
      <div class="table-wrap approval-audit-wrap">
        <table class="activity-table approval-audit-table">
          <thead><tr><th>Requested</th><th>Approval</th><th>Decision</th><th>By</th><th>Notes / reason</th></tr></thead>
          <tbody>
            ${rows.map(({request, decision, status}) => `
              <tr>
                <td>${escapeHtml(request.created_at_utc || "-")}</td>
                <td>${escapeHtml(request.kind || "unknown")} / ${escapeHtml(request.tool_name || "runtime")}</td>
                <td><span class="small-badge ${status === "pending" ? "warn" : status === "deny" || status === "cancel" ? "bad" : "good"}">${escapeHtml(status)}</span></td>
                <td>${escapeHtml(decision?.source || "-")}</td>
                <td>${escapeHtml(decision?.reason || request.id)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function renderApprovalsSurface({view, diagnostics, requests, decisions, pendingIds}) {
  const decisionByRequest = new Map();
  decisions.forEach((decision) => decisionByRequest.set(decision.request_id, decision));
  const auditHistory = view?.audit_history || [];
  const cards = requests.length
    ? requests.map((request) => renderApprovalRequestCard(request, decisionByRequest.get(request.id), pendingIds)).join("")
    : `<div class="empty-state">No runtime operator requests for this job. Saved stage diagnostics are still shown in the queue summary.</div>`;
  const requestPath = view?.requests_path || diagnostics?.requests_path;
  const decisionsPath = view?.decisions_path || diagnostics?.decisions_path;
  return `
    <section class="approval-console-screen">
      <section class="surface">
        <div class="surface-title">
          <span>Approvals / Runtime Requests</span>
          <span class="small-badge ${pendingIds.size || diagnostics?.pending_count ? "warn" : "good"}">${escapeHtml(pendingIds.size || diagnostics?.pending_count || 0)} pending</span>
        </div>
        ${renderApprovalDecisionSpotlight({requests, decisions, pendingIds, diagnostics, auditHistory})}
        ${renderApprovalQueueSummary({requests, decisions, pendingIds, diagnostics})}
        <div class="approval-ledger-paths">
          ${requestPath ? pathLine(`requests: ${requestPath}`, 94) : ""}
          ${decisionsPath ? pathLine(`decisions: ${decisionsPath}`, 94) : ""}
        </div>
        <div class="question-list approval-queue">${cards}</div>
      </section>
      ${renderApprovalAuditLog(requests, decisions, pendingIds, diagnostics, auditHistory)}
    </section>
  `;
}

async function renderApprovals() {
  const content = document.getElementById("cockpitContent");
  const diagnostics = activeStageView()?.diagnostics?.approvals || null;
  if (!state.activeJobId) {
    content.innerHTML = renderApprovalsSurface({
      view: null,
      diagnostics,
      requests: [],
      decisions: [],
      pendingIds: new Set(diagnostics?.pending_request_ids || [])
    });
    return;
  }
  try {
    const view = await api(`/api/jobs/${encodeURIComponent(state.activeJobId)}/operator-requests`);
    const requests = view.requests || [];
    const decisions = view.decisions || [];
    const pendingIds = new Set(view.pending_request_ids || []);
    content.innerHTML = renderApprovalsSurface({view, diagnostics, requests, decisions, pendingIds});
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function submitApproval(requestId, action) {
  if (!state.activeJobId) return;
  await postJson(`/api/jobs/${encodeURIComponent(state.activeJobId)}/operator-requests/${encodeURIComponent(requestId)}/decision`, {action});
  toast(`Runtime approval ${action}.`);
  await renderApprovals();
}

async function submitIntervention() {
  const readinessReason = runtimeReadinessMessage();
  if (readinessReason) {
    updateSubmitInterventionState();
    toast(readinessReason);
    return;
  }
  if (!ensureRunnableRuntime()) return;
  const textarea = document.getElementById("operatorRequestText");
  const request = textarea?.value?.trim() || "";
  if (!request) {
    toast("Request text is required.");
    return;
  }
  const targetDocuments = selectedInterventionTargets();
  const payload = {
    stage: state.activeStage,
    runtime: state.selectedRuntime,
    request,
    target_documents: targetDocuments,
    log_follow: true
  };
  if (state.activeRunId) payload.run_id = state.activeRunId;
  const job = await postJson("/api/stage/interact", payload);
  await startJobPolling(job);
}
