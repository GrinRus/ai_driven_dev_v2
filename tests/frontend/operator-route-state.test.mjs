import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-route-state.js");

async function routeContext() {
  const context = vm.createContext({URLSearchParams});
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return context;
}

function decode(context, search, options = {}) {
  return JSON.parse(JSON.stringify(vm.runInContext(
    `decodeOperatorRoute(${JSON.stringify(search)}, ${JSON.stringify(options)})`,
    context,
  )));
}

test("canonical route state round-trips every supported context key", async () => {
  const context = await routeContext();
  const route = {
    mode: "studio",
    view: "artifacts",
    workItem: "WI-001",
    runId: "run-20260717",
    stage: "implement",
    attempt: null,
    taskAttempt: 3,
    artifact: "implementation-report.md",
  };
  const query = vm.runInContext(`encodeOperatorRoute(${JSON.stringify(route)})`, context);
  assert.deepEqual(decode(context, query).value, route);
});

test("missing and legacy routes resolve deterministically", async () => {
  const context = await routeContext();
  assert.deepEqual(decode(context, "").value, {
    mode: "inbox",
    view: "overview",
    workItem: "",
    runId: "",
    stage: "",
    attempt: null,
    taskAttempt: null,
    artifact: "",
  });
  const legacy = decode(context, "?tab=evidence&stage=qa&run_id=run-1&key=qa-report.md");
  assert.equal(legacy.source, "legacy");
  assert.equal(legacy.value.mode, "studio");
  assert.equal(legacy.value.view, "artifacts");
  assert.equal(legacy.value.artifact, "qa-report.md");
});

test("invalid, stale, and ambiguous contexts fail closed with stable warnings", async () => {
  const context = await routeContext();
  const result = decode(
    context,
    "?mode=history&work_item=WI-404&run_id=../escape&stage=deploy&attempt=2&task_attempt=3&artifact=/etc/passwd",
    {knownWorkItems: ["WI-001"], knownRuns: ["run-1"]},
  );
  assert.equal(result.value.mode, "inbox");
  assert.equal(result.value.workItem, "");
  assert.equal(result.value.runId, "");
  assert.equal(result.value.artifact, "");
  assert.equal(result.value.attempt, null);
  assert.deepEqual(result.warnings.map((item) => item.code), [
    "invalid-value",
    "invalid-value",
    "invalid-value",
    "ambiguous-detail",
    "stale-value",
    "missing-context",
  ]);
});
