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
      return Object.freeze({...guided, error: "Select a valid create or resume work item."});
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

function onboardingProject() {
  return state.onboarding.project || null;
}

function onboardingRuntimeLabel(runtime) {
  const provider = runtime.provider_available ? "provider ready" : "provider missing";
  const command = runtime.execution_command_available ? "command ready" : "command missing";
  return `${provider}; ${command}`;
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
    const ready = runtime.provider_available && runtime.execution_command_available;
    const selected = runtimeId === state.selectedRuntime;
    const profile = onboardingRunnerProfile(runtime);
    return `
      <button class="runner-card ${profile.recommended ? "recommended" : ""} ${selected ? "selected" : ""}" data-onboarding-runtime="${escapeHtml(runtimeId)}" type="button" aria-pressed="${selected ? "true" : "false"}" aria-label="${escapeHtml(`${runtimeId}: ${profile.kind}; ${onboardingRuntimeLabel(runtime)}`)}">
        <span class="runner-card-head">
          <strong>${escapeHtml(runtimeId)}</strong>
          <span class="runner-card-meta">
            <span class="small-badge ${profile.recommended ? "good" : ""}">${escapeHtml(profile.badge)}</span>
            <span class="small-badge ${ready ? "good" : "warn"}">${ready ? "ready" : "check"}</span>
          </span>
        </span>
        <span class="runner-card-guidance">
          <strong>${escapeHtml(profile.summary)}</strong>
          ${escapeHtml(profile.detail)}
        </span>
        <span>${escapeHtml(onboardingRuntimeLabel(runtime))}</span>
        <span class="runner-command" title="${escapeHtml(readinessText(runtime.command))}">${escapeHtml(compactPath(readinessText(runtime.command), 64))}</span>
      </button>
    `;
  }).join("");
  return `${onboardingRunnerGuidance(runtimes)}${cards}`;
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
  if (!project) return `<div class="empty-state">Validate a project to discover work items.</div>`;
  if (!items.length) return `<div class="empty-state">No work items in this project yet.</div>`;
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
      <div class="panel-item"><strong>AIDD root</strong>${pathLine(project.workspace_root, 86)}</div>
      <div class="panel-item"><strong>Workspace</strong><span>${project.workspace_exists ? "existing .aidd detected" : "new .aidd will be created"}</span></div>
      <div class="panel-item"><strong>Config</strong>${pathLine(state.onboarding.configPath || "aidd.example.toml", 86)}</div>
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

function onboardingCanCreate() {
  return Boolean(
    onboardingProject()
    && state.onboarding.workItemInput.trim()
    && state.onboarding.requestText.trim()
    && state.selectedRuntime
  );
}

function syncOnboardingCreateActionState() {
  const form = document.getElementById("onboardingCreateForm");
  if (!form) return;
  const button = form.querySelector('button[type="submit"]');
  if (!button) return;
  button.disabled = !(onboardingCanCreate() && !state.onboarding.creating);
}

function renderOnboardingTopbar() {
  document.body.classList.add("setup-active");
  const project = onboardingProject();
  const projectRoot = project?.project_root || "select project";
  const runLabel = state.selectedRuntime ? `Runner: ${state.selectedRuntime}` : "Runner: required";
  const projectPath = document.getElementById("projectPath");
  const workItemChip = document.getElementById("workItemChip");
  const runChip = document.getElementById("runChip");
  projectPath.textContent = projectRoot;
  projectPath.title = projectRoot;
  workItemChip.textContent = "Setup mode";
  workItemChip.title = "Setup mode";
  runChip.textContent = runLabel;
  runChip.title = runLabel;
  const localStatus = document.getElementById("localStatus");
  localStatus.textContent = state.onboarding.error || "Onboarding";
  localStatus.title = state.onboarding.error || "Onboarding";
  localStatus.className = state.onboarding.error ? "status-chip" : "status-chip good";
  document.getElementById("openWorkspaceButton").disabled = true;
  if (project) renderRuntimeSelector();
  else {
    const select = document.getElementById("runtimeSelect");
    select.innerHTML = `<option value="">Validate project first</option>`;
  }
}

function renderOnboarding() {
  renderOnboardingTopbar();
  const content = document.getElementById("cockpitContent");
  const selectedRunner = state.selectedRuntime
    ? `<span class="small-badge good">${escapeHtml(state.selectedRuntime)}</span>`
    : `<span class="small-badge warn">required</span>`;
  content.innerHTML = `
    <div class="onboarding-shell">
      <section class="surface onboarding-panel">
        <div class="surface-title">
          <span>Project setup</span>
          <span class="small-badge">${state.onboarding.loading ? "loading" : "local"}</span>
        </div>
        <form id="onboardingProjectForm" class="form-grid">
          <label class="field-label" for="onboardingProjectRoot">Project root</label>
          <div class="inline-form-row">
            <input id="onboardingProjectRoot" name="project_root" type="text" value="${escapeHtml(state.onboarding.projectRootInput)}" autocomplete="off" spellcheck="false">
            <button type="submit" class="secondary" ${state.onboarding.inspecting ? "disabled" : ""}>Validate</button>
          </div>
        </form>
        ${onboardingProjectSummary()}
      </section>

      <section class="surface onboarding-panel">
        <div class="surface-title">
          <span>Work item</span>
          <span class="small-badge">create or resume</span>
        </div>
        <div class="onboarding-work-item-branches">
          <article class="onboarding-work-item-branch" data-onboarding-work-item-branch="create">
            <div class="surface-title compact"><span>Create</span><span class="small-badge">new context</span></div>
            <form id="onboardingCreateForm" class="form-grid">
              <label class="field-label" for="onboardingWorkItem">Work item id</label>
              <input id="onboardingWorkItem" name="work_item" type="text" maxlength="120" value="${escapeHtml(state.onboarding.workItemInput)}" autocomplete="off" spellcheck="false">
              <label class="field-label" for="onboardingRequest">Request</label>
              <textarea id="onboardingRequest" name="request" rows="7" maxlength="20000">${escapeHtml(state.onboarding.requestText)}</textarea>
              <label class="checkbox-row" for="onboardingForceContext">
                <input id="onboardingForceContext" name="force_context" type="checkbox" ${state.onboarding.forceContext ? "checked" : ""}>
                <span>Overwrite existing request context</span>
              </label>
              <div class="setup-actions">
                <button type="submit" ${onboardingCanCreate() && !state.onboarding.creating ? "" : "disabled"}>${state.onboarding.creating ? "Creating..." : "Create and open command center"}</button>
                ${state.onboarding.createError ? `<span class="form-error">${escapeHtml(state.onboarding.createError)}</span>` : ""}
              </div>
            </form>
          </article>
          <article class="onboarding-work-item-branch" data-onboarding-work-item-branch="resume">
            <div class="surface-title compact"><span>Resume</span><span class="small-badge">inspect context</span></div>
            <p class="muted">Open saved work-item context now; runtime selection and launch remain separate actions.</p>
            <div class="panel-list">${onboardingWorkItems()}</div>
          </article>
        </div>
      </section>

      <section class="surface onboarding-panel">
        <div class="surface-title">
          <span>Runner</span>
          ${selectedRunner}
        </div>
        <div class="runner-card-grid">${onboardingRunnerCards()}</div>
      </section>

      <section class="surface onboarding-panel">
        <div class="surface-title">
          <span>Project set</span>
          <span class="small-badge">optional</span>
        </div>
        <div class="form-grid">
          ${renderProjectSetEditor()}
          ${onboardingProjectSetStatus()}
        </div>
      </section>

      <section class="surface onboarding-panel">
        <div class="surface-title">
          <span>Recent projects</span>
          <span class="small-badge">${(state.onboarding.recentProjects || []).length}</span>
        </div>
        <div class="panel-list">${onboardingRecentProjects()}</div>
      </section>
    </div>
  `;
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
  if (action === "create" && !state.selectedRuntime) {
    toast("Select runner first.");
    return;
  }
  transitionGuidedSetup("work-item-selected", {branch: action, workItem});
  if (action === "create") {
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
      request: action === "create" ? state.onboarding.requestText : undefined,
      force_context: action === "create" ? state.onboarding.forceContext : false,
      project_set: action === "create" ? onboardingProjectSetPayload() : []
    });
    state.onboarding.setupRequired = false;
    document.body.classList.remove("setup-active");
    document.getElementById("openWorkspaceButton").disabled = false;
    await refresh();
  } catch (error) {
    state.onboarding.createError = error.message || "work item setup failed";
  } finally {
    state.onboarding.creating = false;
    if (state.onboarding.setupRequired) renderOnboarding();
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
  await renderAll();
}
