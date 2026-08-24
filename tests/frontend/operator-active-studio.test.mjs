import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

async function contextFor(dashboard) {
  const context = vm.createContext({
    console,
    state: {
      dashboard,
      activeStage: "idea",
      nextFlowWizard: {active: false},
      selectedTaskId: "TL-1",
      taskWorkspaceFilter: "",
      selectedRuntime: "codex",
      activeJobStatus: null,
      activeJobConnection: {state: "unknown"},
      activeJobLogChunks: [],
      activeJobCursor: 0,
    },
    escapeHtml(value) { return String(value ?? ""); },
    stageTitle(stage) { return stage.toUpperCase(); },
    stageSubtitle() { return "Clarify the request"; },
    activeStageItem() { return dashboard.stages?.[0] || null; },
    activeStageView() { return dashboard.active_stage_view || null; },
    selectedRuntimeView() { return null; },
    renderRuntimeReadinessDimensions() { return ""; },
    renderProtectedWriteScope() { return ""; },
    pathLine(value) { return `<code>${value}</code>`; },
    renderStateSurface({title}) { return `<div data-state-surface>${title}</div>`; },
    studioFlowCompleteEligibility() { return {eligible: false}; },
    workflowProgressSummary(options) { return `<div data-workflow-collapsed="${Boolean(options?.collapsed)}"></div>`; },
    renderContextualRunnerControl({actionLabel}) {
      return `<div class="contextual-runner-control" data-contextual-runner-control>${actionLabel}</div>`;
    },
    secondsLabel(value) { return `${value}s`; },
    runtimeOutputFreshnessLabel(job) { return `Last runtime output ${job.runtime_output_age_seconds}s ago`; },
    logEntriesFromChunks(chunks) { return (chunks || []).map((chunk) => ({stream: chunk.stream || "stdout", source: "runtime", text: chunk.text || ""})); },
    rawTextFromEntries(entries) { return entries.map((entry) => `[${entry.stream}] ${entry.text}`).join("\\n"); },
    renderActiveJobConnectionSurface() { return `<div data-connection-state="reconnecting">Reconnecting to live output</div>`; },
  });
  const source = await readFile(path.join(staticRoot, "operator-active-studio.js"), "utf8");
  vm.runInContext(source, context, {filename: "operator-active-studio.js"});
  return context;
}

test("active Studio preserves Work Item, phase, and status context", async () => {
  const context = await contextFor({
    work_item: "WI-1",
    run: {run_id: "run-1"},
    stages: [{stage: "idea", status: "executing", subtitle: "Clarify", attempt_count: 1}],
  });
  const html = vm.runInContext("renderActiveStudio()", context);
  assert.match(html, /data-studio-surface="active-studio"/);
  assert.match(html, /data-state="active"/);
  assert.match(html, /<dt>Work Item<\/dt><dd>WI-1<\/dd>/);
  assert.match(html, /data-workflow-collapsed="true"/);
  for (const value of ["idea", "Stage running"]) {
    assert.match(html, new RegExp(value));
  }
  assert.match(html, /Work Item Workspace/);
  assert.doesNotMatch(html, /<dt>Work item<\/dt>/);
  assert.doesNotMatch(html, /<dt>Run<\/dt>/);
  assert.match(html, /data-stage-mobile-toggle/);
  assert.match(html, /aria-controls="canonicalStageGroups"/);
  assert.match(html, /data-mobile-stages-expanded="false"/);
  const stages = [...html.matchAll(/data-canonical-stage="([^"]+)"/g)].map((match) => match[1]);
  assert.deepEqual(stages, ["idea", "research", "plan", "review-spec", "tasklist", "implement", "review", "qa"]);
  assert.match(html, /8 stages/);
  for (const phase of ["Understand", "Decide", "Deliver", "Prove"]) {
    assert.match(html, new RegExp(phase));
  }
  assert.doesNotMatch(html, /data-primary-action/);
});

test("no-run, blocked, and terminal Studio states do not invent primary actions", async () => {
  const dashboards = [
    {work_item: "WI-1", run: null, stages: []},
    {work_item: "WI-1", run: {run_id: "run-1"}, stages: [{status: "blocked"}]},
    {
      work_item: "WI-1", run: {run_id: "run-1"}, stages: [{status: "succeeded"}],
      terminal_handoff: {status: "completed", final_qa_status: "ready"},
    },
  ];
  const states = [];
  for (const dashboard of dashboards) {
    const context = await contextFor(dashboard);
    const html = vm.runInContext("renderActiveStudio()", context);
    states.push(html.match(/data-state="([^"]+)"/)?.[1]);
    assert.doesNotMatch(html, /data-primary-action/);
  }
  assert.deepEqual(states, ["no-run", "blocked", "terminal"]);
});

test("Task Workspace renders the selected contract from core action projection", async () => {
  const dashboard = {
    work_item: "WI-1",
    run: {run_id: "run-1"},
    stages: [{stage: "idea", status: "succeeded"}],
  };
  const context = await contextFor(dashboard);
  const taskView = {
    task_list: [{
      id: "TL-1",
      title: "Implement selected task",
      status: "pending",
      group: "Ready",
      dependencies: [],
      attempt_count: 0,
    }],
    next_ready_task: "TL-1",
    critical_path: ["TL-1"],
    selected_task: {
      id: "TL-1",
      title: "Implement selected task",
      status: "pending",
      outcome: "Deliver the bounded implementation.",
      dominant_deliverable: "A reviewed implementation",
      scope_paths: ["src/example.py"],
      acceptance_criteria: [{id: "AC-1", text: "Focused test passes."}],
      dependencies: [],
      missing_dependencies: [],
      verification: "pytest -q tests/example.py",
      evidence_links: ["run://run-1/implement/task-TL-1"],
      attempts: [],
      action_projection: {
        recommended: "run",
        core_recommended: "run",
        states: {
          run: {action: "run", eligible: true, disabled_reason: null},
          resume: {action: "resume", eligible: false, disabled_reason: "No interrupted attempt."},
          finalize: {action: "finalize", eligible: false, disabled_reason: "Every task must succeed."},
        },
        runner: {required: true, eligible: true},
      },
    },
  };
  context.taskView = taskView;
  const html = vm.runInContext("renderTaskWorkspace(taskView)", context, {filename: "operator-active-studio.js"});
  assert.match(html, /data-task-detail/);
  assert.match(html, /A reviewed implementation/);
  assert.match(html, /src\/example\.py/);
  assert.match(html, /Focused test passes\./);
  assert.match(html, /run:\/\/run-1\/implement\/task-TL-1/);
  assert.match(html, /data-task-action="run"/);
  assert.match(html, /role="table" aria-label="Dependency-aware task list"/);
  assert.match(html, /role="columnheader">Dependencies<\/span>/);
  assert.match(html, /data-task-group="Ready"/);
  assert.match(html, /data-task-status="pending"/);
  assert.equal((html.match(/data-task-action="/g) || []).length, 1);
  assert.match(html, /data-contextual-runner-control/);
  assert.doesNotMatch(html, /selectedRuntimeReady\(\)/);
});

test("Task Workspace preserves a literal service guard when Runner is unavailable", async () => {
  const context = await contextFor({
    work_item: "WI-1",
    run: {run_id: "run-1"},
    stages: [{stage: "idea", status: "succeeded"}],
  });
  const html = vm.runInContext("renderTaskWorkspace({task_list: [], selected_task: {id: 'TL-1', title: 'Blocked task', status: 'pending', action_projection: {recommended: null, core_recommended: 'run', states: {run: {action: 'run', eligible: false, disabled_reason: 'Runner authentication is not verified.'}}}}})", context, {filename: "operator-active-studio.js"});
  assert.match(html, /Runner authentication is not verified\./);
  assert.match(html, /data-task-action="run"[^>]+disabled/);
  assert.match(html, /data-action-recommended="none"/);
});

test("Task Workspace promotes the selected attempt tray and preserves factual live state", async () => {
  const context = await contextFor({
    work_item: "WI-1",
    run: {run_id: "run-1"},
    stages: [{stage: "implement", status: "executing"}],
  });
  context.state.activeJobStatus = {
    kind: "task",
    job_id: "job-task-1",
    attempt_path: ".aidd/attempts/task-TL-1/1",
    status: "running",
    elapsed_seconds: 42,
    runtime_output_age_seconds: 3,
    message: "Focused verification started",
  };
  context.state.activeJobConnection = {state: "reconnecting", failureCount: 1, retryDelayMs: 500};
  context.state.activeJobLogChunks = [{stream: "stdout", text: "pytest -q tests/example.py"}];
  context.state.activeJobCursor = 7;
  const html = vm.runInContext(`renderTaskWorkspace({
    task_list: [{id: "TL-1", title: "Implement selected task", status: "running", group: "Running", dependencies: [], attempt_count: 1}],
    next_ready_task: null,
    critical_path: ["TL-1"],
    selected_task: {
      id: "TL-1", title: "Implement selected task", status: "running", outcome: "Deliver the bounded implementation.",
      dominant_deliverable: "A reviewed implementation", scope_paths: ["src/example.py"], acceptance_criteria: [],
      dependencies: [], missing_dependencies: [], verification: "pytest -q tests/example.py", evidence_links: [], attempts: [],
      action_projection: {recommended: null, states: {}, runner: {required: false, eligible: true}},
    },
  })`, context, {filename: "operator-active-studio.js"});
  assert.match(html, /data-active-task-attempt="true"/);
  assert.match(html, /TL-1 · Implement selected task/);
  assert.match(html, /Focused verification started/);
  assert.match(html, /Last runtime output 3s ago/);
  assert.match(html, /Reconnect cursor/);
  assert.match(html, /data-task-attempt-primary[^>]*data-aidd-primary-action[^>]*>Open live output/);
  assert.match(html, /data-cancel-job="job-task-1"/);
  assert.match(html, /data-connection-state="reconnecting"/);
  assert.match(html, /pytest -q tests\/example\.py/);
  assert.doesNotMatch(html, /progress|\d+%/i);

  context.state.activeJobStatus.status = "completed";
  const terminal = vm.runInContext(`renderTaskWorkspace({
    task_list: [], selected_task: {id: "TL-1", title: "Implement selected task", status: "succeeded", attempts: [], action_projection: {recommended: null, states: {}}}
  })`, context, {filename: "operator-active-studio.js"});
  assert.match(terminal, /data-task-attempt-primary[^>]*>Open live output/);
  assert.doesNotMatch(terminal, /data-cancel-job=/);
});
