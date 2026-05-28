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

function updateSubmitInterventionState() {
  const textarea = document.getElementById("operatorRequestText");
  const button = document.getElementById("submitInterventionButton");
  if (!button) return;
  button.disabled = !selectedRuntimeReady() || !String(textarea?.value || "").trim();
}

async function renderRequestChange() {
  let documents = {};
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
  const targets = interventionTargetEntries(documents);
  const targetBody = targets.length ? targets.map(([key, path]) => `
    <label class="target-option">
      <input type="checkbox" data-intervention-target="${escapeHtml(path)}">
      <span><strong>${escapeHtml(interventionTargetLabel(key))}</strong>${pathLine(path, 82)}</span>
    </label>
  `).join("") : `<div class="empty-state">No current-stage target documents available yet. The request can still run against the stage scope.</div>`;
  document.getElementById("cockpitContent").innerHTML = `
    <section class="surface">
      <div class="surface-title">
        <span>Request change</span>
        <span class="small-badge">${escapeHtml(state.activeStage)}</span>
      </div>
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
    </section>
  `;
  updateSubmitInterventionState();
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
    <article class="approval-card">
      <div class="question-head">
        <strong>${escapeHtml(request.kind || "unknown")} / ${escapeHtml(request.tool_name || "runtime")}</strong>
        ${decisionBadge}
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
      ${actions}
    </article>
  `;
}

async function renderApprovals() {
  const content = document.getElementById("cockpitContent");
  if (!state.activeJobId) {
    content.innerHTML = `<div class="empty-state">No active runtime approval job.</div>`;
    return;
  }
  try {
    const view = await api(`/api/jobs/${encodeURIComponent(state.activeJobId)}/operator-requests`);
    const requests = view.requests || [];
    const decisions = view.decisions || [];
    const pendingIds = new Set(view.pending_request_ids || []);
    const decisionByRequest = new Map();
    decisions.forEach((decision) => decisionByRequest.set(decision.request_id, decision));
    const cards = requests.length
      ? requests.map((request) => renderApprovalRequestCard(request, decisionByRequest.get(request.id), pendingIds)).join("")
      : `<div class="empty-state">No runtime operator requests for this job.</div>`;
    content.innerHTML = `
      <section class="surface">
        <div class="surface-title">
          <span>Runtime approvals</span>
          <span class="small-badge ${pendingIds.size ? "warn" : "good"}">${escapeHtml(pendingIds.size)} pending</span>
        </div>
        <div class="question-list">${cards}</div>
      </section>
    `;
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
  const targetDocuments = Array.from(document.querySelectorAll("[data-intervention-target]:checked"))
    .map((input) => input.dataset.interventionTarget)
    .filter(Boolean);
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
