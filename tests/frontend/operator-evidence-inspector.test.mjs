import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-artifacts-documents.js");

async function inspectorContext() {
  const context = vm.createContext({
    console,
    state: {activeStage: "qa"},
    escapeHtml(value) { return String(value ?? ""); },
    compactPath(value) { return String(value); },
    pathLine(value) { return `<code>${value}</code>`; },
    renderMarkdown(value) { return String(value); },
    resolveStudioEvidenceVisibility({inspectorDecisionValue}) {
      return {inspector: Boolean(inspectorDecisionValue)};
    },
    statusClass() { return ""; },
  });
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return context;
}

test("Evidence Inspector hides when the selected document has no retained evidence", async () => {
  const context = await inspectorContext();
  context.workbench = {};
  assert.equal(vm.runInContext("renderStudioEvidenceInspector(workbench)", context), "");
});

test("Evidence Inspector explains the purpose of findings, contracts, provenance, and related evidence", async () => {
  const context = await inspectorContext();
  context.workbench = {
    attempt_number: 2,
    validation_results: [{status: "failed", label: "SEM-RISK", detail: "Risk is unowned", path: "qa/validator-report.md"}],
    requirements: [
      {status: "present", label: "QA report", kind: "required-section", source: "document-contract", path: "qa/qa-report.md"},
      {status: "missing", label: "Validator report", kind: "required-output", source: "stage-contract", path: "qa/validator-report.md"},
    ],
    versions: [
      {label: "Attempt 1", source: "model-authored", attempt_number: 1, path: "reports/runs/run/stages/qa/attempt-1/qa-report.md"},
      {label: "Attempt 2", source: "stage-attempt", attempt_number: 2, path: "reports/runs/run/stages/qa/attempt-2/qa-report.md"},
    ],
    references: [{label: "runtime_log", kind: "log", path: "reports/runs/run/stages/qa/attempt-2/runtime.log"}],
  };
  const html = vm.runInContext("renderStudioEvidenceInspector(workbench)", context);
  for (const section of ["findings", "source-references", "provenance", "related-artifacts"]) {
    assert.match(html, new RegExp(`data-inspector-section="${section}"`));
  }
  for (const value of ["SEM-RISK", "document-contract", "Attempt 2", "runtime_log", "Needs attention", "What this document must satisfy", "Where this version came from", "Related evidence"]) {
    assert.match(html, new RegExp(value));
  }
  assert.match(html, /These facts can change whether the document is safe to rely on/);
  assert.match(html, /without leaving the reader/);
  assert.match(html, /Why: Needed to assess confidence in this retained copy before relying on it/);
  assert.match(html, /Why: Needed so this document has the structure required by its contract/);
  assert.match(html, /Why: Compare this earlier copy to understand what changed after retry or repair/);
});
