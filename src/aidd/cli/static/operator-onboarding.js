const GUIDED_SETUP_STEPS = ["project", "work-item", "runtime", "review-launch"];

function initialGuidedSetupState() {
  return Object.freeze({
    step: "project",
    projectStatus: "unvalidated",
    workItemBranch: null,
    workItem: "",
    runtimeId: "",
    launchReadiness: "unchecked",
    error: ""
  });
}

function guidedSetupCanContinue(guided) {
  if (guided.step === "project") return guided.projectStatus === "valid";
  if (guided.step === "work-item") {
    return ["create", "resume"].includes(guided.workItemBranch) && Boolean(guided.workItem);
  }
  if (guided.step === "runtime") return Boolean(guided.runtimeId);
  return false;
}

function reduceGuidedSetupState(current, event, payload = {}) {
  const guided = {...initialGuidedSetupState(), ...(current || {})};
  if (event === "reset") return initialGuidedSetupState();
  if (event === "project-valid") {
    return Object.freeze({
      ...initialGuidedSetupState(),
      step: "work-item",
      projectStatus: "valid"
    });
  }
  if (event === "project-invalid") {
    return Object.freeze({
      ...initialGuidedSetupState(),
      projectStatus: "invalid",
      error: String(payload.error || "Project validation failed.")
    });
  }
  if (event === "work-item-selected") {
    const branch = String(payload.branch || "");
    const workItem = String(payload.workItem || "").trim();
    if (guided.projectStatus !== "valid" || !["create", "resume"].includes(branch) || !workItem) {
      return Object.freeze({...guided, error: "Select a valid create or resume Work Item."});
    }
    return Object.freeze({
      ...guided,
      step: "runtime",
      workItemBranch: branch,
      workItem,
      runtimeId: "",
      launchReadiness: "unchecked",
      error: ""
    });
  }
  if (event === "runtime-selected") {
    const runtimeId = String(payload.runtimeId || "").trim();
    if (guided.step !== "runtime" || !runtimeId) {
      return Object.freeze({...guided, error: "Select a runtime before review."});
    }
    return Object.freeze({
      ...guided,
      step: "review-launch",
      runtimeId,
      launchReadiness: "unchecked",
      error: ""
    });
  }
  if (event === "launch-readiness") {
    if (guided.step !== "review-launch") return Object.freeze(guided);
    const ready = payload.ready === true;
    return Object.freeze({
      ...guided,
      launchReadiness: ready ? "ready" : "blocked",
      error: ready ? "" : String(payload.error || "Launch readiness is blocked.")
    });
  }
  if (event === "back") {
    const index = GUIDED_SETUP_STEPS.indexOf(guided.step);
    if (index <= 0) return Object.freeze(guided);
    const step = GUIDED_SETUP_STEPS[index - 1];
    return Object.freeze({
      ...guided,
      step,
      runtimeId: step === "runtime" ? guided.runtimeId : "",
      launchReadiness: "unchecked",
      error: ""
    });
  }
  if (event === "continue") {
    if (!guidedSetupCanContinue(guided)) {
      return Object.freeze({...guided, error: "Complete the current setup step before continuing."});
    }
    const index = GUIDED_SETUP_STEPS.indexOf(guided.step);
    return Object.freeze({...guided, step: GUIDED_SETUP_STEPS[index + 1], error: ""});
  }
  throw new Error(`Unknown Guided Setup transition: ${event}`);
}

function transitionGuidedSetup(event, payload = {}) {
  state.onboarding.guided = reduceGuidedSetupState(state.onboarding.guided, event, payload);
  return state.onboarding.guided;
}

function setGuidedDeliveryPreference(enabled) {
  state.onboarding.guidedDelivery = Boolean(enabled);
  renderOnboarding();
}

function guidedDeliveryExplanation(guided = state.onboarding.guided) {
  const step = guided?.step || "project";
  const explanations = {
    project: ["Confirm the project boundary", "Validate the local workspace before choosing delivery context."],
    "work-item": ["Choose durable Work Item context", "Create a new request or resume saved evidence without launching runtime work."],
    runtime: ["Choose the execution runtime", "Review observed runtime readiness before a launch request is dispatched."],
    "review-launch": ["Review and launch", "Confirm the selected context, then use the same guarded service action as Studio."]
  };
  const [title, detail] = explanations[step] || explanations.project;
  return Object.freeze({title, detail});
}

function renderGuidedDeliveryPreference() {
  const enabled = state.onboarding.guidedDelivery !== false;
  const explanation = guidedDeliveryExplanation();
  return `
    <section class="guided-delivery-preference" aria-labelledby="guidedDeliveryTitle">
      <div>
        <strong id="guidedDeliveryTitle">Guided Delivery</strong>
        <p>Presentation guidance only; selected context, requests, and durable outcomes stay unchanged.</p>
      </div>
      <button type="button" class="secondary" data-guided-delivery-toggle aria-pressed="${enabled}">
        ${enabled ? "Guidance on" : "Guidance off"}
      </button>
    </section>
    ${enabled ? `
      <aside class="guided-delivery-explanation" role="note">
        <span class="small-badge">Current decision</span>
        <strong>${escapeHtml(explanation.title)}</strong>
        <p>${escapeHtml(explanation.detail)}</p>
      </aside>
    ` : ""}
  `;
}

function renderGuidedSetupProgress(guided = state.onboarding.guided || initialGuidedSetupState()) {
  const labels = [
    ["project", "Project"],
    ["work-item", "Work Item"],
    ["runtime", "Runtime"],
    ["review-launch", "Review & Launch"]
  ];
  const activeIndex = Math.max(0, GUIDED_SETUP_STEPS.indexOf(guided.step));
  return `
    <nav class="guided-setup-progress" aria-label="Guided setup progress">
      ${labels.map(([step, label], index) => {
        const complete = index < activeIndex;
        const active = index === activeIndex;
        return `
          <div class="guided-setup-step ${complete ? "complete" : active ? "active" : "upcoming"}" aria-current="${active ? "step" : "false"}">
            <span class="guided-setup-step-index">${complete ? "✓" : index + 1}</span>
            <strong>${escapeHtml(label)}</strong>
            <small>${complete ? "completed" : active ? "active" : "upcoming"}</small>
          </div>
        `;
      }).join("")}
    </nav>
  `;
}

function renderGuidedSetupSummary(guided = state.onboarding.guided || initialGuidedSetupState()) {
  if (guided.projectStatus !== "valid" && !guided.workItem) return "";
  const project = onboardingProject();
  return `
    <section class="surface guided-setup-summary" aria-label="Setup summary">
      <div class="surface-title"><span>Setup summary</span><span class="small-badge">selected context</span></div>
      <dl>
        <div><dt>Project</dt><dd>${escapeHtml(project?.project_root || state.onboarding.projectRootInput || "Local project")}</dd></div>
        <div><dt>Work Item</dt><dd>${escapeHtml(guided.workItem || "Choose a Work Item")}</dd></div>
      </dl>
    </section>
  `;
}

function onboardingProject() {
  return state.onboarding.project || null;
}

function onboardingRuntimeLabel(runtime) {
  const binary = runtime.binary?.status || "unknown";
  const command = runtime.execution_command?.status || "unknown";
  const authentication = runtime.authentication?.status || "unverified";
  return `binary ${binary}; command ${command}; authentication ${authentication}`;
}

function onboardingRunnerProfile(runtime) {
  const runtimeId = String(runtime.runtime_id || "");
  if (runtimeId === "generic-cli") {
    return {
      kind: "deterministic baseline",
      badge: "baseline",
      summary: "Best first smoke when a wrapper or fixture runtime is configured.",
      detail: "Uses adapter-flags execution instead of a native provider session.",
      recommended: true
    };
  }
  return {
    kind: "native provider",
    badge: "provider",
    summary: "Use for product-like runs with an authenticated provider CLI.",
    detail: "Review the command, auth, and permission posture before launch.",
    recommended: false
  };
}

function onboardingRunnerGuidance(runtimes) {
  if (!runtimes.some((runtime) => String(runtime.runtime_id || "") === "generic-cli")) {
    return "";
  }
  return `
    <div class="runner-selection-guidance">
      <strong>Start with the deterministic baseline when you are checking setup.</strong>
      <span>Native provider runners remain available for real model execution; every launch still requires an explicit runner selection.</span>
    </div>
  `;
  syncCurrentDecisionTarget();
}

function onboardingRunnerCards() {
  if (!onboardingProject()) {
    return renderStateSurface({
      kind: "runtime-readiness",
      state: "empty",
      title: "Validate a project",
      consequence: "Runtime selection becomes available after project validation."
    });
  }
  if (state.readinessLoading) {
    return renderStateSurface({
      kind: "runtime-readiness",
      state: "loading",
      title: "Checking runtime readiness",
      consequence: "Selection remains unavailable until the local readiness check completes."
    });
  }
  if (state.readinessError) {
    return renderStateSurface({
      kind: "runtime-readiness",
      state: "unavailable",
      title: "Runtime readiness unavailable",
      consequence: state.readinessError
    });
  }
  const runtimes = state.readiness?.runtimes || [];
  if (!runtimes.length) {
    return renderStateSurface({
      kind: "runtime-readiness",
      state: "unavailable",
      title: "No runtimes configured",
      consequence: "Configure a supported local runtime before launching delivery."
    });
  }
  const cards = runtimes.map((runtime) => {
    const runtimeId = String(runtime.runtime_id || "");
    const selected = runtimeId === state.selectedRuntime;
    const profile = onboardingRunnerProfile(runtime);
    return `
      <button class="runner-card ${profile.recommended ? "recommended" : ""} ${selected ? "selected" : ""}" data-onboarding-runtime="${escapeHtml(runtimeId)}" type="button" aria-pressed="${selected ? "true" : "false"}" aria-label="${escapeHtml(`${runtimeId}: ${profile.kind}; ${onboardingRuntimeLabel(runtime)}`)}">
        <span class="runner-card-head">
          <strong>${escapeHtml(runtimeId)}</strong>
          <span class="runner-card-meta">
            <span class="small-badge ${profile.recommended ? "good" : ""}">${escapeHtml(profile.badge)}</span>
            <span class="small-badge">binary ${escapeHtml(runtime.binary?.status || "unknown")}</span>
            <span class="small-badge">command ${escapeHtml(runtime.execution_command?.status || "unknown")}</span>
          </span>
        </span>
        <span class="runner-card-guidance">
          <strong>${escapeHtml(profile.summary)}</strong>
          ${escapeHtml(profile.detail)}
        </span>
        <span>${escapeHtml(onboardingRuntimeLabel(runtime))}</span>
        <span class="runner-command" title="${escapeHtml(readinessText(runtime.command))}">${escapeHtml(compactPath(readinessText(runtime.command), 64))}</span>
        ${renderRuntimeReadinessDimensions(runtime, {compact: true})}
      </button>
    `;
  }).join("");
  return `${onboardingRunnerGuidance(runtimes)}${cards}${renderProtectedWriteScope()}`;
}

function onboardingRecentProjects() {
  const projects = state.onboarding.recentProjects || [];
  if (!projects.length) return `<div class="empty-state">No recent projects in this UI process.</div>`;
  return projects.map((projectRoot) => `
    <button class="artifact-row" data-onboarding-recent-project="${escapeHtml(projectRoot)}" type="button">
      <span><strong>${escapeHtml(compactPath(projectRoot, 72))}</strong>${pathLine(projectRoot, 86)}</span>
      <span class="small-badge">recent</span>
    </button>
  `).join("");
}

function onboardingWorkItems() {
  const project = onboardingProject();
  const items = project?.work_items || [];
  if (!project) return `<div class="empty-state">Validate a project to discover Work Items.</div>`;
  if (!items.length) return `<div class="empty-state">No Work Items in this project yet.</div>`;
  return items.map((item) => `
    <button class="artifact-row" data-onboarding-resume="${escapeHtml(item.work_item)}" type="button">
      <span>
        <strong>${escapeHtml(item.work_item)}</strong>
        <span class="muted">${item.has_request_context ? "request context present" : "no request context"}</span>
      </span>
      <span class="small-badge">resume</span>
    </button>
  `).join("");
}

function onboardingProjectSummary() {
  const project = onboardingProject();
  if (!project) {
    return state.onboarding.inspectError
      ? `<div class="empty-state bad">${escapeHtml(state.onboarding.inspectError)}</div>`
      : `<div class="empty-state">Project status will appear after validation.</div>`;
  }
  return `
    <div class="panel-list">
      <div class="panel-item"><strong>Project root</strong>${pathLine(project.project_root, 86)}</div>
      <div class="panel-item"><strong>Workspace</strong><span>${project.workspace_exists ? "existing .aidd detected" : "new .aidd will be created"}</span></div>
    </div>
  `;
}

function onboardingProjectSetStatus() {
  if (state.onboarding.projectSetLoading) {
    return `<div class="empty-state loading-state">Validating project set...</div>`;
  }
  if (state.onboarding.projectSetError) {
    return `<div class="empty-state bad">${escapeHtml(state.onboarding.projectSetError)}</div>`;
  }
  const resolved = state.onboarding.projectSetResult;
  if (!resolved) return "";
  const projects = resolved.projects || [];
  return `
    <div class="setup-project-set-result">
      ${projects.map((project) => `
        <div class="panel-item">
          <strong>${escapeHtml(project.id)}</strong>
          ${pathLine(project.root, 72)}
        </div>
      `).join("")}
    </div>
  `;
}

function projectSetRows() {
  return state.onboarding.projectSetRows || [];
}

function projectSetDuplicateRoots() {
  const seen = new Set();
  const duplicates = new Set();
  projectSetRows().forEach((row) => {
    const root = String(row.root || "").trim();
    if (!root) return;
    if (seen.has(root)) duplicates.add(root);
    seen.add(root);
  });
  return duplicates;
}

function renderProjectSetEditor() {
  const duplicates = projectSetDuplicateRoots();
  const rows = projectSetRows();
  return `
    <div class="project-set-editor" aria-label="Project set root editor">
      <div class="project-set-row header" aria-hidden="true">
        <span>Project id</span>
        <span>Root</span>
        <span>Role</span>
        <span></span>
      </div>
      ${rows.map((row, index) => {
        const duplicate = duplicates.has(String(row.root || "").trim());
        return `
          <div class="project-set-row ${duplicate ? "duplicate" : ""}">
            <input id="project-set-${index}-id" name="project_set_${index}_id" data-project-set-field="id" data-project-set-index="${index}" type="text" value="${escapeHtml(row.id || "")}" placeholder="api" autocomplete="off" spellcheck="false" aria-label="Project id ${index + 1}">
            <input id="project-set-${index}-root" name="project_set_${index}_root" data-project-set-field="root" data-project-set-index="${index}" type="text" value="${escapeHtml(row.root || "")}" placeholder="services/api" autocomplete="off" spellcheck="false" aria-label="Project root ${index + 1}">
            <input id="project-set-${index}-role" name="project_set_${index}_role" data-project-set-field="role" data-project-set-index="${index}" type="text" value="${escapeHtml(row.role || "")}" placeholder="owner" autocomplete="off" spellcheck="false" aria-label="Project role ${index + 1}">
            <button data-project-set-remove="${index}" class="secondary" type="button" ${rows.length <= 1 ? "disabled" : ""}>Remove</button>
            ${duplicate ? `<span class="form-error">Duplicate root</span>` : ""}
          </div>
        `;
      }).join("")}
      <div class="setup-actions">
        <button data-project-set-add type="button" class="secondary">Add root</button>
        <button id="onboardingValidateProjectSet" class="secondary" type="button" ${onboardingProject() ? "" : "disabled"}>Validate project set</button>
      </div>
    </div>
  `;
}

function renderOnboardingAdvanced() {
  const project = onboardingProject();
  if (!project) return "";
  return `
    <details class="onboarding-advanced">
      <summary>Advanced configuration</summary>
      <div class="onboarding-advanced-content">
        <div class="panel-list">
          <div class="panel-item"><strong>AIDD root</strong>${pathLine(project.workspace_root, 86)}</div>
          <div class="panel-item"><strong>Config</strong>${pathLine(state.onboarding.configPath || "aidd.example.toml", 86)}</div>
        </div>
        <div class="surface-title compact"><span>Project set</span><span class="small-badge">optional</span></div>
        <div class="form-grid">
          ${renderProjectSetEditor()}
          ${onboardingProjectSetStatus()}
        </div>
      </div>
    </details>
  `;
}

function onboardingCanCreate() {
  return Boolean(
    onboardingProject()
    && state.onboarding.workItemInput.trim()
    && state.onboarding.requestText.trim()
  );
}

function onboardingContextSections(text = state.onboarding.contextText) {
  const normalized = String(text || "").trim();
  if (!normalized) return {context: "", constraints: ""};
  const marker = normalized.match(/^##\s+constraints?\s*$/im);
  if (!marker || marker.index === undefined) {
    return {context: normalized, constraints: ""};
  }
  return {
    context: normalized.slice(0, marker.index).trim(),
    constraints: normalized.slice(marker.index + marker[0].length).trim()
  };
}

function onboardingRequestPayload() {
  const outcome = String(state.onboarding.requestText || "").trim();
  const sections = onboardingContextSections();
  if (!sections.context && !sections.constraints) return outcome;
  return [
    outcome,
    sections.context ? `## Context\n\n${sections.context}` : "",
    sections.constraints ? `## Constraints\n\n${sections.constraints}` : ""
  ].filter(Boolean).join("\n\n");
}

function onboardingMarkdownHtml(text, emptyMessage) {
  const normalized = String(text || "").trim();
  if (!normalized) return `<p class="muted">${escapeHtml(emptyMessage)}</p>`;
  return typeof renderMarkdown === "function" ? renderMarkdown(normalized) : escapeHtml(normalized);
}

function onboardingCreatePreviewHtml() {
  const request = String(state.onboarding.requestText || "").trim();
  const sections = onboardingContextSections();
  return `
    <h2>Outcome</h2>
    <div data-create-preview-outcome>${onboardingMarkdownHtml(request, "Your requested outcome will appear here as Markdown before it is written.")}</div>
    <div class="target-preview-section">
      <h2>Context</h2>
      <div data-create-preview-context>${onboardingMarkdownHtml(sections.context, "No context provided.")}</div>
    </div>
    <div class="target-preview-section">
      <h2>Constraints</h2>
      <div data-create-preview-constraints>${onboardingMarkdownHtml(sections.constraints, "No constraints provided.")}</div>
    </div>
  `;
}

function syncOnboardingCreateEditorMode() {
  const mode = state.onboarding.createEditorMode === "preview" ? "preview" : "write";
  document.querySelectorAll("[data-create-editor-mode]").forEach((tab) => {
    const active = tab.dataset.createEditorMode === mode;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  const textarea = document.getElementById("onboardingRequest");
  const preview = document.querySelector("[data-create-editor-preview]");
  if (textarea) textarea.hidden = mode === "preview";
  if (preview) {
    preview.hidden = mode !== "preview";
    preview.innerHTML = onboardingMarkdownHtml(
      onboardingRequestPayload(),
      "Your requested outcome will appear here as Markdown before it is written."
    );
  }
}

function requestEditorPreviewMarkdown(text) {
  const normalized = String(text || "").trim();
  if (!normalized) return "";
  return `# User request\n\n${normalized}\n`;
}

function previewOperatorRequest() {
  const field = document.querySelector("[data-request-field]");
  const panel = document.querySelector("[data-request-preview-panel]");
  if (!field || !panel) return;
  const markdown = requestEditorPreviewMarkdown(field.value);
  if (!markdown) {
    panel.hidden = false;
    panel.textContent = "Request text is required before preview.";
    return;
  }
  panel.hidden = false;
  panel.innerHTML = `<pre data-request-preview-markdown>${escapeHtml(markdown)}</pre>`;
}

async function writeOperatorRequest() {
  const field = document.querySelector("[data-request-field]");
  const button = document.querySelector("[data-request-write]");
  const status = document.querySelector("[data-request-write-status]");
  const workItem = state.dashboard?.work_item || state.projectHome?.selected_work_item || "";
  if (!field || !button || !workItem) return;
  const requestText = field.value.trim();
  if (!requestText) {
    if (status) status.textContent = "Request text is required before writing.";
    return;
  }
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  if (status) status.textContent = "Writing durable request context…";
  try {
    const payload = await postJson("/api/work-item/request", {
      mode: "write",
      request_text: requestText
    });
    state.requestContext = payload.request || payload;
    if (status) status.textContent = "Request written to the durable context destination.";
    await fetchProjectHome(workItem);
    await fetchInbox();
    await renderAll({skipArtifactLoad: true});
  } catch (error) {
    if (status) status.textContent = error.message || "Request write failed.";
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
  }
}

function syncOnboardingCreateActionState() {
  const form = document.getElementById("onboardingCreateForm");
  if (!form) return;
  const canCreate = onboardingCanCreate() && !state.onboarding.creating;
  const targetButton = document.querySelector("[data-target-create-submit]");
  if (targetButton) targetButton.disabled = !canCreate;
  const preview = document.querySelector("[data-request-preview-markdown]");
  if (preview) preview.innerHTML = onboardingCreatePreviewHtml();
  const draftStatus = document.querySelector("[data-create-draft-status] .small-badge");
  if (draftStatus) {
    const hasDraft = Boolean(
      state.onboarding.requestText.trim() || state.onboarding.contextText.trim()
    );
    draftStatus.textContent = hasDraft ? "Unsaved draft" : "Ready to draft";
    draftStatus.classList.toggle("warn", hasDraft);
  }
  const workItem = document.getElementById("onboardingWorkItem")?.value.trim() || "WI-NEW";
  const destination = document.querySelector("[data-request-preview-panel] .target-document-destination code");
  if (destination) destination.textContent = `.aidd/workitems/${workItem}/context/operator-request.md`;
  syncOnboardingCreateEditorMode();
}

function projectWorkItemCanCreate() {
  return Boolean(
    state.projectHome?.project_root
    && state.onboarding.workItemInput.trim()
    && state.onboarding.requestText.trim()
  );
}

function syncProjectWorkItemCreateActionState() {
  const form = document.getElementById("projectNewWorkItemForm");
  if (!form) return;
  const button = form.querySelector('button[type="submit"]');
  if (!button) return;
  button.disabled = !(projectWorkItemCanCreate() && !state.onboarding.creating);
}

function renderProjectWorkItemCreator() {
  if (!state.onboarding.createPanelOpen) return "";
  const canCreate = projectWorkItemCanCreate() && !state.onboarding.creating;
  return `
    <section class="surface project-work-item-creator" data-project-work-item-creator>
      <div class="surface-title">
        <span>New Work Item</span>
        <button class="link-button" data-cancel-new-work-item type="button">Cancel</button>
      </div>
      <p class="muted">Capture the request now. Runtime selection happens only when you start delivery.</p>
      <form id="projectNewWorkItemForm" class="form-grid">
        <label class="field-label" for="projectNewWorkItem">Work Item id</label>
        <input id="projectNewWorkItem" name="work_item" type="text" maxlength="120" value="${escapeHtml(state.onboarding.workItemInput)}" autocomplete="off" spellcheck="false" placeholder="WI-123">
        <label class="field-label" for="projectNewRequest">Request</label>
        <textarea id="projectNewRequest" name="request" rows="5" maxlength="20000" placeholder="What should this Work Item deliver?">${escapeHtml(state.onboarding.requestText)}</textarea>
        <div class="setup-actions">
          <button type="submit" ${canCreate ? "" : "disabled"}>${state.onboarding.creating ? "Creating..." : "Create Work Item"}</button>
          ${state.onboarding.createError ? `<span class="form-error">${escapeHtml(state.onboarding.createError)}</span>` : ""}
        </div>
      </form>
    </section>
  `;
}

function renderOnboardingTopbar() {
  document.body.classList.add("setup-active");
  const project = onboardingProject();
  const projectRoot = project?.project_root || "select project";
  const runLabel = state.selectedRuntime ? `Runner: ${state.selectedRuntime}` : "Runner: choose before launch";
  const projectPath = document.getElementById("projectPath");
  const workItemChip = document.getElementById("intentChip");
  const runChip = document.getElementById("runChip");
  projectPath.textContent = projectRoot;
  projectPath.title = projectRoot;
  workItemChip.textContent = "Setup mode";
  workItemChip.title = "Setup mode";
  runChip.textContent = runLabel;
  runChip.title = runLabel;
  const topContextProject = document.getElementById("topContextProject");
  const topContextWorkItem = document.getElementById("topContextIntent");
  const topContextRun = document.getElementById("topContextRun");
  if (topContextProject) topContextProject.textContent = projectRoot;
  if (topContextWorkItem) topContextWorkItem.textContent = "Guided setup";
  if (topContextRun) topContextRun.textContent = state.selectedRuntime || "Ready";
  const localStatus = document.getElementById("localStatus");
  localStatus.textContent = state.onboarding.error || "Onboarding";
  localStatus.title = state.onboarding.error || "Onboarding";
  localStatus.className = state.onboarding.error ? "status-chip" : "status-chip good";
  document.getElementById("openWorkspaceButton").disabled = true;
  document.getElementById("newWorkItemButton").disabled = true;
  if (project) renderRuntimeSelector();
  else {
    const select = document.getElementById("runtimeSelect");
    select.innerHTML = `<option value="">Validate project first</option>`;
  }
}

function renderOnboarding() {
  renderOnboardingTopbar();
  const content = document.getElementById("intentContent");
  const guided = state.onboarding.guided || initialGuidedSetupState();
  const selectedRunner = state.selectedRuntime
    ? `<span class="small-badge good">${escapeHtml(state.selectedRuntime)}</span>`
    : `<span class="small-badge">optional until launch</span>`;
  const requestText = state.onboarding.requestText.trim();
  const workItem = state.onboarding.workItemInput.trim() || "WI-NEW";
  content.innerHTML = `
    <div class="onboarding-shell target-create-work-item" data-create-work-item-surface data-guided-step="${escapeHtml(guided.step)}">
      <header class="target-surface-header create-work-item-header">
        <div>
          <h1>Create work item</h1>
          <p>Capture the request, context, and scope. Runner selection happens when you launch work.</p>
        </div>
        <div class="target-surface-status" data-create-draft-status>
          <span class="target-draft-status"><span aria-hidden="true">●</span><span class="small-badge ${requestText ? "warn" : ""}">${requestText ? "Unsaved draft" : "Ready to draft"}</span></span>
          <button class="secondary" data-cancel-new-work-item type="button">Discard draft</button>
        </div>
      </header>
      <div class="target-create-layout">
        <section class="target-create-editor" data-request-editor data-onboarding-work-item-branch="create" aria-label="Work Item request editor">
          <div class="target-panel-heading"><strong>Work Item details</strong><span class="small-badge">operator-authored</span></div>
          <form id="onboardingCreateForm" class="form-grid target-create-form">
            <label class="field-label" for="onboardingWorkItem">Work Item ID</label>
            <input id="onboardingWorkItem" name="work_item" type="text" maxlength="120" value="${escapeHtml(state.onboarding.workItemInput)}" autocomplete="off" spellcheck="false" placeholder="WI-123">
            <span class="field-help">Use a stable identifier that can be retained across runs.</span>
            <label class="field-label" for="onboardingRequest">Requested outcome</label>
            <div class="target-editor-tabs" role="tablist" aria-label="Request editor mode">
              <button class="target-editor-tab ${state.onboarding.createEditorMode === "write" ? "active" : ""}" data-create-editor-mode="write" type="button" role="tab" aria-selected="${state.onboarding.createEditorMode === "write" ? "true" : "false"}">Write</button>
              <button class="target-editor-tab ${state.onboarding.createEditorMode === "preview" ? "active" : ""}" data-create-editor-mode="preview" type="button" role="tab" aria-selected="${state.onboarding.createEditorMode === "preview" ? "true" : "false"}">Preview</button>
            </div>
            <textarea id="onboardingRequest" name="request" rows="11" maxlength="20000" placeholder="What should this Work Item deliver?" ${state.onboarding.createEditorMode === "preview" ? "hidden" : ""}>${escapeHtml(state.onboarding.requestText)}</textarea>
            <div class="target-create-editor-preview" data-create-editor-preview aria-label="Rendered request preview" ${state.onboarding.createEditorMode === "preview" ? "" : "hidden"}>${onboardingMarkdownHtml(onboardingRequestPayload(), "Your requested outcome will appear here as Markdown before it is written.")}</div>
            <label class="field-label target-create-context-label" for="onboardingContext">Context and constraints <span class="muted">(optional)</span></label>
            <textarea id="onboardingContext" name="context" rows="5" maxlength="20000" data-create-context placeholder="Add any background, assumptions, known constraints, or helpful links.">${escapeHtml(state.onboarding.contextText)}</textarea>
            <p class="field-help">Use a <code>## Constraints</code> heading when you want the preview to separate constraints from context.</p>
            <label class="checkbox-row target-create-advanced-toggle" for="onboardingForceContext">
              <input id="onboardingForceContext" name="force_context" type="checkbox" ${state.onboarding.forceContext ? "checked" : ""}>
              <span>Overwrite existing request context</span>
            </label>
            ${state.onboarding.createError ? `<span class="form-error">${escapeHtml(state.onboarding.createError)}</span>` : ""}
          </form>
        </section>
        <aside class="target-create-preview" data-request-preview-panel aria-label="Request Markdown preview">
          <div class="target-panel-heading"><strong>operator-request.md</strong><button class="secondary" type="button" data-copy-request-destination aria-label="Copy request destination">Copy</button></div>
          <p class="target-document-destination">Destination: <code>.aidd/workitems/${escapeHtml(workItem)}/context/operator-request.md</code></p>
          <div class="target-markdown-preview" data-request-preview-markdown>${onboardingCreatePreviewHtml()}</div>
        </aside>
      </div>
      <footer class="target-create-footer"><span>Runner is selected when you launch work.</span><div class="setup-actions"><button class="secondary" data-cancel-new-work-item type="button">Cancel</button><button type="submit" form="onboardingCreateForm" data-target-create-submit data-aidd-primary-action ${onboardingCanCreate() && !state.onboarding.creating ? "" : "disabled"}>Create work item</button></div></footer>
      <details class="target-create-supporting" ${onboardingProject() && state.selectedRuntime ? "" : "open"}>
        <summary>Project scope and supporting setup</summary>
        <div class="onboarding-supporting-grid">
          <section class="surface onboarding-panel">
            <div class="surface-title"><span>Project setup</span><span class="small-badge">${state.onboarding.loading ? "loading" : "local"}</span></div>
            <form id="onboardingProjectForm" class="form-grid">
              <label class="field-label" for="onboardingProjectRoot">Project root</label>
              <div class="inline-form-row">
                <input id="onboardingProjectRoot" name="project_root" type="text" value="${escapeHtml(state.onboarding.projectRootInput)}" autocomplete="off" spellcheck="false">
                <button type="submit" class="secondary" ${state.onboarding.inspecting ? "disabled" : ""}>Validate project</button>
              </div>
            </form>
            ${onboardingProjectSummary()}
            ${renderOnboardingAdvanced()}
          </section>
          <section class="surface onboarding-panel target-create-resume" data-onboarding-work-item-branch="resume">
            <div class="surface-title"><span>Saved Work Items</span><span class="small-badge">resume</span></div>
            <p class="muted">Open saved Work Item context now; runtime selection and launch remain separate actions.</p>
            <div class="panel-list">${onboardingWorkItems()}</div>
          </section>
          <section class="surface onboarding-panel">
            <div class="surface-title"><span>Runner</span>${selectedRunner}</div>
            <div class="runner-card-grid">${onboardingRunnerCards()}</div>
          </section>
        </div>
      </details>
    </div>
  `;
  syncOnboardingCreateEditorMode();
}

async function inspectOnboardingProject() {
  state.onboarding.inspecting = true;
  state.onboarding.inspectError = "";
  state.onboarding.project = null;
  state.readinessLoading = true;
  state.readinessError = "";
  renderOnboarding();
  try {
    const payload = await postJson("/api/onboarding/project", {
      project_root: state.onboarding.projectRootInput
    });
    state.onboarding.project = payload.project || null;
    state.onboarding.configPath = payload.config_path || "";
    state.onboarding.recentProjects = payload.recent_projects || state.onboarding.recentProjects;
    state.readiness = payload.readiness || {runtimes: []};
    state.readinessError = "";
    transitionGuidedSetup("project-valid");
  } catch (error) {
    state.onboarding.inspectError = error.message || "project validation failed";
    state.readiness = {runtimes: []};
    state.readinessError = "";
    transitionGuidedSetup("project-invalid", {error: state.onboarding.inspectError});
  } finally {
    state.onboarding.inspecting = false;
    state.readinessLoading = false;
    renderOnboarding();
  }
}

function onboardingProjectSetPayload() {
  const rows = projectSetRows()
    .map((row) => ({
      id: String(row.id || "").trim(),
      root: String(row.root || "").trim(),
      role: String(row.role || "").trim()
    }))
    .filter((row) => row.id || row.root || row.role);
  if (!rows.length) return [];
  const roots = new Set();
  rows.forEach((row, index) => {
    if (!row.id) throw new Error(`Project set row ${index + 1} requires an id.`);
    if (!row.root) throw new Error(`Project set row ${index + 1} requires a root.`);
    if (roots.has(row.root)) throw new Error(`Project set root is duplicated: ${row.root}.`);
    roots.add(row.root);
  });
  return rows.map((item) => {
    return {
      id: item.id,
      root: item.root,
      role: item.role || null
    };
  });
}

function updateProjectSetRow(index, field, value) {
  const rows = projectSetRows().map((row) => ({...row}));
  if (!rows[index]) return;
  rows[index][field] = value;
  state.onboarding.projectSetRows = rows;
  state.onboarding.projectSetResult = null;
  state.onboarding.projectSetError = "";
}

function addProjectSetRow() {
  state.onboarding.projectSetRows = [...projectSetRows(), {id: "", root: "", role: ""}];
  state.onboarding.projectSetResult = null;
  renderOnboarding();
}

function removeProjectSetRow(index) {
  const rows = projectSetRows().filter((_, rowIndex) => rowIndex !== index);
  state.onboarding.projectSetRows = rows.length ? rows : [{id: "", root: "", role: ""}];
  state.onboarding.projectSetResult = null;
  renderOnboarding();
}

async function validateOnboardingProjectSet() {
  state.onboarding.projectSetLoading = true;
  state.onboarding.projectSetError = "";
  state.onboarding.projectSetResult = null;
  renderOnboarding();
  try {
    const payload = await postJson("/api/onboarding/project-set", {
      project_root: state.onboarding.projectRootInput,
      project_set: onboardingProjectSetPayload()
    });
    state.onboarding.projectSetResult = payload.project_set || null;
  } catch (error) {
    state.onboarding.projectSetError = error.message || "project set validation failed";
  } finally {
    state.onboarding.projectSetLoading = false;
    renderOnboarding();
  }
}

async function completeOnboardingWorkItem(action, workItem) {
  transitionGuidedSetup("work-item-selected", {branch: action, workItem});
  if (action === "create" && state.selectedRuntime) {
    transitionGuidedSetup("runtime-selected", {runtimeId: state.selectedRuntime});
  }
  state.onboarding.creating = true;
  state.onboarding.createError = "";
  renderOnboarding();
  try {
    await postJson("/api/onboarding/work-item", {
      action,
      project_root: state.onboarding.projectRootInput,
      work_item: workItem,
      request: action === "create" ? onboardingRequestPayload() : undefined,
      force_context: action === "create" ? state.onboarding.forceContext : false,
      project_set: action === "create" ? onboardingProjectSetPayload() : []
    });
    state.onboarding.setupRequired = false;
    document.body.classList.remove("setup-active");
    document.getElementById("openWorkspaceButton").disabled = false;
    await refresh();
  } catch (error) {
    state.onboarding.createError = error.message || "Work Item setup failed";
  } finally {
    state.onboarding.creating = false;
    if (state.onboarding.setupRequired) renderOnboarding();
  }
}

async function openProjectWorkItemCreation() {
  state.onboarding.createPanelOpen = true;
  state.onboarding.createError = "";
  state.onboarding.workItemInput = "";
  state.onboarding.requestText = "";
  state.onboarding.contextText = "";
  state.onboarding.createEditorMode = "write";
  activateTab("project-home", {historyMode: "push"});
  renderProjectHomeRail();
  await renderCockpit();
  window.requestAnimationFrame(() => document.getElementById("projectNewWorkItem")?.focus());
}

async function closeProjectWorkItemCreation() {
  state.onboarding.createPanelOpen = false;
  state.onboarding.createError = "";
  await renderCockpit();
}

async function createProjectWorkItem() {
  if (!projectWorkItemCanCreate()) {
    state.onboarding.createError = "Work Item id and request are required.";
    await renderCockpit();
    return;
  }
  state.onboarding.creating = true;
  state.onboarding.createError = "";
  await renderCockpit();
  try {
    const payload = await postJson("/api/onboarding/work-item", {
      action: "create",
      project_root: state.projectHome?.project_root || state.onboarding.projectRootInput || ".",
      work_item: state.onboarding.workItemInput.trim(),
      request: state.onboarding.requestText
    });
    const workItem = payload.created?.work_item || payload.context?.work_item || state.onboarding.workItemInput.trim();
    state.onboarding.contextWorkItem = workItem;
    state.onboarding.createPanelOpen = false;
    state.onboarding.workItemInput = "";
    state.onboarding.requestText = "";
    state.activeRouteWorkItem = workItem;
    state.activeRunId = "";
    setOperatorMode("work");
    syncLocationState({historyMode: "push"});
    await refresh();
  } catch (error) {
    state.onboarding.createError = error.message || "Work Item creation failed";
  } finally {
    state.onboarding.creating = false;
    if (state.onboarding.createPanelOpen) await renderCockpit();
  }
}

async function resumeProjectHomeWorkItem(workItem, options = {}) {
  const item = projectHomeWorkItems().find((candidate) => candidate.work_item === workItem) || null;
  await postJson("/api/onboarding/work-item", {
    action: "resume",
    project_root: state.projectHome?.project_root || state.onboarding.projectRootInput || ".",
    work_item: workItem
  });
  state.onboarding.setupRequired = false;
  state.activeStage = item?.active_stage || state.activeStage;
  state.activeRunId = item?.latest_run?.run_id || "";
  state.activeArtifactKey = "";
  state.selectedEvidenceNodeId = "";
  state.selectedEvidenceEdgeId = "";
  setOperatorMode(options.openLatestRun || item ? "work" : "project-home");
  document.body.classList.remove("setup-active");
  document.getElementById("openWorkspaceButton").disabled = false;
  await fetchDashboard();
  await fetchProjectHome(workItem);
  await fetchInbox();
  await renderAll();
  void fetchReadiness().then((accepted) => {
    if (accepted) renderReadinessSurfaces();
  });
}

async function activateInboxWorkItemRoute(context) {
  if (state.dashboard?.work_item !== context.workItem) {
    await postJson("/api/onboarding/work-item", {
      action: "resume",
      project_root: state.projectHome?.project_root || state.onboarding.projectRootInput || ".",
      work_item: context.workItem
    });
    state.onboarding.setupRequired = false;
  }
  await navigateOperatorRouteIntent("inbox-work-item", context);
}
