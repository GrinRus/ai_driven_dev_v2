import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const assetPath = path.join(repositoryRoot, "src/aidd/cli/static/operator-onboarding.js");

async function context() {
  const value = vm.createContext({console});
  vm.runInContext(await readFile(assetPath, "utf8"), value, {filename: assetPath});
  return value;
}

function reduce(value, state, event, payload = {}) {
  value.__state = state;
  value.__payload = payload;
  return JSON.parse(JSON.stringify(vm.runInContext(
    `reduceGuidedSetupState(__state, ${JSON.stringify(event)}, __payload)`,
    value,
  )));
}

test("Guided Setup advances through project, work item, runtime, and review", async () => {
  const value = await context();
  let state = reduce(value, null, "project-valid");
  assert.equal(state.step, "work-item");
  state = reduce(value, state, "work-item-selected", {branch: "create", workItem: "WI-NEW"});
  assert.equal(state.step, "runtime");
  assert.equal(state.workItemBranch, "create");
  state = reduce(value, state, "runtime-selected", {runtimeId: "generic-cli"});
  assert.equal(state.step, "review-launch");
  assert.equal(state.runtimeId, "generic-cli");
  state = reduce(value, state, "launch-readiness", {ready: true});
  assert.equal(state.launchReadiness, "ready");
});

test("Guided Setup supports resume and deterministic backward navigation", async () => {
  const value = await context();
  let state = reduce(value, null, "project-valid");
  state = reduce(value, state, "work-item-selected", {branch: "resume", workItem: "WI-OLD"});
  state = reduce(value, state, "runtime-selected", {runtimeId: "codex"});
  state = reduce(value, state, "back");
  assert.equal(state.step, "runtime");
  assert.equal(state.runtimeId, "codex");
  state = reduce(value, state, "back");
  assert.equal(state.step, "work-item");
  assert.equal(state.runtimeId, "");
  assert.equal(state.workItemBranch, "resume");
});

test("Guided Setup fails closed on validation, incomplete continue, and blocked launch", async () => {
  const value = await context();
  let state = reduce(value, null, "project-invalid", {error: "outside workspace"});
  assert.equal(state.step, "project");
  assert.equal(state.projectStatus, "invalid");
  state = reduce(value, state, "continue");
  assert.match(state.error, /Complete the current setup step/);
  state = reduce(value, state, "project-valid");
  state = reduce(value, state, "work-item-selected", {branch: "create", workItem: "WI-NEW"});
  state = reduce(value, state, "runtime-selected", {runtimeId: "generic-cli"});
  state = reduce(value, state, "launch-readiness", {ready: false, error: "command unavailable"});
  assert.equal(state.launchReadiness, "blocked");
  assert.equal(state.error, "command unavailable");
});

test("Create and Resume are sibling branches before runtime selection", async () => {
  const source = await readFile(assetPath, "utf8");
  const create = source.indexOf('data-onboarding-work-item-branch="create"');
  const resume = source.indexOf('data-onboarding-work-item-branch="resume"');
  const runtime = source.indexOf("<span>Runner</span>", resume);
  assert.ok(create >= 0 && resume > create && runtime > resume);
  assert.doesNotMatch(source, /const canResume = Boolean\(state\.selectedRuntime\)/);
  assert.match(source, /if \(action === "create" && !state\.selectedRuntime\)/);
  assert.match(source, /runtime selection and launch remain separate actions/);
});

test("project-set and config details are collapsed behind Advanced", async () => {
  const source = await readFile(assetPath, "utf8");
  assert.match(source, /<details class="onboarding-advanced">/);
  assert.match(source, /<summary>Advanced configuration<\/summary>/);
  const advancedStart = source.indexOf('function renderOnboardingAdvanced()');
  const advancedEnd = source.indexOf('function onboardingCanCreate()', advancedStart);
  const advanced = source.slice(advancedStart, advancedEnd);
  assert.match(advanced, /<strong>Config<\/strong>/);
  assert.match(advanced, /renderProjectSetEditor\(\)/);
});

test("first-run setup has no mode selector with duplicate service semantics", async () => {
  const assets = await Promise.all([
    "operator-api-state.js",
    "operator-next-flow-actions.js",
    "operator-next-flow-view.js",
    "operator-main.js",
  ].map((name) => readFile(path.join(path.dirname(assetPath), name), "utf8")));
  const source = assets.join("\n");
  assert.doesNotMatch(source, /SETUP_MODES|data-setup-mode|setupModeView/);
  assert.match(source, /data-first-launch-run/);
  assert.match(source, /data-first-launch-stage/);
  assert.match(source, /data-next-flow-action="start-follow-up-flow"/);
});
