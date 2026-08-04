import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-artifacts-documents.js");

test("flat evidence-graph fallback still opens the indexed document reader", async () => {
  const content = {innerHTML: ""};
  const context = vm.createContext({
    console,
    URLSearchParams,
    state: {
      activeStage: "qa",
      activeRunId: "run-1",
      activeArtifactKey: "",
      selectedEvidenceNodeId: "",
      selectedEvidenceEdgeId: "",
    },
    document: {getElementById(id) { return id === "cockpitContent" ? content : null; }},
    activeStageItem() { return {attempt_count: 1}; },
    escapeHtml(value) { return String(value ?? ""); },
    compactPath(value) { return String(value); },
    pathLine(value) { return String(value); },
    renderMarkdown(value) { return String(value); },
    resolveStudioEvidenceVisibility() { return {inspector: false}; },
    statusClass() { return ""; },
  });
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});

  let openedKey = "";
  context.api = async () => ({
    mode: "flat-table",
    incomplete_reasons: ["artifact-index-incomplete"],
    nodes: [],
    edges: [],
    artifact_table: [
      {kind: "document", key: "qa_report", path: "workitems/WI/stages/qa/qa-report.md"},
    ],
  });
  context.renderEvidenceGraphScreen = () => '<section data-flat-reader-shell></section>';
  context.loadArtifactDocument = async (key) => { openedKey = key; };

  await vm.runInContext("renderArtifacts()", context);

  assert.equal(openedKey, "qa_report");
  assert.equal(context.state.activeArtifactKey, "qa_report");
  assert.match(content.innerHTML, /data-flat-reader-shell/);
});
