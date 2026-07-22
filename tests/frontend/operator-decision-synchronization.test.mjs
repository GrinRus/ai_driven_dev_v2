import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

async function load(context, filename) {
  const source = await readFile(path.join(staticRoot, filename), "utf8");
  vm.runInContext(source, context, {filename});
}

function deferred() {
  let resolve;
  const promise = new Promise((resolver) => {
    resolve = resolver;
  });
  return {promise, resolve};
}

function response(payload) {
  return {ok: true, status: 200, statusText: "OK", json: async () => payload};
}

test("late readiness responses are ignored by the shared generation", async () => {
  const first = deferred();
  const second = deferred();
  const requests = [first, second];
  const toast = {textContent: "", classList: {add() {}, remove() {}}};
  const context = vm.createContext({
    AbortController,
    URLSearchParams,
    clearTimeout,
    console,
    document: {getElementById: () => toast},
    fetch: async () => (await requests.shift().promise),
    setTimeout,
    window: {clearTimeout, setTimeout},
  });
  await load(context, "operator-api-state.js");

  const older = vm.runInContext("fetchReadiness()", context);
  const newer = vm.runInContext("fetchReadiness()", context);
  second.resolve(response({runtimes: [{runtime_id: "newer"}]}));
  assert.equal(await newer, true);
  first.resolve(response({runtimes: [{runtime_id: "older"}]}));
  assert.equal(await older, false);

  assert.equal(vm.runInContext("state.readiness.runtimes[0].runtime_id", context), "newer");
  assert.equal(vm.runInContext("state.readinessLoading", context), false);
});

test("readiness rendering updates only readiness-owned surfaces", async () => {
  const calls = [];
  const readinessSurface = {outerHTML: "old"};
  const context = vm.createContext({
    console,
    document: {
      querySelector: (selector) => selector === "[data-studio-runtime-readiness]"
        ? readinessSurface
        : null,
    },
    state: {},
  });
  await load(context, "operator-stage-cockpit.js");
  Object.assign(context, {
    renderRuntimeSelector: () => calls.push("runtime-selector"),
    renderTopbar: () => calls.push("topbar"),
    renderSafetyPanel: () => calls.push("safety"),
    renderActiveStudioRuntimeReadiness: () => {
      calls.push("studio-readiness");
      return "new-readiness";
    },
    updateSubmitInterventionState: () => calls.push("intervention-state"),
    renderAll: () => calls.push("full-render"),
    renderCockpit: () => calls.push("cockpit-render"),
  });

  vm.runInContext("renderReadinessSurfaces()", context);

  assert.deepEqual(calls, [
    "runtime-selector",
    "topbar",
    "safety",
    "studio-readiness",
    "intervention-state",
  ]);
  assert.equal(readinessSurface.outerHTML, "new-readiness");
});

test("Flow Complete disclosure survives a render of the same durable handoff", async () => {
  const context = vm.createContext({
    AbortController,
    URLSearchParams,
    clearTimeout,
    console,
    document: {getElementById: () => ({classList: {add() {}, remove() {}}, textContent: ""})},
    setTimeout,
    window: {clearTimeout, setTimeout},
  });
  await load(context, "operator-api-state.js");
  await load(context, "operator-mutation-guard.js");
  await load(context, "operator-next-flow-actions.js");
  await load(context, "operator-next-flow-view.js");
  vm.runInContext(`
    state.activeRunId = "run-1";
    state.dashboard = {
      work_item: "WI-1",
      run: {run_id: "run-1"},
      terminal_handoff: {
        status: "completed",
        final_qa_status: "ready",
        final_artifacts: [],
        blockers: [],
        recommended_outcome: "create-new-work-item",
        recommendation_rationale: "QA is clean.",
        recommended_next_flow_actions: [
          {action: "create-new-work-item", label: "Create New Work Item", enabled: true},
          {action: "archive-run", label: "Archive Run", enabled: true}
        ]
      }
    };
    rememberStudioFlowCompleteDisclosure({open: true, matches: () => true});
  `, context);

  assert.match(vm.runInContext("renderStudioFlowCompleteState()", context), /studio-flow-complete-other" open/);
  vm.runInContext("state.activeRunId = 'run-2'", context);
  assert.doesNotMatch(vm.runInContext("renderStudioFlowCompleteState()", context), /studio-flow-complete-other" open/);
});

test("duplicate Archive activation commits one POST and one winner render", async () => {
  const release = deferred();
  const posts = [];
  const renders = [];
  const dashboard = {
    work_item: "WI-1",
    run: {run_id: "run-1", archive: {archived: true}},
    terminal_handoff: {status: "completed"},
  };
  const context = vm.createContext({
    URLSearchParams,
    console,
    document: {querySelectorAll: () => []},
    state: {
      activeRunId: "run-1",
      activeRouteWorkItem: "WI-1",
      dashboard: {work_item: "WI-1", run: {run_id: "run-1"}, terminal_handoff: {status: "completed"}},
      nextFlowWizard: {
        active: true,
        action: "archive-run",
        step: "archive-confirm",
        archiveRunId: "run-1",
        archiveReason: "Archive once",
      },
    },
    postJson: async (url, payload) => {
      posts.push({url, payload});
      await release.promise;
      return {dashboard, archive: dashboard.run.archive};
    },
    api: async () => ({dashboard}),
    renderAll: async () => renders.push("render"),
    setMutationControlsPending: () => {},
    toast: () => {},
  });
  await load(context, "operator-mutation-guard.js");
  await load(context, "operator-next-flow-actions.js");

  const pending = vm.runInContext("Promise.all([archiveCompletedRun(), archiveCompletedRun()])", context);
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(posts.length, 1);
  assert.equal(vm.runInContext("archiveMutationState().status", context), "pending");
  release.resolve();
  await pending;

  assert.deepEqual(JSON.parse(JSON.stringify(posts)), [{
    url: "/api/next-flow/archive",
    payload: {
      source_work_item: "WI-1",
      source_run_id: "run-1",
      reason: "Archive once",
    },
  }]);
  assert.deepEqual(renders, ["render"]);
  assert.equal(vm.runInContext("state.nextFlowWizard.active", context), false);

  vm.runInContext(`
    state.nextFlowWizard.active = true;
    state.nextFlowWizard.archiveIntentId = "second-intent";
  `, context);
  await vm.runInContext("archiveCompletedRun()", context);
  assert.equal(posts.length, 2);
  assert.deepEqual(renders, ["render", "render"]);
});

test("archive presentation failure retries rendering without a second durable POST", async () => {
  const posts = [];
  let renderAttempts = 0;
  const dashboard = {
    work_item: "WI-1",
    run: {run_id: "run-1", archive: {archived: true}},
    terminal_handoff: {status: "completed"},
  };
  const context = vm.createContext({
    URLSearchParams,
    console,
    document: {querySelectorAll: () => []},
    state: {
      activeRunId: "run-1",
      activeRouteWorkItem: "WI-1",
      dashboard: {work_item: "WI-1", run: {run_id: "run-1"}, terminal_handoff: {status: "completed"}},
      nextFlowWizard: {active: true, action: "archive-run", step: "archive-confirm", archiveReason: "Archive once"},
    },
    postJson: async (url, payload) => {
      posts.push({url, payload});
      return {dashboard, archive: dashboard.run.archive};
    },
    api: async () => ({dashboard}),
    renderAll: async () => {
      renderAttempts += 1;
      if (renderAttempts === 1) throw new Error("render failed after commit");
    },
    setMutationControlsPending: () => {},
    toast: () => {},
  });
  await load(context, "operator-mutation-guard.js");
  await load(context, "operator-next-flow-actions.js");

  await assert.rejects(vm.runInContext("archiveCompletedRun()", context), /render failed after commit/);
  assert.equal(vm.runInContext("archiveMutationState().status", context), "succeeded");
  await vm.runInContext("archiveCompletedRun()", context);

  assert.equal(posts.length, 1);
  assert.equal(renderAttempts, 2);
});

async function interventionContext({conflict = false, priorRequestId = "", postBarrier = null} = {}) {
  const posts = [];
  const cleared = [];
  const textarea = {value: "Keep this exact intervention request"};
  const button = {dataset: {interventionEligible: "true"}, disabled: false};
  const note = {textContent: "", hidden: true};
  const target = {dataset: {interventionTarget: "plan.md"}};
  let draftRecord = {
    value: {text: textarea.value, targetDocuments: ["plan.md"]},
  };
  const context = vm.createContext({
    URLSearchParams,
    console,
    document: {
      getElementById: (id) => ({
        operatorRequestText: textarea,
        submitInterventionButton: button,
        interventionReadinessNote: note,
      })[id] || null,
      querySelector: () => null,
      querySelectorAll: (selector) => selector === "[data-intervention-target]:checked" ? [target] : [],
    },
    state: {
      activeRunId: "run-1",
      activeRouteWorkItem: "WI-1",
      activeStage: "plan",
      selectedRuntime: "generic-cli",
      dashboard: {work_item: "WI-1", run: {run_id: "run-1"}},
    },
    activeStageView: () => ({diagnostics: {request_change: {
      eligible: true,
      latest_request_id: priorRequestId || null,
    }}}),
    api: async () => ({
      dashboard: conflict ? {
        work_item: "WI-1",
        run: {run_id: "run-1"},
        active_stage: "plan",
        active_stage_view: {stage: "plan", diagnostics: {request_change: {}}},
      } : {
        work_item: "WI-1",
        run: {run_id: "run-1"},
        active_stage: "plan",
        active_stage_view: {
          stage: "plan",
          diagnostics: {request_change: {
            latest_request_id: priorRequestId || "request-1",
            latest_request_path: ".aidd/workitems/WI-1/stages/plan/operator-requests/request-1.md",
            latest_request_excerpt: posts[0]?.payload.request || textarea.value,
          }},
        },
      },
    }),
    readOperatorDraft: () => draftRecord,
    clearOperatorDraft: (identity) => {
      cleared.push(identity);
      draftRecord = null;
      return true;
    },
    ensureRunnableRuntime: () => true,
    operatorDraftIdentity: () => ({form: "intervention", run: "run-1", stage: "plan"}),
    runtimeReadinessMessage: () => "",
    setMutationControlsPending: () => {},
    startJobPolling: async () => {},
    toast: () => {},
    postJson: async (url, payload) => {
      posts.push({url, payload});
      if (postBarrier) await postBarrier.promise;
      if (conflict) {
        const error = new Error("another request won");
        error.status = 409;
        throw error;
      }
      return {job_id: "job-1", kind: "intervention", stage: "plan"};
    },
    window: {setTimeout},
    __posts: posts,
    __cleared: cleared,
    __textarea: textarea,
    __button: button,
    __setDraft: (value) => { draftRecord = {value}; },
  });
  await load(context, "operator-mutation-guard.js");
  await load(context, "operator-approvals-interventions.js");
  return context;
}

test("duplicate intervention activation uses one immutable payload and clears after matching readback", async () => {
  const context = await interventionContext();
  await vm.runInContext("Promise.all([submitIntervention(), submitIntervention()])", context);

  assert.equal(context.__posts.length, 1);
  assert.deepEqual(JSON.parse(JSON.stringify(context.__posts[0])), {
    url: "/api/stage/interact",
    payload: {
      stage: "plan",
      runtime: "generic-cli",
      request: "Keep this exact intervention request",
      target_documents: ["plan.md"],
      log_follow: true,
      run_id: "run-1",
    },
  });
  assert.equal(context.__cleared.length, 1);
});

test("unrelated intervention conflict retains the browser draft", async () => {
  const context = await interventionContext({conflict: true});
  assert.equal(await vm.runInContext("submitIntervention()", context), null);
  assert.equal(context.__posts.length, 1);
  assert.equal(context.__cleared.length, 0);
});

test("pre-existing matching intervention cannot satisfy a newly accepted action", async () => {
  const context = await interventionContext({priorRequestId: "request-1"});
  assert.notEqual(await vm.runInContext("submitIntervention()", context), null);
  assert.notEqual(await vm.runInContext("submitIntervention()", context), null);
  assert.equal(context.__posts.length, 1);
  assert.equal(context.__cleared.length, 0);
});

test("pending readiness updates stay disabled and accepted work preserves a newer draft", async () => {
  const release = deferred();
  const context = await interventionContext({postBarrier: release});
  const pending = vm.runInContext("submitIntervention()", context);
  await new Promise((resolve) => setImmediate(resolve));

  vm.runInContext("updateSubmitInterventionState()", context);
  assert.equal(context.__button.disabled, true);
  context.__textarea.value = "A newer intervention draft";
  context.__setDraft({text: context.__textarea.value, targetDocuments: ["plan.md"]});
  vm.runInContext("updateSubmitInterventionState()", context);
  assert.equal(context.__button.disabled, true);

  release.resolve();
  await pending;
  assert.equal(context.__posts.length, 1);
  assert.equal(context.__cleared.length, 0);
});
