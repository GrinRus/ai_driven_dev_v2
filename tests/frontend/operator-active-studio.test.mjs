import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const staticRoot = path.join(repositoryRoot, "src/aidd/cli/static");

async function contextFor(dashboard) {
  const context = vm.createContext({
    console,
    state: {dashboard, activeStage: "idea", nextFlowWizard: {active: false}},
    escapeHtml(value) { return String(value ?? ""); },
    stageTitle(stage) { return stage.toUpperCase(); },
    stageSubtitle() { return "Clarify the request"; },
    activeStageItem() { return dashboard.stages?.[0] || null; },
    activeStageView() { return dashboard.active_stage_view || null; },
    selectedRuntimeView() { return null; },
    renderRuntimeReadinessDimensions() { return ""; },
    renderProtectedWriteScope() { return ""; },
    pathLine(value) { return `<code>${value}</code>`; },
    renderPrimaryArtifact() { return "<div data-document>document</div>"; },
    renderStateSurface({title}) { return `<div data-state-surface>${title}</div>`; },
    studioFlowCompleteEligibility() { return {eligible: false}; },
  });
  const source = await readFile(path.join(staticRoot, "operator-active-studio.js"), "utf8");
  vm.runInContext(source, context, {filename: "operator-active-studio.js"});
  return context;
}

test("active Studio preserves work item, run, stage, and status context", async () => {
  const context = await contextFor({
    work_item: "WI-1",
    run: {run_id: "run-1"},
    stages: [{stage: "idea", status: "executing", subtitle: "Clarify", attempt_count: 1}],
  });
  const html = vm.runInContext("renderActiveStudio()", context);
  assert.match(html, /data-studio-surface="active-studio"/);
  assert.match(html, /data-state="active"/);
  for (const value of ["WI-1", "run-1", "idea", "Stage running"]) {
    assert.match(html, new RegExp(value));
  }
  assert.doesNotMatch(html, /data-primary-action/);
});

test("no-run, blocked, and terminal Studio states do not invent primary actions", async () => {
  const dashboards = [
    {work_item: "WI-1", run: null, stages: []},
    {work_item: "WI-1", run: {run_id: "run-1"}, stages: [{status: "blocked"}]},
    {
      work_item: "WI-1", run: {run_id: "run-1"}, stages: [{status: "succeeded"}],
      terminal_handoff: {status: "completed", final_qa_status: "ready"},
    },
  ];
  const states = [];
  for (const dashboard of dashboards) {
    const context = await contextFor(dashboard);
    const html = vm.runInContext("renderActiveStudio()", context);
    states.push(html.match(/data-state="([^"]+)"/)?.[1]);
    assert.doesNotMatch(html, /data-primary-action/);
  }
  assert.deepEqual(states, ["no-run", "blocked", "terminal"]);
});
