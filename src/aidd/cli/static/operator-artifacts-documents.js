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

async function loadArtifactDocument(key) {
  const viewer = document.getElementById("artifactViewer");
  if (!viewer) return;
  try {
    const params = new URLSearchParams({stage: state.activeStage, key});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    params.set("mode", state.artifactViewMode);
    if (state.artifactViewMode === "source") params.set("limit", String(MAX_ARTIFACT_READ_BYTES));
    const documentView = await api(`/api/artifacts/document?${params.toString()}`);
    const previewActive = state.artifactViewMode === "preview" ? " active" : "";
    const sourceActive = state.artifactViewMode === "source" ? " active" : "";
    const body = state.artifactViewMode === "source"
      ? `<pre>${escapeHtml(documentView.text)}</pre>`
      : `<div class="markdown-preview">${renderMarkdown(documentView.text)}</div>`;
    const truncation = renderTruncationNotice("artifact", documentView, state.artifactViewMode);
    viewer.innerHTML = `
      <div class="viewer-header">
        <div>
          <strong>${escapeHtml(documentView.key)}</strong>
          ${pathLine(`${documentView.path} / ${documentView.byte_size} bytes`, 72)}
        </div>
        <div class="viewer-modes">
          <button data-artifact-mode="preview" class="${previewActive}" type="button">Preview</button>
          <button data-artifact-mode="source" class="${sourceActive}" type="button">Source</button>
          <button data-open-artifact="${escapeHtml(documentView.path)}" class="secondary" type="button">Open folder</button>
        </div>
      </div>
      ${truncation}
      ${body}
    `;
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
  const params = new URLSearchParams({stage: state.activeStage});
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  const view = await api(`/api/artifacts?${params.toString()}`);
  const documents = view.documents || {};
  if (!state.activeArtifactKey || !Object.prototype.hasOwnProperty.call(documents, state.activeArtifactKey)) {
    state.activeArtifactKey = preferredArtifactKey(documents);
  }
  const docs = Object.entries(documents).map(([key, path]) => `
    <button class="artifact-doc ${key === state.activeArtifactKey ? "active" : ""}" data-artifact-key="${escapeHtml(key)}" type="button">
      ${escapeHtml(key)}
      <small title="${escapeHtml(path)}">${escapeHtml(compactPath(path, 64))}</small>
    </button>
  `).join("") || `<div class="empty-state">No document artifacts.</div>`;
  const logs = Object.entries(view.logs || {}).map(([key, path]) => `
    <button class="artifact-doc" data-open-artifact="${escapeHtml(path)}" type="button">
      ${escapeHtml(key)}
      <small title="${escapeHtml(path)}">${escapeHtml(compactPath(path, 64))}</small>
    </button>
  `).join("") || `<div class="empty-state">No log artifacts.</div>`;
  document.getElementById("cockpitContent").innerHTML = `
    <div class="artifact-layout">
      <aside class="surface">
        <div class="surface-title">Documents</div>
        <div class="artifact-list">${docs}</div>
        <div class="surface-title" style="margin-top:12px">Logs</div>
        <div class="artifact-list">${logs}</div>
      </aside>
      <section id="artifactViewer" class="artifact-viewer">Select a document</section>
    </div>
  `;
  if (state.activeArtifactKey) await loadArtifactDocument(state.activeArtifactKey);
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
