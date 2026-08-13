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
    "canonical-stage-document": "Source-of-truth stage files for operator review, retained-copy comparison, and corrections.",
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

const DOCUMENT_NAVIGATOR_ROLES = Object.freeze([
  ["output", "Output", "Canonical stage outputs and their retained handoff copies."],
  ["questions", "Questions", "Clarifications that must be answered instead of guessed."],
  ["validation", "Validation", "Validation and repair records that explain gate decisions."],
  ["inputs", "Inputs", "Context supplied to the runtime for this stage attempt."],
  ["evidence", "Evidence", "Logs, project context, lineage, and supporting retained evidence."],
]);

function documentNavigatorRole(item = {}) {
  const key = String(item.key || item.label || "").replace(/-/g, "_").toLowerCase();
  const kind = String(item.kind || "").toLowerCase();
  const category = artifactCategoryFor(item);
  if (["questions", "answers"].includes(key)) return "questions";
  if (["validator_report", "repair_brief", "repair_context"].includes(key) || category === "validation-evidence") {
    return "validation";
  }
  if (["input_bundle", "stage_brief", "operator_request"].includes(key) || category === "runtime-input") {
    return "inputs";
  }
  if (kind === "document" && ["canonical-stage-document", "published-stage-output"].includes(category)) {
    return "output";
  }
  return "evidence";
}

function documentNavigatorRoleLabel(role) {
  return DOCUMENT_NAVIGATOR_ROLES.find(([value]) => value === role)?.[1] || "Evidence";
}

function documentNavigatorRoleDetail(role) {
  return DOCUMENT_NAVIGATOR_ROLES.find(([value]) => value === role)?.[2] || "Supporting retained evidence.";
}

function documentFilename(path, fallback = "document") {
  const normalized = String(path || "").replace(/\\/g, "/").replace(/\/$/, "");
  return normalized.split("/").pop() || fallback;
}

function documentNavigatorFreshness(item = {}, workbench = {}) {
  if (item.stale === true || item.latest === false) return {label: "Historical / stale", tone: "warn"};
  if (item.available === false) return {label: "Unavailable", tone: "bad"};
  const selected = String(item.label || item.key || "") === String(workbench.selected_key || "");
  if (selected) {
    const freshness = readerFreshness(workbench);
    return {label: freshness.label, tone: freshness.tone};
  }
  return {label: "Retained", tone: ""};
}

function documentNavigatorBoundedState(item = {}, workbench = {}) {
  const selected = String(item.label || item.key || "") === String(workbench.selected_key || "");
  const document = selected ? workbench.document || {} : null;
  if (document && document.status && document.status !== "present") {
    return {label: document.status === "missing" ? "Missing" : "Unreadable", tone: "bad"};
  }
  if (item.available === false) return {label: "Missing", tone: "bad"};
  const view = selected ? document?.preview || document?.source : null;
  if (view?.truncated) return {label: "Bounded / truncated", tone: "warn"};
  return {label: "Bounded read", tone: "good"};
}

function documentNavigatorSourceOfTruth(item = {}) {
  const role = documentNavigatorRole(item);
  if (role === "output") return artifactCategoryFor(item) === "published-stage-output"
    ? "Canonical stage document (mirror is downstream evidence)"
    : "Canonical stage document";
  if (role === "questions") return "Persisted question/answer document";
  if (role === "validation") return "Persisted validator or repair evidence";
  if (role === "inputs") return "Persisted stage input context";
  return "Retained evidence path";
}

function renderDocumentNavigatorItem(item, workbench) {
  const selected = String(item.label || item.key || "") === String(workbench.selected_key || "");
  const freshness = documentNavigatorFreshness(item, workbench);
  const bounded = documentNavigatorBoundedState(item, workbench);
  const role = documentNavigatorRole(item);
  const action = item.kind === "document"
    ? `data-artifact-key="${escapeHtml(item.label || item.key)}" data-reader-artifact-key="${escapeHtml(item.label || item.key)}" data-reader-cross-document="push"`
    : `data-open-artifact="${escapeHtml(item.path || "")}"`;
  return `
    <button class="artifact-doc document-navigator-item${selected ? " active" : ""}" ${action} type="button" aria-pressed="${selected ? "true" : "false"}" data-document-role="${escapeHtml(role)}">
      <span class="artifact-doc-title">
        <strong>${escapeHtml(documentFilename(item.path, item.label || item.key || "document"))}</strong>
        <span class="small-badge ${escapeHtml(freshness.tone)}">${escapeHtml(freshness.label)}</span>
      </span>
      <small>${escapeHtml(documentNavigatorRoleLabel(role))} · ${escapeHtml(item.stage || workbench.stage || state.activeStage)} · Attempt ${escapeHtml(workbench.attempt_number || "?")}</small>
      <small>${escapeHtml(bounded.label)} · ${escapeHtml(documentNavigatorSourceOfTruth(item))}</small>
    </button>
  `;
}

function renderDocumentNavigator(workbench) {
  const references = (workbench.references || []).filter((ref) => ref.kind === "document" || ref.kind === "mirror");
  const groups = DOCUMENT_NAVIGATOR_ROLES.map(([role, label, detail]) => {
    const refs = references.filter((ref) => documentNavigatorRole(ref) === role);
    return `
      <section class="document-navigator-group" data-document-role-group="${escapeHtml(role)}">
        <div class="surface-title compact"><span>${escapeHtml(label)}</span><span class="small-badge">${escapeHtml(refs.length)}</span></div>
        <p class="artifact-category-note">${escapeHtml(detail)}</p>
        <div class="artifact-list">
          ${refs.length ? refs.map((ref) => renderDocumentNavigatorItem(ref, workbench)).join("") : `<div class="empty-state document-navigator-empty">No ${escapeHtml(label.toLowerCase())} documents indexed.</div>`}
        </div>
      </section>
    `;
  }).join("");
  return `
    <section class="document-navigator" aria-label="Document navigator">
      <div class="surface-title"><span>Document navigator</span><span class="small-badge">${escapeHtml(references.length)} retained</span></div>
      <p class="artifact-category-note">Read-only documents are grouped by role. Selection opens the bounded reader; generated Markdown has no edit action here.</p>
      ${groups}
    </section>
  `;
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

const DOCUMENT_READING_COPY = Object.freeze({
  idea_brief: {
    title: "Idea brief",
    purpose: "It captures the problem and intended outcome before the delivery flow expands it.",
    use: "Use it to check that later work still answers the original request."
  },
  research_notes: {
    title: "Research notes",
    purpose: "They record the evidence and constraints discovered before a plan was chosen.",
    use: "Use them to distinguish verified context from assumptions."
  },
  plan: {
    title: "Plan",
    purpose: "It explains the proposed delivery approach and the decisions behind it.",
    use: "Use it to review scope and trade-offs before implementation."
  },
  review_spec_report: {
    title: "Review-spec report",
    purpose: "It records whether the planned work satisfies the specification gate.",
    use: "Use it to understand what needs correction before task breakdown."
  },
  tasklist: {
    title: "Tasklist",
    purpose: "It turns the approved approach into a concrete, reviewable sequence of work.",
    use: "Use it to see what implementation should cover and in what order."
  },
  implementation_report: {
    title: "Implementation report",
    purpose: "It records what the implementation attempt changed and how it was checked.",
    use: "Use it to connect code changes with their stated verification evidence."
  },
  review_report: {
    title: "Review report",
    purpose: "It records the quality review and any findings that must be resolved.",
    use: "Use it to decide whether the implementation evidence is ready for QA."
  },
  qa_report: {
    title: "QA report",
    purpose: "It records verification outcomes for this retained QA attempt.",
    use: "Use it with freshness and validation evidence before treating it as a proceed decision."
  },
  stage_result: {
    title: "Stage result",
    purpose: "It records the durable result and gate state for a stage attempt.",
    use: "Use it to understand the recorded stage state, not to infer missing evidence."
  },
  validator_report: {
    title: "Validator report",
    purpose: "It records the checks applied to the attempt and their reported outcome.",
    use: "Use it to understand why progression is allowed, blocked, or needs repair."
  },
  questions: {
    title: "Questions",
    purpose: "It preserves clarification needed before the flow can safely continue.",
    use: "Use it to answer unresolved decisions instead of guessing in later documents."
  },
  answers: {
    title: "Answers",
    purpose: "It preserves operator clarification supplied to the governed flow.",
    use: "Use it to see which assumptions were explicitly resolved."
  },
  input_bundle: {
    title: "Input bundle",
    purpose: "It records the input context supplied to the runtime for this attempt.",
    use: "Use it to reproduce or audit what the runtime was asked to work from."
  },
  stage_brief: {
    title: "Stage brief",
    purpose: "It records the bounded instruction and context assembled for the stage.",
    use: "Use it to understand the intended scope of this attempt."
  },
  repair_brief: {
    title: "Repair brief",
    purpose: "It records the corrective context produced after a validation or review issue.",
    use: "Use it to understand why a later attempt differs from the earlier one."
  },
  operator_request: {
    title: "Operator request",
    purpose: "It records a runtime request that required operator attention or approval.",
    use: "Use it with the decision record to audit the granted scope."
  }
});

function readerLabelForKey(key) {
  const normalized = String(key || "").trim().replace(/-/g, "_").toLowerCase();
  if (DOCUMENT_READING_COPY[normalized]?.title) return DOCUMENT_READING_COPY[normalized].title;
  return String(key || "Selected document");
}

function documentReadingProfile(workbench = {}) {
  const documentView = workbench.document || {};
  const key = String(documentView.key || workbench.selected_key || "").replace(/-/g, "_").toLowerCase();
  const specific = DOCUMENT_READING_COPY[key];
  if (specific) return {...specific, category: artifactCategoryFor({key, kind: "document", path: documentView.path || ""})};
  const category = artifactCategoryFor({key, kind: "document", path: documentView.path || ""});
  const fallback = {
    "published-stage-output": {
      purpose: "This is a published handoff copy retained for downstream use.",
      use: "Use it to inspect the delivered handoff, then check its canonical source before changing it."
    },
    "validation-evidence": {
      purpose: "This is supporting validation or repair evidence, not the primary stage document.",
      use: "Use it to understand gate and recovery decisions around the stage output."
    },
    "runtime-input": {
      purpose: "This is input context supplied to the runtime for the attempt.",
      use: "Use it to audit the attempt context rather than as a final stage decision."
    },
    "runtime-evidence": {
      purpose: "This is retained runtime evidence captured for audit and replay.",
      use: "Use it to investigate what happened during the attempt."
    },
    "project-evidence": {
      purpose: "This is project context used by the governed flow.",
      use: "Use it to understand the project constraints that informed the stage."
    },
    "lineage-evidence": {
      purpose: "This is provenance for a remediation, follow-up, or archived run.",
      use: "Use it to trace why this evidence exists and which run it belongs to."
    },
    "canonical-stage-document": {
      purpose: "This is the canonical document retained for the selected stage attempt.",
      use: "Read it first, then use the supporting evidence to assess confidence and next steps."
    }
  }[category] || {};
  return {
    title: readerLabelForKey(documentView.key || workbench.selected_key),
    purpose: fallback.purpose || "This retained document is available for read-only inspection.",
    use: fallback.use || "Use it with the supporting evidence before making a stage decision.",
    category
  };
}

function readerStageItem() {
  return typeof activeStageItem === "function" ? activeStageItem() : null;
}

function readerFreshness(workbench = {}) {
  const documentView = workbench.document || {};
  if (documentView.status && documentView.status !== "present") {
    return {
      label: "Unavailable",
      tone: "bad",
      detail: "This retained copy could not be read safely, so it cannot support a stage decision."
    };
  }
  const stage = readerStageItem();
  const stageAttempt = Number(stage?.attempt_count || 0);
  const documentAttempt = Number(workbench.attempt_number || 0);
  const stale = Boolean(stage?.stale) || String(stage?.status || "").toLowerCase() === "stale";
  if (stale || (stageAttempt && documentAttempt && stageAttempt !== documentAttempt)) {
    return {
      label: "Historical / stale",
      tone: "warn",
      detail: stage?.stale_reason
        || "A later request or repair changed the stage context. Do not use this copy as the current proceed decision."
    };
  }
  if (documentAttempt) {
    return {
      label: `Attempt ${documentAttempt} retained`,
      tone: "good",
      detail: "This is the retained copy selected for the current stage context. Check validation before relying on it."
    };
  }
  return {
    label: "Retained copy",
    tone: "",
    detail: "The attempt number is unavailable. Treat this as retained evidence and check its provenance."
  };
}

function renderDocumentReadingBrief(workbench) {
  const documentView = workbench.document || {};
  const profile = documentReadingProfile(workbench);
  const freshness = readerFreshness(workbench);
  const role = documentNavigatorRole({
    key: documentView.key || workbench.selected_key,
    kind: "document",
    path: documentView.path || ""
  });
  const bounded = documentNavigatorBoundedState({
    key: documentView.key || workbench.selected_key,
    kind: "document",
    path: documentView.path || ""
  }, workbench);
  const badge = artifactOwnershipBadge({
    key: documentView.key || workbench.selected_key,
    kind: "document",
    path: documentView.path || "",
    category: profile.category
  });
  return `
    <section class="reader-brief" aria-label="Document reading brief">
      <div class="reader-brief-heading">
        <div>
          <p class="reader-eyebrow">Reading brief</p>
          <h2>${escapeHtml(profile.title)}</h2>
          <p>${escapeHtml(profile.purpose)}</p>
        </div>
        <div class="reader-badges">
          <span class="small-badge ${escapeHtml(badge.tone)}">${escapeHtml(badge.label)}</span>
          <span class="small-badge ${escapeHtml(freshness.tone)}">${escapeHtml(freshness.label)}</span>
        </div>
      </div>
      <dl class="reader-brief-facts">
        <div><dt>Role</dt><dd>${escapeHtml(documentNavigatorRoleLabel(role))}</dd></div>
        <div><dt>Stage / attempt</dt><dd>${escapeHtml(workbench.stage || state.activeStage)} / ${escapeHtml(workbench.attempt_number || "?")}</dd></div>
        <div><dt>Bounded state</dt><dd><span class="small-badge ${escapeHtml(bounded.tone)}">${escapeHtml(bounded.label)}</span></dd></div>
        <div><dt>Source of truth</dt><dd>${escapeHtml(documentNavigatorSourceOfTruth({key: documentView.key || workbench.selected_key, kind: "document", path: documentView.path || ""}))}</dd></div>
        <div><dt>Why it matters now</dt><dd>${escapeHtml(profile.use)}</dd></div>
        <div><dt>Freshness</dt><dd>${escapeHtml(freshness.detail)}</dd></div>
      </dl>
    </section>
  `;
}

function renderReaderTechnicalDetails(workbench) {
  const documentView = workbench.document || {};
  const attempt = workbench.attempt_number ? `Attempt ${workbench.attempt_number}` : "Attempt unavailable";
  return `
    <details class="reader-technical-details">
      <summary>Technical details and file location</summary>
      <div class="reader-technical-content">
        <div class="reader-technical-facts">
          <span><strong>Version</strong>${escapeHtml(attempt)}</span>
          <span><strong>Size</strong>${escapeHtml(documentView.byte_size ?? "unknown")} bytes</span>
          ${documentView.path ? `<span><strong>Path</strong>${pathLine(documentView.path, 92)}</span>` : ""}
        </div>
        ${documentView.path ? renderArtifactOwnershipNote({
          key: documentView.key || workbench.selected_key,
          kind: "document",
          path: documentView.path
        }) : ""}
        ${documentView.path ? `<div class="reader-path-actions"><button data-open-artifact="${escapeHtml(documentView.path)}" class="secondary" type="button">Open folder</button><button data-copy-artifact-path="${escapeHtml(documentView.path)}" class="secondary" type="button">Copy path</button></div>` : ""}
      </div>
    </details>
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
    ${renderDocumentNavigator(workbench)}
    <div class="surface-title">Artifact categories</div>
    ${grouped || `<div class="empty-state">No artifacts indexed for this stage.</div>`}
  `;
}

function readerValidationPresentation(item = {}) {
  const detail = String(item.detail || "");
  const noRecordedVerdict = String(item.label || "").toLowerCase() === "validator-report"
    && /0\s+passing[^\d]*0\s+failing/i.test(detail);
  if (noRecordedVerdict) {
    return {
      label: "no verdict",
      tone: "warn",
      detail: `${detail || "No validator checks were recorded."} This is not a passing validation verdict.`,
      needsAttention: true
    };
  }
  const status = String(item.status || "unknown");
  return {
    label: status,
    tone: workbenchStatusClass(status),
    detail,
    needsAttention: ["missing", "fail", "failed", "invalid", "blocked", "warning", "warn", "unknown"].includes(status.toLowerCase())
  };
}

function readerRequirementPurpose(item = {}) {
  const kind = String(item.kind || "").toLowerCase();
  const status = String(item.status || "").toLowerCase();
  if (["missing", "unknown"].includes(status)) {
    return "Without this evidence, the stage contract is not fully supported.";
  }
  if (kind === "required-section") {
    return "Needed so this document has the structure required by its contract.";
  }
  return "Needed to show that the stage has the contract evidence required for a safe handoff.";
}

function readerValidationPurpose(item = {}) {
  if (String(item.label || "").toLowerCase() === "validator-report") {
    return "Needed to establish whether recorded checks support progression.";
  }
  return "Needed to assess confidence in this retained copy before relying on it.";
}

function renderRequirementList(requirements) {
  return (requirements || []).map((item) => `
    <div class="workbench-side-row">
      <span class="small-badge ${workbenchStatusClass(item.status)}">${escapeHtml(item.status)}</span>
      <span>
        <strong>${escapeHtml(item.label)}</strong>
        <small>${escapeHtml(item.kind)} / ${escapeHtml(item.source)}</small>
        <small class="reader-item-purpose">Why: ${escapeHtml(readerRequirementPurpose(item))}</small>
        ${item.path ? pathLine(item.path, 60) : ""}
      </span>
    </div>
  `).join("") || `<div class="empty-state">No contract requirements resolved.</div>`;
}

function renderValidationResults(results) {
  return (results || []).map((item) => {
    const presentation = readerValidationPresentation(item);
    return `
      <div class="workbench-side-row">
        <span class="small-badge ${escapeHtml(presentation.tone)}">${escapeHtml(presentation.label)}</span>
        <span>
          <strong>${escapeHtml(item.label)}</strong>
          <small>${escapeHtml(presentation.detail)}</small>
          <small class="reader-item-purpose">Why: ${escapeHtml(readerValidationPurpose(item))}</small>
          ${renderFindingAnchor(item)}
          ${item.path ? pathLine(item.path, 60) : ""}
        </span>
      </div>
    `;
  }).join("") || `<div class="empty-state">No validation results yet.</div>`;
}

function renderMissingEvidence(requirements) {
  const missing = (requirements || []).filter((item) => ["missing", "unknown"].includes(String(item.status || "").toLowerCase()));
  return missing.map((item) => `
    <div class="workbench-side-row">
      <span class="small-badge bad">${escapeHtml(item.status)}</span>
      <span>
        <strong>${escapeHtml(item.label)}</strong>
        <small>${escapeHtml(item.kind)} from ${escapeHtml(item.source)}</small>
        <small class="reader-item-purpose">Why: ${escapeHtml(readerRequirementPurpose(item))}</small>
        ${item.path ? pathLine(item.path, 60) : ""}
      </span>
    </div>
  `).join("") || `<div class="empty-state">No missing evidence for the selected document.</div>`;
}

function readerReferenceAction(ref = {}) {
  if (ref.kind === "document") {
    return `data-reader-artifact-key="${escapeHtml(ref.label)}" data-reader-cross-document="push"`;
  }
  if (ref.kind === "log") {
    return `data-evidence-path="${escapeHtml(ref.path)}" data-evidence-stage="${escapeHtml(ref.stage || state.activeStage)}" data-evidence-kind="log"`;
  }
  return `data-open-artifact="${escapeHtml(ref.path)}"`;
}

function renderWorkbenchReferences(references) {
  return (references || []).map((ref) => `
    <button class="artifact-row" ${readerReferenceAction(ref)} type="button">
      <span>
        <strong>${escapeHtml(ref.label)}</strong>
        <small>${escapeHtml(artifactCategoryDetail(artifactCategoryFor(ref)))}</small>
        ${pathLine(ref.path, 58)}
      </span>
      <span class="small-badge ${escapeHtml(artifactOwnershipBadge(ref).tone)}">${escapeHtml(artifactOwnershipBadge(ref).label)}</span>
    </button>
  `).join("") || `<div class="empty-state">No references linked.</div>`;
}

function renderVersionHistory(versions, currentAttempt = 0) {
  return (versions || []).map((version) => {
    const isCurrent = Number(version.attempt_number || 0) === Number(currentAttempt || 0);
    const action = isCurrent ? "disabled" : `data-compare-attempt="${escapeHtml(version.attempt_number)}"`;
    const actionLabel = isCurrent ? "current copy" : "compare copy";
    const purpose = isCurrent
      ? "Why: This identifies the retained copy currently being read."
      : "Why: Compare this earlier copy to understand what changed after retry or repair.";
    return `
      <button class="artifact-row" ${action} type="button">
        <span>
          <strong>${escapeHtml(version.label)}</strong>
          <small>${escapeHtml(version.source)} / ${escapeHtml(version.updated_at_utc || "timestamp unavailable")}</small>
          <small class="reader-item-purpose">${escapeHtml(purpose)}</small>
          ${pathLine(version.path, 58)}
        </span>
        <span class="small-badge">${escapeHtml(actionLabel)}</span>
      </button>
    `;
  }).join("") || `<div class="empty-state">No version history for this document.</div>`;
}

function renderComparisonCopy(workbench, label) {
  const documentView = workbench?.document || {};
  const view = documentView.source || documentView.preview;
  if (!view || documentView.status !== "present") {
    return `
      <section class="reader-comparison-copy">
        <div class="surface-title compact">${escapeHtml(label)}</div>
        <div class="empty-state">This retained copy is unavailable for safe comparison.</div>
      </section>
    `;
  }
  return `
    <section class="reader-comparison-copy">
      <div class="surface-title compact">
        <span>${escapeHtml(label)}</span>
        <span class="small-badge">attempt ${escapeHtml(workbench.attempt_number || "?")}</span>
      </div>
      ${renderTruncationNotice("artifact", view, "source")}
      <pre data-source-rendering="exact-bounded-source">${renderSourceWithLineAnchors(view.text)}</pre>
    </section>
  `;
}

function comparisonCandidates(workbench) {
  const currentAttempt = Number(workbench?.attempt_number || 0);
  return (workbench?.versions || []).filter((version) => Number(version.attempt_number || 0) && Number(version.attempt_number) !== currentAttempt);
}

function renderWorkbenchComparison(workbench) {
  const selected = state.activeArtifactComparison;
  const candidates = comparisonCandidates(workbench);
  if (selected?.workbench) {
    return `
      <div class="reader-comparison-panel">
        <div class="reader-comparison-heading">
          <div>
            <div class="surface-title">Compare retained copies</div>
            <p>Side-by-side source is shown below. This is a comparison view, not a generated line-by-line diff.</p>
          </div>
          <button data-clear-artifact-comparison class="secondary" type="button">Choose another copy</button>
        </div>
        <div class="reader-comparison-grid">
          ${renderComparisonCopy(workbench, "Selected stage copy")}
          ${renderComparisonCopy(selected.workbench, `Retained attempt ${selected.attemptNumber}`)}
        </div>
      </div>
    `;
  }
  if (!candidates.length) {
    return `
      <div class="reader-comparison-panel empty-state">
        <strong>No retained prior copy</strong>
        <span>Comparison is unavailable because this document has no earlier retained attempt. No diff is implied.</span>
      </div>
    `;
  }
  return `
    <div class="reader-comparison-panel">
      <div class="surface-title">Compare retained copies</div>
      <p>Choose an earlier retained attempt. The reader will show both bounded source copies side by side; it does not claim to generate a diff.</p>
      <div class="recent-artifacts reader-comparison-options">
        ${candidates.map((version) => `
          <button class="artifact-row" data-compare-attempt="${escapeHtml(version.attempt_number)}" type="button">
            <span><strong>${escapeHtml(version.label)}</strong><small>${escapeHtml(version.source)} / ${escapeHtml(version.updated_at_utc || "timestamp unavailable")}</small></span>
            <span class="small-badge">compare</span>
          </button>
        `).join("")}
      </div>
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

function readerAnchorSlug(value, fallback = "section") {
  const slug = String(value || "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 72);
  return slug || fallback;
}

function readerHeadingAnchorId(heading, index = 0) {
  return `finding-${readerAnchorSlug(heading?.label, "section")}-${index + 1}`;
}

function renderMarkdownWithReaderAnchors(text) {
  const headings = markdownHeadingSummary(text);
  let headingIndex = 0;
  return renderMarkdown(text).replace(/<h([1-6])>/g, (match, level) => {
    const heading = headings[headingIndex];
    const id = readerHeadingAnchorId(heading, headingIndex);
    headingIndex += 1;
    return `<h${level} id="${escapeHtml(id)}" data-finding-anchor="heading">`;
  });
}

function renderSourceWithLineAnchors(text) {
  return String(text ?? "")
    .split(/\r?\n/)
    .map((line, index) => `<span id="line-${index + 1}" data-finding-anchor="line">${escapeHtml(line)}</span>`)
    .join("\n");
}

function renderFindingAnchor(item = {}) {
  const line = Number(item.line_number || item.line || 0);
  if (!Number.isInteger(line) || line <= 0) return "";
  return `<a class="finding-anchor" data-finding-anchor-link="line" href="#line-${line}">Line ${line}</a>`;
}

function renderWorkbenchTableOfContents(workbench) {
  if (state.artifactViewMode === "compare") return "";
  const view = workbenchSelectedDocumentView(workbench);
  const headings = markdownHeadingSummary(view?.text || "");
  return `
    <details class="workbench-toc reader-document-map" aria-label="Document map">
      <summary>
        <span>Document map</span>
        <span class="small-badge">${escapeHtml(headings.length)} sections</span>
      </summary>
      <p>This is a reading map for the visible copy; it does not change the document or navigate away.</p>
      ${headings.length ? `<ol class="workbench-toc-list">
        ${headings.map((heading, index) => `
          <li class="toc-level-${escapeHtml(heading.level)}"><a href="#${escapeHtml(readerHeadingAnchorId(heading, index))}" data-finding-anchor-link="heading">${escapeHtml(heading.label)}</a></li>
        `).join("")}
      </ol>` : `<div class="empty-state">No Markdown headings were recorded in this bounded copy.</div>`}
    </details>
  `;
}

function renderReaderNextAction(workbench, reason) {
  const documentView = workbench?.document || {};
  const path = documentView.path || "";
  if (path) {
    return `<button class="secondary reader-next-action" data-reader-next-action="open-folder" data-open-artifact="${escapeHtml(path)}" type="button">Open folder</button>`;
  }
  if (reason === "empty") {
    return `<button class="secondary reader-next-action" data-reader-next-action="source" data-artifact-mode="source" type="button">Read source view</button>`;
  }
  return `<span class="reader-next-action" data-reader-next-action="none">No safe next action is available.</span>`;
}

function readerDocumentStatus(documentView = {}) {
  const status = String(documentView.status || "").toLowerCase();
  const message = String(documentView.message || "");
  if (status === "permission-denied" || /permission|denied|access/i.test(message)) return {label: "Permission denied", reason: "permission-denied"};
  if (status === "missing") return {label: "Missing", reason: "missing"};
  if (status && status !== "present") return {label: "Malformed or unreadable", reason: "malformed"};
  return {label: "Present", reason: "present"};
}

function renderWorkbenchDocumentBody(workbench) {
  const documentView = workbench.document;
  if (!documentView || documentView.status !== "present") {
    const status = readerDocumentStatus(documentView || {});
    return `
      <div class="reader-state reader-state-error" role="alert">
        <strong>Document ${escapeHtml(status.label.toLowerCase())}</strong>
        <span>This retained copy cannot be read safely, so do not use the stage state alone as evidence.</span>
        <details>
          <summary>Technical details</summary>
          <code>${escapeHtml(documentView?.status || "missing")}: ${escapeHtml(documentView?.message || "Selected document is not available.")}</code>
        </details>
        ${renderReaderNextAction(workbench, status.reason)}
      </div>
    `;
  }
  if (state.artifactViewMode === "compare") return renderWorkbenchComparison(workbench);
  const view = workbenchSelectedDocumentView(workbench);
  if (!view) {
    return `<div class="reader-state reader-state-empty" role="status"><strong>Document is empty</strong><span>No bounded ${escapeHtml(state.artifactViewMode)} view is available for this retained document.</span>${renderReaderNextAction(workbench, "empty")}</div>`;
  }
  if (!String(view.text || "").trim()) {
    return `<div class="reader-state reader-state-empty" role="status"><strong>Document is empty</strong><span>The retained file is present but contains no readable Markdown content.</span>${renderReaderNextAction(workbench, "empty")}</div>`;
  }
  const body = state.artifactViewMode === "source" || view.content_type !== "text/markdown"
    ? `<pre data-source-rendering="exact-bounded-source">${renderSourceWithLineAnchors(view.text)}</pre>`
    : `<div class="markdown-preview">${renderMarkdownWithReaderAnchors(view.text)}</div>`;
  return `${renderTruncationNotice("artifact", view, state.artifactViewMode)}${body}`;
}

function renderDocumentReaderControls(workbench) {
  const previewActive = state.artifactViewMode === "preview" ? " active" : "";
  const sourceActive = state.artifactViewMode === "source" ? " active" : "";
  const compareActive = state.artifactViewMode === "compare" ? " active" : "";
  const compareAvailable = comparisonCandidates(workbench).length > 0;
  const profile = documentReadingProfile(workbench);
  return `
    <div class="viewer-header reader-header">
      <div>
        <span class="reader-eyebrow">Document reader</span>
        <strong>${escapeHtml(profile.title)}</strong>
      </div>
      <div class="viewer-modes" role="group" aria-label="Document reader mode">
        <button data-artifact-mode="preview" class="${previewActive}" type="button" aria-pressed="${state.artifactViewMode === "preview" ? "true" : "false"}">Read</button>
        <button data-artifact-mode="source" class="${sourceActive}" type="button" aria-pressed="${state.artifactViewMode === "source" ? "true" : "false"}">Source</button>
        <button data-artifact-mode="compare" class="${compareActive}" type="button" aria-pressed="${state.artifactViewMode === "compare" ? "true" : "false"}" ${compareAvailable ? "" : "disabled aria-disabled=\"true\""}>Compare</button>
      </div>
    </div>
  `;
}

function renderDocumentReaderCanvas(workbench, {studio = false} = {}) {
  return `
    ${renderDocumentReadingBrief(workbench)}
    ${renderDocumentReaderControls(workbench)}
    ${renderReaderTechnicalDetails(workbench)}
    <section class="workbench-document-pane hierarchy-primary document-canvas" data-document-canvas-mode="${escapeHtml(state.artifactViewMode)}">
      ${renderWorkbenchTableOfContents(workbench)}
      ${renderWorkbenchDocumentBody(workbench)}
    </section>
  `;
}

function renderWorkbenchViewer(workbench) {
  const evidenceInspector = renderWorkbenchEvidenceInspector(workbench);
  return `
    <div class="workbench-main reader-workbench-main" data-evidence-inspector="${evidenceInspector ? "present" : "absent"}">
      <div class="reader-document-column">
        ${renderDocumentReaderCanvas(workbench)}
      </div>
      ${evidenceInspector}
    </div>
  `;
}

function renderStudioDocumentCanvas(workbench) {
  return renderDocumentReaderCanvas(workbench, {studio: true});
}

function readerEvidenceGroups(workbench = {}) {
  const validation = Array.isArray(workbench.validation_results) ? workbench.validation_results : [];
  const requirements = Array.isArray(workbench.requirements) ? workbench.requirements : [];
  const references = Array.isArray(workbench.references) ? workbench.references : [];
  const versions = Array.isArray(workbench.versions) ? workbench.versions : [];
  const documentRequirements = requirements.filter((item) => item.kind === "required-section");
  const stageRequirements = requirements.filter((item) => item.kind !== "required-section");
  const missingRequirements = requirements.filter((item) => ["missing", "unknown"].includes(String(item.status || "").toLowerCase()));
  const attentionValidation = validation.filter((item) => readerValidationPresentation(item).needsAttention);
  const freshness = readerFreshness(workbench);
  const staleDocument = freshness.label === "Historical / stale";
  return {
    validation,
    requirements,
    documentRequirements,
    stageRequirements,
    missingRequirements,
    attentionValidation,
    references,
    versions,
    freshness,
    hasAttention: Boolean(attentionValidation.length || missingRequirements.length || staleDocument),
    hasDecisionValue: Boolean(
      validation.length
      || requirements.length
      || references.length
      || versions.length > 1
      || staleDocument
    )
  };
}

function studioEvidenceInspectorItemCount(workbench) {
  const groups = readerEvidenceGroups(workbench);
  return groups.validation.length
    + groups.requirements.length
    + groups.references.length
    + groups.versions.length;
}

function renderReaderEvidenceDisclosure({section, title, purpose, count, body, open = false}) {
  return `
    <details class="reader-evidence-group" data-inspector-section="${escapeHtml(section)}" ${open ? "open" : ""}>
      <summary>
        <span class="reader-evidence-summary-copy">
          <strong>${escapeHtml(title)}</strong>
          <small>${escapeHtml(purpose)}</small>
        </span>
        <span class="small-badge">${escapeHtml(count)} item${Number(count) === 1 ? "" : "s"}</span>
      </summary>
      <div class="reader-evidence-body">${body}</div>
    </details>
  `;
}

function renderReaderRequirementGroups(groups) {
  const documentRequirements = groups.documentRequirements.length ? `
    <div class="reader-evidence-subgroup">
      <strong>Document structure</strong>
      <small>These headings make this document complete enough for its contract.</small>
      ${renderRequirementList(groups.documentRequirements)}
    </div>
  ` : "";
  const stageRequirements = groups.stageRequirements.length ? `
    <div class="reader-evidence-subgroup">
      <strong>Stage outputs</strong>
      <small>These related outputs show whether the stage has the evidence its contract expects.</small>
      ${renderRequirementList(groups.stageRequirements)}
    </div>
  ` : "";
  return documentRequirements || stageRequirements || `<div class="empty-state">No contract requirements resolved.</div>`;
}

function renderReaderAttention(groups) {
  const stale = groups.freshness.label === "Historical / stale" ? `
    <div class="reader-attention-note">
      <span class="small-badge warn">historical / stale</span>
      <span>${escapeHtml(groups.freshness.detail)}</span>
    </div>
  ` : "";
  const validation = groups.attentionValidation.length ? renderValidationResults(groups.attentionValidation) : "";
  const missing = groups.missingRequirements.length ? `
    <div class="reader-evidence-subgroup">
      <strong>Missing or unresolved contract evidence</strong>
      ${renderMissingEvidence(groups.missingRequirements)}
    </div>
  ` : "";
  return stale || validation || missing || `<div class="empty-state">No recorded evidence needs immediate attention.</div>`;
}

function renderStudioEvidenceInspector(workbench) {
  const groups = readerEvidenceGroups(workbench);
  const itemCount = studioEvidenceInspectorItemCount(workbench);
  if (!resolveStudioEvidenceVisibility({inspectorDecisionValue: groups.hasDecisionValue}).inspector) return "";
  const sections = [];
  if (groups.hasAttention || groups.validation.length) {
    const title = groups.hasAttention ? "Needs attention" : "Validation checks";
    const purpose = groups.hasAttention
      ? "These facts can change whether the document is safe to rely on or whether the stage can proceed."
      : "These recorded checks support the confidence of this retained copy; review them before proceeding.";
    const body = groups.hasAttention ? renderReaderAttention(groups) : renderValidationResults(groups.validation);
    sections.push(renderReaderEvidenceDisclosure({
      section: "findings",
      title,
      purpose,
      count: groups.hasAttention ? groups.attentionValidation.length + groups.missingRequirements.length + (groups.freshness.label === "Historical / stale" ? 1 : 0) : groups.validation.length,
      body,
      open: groups.hasAttention
    }));
  }
  if (groups.requirements.length) {
    sections.push(renderReaderEvidenceDisclosure({
      section: "source-references",
      title: "What this document must satisfy",
      purpose: "These are the contract requirements behind the document, so you can see what “complete” means here.",
      count: groups.requirements.length,
      body: renderReaderRequirementGroups(groups)
    }));
  }
  if (groups.versions.length) {
    sections.push(renderReaderEvidenceDisclosure({
      section: "provenance",
      title: "Where this version came from",
      purpose: "Version history explains which retained attempt you are reading and lets you compare an earlier copy without leaving the reader.",
      count: groups.versions.length,
      body: `<div class="recent-artifacts">${renderVersionHistory(groups.versions, workbench.attempt_number)}</div>`
    }));
  }
  if (groups.references.length) {
    sections.push(renderReaderEvidenceDisclosure({
      section: "related-artifacts",
      title: "Related evidence",
      purpose: "These files add context, validation, logs, or handoff provenance for the selected document.",
      count: groups.references.length,
      body: `<div class="recent-artifacts">${renderWorkbenchReferences(groups.references)}</div>`
    }));
  }
  return `
    <div class="surface-title evidence-inspector-title">
      <span>Evidence supporting this reading</span><span class="small-badge">${escapeHtml(itemCount)} retained</span>
    </div>
    <p class="evidence-inspector-intro">Open only the evidence that answers a confidence or next-step question.</p>
    ${sections.join("")}
  `;
}

function updateStudioEvidenceInspector(workbench) {
  const inspector = document.getElementById("studioEvidenceInspector");
  if (!inspector) return;
  const markup = renderStudioEvidenceInspector(workbench);
  inspector.hidden = !markup;
  inspector.innerHTML = markup;
}

function renderWorkbenchEvidenceInspector(workbench) {
  const inspector = renderStudioEvidenceInspector(workbench);
  if (!inspector) return "";
  return `
      <aside class="workbench-sidebar hierarchy-supporting evidence-inspector">
        ${inspector}
      </aside>
  `;
}

function workbenchRequestPath(key, attemptNumber = null) {
  const params = new URLSearchParams({stage: state.activeStage});
  if (key) params.set("key", key);
  if (state.activeRunId) params.set("run_id", state.activeRunId);
  if (attemptNumber) params.set("attempt_number", String(attemptNumber));
  params.set("source_limit", String(MAX_ARTIFACT_READ_BYTES));
  return `/api/stage/workbench?${params.toString()}`;
}

function activeReaderViewer() {
  return document.getElementById("artifactViewer") || document.getElementById("studioDocumentCanvas");
}

function renderDocumentReaderFailure(error) {
  const message = String(error?.message || error || "Document reader unavailable.");
  return `
    <div class="reader-state reader-state-error" role="alert">
      <strong>Document reader unavailable</strong>
      <span>The document was not loaded, so no reading or progression decision should rely on this view.</span>
      <button data-retry-artifact-document class="secondary" type="button">Try again</button>
      <details>
        <summary>Technical details</summary>
        <code>${escapeHtml(message)}</code>
      </details>
    </div>
  `;
}

function renderLoadedArtifactDocument(workbench, {tree, viewer, studioCanvas}) {
  state.activeArtifactKey = workbench.selected_key;
  state.activeArtifactWorkbench = workbench;
  if (studioCanvas) {
    state.activeStudioWorkbench = workbench;
    state.activeStudioWorkbenchError = "";
    updateStudioEvidenceInspector(workbench);
  }
  if (tree) tree.innerHTML = renderWorkbenchTree(workbench);
  viewer.innerHTML = studioCanvas
    ? renderStudioDocumentCanvas(workbench)
    : renderWorkbenchViewer(workbench);
}

async function loadArtifactDocument(key) {
  const tree = document.getElementById("workbenchTree");
  const viewer = activeReaderViewer();
  if (!viewer) return;
  const studioCanvas = viewer.id === "studioDocumentCanvas";
  if (key && key !== state.activeArtifactKey) state.activeArtifactComparison = null;
  viewer.innerHTML = `<div class="reader-state loading-state" role="status">Loading retained document evidence…</div>`;
  try {
    const workbench = await api(workbenchRequestPath(key));
    const comparisonKey = state.activeArtifactComparison?.workbench?.selected_key;
    if (comparisonKey && comparisonKey !== workbench.selected_key) state.activeArtifactComparison = null;
    renderLoadedArtifactDocument(workbench, {tree, viewer, studioCanvas});
  } catch (error) {
    if (studioCanvas) {
      state.activeStudioWorkbench = null;
      state.activeStudioWorkbenchError = error.message || "Document Canvas unavailable";
      updateStudioEvidenceInspector({});
    }
    viewer.innerHTML = renderDocumentReaderFailure(error);
  }
}

async function loadArtifactComparison(attemptNumber) {
  const currentWorkbench = state.activeArtifactWorkbench || state.activeStudioWorkbench;
  const viewer = activeReaderViewer();
  if (!currentWorkbench || !viewer || !state.activeArtifactKey) return;
  const selectedAttempt = Number(attemptNumber || 0);
  if (!selectedAttempt || selectedAttempt === Number(currentWorkbench.attempt_number || 0)) return;
  const studioCanvas = viewer.id === "studioDocumentCanvas";
  viewer.innerHTML = `<div class="reader-state loading-state" role="status">Loading retained comparison copy…</div>`;
  try {
    const comparison = await api(workbenchRequestPath(state.activeArtifactKey, selectedAttempt));
    state.activeArtifactComparison = {attemptNumber: selectedAttempt, workbench: comparison};
    renderLoadedArtifactDocument(currentWorkbench, {
      tree: document.getElementById("workbenchTree"),
      viewer,
      studioCanvas
    });
  } catch (error) {
    state.activeArtifactComparison = null;
    viewer.innerHTML = renderDocumentReaderFailure(error);
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
      <p>Graph provenance is incomplete, so the artifact table remains the source of truth for inspection actions. Indexed documents still open in the reader above.</p>
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
      <div class="reader-state reader-state-error">
        <strong>No indexed document is available to read</strong>
        <span>The evidence graph is in flat-table fallback (${escapeHtml(reasons)}), and no document key could be selected from the retained artifact index.</span>
        <span>Use the table below to inspect available evidence or choose a document when one is indexed.</span>
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
    document.getElementById("intentContent").innerHTML = `<div class="empty-state">No artifacts for this stage yet.</div>`;
    return;
  }
  const content = document.getElementById("intentContent");
  content.innerHTML = `<div class="empty-state loading-state">Loading Artifacts / Evidence Graph...</div>`;
  try {
    const params = new URLSearchParams({stage: state.activeStage});
    if (state.activeRunId) params.set("run_id", state.activeRunId);
    const view = await api(`/api/artifacts/evidence-graph?${params.toString()}`);
    const selection = selectedEvidenceSelection(view);
    content.innerHTML = renderEvidenceGraphScreen(view, selection);
    const selectedArtifactKey = selection.node?.kind === "document"
      ? evidenceNodeArtifactKey(selection.node)
      : state.activeArtifactKey || preferredEvidenceArtifactKey(view);
    if (selectedArtifactKey) {
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
  state.activeArtifactComparison = null;
  state.selectedEvidenceNodeId = state.activeArtifactKey
    ? `${kind === "log" ? "log" : "document"}:${state.activeArtifactKey}`
    : "";
  state.selectedEvidenceEdgeId = "";
  setOperatorMode(kind === "log" ? "logs" : "artifacts");
  await fetchDashboard();
  activateTab(kind === "log" ? "logs" : "artifacts", {historyMode: "push"});
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
