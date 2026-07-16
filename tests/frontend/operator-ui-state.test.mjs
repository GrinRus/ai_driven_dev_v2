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
    "/operator-api-state.js",
    "/operator-shell-rendering.js",
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

test("late dashboard response cannot overwrite a newer request", async () => {
  const {context} = domContext();
  const requests = [];
  context.fetch = (url) => {
    const pending = deferred();
    requests.push({url, pending});
    return pending.promise;
  };
  await load(context, "operator-api-state.js");

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
