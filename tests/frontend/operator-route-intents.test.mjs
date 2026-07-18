import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

async function routeIntentContext() {
  const context = vm.createContext({URLSearchParams});
  for (const filename of ["operator-route-state.js", "operator-route-intents.js"]) {
    const sourcePath = path.join(staticRoot, filename);
    vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  }
  return context;
}

function resolve(context, intent, routeContext) {
  return JSON.parse(JSON.stringify(vm.runInContext(
    `resolveOperatorRouteIntent(${JSON.stringify(intent)}, ${JSON.stringify(routeContext)})`,
    context,
  )));
}

test("every visible navigation action resolves to one canonical route outcome", async () => {
  const context = await routeIntentContext();
  const cases = [
    ["inbox-work-item", {workItem: "WI-001"}, "Open in Studio", "studio", ""],
    ["historical-run", {workItem: "WI-001", runId: "run-2"}, "Inspect run history", "history", "run-2"],
    ["parent-run", {workItem: "WI-000", runId: "run-1"}, "Inspect parent run", "history", "run-1"],
    ["child-work-item", {workItem: "WI-002"}, "Open child work item", "studio", ""],
    ["run-artifacts", {workItem: "WI-001", runId: "run-2"}, "Inspect run artifacts", "studio", "run-2"],
  ];
  for (const [intent, input, label, mode, runId] of cases) {
    const result = resolve(context, intent, input);
    assert.equal(result.intent, intent);
    assert.equal(result.label, label);
    assert.equal(result.route.mode, mode);
    assert.equal(result.route.runId, runId);
  }
});

test("archived run intents retain both history and artifact inspection", async () => {
  const context = await routeIntentContext();
  const input = {workItem: "WI-ARCHIVE", runId: "run-closed", archived: true};
  const historyHref = vm.runInContext(
    `operatorRouteIntentHref("historical-run", ${JSON.stringify(input)})`,
    context,
  );
  const artifactsHref = vm.runInContext(
    `operatorRouteIntentHref("run-artifacts", ${JSON.stringify(input)})`,
    context,
  );
  assert.match(historyHref, /^\/\?mode=history/);
  assert.match(artifactsHref, /^\/\?mode=studio&view=artifacts/);
  assert.match(historyHref, /run_id=run-closed/);
  assert.match(artifactsHref, /run_id=run-closed/);
});

test("Inbox work-item intent preserves optional run and stage context", async () => {
  const context = await routeIntentContext();
  const resolved = resolve(context, "inbox-work-item", {
    workItem: "WI-001", runId: "run-1", stage: "qa",
  });
  assert.equal(resolved.route.workItem, "WI-001");
  assert.equal(resolved.route.runId, "run-1");
  assert.equal(resolved.route.stage, "qa");
});

test("unsafe and incomplete route intents fail closed", async () => {
  const context = await routeIntentContext();
  assert.throws(
    () => vm.runInContext('resolveOperatorRouteIntent("historical-run", {workItem: "WI-1"})', context),
    /safe run id/,
  );
  assert.throws(
    () => vm.runInContext('resolveOperatorRouteIntent("child-work-item", {workItem: ".."})', context),
    /safe work item/,
  );
  assert.throws(
    () => vm.runInContext('resolveOperatorRouteIntent("surprise", {workItem: "WI-1"})', context),
    /Unknown operator route intent/,
  );
});

test("Inbox and History renderers bind their visible actions to shared intents", async () => {
  const inbox = await readFile(path.join(staticRoot, "operator-inbox.js"), "utf8");
  const history = await readFile(path.join(staticRoot, "operator-history.js"), "utf8");
  assert.match(inbox, /data-operator-route-intent="\$\{escapeHtml\(route.intent\)\}"/);
  for (const intent of ["parent-run", "child-work-item", "run-artifacts"]) {
    assert.match(history, new RegExp(`data-operator-route-intent="${intent}"`));
  }
});
