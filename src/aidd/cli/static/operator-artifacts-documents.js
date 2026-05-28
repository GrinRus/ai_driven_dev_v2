const PREFERRED_ARTIFACT_KEYS = [
  "idea_brief",
  "research_notes",
  "plan",
  "review_spec_report",
  "tasklist",
  "implementation_report",
  "review_report",
  "qa_report",
  "stage_result",
  "validator_report",
  "questions",
  "input_bundle",
  "stage_brief",
  "repair_brief",
  "operator_request",
  "answers"
];
const MAX_ARTIFACT_READ_BYTES = 262144;

function byteRangeSummary(view) {
  const start = Number(view?.start_byte || 0);
  const end = Number(view?.end_byte || 0);
  const total = Number(view?.byte_size || 0);
  return `${start}-${end} of ${total} bytes`;
}

function renderTruncationNotice(kind, view, mode = "") {
  if (!view?.truncated) return "";
  const direction = view.truncated_head && view.truncated_tail
    ? "selected range"
    : view.truncated_head
      ? "latest content"
      : "first content";
  const subject = kind === "artifact" ? "Artifact view truncated" : "Runtime log truncated";
  const artifactHint = mode === "preview"
    ? "Switch to Source for a larger bounded read, or open the folder for the full file."
    : "Source view is bounded. Open the folder for the full file.";
  const logHint = "Full runtime.log remains on disk and available through CLI log inspection.";
  const hint = kind === "artifact" ? artifactHint : logHint;
  return `
    <div class="truncation-notice" role="status">
      <strong>${subject}</strong>
      <span>Showing ${escapeHtml(direction)} (${escapeHtml(byteRangeSummary(view))}). ${escapeHtml(hint)}</span>
    </div>
  `;
}

function renderPrimaryArtifact() {
  const artifact = state.dashboard?.primary_artifact;
  if (!artifact) {
    return `<div class="empty-state">No primary artifact for this stage yet.</div>`;
  }
  const truncated = artifact.truncated ? `<p class="muted">Preview truncated at ${escapeHtml(artifact.excerpt.length)} characters.</p>` : "";
  const body = artifact.content_type === "text/markdown"
    ? `<div class="markdown-preview">${renderMarkdown(artifact.excerpt)}</div>`
    : `<pre>${escapeHtml(artifact.excerpt)}</pre>`;
  return `
    <div class="viewer-header">
      <div>
        <strong>${escapeHtml(artifact.key)}</strong>
        ${pathLine(`${artifact.path} / ${artifact.byte_size} bytes`, 72)}
      </div>
      <button data-open-artifact="${escapeHtml(artifact.path)}" class="secondary" type="button">Open folder</button>
    </div>
    <div class="primary-artifact">${body}${truncated}</div>
  `;
}

function preferredArtifactKey(documents) {
  for (const key of PREFERRED_ARTIFACT_KEYS) {
    if (Object.prototype.hasOwnProperty.call(documents, key)) return key;
  }
  return Object.keys(documents)[0] || "";
}

function workbenchStatusClass(status) {
  const normalized = String(status || "").toLowerCase();
  if (["present", "satisfied", "pass", "valid", "succeeded"].includes(normalized)) return "good";
  if (["missing", "fail", "failed", "invalid", "blocked"].includes(normalized)) return "bad";
  if (["warning", "warn", "unknown"].includes(normalized)) return "warn";
  return "";
}

function renderWorkbenchTree(workbench) {
  const references = workbench.references || [];
  const documents = references.filter((ref) => ref.kind === "document");
  const secondary = references.filter((ref) => ref.kind !== "document");
  const docs = documents.map((ref) => `
    <button class="artifact-doc ${ref.label === workbench.selected_key ? "active" : ""}" data-artifact-key="${escapeHtml(ref.label)}" type="button">
      ${escapeHtml(ref.label)}
      <small title="${escapeHtml(ref.path)}">${escapeHtml(compactPath(ref.path, 64))}</small>
    </button>
  `).join("") || `<div class="empty-state">No document artifacts.</div>`;
  const refs = secondary.map((ref) => `
    <button class="artifact-doc" data-open-artifact="${escapeHtml(ref.path)}" type="button">
      ${escapeHtml(ref.label)}
      <small>${escapeHtml(ref.kind)} / ${escapeHtml(compactPath(ref.path, 58))}</small>
    </button>
  `).join("") || `<div class="empty-state">No logs or repair refs.</div>`;
  return `
    <div class="surface-title">Artifact tree</div>
    <div class="artifact-list">${docs}</div>
    <div class="surface-title compact">Logs / repair refs</div>
    <div class="artifact-list">${refs}</div>
  `;
}

function renderRequirementList(requirements) {
  return (requirements || []).map((item) => `
    <div class="workbench-side-row">
      <span class="small-badge ${workbenchStatusClass(item.status)}">${escapeHtml(item.status)}</span>
      <span>
        <strong>${escapeHtml(item.label)}</strong>
        <small>${escapeHtml(item.kind)} / ${escapeHtml(item.source)}</small>
        ${item.path ? pathLine(item.path, 60) : ""}
      </span>
    </div>
  `).join("") || `<div class="empty-state">No contract requirements resolved.</div>`;
}

function renderValidationResults(results) {
  return (results || []).map((item) => `
    <div class="workbench-side-row">
      <span class="small-badge ${workbenchStatusClass(item.status)}">${escapeHtml(item.status)}</span>
      <span>
        <strong>${escapeHtml(item.label)}</strong>
        <small>${escapeHtml(item.detail)}</small>
        ${item.path ? pathLine(item.path, 60) : ""}
      </span>
    </div>
  `).join("") || `<div class="empty-state">No validation results yet.</div>`;
}

function renderMissingEvidence(requirements) {
  const missing = (requirements || []).filter((item) => item.status === "missing");
  return missing.map((item) => `
    <div class="workbench-side-row">
      <span class="small-badge bad">missing</span>
      <span>
        <strong>${escapeHtml(item.label)}</strong>
        <small>${escapeHtml(item.kind)} from ${escapeHtml(item.source)}</small>
        ${item.path ? pathLine(item.path, 60) : ""}
      </span>
    </div>
  `).join("") || `<div class="empty-state">No missing evidence for the selected document.</div>`;
}

function renderWorkbenchReferences(references) {
  return (references || []).map((ref) => `
    <button class="artifact-row" data-open-artifact="${escapeHtml(ref.path)}" type="button">
      <span><strong>${escapeHtml(ref.label)}</strong>${pathLine(ref.path, 58)}</span>
      <span class="small-badge">${escapeHtml(ref.kind)}</span>
    </button>
  `).join("") || `<div class="empty-state">No references linked.</div>`;
}

function renderVersionHistory(versions) {
  return (versions || []).map((version) => `
    <button class="artifact-row" data-open-artifact="${escapeHtml(version.path)}" type="button">
      <span>
        <strong>${escapeHtml(version.label)}</strong>
        <span>${escapeHtml(version.source)} / ${escapeHtml(version.updated_at_utc || "timestamp unavailable")}</span>
        ${pathLine(version.path, 58)}
      </span>
      <span class="small-badge">v${escapeHtml(version.attempt_number)}</span>
    </button>
  `).join("") || `<div class="empty-state">No version history for this document.</div>`;
}

function renderWorkbenchDiff(workbench) {
  const inputs = workbench.diff_inputs || [];
  const inputRows = inputs.map((item) => `
    <button class="artifact-row" data-open-artifact="${escapeHtml(item.path)}" type="button">
      <span>
        <strong>${escapeHtml(item.label)}</strong>
        <span>${escapeHtml(item.kind)}${item.attempt_number ? ` / attempt ${escapeHtml(item.attempt_number)}` : ""}</span>
        ${pathLine(item.path, 78)}
      </span>
      <span class="small-badge">diff</span>
    </button>
  `).join("") || `<div class="empty-state">No diff inputs available for this document.</div>`;
  return `
    <div class="workbench-diff-panel">
      <div class="surface-title">Diff controls</div>
      <p>Compare the selected document with another current artifact or the previous attempt. Source files remain read-only.</p>
      <div class="recent-artifacts">${inputRows}</div>
    </div>
  `;
}

function renderWorkbenchDocumentBody(workbench) {
  const documentView = workbench.document;
  if (!documentView || documentView.status !== "present") {
    return `
      <div class="empty-state">
        <strong>${escapeHtml(documentView?.status || "missing")}</strong>
        <span>${escapeHtml(documentView?.message || "Selected document is not available.")}</span>
      </div>
    `;
  }
  if (state.artifactViewMode === "diff") return renderWorkbenchDiff(workbench);
  const view = state.artifactViewMode === "source"
    ? documentView.source || documentView.preview
    : documentView.preview || documentView.source;
  if (!view) {
    return `<div class="empty-state">No bounded ${escapeHtml(state.artifactViewMode)} view available.</div>`;
  }
  const body = state.artifactViewMode === "source" || view.content_type !== "text/markdown"
    ? `<pre>${escapeHtml(view.text)}</pre>`
    : `<div class="markdown-preview">${renderMarkdown(view.text)}</div>`;
  return `${renderTruncationNotice("artifact", view, state.artifactViewMode)}${body}`;
}

function renderWorkbenchViewer(workbench) {
  const previewActive = state.artifactViewMode === "preview" ? " active" : "";
  const sourceActive = state.artifactViewMode === "source" ? " active" : "";
  const diffActive = state.artifactViewMode === "diff" ? " active" : "";
  const documentView = workbench.document || {};
  return `
    <div class="viewer-header">
      <div>
        <strong>${escapeHtml(documentView.key || workbench.selected_key)}</strong>
        ${pathLine(`${documentView.path || "path unavailable"} / ${documentView.byte_size ?? "unknown"} bytes`, 78)}
      </div>
      <div class="viewer-modes">
        <button data-artifact-mode="preview" class="${previewActive}" type="button">Preview</button>
        <button data-artifact-mode="source" class="${sourceActive}" type="button">Source</button>
        <button data-artifact-mode="diff" class="${diffActive}" type="button">Diff</button>
        ${documentView.path ? `<button data-open-artifact="${escapeHtml(documentView.path)}" class="secondary" type="button">Open folder</button>` : ""}
      </div>
    </div>
    <div class="workbench-main">
      <section class="workbench-document-pane">
        ${renderWorkbenchDocumentBody(workbench)}
      </section>
      <aside class="workbench-sidebar">
        <section class="surface">
          <div class="surface-title">Contract requirements</div>
          ${renderRequirementList(workbench.requirements)}
        </section>
        <section class="surface">
          <div class="surface-title">Validation results</div>
          ${renderValidationResults(workbench.validation_results)}
        </section>
        <section class="surface">
          <div class="surface-title">Missing evidence</div>
          ${renderMissingEvidence(workbench.requirements)}
        </section>
        <section class="surface">
          <div class="surface-title">References</div>
          <div class="recent-artifacts">${renderWorkbenchReferences(workbench.references)}</div>
        </section>
        <section class="surface">
          <div class="surface-title">Version history</div>
          <div class="recent-artifacts">${renderVersionHistory(workbench.versions)}</div>
        </section>
      </aside>
    </div>
  `;
}

async function loadArtifactDocument(key) {
  const tree = document.getElementById("workbenchTree");
  const viewer = document.getElementById("artifactViewer");
  if (!viewer) return;
  try {
    const params = new URLSearchParams({stage: state.activeStage});
    if (key) params.set("key", key);
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    params.set("source_limit", String(MAX_ARTIFACT_READ_BYTES));
    const workbench = await api(`/api/stage/workbench?${params.toString()}`);
    state.activeArtifactKey = workbench.selected_key;
    if (tree) tree.innerHTML = renderWorkbenchTree(workbench);
    viewer.innerHTML = renderWorkbenchViewer(workbench);
  } catch (error) {
    viewer.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function renderArtifacts() {
  const item = activeStageItem();
  if (!item || Number(item.attempt_count || 0) <= 0) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">No artifacts for this stage yet.</div>`;
    return;
  }
  document.getElementById("cockpitContent").innerHTML = `
    <div class="artifact-layout stage-document-workbench">
      <aside id="workbenchTree" class="surface workbench-tree">
        <div class="empty-state loading-state">Loading artifact tree...</div>
      </aside>
      <section id="artifactViewer" class="artifact-viewer">
        <div class="empty-state loading-state">Loading Stage Document Workbench...</div>
      </section>
    </div>
  `;
  await loadArtifactDocument(state.activeArtifactKey);
}

function artifactKeyForPath(path, stage) {
  const refs = state.dashboard?.recent_artifacts || [];
  const match = refs.find((ref) => ref.path === path && (!stage || ref.stage === stage));
  return match?.key || "";
}

async function inspectArtifactReference({stage, key, path, kind}) {
  const targetStage = stage || state.activeStage;
  state.activeStage = targetStage;
  state.activeArtifactKey = key || artifactKeyForPath(path, targetStage);
  state.activeTab = kind === "log" ? "logs" : "artifacts";
  await fetchDashboard();
  activateTab(state.activeTab);
  await renderAll();
}
