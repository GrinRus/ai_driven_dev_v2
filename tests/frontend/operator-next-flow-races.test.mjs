import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

function deferred() {
  let resolve;
  const promise = new Promise((resolver) => {
    resolve = resolver;
  });
  return {promise, resolve};
}

async function load(context, filename) {
  const source = await readFile(path.join(staticRoot, filename), "utf8");
  vm.runInContext(source, context, {filename});
}

test("late run comparison cannot replace a newer run or leave its loading state stuck", async () => {
  const pending = deferred();
  const panel = {outerHTML: ""};
  const context = vm.createContext({
    URLSearchParams,
    console,
    document: {
      getElementById(id) {
        return id === "runComparisonPanel" ? panel : null;
      },
    },
    fetch: async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      async json() {
        return pending.promise;
      },
    }),
    renderActiveRunComparisonPanel() {
      return "<div data-comparison-panel></div>";
    },
  });
  await load(context, "operator-api-state.js");
  await load(context, "operator-next-flow-actions.js");
  vm.runInContext(`
    state.activeRunId = "run-old";
    state.dashboard = {
      run: {run_id: "run-old", lineage: {source_run_id: "base-old"}}
    };
  `, context);

  const request = vm.runInContext("loadRunComparisonPanel()", context);
  vm.runInContext(`
    state.activeRunId = "run-new";
    state.dashboard = {
      run: {run_id: "run-new", lineage: {source_run_id: "base-new"}}
    };
    state.runComparisonRequestGeneration += 1;
    state.runComparisonLoading = false;
  `, context);
  pending.resolve({target_run_id: "run-old", baseline_run_id: "base-old"});
  await request;

  assert.equal(vm.runInContext("state.runComparison", context), null);
  assert.equal(vm.runInContext("state.runComparisonLoading", context), false);
});

test("late source findings cannot repopulate a different next-flow wizard", async () => {
  const pending = deferred();
  const context = vm.createContext({
    URLSearchParams,
    console,
    document: {getElementById: () => ({})},
    fetch: async () => ({
      ok: true,
      status: 200,
      statusText: "OK",
      async json() {
        return pending.promise;
      },
    }),
    renderCockpit: async () => {},
  });
  await load(context, "operator-api-state.js");
  await load(context, "operator-next-flow-actions.js");
  context.activateTab = () => {};
  context.sourceFindingPriority = () => 0;
  vm.runInContext(`
    state.activeRunId = "run-old";
    state.dashboard = {work_item: "WI-1", run: {run_id: "run-old"}};
  `, context);

  const request = vm.runInContext('openNextFlowWizard("start-follow-up-flow")', context);
  await new Promise((resolve) => setImmediate(resolve));
  vm.runInContext(`
    state.activeRunId = "run-new";
    state.nextFlowWizard.active = true;
    state.nextFlowWizard.action = "create-new-work-item";
    state.nextFlowWizard.requestGeneration += 1;
  `, context);
  pending.resolve({source_run_id: "run-old", groups: [{items: [{id: "old-finding"}]}]});
  await request;

  assert.equal(vm.runInContext("state.nextFlowWizard.sourceFindings", context), null);
  assert.equal(vm.runInContext("state.nextFlowWizard.action", context), "create-new-work-item");
});
