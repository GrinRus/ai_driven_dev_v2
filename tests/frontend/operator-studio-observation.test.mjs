import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const sourcePath = path.join(repositoryRoot, "src/aidd/cli/static/operator-active-studio.js");

async function observationContext(item, job = null) {
  const context = vm.createContext({
    console,
    state: {
      activeStage: "idea",
      activeJobStatus: job,
      activeJobConnection: {state: "online"},
    },
    activeStageItem() { return item; },
    stageTitle(stage) { return stage.toUpperCase(); },
    secondsLabel(value) { return value == null ? "not available" : `${value}s`; },
    runtimeOutputFreshnessLabel(value) { return value.runtime_output_age_seconds == null ? "No runtime output captured yet" : `Last runtime output ${value.runtime_output_age_seconds}s ago`; },
    runtimeOutputMissingLabel(value) { return `No runtime output for ${value.elapsed_seconds}s`; },
    escapeHtml(value) { return String(value ?? ""); },
  });
  vm.runInContext(await readFile(sourcePath, "utf8"), context, {filename: sourcePath});
  return context;
}

test("Studio observation reports running, silence, and cancellation without fake progress", async () => {
  const jobs = [
    {status: "running", stage: "idea", elapsed_seconds: 12, runtime_output_age_seconds: 2},
    {status: "running", stage: "idea", elapsed_seconds: 140, silence_warning: true},
    {status: "cancelling", stage: "idea", elapsed_seconds: 20, cancel_state: "cancelling"},
  ];
  const expected = ["Live runtime evidence is updating", "No runtime output for 140s", "Cancellation requested"];
  for (let index = 0; index < jobs.length; index += 1) {
    const context = await observationContext({stage: "idea", status: "executing", attempt_count: 1}, jobs[index]);
    const html = vm.runInContext("renderStudioLiveObservation()", context);
    assert.match(html, new RegExp(expected[index]));
    assert.match(html, /Open live output/);
    assert.doesNotMatch(html, /%|percent|estimated/);
  }
});

test("completed and externally running observations come only from durable stage state", async () => {
  const cases = [
    [{stage: "idea", status: "succeeded", attempt_count: 2}, "durable-attempt", "Open persisted logs"],
    [{stage: "idea", status: "executing", attempt_count: 1}, "durable-external", "outside this browser session"],
  ];
  for (const [item, source, expected] of cases) {
    const context = await observationContext(item);
    const html = vm.runInContext("renderStudioLiveObservation()", context);
    assert.match(html, new RegExp(`data-studio-observation="${source}"`));
    assert.match(html, new RegExp(expected));
    assert.match(html, /attempt [12]/);
  }
});
