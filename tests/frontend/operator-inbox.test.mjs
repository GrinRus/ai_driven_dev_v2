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
    renderProjectWorkItemCreator() { return ""; },
  });
  await load(context, "operator-inbox.js");
  return context;
}

test("Studio Inbox preserves section priority and exact durable routes", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`
    state.inbox = {
      durable: {sections: [
        {key: "needs-input", label: "Needs input", items: [{
          item_id: "decision", state: "blocking", status_label: "Blocked",
          title: "Answer question", summary: "Q1 is unresolved",
          route: {intent: "inbox-work-item", work_item: "WI-1", run_id: "run-1", stage: "idea"},
          primary_action: {action: "answer-questions", label: "Answer", enabled: true}
        }]},
        {key: "ready", label: "Ready", items: [{
          item_id: "ready", state: "ready", status_label: "Ready",
          title: "Continue plan", summary: "Plan may run",
          route: {intent: "inbox-work-item", work_item: "WI-2", run_id: "run-2", stage: "plan"},
          primary_action: {action: "run-stage", label: "Run plan", enabled: true}
        }]},
        {key: "complete", label: "Complete", items: [{
          item_id: "complete", state: "terminal", status_label: "Complete",
          title: "QA complete", summary: "Choose next flow",
          route: {intent: "inbox-work-item", work_item: "WI-3", run_id: "run-3", stage: "qa"},
          primary_action: {action: "create-new-work-item", label: "Create", enabled: true}
        }]}
      ]},
      running_now: [{
        job_id: "job-1", kind: "stage", message: "Working", last_output_text: "",
        project_root: "/projects/project-a",
        route: {intent: "inbox-work-item", work_item: "WI-4", run_id: "run-4", stage: "research"}
      }]
    };
    renderStudioInbox();
  `, context);
  const positions = ["needs-input", "running", "ready", "complete"]
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
  assert.match(html, /data-route-project-root="\/projects\/project-a"/);
});

test("Studio Inbox renders canonical DOM keys while accepting legacy payload groups", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`
    state.inbox = {
      durable: {sections: [
        {key: "needs-input", label: "Needs input", items: [{
          item_id: "decision", state: "blocking", status_label: "Blocked",
          title: "Answer question", summary: "Q1 is unresolved",
          route: {intent: "inbox-work-item", work_item: "WI-1", run_id: "run-1", stage: "idea"},
          primary_action: {action: "answer-questions", label: "Answer", enabled: true}
        }]},
        {key: "running", label: "Running", items: [{
          item_id: "running", state: "running", status_label: "Running",
          title: "Wait for stage", summary: "Stage is executing",
          route: {intent: "inbox-work-item", work_item: "WI-2", run_id: "run-2", stage: "plan"},
          primary_action: {action: "wait-for-stage", label: "View", enabled: true}
        }]},
        {key: "ready", label: "Ready", items: [{
          item_id: "ready", state: "ready", status_label: "Ready",
          title: "Continue plan", summary: "Plan may run",
          route: {intent: "inbox-work-item", work_item: "WI-3", run_id: "run-3", stage: "plan"},
          primary_action: {action: "run-stage", label: "Run plan", enabled: true}
        }]},
        {key: "complete", label: "Complete", items: [{
          item_id: "complete", state: "terminal", status_label: "Complete",
          title: "QA complete", summary: "Choose next flow",
          route: {intent: "inbox-work-item", work_item: "WI-4", run_id: "run-4", stage: "qa"},
          primary_action: {action: "create-new-work-item", label: "Create", enabled: true}
        }]}
      ]},
      running_now: []
    };
    renderStudioInbox();
  `, context);

  const positions = ["needs-input", "running", "ready", "complete"]
    .map((section) => html.indexOf(`data-inbox-section="${section}"`));
  assert.deepEqual([...positions].sort((a, b) => a - b), positions);
  assert.match(html, /data-inbox-section="needs-input"/);
  assert.match(html, /data-inbox-section="running"/);
  assert.match(html, /data-route-work-item="WI-2"/);
});

test("Project Inbox exposes a direct new Work Item entry point", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`
    state.inbox = {durable: {sections: []}, running_now: []};
    renderStudioInbox();
  `, context);

  assert.match(html, /data-new-work-item/);
  assert.match(html, /New Work Item/);
});

test("Project Inbox renders empty groups and one selected Work Item inspector action", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`
    state.projectHome = {
      selected_work_item: "WI-7",
      work_items: [{
        work_item: "WI-7", intent: {excerpt: "Investigate checkout"},
        active_stage: "plan", stage_progress_count: 2, stage_total_count: 8,
        terminal_state: "blocked", blocker_count: 1
      }]
    };
    state.inbox = {durable: {sections: [
      {key: "needs-input", label: "Needs input", items: [{
        item_id: "decision", state: "blocking", status_label: "Waiting for answer",
        title: "Answer question", summary: "A decision is required.",
        route: {intent: "inbox-work-item", work_item: "WI-7", run_id: "run-7", stage: "plan"},
        primary_action: {action: "answer-questions", label: "Open decision", enabled: true}
      }]}
    ]}, running_now: []};
    renderStudioInbox();
  `, context);

  for (const section of ["needs-input", "running", "ready", "complete"]) {
    assert.match(html, new RegExp(`data-inbox-section="${section}"`));
  }
  assert.match(html, /data-inbox-inspector/);
  assert.match(html, /data-inbox-selected-context="WI-7"/);
  assert.equal((html.match(/data-inbox-action="answer-questions"/g) || []).length, 1);
  assert.match(html, /data-selected-work-item="WI-7"/);
});

test("Project Inbox exposes one durable continue-or-create entry recommendation", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`
    state.inbox = {durable: {
      entry_recommendation: {
        action: "continue-existing-intent",
        label: "Continue existing Work Item",
        detail: "The research brief is waiting for review.",
        work_item: "WI-7",
        route: {intent: "inbox-work-item", work_item: "WI-7", run_id: "run-7", stage: "research"}
      },
      sections: []
    }, running_now: []};
    renderStudioInbox();
  `, context);
  assert.match(html, /Continue existing Work Item/);
  assert.match(html, /New Work Item/);
  assert.match(html, /data-route-work-item="WI-7"/);
  assert.match(html, /research/);
});

test("consumed request context is rendered as read-only copy without a nested textarea", async () => {
  const context = await inboxContext();
  const html = vm.runInContext(`renderOperatorRequestEditor({
    request_text: "## Title\\n\\nA long-lived request",
    consumed: true,
    editable: false,
    disabled_reason: "The request was consumed by an existing run."
  })`, context);

  assert.match(html, /class="operator-request-readonly"/);
  assert.match(html, /Request Markdown \(read-only\)/);
  assert.match(html, /The request was consumed by an existing run\./);
  assert.doesNotMatch(html, /<textarea/);
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
  assert.match(onboarding, /const projectMismatch = Boolean/);
  assert.match(onboarding, /project_root: context\.projectRoot \|\|/);
  assert.match(onboarding, /navigateOperatorRouteIntent\("inbox-work-item", context\)/);
  assert.match(main, /intent === "inbox-work-item"/);
  assert.match(main, /projectRoot: routeTarget\.dataset\.routeProjectRoot/);
  assert.match(main, /activateInboxWorkItemRoute\(context\)/);
  assert.match(main, /async function activateInboxAction\(context, action\)/);
  assert.match(main, /await activateInboxAction\(context, action\)/);
  assert.match(main, /serviceActionEnabled === "false"/);
});

test("running job route switches project even when Work Item ids collide", async () => {
  const calls = [];
  const context = vm.createContext({
    console,
    state: {
      dashboard: {work_item: "WI-SAME"},
      projectHome: {project_root: "/project-b"},
      onboarding: {projectRootInput: "/project-b"},
    },
    postJson: async (path, payload) => calls.push({path, payload}),
    navigateOperatorRouteIntent: async (intent, route) => calls.push({intent, route}),
  });
  await load(context, "operator-onboarding.js");

  await vm.runInContext(
    "activateInboxWorkItemRoute({projectRoot: '/project-a', workItem: 'WI-SAME', runId: 'run-a', stage: 'plan'})",
    context,
  );

  assert.deepEqual(JSON.parse(JSON.stringify(calls)), [
    {
      path: "/api/onboarding/work-item",
      payload: {action: "resume", project_root: "/project-a", work_item: "WI-SAME"},
    },
    {
      intent: "inbox-work-item",
      route: {projectRoot: "/project-a", workItem: "WI-SAME", runId: "run-a", stage: "plan"},
    },
  ]);
});
