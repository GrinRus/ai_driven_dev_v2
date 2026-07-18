import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-mutation-guard.js");

async function guardContext() {
  const context = vm.createContext({});
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return context;
}

test("same-key double click shares one request while different keys run concurrently", async () => {
  const context = await guardContext();
  vm.runInContext(`
    calls = [];
    releases = {};
    execute = (key) => () => new Promise((resolve) => {
      calls.push(key);
      releases[key] = resolve;
    });
    keyA = operatorMutationKey("run-stage", "run-1", "plan");
    keyB = operatorMutationKey("run-stage", "run-1", "qa");
    first = runGuardedMutation({key: keyA, execute: execute("plan")});
    duplicate = runGuardedMutation({key: keyA, execute: execute("duplicate")});
    other = runGuardedMutation({key: keyB, execute: execute("qa")});
  `, context);
  assert.equal(vm.runInContext("first === duplicate", context), true);
  assert.deepEqual(JSON.parse(JSON.stringify(vm.runInContext("calls", context))), ["plan", "qa"]);
  vm.runInContext('releases.plan({job_id: "job-plan"}); releases.qa({job_id: "job-qa"});', context);
  await vm.runInContext("Promise.all([first, duplicate, other])", context);
  assert.equal(vm.runInContext("mutationGuardState(keyA).status", context), "succeeded");
  assert.equal(vm.runInContext("mutationGuardState(keyB).status", context), "succeeded");
});

test("conflict resolves to the durable winner without a second mutation", async () => {
  const context = await guardContext();
  const result = await vm.runInContext(`
    (() => {
      let calls = 0;
      return runGuardedMutation({
        key: operatorMutationKey("approval", "job-1", "REQ-1"),
        execute: async () => {
          calls += 1;
          const error = new Error("decision conflict");
          error.status = 409;
          throw error;
        },
        readWinner: async () => ({action: "deny", source: "durable"})
      }).then((result) => ({result, calls}));
    })()
  `, context);
  const serialized = JSON.parse(JSON.stringify(result));
  assert.equal(serialized.calls, 1);
  assert.equal(serialized.result.status, "conflict");
  assert.deepEqual(serialized.result.winner, {action: "deny", source: "durable"});
});

test("failed state remains retryable and a later attempt can succeed", async () => {
  const context = await guardContext();
  await assert.rejects(
    vm.runInContext(`runGuardedMutation({
      key: operatorMutationKey("answer", "run-1", "Q1"),
      execute: async () => { throw new Error("temporary failure"); }
    })`, context),
    /temporary failure/,
  );
  assert.equal(vm.runInContext(
    'mutationGuardState(operatorMutationKey("answer", "run-1", "Q1")).status',
    context,
  ), "failed");
  const result = await vm.runInContext(`runGuardedMutation({
    key: operatorMutationKey("answer", "run-1", "Q1"),
    execute: async () => ({saved: true})
  })`, context);
  assert.equal(result.status, "succeeded");
});

test("mutation keys reject missing and unbounded identity", async () => {
  const context = await guardContext();
  assert.throws(() => vm.runInContext('operatorMutationKey("Run Stage", "run-1")', context));
  assert.throws(() => vm.runInContext('operatorMutationKey("run-stage")', context));
  assert.throws(() => vm.runInContext('operatorMutationKey("run-stage", "x".repeat(161))', context));
});
