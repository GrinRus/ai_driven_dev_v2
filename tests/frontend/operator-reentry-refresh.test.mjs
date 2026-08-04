import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

function classList() {
  return {add() {}, remove() {}, toggle() {}};
}

async function load(context, filename) {
  const source = await readFile(path.join(staticRoot, filename), "utf8");
  vm.runInContext(source, context, {filename});
}

async function refreshContext({contextWorkItem, resumeFails = false}) {
  const calls = [];
  const elements = new Map();
  const element = (id) => {
    if (!elements.has(id)) {
      elements.set(id, {
        disabled: false,
        innerHTML: "",
        textContent: "",
      });
    }
    return elements.get(id);
  };
  const location = {
    pathname: "/",
    search: "?mode=studio&work_item=WI-ROUTE&stage=plan",
  };
  const window = {
    addEventListener() {},
    history: {pushState() {}, replaceState() {}},
    location,
    requestAnimationFrame() {},
    setTimeout,
  };
  const context = vm.createContext({
    URL,
    URLSearchParams,
    console,
    document: {
      addEventListener() {},
      body: {classList: classList(), dataset: {}},
      getElementById: element,
      querySelector() { return null; },
      querySelectorAll() { return []; },
    },
    history: window.history,
    location,
    setTimeout,
    window,
  });
  await load(context, "operator-route-state.js");
  await load(context, "operator-api-state.js");

  context.__calls = calls;
  context.__initialContextWorkItem = contextWorkItem;
  context.__resumeFails = resumeFails;
  vm.runInContext(`
    let onboardingFetchCount = 0;
    fetchOnboardingState = async () => {
      __calls.push({kind: "onboarding"});
      onboardingFetchCount += 1;
      state.onboarding.setupRequired = false;
      state.onboarding.projectRootInput = "/project";
      state.onboarding.contextWorkItem = onboardingFetchCount === 1
        ? __initialContextWorkItem
        : "WI-ROUTE";
    };
    postJson = async (path, payload) => {
      __calls.push({kind: "post", path, payload});
      if (__resumeFails) throw new Error("Requested work item is unavailable.");
      return {context: {work_item: "WI-ROUTE"}};
    };
    fetchDashboard = async () => {
      __calls.push({kind: "dashboard"});
      state.dashboard = {work_item: "WI-ROUTE", run: {run_id: ""}};
    };
    fetchProjectHome = async (workItem = "") => {
      __calls.push({kind: "project-home", workItem});
    };
    fetchInbox = async () => {
      __calls.push({kind: "inbox"});
    };
    renderAll = async () => {
      __calls.push({kind: "render"});
    };
    fetchReadiness = async () => {
      __calls.push({kind: "readiness"});
      return true;
    };
    renderReadinessSurfaces = () => {
      __calls.push({kind: "readiness-surfaces"});
    };
    renderOnboarding = async () => {
      __calls.push({kind: "onboarding-render"});
    };
    toast = (message) => {
      __calls.push({kind: "toast", message});
    };
    hasDirtyOperatorDraft = () => false;
    currentOperatorDraftProject = () => "project";
  `, context);

  const mainPath = path.join(staticRoot, "operator-main.js");
  const main = await readFile(mainPath, "utf8");
  vm.runInContext(main.replace(/\nrefresh\(\);\s*$/, "\n"), context, {filename: mainPath});
  await vm.runInContext("refresh()", context);
  await new Promise((resolve) => setImmediate(resolve));
  return {calls, context};
}

test("explicit Studio re-entry resumes a missing or different project context", async () => {
  for (const contextWorkItem of ["", "WI-OTHER"]) {
    const {calls, context} = await refreshContext({contextWorkItem});
    const posts = JSON.parse(JSON.stringify(calls.filter((call) => call.kind === "post")));
    assert.deepEqual(posts, [{
      kind: "post",
      path: "/api/onboarding/work-item",
      payload: {
        action: "resume",
        project_root: "/project",
        work_item: "WI-ROUTE",
      },
    }]);
    assert.equal(calls.filter((call) => call.kind === "onboarding").length, 2);
    assert.ok(calls.some((call) => call.kind === "dashboard"));
    assert.deepEqual(
      calls.filter((call) => call.kind === "project-home").map((call) => call.workItem),
      ["WI-ROUTE"],
    );
    assert.equal(vm.runInContext("state.dashboard.work_item", context), "WI-ROUTE");
    assert.deepEqual(
      JSON.parse(JSON.stringify(vm.runInContext(
        "({tab: state.activeTab, detail: state.workDetail, routeWorkItem: state.activeRouteWorkItem})",
        context,
      ))),
      {tab: "work", detail: "overview", routeWorkItem: "WI-ROUTE"},
    );
  }
});

test("failed explicit Studio re-entry falls back to the project Inbox", async () => {
  const {calls, context} = await refreshContext({
    contextWorkItem: "",
    resumeFails: true,
  });

  assert.equal(calls.filter((call) => call.kind === "post").length, 1);
  assert.equal(calls.filter((call) => call.kind === "dashboard").length, 0);
  assert.deepEqual(
    calls.filter((call) => call.kind === "project-home").map((call) => call.workItem),
    [""],
  );
  assert.equal(calls.filter((call) => call.kind === "inbox").length, 1);
  assert.equal(calls.filter((call) => call.kind === "readiness").length, 0);
  assert.equal(calls.find((call) => call.kind === "toast")?.message, "Requested work item is unavailable.");
  assert.deepEqual(
    JSON.parse(JSON.stringify(vm.runInContext(
      "({tab: state.activeTab, detail: state.workDetail, routeWorkItem: state.activeRouteWorkItem, dashboard: state.dashboard})",
      context,
    ))),
    {tab: "work", detail: "project-home", routeWorkItem: "", dashboard: null},
  );
});

test("resuming a project work item refreshes readiness after the durable render", async () => {
  const calls = [];
  const context = vm.createContext({
    console,
    document: {
      body: {classList: classList()},
      getElementById: () => ({disabled: true}),
    },
    state: {
      activeArtifactKey: "artifact",
      activeRunId: "",
      activeStage: "idea",
      onboarding: {projectRootInput: "/project", setupRequired: true},
      projectHome: {project_root: "/project"},
      selectedEvidenceEdgeId: "edge",
      selectedEvidenceNodeId: "node",
    },
    fetchDashboard: async () => calls.push("dashboard"),
    fetchInbox: async () => calls.push("inbox"),
    fetchProjectHome: async (workItem) => calls.push(`project:${workItem}`),
    fetchReadiness: async () => {
      calls.push("readiness");
      return true;
    },
    postJson: async (path, payload) => calls.push(`post:${path}:${payload.work_item}`),
    projectHomeWorkItems: () => [{
      work_item: "WI-RESUME",
      active_stage: "plan",
      latest_run: {run_id: "run-resume"},
    }],
    renderAll: async () => calls.push("render"),
    renderReadinessSurfaces: () => calls.push("readiness-surfaces"),
    setOperatorMode: (mode) => calls.push(`mode:${mode}`),
  });
  await load(context, "operator-onboarding.js");

  await vm.runInContext("resumeProjectHomeWorkItem('WI-RESUME')", context);
  await new Promise((resolve) => setImmediate(resolve));

  assert.deepEqual(calls, [
    "post:/api/onboarding/work-item:WI-RESUME",
    "mode:work",
    "dashboard",
    "project:WI-RESUME",
    "inbox",
    "render",
    "readiness",
    "readiness-surfaces",
  ]);
  assert.equal(vm.runInContext("state.activeStage", context), "plan");
  assert.equal(vm.runInContext("state.activeRunId", context), "run-resume");
  assert.equal(vm.runInContext("state.activeArtifactKey", context), "");
  assert.equal(vm.runInContext("state.selectedEvidenceNodeId", context), "");
  assert.equal(vm.runInContext("state.selectedEvidenceEdgeId", context), "");
});
