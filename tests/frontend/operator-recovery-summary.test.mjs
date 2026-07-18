import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const cockpitPath = path.join(repositoryRoot, "src/aidd/cli/static/operator-stage-cockpit.js");

test("Studio recovery has one canonical summary and a navigation-only sidebar", async () => {
  const source = await readFile(cockpitPath, "utf8");
  const workbenchStart = source.indexOf("function renderRecoveryWorkbench()");
  const workbenchEnd = source.indexOf("function renderBlockedStageRecovery", workbenchStart);
  const workbench = source.slice(workbenchStart, workbenchEnd);
  assert.equal((workbench.match(/renderRecoverySummary\(/g) || []).length, 1);
  assert.doesNotMatch(workbench, /recovery-hero|recoveryPrimaryActionButton/);
  assert.match(workbench, /evidence: \{label: runtimeFailure \? "Runtime log" : "Supporting evidence", path: evidencePath\}/);

  const sidebarStart = source.indexOf("function renderRecoveryAssistantPanel()");
  const sidebarEnd = source.indexOf("function renderRuntimeRootPanel", sidebarStart);
  const sidebar = source.slice(sidebarStart, sidebarEnd);
  assert.match(sidebar, /Open Recovery Summary/);
  assert.doesNotMatch(sidebar, /recovery-card|data-recovery-action/);
  assert.doesNotMatch(source, /function renderRecoveryScreen\(/);
});
