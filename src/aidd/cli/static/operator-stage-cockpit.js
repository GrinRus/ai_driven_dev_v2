const RUNTIME_FAILURE_KINDS = new Set([
  "cancelled",
  "failed",
  "non_zero_exit",
  "non-zero-exit",
  "provider_error",
  "provider-no-progress",
  "runtime-error",
  "runtime-exit-metadata-invalid",
  "runtime-failure",
  "stage-failed",
  "timeout"
]);

function isRuntimeFailureKind(kind) {
  return RUNTIME_FAILURE_KINDS.has(String(kind || "").trim().toLowerCase());
}

function isRuntimeFirstFailure(firstFailure) {
  return Boolean(firstFailure && isRuntimeFailureKind(firstFailure.kind));
}

function runtimeLogEvidencePath(diagnostics) {
  return diagnostics?.raw_log?.path || diagnostics?.runtime_log?.path || "";
}

function runtimeFailureEvidencePath(firstFailure, diagnostics) {
  return firstFailure?.path || runtimeLogEvidencePath(diagnostics) || "";
}

function renderLegacyOverview() {
  if (!state.dashboard?.run?.run_id) {
    return renderFirstLaunchState();
  }
  if (state.nextFlowWizard.active) {
    return renderNextFlowSourceSelection();
  }
  if (state.dashboard?.terminal_handoff) {
    return renderFlowCompleteState();
  }
  const item = activeStageItem();
  const view = activeStageView();
  const unresolved = view?.questions?.unresolved_blocking_question_ids || [];
  if (unresolved.length) {
    return `
      <section class="surface">
        <div class="surface-title">
          <span>Blocking questions</span>
          <span class="small-badge warn">${escapeHtml(unresolved.length)} blocking</span>
        </div>
        ${renderQuestionCards({showResume: true})}
      </section>
    `;
  }
  const result = view?.result;
  return `
    <div class="overview-grid">
      <section class="surface">
        <div class="surface-title">
          <span>Primary artifact</span>
          <span class="small-badge">${escapeHtml(state.activeStage)}</span>
        </div>
        ${renderPrimaryArtifact()}
      </section>
      <aside class="surface">
        <div class="surface-title">Stage health</div>
        <div class="metric-grid">
          <div class="metric"><span>State</span><strong>${escapeHtml(item?.status || "pending")}</strong></div>
          <div class="metric"><span>Attempts</span><strong>${escapeHtml(item?.attempt_count || 0)}</strong></div>
          <div class="metric"><span>Questions</span><strong>${escapeHtml(item?.unresolved_blocking_count || 0)}/${escapeHtml(item?.question_count || 0)}</strong></div>
          <div class="metric"><span>Validation</span><strong>${escapeHtml(item?.validator_pass_count || 0)}/${escapeHtml(item?.validator_fail_count || 0)}</strong></div>
        </div>
        <div class="panel-item">
          <strong>Eligibility</strong>
          <span>${escapeHtml(item?.reason || "not started")}</span>
        </div>
        <div class="panel-item">
          <strong>Validator report</strong>
          ${pathLine(result?.validator_report_path || "not available")}
        </div>
      </aside>
      <section id="runAccountabilityCard" class="surface run-accountability-card">
        ${renderRunAccountabilityCard()}
      </section>
    </div>
  `;
}

function renderOverviewSurface() {
  const {renderer} = selectSurfaceRenderer("active-studio", {
    legacy: renderLegacyOverview,
    studio: renderActiveStudio
  });
  return renderer();
}

function renderRunAccountabilityCard() {
  const view = state.runAccountability;
  if (state.runAccountabilityError) {
    return `<div class="empty-state bad">${escapeHtml(state.runAccountabilityError)}</div>`;
  }
  if (!view) {
    return `<div class="empty-state loading-state">Loading run provenance...</div>`;
  }
  const prompts = view.prompt_pack_provenance || [];
  const configKeys = Object.keys(view.config_snapshot || {});
  return `
    <div class="surface-title">
      <span>Run provenance</span>
      <span class="small-badge">${escapeHtml(prompts.length)} prompts</span>
    </div>
    ${renderWarnings(view.warnings)}
    <div class="metric-grid">
      <div class="metric"><span>Runtime</span><strong>${escapeHtml(view.runtime_id)}</strong></div>
      <div class="metric"><span>Adapter</span><strong>${escapeHtml(view.adapter_id || "unknown")}</strong></div>
      <div class="metric"><span>Resource</span><strong>${escapeHtml(view.resource_source || "unknown")}</strong></div>
      <div class="metric"><span>Config keys</span><strong>${escapeHtml(configKeys.length)}</strong></div>
    </div>
    <div class="panel-item">
      <strong>Git SHA</strong>
      <span>${escapeHtml(view.repository_git_sha || "not recorded")}</span>
    </div>
    <div class="panel-item">
      <strong>Resource revision</strong>
      <span>${escapeHtml(view.resource_revision || "not recorded")}</span>
    </div>
    <div class="panel-item">
      <strong>Stage graph</strong>
      <span>${escapeHtml((view.stage_graph || []).join(" -> "))}</span>
    </div>
    <div class="compact-list">
      ${prompts.slice(0, 4).map((entry) => `<span>${escapeHtml(entry.path)} ${escapeHtml(entry.sha256.slice(0, 12))}</span>`).join("") || "<span>No prompt provenance recorded.</span>"}
    </div>
  `;
}

async function loadRunAccountabilityCard() {
  const card = document.getElementById("runAccountabilityCard");
  if (!card || !state.activeRunId) return;
  try {
    state.runAccountabilityError = "";
    state.runAccountability = await api(`/api/run/accountability?${runScopedQuery()}`);
  } catch (error) {
    state.runAccountability = null;
    state.runAccountabilityError = error.message || "run provenance unavailable";
  }
  card.innerHTML = renderRunAccountabilityCard();
}

function repairCenterStatus(validation, stopped) {
  if (stopped?.stopped) return "explicit-stop";
  return validation?.status || (validation?.validator_fail_count ? "repair-needed" : "clear");
}

function renderRecoveryActionBand(diagnostics) {
  const validation = diagnostics?.validation;
  const stopped = diagnostics?.stopped;
  const status = repairCenterStatus(validation, stopped);
  const repairAvailable = status === "repair-available";
  const requestPrimary = status === "repair-exhausted" || status === "explicit-stop";
  const stoppedMessage = stopped?.stopped ? stopped.detail || "Stage stopped." : "";
  const finding = primaryValidationFindingForValidation(validation);
  const guidance = stoppedMessage
    || (repairAvailable
      ? "Validation failed. Run Repair starts the selected stage through the normal stage runner."
      : status === "repair-exhausted"
        ? "Validation still fails after repair attempts. Request Change creates an operator intervention for this stage."
        : "Review validation evidence, repair history, and recovery actions before continuing.");
  return `
    <section class="repair-action-band ${repairAvailable ? "repair-available" : ""}">
      <div>
        <div class="surface-title">
          <span>${repairAvailable ? "Repair Available" : status === "repair-exhausted" ? "Repair Exhausted" : status === "explicit-stop" ? "Explicit Stop" : "Repair Center"}</span>
          <span class="small-badge ${status === "clear" ? "good" : status === "explicit-stop" || status === "repair-exhausted" ? "bad" : "warn"}">${escapeHtml(status)}</span>
        </div>
        <p>${escapeHtml(guidance)}</p>
        ${renderValidationFindingSummary(finding)}
      </div>
      <div class="repair-actions">
        ${requestPrimary ? `<button data-tab-shortcut="request" type="button">Request Change</button>` : `<button data-run-repair type="button" ${repairAvailable ? "" : "disabled"}>Run Repair</button>`}
        ${requestPrimary ? `<button data-run-repair type="button" class="secondary" disabled>Repair exhausted</button>` : `<button data-tab-shortcut="request" type="button" class="secondary">Request Change</button>`}
        <button data-stop-run type="button" class="danger">Stop Run</button>
      </div>
    </section>
  `;
}

function renderRepairTimeline(validation) {
  const attempts = validation?.repair_attempts || [];
  if (!attempts.length) {
    return `<div class="empty-state">No repair attempts recorded.</div>`;
  }
  return `
    <div class="repair-timeline">
      ${attempts.map((attempt) => `
        <article class="repair-timeline-card">
          <div class="question-head">
            <strong>Attempt ${escapeHtml(attempt.attempt_number)}</strong>
            <span class="small-badge ${attempt.outcome === "succeeded" ? "good" : "warn"}">${escapeHtml(attempt.outcome)}</span>
          </div>
          <div class="question-meta">
            <span>${escapeHtml(attempt.trigger)}</span>
            <span>${escapeHtml(attempt.recorded_at_utc)}</span>
          </div>
          ${attempt.validator_report_path ? pathLine(attempt.validator_report_path, 78) : ""}
          ${attempt.repair_brief_path ? pathLine(attempt.repair_brief_path, 78) : ""}
        </article>
      `).join("")}
    </div>
  `;
}

function renderResolvedRepairSummary(validation) {
  const attempts = validation?.repair_attempts || [];
  if (!attempts.length) return "";
  const latest = attempts[attempts.length - 1] || {};
  const attemptLabel = attempts.length === 1 ? "1 validation attempt" : `${attempts.length} validation attempts`;
  const retryCount = Math.max(0, attempts.length - 1);
  const retryLabel = retryCount === 1 ? "1 retry" : `${retryCount} retries`;
  const summaryLabel = retryCount ? `${retryLabel} resolved across ${attemptLabel}` : `${attemptLabel} recorded`;
  return `
    <div class="repair-resolved-summary">
      <span class="small-badge good">resolved after retry</span>
      <strong>${escapeHtml(summaryLabel)}</strong>
      <p>Validation is clear after a retry. Use the timeline below for validator report and repair brief evidence.</p>
      ${latest.validator_report_path ? pathLine(latest.validator_report_path, 86) : ""}
      ${latest.repair_brief_path ? pathLine(latest.repair_brief_path, 86) : ""}
    </div>
  `;
}

function renderValidationFindingList(validation) {
  const findings = actionableValidationFindings(validation);
  if (!findings.length) {
    return `<div class="empty-state">No actionable validator findings parsed.</div>`;
  }
  return `
    <div class="validation-finding-list">
      ${findings.map((finding) => renderValidationFindingSummary(finding)).join("")}
    </div>
  `;
}

function renderOutputMirrorNoticeList(validation) {
  const notices = nonBlockingValidationNotices(validation);
  if (!notices.length) return "";
  const noticeLabel = notices.length === 1 ? "1 mirror notice" : `${notices.length} mirror notices`;
  return `
    <div class="output-mirror-notice-list" role="status">
      <div class="surface-title compact">
        <span>Auto-promoted output mirrors</span>
        <span class="small-badge good">${escapeHtml(noticeLabel)}</span>
      </div>
      <p>AIDD copied misplaced output/ handoff mirrors into canonical stage documents. Continue from the canonical source document shown in each notice.</p>
      <div class="validation-finding-list">
        ${notices.map((notice) => renderValidationFindingSummary(notice, {compact: true})).join("")}
      </div>
    </div>
  `;
}

function recoveryPrimaryActionSpec(diagnostics) {
  const recoveryActions = state.dashboard?.recovery_actions || [];
  const firstFailure = state.dashboard?.first_failure || null;
  const runtimeAction = recoveryActions.find((item) => item.action === "inspect-runtime-log" && item.enabled !== false)
    || (isRuntimeFirstFailure(firstFailure)
      ? {
        action: "inspect-runtime-log",
        label: "Open logs",
        detail: firstFailure.detail || "Inspect runtime log and runtime-exit metadata before retrying.",
        stage: firstFailure.stage,
        enabled: true
      }
      : null);
  const guidedAction = runtimeAction || recoveryActions.find((item) => item.enabled !== false) || null;
  const action = guidedAction || state.dashboard?.next_action || {};
  const validation = diagnostics?.validation;
  const status = repairCenterStatus(validation, diagnostics?.stopped);
  const stage = action.stage || state.activeStage;
  if (isRuntimeFirstFailure(firstFailure) && runtimeAction) {
    return {
      action: "inspect-runtime-log",
      label: runtimeAction.label || "Open logs",
      detail: runtimeAction.detail || "Inspect the saved runtime log, runtime-exit metadata, and readiness/config context before retrying.",
      attrs: `data-recovery-action="inspect-runtime-log" data-recovery-stage="${escapeHtml(runtimeAction.stage || stage)}"`
    };
  }
  if (status === "repair-available") {
    return {
      action: "run-repair",
      label: "Run Repair",
      detail: "Run the selected stage again with the latest repair brief and normal validation.",
      attrs: "data-run-repair"
    };
  }
  if (status === "repair-exhausted" || status === "explicit-stop") {
    return {
      action: "request-change",
      label: "Request Change",
      detail: "Create a durable stage-scoped intervention request before trying another attempt.",
      attrs: `data-recovery-action="request-change" data-recovery-stage="${escapeHtml(stage)}"`
    };
  }
  if (action.action === "answer-questions") {
    return {
      action: "answer-questions",
      label: action.label || "Answer questions",
      detail: action.detail || "Resolve blocking questions before resuming execution.",
      attrs: `data-recovery-action="answer-questions" data-recovery-stage="${escapeHtml(stage)}"`
    };
  }
  if (action.action === "inspect-runtime-log") {
    return {
      action: "inspect-runtime-log",
      label: action.label || "Open logs",
      detail: action.detail || "Inspect the saved runtime log, runtime-exit metadata, and readiness/config context before retrying.",
      attrs: `data-recovery-action="inspect-runtime-log" data-recovery-stage="${escapeHtml(stage)}"`
    };
  }
  return {
    action: action.action || "inspect-blocker",
    label: action.label || "Review recovery",
    detail: action.detail || "Review the active blocker and supporting evidence.",
    attrs: `data-recovery-action="${escapeHtml(action.action || "inspect-blocker")}" data-recovery-stage="${escapeHtml(stage)}" ${action.enabled === false ? "disabled" : ""}`
  };
}

function recoveryFailureTitle(firstFailure, diagnostics) {
  if (isRuntimeFirstFailure(firstFailure)) return firstFailure.title || "Runtime failure";
  const validation = diagnostics?.validation;
  const status = repairCenterStatus(validation, diagnostics?.stopped);
  if (status === "repair-available") return "Validation needs repair";
  if (status === "repair-exhausted") return "Repair budget exhausted";
  if (diagnostics?.blocking_questions?.unresolved_count) return "Blocking questions";
  if (firstFailure?.title) return firstFailure.title;
  return "Recovery required";
}

function renderRuntimePartialEvidence(firstFailure) {
  if (!isRuntimeFirstFailure(firstFailure)) return "";
  const stage = firstFailure?.stage || state.activeStage;
  const refs = (state.dashboard?.evidence_refs || []).filter((ref) =>
    (ref.stage || state.activeStage) === stage
  );
  if (!refs.length) return "";
  const recoveryActions = (state.dashboard?.recovery_actions || []).filter((action) =>
    (action.stage || stage) === stage
  );
  const retryAction = recoveryActions.find((action) => action.action === "resume-stage");
  const requestAction = recoveryActions.find((action) => action.action === "request-change");
  const documentRefs = refs.filter((ref) => ref.kind === "document");
  const logRefs = refs.filter((ref) => ref.kind === "log");
  const selectedRefs = [...documentRefs.slice(0, 3), ...logRefs.slice(0, 3)].slice(0, 6);
  const rows = selectedRefs.map((ref) => `
    <button class="artifact-row" data-evidence-stage="${escapeHtml(ref.stage || stage)}" data-evidence-path="${escapeHtml(ref.path)}" data-evidence-kind="${escapeHtml(ref.kind)}" type="button">
      <span><strong>${escapeHtml(ref.label)}</strong>${pathLine(ref.path)}</span>
      <span class="small-badge">${escapeHtml(ref.kind)}</span>
    </button>
  `).join("");
  const actions = retryAction || requestAction ? `
    <div class="wizard-actions">
      ${retryAction ? `<button data-recovery-action="resume-stage" data-recovery-stage="${escapeHtml(stage)}" type="button" ${retryAction.enabled ? "" : "disabled"}>${escapeHtml(retryAction.label || "Retry stage")}</button>` : ""}
      ${requestAction ? `<button class="secondary" data-recovery-action="request-change" data-recovery-stage="${escapeHtml(stage)}" type="button" ${requestAction.enabled ? "" : "disabled"}>${escapeHtml(requestAction.label || "Request change")}</button>` : ""}
    </div>
  ` : "";
  return `
    <section class="surface recovery-section runtime-partial-evidence">
      <div class="surface-title">
        <span>Partial stage evidence</span>
        <span class="small-badge warn">${escapeHtml(selectedRefs.length)} refs</span>
      </div>
      <p>The runtime stopped before this stage completed. Inspect partial documents, runtime log, and runtime-exit metadata before retrying or requesting a change.</p>
      <div class="recent-artifacts">${rows}</div>
      ${actions}
    </section>
  `;
}

function renderRecoveryWorkbench() {
  const view = activeStageView();
  const diagnostics = view?.diagnostics || {};
  const validation = diagnostics.validation || {};
  const questions = view?.questions || {};
  const unresolvedQuestions = questions.unresolved_blocking_question_ids || [];
  const firstFailure = state.dashboard?.first_failure || null;
  const globalAction = state.dashboard?.next_action || {};
  const globalStage = globalAction.stage || firstFailure?.stage || "";
  const hasGlobalBlocker = Boolean(globalStage && globalStage !== state.activeStage);
  const finding = primaryValidationFinding();
  const primary = recoveryPrimaryActionSpec(diagnostics);
  const status = repairCenterStatus(validation, diagnostics.stopped);
  const selectedStage = activeStageItem();
  const selectedStageLabel = stageTitle(state.activeStage);
  const runtimeFailure = isRuntimeFirstFailure(firstFailure);
  const selectedReason = runtimeFailure
    ? firstFailure.detail || primary.detail
    : diagnostics.stopped?.detail
    || validation.primary_validation_finding?.message
    || (unresolvedQuestions.length
      ? `${unresolvedQuestions.length} blocking question(s) for ${selectedStageLabel} must be resolved.`
      : primary.detail);
  const evidencePath = runtimeFailure
    ? runtimeFailureEvidencePath(firstFailure, diagnostics)
    : finding ? validationFindingLocation(finding) : validation.validator_report_path || diagnostics.raw_log?.path || diagnostics.blocking_questions?.answers_path || state.dashboard?.evidence_refs?.[0]?.path || "Evidence not yet persisted";
  const globalBlockerDetail = globalAction.detail || firstFailure?.detail || "Resolve the run-global blocker before progressing the flow.";
  const globalBlockerLabel = globalAction.label || firstFailure?.title || "Run blocker";
  const repairAttempts = validation.repair_attempts || [];
  const hasRepairAttempts = repairAttempts.length > 0;
  const actionableFindings = actionableValidationFindings(validation);
  const hasValidationFindings = Boolean(
    finding
    || Number(validation.validator_fail_count || 0) > 0
    || actionableFindings.length
  );
  const hasValidationRecovery = hasValidationFindings || hasRepairAttempts;
  const recoveryKind = runtimeFailure
    ? "runtime"
    : unresolvedQuestions.length
      ? "question"
      : hasValidationRecovery
        ? "validation"
        : "intervention";
  return `
    <section class="recovery-workbench">
      ${renderRecoverySummary({
        kind: recoveryKind,
        status: "blocked",
        statusLabel: selectedStage?.status || status || "blocked",
        title: recoveryFailureTitle(firstFailure, diagnostics),
        consequence: selectedReason,
        decisiveFailure: {
          label: hasGlobalBlocker ? `Run-global blocker: ${globalBlockerLabel}` : `Selected stage: ${selectedStageLabel}`,
          detail: hasGlobalBlocker ? globalBlockerDetail : selectedReason
        },
        evidence: {label: runtimeFailure ? "Runtime log" : "Supporting evidence", path: evidencePath},
        primaryAction: {action: primary.action, label: primary.label, enabled: !primary.attrs.includes("disabled")}
      })}
      ${renderRuntimePartialEvidence(firstFailure)}
      ${unresolvedQuestions.length || (questions.questions || []).length ? `
        <section class="surface recovery-section">
          <div class="surface-title">
            <span>Questions</span>
            <span class="small-badge ${unresolvedQuestions.length ? "bad" : "good"}">${escapeHtml(unresolvedQuestions.length)} blocking</span>
          </div>
          ${renderQuestionCards({showResume: true})}
        </section>
      ` : ""}
      ${hasValidationRecovery ? `
        <section class="surface recovery-section">
          <div class="surface-title">
            <span>${hasValidationFindings ? "Validation finding" : "Resolved retry"}</span>
            <span class="small-badge ${hasValidationFindings && Number(validation.validator_fail_count || 0) ? "bad" : "good"}">${escapeHtml(hasValidationFindings ? status : "resolved after retry")}</span>
          </div>
          ${hasValidationFindings ? renderValidationFindingList(validation) : renderResolvedRepairSummary(validation)}
          <div class="surface-title compact">Repair attempt timeline</div>
          ${renderRepairTimeline(validation)}
        </section>
      ` : ""}
    </section>
  `;
}

function renderBlockedStageRecovery(diagnostics) {
  const blocking = diagnostics?.blocking_questions;
  const stopped = diagnostics?.stopped;
  const requestChange = diagnostics?.request_change;
  return `
    <aside class="surface repair-context-panel">
      <div class="surface-title">Recovery context</div>
      <div class="panel-item">
        <strong>Blocked questions</strong>
        <span>${escapeHtml(blocking?.unresolved_question_ids?.join(", ") || "none")}</span>
      </div>
      <div class="panel-item">
        <strong>Answers path</strong>
        ${pathLine(blocking?.answers_path || "not available", 78)}
      </div>
      <div class="panel-item">
        <strong>Stopped state</strong>
        <span>${escapeHtml(stopped?.stopped ? stopped.detail || "stopped" : "not stopped")}</span>
      </div>
      <div class="panel-item">
        <strong>Request change</strong>
        <span>${escapeHtml(requestChange?.reason || "Stage-scoped intervention can be opened from Request Change.")}</span>
      </div>
    </aside>
  `;
}

function renderValidation() {
  const view = activeStageView();
  const result = view?.result;
  const diagnostics = view?.diagnostics;
  const validation = diagnostics?.validation;
  if (!result) return `<div class="empty-state">No validation evidence for this stage yet.</div>`;
  const repairs = (result.repair_output_paths || []).map((path) => `
    <button class="artifact-row" data-open-artifact="${escapeHtml(path)}" type="button">
      <span><strong>${escapeHtml(path.split("/").pop())}</strong>${pathLine(path)}</span>
      <span class="small-badge warn">repair</span>
    </button>
  `).join("") || `<div class="empty-state">No repair outputs recorded.</div>`;
  return `
    <div class="validation-repair-center">
      <section class="surface">
        <div class="surface-title">
          <span>Validation / Repair Center</span>
          <span class="small-badge ${result.validator_fail_count ? "bad" : "good"}">${escapeHtml(repairCenterStatus(validation, diagnostics?.stopped))}</span>
        </div>
        <div class="metric-grid">
          <div class="metric"><span>Pass</span><strong>${escapeHtml(result.validator_pass_count)}</strong></div>
          <div class="metric"><span>Fail</span><strong>${escapeHtml(result.validator_fail_count)}</strong></div>
          <div class="metric"><span>Final state</span><strong>${escapeHtml(result.final_state)}</strong></div>
          <div class="metric"><span>Attempts</span><strong>${escapeHtml(result.attempt_count)}</strong></div>
        </div>
        ${(validation?.repair_attempts || []).length && !Number(result.validator_fail_count || 0) ? renderResolvedRepairSummary(validation) : ""}
        ${renderRecoveryActionBand(diagnostics)}
        <div class="panel-item">
          <strong>Validator report</strong>
          ${pathLine(result.validator_report_path)}
        </div>
        ${renderOutputMirrorNoticeList(validation)}
        <div class="panel-item">
          <strong>Actionable validation findings</strong>
          ${renderValidationFindingList(validation)}
        </div>
        <div class="panel-item">
          <strong>Repair evidence</strong>
          <div class="recent-artifacts">${repairs}</div>
        </div>
        <div class="surface-title compact">Validation attempt timeline</div>
        ${renderRepairTimeline(validation)}
      </section>
      ${renderBlockedStageRecovery(diagnostics)}
    </div>
  `;
}

async function renderCockpitContent() {
  const content = document.getElementById("cockpitContent");
  if (state.activeTab === "work") {
    if (state.workDetail === "project-home") {
      content.innerHTML = renderInboxSurface();
      return;
    }
    if (state.workDetail === "implement-review") {
      await renderImplementReview();
      return;
    }
    if (state.workDetail === "review-findings") {
      await renderReviewFindings();
      return;
    }
    if (state.workDetail === "qa-verdict") {
      await renderQaVerdict();
      return;
    }
    content.innerHTML = renderOverviewSurface();
    if (document.getElementById("studioDocumentCanvas")) {
      await loadArtifactDocument(state.activeArtifactKey);
    }
    void loadRunAccountabilityCard();
    revealNextFlowWizardOnMobile();
    return;
  }
  if (state.activeTab === "recovery") {
    if (state.recoveryDetail === "questions") {
      content.innerHTML = renderQuestions();
      updateQuestionResumeButtonStates();
      return;
    }
    if (state.recoveryDetail === "validation") {
      content.innerHTML = renderValidation();
      return;
    }
    if (state.recoveryDetail === "request") {
      await renderRequestChange();
      return;
    }
    if (state.recoveryDetail === "approvals") {
      await renderApprovals();
      return;
    }
    if (state.recoveryDetail === "logs") {
      await renderLogs();
      return;
    }
    content.innerHTML = renderRecoveryWorkbench();
    return;
  }
  if (state.activeTab === "evidence") {
    if (state.evidenceDetail === "logs") {
      await renderLogs();
      return;
    }
    await renderArtifacts();
    return;
  }
  if (state.activeTab === "history") {
    content.innerHTML = renderHistoryMode();
    void loadRunComparisonPanel();
  }
}

async function renderCockpit() {
  try {
    await renderCockpitContent();
  } finally {
    syncCurrentDecisionTarget();
  }
}

function renderProjectHomeWorkItemCard(item) {
  const selected = item.work_item === state.dashboard?.work_item;
  const run = item.latest_run || {};
  const rootChips = renderProjectSetRootChips(item);
  const blockerBadge = item.blocker_count
    ? `<span class="small-badge warn">${escapeHtml(item.blocker_count)} blocker${item.blocker_count === 1 ? "" : "s"}</span>`
    : `<span class="small-badge good">clear</span>`;
  return `
    <article class="project-work-item-card ${selected ? "selected" : ""}">
      <div class="surface-title compact">
        <span>${escapeHtml(item.work_item)}</span>
        <span class="small-badge ${workItemStatusClass(item)}">${escapeHtml(item.terminal_state)}</span>
      </div>
      <p>${escapeHtml(item.has_request_context ? "Request context ready" : "Request context missing")}</p>
      <div class="metric-grid compact">
        <div class="metric"><span>Stage</span><strong>${escapeHtml(item.active_stage)}</strong></div>
        <div class="metric"><span>Progress</span><strong>${escapeHtml(item.stage_progress_label)}</strong></div>
        <div class="metric"><span>Run</span><strong>${escapeHtml(run.run_id || "none")}</strong></div>
        <div class="metric"><span>Runtime</span><strong>${escapeHtml(run.runtime_id || "not selected")}</strong></div>
      </div>
      <div class="badge-row">${rootChips}${blockerBadge}</div>
      <div class="wizard-actions">
        <button data-operator-route-intent="inbox-work-item" data-route-work-item="${escapeHtml(item.work_item)}" type="button">Open in Studio</button>
        ${run.run_id ? `<button data-operator-route-intent="historical-run" data-route-work-item="${escapeHtml(item.work_item)}" data-route-run-id="${escapeHtml(run.run_id)}" class="secondary" type="button">Inspect run history</button>` : ""}
      </div>
    </article>
  `;
}

function renderLegacyProjectHome() {
  const home = state.projectHome;
  if (!home) return `<div class="empty-state loading-state">Loading Project Home...</div>`;
  const items = projectHomeWorkItems();
  const selected = currentWorkItemSummary();
  const blocked = items.filter((item) => item.blocker_count);
  const running = items.filter((item) => item.terminal_state === "running");
  const complete = items.filter((item) => item.terminal_state === "completed");
  return `
    <section class="project-home-screen">
      <div class="surface project-home-hero">
        <div>
          <p class="eyebrow">Project Home</p>
          <h2>Work item console</h2>
          <p class="muted">Project, work item, run, stage progress, blockers, and project-set roots are rebuilt from the selected local <code>.aidd</code> workspace.</p>
        </div>
        <div class="panel-list compact">
          <div class="panel-item"><strong>Project root</strong>${pathLine(home.project_root, 82)}</div>
          <div class="panel-item"><strong>.aidd root</strong>${pathLine(home.workspace_root, 82)}</div>
          <div class="panel-item"><strong>Selected</strong><span>${escapeHtml(selected?.work_item || "none")}</span></div>
        </div>
      </div>
      <div class="project-home-grid">
        <section class="surface">
          <div class="surface-title">
            <span>Work Item Board</span>
            <span class="small-badge">${escapeHtml(items.length)} total</span>
          </div>
          <div class="metric-grid compact">
            <div class="metric"><span>Running</span><strong>${escapeHtml(running.length)}</strong></div>
            <div class="metric"><span>Blocked</span><strong>${escapeHtml(blocked.length)}</strong></div>
            <div class="metric"><span>Done</span><strong>${escapeHtml(complete.length)}</strong></div>
            <div class="metric"><span>Workspace</span><strong>${home.workspace_exists ? "exists" : "new"}</strong></div>
          </div>
          <div class="project-work-item-grid">
            ${items.length ? items.map(renderProjectHomeWorkItemCard).join("") : `<div class="empty-state">No work items in this project yet.</div>`}
          </div>
        </section>
        <aside class="surface">
          <div class="surface-title">
            <span>Resume context</span>
            <span class="small-badge">${escapeHtml(selected?.terminal_state || "none")}</span>
          </div>
          ${selected ? `
            <div class="panel-list">
              <div class="panel-item"><strong>Work item</strong><span>${escapeHtml(selected.work_item)}</span></div>
              <div class="panel-item"><strong>Latest run</strong><span>${escapeHtml(selected.latest_run?.run_id || "none")}</span></div>
              <div class="panel-item"><strong>Next stage</strong><span>${escapeHtml(selected.active_stage)}</span></div>
              <div class="panel-item"><strong>Blockers</strong><span>${escapeHtml(selected.blocker_count)}</span></div>
            </div>
            <div class="surface-title compact">Project-set roots</div>
            <div class="compact-list">
              ${(selected.project_set_roots || []).map((root) => `<span title="${escapeHtml(root.root)}">${escapeHtml(root.root_id)} / ${escapeHtml(root.relative_root)}${root.role ? ` / ${escapeHtml(root.role)}` : ""}</span>`).join("") || "<span>Single project root</span>"}
            </div>
          ` : `<div class="empty-state">Select a work item to inspect resume context.</div>`}
        </aside>
      </div>
    </section>
  `;
}

function renderInboxSurface() {
  const {renderer} = selectSurfaceRenderer("inbox", {
    legacy: renderLegacyProjectHome,
    studio: renderStudioInbox
  });
  return renderer();
}

function renderBlockersPanel() {
  const blockers = state.dashboard?.blockers || [];
  const body = blockers.length ? blockers.map((blocker) => `
    <button class="artifact-row" data-blocker-stage="${escapeHtml(blocker.stage || state.activeStage)}" data-blocker-kind="${escapeHtml(blocker.kind)}" type="button">
      <span>
        <strong>${escapeHtml(blocker.title)}</strong>
        <span>${escapeHtml(blocker.detail)}</span>
        ${blocker.path ? pathLine(blocker.path) : ""}
      </span>
      <span class="small-badge ${blocker.severity === "error" ? "bad" : "warn"}">${escapeHtml(blocker.kind)}</span>
    </button>
  `).join("") : `<p>No blockers detected for the selected stage.</p>`;
  document.getElementById("blockersPanel").innerHTML = `
    <div class="panel-title">Blockers <span class="small-badge ${blockers.length ? "warn" : "good"}">${escapeHtml(blockers.length)}</span></div>
    <div class="panel-list">${body}</div>
  `;
}

function renderEvidencePanel() {
  const refs = state.dashboard?.evidence_refs || [];
  const open = state.activeTab === "evidence";
  const body = refs.length ? refs.slice(0, 6).map((ref) => `
    <button class="artifact-row" data-evidence-stage="${escapeHtml(ref.stage || state.activeStage)}" data-evidence-path="${escapeHtml(ref.path)}" data-evidence-kind="${escapeHtml(ref.kind)}" type="button">
      <span><strong>${escapeHtml(ref.label)}</strong>${pathLine(ref.path)}</span>
      <span class="small-badge">${escapeHtml(ref.kind)}</span>
    </button>
  `).join("") : `<p>No evidence refs yet.</p>`;
  document.getElementById("evidencePanel").innerHTML = `
    <details class="secondary-drilldown" ${open ? "open" : ""}>
      <summary><span>Evidence refs</span><span class="small-badge">${escapeHtml(refs.length)}</span></summary>
      <div class="panel-list">${body}</div>
    </details>
  `;
}

function renderRecoveryAssistantPanel() {
  const host = document.getElementById("recoveryAssistantPanel");
  if (!host) return;
  const firstFailure = state.dashboard?.first_failure || null;
  const actions = state.dashboard?.recovery_actions || [];
  const questionCount = (state.dashboard?.stages || []).reduce((total, item) => total + Number(item.unresolved_blocking_count || 0), 0);
  const failureCount = firstFailure ? 1 : 0;
  host.innerHTML = `
    <div class="panel-title">Recovery Assistant</div>
    <div class="filter-row compact">
      <span class="small-badge ${questionCount ? "warn" : ""}">Questions ${escapeHtml(questionCount)}</span>
      <span class="small-badge ${failureCount ? "bad" : ""}">Failures ${escapeHtml(failureCount)}</span>
      <span class="small-badge">Suggestions ${escapeHtml(actions.length)}</span>
    </div>
    <button class="secondary" data-tab-shortcut="recovery" type="button" ${firstFailure || questionCount || actions.length ? "" : "disabled"}>Open Recovery Summary</button>
  `;
}

function renderRuntimeRootPanel() {
  const workspace = state.dashboard?.workspace_root || "";
  document.getElementById("runtimeRootPanel").innerHTML = `
    <details class="secondary-drilldown">
      <summary><span>Runtime root</span><span class="small-badge">.aidd</span></summary>
      <p><code>.aidd/</code></p>
      ${pathLine(workspace)}
      <button data-open-folder="workspace" class="next-button secondary" type="button">Open folder</button>
    </details>
  `;
}

function renderSafetyPanel() {
  const runtime = selectedRuntimeView();
  const badge = runtime
    ? runtime.runtime_id
    : state.readinessLoading
      ? "checking"
      : state.readinessError
        ? "error"
        : "none";
  let details = "";
  if (state.readinessLoading) {
    details = readinessDetail("Status", "checking runtimes");
  } else if (!runtime && state.readinessError) {
    details = readinessDetail("Status", `readiness unavailable: ${state.readinessError}`);
  } else if (!runtime) {
    details = readinessDetail("Status", "select a runtime to view readiness");
  } else {
    details = [
      readinessDetail("Support tier", runtime.support_tier),
      readinessDetail("Command source", runtime.command_source),
      readinessDetail("Command", runtime.command, 86),
      readinessDetail("Execution mode", runtime.execution_mode),
      readinessDetail("Permission policy", runtime.permission_policy),
      readinessDetail("Interaction mode", runtime.interaction_mode),
      readinessDetail("Auto approval", runtime.auto_approval_preset),
      readinessDetail("Timeouts", timeoutSummary(runtime), 96),
      renderRuntimeReadinessDimensions(runtime),
      renderProtectedWriteScope()
    ].join("");
  }
  document.getElementById("safetyPanel").innerHTML = `
    <details class="secondary-drilldown" ${activeModeIsEvidenceLog() ? "open" : ""}>
      <summary><span>Safety / Readiness</span><span class="small-badge">${escapeHtml(badge)}</span></summary>
      <div class="panel-list">
        ${details}
      </div>
    </details>
  `;
}

function renderSidebar() {
  if (typeof renderActiveRunPanel === "function") renderActiveRunPanel();
  renderNextActionPanel();
  renderBlockersPanel();
  renderRecoveryAssistantPanel();
  renderEvidencePanel();
  renderRuntimeRootPanel();
  renderSafetyPanel();
}

function liveJobActivityEvents() {
  if (!state.activeJobStatus) return [];
  const status = state.activeJobStatus.status || "running";
  const events = [{
    time_utc: state.activeJobStatus.updated_at_utc || "live",
    level: status === "failed" ? "error" : status === "running" ? "info" : "info",
    source: state.activeJobStatus.stage || state.activeJobStatus.kind || "job",
    event: `job.${status}`,
    details: state.activeJobStatus.message || `UI-started ${state.activeJobStatus.kind || "job"} is ${status}.`
  }];
  const entries = logEntriesFromChunks(state.activeJobLogChunks).slice(-10).reverse();
  for (const entry of entries) {
    events.push({
      time_utc: "live",
      level: entry.stream === "stderr" ? "warn" : "info",
      source: entry.source || entry.stream || "runtime",
      event: `job.${entry.stream || "output"}`,
      details: entry.text
    });
  }
  return events;
}

function activityEvents() {
  return [
    ...liveJobActivityEvents(),
    ...(state.dashboard?.activity || [])
  ];
}

function summarizeActivityDetails(details) {
  const raw = String(details ?? "");
  const normalized = raw.replace(/\s+/g, " ").trim();
  if (!normalized) return {summary: "-", raw: "", showRaw: false};
  let summary = normalized;
  if (/^[\[{]/.test(normalized)) {
    try {
      const parsed = JSON.parse(normalized);
      if (Array.isArray(parsed)) {
        summary = `JSON array (${parsed.length} items)`;
      } else if (parsed && typeof parsed === "object") {
        const keys = Object.keys(parsed);
        const type = parsed.type || parsed.event || parsed.kind || parsed.name || "JSON event";
        const outcome = parsed.status || parsed.outcome || parsed.message || "";
        summary = [type, outcome, keys.length ? `keys: ${keys.slice(0, 6).join(", ")}` : ""]
          .filter(Boolean)
          .join(" / ");
      }
    } catch (_) {
      summary = normalized;
    }
  }
  const compact = summary.length > 220 ? `${summary.slice(0, 217)}...` : summary;
  const rawPreview = normalized.length > 2400 ? `${normalized.slice(0, 2400)}...` : normalized;
  return {
    summary: compact,
    raw: rawPreview,
    showRaw: normalized !== compact,
    rawTruncated: normalized.length > rawPreview.length
  };
}

function renderActivityDetail(details) {
  const detail = summarizeActivityDetails(details);
  if (!detail.showRaw) {
    return escapeHtml(detail.summary);
  }
  return `
    <details class="activity-detail">
      <summary>${escapeHtml(detail.summary)}</summary>
      <pre>${escapeHtml(detail.raw)}${detail.rawTruncated ? "\n...[raw truncated in UI]" : ""}</pre>
    </details>
  `;
}

function renderActivityTableMarkup(events) {
  if (!events.length) {
    return `<div class="empty-state">No activity for this run yet.</div>`;
  }
  return `
    <table class="activity-table">
      <thead><tr><th>Time</th><th>Level</th><th>Event</th><th>Details</th></tr></thead>
      <tbody>
        ${events.map((event) => `
          <tr>
            <td>${escapeHtml(event.time_utc || "-")}</td>
            <td><span class="small-badge ${event.level === "error" ? "bad" : event.level === "warn" ? "warn" : ""}">${escapeHtml(event.level)}</span></td>
            <td>${escapeHtml(event.source)} / ${escapeHtml(event.event)}</td>
            <td>${renderActivityDetail(event.details)}</td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderActivityTable() {
  const host = document.getElementById("activityTable");
  if (!host) return;
  host.innerHTML = renderActivityTableMarkup(activityEvents());
}

function renderHistoryMode() {
  return `
    <div class="history-mode hierarchy-sequence">
      ${renderRunHistory()}
      <section class="surface hierarchy-supporting history-events">
        <div class="surface-title">
          <span>Activity / Events</span>
          <span class="small-badge">${escapeHtml(activityEvents().length)} events</span>
        </div>
        <div class="table-wrap">${renderActivityTableMarkup(activityEvents())}</div>
      </section>
    </div>
  `;
}

function renderRecentArtifacts() {
  const refs = state.dashboard?.recent_artifacts || [];
  document.getElementById("recentArtifacts").innerHTML = refs.length ? refs.map((ref) => `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(ref.stage)}" data-artifact-key="${escapeHtml(ref.key)}" data-artifact-kind="${escapeHtml(ref.kind)}" type="button">
      <span><strong>${escapeHtml(ref.stage)} / ${escapeHtml(ref.key)}</strong>${pathLine(ref.path)}</span>
      <span class="small-badge">${escapeHtml(ref.kind)}</span>
    </button>
  `).join("") : `<div class="empty-state">No artifacts yet.</div>`;
}

function bottomDockDefaultCollapsed() {
  if (!state.dashboard?.run?.run_id) return false;
  if (state.nextFlowWizard.active) return true;
  if (state.activeTab === "evidence" || state.activeTab === "recovery") return true;
  if (state.activeTab === "work") {
    if (state.dashboard?.terminal_handoff) return true;
    return state.workDetail !== "overview";
  }
  return false;
}

function bottomDockIsCollapsed() {
  if (state.bottomDockUserCollapsed === true || state.bottomDockUserCollapsed === false) {
    return state.bottomDockUserCollapsed;
  }
  return bottomDockDefaultCollapsed();
}

function renderBottomDock() {
  const dock = document.querySelector(".bottom-dock");
  if (!dock) return;
  const collapsed = bottomDockIsCollapsed();
  document.body.classList.toggle("bottom-dock-collapsed", collapsed);
  dock.classList.toggle("collapsed", collapsed);
  dock.setAttribute("aria-expanded", collapsed ? "false" : "true");
  dock.innerHTML = `
    <div class="bottom-dock-toggle-row">
      <span>Activity / Recent artifacts</span>
      <button data-bottom-dock-toggle class="link-button" type="button">${collapsed ? "Show activity" : "Hide activity"}</button>
    </div>
    ${collapsed ? "" : `
      <div class="dock-panel activity-panel">
        <div class="dock-header">
          <span>Activity / Events</span>
          <button id="viewFullLogButton" class="link-button" type="button">View full log</button>
        </div>
        <div id="activityTable" class="table-wrap"></div>
      </div>
      <div class="dock-panel artifacts-panel">
        <div class="dock-header">
          <span>Recent artifacts</span>
          <button id="openStageFolderButton" class="link-button" type="button">Open stage folder</button>
        </div>
        <div id="recentArtifacts" class="recent-artifacts"></div>
      </div>
    `}
  `;
  if (!collapsed) {
    renderActivityTable();
    renderRecentArtifacts();
  }
}

async function renderAll() {
  document.body.classList.remove("setup-active");
  document.getElementById("openWorkspaceButton").disabled = false;
  renderRuntimeSelector();
  renderTopbar();
  renderProjectHomeRail();
  renderStageRail();
  renderStageHeader();
  applyActiveStudioShellPresentation();
  renderGlobalNextActionStrip();
  updateContextualTabs();
  renderSidebar();
  renderBottomDock();
  activateTab(state.activeTab, {preserveDetail: true});
  await renderCockpit();
  revealCockpitOnMobile();
}
