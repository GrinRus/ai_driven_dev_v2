import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

async function primitivesContext() {
  const context = vm.createContext({console});
  vm.runInContext(
    "function escapeHtml(value) { return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('\\\"', '&quot;'); }",
    context,
  );
  const source = await readFile(path.join(staticRoot, "operator-primitives.js"), "utf8");
  vm.runInContext(source, context, {filename: "operator-primitives.js"});
  return context;
}

test("Decision Bar keeps one primary slot for every state", async () => {
  const context = await primitivesContext();
  for (const status of ["action", "pending", "blocked", "complete", "stale", "no-action"]) {
    const html = vm.runInContext(
      `renderDecisionBar({
        kind: "fixture",
        status: ${JSON.stringify(status)},
        statusLabel: ${JSON.stringify(status)},
        title: "Decide now",
        body: "Durable outcome is authoritative.",
        primaryAction: ${status === "action" ? '{action: "run", label: "Run"}' : "null"}
      })`,
      context,
    );
    assert.equal((html.match(/data-primary-slot/g) || []).length, 1);
    assert.match(html, new RegExp(`data-status="${status}"`));
    assert.match(html, new RegExp(`>${status}<`));
  }
});

test("Decision Bar rejects unknown state instead of inferring policy", async () => {
  const context = await primitivesContext();
  assert.throws(
    () => vm.runInContext(
      'renderStatusMarker({status: "maybe", label: "Maybe"})',
      context,
    ),
    /Unknown decision bar state/,
  );
});

test("primary action slot renders supplied decisions without policy", async () => {
  const value = await primitivesContext();
  const action = vm.runInContext(
    'renderPrimaryActionSlot({primaryAction: {action: "service-owned", label: "Proceed", enabled: false}})',
    value,
  );
  assert.match(action, /data-primary-slot/);
  assert.match(action, /data-decision-action="service-owned"/);
  assert.match(action, /disabled aria-disabled="true"/);
  assert.doesNotMatch(action, /next_action|eligib|priority|terminal/i);

  const noAction = vm.runInContext(
    'renderPrimaryActionSlot({guidance: "No service-owned action for this state."})',
    value,
  );
  assert.match(noAction, /data-primary-slot/);
  assert.match(noAction, /No service-owned action for this state/);
  assert.doesNotMatch(noAction, /<button/);
});

test("state surfaces expose consequence, recovery, and truthful live semantics", async () => {
  const context = await primitivesContext();
  const states = ["empty", "loading", "error", "reconnecting", "unavailable"];
  for (const state of states) {
    const html = vm.runInContext(
      `renderStateSurface({
        kind: "fixture",
        state: ${JSON.stringify(state)},
        title: "Visible title",
        consequence: "Visible consequence",
        recovery: {action: "retry", label: "Retry"}
      })`,
      context,
    );
    assert.match(html, /Visible title/);
    assert.match(html, /Visible consequence/);
    assert.match(html, /data-state-recovery="retry"/);
    assert.match(html, new RegExp(`data-state="${state}"`));
    assert.match(
      html,
      new RegExp(`aria-busy="${["loading", "reconnecting"].includes(state)}"`),
    );
    assert.match(html, new RegExp(`role="${state === "error" ? "alert" : "status"}"`));
  }
});

test("shared interaction contract covers every state and its semantic announcement", async () => {
  const context = await primitivesContext();
  const states = JSON.parse(vm.runInContext("JSON.stringify(SHARED_INTERACTION_STATES)", context));
  assert.deepEqual(states, [
    "loading", "empty", "partial", "error", "disabled", "selected", "pending",
    "conflict", "success", "offline", "unavailable", "reconnecting",
    "permission-denied", "focus", "keyboard"
  ]);

  for (const state of states) {
    const contract = JSON.parse(vm.runInContext(
      `JSON.stringify(validateSharedInteractionContract({
        state: ${JSON.stringify(state)},
        accessibleName: "Shared state",
        statusText: ${JSON.stringify(state)}
      }))`,
      context,
    ));
    const html = vm.runInContext(
      `renderStateSurface({
        kind: "shared-contract",
        state: ${JSON.stringify(state)},
        title: "Shared state",
        consequence: "The service-owned consequence is visible.",
        recovery: {action: "retry", label: "Retry"}
      })`,
      context,
    );
    assert.match(html, /data-interaction-contract="shared-v1"/);
    assert.match(html, new RegExp(`data-state="${state}"`));
    assert.match(html, new RegExp(`role="${contract.role}"`));
    assert.match(html, new RegExp(`aria-live="${contract.live}"`));
    assert.match(html, new RegExp(`aria-busy="${contract.busy}"`));
    assert.equal((html.match(/data-status-text/g) || []).length, 1);
    assert.equal((html.match(/data-state-recovery/g) || []).length, 1);
  }
});

test("shared interaction contract rejects duplicate actions, color-only status, clipping, and focus loss", async () => {
  const context = await primitivesContext();
  const invalidCases = [
    ["primaryActionCount: 2", /one primary action/],
    ["statusUsesColorOnly: true", /text, not color alone/],
    ["clipped: true", /fit their rendered bounds/],
    ["focusLost: true", /preserve focus/],
  ];
  for (const [option, message] of invalidCases) {
    assert.throws(
      () => vm.runInContext(
        `validateSharedInteractionContract({state: "selected", accessibleName: "State", statusText: "Selected", ${option}})`,
        context,
      ),
      message,
    );
  }
  assert.throws(
    () => vm.runInContext(
      'validateSharedInteractionContract({state: "selected", accessibleName: "", statusText: "Selected"})',
      context,
    ),
    /accessible name/,
  );
});

test("decision bars publish one primary action and a non-color status contract", async () => {
  const context = await primitivesContext();
  for (const status of ["action", "pending", "blocked", "complete", "stale", "no-action"]) {
    const html = vm.runInContext(
      `renderDecisionBar({
        kind: "shared-contract",
        status: ${JSON.stringify(status)},
        statusLabel: "${status}",
        title: "Decision",
        body: "The consequence is visible.",
        primaryAction: ${status === "action" ? '{action: "run", label: "Run"}' : "null"}
      })`,
      context,
    );
    assert.match(html, /data-interaction-region/);
    assert.equal((html.match(/data-primary-action/g) || []).length, status === "action" ? 1 : 0);
    assert.equal((html.match(/data-status-text/g) || []).length, 1);
  }
});

test("Inbox Item renders service-owned routes and actions without eligibility policy", async () => {
  const context = await primitivesContext();
  for (const state of ["blocking", "running", "ready", "terminal", "malformed"]) {
    const html = vm.runInContext(
      `renderInboxItem({
        id: "item-${state}",
        state: ${JSON.stringify(state)},
        statusLabel: ${JSON.stringify(state)},
        title: "Inbox title",
        summary: "Inbox consequence",
        route: "/studio?work_item=WI-001&state=${state}",
        primaryAction: {action: "service-action-${state}", label: "Open", enabled: true},
        metadata: [{label: "Stage", value: "implement"}]
      })`,
      context,
    );
    assert.match(html, new RegExp(`data-state="${state}"`));
    assert.match(html, new RegExp(`data-inbox-action="service-action-${state}"`));
    assert.match(html, /data-inbox-route="\/studio\?work_item=WI-001&amp;state=/);
    assert.doesNotMatch(html, /disabled aria-disabled/);
    assert.match(html, /<dt>Stage<\/dt><dd>implement<\/dd>/);
  }
});

test("Guided Step keeps one complete anatomy across every state", async () => {
  const context = await primitivesContext();
  for (const state of ["current", "complete", "invalid", "optional", "disabled"]) {
    const html = vm.runInContext(
      `renderGuidedStep({
        id: "runtime",
        state: ${JSON.stringify(state)},
        title: "Choose runtime",
        explanation: "Select the command that will execute this work item.",
        fields: [{id: "runtime", label: "Runtime", type: "select", value: "generic-cli", options: [{value: "generic-cli", label: "Generic CLI"}]}],
        primaryAction: {action: "continue", label: "Continue", enabled: ${state !== "disabled"}},
        backAction: {action: "back", label: "Back", enabled: true},
        advanced: ["Permission policy is inherited."]
      })`,
      context,
    );
    assert.match(html, new RegExp(`data-state="${state}"`));
    assert.match(html, /<p>Select the command that will execute this work item\.<\/p>/);
    assert.match(html, /<label for="guided-runtime-runtime">Runtime<\/label>/);
    assert.equal((html.match(/data-guided-action="continue"/g) || []).length, 1);
    assert.equal((html.match(/data-guided-action="back"/g) || []).length, 1);
    assert.match(html, /<summary>Advanced<\/summary>/);
  }
});

test("Recovery Summary keeps one failure, evidence path, and primary action", async () => {
  const context = await primitivesContext();
  const kinds = [
    "question",
    "approval",
    "runtime",
    "validation",
    "intervention",
    "quality-gate",
  ];
  for (const kind of kinds) {
    const html = vm.runInContext(
      `renderRecoverySummary({
        kind: ${JSON.stringify(kind)},
        status: "blocked",
        statusLabel: "blocked",
        title: "Recovery required",
        consequence: "Progression is closed until the operator resolves this state.",
        decisiveFailure: {label: "First failure", detail: "${kind} requires attention"},
        evidence: {label: "Evidence", path: ".aidd/reports/${kind}.json"},
        primaryAction: {action: "recover-${kind}", label: "Resolve", enabled: true}
      })`,
      context,
    );
    assert.equal((html.match(/data-decisive-failure/g) || []).length, 1);
    assert.equal((html.match(/data-evidence-path/g) || []).length, 1);
    assert.equal((html.match(/data-primary-recovery-slot/g) || []).length, 1);
    assert.equal((html.match(/data-tab-shortcut="evidence"/g) || []).length, 1);
    assert.match(html, /data-decision-bar="recovery"/);
    assert.match(html, new RegExp(`data-recovery-action="recover-${kind}"`));
  }
});
