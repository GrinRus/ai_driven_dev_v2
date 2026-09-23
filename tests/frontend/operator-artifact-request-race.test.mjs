import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import {fileURLToPath} from "node:url";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const artifactSource = path.join(repositoryRoot, "src/aidd/cli/static/operator-artifacts-documents.js");

function deferred() {
  let resolve;
  const promise = new Promise((resolver) => {
    resolve = resolver;
  });
  return {promise, resolve};
}

test("late artifact document response cannot replace a newer document selection", async () => {
  const elements = new Map([
    ["workbenchTree", {id: "workbenchTree", innerHTML: ""}],
    ["studioDocumentCanvas", {id: "studioDocumentCanvas", innerHTML: ""}],
  ]);
  const requests = [];
  const applied = [];
  const context = vm.createContext({
    AbortController,
    URLSearchParams,
    console,
    document: {
      getElementById(id) {
        return elements.get(id) || null;
      },
    },
    state: {
      activeRunId: "run-old",
      activeStage: "qa",
      activeArtifactKey: "old-report",
      artifactRequestGeneration: 0,
      artifactWorkbenchRequestGeneration: 0,
      artifactWorkbenchAbortController: null,
      artifactGraphRequestGeneration: 0,
      activeArtifactComparison: null,
      activeArtifactWorkbench: null,
      activeStudioWorkbench: null,
    },
  });
  vm.runInContext(await readFile(artifactSource, "utf8"), context, {filename: artifactSource});
  context.api = (url) => {
    const pending = deferred();
    requests.push({url, pending});
    return pending.promise;
  };
  context.renderLoadedArtifactDocument = (workbench) => {
    applied.push(workbench.selected_key);
  };

  const oldRequest = vm.runInContext('loadArtifactDocument("old-report")', context);
  vm.runInContext('state.activeArtifactKey = "new-report"', context);
  const newRequest = vm.runInContext('loadArtifactDocument("new-report")', context);
  assert.equal(requests.length, 2);

  requests[0].pending.resolve({selected_key: "old-report", document: {status: "present"}});
  await oldRequest;
  assert.deepEqual(applied, []);

  requests[1].pending.resolve({selected_key: "new-report", document: {status: "present"}});
  await newRequest;
  assert.deepEqual(applied, ["new-report"]);
});
