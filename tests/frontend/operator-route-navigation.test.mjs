import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

async function navigationContext(search = "") {
  const writes = [];
  const location = {pathname: "/", search};
  const write = (kind, value) => {
    const url = new URL(value, "http://operator.local");
    location.pathname = url.pathname;
    location.search = url.search;
    writes.push({kind, value});
  };
  const window = {
    location,
    history: {
      pushState: (_state, _title, value) => write("push", value),
      replaceState: (_state, _title, value) => write("replace", value),
    },
  };
  const context = vm.createContext({URL, URLSearchParams, window});
  for (const filename of ["operator-route-state.js", "operator-api-state.js"]) {
    const sourcePath = path.join(staticRoot, filename);
    vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  }
  return {context, location, writes};
}

function value(context, expression) {
  return JSON.parse(JSON.stringify(vm.runInContext(expression, context)));
}

test("reload restores selected stage, run, artifact, and logs view", async () => {
  const {context} = await navigationContext(
    "?mode=studio&view=logs&work_item=WI-001&run_id=run-1&stage=qa&artifact=runtime.log",
  );
  vm.runInContext("initializeStateFromLocation()", context);
  assert.deepEqual(value(context, `({
    tab: state.activeTab,
    detail: state.evidenceDetail,
    stage: state.activeStage,
    run: state.activeRunId,
    workItem: state.activeRouteWorkItem,
    artifact: state.activeArtifactKey
  })`), {
    tab: "evidence",
    detail: "logs",
    stage: "qa",
    run: "run-1",
    workItem: "WI-001",
    artifact: "runtime.log",
  });
});

test("Inbox route restores the project-home surface", async () => {
  const {context} = await navigationContext("?mode=inbox&ui=studio");
  vm.runInContext("initializeStateFromLocation()", context);
  assert.deepEqual(value(context, `({tab: state.activeTab, detail: state.workDetail})`), {
    tab: "work",
    detail: "project-home",
  });
});

test("bare route preserves the context-aware Studio fallback", async () => {
  const {context} = await navigationContext();
  vm.runInContext("initializeStateFromLocation()", context);
  assert.deepEqual(value(context, `({tab: state.activeTab, detail: state.workDetail})`), {
    tab: "work",
    detail: "overview",
  });
});

test("project-home navigation writes a context-free Inbox route", async () => {
  const {context, writes} = await navigationContext("?mode=studio");
  vm.runInContext(`Object.assign(state, {
    activeRunId: "run-1", activeStage: "qa", activeArtifactKey: "qa_report",
    dashboard: {work_item: "WI-001"}
  })`, context);
  vm.runInContext("setOperatorMode('project-home'); syncLocationState({historyMode: 'push'})", context);
  assert.equal(writes[0].kind, "push");
  assert.equal(writes[0].value, "/?mode=inbox");
});

test("navigation writes explicit transitions and replaces derived state", async () => {
  const {context, writes} = await navigationContext("?mode=inbox");
  vm.runInContext(`applyOperatorRoute({
    mode: "studio", view: "artifacts", workItem: "WI-001", runId: "run-1",
    stage: "implement", attempt: 2, taskAttempt: null, artifact: "task-diff.json"
  })`, context);
  vm.runInContext("syncLocationState({historyMode: 'push'})", context);
  vm.runInContext("state.activeStage = 'review'; syncLocationState()", context);
  assert.equal(writes[0].kind, "push");
  assert.match(writes[0].value, /view=artifacts/);
  assert.match(writes[0].value, /artifact=task-diff.json/);
  assert.equal(writes[1].kind, "replace");
  assert.match(writes[1].value, /stage=review/);
});

test("retired presentation query is removed from canonical navigation", async () => {
  const {context, writes} = await navigationContext("?ui=legacy&mode=studio");
  vm.runInContext(`applyOperatorRoute({
    mode: "studio", view: "artifacts", workItem: "WI-001", runId: "run-1",
    stage: "qa", attempt: null, taskAttempt: null, artifact: "qa_report"
  })`, context);
  vm.runInContext("syncLocationState({historyMode: 'push'})", context);
  assert.equal(writes[0].kind, "push");
  assert.doesNotMatch(writes[0].value, /ui=/);
  assert.match(writes[0].value, /artifact=qa_report/);
});

test("main wiring restores browser history through the read-only route path", async () => {
  const source = await readFile(path.join(staticRoot, "operator-main.js"), "utf8");
  assert.match(source, /addEventListener\("popstate"/);
  assert.match(source, /restoreOperatorRouteFromLocation\(\)/);
});
