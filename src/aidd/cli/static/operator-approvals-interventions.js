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
  if (!button) return;
  button.disabled = !selectedRuntimeReady() || !String(textarea?.value || "").trim();
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
  const approved = decisions.filter((decision) => decision.action === "allow_once" || decision.action === "allow_for_session").length;
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

function renderApprovalAuditLog(requests, decisions, pendingIds, diagnostics = null) {
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
        ${renderApprovalQueueSummary({requests, decisions, pendingIds, diagnostics})}
        <div class="approval-ledger-paths">
          ${requestPath ? pathLine(`requests: ${requestPath}`, 94) : ""}
          ${decisionsPath ? pathLine(`decisions: ${decisionsPath}`, 94) : ""}
        </div>
        <div class="question-list approval-queue">${cards}</div>
      </section>
      ${renderApprovalAuditLog(requests, decisions, pendingIds, diagnostics)}
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
