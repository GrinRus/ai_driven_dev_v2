import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-quality-gates.js");
const dashboardActionsPath = path.join(repositoryRoot, "src/aidd/cli/static/operator-dashboard-actions.js");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>\"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;",
  })[character]);
}

async function recoveryContext() {
  const context = vm.createContext({
    console,
    state: {selectedRuntime: "codex"},
    escapeHtml,
    selectedRuntimeReady() { return true; },
    renderContextualRunnerControl({actionLabel, inspector}) {
      return `<div data-contextual-runner-control data-inspector="${Boolean(inspector)}">${actionLabel}</div>`;
    },
  });
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return context;
}

function failedTaskView() {
  return {
    next_ready_task: "TL-2",
    finalization_eligible: false,
    finalization: {status: "pending"},
    tasks: [{
      id: "TL-1",
      status: "succeeded",
      ready: false,
      action_projection: {states: {run: {eligible: false}, resume: {eligible: false}}},
    }, {
      id: "TL-2",
      status: "failed",
      ready: true,
      action_projection: {
        recommended: "resume",
        states: {
          run: {eligible: false},
          resume: {eligible: true},
        },
      },
    }],
  };
}

test("implementation recovery targets the failed task instead of aggregate stage run", async () => {
  const context = await recoveryContext();
  context.taskView = failedTaskView();
  const recovered = vm.runInContext("implementationRecoveryTarget(taskView)", context);
  assert.deepEqual(JSON.parse(JSON.stringify(recovered)), {
    kind: "task",
    taskId: "TL-2",
    action: "resume",
    label: "Resume TL-2",
  });
  const html = vm.runInContext("renderStudioImplementationQualityGate(taskView)", context);
  assert.match(html, /data-run-task="TL-2"/);
  assert.match(html, />Resume<\/button>/);
  assert.match(html, /data-inspector="true"/);
});

test("implementation recovery targets failed finalization after all tasks succeed", async () => {
  const context = await recoveryContext();
  context.taskView = {
    next_ready_task: null,
    finalization_eligible: true,
    finalization: {status: "failed"},
    tasks: [{
      id: "TL-1",
      status: "succeeded",
      ready: false,
      action_projection: {states: {run: {eligible: false}, resume: {eligible: false}}},
    }],
  };
  const recovered = vm.runInContext("implementationRecoveryTarget(taskView)", context);
  assert.deepEqual(JSON.parse(JSON.stringify(recovered)), {
    kind: "finalization",
    label: "Resume finalization",
  });
});

test("resume action dispatches to the canonical task endpoint instead of aggregate stage run", async () => {
  const context = vm.createContext({
    console,
    URLSearchParams,
    state: {activeRunId: "run-1", activeStage: "implement"},
    api: async (url) => {
      assert.equal(url, "/api/tasks?run_id=run-1&stage=implement");
      return failedTaskView();
    },
    runScopedQuery(stage) {
      return new URLSearchParams({run_id: "run-1", stage}).toString();
    },
    implementationRecoveryTarget(view) {
      return view.tasks.some((task) => task.id === "TL-2")
        ? {kind: "task", taskId: "TL-2"}
        : null;
    },
    startImplementationTask(taskId) {
      context.startedTask = taskId;
    },
    startTaskFinalization() {
      context.finalized = true;
    },
    startStage() {
      context.aggregateStageRun = true;
    },
    toast() {},
  });
  vm.runInContext(await readFile(dashboardActionsPath, "utf8"), context, {
    filename: dashboardActionsPath,
  });
  context.ensureRunnableRuntime = () => true;
  context.startImplementationTask = (taskId) => {
    context.startedTask = taskId;
  };
  context.startTaskFinalization = () => {
    context.finalized = true;
  };
  context.startStage = () => {
    context.aggregateStageRun = true;
  };
  await vm.runInContext("resumeStageOrImplementationTarget('implement')", context);
  assert.equal(context.startedTask, "TL-2");
  assert.equal(context.aggregateStageRun, undefined);
});

test("late implementation recovery targets are discarded after the run changes", async () => {
  let resolveTaskView;
  let startedTask = "";
  const context = vm.createContext({
    console,
    URLSearchParams,
    state: {
      activeRunId: "run-1",
      activeStage: "implement",
      activeRouteWorkItem: "WI-1",
      dashboard: {work_item: "WI-1"},
    },
    api: () => new Promise((resolve) => { resolveTaskView = resolve; }),
    runScopedQuery(stage) {
      return new URLSearchParams({run_id: context.state.activeRunId, stage}).toString();
    },
    implementationRecoveryTarget: () => ({kind: "task", taskId: "TL-2"}),
    startImplementationTask(taskId) { startedTask = taskId; },
    startTaskFinalization() {},
    startStage() {},
    toast() {},
  });
  vm.runInContext(await readFile(dashboardActionsPath, "utf8"), context, {
    filename: dashboardActionsPath,
  });
  context.ensureRunnableRuntime = () => true;

  const recovery = vm.runInContext("resumeStageOrImplementationTarget('implement')", context);
  context.state.activeRunId = "run-2";
  context.state.activeRouteWorkItem = "WI-2";
  context.state.dashboard.work_item = "WI-2";
  resolveTaskView(failedTaskView());
  await recovery;

  assert.equal(startedTask, "");
});
