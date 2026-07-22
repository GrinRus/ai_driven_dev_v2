import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");
const assetPath = path.join(staticRoot, "operator-approvals-interventions.js");

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function approvalContext({conflict = false, terminal = false} = {}) {
  const posts = [];
  const toasts = [];
  const controls = Array.from({length: 6}, () => ({
    disabled: false,
    setAttribute(name, value) {
      this[name] = value;
    },
  }));
  const reason = {value: "Bounded read-only inspection"};
  const preview = {textContent: ""};
  const confirmation = {
    hidden: true,
    querySelector: () => ({focus: () => {}}),
  };
  const document = {
    querySelector(selector) {
      if (selector.includes("data-approval-reason-preview")) return preview;
      if (selector.includes("data-approval-session-confirmation")) return confirmation;
      if (selector.includes("data-approval-reason")) return reason;
      if (selector.includes("data-operator-action")) return {focus: () => {}};
      return null;
    },
    querySelectorAll: () => controls,
  };
  const state = {activeJobId: "job-1", approvalSessionConfirmation: null};
  const context = vm.createContext({
    console,
    document,
    escapeHtml,
    pathLine: (value) => `<span>${escapeHtml(value)}</span>`,
    state,
    postJson: async (url, payload) => {
      assert.ok(controls.every((control) => control.disabled));
      posts.push({url, payload});
      if (conflict) {
        const error = new Error("decision conflict");
        error.status = 409;
        throw error;
      }
      return {
        decisions: [{request_id: "REQ-1", action: payload.action, reason: payload.reason}],
        audit_history: [{request_id: "REQ-1", decision_action: payload.action}],
      };
    },
    api: async () => terminal ? {decisions: [], audit_history: []} : ({
      decisions: [{request_id: "REQ-1", action: "allow_once", reason: "durable winner"}],
      audit_history: [{request_id: "REQ-1", decision_action: "allow_once"}],
    }),
    toast: (message) => toasts.push(message),
    __posts: posts,
    __toasts: toasts,
    __controls: controls,
    __confirmation: confirmation,
    __preview: preview,
    __state: state,
  });
  vm.runInContext(
    await readFile(path.join(staticRoot, "operator-mutation-guard.js"), "utf8"),
    context,
  );
  vm.runInContext(await readFile(assetPath, "utf8"), context, {filename: assetPath});
  vm.runInContext("renderApprovals = async () => {}", context);
  return context;
}

test("approval card exposes reason capture and explicit session breadth", async () => {
  const context = await approvalContext();
  const html = vm.runInContext(
    `renderApprovalRequestCard({
      id: "REQ-1", kind: "shell", runtime_id: "generic-cli", stage: "idea",
      payload: {command: "python -m pytest -q"}
    }, null, new Set(["REQ-1"]))`,
    context,
  );
  assert.match(html, /data-approval-reason="REQ-1"/);
  assert.match(html, /Confirm session-wide approval/);
  assert.match(html, /all matching requests in the current runtime approval session/);
  assert.match(html, /data-approval-request-id="REQ-1"/);
  assert.match(html, /data-approval-status="pending"/);
  assert.match(html, /data-approval-risk="unknown"/);
  assert.match(html, /data-approval-scope="runtime request payload"/);
  assert.match(html, /data-approval-breadth="single-request"/);
});

test("resolved approval card exposes the durable winner and session breadth", async () => {
  const context = await approvalContext();
  const html = vm.runInContext(
    `renderApprovalRequestCard({
      id: "REQ-1", kind: "shell", runtime_id: "generic-cli", stage: "idea",
      cwd: "/workspace", paths: ["src"], risk: "medium",
      payload: {command: "python -m pytest -q"}
    }, {action: "allow_for_session", source: "ui", reason: "bounded"}, new Set())`,
    context,
  );
  assert.match(html, /data-approval-status="allow_for_session"/);
  assert.match(html, /data-approval-risk="medium"/);
  assert.match(html, /data-approval-scope="\/workspace \/ src"/);
  assert.match(html, /data-approval-breadth="session"/);
  assert.match(html, /data-approval-winner="allow_for_session"/);
  assert.match(html, /data-approval-durable-winner="allow_for_session"/);
  assert.match(html, /Durable winner/);
});

test("session approval posts only after confirmation with visible reason", async () => {
  const context = await approvalContext();
  await vm.runInContext(`submitApproval("REQ-1", "allow_for_session")`, context);
  assert.equal(context.__posts.length, 0);
  assert.equal(context.__confirmation.hidden, false);
  assert.equal(context.__preview.textContent, "Bounded read-only inspection");

  await vm.runInContext(
    `submitApproval("REQ-1", "allow_for_session", {sessionConfirmed: true})`,
    context,
  );
  assert.equal(JSON.stringify(context.__posts), JSON.stringify([{
    url: "/api/jobs/job-1/operator-requests/REQ-1/decision",
    payload: {action: "allow_for_session", reason: "Bounded read-only inspection"},
  }]));
  assert.equal(context.__toasts.at(-1), "Durable runtime decision: allow_for_session: Bounded read-only inspection");
});

test("polling re-render preserves pending session confirmation and reason", async () => {
  const context = await approvalContext();
  await vm.runInContext(`submitApproval("REQ-1", "allow_for_session")`, context);
  context.__confirmation.hidden = true;
  context.__preview.textContent = "";
  vm.runInContext(
    `restoreApprovalSessionConfirmation({
      pending_request_ids: ["REQ-1"], decisions: []
    })`,
    context,
  );

  assert.equal(context.__confirmation.hidden, false);
  assert.equal(context.__preview.textContent, "Bounded read-only inspection");
  assert.equal(JSON.stringify(context.__state.approvalSessionConfirmation), JSON.stringify({
    jobId: "job-1",
    requestId: "REQ-1",
    reason: "Bounded read-only inspection",
  }));

  vm.runInContext(
    `restoreApprovalSessionConfirmation({
      pending_request_ids: [],
      decisions: [{request_id: "REQ-1", action: "allow_for_session"}]
    })`,
    context,
  );
  assert.equal(context.__state.approvalSessionConfirmation, null);
});

test("cancelling session confirmation clears browser-only state", async () => {
  const context = await approvalContext();
  await vm.runInContext(`submitApproval("REQ-1", "allow_for_session")`, context);
  vm.runInContext(`closeApprovalSessionConfirmation("REQ-1")`, context);

  assert.equal(context.__confirmation.hidden, true);
  assert.equal(context.__state.approvalSessionConfirmation, null);
  assert.equal(context.__posts.length, 0);
});

test("opposite concurrent decisions render one durable winner", async () => {
  const context = await approvalContext({conflict: true});
  await vm.runInContext(
    `Promise.all([
      submitApproval("REQ-1", "allow_once"),
      submitApproval("REQ-1", "deny")
    ])`,
    context,
  );
  assert.equal(context.__posts.length, 1);
  assert.deepEqual(context.__toasts, [
    "Durable runtime decision: allow_once: durable winner",
    "Durable runtime decision: allow_once: durable winner",
  ]);
  assert.ok(context.__controls.every((control) => control.disabled === false));
});

test("terminal decision conflict refreshes audit state without stale controls", async () => {
  const context = await approvalContext({conflict: true, terminal: true});
  await vm.runInContext(`submitApproval("REQ-1", "deny")`, context);
  assert.equal(
    context.__toasts.at(-1),
    "The approval job is terminal; showing the durable audit state.",
  );
  assert.ok(context.__controls.every((control) => control.disabled === false));
});
