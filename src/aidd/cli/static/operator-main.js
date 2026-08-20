async function refresh() {
  state.readinessLoading = true;
  state.readinessError = "";
  try {
    await fetchOnboardingState();
    if (state.onboarding.setupRequired) {
      state.dashboard = null;
      await renderOnboarding();
      return;
    }
    document.body.classList.remove("setup-active");
    document.getElementById("openWorkspaceButton").disabled = false;
    let selectedWorkItem = state.onboarding.contextWorkItem;
    const route = decodeOperatorRoute(window.location.search).value;
    let routeRestoreError = "";
    if (
      route.mode !== "inbox"
      && route.workItem
      && route.workItem !== selectedWorkItem
    ) {
      try {
        // A non-Inbox deep link is an explicit context request. After a server
        // restart the service intentionally starts project-only, so restore
        // this known intent through the same guarded Inbox resume endpoint.
        await postJson("/api/onboarding/work-item", {
          action: "resume",
          project_root: state.onboarding.projectRootInput || ".",
          work_item: route.workItem
        });
        await fetchOnboardingState();
        selectedWorkItem = state.onboarding.contextWorkItem;
        if (selectedWorkItem !== route.workItem) {
          throw new Error("The requested Work Item was not restored.");
        }
      } catch (error) {
        routeRestoreError = error.message || "The requested Work Item could not be restored.";
      }
    }
    if (!selectedWorkItem || routeRestoreError) {
      // An existing project is useful before an operator chooses an intent:
      // keep the first view at the Inbox instead of inventing a Studio context.
      state.dashboard = null;
      state.dashboardActiveJob = null;
      state.activeRunId = "";
      state.activeRouteWorkItem = "";
      state.readinessLoading = false;
      state.readinessError = "";
      state.readiness = {runtimes: []};
      setOperatorMode("project-home");
      await Promise.all([fetchProjectHome(), fetchInbox()]);
      await renderAll();
      if (routeRestoreError) toast(routeRestoreError);
      return;
    }
    if (!new URLSearchParams(window.location.search).has("mode")) {
      // --work-item is an explicit Studio deep link; a bare existing project
      // above remains an Inbox route.
      state.activeRouteWorkItem = selectedWorkItem;
      setOperatorMode("work");
    }
    await fetchDashboard();
    await fetchProjectHome(state.dashboard?.work_item || "");
    await fetchInbox();
    await renderAll();
    void fetchReadiness().then((accepted) => {
      if (accepted) renderReadinessSurfaces();
    });
  } catch (error) {
    document.getElementById("intentContent").innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
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

function orderedTabButtons() {
  return [...document.querySelectorAll("[data-tab]")].filter((button) =>
    VALID_TABS.includes(button.dataset.tab || "") && !button.hidden
  );
}

function orderedWorkItemTabButtons() {
  return [...document.querySelectorAll("[data-work-item-tab]")].filter((button) => !button.hidden);
}

async function moveWorkItemTabFocus(currentButton, offset) {
  const buttons = orderedWorkItemTabButtons();
  const currentIndex = buttons.indexOf(currentButton);
  if (currentIndex < 0 || buttons.length === 0) return;
  const nextButton = buttons[(currentIndex + offset + buttons.length) % buttons.length];
  activateWorkItemTab(nextButton.dataset.workItemTab);
  await renderAll();
  document.querySelector(`[data-work-item-tab="${CSS.escape(nextButton.dataset.workItemTab)}"]`)?.focus();
}

async function focusWorkItemTabAtIndex(index) {
  const buttons = orderedWorkItemTabButtons();
  const nextButton = buttons[index];
  if (!nextButton) return;
  activateWorkItemTab(nextButton.dataset.workItemTab);
  await renderAll();
  document.querySelector(`[data-work-item-tab="${CSS.escape(nextButton.dataset.workItemTab)}"]`)?.focus();
}

async function moveTabFocus(currentButton, offset) {
  const buttons = orderedTabButtons();
  const currentIndex = buttons.indexOf(currentButton);
  if (currentIndex < 0 || buttons.length === 0) return;
  const nextButton = buttons[(currentIndex + offset + buttons.length) % buttons.length];
  activateTab(nextButton.dataset.tab);
  await renderCockpit();
  nextButton.focus();
}

async function focusTabAtIndex(index) {
  const buttons = orderedTabButtons();
  const nextButton = buttons[index];
  if (!nextButton) return;
  activateTab(nextButton.dataset.tab);
  await renderCockpit();
  nextButton.focus();
}

document.addEventListener("keydown", async (event) => {
  const currentWorkItemTab = event.target.closest?.("[data-work-item-tab]");
  if (currentWorkItemTab) {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      await moveWorkItemTabFocus(currentWorkItemTab, 1);
      return;
    }
    if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      await moveWorkItemTabFocus(currentWorkItemTab, -1);
      return;
    }
    if (event.key === "Home") {
      event.preventDefault();
      await focusWorkItemTabAtIndex(0);
      return;
    }
    if (event.key === "End") {
      event.preventDefault();
      await focusWorkItemTabAtIndex(orderedWorkItemTabButtons().length - 1);
      return;
    }
  }
  const currentTab = event.target.closest?.("[data-tab]");
  if (!currentTab) return;
  if (event.key === "ArrowRight" || event.key === "ArrowDown") {
    event.preventDefault();
    await moveTabFocus(currentTab, 1);
    return;
  }
  if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
    event.preventDefault();
    await moveTabFocus(currentTab, -1);
    return;
  }
  if (event.key === "Home") {
    event.preventDefault();
    await focusTabAtIndex(0);
    return;
  }
  if (event.key === "End") {
    event.preventDefault();
    await focusTabAtIndex(orderedTabButtons().length - 1);
  }
});

document.addEventListener("click", async (event) => {
  try {
    if (event.target.closest("[data-request-preview]")) {
      previewOperatorRequest();
      return;
    }
    if (event.target.closest("[data-request-write]")) {
      await writeOperatorRequest();
      return;
    }
    if (event.target.closest("[data-open-runner]")) {
      focusRuntimeSelector();
      return;
    }
    const stateRecovery = event.target.closest("[data-state-recovery]")?.dataset.stateRecovery;
    if (stateRecovery === "reconnect-live-job") {
      await reconnectActiveJob();
      return;
    }
    if (stateRecovery === "refresh-expired-job") {
      await refresh();
      return;
    }
    const routeTarget = event.target.closest("[data-operator-route-intent]");
    if (routeTarget) {
      const intent = routeTarget.dataset.operatorRouteIntent;
      const context = {
        workItem: routeTarget.dataset.routeWorkItem,
        runId: routeTarget.dataset.routeRunId,
        stage: routeTarget.dataset.routeStage,
        artifact: routeTarget.dataset.routeArtifact
      };
      if (intent === "inbox-work-item") await activateInboxWorkItemRoute(context);
      else await navigateOperatorRouteIntent(intent, context);
      return;
    }
    if (event.target.closest("[data-new-work-item]")) {
      await openProjectWorkItemCreation();
      return;
    }
    if (event.target.closest("[data-cancel-new-work-item]")) {
      await closeProjectWorkItemCreation();
      return;
    }
    if (event.target.closest("[data-guided-delivery-toggle]")) {
      setGuidedDeliveryPreference(state.onboarding.guidedDelivery === false);
      return;
    }
    const onboardingRecentProject = event.target.closest("[data-onboarding-recent-project]")?.dataset.onboardingRecentProject;
    if (onboardingRecentProject) {
      state.onboarding.projectRootInput = onboardingRecentProject;
      await inspectOnboardingProject();
      return;
    }
    const onboardingRuntime = event.target.closest("[data-onboarding-runtime]")?.dataset.onboardingRuntime;
    if (onboardingRuntime) {
      state.selectedRuntime = onboardingRuntime;
      renderOnboarding();
      return;
    }
    if (event.target.id === "onboardingValidateProjectSet") {
      await validateOnboardingProjectSet();
      return;
    }
    if (event.target.closest("[data-project-set-add]")) {
      addProjectSetRow();
      return;
    }
    const projectSetRemove = event.target.closest("[data-project-set-remove]")?.dataset.projectSetRemove;
    if (projectSetRemove !== undefined) {
      removeProjectSetRow(Number(projectSetRemove));
      return;
    }
    const onboardingResume = event.target.closest("[data-onboarding-resume]")?.dataset.onboardingResume;
    if (onboardingResume) {
      await completeOnboardingWorkItem("resume", onboardingResume);
      return;
    }
    const stageButton = event.target.closest("[data-stage]");
    if (stageButton) {
      state.activeStage = stageButton.dataset.stage;
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      if (state.activeTab === "work") state.workDetail = "overview";
      syncLocationState({historyMode: "push"});
      await fetchDashboard();
      await fetchProjectHome(state.dashboard?.work_item || "");
      await fetchInbox();
      await renderAll();
      return;
    }
    const stageRecovery = event.target.closest("[data-stage-recovery]");
    if (stageRecovery) {
      activateTab(stageRecovery.dataset.stageRecovery || "recovery", {historyMode: "push"});
      renderProjectHomeRail();
      await renderCockpit();
      return;
    }
    const projectHomeResume = event.target.closest("[data-project-home-resume]")?.dataset.projectHomeResume;
    if (projectHomeResume) {
      await resumeProjectHomeWorkItem(projectHomeResume);
      return;
    }
    const projectHomeRun = event.target.closest("[data-project-home-open-run]")?.dataset.projectHomeOpenRun;
    if (projectHomeRun) {
      await resumeProjectHomeWorkItem(projectHomeRun, {openLatestRun: true});
      return;
    }
    const tab = event.target.closest("[data-tab]")?.dataset.tab;
    if (tab) {
      activateTab(tab, {historyMode: "push"});
      renderProjectHomeRail();
      await renderCockpit();
      return;
    }
    const workItemTab = event.target.closest("[data-work-item-tab]")?.dataset.workItemTab;
    if (workItemTab) {
      activateWorkItemTab(workItemTab, {historyMode: "push"});
      await renderAll();
      document.querySelector(`[data-work-item-tab="${CSS.escape(workItemTab)}"]`)?.focus();
      return;
    }
    const taskSelection = event.target.closest("[data-task-select]")?.dataset.taskSelect;
    if (taskSelection) {
      state.selectedTaskId = taskSelection;
      syncLocationState({historyMode: "push"});
      await renderCockpit();
      document.querySelector(`[data-task-select="${CSS.escape(taskSelection)}"]`)?.focus();
      return;
    }
    const taskAction = event.target.closest("[data-task-action]");
    if (taskAction) {
      const action = taskAction.dataset.taskAction;
      if (action === "run" || action === "resume") {
        await startImplementationTask(taskAction.dataset.taskActionId);
      } else if (action === "finalize") {
        await startTaskFinalization();
      }
      return;
    }
    const tabShortcut = event.target.closest("[data-tab-shortcut]")?.dataset.tabShortcut;
    if (tabShortcut) {
      activateTab(tabShortcut, {historyMode: "push"});
      if (tabShortcut === "project-home") await fetchInbox();
      renderProjectHomeRail();
      await renderCockpit();
      if (tabShortcut === "project-home") {
        const primaryInboxAction = document.querySelector(
          '[data-inbox-section="needs-input"] [data-inbox-action], [data-inbox-action]'
        );
        primaryInboxAction?.focus({preventScroll: true});
        const revealInboxStart = () => {
          document.querySelector("#operatorWorkspace")?.scrollTo({top: 0, behavior: "auto"});
          window.scrollTo({top: 0, behavior: "auto"});
        };
        revealInboxStart();
        window.requestAnimationFrame(revealInboxStart);
      }
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
        await openArchiveConfirmation();
        return;
      }
      toast("Unsupported next-flow action.");
      return;
    }
    const historyFrame = event.target.closest("[data-history-frame]")?.dataset.historyFrame;
    if (historyFrame) {
      state.historySelectedFrame = historyFrame;
      state.historyAutoFollow = false;
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-history-return-live]")) {
      state.historySelectedFrame = "";
      state.historyAutoFollow = true;
      await renderCockpit();
      return;
    }
    const historyEvidence = event.target.closest("[data-history-evidence-path]");
    if (historyEvidence) {
      state.activeStage = historyEvidence.dataset.historyEvidenceStage || state.activeStage;
      const path = historyEvidence.dataset.historyEvidencePath || "";
      activateTab(path.endsWith("runtime.log") ? "logs" : "artifacts");
      await renderCockpit();
      return;
    }
    const sourceSelectionMode = event.target.closest("[data-source-selection-mode]")?.dataset.sourceSelectionMode;
    if (sourceSelectionMode) {
      selectSourceFindings(sourceSelectionMode);
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-close-next-flow-wizard]")) {
      state.nextFlowWizard.active = false;
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-archive-confirm]")) {
      await archiveCompletedRun();
      return;
    }
    if (event.target.closest("[data-next-flow-continue]")) {
      await loadFollowUpDraft();
      return;
    }
    if (event.target.closest("[data-next-flow-back-to-sources]")) {
      persistNextFlowBrowserDraft();
      state.nextFlowWizard.step = "sources";
      requestNextFlowWizardReveal();
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-run-comparison-refresh]")) {
      await loadRunComparisonPanel();
      return;
    }
    if (event.target.closest("[data-next-flow-confirm-preview]")) {
      await loadLaunchConfirmation();
      return;
    }
    if (event.target.closest("[data-next-flow-back-to-definition]")) {
      persistNextFlowBrowserDraft();
      state.nextFlowWizard.step = state.nextFlowWizard.action === "clone-flow" ? "sources" : "definition";
      if (state.nextFlowWizard.action === "clone-flow") {
        state.nextFlowWizard.active = false;
      } else {
        requestNextFlowWizardReveal();
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
    const diffFilter = event.target.closest("[data-implement-diff-filter]")?.dataset.implementDiffFilter;
    if (diffFilter) {
      state.implementDiffFilter = diffFilter;
      state.implementDiffPath = "";
      await renderImplementReview();
      return;
    }
    const diffFile = event.target.closest("[data-open-diff-file]")?.dataset.openDiffFile;
    if (diffFile) {
      state.implementDiffPath = diffFile;
      await renderImplementReview();
      return;
    }
    const proceedStage = event.target.closest("[data-proceed-stage]")?.dataset.proceedStage;
    if (proceedStage) {
      await startStage(proceedStage);
      return;
    }
    const taskId = event.target.closest("[data-run-task]")?.dataset.runTask;
    if (taskId) {
      await startImplementationTask(taskId);
      return;
    }
    if (event.target.closest("[data-finalize-tasks]")) {
      await startTaskFinalization();
      return;
    }
    if (event.target.closest("[data-rerun-implement]")) {
      await startStage("implement");
      return;
    }
    if (event.target.closest("[data-open-request-tab]")) {
      activateTab("request");
      await renderCockpit();
      return;
    }
    const remediationLaunch = event.target.closest("[data-remediation-launch]")?.dataset.remediationLaunch;
    if (remediationLaunch) {
      await launchRemediation(remediationLaunch);
      return;
    }
    if (event.target.closest("[data-accept-qa]")) {
      toast("QA acceptance stays recorded by the completed QA artifacts.");
      activateTab("artifacts");
      await renderCockpit();
      return;
    }
    if (event.target.closest("[data-next-flow-start]")) {
      await openNextFlowWizard("start-follow-up-flow");
      return;
    }
    const approvalConfirmation = event.target.closest("[data-approval-confirm-session]")?.dataset.approvalConfirmSession;
    if (approvalConfirmation) {
      await submitApproval(approvalConfirmation, "allow_for_session", {sessionConfirmed: true});
      return;
    }
    const approvalCancellation = event.target.closest("[data-approval-cancel-session]")?.dataset.approvalCancelSession;
    if (approvalCancellation) {
      closeApprovalSessionConfirmation(approvalCancellation);
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
    const readerArtifactKey = event.target.closest("[data-reader-artifact-key]")?.dataset.readerArtifactKey;
    if (readerArtifactKey) {
      state.activeArtifactKey = readerArtifactKey;
      state.activeArtifactComparison = null;
      state.selectedEvidenceNodeId = `document:${readerArtifactKey}`;
      state.selectedEvidenceEdgeId = "";
      // Keep a document-reading selection shareable without switching the
      // operator away from the Studio reader into the evidence browser.
      syncLocationState({historyMode: "push"});
      await loadArtifactDocument(readerArtifactKey);
      return;
    }
    const compareAttempt = event.target.closest("[data-compare-attempt]")?.dataset.compareAttempt;
    if (compareAttempt) {
      state.artifactViewMode = "compare";
      await loadArtifactComparison(compareAttempt);
      return;
    }
    if (event.target.closest("[data-clear-artifact-comparison]")) {
      state.activeArtifactComparison = null;
      if (state.activeArtifactKey) await loadArtifactDocument(state.activeArtifactKey);
      return;
    }
    if (event.target.closest("[data-retry-artifact-document]")) {
      if (state.activeArtifactKey) await loadArtifactDocument(state.activeArtifactKey);
      return;
    }
    const artifactKey = event.target.closest("[data-artifact-key]")?.dataset.artifactKey;
    if (artifactKey) {
      state.activeArtifactKey = artifactKey;
      state.activeArtifactComparison = null;
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
        state.activeArtifactComparison = null;
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
      if (artifactMode !== "compare") state.activeArtifactComparison = null;
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
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      const kind = blockerReference.dataset.blockerKind;
      setOperatorMode(kind === "questions" ? "questions" : kind === "validation" ? "validation" : "work");
      await fetchDashboard();
      await renderAll();
      return;
    }
    const recoveryAction = event.target.closest("[data-recovery-action]");
    if (recoveryAction) {
      state.activeStage = recoveryAction.dataset.recoveryStage || state.activeStage;
      state.activeStageExplicit = true;
      const action = recoveryAction.dataset.recoveryAction;
      state.activeArtifactKey = "";
      if (action === "answer-questions") setOperatorMode("questions");
      else if (action === "inspect-validation" || action === "inspect-blocker") setOperatorMode("validation");
      else if (action === "request-change") setOperatorMode("request");
      else if (action === "inspect-runtime-log") setOperatorMode("logs");
      else if (action === "review-findings") setOperatorMode("review-findings");
      else if (action === "qa-verdict") setOperatorMode("qa-verdict");
      else if (action === "run-repair") {
        await startStage(state.activeStage);
        return;
      }
      else if (action === "resume-stage") {
        await startStage(state.activeStage);
        return;
      }
      else if (action === "rerun-stale-downstream") {
        await rerunStaleDownstream();
        return;
      }
      requestCockpitReveal();
      await fetchDashboard();
      await fetchProjectHome(state.dashboard?.work_item || "");
      await fetchInbox();
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
    const answerPreviewButton = event.target.closest("[data-answer-preview]");
    if (answerPreviewButton) {
      await previewAnswer(answerPreviewButton.dataset.answerPreview);
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
    if (event.target.closest("[data-refresh-dashboard]")) {
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
    if (event.target.id === "nextActionButton" || event.target.id === "globalNextActionButton") {
      await handleNextAction();
      return;
    }
    const guidedLaunch = event.target.closest("[data-guided-launch]")?.dataset.guidedLaunch;
    if (guidedLaunch) {
      await dispatchTaskAwareLaunch(guidedLaunch, state.activeStage);
      return;
    }
    if (event.target.closest("[data-first-launch-stage]")) {
      await dispatchTaskAwareLaunch("stage", state.activeStage);
      return;
    }
    if (event.target.closest("[data-first-launch-run]")) {
      await dispatchTaskAwareLaunch("workflow");
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
    const logView = event.target.closest("[data-log-view]")?.dataset.logView;
    if (logView) {
      state.logViewMode = logView;
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
    state.runtimeSelectionRuntime = "";
    state.runtimeModel = "";
    state.runtimeReasoningEffort = "";
    state.runtimeModelDirty = false;
    state.runtimeReasoningEffortDirty = false;
    const runtimeSettings = document.getElementById("runtimeSettings");
    if (runtimeSettings && window.matchMedia("(max-width: 760px)").matches) {
      runtimeSettings.open = false;
    }
    if (state.onboarding.setupRequired) {
      renderOnboarding();
      return;
    }
    setRunButtonState();
    updateSubmitInterventionState();
    renderTopbar();
    renderSidebar();
    if (state.activeTab === "work") await renderCockpit();
  }
  if (event.target.id === "runtimeModelInput") {
    state.runtimeModel = event.target.value;
    state.runtimeModelDirty = true;
  }
  if (event.target.id === "runtimeReasoningEffortInput") {
    state.runtimeReasoningEffort = event.target.value;
    state.runtimeReasoningEffortDirty = true;
  }
  const questionResolution = event.target.closest("[data-question-resolution]")?.dataset.questionResolution;
  if (questionResolution) {
    persistQuestionDraft(questionResolution);
    updateQuestionResumeButtonState(questionResolution);
  }
  if (event.target.closest("[data-intervention-target]")) {
    persistInterventionDraft();
    updateInterventionPreview();
  }
  const remediationSource = event.target.closest("[data-remediation-source]")?.dataset.remediationSource;
  if (remediationSource) {
    persistRemediationDraft(remediationSource);
    updateRemediationPreview(remediationSource);
  }
  const sourceSelection = event.target.closest("[data-source-selection-id]");
  if (sourceSelection) {
    setSourceFindingSelection(sourceSelection.dataset.sourceSelectionId, sourceSelection.checked);
    await renderCockpit();
    return;
  }
  if (
    event.target.closest("[data-follow-up-list]")
    || event.target.closest("[data-inherited-context]")
  ) {
    invalidateFollowUpDraftPreview();
    persistNextFlowBrowserDraft();
  }
});

document.addEventListener("input", (event) => {
  if (event.target.closest?.("[data-task-filter]")) {
    state.taskWorkspaceFilter = event.target.value || "";
    void renderCockpit();
    return;
  }
  const projectSetField = event.target.dataset?.projectSetField;
  const projectSetIndex = event.target.dataset?.projectSetIndex;
  if (projectSetField && projectSetIndex !== undefined) {
    updateProjectSetRow(Number(projectSetIndex), projectSetField, event.target.value);
    syncOnboardingCreateActionState();
    return;
  }
  if (event.target.id === "onboardingProjectRoot") {
    state.onboarding.projectRootInput = event.target.value;
  }
  if (event.target.id === "onboardingWorkItem") {
    state.onboarding.workItemInput = event.target.value;
    syncOnboardingCreateActionState();
  }
  if (event.target.id === "onboardingRequest") {
    state.onboarding.requestText = event.target.value;
    syncOnboardingCreateActionState();
  }
  if (event.target.id === "projectNewWorkItem") {
    state.onboarding.workItemInput = event.target.value;
    syncProjectWorkItemCreateActionState();
  }
  if (event.target.id === "projectNewRequest") {
    state.onboarding.requestText = event.target.value;
    syncProjectWorkItemCreateActionState();
  }
  if (event.target.closest?.("[data-request-field]")) {
    const status = document.querySelector("[data-request-write-status]");
    if (status) status.textContent = "Draft changed; preview or write the durable request.";
  }
  if (event.target.id === "operatorRequestText") {
    persistInterventionDraft();
    updateInterventionPreview();
  }
  const remediationNote = event.target.closest("[data-remediation-note]")?.dataset.remediationNote;
  if (remediationNote) {
    persistRemediationDraft(remediationNote);
    updateRemediationPreview(remediationNote);
  }
  const questionText = event.target.closest("[data-question-text]")?.dataset.questionText;
  if (questionText) {
    persistQuestionDraft(questionText);
    updateQuestionResumeButtonState(questionText);
  }
  const questionEvidence = event.target.closest("[data-question-evidence]")?.dataset.questionEvidence;
  if (questionEvidence) persistQuestionDraft(questionEvidence);
  const questionConsequence = event.target.closest("[data-question-consequence]")?.dataset.questionConsequence;
  if (questionConsequence) persistQuestionDraft(questionConsequence);
  const approvalReasonId = event.target.closest("[data-approval-reason]")?.dataset.approvalReason;
  if (approvalReasonId) updateApprovalConfirmationPreview(approvalReasonId);
  if (event.target.id === "runComparisonBaseline") {
    state.runComparisonBaselineInput = event.target.value;
    state.runComparison = null;
    state.runComparisonError = "";
  }
  if (
    event.target.closest("[data-follow-up-field]")
    || event.target.closest("[data-follow-up-list-text]")
  ) {
    invalidateFollowUpDraftPreview();
    persistNextFlowBrowserDraft();
  }
});

document.addEventListener("change", (event) => {
  if (event.target.id === "onboardingForceContext") {
    state.onboarding.forceContext = event.target.checked;
  }
});

document.addEventListener("toggle", (event) => {
  rememberStudioFlowCompleteDisclosure(event.target);
}, true);

document.addEventListener("submit", async (event) => {
  try {
    if (event.target.id === "onboardingProjectForm") {
      event.preventDefault();
      await inspectOnboardingProject();
      return;
    }
    if (event.target.id === "onboardingCreateForm") {
      event.preventDefault();
      await completeOnboardingWorkItem("create", state.onboarding.workItemInput.trim());
      return;
    }
    if (event.target.id === "projectNewWorkItemForm") {
      event.preventDefault();
      await createProjectWorkItem();
    }
  } catch (error) {
    toast(error.message);
  }
});

initializeStateFromLocation();
window.addEventListener("popstate", () => {
  window.aiddRouteRestore = restoreOperatorRouteFromLocation().catch((error) => {
    toast(error.message);
  });
});
window.addEventListener("beforeunload", (event) => {
  if (!hasDirtyOperatorDraft(currentOperatorDraftProject())) return;
  event.preventDefault();
  event.returnValue = "";
});
refresh();
