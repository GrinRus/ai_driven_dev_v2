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
