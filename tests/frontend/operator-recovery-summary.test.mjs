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

test("repair-extension recovery is rendered from core eligibility and keeps alternatives distinct", async () => {
  const source = await readFile(cockpitPath, "utf8");
  assert.match(source, /function renderRepairExtensionPreview\(validation\)/);
  assert.match(source, /validation\?\.repair_extension/);
  assert.match(source, /preview\.eligible === true/);
  assert.match(source, /Run one more repair/);
  assert.match(source, /data-recovery-action="repair-extension"/);
  assert.match(source, /data-repair-extension/);
  assert.match(source, /Request Change/);
  assert.match(source, /Start new run/);
  assert.match(source, /automatic_repair_attempts_used/);
  assert.match(source, /validator_report_sha256/);
  assert.match(source, /repair_brief_sha256/);
});
