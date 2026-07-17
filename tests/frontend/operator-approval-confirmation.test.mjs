import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const assetPath = path.join(
  repositoryRoot,
  "src/aidd/cli/static/operator-approvals-interventions.js",
);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function approvalContext() {
  const posts = [];
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
  const context = vm.createContext({
    console,
    document,
    escapeHtml,
    pathLine: (value) => `<span>${escapeHtml(value)}</span>`,
    state: {activeJobId: "job-1"},
    postJson: async (url, payload) => {
      assert.ok(controls.every((control) => control.disabled));
      posts.push({url, payload});
      return {};
    },
    toast: () => {},
    __posts: posts,
    __controls: controls,
    __confirmation: confirmation,
    __preview: preview,
  });
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
});
