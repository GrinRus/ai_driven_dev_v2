async function refresh() {
  state.readinessLoading = true;
  state.readinessError = "";
  try {
    await fetchDashboard();
    await renderAll();
    void fetchReadiness().then(renderAll).catch((error) => {
      toast(error.message);
    });
  } catch (error) {
    document.getElementById("cockpitContent").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
  }
}

async function openFolder(payload) {
  const result = await postJson("/api/open-folder", payload);
  toast(`Opened ${result.target} folder.`);
}

async function stopServer() {
  const result = await postJson("/api/server/stop", {});
  document.getElementById("stopServerButton").disabled = true;
  toast(result.message || "Stopping local UI server.");
}

document.addEventListener("click", async (event) => {
  try {
    const stageButton = event.target.closest("[data-stage]");
    if (stageButton) {
      state.activeStage = stageButton.dataset.stage;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
      return;
    }
    const tab = event.target.closest("[data-tab]")?.dataset.tab;
    if (tab) {
      activateTab(tab);
      await renderCockpit();
      return;
    }
    const tabShortcut = event.target.closest("[data-tab-shortcut]")?.dataset.tabShortcut;
    if (tabShortcut) {
      activateTab(tabShortcut);
      await renderCockpit();
      return;
    }
    const setupModeCard = event.target.closest("[data-setup-mode]");
    if (setupModeCard) {
      const requestedMode = SETUP_MODES.find((mode) => mode.id === setupModeCard.dataset.setupMode);
      if (!requestedMode) return;
      if (requestedMode.requiresPreviousRun && !setupPreviousRunContext().available) return;
      state.setupMode = requestedMode.id;
      await renderCockpit();
      return;
    }
    const nextFlowAction = event.target.closest("[data-next-flow-action]");
    if (nextFlowAction) {
      const action = nextFlowAction.dataset.nextFlowAction;
      if (action === "create-new-work-item") {
        await openNewWorkItemHandoff();
        return;
      }
      if (action === "start-follow-up-flow") {
        await openNextFlowWizard(action);
        return;
      }
      if (action === "clone-flow") {
        await openCloneFlowDraft();
        return;
      }
      if (action === "run-eval-batch") {
        await openEvalBatchHandoff();
        return;
      }
      if (action === "archive-run") {
        await archiveCompletedRun();
        return;
      }
      toast("Unsupported next-flow action.");
      return;
    }
    const sourceSelection = event.target.closest("[data-source-selection-id]");
    if (sourceSelection) {
      setSourceFindingSelection(sourceSelection.dataset.sourceSelectionId, sourceSelection.checked);
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-close-next-flow-wizard]")) {
      state.nextFlowWizard.active = false;
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-next-flow-continue]")) {
      await loadFollowUpDraft();
      return;
    }
    if (event.target.closest("[data-next-flow-back-to-sources]")) {
      state.nextFlowWizard.step = "sources";
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-next-flow-confirm-preview]")) {
      await loadLaunchConfirmation();
      return;
    }
    if (event.target.closest("[data-next-flow-back-to-definition]")) {
      state.nextFlowWizard.step = state.nextFlowWizard.action === "clone-flow" ? "sources" : "definition";
      if (state.nextFlowWizard.action === "clone-flow") {
        state.nextFlowWizard.active = false;
      }
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-launch-flow-now]")) {
      await launchNextFlowNow();
      return;
    }
    const cancelJob = event.target.closest("[data-cancel-job]");
    if (cancelJob) {
      await cancelActiveJob();
      return;
    }
    const approvalButton = event.target.closest("[data-operator-request][data-operator-action]");
    if (approvalButton) {
      await submitApproval(approvalButton.dataset.operatorRequest, approvalButton.dataset.operatorAction);
      return;
    }
    const artifactReference = event.target.closest("[data-artifact-stage]");
    if (artifactReference) {
      await inspectArtifactReference({
        stage: artifactReference.dataset.artifactStage,
        key: artifactReference.dataset.artifactKey,
        kind: artifactReference.dataset.artifactKind
      });
      return;
    }
    const artifactKey = event.target.closest("[data-artifact-key]")?.dataset.artifactKey;
    if (artifactKey) {
      state.activeArtifactKey = artifactKey;
      state.selectedEvidenceNodeId = `document:${artifactKey}`;
      state.selectedEvidenceEdgeId = "";
      await renderArtifacts();
      return;
    }
    const evidenceNode = event.target.closest("[data-evidence-node]")?.dataset.evidenceNode;
    if (evidenceNode) {
      state.selectedEvidenceNodeId = evidenceNode;
      state.selectedEvidenceEdgeId = "";
      if (evidenceNode.startsWith("document:")) {
        state.activeArtifactKey = evidenceNode.split(":").slice(1).join(":");
      }
      await renderArtifacts();
      return;
    }
    const evidenceEdge = event.target.closest("[data-evidence-edge]")?.dataset.evidenceEdge;
    if (evidenceEdge) {
      state.selectedEvidenceEdgeId = evidenceEdge;
      state.selectedEvidenceNodeId = "";
      await renderArtifacts();
      return;
    }
    const copyArtifact = event.target.closest("[data-copy-artifact-path]")?.dataset.copyArtifactPath;
    if (copyArtifact) {
      await copyArtifactPath(copyArtifact);
      return;
    }
    const downloadButton = event.target.closest("[data-download-artifact]");
    if (downloadButton) {
      await downloadArtifact({
        path: downloadButton.dataset.downloadArtifact,
        key: downloadButton.dataset.downloadArtifactKey,
        kind: downloadButton.dataset.downloadArtifactKind,
        stage: downloadButton.dataset.downloadArtifactStage || state.activeStage
      });
      return;
    }
    const artifactMode = event.target.closest("[data-artifact-mode]")?.dataset.artifactMode;
    if (artifactMode) {
      state.artifactViewMode = artifactMode;
      if (state.activeArtifactKey) await loadArtifactDocument(state.activeArtifactKey);
      return;
    }
    const evidenceReference = event.target.closest("[data-evidence-path]");
    if (evidenceReference) {
      await inspectArtifactReference({
        stage: evidenceReference.dataset.evidenceStage,
        path: evidenceReference.dataset.evidencePath,
        kind: evidenceReference.dataset.evidenceKind
      });
      return;
    }
    const openArtifact = event.target.closest("[data-open-artifact]")?.dataset.openArtifact;
    if (openArtifact) {
      await openFolder({target: "artifact", path: openArtifact});
      return;
    }
    const openFolderTarget = event.target.closest("[data-open-folder]")?.dataset.openFolder;
    if (openFolderTarget === "workspace") {
      await openFolder({target: "workspace"});
      return;
    }
    const blockerReference = event.target.closest("[data-blocker-stage]");
    if (blockerReference) {
      state.activeStage = blockerReference.dataset.blockerStage;
      state.activeArtifactKey = "";
      const kind = blockerReference.dataset.blockerKind;
      state.activeTab = kind === "questions" ? "questions" : kind === "validation" ? "validation" : "overview";
      await fetchDashboard();
      await renderAll();
      return;
    }
    const saveAnswerButton = event.target.closest("[data-save-answer]");
    if (saveAnswerButton) {
      await saveAnswer(saveAnswerButton.dataset.saveAnswer);
      await fetchDashboard();
      await renderAll();
      return;
    }
    const answerResumeButton = event.target.closest("[data-answer-resume]");
    if (answerResumeButton) {
      await answerAndResume(answerResumeButton.dataset.answerResume);
      return;
    }
    if (event.target.id === "refreshButton") {
      await refresh();
      return;
    }
    if (event.target.id === "openWorkspaceButton") {
      await openFolder({target: "workspace"});
      return;
    }
    if (event.target.id === "openStageFolderButton") {
      await openFolder({target: "stage", stage: state.activeStage});
      return;
    }
    if (event.target.id === "stopServerButton") {
      await stopServer();
      return;
    }
    if (event.target.id === "nextActionButton") {
      await handleNextAction();
      return;
    }
    if (event.target.closest("[data-first-launch-run]")) {
      await startWorkflow();
      return;
    }
    if (event.target.id === "submitInterventionButton") {
      await submitIntervention();
      return;
    }
    if (event.target.id === "viewFullLogButton") {
      activateTab("logs");
      await renderCockpit();
      return;
    }
    const logFilter = event.target.closest("[data-log-filter]")?.dataset.logFilter;
    if (logFilter) {
      state.logFilter = logFilter;
      await renderLogs();
      return;
    }
    if (event.target.closest("[data-log-raw]")) {
      state.rawLogMode = !state.rawLogMode;
      await renderLogs();
      return;
    }
    if (event.target.closest("[data-answer-resume-all]")) {
      await resumeAfterAnswers();
      return;
    }
    if (event.target.closest("[data-run-repair]")) {
      await startStage(state.activeStage);
      return;
    }
    if (event.target.closest("[data-stop-run]")) {
      if (state.activeJobId) {
        await cancelActiveJob();
      } else {
        toast("Stop Run requires an active UI-started job.");
      }
    }
  } catch (error) {
    toast(error.message);
  }
});

document.addEventListener("change", async (event) => {
  if (event.target.id === "runtimeSelect") {
    state.selectedRuntime = event.target.value;
    setRunButtonState();
    updateSubmitInterventionState();
    renderTopbar();
    renderSidebar();
    if (state.activeTab === "overview") await renderCockpit();
  }
  if (event.target.closest("[data-intervention-target]")) {
    updateInterventionPreview();
  }
});

document.addEventListener("input", (event) => {
  if (event.target.id === "operatorRequestText") {
    updateInterventionPreview();
  }
});

refresh();
