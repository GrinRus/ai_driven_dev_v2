import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-artifacts-documents.js");

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;",
  })[character]);
}

async function canvasContext() {
  const context = vm.createContext({
    console,
    state: {activeStage: "qa", artifactViewMode: "preview"},
    escapeHtml,
    compactPath(value) { return String(value); },
    pathLine(value) { return `<code>${escapeHtml(value)}</code>`; },
    renderMarkdown(value) { return `<div data-markdown>${escapeHtml(value)}</div>`; },
    resolveStudioEvidenceVisibility() { return {inspector: false}; },
    statusClass() { return ""; },
  });
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return context;
}

const workbench = {
  selected_key: "qa_report",
  document: {
    status: "present",
    key: "qa_report",
    path: "workitems/WI/stages/qa/qa-report.md",
    byte_size: 140,
    preview: {text: "# QA\nPreview", content_type: "text/markdown", truncated: false},
    source: {text: "# QA\nFull source", content_type: "text/markdown", truncated: true, byte_size: 140},
  },
  diff_inputs: [{label: "attempt 1", path: "reports/runs/run/stages/qa/attempt-1/qa-report.md", kind: "attempt"}],
};

test("Document Canvas renders Preview, Source, and Diff from one workbench model", async () => {
  const context = await canvasContext();
  for (const [mode, expected] of [
    ["preview", "Preview"],
    ["source", "Full source"],
    ["diff", "attempt 1"],
  ]) {
    context.workbench = workbench;
    const html = vm.runInContext(
      `state.artifactViewMode = ${JSON.stringify(mode)}; renderStudioDocumentCanvas(workbench)`,
      context,
    );
    assert.match(html, new RegExp(`data-document-canvas-mode="${mode}"`));
    assert.match(html, new RegExp(expected));
    assert.match(html, new RegExp(`data-artifact-mode="${mode}" class=" active"`));
  }
});

test("Document Canvas fails visibly for missing documents and escapes unsafe keys", async () => {
  const context = await canvasContext();
  context.workbench = {
    selected_key: '<script data-bad="1">',
    document: {status: "missing", message: "Canonical document is missing"},
    diff_inputs: [],
  };
  const html = vm.runInContext("renderStudioDocumentCanvas(workbench)", context);
  assert.match(html, /Canonical document is missing/);
  assert.doesNotMatch(html, /<script data-bad/);
  assert.match(html, /&lt;script data-bad=&quot;1&quot;&gt;/);
});

test("bounded Source keeps explicit truncation semantics", async () => {
  const context = await canvasContext();
  context.workbench = workbench;
  const html = vm.runInContext(
    'state.artifactViewMode = "source"; renderStudioDocumentCanvas(workbench)',
    context,
  );
  assert.match(html, /bounded/);
  assert.match(html, /Open the folder for the full file/);
});
