function setupPreviousRunContext() {
  const dashboard = state.dashboard || {};
  const run = dashboard.run || {};
  const lineage = run.lineage || {};
  const handoff = dashboard.terminal_handoff || null;
  const sourceRunId = lineage.source_run_id || (handoff && run.run_id ? run.run_id : "");
  const sourceWorkItem = lineage.source_work_item_id || (sourceRunId ? dashboard.work_item : "");
  const baseline = lineage.baseline_label || lineage.baseline_id || "";
  const finalArtifacts = handoff?.final_artifacts || [];
  const blockers = handoff?.blockers || [];
  const approvalCounts = handoff?.approval_counts || null;
  return {
    available: Boolean(sourceRunId || baseline || finalArtifacts.length || blockers.length),
    sourceRunId,
    sourceWorkItem,
    baseline,
    finalArtifacts,
    blockers,
    approvalCounts
  };
}

function setupModeView(context = null) {
  const mode = SETUP_MODES.find((candidate) => candidate.id === state.setupMode) || SETUP_MODES[0];
  if (context && mode.requiresPreviousRun && !context.available) return SETUP_MODES[0];
  return mode;
}

function terminalHandoffNeedsRecovery(handoff) {
  return Boolean(handoff && (handoff.status !== "completed" || (handoff.blockers || []).length));
}

function nextFlowSourceRunId() {
  return state.activeRunId || state.dashboard?.run?.run_id || "";
}

function nextFlowSourceWorkItem() {
  return state.dashboard?.work_item || state.dashboard?.run?.lineage?.source_work_item_id || "";
}

function nextFlowDefaultWorkItem(suffix) {
  const source = nextFlowSourceWorkItem() || "WI";
  return `${source}-${suffix}`;
}

function nextFlowRuntimeId() {
  return state.selectedRuntime || state.dashboard?.run?.runtime_id || "";
}

function nextFlowMutationKey(kind, draft = null) {
  return operatorMutationKey(
    `next-flow-${kind}`,
    draft?.source_work_item || nextFlowSourceWorkItem() || "no-work-item",
    draft?.source_run_id || nextFlowSourceRunId() || "no-run",
    draft?.new_work_item || nextFlowDefaultWorkItem("PENDING"),
    state.nextFlowWizard.action || "handoff"
  );
}

function nextFlowMutationState(selectors) {
  return (mutation) => setMutationControlsPending(selectors, mutation.status === "pending");
}

const TERMINAL_EVIDENCE_REQUIREMENTS = [
  {
    key: "runtime_log",
    label: "Runtime log",
    detail: "Raw runtime output for the terminal QA attempt."
  },
  {
    key: "qa_report",
    label: "QA report",
    detail: "Final QA readiness and release recommendation."
  },
  {
    key: "validator_report",
    label: "Validator report",
    detail: "Document validation result for the terminal QA stage."
  },
  {
    key: "stage_result",
    label: "Stage result",
    detail: "Terminal stage status and handoff summary."
  }
];

function terminalEvidenceArtifacts(artifacts) {
  const priority = TERMINAL_EVIDENCE_REQUIREMENTS.map((item) => item.key);
  const seen = new Set();
  const byKey = new Map((artifacts || []).map((artifact) => [artifact.key, artifact]));
  const prioritized = priority
    .map((key) => byKey.get(key))
    .filter(Boolean)
    .map((artifact) => {
      seen.add(artifact.key);
      return artifact;
    });
  const remaining = (artifacts || []).filter((artifact) => !seen.has(artifact.key));
  return prioritized.concat(remaining).slice(0, 4);
}

function terminalEvidenceRequirement(key) {
  return TERMINAL_EVIDENCE_REQUIREMENTS.find((item) => item.key === key) || {
    key,
    label: key,
    detail: "Expected terminal evidence was not recorded."
  };
}

function terminalMissingEvidence(artifacts) {
  const available = new Set((artifacts || []).map((artifact) => artifact.key));
  return TERMINAL_EVIDENCE_REQUIREMENTS.filter((item) => !available.has(item.key));
}

function handoffMissingTerminalEvidence(handoff) {
  return Boolean(terminalMissingEvidence(handoff?.final_artifacts || []).length);
}

function defaultComparisonBaselineRunId(run, lineage) {
  return lineage.source_run_id || lineage.baseline_id || run.run_id || "";
}

function comparisonBaselineRunId(run, lineage) {
  return (state.runComparisonBaselineInput || defaultComparisonBaselineRunId(run, lineage)).trim();
}

async function loadRunComparisonPanel() {
  const panel = document.getElementById("runComparisonPanel");
  const run = state.dashboard?.run || {};
  if (!panel || !run.run_id) return;
  const lineage = run.lineage || {};
  const baselineRunId = comparisonBaselineRunId(run, lineage);
  const targetRunId = run.run_id;
  if (!baselineRunId || !targetRunId) {
    state.runComparison = null;
    state.runComparisonError = "baseline and target run ids are required";
    panel.outerHTML = renderRunComparisonPanel();
    return;
  }
  state.runComparisonLoading = true;
  state.runComparisonError = "";
  panel.outerHTML = renderRunComparisonPanel();
  const params = new URLSearchParams({
    baseline_run_id: baselineRunId,
    target_run_id: targetRunId
  });
  try {
    state.runComparison = await api(`/api/run/comparison?${params.toString()}`);
    state.runComparisonError = "";
  } catch (error) {
    state.runComparison = null;
    state.runComparisonError = error.message || "run comparison unavailable";
  } finally {
    state.runComparisonLoading = false;
    const updatedPanel = document.getElementById("runComparisonPanel");
    if (updatedPanel) updatedPanel.outerHTML = renderRunComparisonPanel();
  }
}

function allSourceFindingItems(payload = state.nextFlowWizard.sourceFindings) {
  return (payload?.groups || [])
    .flatMap((group) => group.items || [])
    .sort((left, right) => sourceFindingPriority(left) - sourceFindingPriority(right));
}

function recommendedSourceFindingIds(payload = state.nextFlowWizard.sourceFindings) {
  return allSourceFindingItems(payload)
    .filter((item) => item.recommended)
    .map((item) => item.id);
}

function sourceFindingSelected(id) {
  return state.nextFlowWizard.selectedSourceIds.includes(id);
}

function setSourceFindingSelection(id, selected) {
  const current = new Set(state.nextFlowWizard.selectedSourceIds);
  if (selected) current.add(id);
  else current.delete(id);
  state.nextFlowWizard.selectedSourceIds = Array.from(current);
}

function selectSourceFindings(mode) {
  if (mode === "clear") {
    state.nextFlowWizard.selectedSourceIds = [];
    return;
  }
  if (mode === "recommended") {
    state.nextFlowWizard.selectedSourceIds = recommendedSourceFindingIds();
  }
}

async function renderNextFlowWizardStep() {
  requestNextFlowWizardReveal();
  await renderCockpit();
}

function resetLaunchReadiness(wizard = state.nextFlowWizard) {
  wizard.launchReadinessChecking = false;
  wizard.launchReadinessError = "";
}

function nextFlowDraftForm(action = state.nextFlowWizard.action) {
  return action === "clone-flow" ? "clone" : "follow-up";
}

function nextFlowBrowserDraftIdentity(action = state.nextFlowWizard.action) {
  return operatorDraftIdentity(nextFlowDraftForm(action), nextFlowSourceRunId());
}

function editableNextFlowDraftValue(draft) {
  if (!draft) return null;
  return {
    new_work_item: draft.new_work_item || "",
    title: draft.title || "",
    first_stage_input_preview: draft.first_stage_input_preview || "",
    acceptance_criteria: draft.acceptance_criteria || [],
    acceptance_criteria_all: draft.acceptance_criteria_all || null,
    required_evidence: draft.required_evidence || [],
    required_evidence_all: draft.required_evidence_all || null,
    inherited_context_lines: draft.inherited_context_lines || null,
    selected_source_ids: [...(state.nextFlowWizard.selectedSourceIds || [])]
  };
}

function mergeNextFlowBrowserDraft(serverDraft, action = state.nextFlowWizard.action) {
  const restored = readOperatorDraft(nextFlowBrowserDraftIdentity(action))?.value;
  if (!restored) return serverDraft;
  state.nextFlowWizard.selectedSourceIds = restored.selected_source_ids
    || state.nextFlowWizard.selectedSourceIds;
  return {
    ...serverDraft,
    ...restored,
    source_work_item: serverDraft.source_work_item,
    source_run_id: serverDraft.source_run_id,
    inherited_context: serverDraft.inherited_context,
    created: serverDraft.created
  };
}

function persistNextFlowBrowserDraft() {
  if (!["start-follow-up-flow", "clone-flow"].includes(state.nextFlowWizard.action)) return;
  const draft = readFollowUpDraftForm() || state.nextFlowWizard.followUpDraft;
  const value = editableNextFlowDraftValue(draft);
  if (!value) return;
  writeOperatorDraft(nextFlowBrowserDraftIdentity(), value);
}

async function openNextFlowWizard(action) {
  const sourceRunId = nextFlowSourceRunId();
  const canReuseSourceFindings = (
    state.nextFlowWizard.action === action
    && state.nextFlowWizard.sourceFindings
    && state.nextFlowWizard.sourceFindings.source_run_id === sourceRunId
  );
  state.nextFlowWizard.active = true;
  state.nextFlowWizard.action = action;
  state.nextFlowWizard.step = "sources";
  if (canReuseSourceFindings) {
    state.nextFlowWizard.loading = false;
    state.nextFlowWizard.error = "";
    activateTab("overview");
    await renderNextFlowWizardStep();
    return;
  }
  state.nextFlowWizard.loading = true;
  state.nextFlowWizard.error = "";
  state.nextFlowWizard.sourceFindings = null;
  state.nextFlowWizard.followUpDraft = null;
  state.nextFlowWizard.followUpDraftError = "";
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.preflightError = "";
  state.nextFlowWizard.definitionErrors = [];
  state.nextFlowWizard.createdDraft = null;
  state.nextFlowWizard.launchLoading = false;
  state.nextFlowWizard.launchError = "";
  resetLaunchReadiness();
  state.nextFlowWizard.archiveRunId = "";
  state.nextFlowWizard.archiveReason = "";
  state.nextFlowWizard.selectedSourceIds = [];
  activateTab("overview");
  await renderNextFlowWizardStep();
  try {
    const payload = await api(sourceFindingsUrl());
    state.nextFlowWizard.sourceFindings = payload;
    state.nextFlowWizard.selectedSourceIds = allSourceFindingItems(payload)
      .filter((item) => item.selected)
      .map((item) => item.id);
  } catch (error) {
    state.nextFlowWizard.error = error.message;
  } finally {
    state.nextFlowWizard.loading = false;
    await renderNextFlowWizardStep();
  }
}

async function openNewWorkItemHandoff() {
  state.nextFlowWizard.active = true;
  state.nextFlowWizard.action = "create-new-work-item";
  state.nextFlowWizard.step = "new-work-item";
  state.nextFlowWizard.loading = false;
  state.nextFlowWizard.error = "";
  state.nextFlowWizard.followUpDraft = null;
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.definitionErrors = [];
  state.nextFlowWizard.createdDraft = null;
  state.nextFlowWizard.launchError = "";
  resetLaunchReadiness();
  state.nextFlowWizard.archiveRunId = "";
  state.nextFlowWizard.archiveReason = "";
  activateTab("overview");
  await renderNextFlowWizardStep();
}

async function openEvalBatchHandoff() {
  state.nextFlowWizard.active = true;
  state.nextFlowWizard.action = "run-eval-batch";
  state.nextFlowWizard.step = "eval-batch";
  state.nextFlowWizard.loading = false;
  state.nextFlowWizard.error = "";
  state.nextFlowWizard.followUpDraft = null;
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.definitionErrors = [];
  state.nextFlowWizard.createdDraft = null;
  state.nextFlowWizard.launchError = "";
  resetLaunchReadiness();
  state.nextFlowWizard.archiveRunId = "";
  state.nextFlowWizard.archiveReason = "";
  activateTab("overview");
  await renderNextFlowWizardStep();
}

function cloneDraftFromPayload(payload) {
  const draft = payload.draft || {};
  const created = payload.created || {};
  const config = created.config || {};
  return {
    kind: "clone-flow",
    source_work_item: draft.source_work_item || nextFlowSourceWorkItem(),
    source_run_id: draft.source_run_id || nextFlowSourceRunId(),
    new_work_item: draft.new_work_item || created.work_item || nextFlowDefaultWorkItem("CLONE"),
    title: draft.title || `Clone ${nextFlowSourceWorkItem()} from ${nextFlowSourceRunId()}`,
    selected_sources: [],
    acceptance_criteria: [
      "Review cloned runtime, prompt pack, contracts, branch, resource, and baseline configuration before launch."
    ],
    required_evidence: [
      created.draft_path ? `Clone draft: ${created.draft_path}` : "Clone draft recorded before launch."
    ],
    inherited_context: [
      {
        id: "clone-runtime-config",
        label: "Runtime and prompt configuration",
        detail: `${config.runtime_id || "runtime"} / ${config.stage_target || "workflow"}`,
        enabled: true
      },
      {
        id: "clone-baseline",
        label: "Baseline reference",
        detail: config.baseline_label || config.baseline_id || "source run",
        enabled: true
      }
    ],
    created
  };
}

async function openCloneFlowDraft() {
  const wizard = state.nextFlowWizard;
  wizard.active = true;
  wizard.action = "clone-flow";
  wizard.step = "confirm";
  wizard.loading = false;
  wizard.error = "";
  wizard.followUpDraft = null;
  wizard.preflight = null;
  wizard.preflightError = "";
  wizard.definitionErrors = [];
  wizard.launchError = "";
  resetLaunchReadiness(wizard);
  wizard.createdDraft = null;
  wizard.archiveRunId = "";
  wizard.archiveReason = "";
  wizard.preflightLoading = true;
  activateTab("overview");
  await renderNextFlowWizardStep();
  try {
    const draftRequest = {
      source_work_item: nextFlowSourceWorkItem(),
      source_run_id: nextFlowSourceRunId(),
      new_work_item: nextFlowDefaultWorkItem("CLONE")
    };
    const guarded = await runGuardedMutation({
      key: nextFlowMutationKey("clone-draft", draftRequest),
      execute: () => postJson("/api/next-flow/clone-draft/create", {
        ...draftRequest,
        title: `Clone ${nextFlowSourceWorkItem()} from ${nextFlowSourceRunId()}`
      }),
      readWinner: async () => null,
      onState: nextFlowMutationState(['[data-next-flow-action="clone-flow"]'])
    });
    if (guarded.status === "conflict") {
      throw new Error(`A clone draft or work item already exists for ${draftRequest.new_work_item}.`);
    }
    const payload = guarded.result;
    wizard.followUpDraft = mergeNextFlowBrowserDraft(cloneDraftFromPayload(payload), "clone-flow");
    wizard.createdDraft = payload.created;
    toast("Clone draft created for launch review.");
    await loadLaunchConfirmation();
  } catch (error) {
    wizard.preflightLoading = false;
    wizard.preflightError = error.message;
    await renderNextFlowWizardStep();
  }
}

async function loadLaunchConfirmation() {
  const wizard = state.nextFlowWizard;
  const draft = readFollowUpDraftForm() || wizard.followUpDraft;
  if (!draft) {
    wizard.preflightError = "No next-flow draft is available for preflight.";
    wizard.step = "confirm";
    await renderNextFlowWizardStep();
    return;
  }
  persistNextFlowBrowserDraft();
  const definitionErrors = followUpDraftValidationErrors(draft);
  const definitionError = definitionErrors[0] || "";
  if (definitionError) {
    wizard.preflightLoading = false;
    wizard.preflightError = definitionError;
    wizard.definitionErrors = definitionErrors;
    wizard.step = "definition";
    await renderNextFlowWizardStep();
    return;
  }
  wizard.preflightLoading = true;
  wizard.preflightError = "";
  wizard.definitionErrors = [];
  wizard.launchError = "";
  resetLaunchReadiness(wizard);
  wizard.step = "confirm";
  await renderNextFlowWizardStep();
  try {
    const payload = {
      source_work_item: draft.source_work_item,
      source_run_id: draft.source_run_id,
      runtime: state.selectedRuntime || state.dashboard?.run?.runtime_id || "",
      baseline_id: state.dashboard?.run?.lineage?.baseline_id || draft.source_run_id
    };
    const guarded = await runGuardedMutation({
      key: nextFlowMutationKey("preflight", draft),
      execute: async () => {
        const response = await fetch("/api/next-flow/preflight", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify(payload)
        });
        return {response, result: await response.json()};
      },
      onState: nextFlowMutationState(["[data-next-flow-confirm-preview]"])
    });
    const {response, result} = guarded.result;
    if (response.ok) {
      wizard.preflight = result.preflight;
    } else if (result.status === "blocked") {
      wizard.preflight = {
        status: "blocked",
        can_launch: false,
        checks: result.checks || [],
        blocking_codes: result.blocking_codes || [],
        warning_codes: result.warning_codes || [],
        resolved_baseline_id: null
      };
      wizard.preflightError = result.error || "next-flow launch preflight blocked";
    } else {
      throw new Error(result.error || response.statusText);
    }
  } catch (error) {
    wizard.preflightError = error.message;
  } finally {
    wizard.preflightLoading = false;
    await renderNextFlowWizardStep();
  }
}

function selectedFollowUpListValues(name, fallbackItems = []) {
  const controls = Array.from(document.querySelectorAll("[data-follow-up-list]"))
    .filter((control) => control.dataset.followUpList === name);
  if (!controls.length) return fallbackItems || [];
  return controls
    .filter((control) => control.checked)
    .map((control) => {
      const index = Number(control.dataset.followUpIndex);
      const textControl = Array.from(document.querySelectorAll("[data-follow-up-list-text]"))
        .find((candidate) => (
          candidate.dataset.followUpListText === name
          && Number(candidate.dataset.followUpIndex) === index
        ));
      return textControl ? textControl.value : fallbackItems[index];
    })
    .filter((value) => String(value || "").trim());
}

function allFollowUpListValues(name, fallbackItems = []) {
  const controls = Array.from(document.querySelectorAll("[data-follow-up-list-text]"))
    .filter((control) => control.dataset.followUpListText === name);
  if (!controls.length) return fallbackItems || [];
  return controls
    .sort((left, right) => Number(left.dataset.followUpIndex) - Number(right.dataset.followUpIndex))
    .map((control) => control.value);
}

function inheritedContextLinesFromItems(items = []) {
  return (items || [])
    .map((item) => {
      const label = String(item?.label || "").trim();
      const detail = String(item?.detail || "").trim();
      if (!label) return "";
      return detail ? `${label}: ${detail}` : label;
    })
    .filter(Boolean);
}

function selectedInheritedContextLines(items = [], fallbackLines = null) {
  const controls = Array.from(document.querySelectorAll("[data-inherited-context]"));
  if (!controls.length) return fallbackLines || inheritedContextLinesFromItems(items);
  const selectedIds = new Set(
    controls
      .filter((control) => control.checked)
      .map((control) => control.dataset.inheritedContext)
  );
  return inheritedContextLinesFromItems(
    (items || []).filter((item) => selectedIds.has(String(item?.id || "")))
  );
}

function followUpDraftValidationErrors(draft) {
  if (state.nextFlowWizard.action !== "start-follow-up-flow") return [];
  const errors = [];
  if (!String(draft?.new_work_item || "").trim()) errors.push("Work item id is required before preflight.");
  if (!String(draft?.title || "").trim()) errors.push("Title is required before preflight.");
  if (!String(draft?.first_stage_input_preview || "").trim()) errors.push("First-stage input preview is required before preflight.");
  if (!(draft?.acceptance_criteria || []).some((item) => String(item || "").trim())) {
    errors.push("At least one acceptance criterion is required before preflight.");
  }
  if (!(draft?.required_evidence || []).some((item) => String(item || "").trim())) {
    errors.push("At least one required evidence item is required before preflight.");
  }
  return errors;
}

function followUpDraftValidationError(draft) {
  return followUpDraftValidationErrors(draft)[0] || "";
}

function readFollowUpDraftForm() {
  const draft = state.nextFlowWizard.followUpDraft;
  if (!draft || state.nextFlowWizard.action !== "start-follow-up-flow") return draft;
  const newWorkItemField = document.querySelector('[data-follow-up-field="new_work_item"]');
  const titleField = document.querySelector('[data-follow-up-field="title"]');
  const previewField = document.querySelector('[data-follow-up-field="first_stage_input_preview"]');
  if (newWorkItemField) draft.new_work_item = newWorkItemField.value.trim();
  if (titleField) draft.title = titleField.value.trim();
  if (previewField) draft.first_stage_input_preview = previewField.value;
  draft.acceptance_criteria_all = allFollowUpListValues(
    "acceptance_criteria",
    draft.acceptance_criteria_all || draft.acceptance_criteria
  );
  draft.required_evidence_all = allFollowUpListValues(
    "required_evidence",
    draft.required_evidence_all || draft.required_evidence
  );
  draft.acceptance_criteria = selectedFollowUpListValues("acceptance_criteria", draft.acceptance_criteria_all);
  draft.required_evidence = selectedFollowUpListValues("required_evidence", draft.required_evidence_all);
  draft.inherited_context_lines = selectedInheritedContextLines(draft.inherited_context, draft.inherited_context_lines);
  return draft;
}

function invalidateFollowUpDraftPreview() {
  if (!state.nextFlowWizard.active || state.nextFlowWizard.step !== "definition") return;
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.preflightError = "";
  state.nextFlowWizard.definitionErrors = [];
  state.nextFlowWizard.createdDraft = null;
  state.nextFlowWizard.launchError = "";
  resetLaunchReadiness();
  document.querySelectorAll("[data-follow-up-definition-error], [data-follow-up-list-blocker]")
    .forEach((node) => node.remove());
}

async function createFollowUpDraftForLaunch(draft) {
  if (state.nextFlowWizard.createdDraft) return state.nextFlowWizard.createdDraft;
  const guarded = await runGuardedMutation({
    key: nextFlowMutationKey("follow-up-draft", draft),
    execute: () => postJson("/api/next-flow/follow-up-draft/create", {
      source_work_item: draft.source_work_item,
      source_run_id: draft.source_run_id,
      selected_source_ids: state.nextFlowWizard.selectedSourceIds,
      new_work_item: draft.new_work_item,
      title: draft.title,
      first_stage_input: draft.first_stage_input_preview,
      acceptance_criteria: draft.acceptance_criteria || [],
      required_evidence: draft.required_evidence || [],
      inherited_context: draft.inherited_context_lines || inheritedContextLinesFromItems(draft.inherited_context)
    }),
    readWinner: async () => null,
    onState: nextFlowMutationState(["[data-launch-flow-now]"])
  });
  if (guarded.status === "conflict") {
    throw new Error(`A follow-up draft or work item already exists for ${draft.new_work_item}.`);
  }
  const payload = guarded.result;
  state.nextFlowWizard.createdDraft = payload.created;
  return payload.created;
}

async function blockLaunchForRuntimeReadiness(message) {
  const wizard = state.nextFlowWizard;
  wizard.launchReadinessChecking = false;
  wizard.launchReadinessError = message;
  const runtimeSelect = document.getElementById("runtimeSelect");
  if (runtimeSelect) runtimeSelect.focus();
  if (!message.startsWith("Runtime readiness unavailable:")) toast(message);
  await renderNextFlowWizardStep();
  return false;
}

async function refreshRuntimeReadinessForLaunch() {
  const wizard = state.nextFlowWizard;
  if (!state.selectedRuntime) {
    return blockLaunchForRuntimeReadiness(runtimeReadinessMessage());
  }
  wizard.launchReadinessChecking = true;
  wizard.launchReadinessError = "";
  await renderNextFlowWizardStep();
  await fetchReadiness();
  renderRuntimeSelector();
  renderTopbar();
  renderSidebar();
  wizard.launchReadinessChecking = false;
  const message = runtimeReadinessMessage();
  if (message) {
    return blockLaunchForRuntimeReadiness(message);
  }
  await renderNextFlowWizardStep();
  return true;
}

async function launchNextFlowNow() {
  const wizard = state.nextFlowWizard;
  const draft = readFollowUpDraftForm() || wizard.followUpDraft;
  if (!draft) {
    toast("No next-flow draft is ready to launch.");
    return;
  }
  persistNextFlowBrowserDraft();
  wizard.launchError = "";
  resetLaunchReadiness(wizard);
  if (!(await refreshRuntimeReadinessForLaunch())) return;
  wizard.launchLoading = true;
  await renderNextFlowWizardStep();
  try {
    if (wizard.action === "start-follow-up-flow") {
      await createFollowUpDraftForLaunch(draft);
    }
    const guarded = await runGuardedMutation({
      key: nextFlowMutationKey("launch", draft),
      execute: async () => {
        const job = await postJson("/api/next-flow/launch", {
          source_work_item: draft.source_work_item,
          source_run_id: draft.source_run_id,
          new_work_item: draft.new_work_item,
          runtime: nextFlowRuntimeId(),
          baseline_id: state.nextFlowWizard.preflight?.resolved_baseline_id || draft.source_run_id,
          relationship: wizard.action === "clone-flow" ? "clone" : "follow-up",
          from_stage: "idea",
          to_stage: "qa",
          log_follow: true
        });
        const readback = await api(`/api/jobs/${encodeURIComponent(job.job_id)}`);
        if (readback.job_id !== job.job_id) {
          throw new Error("Next-flow job readback did not confirm the durable launch");
        }
        await startJobPolling(job);
        return job;
      },
      readWinner: async () => null,
      onState: nextFlowMutationState(["[data-launch-flow-now]"])
    });
    if (guarded.status === "conflict") {
      throw new Error("Another next-flow launch already won; refresh durable state before retrying.");
    }
    clearOperatorDraft(nextFlowBrowserDraftIdentity());
    wizard.active = false;
    toast(`Launching ${draft.new_work_item}.`);
  } catch (error) {
    wizard.launchError = error.message;
    toast(error.message);
    wizard.launchLoading = false;
    await renderNextFlowWizardStep();
  } finally {
    wizard.launchLoading = false;
  }
}

async function loadFollowUpDraft() {
  const wizard = state.nextFlowWizard;
  wizard.followUpDraftLoading = true;
  wizard.followUpDraftError = "";
  wizard.step = "definition";
  await renderNextFlowWizardStep();
  try {
    const payload = await postJson("/api/next-flow/follow-up-draft", {
      source_run_id: state.activeRunId,
      selected_source_ids: wizard.selectedSourceIds
    });
    wizard.followUpDraft = mergeNextFlowBrowserDraft(payload.draft, "start-follow-up-flow");
  } catch (error) {
    wizard.followUpDraftError = error.message;
  } finally {
    wizard.followUpDraftLoading = false;
    await renderNextFlowWizardStep();
  }
}

async function openArchiveConfirmation() {
  const runId = state.activeRunId || state.dashboard?.run?.run_id || "";
  if (!runId) {
    toast("No completed run is selected for archive.");
    return;
  }
  state.nextFlowWizard.active = true;
  state.nextFlowWizard.action = "archive-run";
  state.nextFlowWizard.step = "archive-confirm";
  state.nextFlowWizard.loading = false;
  state.nextFlowWizard.error = "";
  state.nextFlowWizard.followUpDraft = null;
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.preflightError = "";
  state.nextFlowWizard.definitionErrors = [];
  state.nextFlowWizard.launchError = "";
  resetLaunchReadiness();
  state.nextFlowWizard.archiveRunId = runId;
  state.nextFlowWizard.archiveReason = state.dashboard?.terminal_handoff
    ? `Archived from Flow Complete handoff with status ${state.dashboard.terminal_handoff.status}.`
    : "Archived from Run History.";
  activateTab("overview");
  await renderNextFlowWizardStep();
}

async function archiveCompletedRun() {
  const runId = state.nextFlowWizard.archiveRunId || state.activeRunId || state.dashboard?.run?.run_id || "";
  if (!runId) {
    toast("No completed run is selected for archive.");
    return;
  }
  const reason = state.nextFlowWizard.archiveReason
    || (state.dashboard?.terminal_handoff
      ? `Archived from Flow Complete handoff with status ${state.dashboard.terminal_handoff.status}.`
      : "Archived from Run History.");
  const payload = await postJson("/api/next-flow/archive", {
    source_run_id: runId,
    reason
  });
  state.dashboard = payload.dashboard;
  state.nextFlowWizard.active = false;
  state.nextFlowWizard.action = "";
  state.nextFlowWizard.step = "sources";
  toast("Run archived for operator navigation.");
  await renderAll();
}

function blockingPreflightChecks(preflight) {
  return (preflight?.checks || []).filter((check) => check.severity === "blocking");
}

function followUpDefinitionErrorsForRender(wizard) {
  const errors = Array.isArray(wizard.definitionErrors)
    ? wizard.definitionErrors.filter((item) => String(item || "").trim())
    : [];
  if (errors.length) return errors;
  return wizard.preflightError ? [wizard.preflightError] : [];
}

function activeJobBlocksNextAction(action) {
  const job = state.activeJobStatus;
  if (!state.activeJobId || !job || activeJobIsTerminal()) return false;
  const status = job.status || "running";
  if (!["running", "waiting-for-operator", "cancelling"].includes(status)) return false;
  if (job.kind === "workflow" || job.kind === "next-flow-launch") return true;
  const actionStage = action?.stage || state.activeStage;
  return Boolean(job.stage && actionStage && job.stage === actionStage);
}

function activeJobNextActionState(action) {
  if (!activeJobBlocksNextAction(action)) return null;
  const job = state.activeJobStatus || {};
  const stage = job.stage || action?.stage || state.activeStage;
  const stageLabel = stage ? stageTitle(stage) : "Run";
  const status = job.status || "running";
  return {
    label: status === "waiting-for-operator" ? `${stageLabel} waiting for approval` : `${stageLabel} running`,
    detail: `Job ${state.activeJobId} is ${status}. Open Runtime Logs / Live Console for live output before starting another action.`,
    stage: stage ? stageTitle(stage) : "run",
    run: state.activeRunId || state.dashboard?.run?.run_id || "not started"
  };
}

function staleDownstreamStages() {
  return (state.dashboard?.stages || []).filter((item) => item.stale);
}

function staleDownstreamRuntimeGate() {
  if (!state.selectedRuntime) {
    return {label: "Runtime required", nextStep: "Select runtime"};
  }
  if (!selectedRuntimeReady()) {
    return {label: `${state.selectedRuntime} not ready`, nextStep: "Select ready runtime"};
  }
  return {label: `${state.selectedRuntime} ready`, nextStep: "Rerun downstream"};
}

function workDetailOwnsPrimarySurface() {
  return state.activeTab === "work"
    && ["implement-review", "review-findings", "qa-verdict"].includes(state.workDetail);
}

function globalNextActionStripProvidesPrimary() {
  if (state.onboarding?.setupRequired) return false;
  if (state.activeTab === "recovery") return false;
  if (workDetailOwnsPrimarySurface()) return false;
  return !document.body.classList.contains("evidence-log-mode");
}
