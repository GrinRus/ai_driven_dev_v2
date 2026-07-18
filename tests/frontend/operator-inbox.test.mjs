import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

async function load(context, filename) {
  const source = await readFile(path.join(staticRoot, filename), "utf8");
  vm.runInContext(source, context, {filename});
}

async function inboxContext() {
  const context = vm.createContext({
    console,
    state: {inbox: null},
    escapeHtml(value) { return String(value ?? ""); },
    renderStateSurface() { return "loading"; },
    renderStatusMarker({status, label}) { return `<mark data-status="${status}">${label}</mark>`; },
  });
  await load(context, "operator-inbox.js");
  return context;
}

test("Studio Inbox preserves section priority and exact durable routes", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`
    state.inbox = {
      durable: {sections: [
        {key: "needs-decision", label: "Needs your decision", items: [{
          item_id: "decision", state: "blocking", status_label: "Blocked",
          title: "Answer question", summary: "Q1 is unresolved",
          route: {intent: "inbox-work-item", work_item: "WI-1", run_id: "run-1", stage: "idea"},
          primary_action: {action: "answer-questions", label: "Answer", enabled: true}
        }]},
        {key: "ready-to-continue", label: "Ready to continue", items: [{
          item_id: "ready", state: "ready", status_label: "Ready",
          title: "Continue plan", summary: "Plan may run",
          route: {intent: "inbox-work-item", work_item: "WI-2", run_id: "run-2", stage: "plan"},
          primary_action: {action: "run-stage", label: "Run plan", enabled: true}
        }]},
        {key: "flow-complete", label: "Flow complete", items: [{
          item_id: "complete", state: "terminal", status_label: "Complete",
          title: "QA complete", summary: "Choose next flow",
          route: {intent: "inbox-work-item", work_item: "WI-3", run_id: "run-3", stage: "qa"},
          primary_action: {action: "create-new-work-item", label: "Create", enabled: true}
        }]}
      ]},
      running_now: [{
        job_id: "job-1", kind: "stage", message: "Working", last_output_text: "",
        route: {intent: "inbox-work-item", work_item: "WI-4", run_id: "run-4", stage: "research"}
      }]
    };
    renderStudioInbox();
  `, context);
  const positions = ["needs-decision", "running-now", "ready-to-continue", "flow-complete"]
    .map((section) => html.indexOf(`data-inbox-section="${section}"`));
  assert.deepEqual([...positions].sort((a, b) => a - b), positions);
  for (const [workItem, runId, stage] of [
    ["WI-1", "run-1", "idea"],
    ["WI-2", "run-2", "plan"],
    ["WI-3", "run-3", "qa"],
    ["WI-4", "run-4", "research"],
  ]) {
    assert.match(html, new RegExp(`data-route-work-item="${workItem}"[^>]*data-route-run-id="${runId}"[^>]*data-route-stage="${stage}"`));
  }
  assert.match(html, /data-inbox-action="answer-questions"/);
  assert.match(html, /data-inbox-action="run-stage"/);
  assert.match(html, /data-inbox-action="create-new-work-item"/);
});

test("disabled service eligibility does not disable read-only context navigation", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`renderStudioInboxItem({
    item_id: "not-ready", state: "ready", status_label: "Needs runtime",
    title: "Select runtime", summary: "Choose a runtime before launch",
    route: {intent: "inbox-work-item", work_item: "WI-1", run_id: null, stage: "idea"},
    primary_action: {action: "choose-runtime", label: "Select runtime", enabled: false}
  })`, context);
  assert.match(html, /data-service-action-enabled="false"/);
  assert.doesNotMatch(html, /\sdisabled(?:\s|>)/);
});

test("Running-now identity gaps stay visible and cannot navigate", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`
    state.inbox = {durable: {sections: []}, running_now: [{
      job_id: "legacy", kind: "workflow", message: "Legacy job", route: null
    }]};
    renderStudioInbox();
  `, context);
  assert.match(html, /data-state="malformed"/);
  assert.match(html, /Durable identity unavailable/);
  assert.doesNotMatch(html, /data-route-work-item/);
});

test("Inbox route activation resumes server context before browser navigation", async () => {
  const onboarding = await readFile(
    path.join(staticRoot, "operator-onboarding.js"),
    "utf8",
  );
  const main = await readFile(path.join(staticRoot, "operator-main.js"), "utf8");
  assert.match(onboarding, /postJson\("\/api\/onboarding\/work-item"/);
  assert.match(onboarding, /navigateOperatorRouteIntent\("inbox-work-item", context\)/);
  assert.match(main, /intent === "inbox-work-item"/);
  assert.match(main, /activateInboxWorkItemRoute\(context\)/);
});
