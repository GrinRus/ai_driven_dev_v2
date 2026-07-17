import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
  };
}

async function launchContext({failLaunch = false} = {}) {
  const storage = memoryStorage();
  const posts = [];
  const polls = [];
  const preflights = [];
  const context = vm.createContext({
    TextEncoder,
    window: {sessionStorage: storage},
    document: {querySelector: () => null, querySelectorAll: () => []},
    state: {
      activeRunId: "run-source",
      selectedRuntime: "generic-cli",
      dashboard: {
        project_root: "/project",
        work_item: "WI-SOURCE",
        run: {run_id: "run-source", runtime_id: "generic-cli", lineage: {}},
      },
      nextFlowWizard: {
        active: true,
        action: "clone-flow",
        step: "confirm",
        followUpDraft: {
          source_work_item: "WI-SOURCE",
          source_run_id: "run-source",
          new_work_item: "WI-CLONE",
          title: "Clone source",
          acceptance_criteria: ["Preserve behavior"],
          required_evidence: ["pytest"],
          inherited_context: [],
        },
        selectedSourceIds: [],
        preflight: {resolved_baseline_id: "run-source"},
        launchLoading: false,
        launchError: "",
      },
    },
    operatorDraftIdentity: (form, sourceId) => ({
      project: "/project", workItem: "WI-SOURCE", run: "run-source", stage: "qa", form, sourceId,
    }),
    renderNextFlowWizardStep: async () => {},
    fetchReadiness: async () => {},
    renderRuntimeSelector: () => {},
    renderTopbar: () => {},
    renderSidebar: () => {},
    runtimeReadinessMessage: () => "",
    toast: () => {},
    api: async () => ({job_id: "job-launch", status: "running"}),
    setMutationControlsPending: () => {},
    startJobPolling: async (job) => polls.push(job.job_id),
    postJson: async (url) => {
      posts.push(url);
      if (url === "/api/next-flow/launch" && failLaunch) throw new Error("launch failed");
      return {job_id: "job-launch"};
    },
    fetch: async (url) => {
      preflights.push(url);
      return {
        ok: true,
        json: async () => ({preflight: {status: "pass", can_launch: true, checks: []}}),
      };
    },
    __posts: posts,
    __polls: polls,
    __preflights: preflights,
  });
  for (const filename of [
    "operator-draft-store.js",
    "operator-mutation-guard.js",
    "operator-next-flow-actions.js",
  ]) {
    const sourcePath = path.join(staticRoot, filename);
    vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  }
  vm.runInContext("refreshRuntimeReadinessForLaunch = async () => true", context);
  vm.runInContext("renderNextFlowWizardStep = async () => {}", context);
  vm.runInContext("persistNextFlowBrowserDraft()", context);
  return context;
}

test("confirmed next-flow launch clears only its owning browser draft", async () => {
  const context = await launchContext();
  assert.equal(vm.runInContext("Object.keys(loadOperatorDraftBucket().entries).length", context), 1);
  await vm.runInContext("Promise.all([launchNextFlowNow(), launchNextFlowNow()])", context);
  assert.equal(vm.runInContext("Object.keys(loadOperatorDraftBucket().entries).length", context), 0);
  assert.equal(context.__posts.filter((url) => url === "/api/next-flow/launch").length, 1);
  assert.deepEqual(context.__polls, ["job-launch"]);
});

test("failed next-flow launch retains its browser draft for retry", async () => {
  const context = await launchContext({failLaunch: true});
  await vm.runInContext("launchNextFlowNow()", context);
  assert.equal(vm.runInContext("Object.keys(loadOperatorDraftBucket().entries).length", context), 1);
  assert.equal(vm.runInContext("state.nextFlowWizard.launchError", context), "launch failed");
});

test("repeated next-flow preflight shares one request", async () => {
  const context = await launchContext();
  await vm.runInContext("Promise.all([loadLaunchConfirmation(), loadLaunchConfirmation()])", context);
  assert.deepEqual(context.__preflights, ["/api/next-flow/preflight"]);
});
