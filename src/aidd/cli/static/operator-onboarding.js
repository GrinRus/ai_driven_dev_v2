function onboardingProject() {
  return state.onboarding.project || null;
}

function onboardingRuntimeLabel(runtime) {
  const provider = runtime.provider_available ? "provider ready" : "provider missing";
  const command = runtime.execution_command_available ? "command ready" : "command missing";
  return `${provider}; ${command}`;
}

function onboardingRunnerCards() {
  if (!onboardingProject()) {
    return `<div class="empty-state">Validate a project before selecting a runner.</div>`;
  }
  if (state.readinessLoading) {
    return `<div class="empty-state loading-state">Checking runner readiness...</div>`;
  }
  if (state.readinessError) {
    return `<div class="empty-state">Runner readiness unavailable: ${escapeHtml(state.readinessError)}</div>`;
  }
  const runtimes = state.readiness?.runtimes || [];
  if (!runtimes.length) return `<div class="empty-state">No runtimes are configured.</div>`;
  return runtimes.map((runtime) => {
    const runtimeId = String(runtime.runtime_id || "");
    const ready = runtime.provider_available && runtime.execution_command_available;
    const selected = runtimeId === state.selectedRuntime;
    return `
      <button class="runner-card ${selected ? "selected" : ""}" data-onboarding-runtime="${escapeHtml(runtimeId)}" type="button" aria-pressed="${selected ? "true" : "false"}">
        <span class="runner-card-head">
          <strong>${escapeHtml(runtimeId)}</strong>
          <span class="small-badge ${ready ? "good" : "warn"}">${ready ? "ready" : "check"}</span>
        </span>
        <span>${escapeHtml(onboardingRuntimeLabel(runtime))}</span>
        <span class="runner-command" title="${escapeHtml(readinessText(runtime.command))}">${escapeHtml(compactPath(readinessText(runtime.command), 64))}</span>
      </button>
    `;
  }).join("");
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
  const canResume = Boolean(state.selectedRuntime);
  return items.map((item) => `
    <button class="artifact-row" data-onboarding-resume="${escapeHtml(item.work_item)}" type="button" ${canResume ? "" : "disabled"}>
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
  document.getElementById("projectPath").textContent = project?.project_root || "select project";
  document.getElementById("workItemChip").textContent = "Setup mode";
  document.getElementById("runChip").textContent = state.selectedRuntime ? `Runner: ${state.selectedRuntime}` : "Runner: required";
  const localStatus = document.getElementById("localStatus");
  localStatus.textContent = state.onboarding.error || "Onboarding";
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
            <input id="onboardingProjectRoot" type="text" value="${escapeHtml(state.onboarding.projectRootInput)}" autocomplete="off" spellcheck="false">
            <button type="submit" class="secondary" ${state.onboarding.inspecting ? "disabled" : ""}>Validate</button>
          </div>
        </form>
        ${onboardingProjectSummary()}
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
          <span>Create work item</span>
          <span class="small-badge">${state.selectedRuntime ? "runner selected" : "select runner"}</span>
        </div>
        <form id="onboardingCreateForm" class="form-grid">
          <label class="field-label" for="onboardingWorkItem">Work item id</label>
          <input id="onboardingWorkItem" type="text" maxlength="120" value="${escapeHtml(state.onboarding.workItemInput)}" autocomplete="off" spellcheck="false">
          <label class="field-label" for="onboardingRequest">Request</label>
          <textarea id="onboardingRequest" rows="7" maxlength="20000">${escapeHtml(state.onboarding.requestText)}</textarea>
          <label class="checkbox-row">
            <input id="onboardingForceContext" type="checkbox" ${state.onboarding.forceContext ? "checked" : ""}>
            <span>Overwrite existing request context</span>
          </label>
          <div class="setup-actions">
            <button type="submit" ${onboardingCanCreate() && !state.onboarding.creating ? "" : "disabled"}>${state.onboarding.creating ? "Creating..." : "Create and open command center"}</button>
            ${state.onboarding.createError ? `<span class="form-error">${escapeHtml(state.onboarding.createError)}</span>` : ""}
          </div>
        </form>
      </section>

      <section class="surface onboarding-panel">
        <div class="surface-title">
          <span>Resume existing</span>
          <span class="small-badge">${(onboardingProject()?.work_items || []).length}</span>
        </div>
        <div class="panel-list">${onboardingWorkItems()}</div>
      </section>

      <section class="surface onboarding-panel">
        <div class="surface-title">
          <span>Project set</span>
          <span class="small-badge">optional</span>
        </div>
        <div class="form-grid">
          <label class="field-label" for="onboardingProjectSet">Projects JSON</label>
          <textarea id="onboardingProjectSet" rows="4" spellcheck="false" placeholder='[{"id":"api","root":"services/api"}]'>${escapeHtml(state.onboarding.projectSetText)}</textarea>
          <div class="setup-actions">
            <button id="onboardingValidateProjectSet" class="secondary" type="button" ${onboardingProject() ? "" : "disabled"}>Validate project set</button>
          </div>
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
  } catch (error) {
    state.onboarding.inspectError = error.message || "project validation failed";
    state.readiness = {runtimes: []};
    state.readinessError = "";
  } finally {
    state.onboarding.inspecting = false;
    state.readinessLoading = false;
    renderOnboarding();
  }
}

function onboardingProjectSetPayload() {
  const text = state.onboarding.projectSetText.trim();
  if (!text) return [];
  const parsed = JSON.parse(text);
  if (!Array.isArray(parsed)) throw new Error("Project set must be a JSON array.");
  return parsed.map((item, index) => {
    if (!item || typeof item !== "object") throw new Error(`Project set item ${index + 1} must be an object.`);
    return {
      id: String(item.id || "").trim(),
      root: String(item.root || "").trim(),
      role: item.role == null ? null : String(item.role).trim()
    };
  });
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
  if (!state.selectedRuntime) {
    toast("Select runner first.");
    return;
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
