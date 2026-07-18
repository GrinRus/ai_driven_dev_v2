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
    resolveStudioEvidenceVisibility({inspectorItemCount}) {
      return {inspector: Number(inspectorItemCount) > 0};
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

test("Evidence Inspector keeps findings, provenance, artifacts, and exact sources separate", async () => {
  const context = await inspectorContext();
  context.workbench = {
    validation_results: [{status: "failed", label: "SEM-RISK", detail: "Risk is unowned", path: "qa/validator-report.md"}],
    requirements: [{status: "present", label: "QA report", kind: "contract", source: "contracts/stages/qa.md", path: "qa/qa-report.md"}],
    versions: [{label: "attempt 2", source: "stage-attempt", attempt_number: 2, path: "reports/runs/run/stages/qa/attempt-2/qa-report.md"}],
    references: [{label: "runtime_log", kind: "log", path: "reports/runs/run/stages/qa/attempt-2/runtime.log"}],
  };
  const html = vm.runInContext("renderStudioEvidenceInspector(workbench)", context);
  for (const section of ["findings", "source-references", "provenance", "related-artifacts"]) {
    assert.match(html, new RegExp(`data-inspector-section="${section}"`));
  }
  for (const value of ["SEM-RISK", "contracts/stages/qa.md", "attempt 2", "runtime_log"]) {
    assert.match(html, new RegExp(value));
  }
});
