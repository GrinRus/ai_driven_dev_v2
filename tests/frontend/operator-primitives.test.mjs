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
