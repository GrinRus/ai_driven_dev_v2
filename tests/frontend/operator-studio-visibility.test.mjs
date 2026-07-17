import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const assetsRoot = path.join(repositoryRoot, "src/aidd/cli/static");

async function policyContext() {
  const context = vm.createContext({console, window: {aiddPresentation: null}});
  const source = await readFile(path.join(assetsRoot, "operator-api-state.js"), "utf8");
  vm.runInContext(source, context, {filename: "operator-api-state.js"});
  return context;
}

function resolve(context, input) {
  context.__input = input;
  return JSON.parse(JSON.stringify(vm.runInContext(
    "resolveStudioEvidenceVisibility(__input)",
    context,
  )));
}

test("Studio evidence visibility is value-aware and request-gated", async () => {
  const context = await policyContext();
  const cases = [
    ["no run", {}, {inspector: false, filmstrip: false, logs: false}],
    ["healthy running", {inspectorItemCount: 2, logEvidenceAvailable: true}, {inspector: true, filmstrip: false, logs: false}],
    ["blocked evidence", {inspectorItemCount: 1, logEvidenceAvailable: true, requestedSurface: "logs"}, {inspector: true, filmstrip: false, logs: true}],
    ["terminal overview", {filmstripFrameCount: 4, logEvidenceAvailable: true}, {inspector: false, filmstrip: false, logs: false}],
    ["requested history", {filmstripFrameCount: 4, requestedSurface: "history"}, {inspector: false, filmstrip: true, logs: false}],
  ];
  for (const [label, input, expected] of cases) {
    assert.deepEqual(resolve(context, input), expected, label);
  }
});

test("inspector, Filmstrip, and logs use the shared visibility policy", async () => {
  const artifacts = await readFile(path.join(assetsRoot, "operator-artifacts-documents.js"), "utf8");
  const history = await readFile(path.join(assetsRoot, "operator-next-flow-view.js"), "utf8");
  const logs = await readFile(path.join(assetsRoot, "operator-logs-jobs.js"), "utf8");
  const cockpit = await readFile(path.join(assetsRoot, "operator-stage-cockpit.js"), "utf8");
  assert.match(artifacts, /resolveStudioEvidenceVisibility\(\{inspectorItemCount\}\)/);
  assert.match(history, /filmstripFrameCount: run\.run_id \? 1 : 0/);
  assert.match(history, /requestedSurface: state\.activeTab === "history" \? "history" : ""/);
  assert.match(logs, /logEvidenceAvailable: liveLogAvailable \|\| Number\(item\?\.attempt_count \|\| 0\) > 0/);
  assert.match(logs, /requestedSurface: "logs"/);
  assert.match(cockpit, /state\.activeTab === "evidence"/);
  assert.match(cockpit, /state\.evidenceDetail === "logs"/);
  assert.match(cockpit, /state\.recoveryDetail === "logs"/);
});
