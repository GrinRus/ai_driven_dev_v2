import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

function classList() {
  return {
    add() {},
    contains() { return false; },
    remove() {},
    toggle() {},
  };
}

function domContext() {
  const elements = new Map();
  const element = (id) => {
    if (!elements.has(id)) {
      elements.set(id, {
        id,
        textContent: "",
        innerHTML: "",
        disabled: false,
        dataset: {},
        classList: classList(),
        setAttribute() {},
      });
    }
    return elements.get(id);
  };
  const context = vm.createContext({
    AbortController,
    URLSearchParams,
    clearInterval,
    clearTimeout,
    console,
    document: {
      body: {classList: classList(), dataset: {}},
      getElementById: element,
      querySelector() { return null; },
      querySelectorAll() { return []; },
    },
    encodeURIComponent,
    fetch: async () => {
      throw new Error("fetch double was not configured");
    },
    history: {replaceState() {}},
    location: {pathname: "/", search: ""},
    renderActivityTable() {},
    renderActiveRunPanel() {},
    renderAll: async () => {},
    renderApprovals: async () => {},
    renderNextActionPanel() {},
    setInterval,
    setTimeout,
    window: {
      clearTimeout,
      history: {replaceState() {}},
      location: {pathname: "/", search: ""},
      matchMedia: () => ({matches: false}),
      requestAnimationFrame() {},
      scrollTo() {},
      setTimeout,
      scrollY: 0,
    },
  });
  return {context, element};
}

async function load(context, filename) {
  const source = await readFile(path.join(staticRoot, filename), "utf8");
  vm.runInContext(source, context, {filename});
}

function response(payload, {ok = true, statusText = "OK"} = {}) {
  return {
    ok,
    statusText,
    async json() {
      return payload;
    },
  };
}

function deferred() {
  let resolve;
  const promise = new Promise((resolver) => {
    resolve = resolver;
  });
  return {promise, resolve};
}

test("operator bootstrap loads modules in declared order", async () => {
  const appended = [];
  const context = vm.createContext({
    console,
    document: {
      createElement() {
        return {src: "", async: true, onload: null, onerror: null};
      },
      head: {
        appendChild(script) {
          appended.push(script.src);
          script.onload();
        },
      },
    },
  });

  await load(context, "operator.js");

  assert.deepEqual(appended, [
    "/operator-surface-parity.js",
    "/operator-presentation.js",
    "/operator-api-state.js",
    "/operator-shell-rendering.js",
    "/operator-dashboard-actions.js",
    "/operator-primitives.js",
    "/operator-focus.js",
    "/operator-onboarding.js",
    "/operator-artifacts-documents.js",
    "/operator-questions.js",
    "/operator-approvals-interventions.js",
    "/operator-logs-jobs.js",
    "/operator-next-flow-actions.js",
    "/operator-next-flow-view.js",
    "/operator-control-center.js",
    "/operator-stage-cockpit.js",
    "/operator-main.js",
  ]);
});

test("surface parity manifest has one owner and journey per migration surface", async () => {
  const context = vm.createContext({console});
  await load(context, "operator-surface-parity.js");
  const entries = JSON.parse(JSON.stringify(vm.runInContext(
    "SURFACE_PARITY_MANIFEST.map((entry) => ({...entry}))",
    context,
  )));
  assert.equal(entries.length, 12);
  assert.equal(new Set(entries.map((entry) => entry.id)).size, entries.length);
  assert.deepEqual(entries.map((entry) => entry.journey).sort(), [
    "W36-E7-S1-T1",
    "W36-E7-S1-T10",
    "W36-E7-S1-T11",
    "W36-E7-S1-T12",
    "W36-E7-S1-T2",
    "W36-E7-S1-T3",
    "W36-E7-S1-T4",
    "W36-E7-S1-T5",
    "W36-E7-S1-T6",
    "W36-E7-S1-T7",
    "W36-E7-S1-T8",
    "W36-E7-S1-T9",
  ]);
  assert.ok(entries.every((entry) => entry.rollout === "legacy_only"));
  assert.ok(entries.every((entry) => entry.owner.startsWith("W36-")));
  assert.ok(entries.every((entry) => entry.rollbackRenderer.startsWith("operator-")));
  assert.ok(entries.every((entry) => entry.fixture));
  assert.ok(entries.every((entry) => entry.removalGate.startsWith("W36-")));
});

test("presentation selector is browser-only and fails back to legacy", async () => {
  const cases = [
    {search: "", requested: "legacy", fallback: false},
    {search: "?ui=legacy", requested: "legacy", fallback: false},
    {search: "?ui=studio", requested: "studio", fallback: true},
    {search: "?ui=unknown", requested: "legacy", fallback: false},
  ];
  for (const item of cases) {
    const documentElement = {dataset: {}};
    const window = {location: {search: item.search}};
    const context = vm.createContext({
      URLSearchParams,
      document: {documentElement},
      window,
    });
    await load(context, "operator-surface-parity.js");
    await load(context, "operator-presentation.js");
    assert.equal(window.aiddPresentation.requested, item.requested);
    assert.equal(window.aiddPresentation.effective, "legacy");
    assert.equal(window.aiddPresentation.fallback, item.fallback);
    assert.equal(Object.keys(window.aiddPresentation.surfaces).length, 12);
    assert.ok(Object.values(window.aiddPresentation.surfaces).every(
      (resolution) => resolution.presentation === "legacy",
    ));
    assert.equal(documentElement.dataset.presentationRequested, item.requested);
    assert.equal(documentElement.dataset.presentationEffective, "legacy");
  }
});

test("surface resolver implements selector and rollout truth table", async () => {
  const documentElement = {dataset: {}};
  const window = {location: {search: ""}};
  const context = vm.createContext({
    URLSearchParams,
    document: {documentElement},
    window,
  });
  await load(context, "operator-surface-parity.js");
  await load(context, "operator-presentation.js");
  const result = JSON.parse(JSON.stringify(vm.runInContext(
    `
      ["legacy_only", "candidate", "parity_closed"].flatMap((rollout) =>
        ["legacy", "studio", "missing", "invalid"].map((selector) => {
          const value = selector === "missing" ? "" : selector === "invalid" ? "other" : selector;
          const resolution = resolveSurfaceRendererFor({
            id: "fixture",
            rollout,
            rollbackRenderer: "operator-legacy"
          }, value);
          return {rollout, selector, ...resolution};
        })
      )
    `,
    context,
  )));
  for (const item of result) {
    const studio = item.selector === "studio" && item.rollout !== "legacy_only";
    assert.equal(item.presentation, studio ? "studio" : "legacy");
    assert.equal(item.renderer, studio ? "studio:fixture" : "operator-legacy");
    assert.equal(item.fallback, item.selector === "studio" && !studio);
  }
});

test("late dashboard response cannot overwrite a newer request", async () => {
  const {context} = domContext();
  const requests = [];
  context.fetch = (url) => {
    const pending = deferred();
    requests.push({url, pending});
    return pending.promise;
  };
  await load(context, "operator-api-state.js");
  await load(context, "operator-dashboard-actions.js");

  const first = vm.runInContext("fetchDashboard()", context);
  const second = vm.runInContext("fetchDashboard()", context);
  assert.equal(requests.length, 2);

  requests[1].pending.resolve(response({
    app_version: "new",
    active_job: null,
    dashboard: {marker: "new", stages: [], next_action: {}},
  }));
  await second;
  requests[0].pending.resolve(response({
    app_version: "old",
    active_job: null,
    dashboard: {marker: "old", stages: [], next_action: {}},
  }));
  await first;

  assert.equal(vm.runInContext("state.dashboard.marker", context), "new");
});

test("shared dashboard actions preserve workflow and stage request payloads", async () => {
  const {context} = domContext();
  const requests = [];
  const jobs = [];
  context.fetch = async (url, options = {}) => {
    requests.push({url, options});
    return response({job_id: `job-${requests.length}`, status: "running"});
  };
  context.startJobPolling = async (job) => jobs.push(job);
  await load(context, "operator-api-state.js");
  await load(context, "operator-shell-rendering.js");
  await load(context, "operator-dashboard-actions.js");
  vm.runInContext(
    `
      state.onboarding.setupRequired = false;
      state.dashboard = {work_item: "WI-UI"};
      state.activeRunId = "run-ui";
      state.activeStage = "plan";
      state.selectedRuntime = "generic-cli";
      state.readinessLoading = false;
      state.readiness = {runtimes: [{
        runtime_id: "generic-cli",
        provider_available: true,
        execution_command_available: true
      }]};
    `,
    context,
  );

  await vm.runInContext("startWorkflow()", context);
  await vm.runInContext("startStage()", context);

  assert.deepEqual(requests.map(({url, options}) => ({
    url,
    method: options.method,
    body: JSON.parse(options.body),
  })), [
    {
      url: "/api/workflow/run",
      method: "POST",
      body: {runtime: "generic-cli", log_follow: true, run_id: "run-ui"},
    },
    {
      url: "/api/stage/run",
      method: "POST",
      body: {stage: "plan", runtime: "generic-cli", log_follow: true, run_id: "run-ui"},
    },
  ]);
  assert.deepEqual(jobs, [
    {job_id: "job-1", status: "running"},
    {job_id: "job-2", status: "running"},
  ]);
});

test("cancellation invalidates an in-flight job poll", async () => {
  const {context} = domContext();
  const requests = [];
  context.fetch = (url) => {
    const pending = deferred();
    requests.push({url, pending});
    return pending.promise;
  };
  await load(context, "operator-api-state.js");
  await load(context, "operator-logs-jobs.js");
  vm.runInContext(
    "state.activeJobId = 'job-1'; state.activeJobStatus = {status: 'running'};",
    context,
  );

  const poll = vm.runInContext("pollActiveJob()", context);
  const cancel = vm.runInContext("cancelActiveJob()", context);
  assert.match(requests[0].url, /\/logs\?cursor=0$/);
  assert.match(requests[1].url, /\/cancel$/);

  requests[1].pending.resolve(response({job_id: "job-1", status: "cancelled"}));
  await cancel;
  requests[0].pending.resolve(response({cursor: 4, chunks: [{text: "late"}]}));
  await poll;

  assert.equal(vm.runInContext("state.activeJobStatus.status", context), "cancelled");
  assert.equal(vm.runInContext("state.activeJobCursor", context), 0);
  assert.equal(requests.length, 2);
});

test("rejected log request renders a deterministic escaped error", async () => {
  const {context, element} = domContext();
  context.fetch = async () => {
    throw new Error("<offline>");
  };
  await load(context, "operator-api-state.js");
  await load(context, "operator-logs-jobs.js");
  vm.runInContext(
    "state.dashboard = {stages: [{stage: 'idea', attempt_count: 1}]};",
    context,
  );

  await vm.runInContext("renderLogs()", context);

  assert.match(element("cockpitContent").innerHTML, /&lt;offline&gt;/);
  assert.doesNotMatch(element("cockpitContent").innerHTML, /<offline>/);
});

test("next-flow view renders terminal and readiness states without network mutations", async () => {
  const {context, element} = domContext();
  let fetchCount = 0;
  context.fetch = async () => {
    fetchCount += 1;
    throw new Error("view must not fetch");
  };
  await load(context, "operator-api-state.js");
  await load(context, "operator-shell-rendering.js");
  await load(context, "operator-next-flow-actions.js");
  await load(context, "operator-next-flow-view.js");
  vm.runInContext(
    `
      state.selectedRuntime = "generic-cli";
      state.readinessLoading = false;
      state.readiness = {
        runtimes: [{
          runtime_id: "generic-cli",
          provider_available: true,
          execution_command_available: true
        }]
      };
      state.dashboard = {
        work_item: "WI-UI",
        active_stage: "qa",
        run: {run_id: "run-ui", runtime_id: "generic-cli", lineage: {}},
        stages: [],
        blockers: [],
        next_action: {
          action: "open-terminal-handoff",
          label: "Review handoff",
          detail: "Review terminal evidence.",
          stage: "qa",
          enabled: true
        },
        terminal_handoff: {
          status: "completed",
          final_qa_status: "ready",
          final_artifacts: [],
          blockers: [],
          repair_counts: {attempts: 0, succeeded: 0, failed: 0},
          repair_highlights: [],
          approval_counts: {requested: 0, approved: 0, denied: 0, cancelled: 0, pending: 0},
          questions_answered_count: 0,
          questions_total_count: 0,
          recommended_next_flow_actions: []
        }
      };
      renderNextActionPanel();
    `,
    context,
  );

  const terminalHtml = vm.runInContext("renderFlowCompleteState()", context);

  assert.match(terminalHtml, /Flow Complete/);
  assert.match(terminalHtml, /QA terminal handoff/);
  assert.match(element("nextActionPanel").innerHTML, /Review handoff/);
  assert.equal(fetchCount, 0);
});
