import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-draft-store.js");

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
    values,
  };
}

async function draftContext() {
  const storage = memoryStorage();
  const context = vm.createContext({TextEncoder, window: {sessionStorage: storage}});
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return {context, storage};
}

function expression(context, source) {
  return JSON.parse(JSON.stringify(vm.runInContext(source, context)));
}

const IDENTITY = {
  project: "/project/one",
  workItem: "WI-001",
  run: "run-1",
  stage: "implement",
  form: "question",
  sourceId: "Q-001",
};

test("every identity dimension selects an isolated draft", async () => {
  const {context} = await draftContext();
  const dimensions = {
    project: "/project/two",
    workItem: "WI-002",
    run: "run-2",
    stage: "qa",
    form: "intervention",
    sourceId: "REQ-002",
  };
  vm.runInContext(`writeOperatorDraft(${JSON.stringify(IDENTITY)}, {text: "owner"}, {now: 100})`, context);
  for (const [field, value] of Object.entries(dimensions)) {
    const identity = {...IDENTITY, [field]: value};
    vm.runInContext(
      `writeOperatorDraft(${JSON.stringify(identity)}, {text: ${JSON.stringify(field)}}, {now: 200})`,
      context,
    );
    assert.equal(expression(
      context,
      `readOperatorDraft(${JSON.stringify(identity)}, {now: 201}).value.text`,
    ), field);
  }
  assert.equal(expression(
    context,
    `readOperatorDraft(${JSON.stringify(IDENTITY)}, {now: 201}).value.text`,
  ), "owner");
});

test("successful owner cleanup leaves sibling drafts untouched", async () => {
  const {context} = await draftContext();
  const sibling = {...IDENTITY, sourceId: "Q-002"};
  vm.runInContext(`writeOperatorDraft(${JSON.stringify(IDENTITY)}, {text: "one"}, {now: 100})`, context);
  vm.runInContext(`writeOperatorDraft(${JSON.stringify(sibling)}, {text: "two"}, {now: 100})`, context);
  assert.equal(vm.runInContext(`clearOperatorDraft(${JSON.stringify(IDENTITY)}, {now: 101})`, context), true);
  assert.equal(vm.runInContext(`readOperatorDraft(${JSON.stringify(IDENTITY)}, {now: 101})`, context), null);
  assert.equal(expression(
    context,
    `readOperatorDraft(${JSON.stringify(sibling)}, {now: 101}).value.text`,
  ), "two");
});

test("expiry and malformed records are purged rather than restored", async () => {
  const {context, storage} = await draftContext();
  vm.runInContext(`writeOperatorDraft(${JSON.stringify(IDENTITY)}, {text: "temporary"}, {now: 0})`, context);
  assert.equal(
    vm.runInContext(
      `readOperatorDraft(${JSON.stringify(IDENTITY)}, {now: OPERATOR_DRAFT_TTL_MS + 1})`,
      context,
    ),
    null,
  );
  storage.setItem("aidd.operator.drafts.v1", "{not-json");
  assert.equal(vm.runInContext(`readOperatorDraft(${JSON.stringify(IDENTITY)}, {now: 1})`, context), null);
});

test("store enforces count, payload, and sensitive-field bounds", async () => {
  const {context} = await draftContext();
  for (let index = 1; index <= 33; index += 1) {
    const identity = {...IDENTITY, sourceId: `Q-${index}`};
    vm.runInContext(`writeOperatorDraft(${JSON.stringify(identity)}, {text: "ok"}, {now: ${index}})`, context);
  }
  assert.equal(vm.runInContext(
    "Object.keys(loadOperatorDraftBucket(window.sessionStorage, 34).entries).length",
    context,
  ), 32);
  assert.throws(
    () => vm.runInContext(
      `writeOperatorDraft(${JSON.stringify(IDENTITY)}, {text: "x".repeat(70 * 1024)}, {now: 40})`,
      context,
    ),
    /64 KiB/,
  );
  assert.throws(
    () => vm.runInContext(
      `writeOperatorDraft(${JSON.stringify(IDENTITY)}, {api_token: "forbidden"}, {now: 40})`,
      context,
    ),
    /secret fields/,
  );
});
