import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-artifacts-documents.js");

async function navigatorContext() {
  const context = vm.createContext({
    console,
    state: {activeStage: "qa", artifactViewMode: "preview"},
    escapeHtml(value) { return String(value ?? "").replace(/[&<>\"]/g, (character) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;",
    })[character]); },
    compactPath(value) { return String(value); },
    pathLine(value) { return `<code>${value}</code>`; },
    renderMarkdown(value) { return String(value); },
    resolveStudioEvidenceVisibility() { return {inspector: false}; },
    statusClass() { return ""; },
  });
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return context;
}

const workbench = {
  stage: "qa",
  attempt_number: 3,
  selected_key: "qa_report",
  document: {
    status: "present",
    key: "qa_report",
    path: "workitems/WI/stages/qa/qa-report.md",
    byte_size: 80,
    preview: {text: "# QA\n\n## Verdict\npass", content_type: "text/markdown", truncated: false},
  },
  references: [
    {label: "qa_report", kind: "document", path: "workitems/WI/stages/qa/qa-report.md", stage: "qa", category: "canonical-stage-document"},
    {label: "questions", kind: "document", path: "workitems/WI/stages/qa/questions.md", stage: "qa", category: "runtime-input"},
    {label: "validator_report", kind: "document", path: "workitems/WI/stages/qa/validator-report.md", stage: "qa", category: "validation-evidence"},
    {label: "stage_brief", kind: "document", path: "workitems/WI/stages/qa/stage-brief.md", stage: "qa", category: "runtime-input"},
    {label: "runtime_log", kind: "log", path: "reports/run/stages/qa/runtime.log", stage: "qa", category: "runtime-evidence"},
  ],
};

test("Document navigator renders the five role groups and bounded provenance", async () => {
  const context = await navigatorContext();
  context.workbench = workbench;
  const html = vm.runInContext("renderWorkbenchTree(workbench)", context);
  for (const role of ["Output", "Questions", "Validation", "Inputs", "Evidence"]) {
    assert.match(html, new RegExp(role));
  }
  for (const value of ["qa-report.md", "qa · Attempt 3", "Bounded read", "Canonical stage document", "data-document-role=\"output\""]) {
    assert.match(html, new RegExp(value));
  }
  assert.doesNotMatch(html, /Write|Edit/);
});

test("Document reader reports empty, missing, malformed, permission, and truncated states with one safe action", async () => {
  const context = await navigatorContext();
  for (const [status, message, expected] of [
    ["missing", "file does not exist", "Document missing"],
    ["invalid", "not UTF-8 text", "Document malformed or unreadable"],
    ["invalid", "Permission denied", "Document permission denied"],
  ]) {
    const candidate = {selected_key: "doc", document: {status, message, path: "workitems/WI/doc.md"}};
    context.workbench = candidate;
    const html = vm.runInContext("renderWorkbenchDocumentBody(workbench)", context);
    assert.match(html, new RegExp(expected));
    assert.equal((html.match(/data-reader-next-action=/g) || []).length, 1);
    assert.match(html, /Open folder/);
  }
  context.workbench = {selected_key: "doc", document: {status: "present", path: "workitems/WI/doc.md", preview: {text: "", truncated: false}}};
  let html = vm.runInContext("renderWorkbenchDocumentBody(workbench)", context);
  assert.match(html, /Document is empty/);
  assert.equal((html.match(/data-reader-next-action=/g) || []).length, 1);
  context.workbench = {selected_key: "doc", document: {status: "present", path: "workitems/WI/doc.md", preview: {text: "# bounded", truncated: true, byte_size: 10, start_byte: 0, end_byte: 10}}};
  html = vm.runInContext("renderWorkbenchDocumentBody(workbench)", context);
  assert.match(html, /Artifact view truncated/);
});

test("Reading brief includes role, stage/attempt, bounded state, and source of truth", async () => {
  const context = await navigatorContext();
  context.workbench = workbench;
  const html = vm.runInContext("renderDocumentReadingBrief(workbench)", context);
  for (const value of ["Role", "Output", "Stage / attempt", "qa / 3", "Bounded state", "Source of truth"]) {
    assert.match(html, new RegExp(value));
  }
});
