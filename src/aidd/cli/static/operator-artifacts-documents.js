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

function artifactCategoryFor(item = {}) {
  const explicit = String(item.category || "").trim();
  if (explicit) return explicit;
  const path = String(item.path || "").replace(/\\/g, "/").toLowerCase();
  const key = String(item.key || item.label || "").replace(/-/g, "_").toLowerCase();
  const kind = String(item.kind || "").toLowerCase();
  if (kind === "log" || ["runtime_log", "events_jsonl"].includes(key)) return "runtime-evidence";
  if (path.includes("/stages/") && path.includes("/output/")) return "published-stage-output";
  if (["input_bundle", "stage_brief", "repair_context", "operator_request"].includes(key) || path.includes("/operator-requests/")) return "runtime-input";
  if (["validator_report", "repair_brief"].includes(key)) return "validation-evidence";
  if (path.includes("project-set.md") || key === "project_set_context") return "project-evidence";
  if (path.includes("/remediations/") || key.includes("lineage")) return "lineage-evidence";
  return "canonical-stage-document";
}

function artifactCategoryLabel(category) {
  return ({
    "canonical-stage-document": "Canonical stage documents",
    "published-stage-output": "Published output mirrors",
    "runtime-input": "Runtime inputs",
    "validation-evidence": "Validation evidence",
    "runtime-evidence": "Runtime evidence",
    "project-evidence": "Project evidence",
    "lineage-evidence": "Lineage evidence"
  })[category] || category;
}

function artifactCategoryDetail(category) {
  return ({
    "canonical-stage-document": "Source-of-truth stage files for operator review, diff, and corrections.",
    "published-stage-output": "Downstream handoff copies under output/. They mirror stage evidence after validation or promotion.",
    "runtime-input": "Prompt and request context supplied to the runtime for this stage.",
    "validation-evidence": "Validator and repair records. Use these to understand gates and recovery decisions.",
    "runtime-evidence": "Raw runtime logs and event streams captured for audit and replay.",
    "project-evidence": "Project-set and repository context used by the governed flow.",
    "lineage-evidence": "Follow-up, remediation, clone, or archive provenance for this run."
  })[category] || "Additional indexed artifact evidence.";
}

function artifactOwnershipBadge(item = {}) {
  const category = artifactCategoryFor(item);
  if (category === "canonical-stage-document") return {label: "canonical source", tone: "good"};
  if (category === "published-stage-output") return {label: "handoff mirror", tone: "warn"};
  if (category === "validation-evidence") return {label: "validation", tone: "warn"};
  if (category === "runtime-evidence") return {label: "runtime log", tone: ""};
  return {label: "evidence", tone: ""};
}

function artifactSupportsDownload(item = {}) {
  const kind = String(item.kind || "").toLowerCase();
  return kind === "document" || kind === "log";
}

function renderArtifactDownloadButton(item = {}, className = "link-button") {
  if (!artifactSupportsDownload(item)) return "";
  return `<button data-download-artifact="${escapeHtml(item.path || "")}" data-download-artifact-key="${escapeHtml(item.key || "")}" data-download-artifact-kind="${escapeHtml(item.kind || "")}" data-download-artifact-stage="${escapeHtml(item.stage || state.activeStage)}" class="${escapeHtml(className)}" type="button">Download</button>`;
}

function canonicalCandidatePath(path) {
  return String(path || "").replace("/output/", "/");
}

function renderArtifactOwnershipNote(item = {}) {
  const category = artifactCategoryFor(item);
  const badge = artifactOwnershipBadge({...item, category});
  const path = String(item.path || "");
  const canonicalPath = canonicalCandidatePath(path);
  let title = "Artifact evidence";
  let detail = artifactCategoryDetail(category);
  let extra = "";
  if (category === "canonical-stage-document") {
    title = "Canonical source of truth";
    detail = "Use this stage document for review, source inspection, and scoped corrections. Output mirrors publish validated copies downstream.";
  } else if (category === "published-stage-output") {
    title = "Published handoff mirror";
    detail = "Downstream stages consume this output/ copy. If validation promoted a misplaced file, inspect the canonical stage document and validator report before treating it as source.";
    if (canonicalPath !== path) extra = pathLine(`Canonical stage path: ${canonicalPath}`, 82);
  } else if (category === "validation-evidence") {
    title = "Validation and repair evidence";
    detail = "This explains validator gates and recovery. It is not the primary runtime-authored stage document.";
  }
  return `
    <div class="artifact-ownership-note ${escapeHtml(category)}" role="note">
      <span class="small-badge ${escapeHtml(badge.tone)}">${escapeHtml(badge.label)}</span>
      <div>
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(detail)}</p>
        ${extra}
      </div>
    </div>
  `;
}

function renderWorkbenchTree(workbench) {
  const references = workbench.references || [];
  const categories = [
    "canonical-stage-document",
    "published-stage-output",
    "runtime-input",
    "validation-evidence",
    "runtime-evidence",
    "project-evidence",
    "lineage-evidence"
  ];
  const grouped = categories.map((category) => {
    const refs = references.filter((ref) => artifactCategoryFor(ref) === category);
    if (!refs.length) return "";
    return `
      <div class="surface-title compact">${escapeHtml(artifactCategoryLabel(category))} <span class="small-badge">${escapeHtml(refs.length)}</span></div>
      <p class="artifact-category-note">${escapeHtml(artifactCategoryDetail(category))}</p>
      <div class="artifact-list">
        ${refs.map((ref) => {
          const document = ref.kind === "document";
          const actionAttr = document
            ? `data-artifact-key="${escapeHtml(ref.label)}"`
            : `data-open-artifact="${escapeHtml(ref.path)}"`;
          const badge = artifactOwnershipBadge(ref);
          return `
            <button class="artifact-doc ${ref.label === workbench.selected_key ? "active" : ""}" ${actionAttr} type="button" aria-pressed="${ref.label === workbench.selected_key ? "true" : "false"}">
              <span class="artifact-doc-title">
                <strong>${escapeHtml(ref.label)}</strong>
                <span class="small-badge ${escapeHtml(badge.tone)}">${escapeHtml(badge.label)}</span>
              </span>
              <small title="${escapeHtml(ref.path)}">${escapeHtml(ref.kind)} / ${escapeHtml(compactPath(ref.path, 58))}</small>
            </button>
          `;
        }).join("")}
      </div>
    `;
  }).filter(Boolean).join("");
  return `
    <div class="surface-title">Artifact categories</div>
    ${grouped || `<div class="empty-state">No artifacts indexed for this stage.</div>`}
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
      <span class="small-badge ${escapeHtml(artifactOwnershipBadge(ref).tone)}">${escapeHtml(artifactOwnershipBadge(ref).label)}</span>
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

function workbenchSelectedDocumentView(workbench) {
  const documentView = workbench.document;
  if (!documentView || documentView.status !== "present") return null;
  return state.artifactViewMode === "source"
    ? documentView.source || documentView.preview
    : documentView.preview || documentView.source;
}

function markdownHeadingSummary(text) {
  return String(text ?? "")
    .split(/\r?\n/)
    .map((line) => {
      const match = line.match(/^(#{1,4})\s+(.+)$/);
      if (!match) return null;
      return {
        level: match[1].length,
        label: match[2]
          .replace(/[`*_#[\]]/g, "")
          .replace(/\s+/g, " ")
          .trim()
      };
    })
    .filter((heading) => heading && heading.label)
    .slice(0, 10);
}

function renderWorkbenchTableOfContents(workbench) {
  if (state.artifactViewMode === "diff") {
    return `
      <section class="workbench-toc" aria-label="Table of Contents">
        <div class="surface-title compact">Table of Contents</div>
        <div class="empty-state">Switch to Preview or Source to inspect document headings.</div>
      </section>
    `;
  }
  const view = workbenchSelectedDocumentView(workbench);
  const headings = markdownHeadingSummary(view?.text || "");
  return `
    <section class="workbench-toc" aria-label="Table of Contents">
      <div class="surface-title compact">
        <span>Table of Contents</span>
        <span class="small-badge">${escapeHtml(headings.length)} headings</span>
      </div>
      <ol class="workbench-toc-list">
        ${headings.length ? headings.map((heading) => `
          <li class="toc-level-${escapeHtml(heading.level)}">${escapeHtml(heading.label)}</li>
        `).join("") : `<li>No headings in the visible document window.</li>`}
      </ol>
    </section>
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
  const view = workbenchSelectedDocumentView(workbench);
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
  const evidenceInspector = renderWorkbenchEvidenceInspector(workbench);
  return `
    <div class="viewer-header">
      <div>
        <strong>${escapeHtml(documentView.key || workbench.selected_key)}</strong>
        ${pathLine(`${documentView.path || "path unavailable"} / ${documentView.byte_size ?? "unknown"} bytes`, 78)}
      </div>
      <div class="viewer-modes" role="group" aria-label="Document presentation">
        <button data-artifact-mode="preview" class="${previewActive}" type="button" aria-pressed="${state.artifactViewMode === "preview" ? "true" : "false"}">Preview</button>
        <button data-artifact-mode="source" class="${sourceActive}" type="button" aria-pressed="${state.artifactViewMode === "source" ? "true" : "false"}">Source</button>
        <button data-artifact-mode="diff" class="${diffActive}" type="button" aria-pressed="${state.artifactViewMode === "diff" ? "true" : "false"}">Diff</button>
        ${documentView.path ? `<button data-open-artifact="${escapeHtml(documentView.path)}" class="secondary" type="button">Open folder</button>` : ""}
      </div>
    </div>
    ${renderArtifactOwnershipNote({
      key: documentView.key || workbench.selected_key,
      kind: "document",
      path: documentView.path || ""
    })}
    <div class="workbench-main" data-evidence-inspector="${evidenceInspector ? "present" : "absent"}">
      <section class="workbench-document-pane hierarchy-primary document-canvas">
        ${renderWorkbenchTableOfContents(workbench)}
        ${renderWorkbenchDocumentBody(workbench)}
      </section>
      ${evidenceInspector}
    </div>
  `;
}

function renderWorkbenchEvidenceInspector(workbench) {
  const visible = [
    workbench.requirements,
    workbench.validation_results,
    workbench.references,
    workbench.versions
  ].some((items) => Array.isArray(items) && items.length > 0);
  if (!visible) return "";
  return `
      <aside class="workbench-sidebar hierarchy-supporting evidence-inspector">
        <div class="surface-title evidence-inspector-title">Evidence Inspector</div>
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

function evidenceEdgeId(edge) {
  return `${edge.source_id}::${edge.target_id}::${edge.kind}`;
}

function evidenceNodeArtifactKey(node) {
  const nodeId = String(node?.node_id || "");
  if (nodeId.startsWith("document:") || nodeId.startsWith("log:")) {
    return nodeId.split(":").slice(1).join(":");
  }
  return "";
}

function preferredEvidenceArtifactKey(view) {
  const documents = {};
  for (const ref of view.artifact_table || []) {
    if (ref.kind === "document" && ref.key) documents[ref.key] = ref.path || "";
  }
  return preferredArtifactKey(documents);
}

function evidenceStatusClass(status) {
  return workbenchStatusClass(status) || statusClass(status || "unknown");
}

function evidenceNodeIcon(kind) {
  const icons = {
    "stage": "ST",
    "attempt": "AT",
    "document": "MD",
    "mirror": "MR",
    "log": "LG",
    "event": "EV",
    "approval-log": "AL",
    "approval-request": "RQ",
    "approval-decision": "OK"
  };
  return icons[kind] || "AR";
}

function selectedEvidenceSelection(view) {
  const edges = view.edges || [];
  const nodes = view.nodes || [];
  const selectedEdge = edges.find((edge) => evidenceEdgeId(edge) === state.selectedEvidenceEdgeId) || null;
  if (selectedEdge) return {edge: selectedEdge, node: null};
  const preferredKey = state.activeArtifactKey || preferredEvidenceArtifactKey(view);
  const preferredNodeId = state.selectedEvidenceNodeId || (preferredKey ? `document:${preferredKey}` : "");
  const selectedNode = nodes.find((node) => node.node_id === preferredNodeId)
    || nodes.find((node) => node.kind === "document" && node.path)
    || nodes.find((node) => node.path)
    || nodes[0]
    || null;
  state.selectedEvidenceNodeId = selectedNode?.node_id || "";
  state.selectedEvidenceEdgeId = "";
  if (selectedNode?.kind === "document") {
    state.activeArtifactKey = evidenceNodeArtifactKey(selectedNode);
  }
  return {edge: null, node: selectedNode};
}

function renderEvidenceGraphBrowser(view, selection) {
  const nodes = view.nodes || [];
  const table = view.artifact_table || [];
  const artifactNodes = nodes.filter((node) => node.path);
  const rows = (artifactNodes.length ? artifactNodes : table).map((item) => {
    const nodeId = item.node_id || `${item.kind}:${item.key}`;
    const selected = selection.node?.node_id === nodeId;
    const label = item.label || item.key || "artifact";
    const status = item.status || "present";
    return `
      <button class="artifact-doc evidence-browser-row ${selected ? "active" : ""}" data-evidence-node="${escapeHtml(nodeId)}" type="button" aria-pressed="${selected ? "true" : "false"}">
        <span>
          <strong>${escapeHtml(label)}</strong>
          <small>${escapeHtml(item.kind || "artifact")} / ${escapeHtml(status)}</small>
          ${item.path ? pathLine(item.path, 60) : ""}
        </span>
        <span class="small-badge ${escapeHtml(evidenceStatusClass(status))}">${escapeHtml(status)}</span>
      </button>
    `;
  }).join("") || `<div class="empty-state">No artifacts indexed for this stage.</div>`;
  return `
    <aside class="surface evidence-artifact-browser">
      <div class="surface-title">
        <span>Artifact Browser</span>
        <span class="small-badge">${escapeHtml(table.length)} items</span>
      </div>
      <div class="evidence-filter-row">
        <span class="small-badge">Graph ${escapeHtml((view.nodes || []).length)}</span>
        <span class="small-badge">Edges ${escapeHtml((view.edges || []).length)}</span>
        <span class="small-badge">${escapeHtml(view.mode)}</span>
      </div>
      <div class="artifact-list evidence-browser-list">${rows}</div>
    </aside>
  `;
}

function renderEvidenceNodeButton(node, selection) {
  const selected = selection.node?.node_id === node.node_id;
  return `
    <button class="evidence-node ${escapeHtml(node.kind)} ${selected ? "selected" : ""}" data-evidence-node="${escapeHtml(node.node_id)}" type="button">
      <span class="evidence-node-icon">${escapeHtml(evidenceNodeIcon(node.kind))}</span>
      <span>
        <strong>${escapeHtml(node.label)}</strong>
        <small>${escapeHtml(node.kind)} / ${escapeHtml(node.status)}</small>
        ${node.path ? pathLine(node.path, 46) : ""}
      </span>
    </button>
  `;
}

function renderEvidenceEdgeButton(edge, nodesById, selection) {
  const selected = selection.edge && evidenceEdgeId(edge) === evidenceEdgeId(selection.edge);
  const source = nodesById.get(edge.source_id)?.label || edge.source_id;
  const target = nodesById.get(edge.target_id)?.label || edge.target_id;
  return `
    <button class="evidence-edge ${selected ? "selected" : ""}" data-evidence-edge="${escapeHtml(evidenceEdgeId(edge))}" type="button">
      <span class="small-badge">${escapeHtml(edge.kind)}</span>
      <span><strong>${escapeHtml(source)} -> ${escapeHtml(target)}</strong><small>${escapeHtml(edge.label)}</small></span>
    </button>
  `;
}

function renderEvidenceGraphFallback(view) {
  const reasons = view.incomplete_reasons || [];
  return `
    <div class="evidence-fallback">
      <div class="surface-title">
        <span>Flat Table Fallback</span>
        <span class="small-badge warn">${escapeHtml(reasons.length || 1)} reason</span>
      </div>
      <p>Graph provenance is incomplete, so the artifact table remains the source of truth for inspection actions.</p>
      <div class="evidence-reasons">
        ${(reasons.length ? reasons : ["graph-unavailable"]).map((reason) => `<span class="small-badge warn">${escapeHtml(reason)}</span>`).join("")}
      </div>
    </div>
  `;
}

function renderEvidenceGraphCanvas(view, selection) {
  const nodes = view.nodes || [];
  const edges = view.edges || [];
  const nodesById = new Map(nodes.map((node) => [node.node_id, node]));
  if (view.mode !== "graph" || !nodes.length || !edges.length) {
    return renderEvidenceGraphFallback(view);
  }
  return `
    <section class="surface evidence-graph-panel">
      <div class="surface-title">
        <span>Artifacts / Evidence Graph</span>
        <span class="small-badge good">${escapeHtml(nodes.length)} nodes / ${escapeHtml(edges.length)} edges</span>
      </div>
      <div class="evidence-graph-canvas" aria-label="Artifact provenance graph">
        ${nodes.map((node) => renderEvidenceNodeButton(node, selection)).join("")}
      </div>
      <div class="surface-title compact">Edges</div>
      <div class="evidence-edge-list">
        ${edges.map((edge) => renderEvidenceEdgeButton(edge, nodesById, selection)).join("")}
      </div>
    </section>
  `;
}

function renderArtifactInspector(view, selection) {
  if (selection.edge) {
    const nodesById = new Map((view.nodes || []).map((node) => [node.node_id, node]));
    const source = nodesById.get(selection.edge.source_id);
    const target = nodesById.get(selection.edge.target_id);
    return `
      <aside class="surface artifact-inspector">
        <div class="surface-title">
          <span>Selected Edge</span>
          <span class="small-badge">${escapeHtml(selection.edge.kind)}</span>
        </div>
        <div class="panel-list">
          <div class="panel-item"><strong>Label</strong><span>${escapeHtml(selection.edge.label)}</span></div>
          <div class="panel-item"><strong>Source</strong><span>${escapeHtml(source?.label || selection.edge.source_id)}</span></div>
          <div class="panel-item"><strong>Target</strong><span>${escapeHtml(target?.label || selection.edge.target_id)}</span></div>
        </div>
      </aside>
    `;
  }
  const node = selection.node;
  if (!node) {
    return `<aside class="surface artifact-inspector"><div class="empty-state">Select a graph node or edge.</div></aside>`;
  }
  const key = evidenceNodeArtifactKey(node);
  const actionButtons = node.path ? `
    <div class="artifact-action-row">
      <button data-open-artifact="${escapeHtml(node.path)}" class="secondary" type="button">Open</button>
      ${renderArtifactDownloadButton({...node, key}, "secondary")}
      <button data-copy-artifact-path="${escapeHtml(node.path)}" class="secondary" type="button">Copy Path</button>
    </div>
  ` : "";
  return `
    <aside class="surface artifact-inspector">
      <div class="surface-title">
        <span>Selected Artifact</span>
        <span class="small-badge ${escapeHtml(evidenceStatusClass(node.status))}">${escapeHtml(node.status)}</span>
      </div>
      <div class="artifact-inspector-head">
        <span class="evidence-node-icon">${escapeHtml(evidenceNodeIcon(node.kind))}</span>
        <div>
          <strong>${escapeHtml(node.label)}</strong>
          <span>${escapeHtml(node.kind)}</span>
        </div>
      </div>
      <div class="panel-list">
        <div class="panel-item"><strong>Stage</strong><span>${escapeHtml(node.stage || "-")}</span></div>
        <div class="panel-item"><strong>Node</strong><span>${escapeHtml(node.node_id)}</span></div>
        <div class="panel-item"><strong>Detail</strong><span>${escapeHtml(node.detail)}</span></div>
        <div class="panel-item"><strong>Size</strong><span>${escapeHtml(node.byte_size ?? "unknown")} bytes</span></div>
        <div class="panel-item"><strong>Updated</strong><span>${escapeHtml(node.updated_at_utc || "unknown")}</span></div>
        ${node.path ? `<div class="panel-item"><strong>Path</strong>${pathLine(node.path, 80)}</div>` : ""}
      </div>
      ${actionButtons}
    </aside>
  `;
}

function renderEvidenceArtifactTable(view, selection) {
  const refs = view.artifact_table || [];
  const selectedPath = selection.node?.path || "";
  const rows = refs.map((ref) => {
    const selected = ref.path === selectedPath;
    return `
      <tr class="${selected ? "selected" : ""}">
        <td><button class="link-button" data-evidence-node="${escapeHtml(`${ref.kind}:${ref.key}`)}" type="button">${escapeHtml(ref.key)}</button></td>
        <td>${escapeHtml(ref.kind)}</td>
        <td>${escapeHtml(artifactCategoryLabel(artifactCategoryFor(ref)))}</td>
        <td>${escapeHtml(ref.stage)}</td>
        <td>${escapeHtml(artifactOwnershipBadge(ref).label)} / ${ref.latest === false ? "stale" : "latest"} / ${ref.available === false ? "missing" : "available"}</td>
        <td>${escapeHtml(ref.byte_size ?? "unknown")}</td>
        <td>${escapeHtml(ref.updated_at_utc || "unknown")}</td>
        <td>${pathLine(ref.path, 58)}</td>
        <td>
          <div class="artifact-table-actions">
            <button data-open-artifact="${escapeHtml(ref.path)}" class="link-button" type="button">Open</button>
            ${renderArtifactDownloadButton(ref)}
            <button data-copy-artifact-path="${escapeHtml(ref.path)}" class="link-button" type="button">Copy path</button>
          </div>
        </td>
      </tr>
    `;
  }).join("") || `<tr><td colspan="9">No artifact table rows available.</td></tr>`;
  return `
    <section class="surface evidence-artifact-table">
      <div class="surface-title">
        <span>Artifacts (${escapeHtml(refs.length)})</span>
        <span class="small-badge">${escapeHtml(view.mode)}</span>
      </div>
      <div class="table-wrap evidence-table-wrap">
        <table class="activity-table evidence-table">
          <thead><tr><th>Name</th><th>Type</th><th>Category</th><th>Stage</th><th>Flags</th><th>Size</th><th>Updated</th><th>Path</th><th>Actions</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
    </section>
  `;
}

function renderEvidenceWorkbenchShell(selection) {
  const key = selection.node?.kind === "document" ? evidenceNodeArtifactKey(selection.node) : state.activeArtifactKey;
  const label = key || "Select a document node";
  return `
    <section class="surface evidence-workbench">
      <div class="surface-title">
        <span>Stage Document Workbench</span>
        <span class="small-badge">${escapeHtml(state.activeStage)}</span>
      </div>
      <div class="artifact-layout stage-document-workbench evidence-workbench-grid">
        <aside id="workbenchTree" class="surface workbench-tree">
          <div class="empty-state loading-state">Loading artifact tree...</div>
        </aside>
        <section id="artifactViewer" class="artifact-viewer">
          <div class="empty-state loading-state">Loading ${escapeHtml(label)}...</div>
        </section>
      </div>
    </section>
  `;
}

function renderEvidenceWorkbenchUnavailable(view) {
  const reasons = (view.incomplete_reasons || []).join(", ") || "artifact graph unavailable";
  const tree = document.getElementById("workbenchTree");
  const viewer = document.getElementById("artifactViewer");
  if (tree) {
    tree.innerHTML = `
      <div class="surface-title">
        <span>Stage Document Workbench</span>
        <span class="small-badge warn">fallback</span>
      </div>
      <div class="empty-state">Workbench requires the stage artifact index.</div>
    `;
  }
  if (viewer) {
    viewer.innerHTML = `
      <div class="empty-state">
        Stage Document Workbench is unavailable while Evidence Graph is in flat table fallback (${escapeHtml(reasons)}).
        Use the artifact table actions for read-only inspection.
      </div>
    `;
  }
}

function renderEvidenceGraphScreen(view, selection) {
  return `
    <div class="evidence-screen-stack">
      ${renderEvidenceWorkbenchShell(selection)}
      <details class="surface evidence-drilldown">
        <summary>
          <span>Evidence graph and artifact table</span>
          <span class="small-badge">${escapeHtml(view.mode)}</span>
        </summary>
        <section class="evidence-graph-screen">
          ${renderEvidenceGraphBrowser(view, selection)}
          <div class="evidence-graph-main">
            ${renderEvidenceGraphCanvas(view, selection)}
            ${renderEvidenceArtifactTable(view, selection)}
          </div>
          ${renderArtifactInspector(view, selection)}
        </section>
      </details>
    </div>
  `;
}

async function renderArtifacts() {
  const item = activeStageItem();
  if (!item || Number(item.attempt_count || 0) <= 0) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">No artifacts for this stage yet.</div>`;
    return;
  }
  const content = document.getElementById("cockpitContent");
  content.innerHTML = `<div class="empty-state loading-state">Loading Artifacts / Evidence Graph...</div>`;
  try {
    const params = new URLSearchParams({stage: state.activeStage});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    const view = await api(`/api/artifacts/evidence-graph?${params.toString()}`);
    const selection = selectedEvidenceSelection(view);
    content.innerHTML = renderEvidenceGraphScreen(view, selection);
    const selectedArtifactKey = selection.node?.kind === "document"
      ? evidenceNodeArtifactKey(selection.node)
      : state.activeArtifactKey;
    if (view.mode === "graph" && selectedArtifactKey) {
      state.activeArtifactKey = selectedArtifactKey;
      state.selectedEvidenceNodeId = `document:${selectedArtifactKey}`;
      await loadArtifactDocument(selectedArtifactKey);
    } else {
      renderEvidenceWorkbenchUnavailable(view);
    }
  } catch (error) {
    content.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

function artifactKeyForPath(path, stage) {
  const refs = state.dashboard?.recent_artifacts || [];
  const match = refs.find((ref) => ref.path === path && (!stage || ref.stage === stage));
  return match?.key || "";
}

async function inspectArtifactReference({stage, key, path, kind}) {
  const targetStage = stage || state.activeStage;
  state.activeStage = targetStage;
  state.activeStageExplicit = true;
  state.activeArtifactKey = key || artifactKeyForPath(path, targetStage);
  state.selectedEvidenceNodeId = state.activeArtifactKey
    ? `${kind === "log" ? "log" : "document"}:${state.activeArtifactKey}`
    : "";
  state.selectedEvidenceEdgeId = "";
  setOperatorMode(kind === "log" ? "logs" : "artifacts");
  await fetchDashboard();
  activateTab(kind === "log" ? "logs" : "artifacts");
  await renderAll();
  if (kind !== "log") focusArtifactWorkbench();
}

function focusArtifactWorkbench() {
  const workbench = document.querySelector(".evidence-workbench, .stage-document-workbench, #artifactViewer");
  if (!workbench) return;
  if (!workbench.hasAttribute("tabindex")) workbench.setAttribute("tabindex", "-1");
  workbench.scrollIntoView({block: "start", inline: "nearest"});
  workbench.focus({preventScroll: true});
}

async function copyArtifactPath(path) {
  const text = String(path || "");
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
  } catch (error) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
  }
  toast("Artifact path copied.");
}

async function downloadArtifact({stage, key, kind, path}) {
  let text = "";
  if (kind === "document" && key) {
    const params = new URLSearchParams({stage, key, mode: "source", limit: String(MAX_ARTIFACT_READ_BYTES)});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    const documentView = await api(`/api/artifacts/document?${params.toString()}`);
    text = documentView.text || "";
    if (documentView.truncated) toast("Downloaded bounded artifact source; open folder for the full file.");
  } else if (kind === "log") {
    const params = new URLSearchParams({stage});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    const logView = await api(`/api/logs?${params.toString()}`);
    text = logView.text || "";
    if (logView.truncated) toast("Downloaded bounded runtime log; open folder for the full file.");
  } else {
    toast("Download is available for document and runtime log artifacts.");
    return;
  }
  const filename = String(path || key || "artifact").split("/").pop() || "artifact.txt";
  const link = document.createElement("a");
  link.href = URL.createObjectURL(new Blob([text], {type: "text/plain;charset=utf-8"}));
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  URL.revokeObjectURL(link.href);
  link.remove();
}
