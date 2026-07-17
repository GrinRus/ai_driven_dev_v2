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
