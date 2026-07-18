import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-shell-rendering.js");

async function readinessContext() {
  const context = vm.createContext({
    console,
    state: {readiness: {}},
    escapeHtml(value) { return String(value ?? ""); },
    compactPath(value) { return String(value); },
  });
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return context;
}

test("runtime presentation keeps binary, command, authentication, and capability dimensions separate", async () => {
  const context = await readinessContext();
  context.runtime = {
    binary: {status: "detected", version: "1.2.3"},
    execution_command: {status: "available", source: "config"},
    authentication: {status: "unverified", detail: "provider does not expose auth state"},
    capabilities: {
      status: "known", preferred_transport: "subprocess",
      supports_raw_log_stream: true, supports_questions: false,
      supports_permission_policy: true, supports_live_decisions: false,
    },
    latest_launch: {
      outcome: "timeout", recorded_at_utc: "2026-07-18T10:00:00Z",
      stage: "plan", attempt_number: 2,
    },
  };
  const html = vm.runInContext("renderRuntimeReadinessDimensions(runtime)", context);
  for (const value of [
    "Binary", "detected / 1.2.3", "Execution command", "available / config",
    "Authentication evidence", "unverified", "Adapter capabilities",
    "transport subprocess", "Latest launch", "timeout / 2026-07-18T10:00:00Z / plan attempt 2",
  ]) {
    assert.match(html, new RegExp(value));
  }
  assert.doesNotMatch(html, />ready</);
});

test("protected write scope distinguishes bounded, invalid, and not-authored states", async () => {
  const context = await readinessContext();
  for (const scope of [
    {status: "bounded", prefixes: ["src", "tests"], source_path: "workitems/WI/context/allowed-write-scope.md", message: "bounded"},
    {status: "invalid", prefixes: [], source_path: "workitems/WI/context/allowed-write-scope.md", message: "invalid document"},
    {status: "not-authored", prefixes: [], source_path: null, message: "not authored"},
  ]) {
    context.scope = scope;
    const html = vm.runInContext("renderProtectedWriteScope(scope)", context);
    assert.match(html, new RegExp(`data-protected-write-scope="${scope.status}"`));
    assert.match(html, /Protected write scope/);
    assert.doesNotMatch(html, /No upstream write/);
  }
});
