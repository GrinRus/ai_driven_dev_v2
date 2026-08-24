const RUNTIME_FAILURE_KINDS = new Set([
  "cancelled",
  "cancellation",
  "authentication_failure",
  "authentication-failure",
  "failed",
  "non_zero_exit",
  "non-zero-exit",
  "provider_error",
  "provider-no-progress",
  "runtime-error",
  "runtime_failure",
  "launch_failure",
  "launch-failure",
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

function renderOverviewSurface() {
  return renderActiveStudio();
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

function renderRepairExtensionPreview(validation) {
  const preview = validation?.repair_extension;
  if (!preview) return "";
  const eligible = preview.eligible === true;
  const cause = preview.primary_cause;
  const findings = preview.current_findings || [];
  const downstream = preview.downstream_succeeded || [];
  const disabledReason = String(preview.disabled_reason || "").trim();
  const causeMarkup = cause
    ? renderValidationFindingSummary(cause, {compact: true})
    : `<div class="empty-state">No primary cause recorded.</div>`;
  return `
    <section class="repair-extension-preview" data-repair-extension-preview data-repair-extension-eligible="${eligible ? "true" : "false"}">
      <div class="surface-title compact">
        <span>One more repair preview</span>
        <span class="small-badge ${eligible ? "warn" : "bad"}">${eligible ? "eligible" : "blocked"}</span>
      </div>
      <p>${escapeHtml(eligible
        ? "Runs exactly one repair-extension attempt without resetting automatic repair history or budget."
        : disabledReason || "Repair extension is not eligible for this stage.")}</p>
      <dl class="recovery-decision-facts">
        <div><dt>Automatic budget</dt><dd>${escapeHtml(`${preview.automatic_repair_attempts_used}/${preview.automatic_repair_attempts_max} used; ${preview.automatic_repair_attempts_remaining} remaining`)}</dd></div>
        <div><dt>Manual grant</dt><dd>${escapeHtml(preview.manual_grant_used ? "already used" : "unused")}</dd></div>
        <div><dt>Selected Runner</dt><dd>${escapeHtml(preview.selected_runner || preview.runtime_id || "not selected")}</dd></div>
        <div><dt>Downstream</dt><dd>${escapeHtml(downstream.length ? downstream.join(", ") : "none succeeded")}</dd></div>
      </dl>
      <div class="panel-item"><strong>Primary cause</strong>${causeMarkup}</div>
      <div class="panel-item"><strong>Current findings</strong><span>${escapeHtml(findings.length)}</span></div>
      <div class="panel-item"><strong>Validator evidence</strong>${pathLine(preview.validator_report_path || "not available", 86)}<code>${escapeHtml(preview.validator_report_sha256 || "hash unavailable")}</code></div>
      <div class="panel-item"><strong>Repair brief evidence</strong>${pathLine(preview.repair_brief_path || "not available", 86)}<code>${escapeHtml(preview.repair_brief_sha256 || "hash unavailable")}</code></div>
      ${preview.configuration_identity ? `<div class="panel-item"><strong>Configuration identity</strong><code>${escapeHtml(preview.configuration_identity)}</code></div>` : ""}
    </section>
  `;
}

function renderRecoveryActionBand(diagnostics) {
  return renderRecoveryActionBandInternal(diagnostics, {showPrimary: true});
}

function renderRecoveryActionBandReadOnly(diagnostics) {
  return renderRecoveryActionBandInternal(diagnostics, {showPrimary: false});
}

function renderRecoveryActionBandInternal(diagnostics, {showPrimary = true} = {}) {
  const validation = diagnostics?.validation;
  const stopped = diagnostics?.stopped;
  const status = repairCenterStatus(validation, stopped);
  const repairAvailable = status === "repair-available";
  const requestPrimary = status === "repair-exhausted" || status === "explicit-stop";
  const extensionPreview = validation?.repair_extension;
  const extensionEligible = status === "repair-exhausted" && extensionPreview?.eligible === true;
  const stoppedMessage = stopped?.stopped ? stopped.detail || "Stage stopped." : "";
  const finding = primaryValidationFindingForValidation(validation);
  const guidance = stoppedMessage
    || (repairAvailable
      ? "Validation failed. Run Repair starts the selected stage through the normal stage runner."
      : status === "repair-exhausted"
        ? extensionEligible
          ? "Automatic repair is exhausted. Run one more repair is a single explicitly authorized extension; Request Change and Start new run remain separate alternatives."
          : extensionPreview?.disabled_reason || "Validation still fails after repair attempts. Request Change creates an operator intervention for this stage."
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
      ${renderRepairExtensionPreview(validation)}
      <div class="repair-actions">
        ${repairAvailable && typeof renderContextualRunnerControl === "function" ? renderContextualRunnerControl({actionLabel: "validation repair"}) : extensionEligible && typeof renderContextualRunnerControl === "function" ? renderContextualRunnerControl({actionLabel: "one more repair"}) : ""}
        ${showPrimary ? extensionEligible ? `<button data-recovery-action="repair-extension" data-recovery-stage="${escapeHtml(state.activeStage)}" data-repair-extension type="button">Run one more repair</button>` : requestPrimary ? `<button data-recovery-action="request-change" data-recovery-stage="${escapeHtml(state.activeStage)}" type="button">Request Change</button>` : `<button data-run-repair type="button" ${repairAvailable ? "" : "disabled"}>Run Repair</button>` : `<span class="muted">Primary recovery action is shown above.</span>`}
        ${requestPrimary && extensionEligible ? `<button data-recovery-action="request-change" data-recovery-stage="${escapeHtml(state.activeStage)}" type="button" class="secondary">Request Change</button><button data-work-item-tab="overview" type="button" class="secondary">Start new run</button>` : requestPrimary ? `<button type="button" class="secondary" disabled aria-disabled="true">${status === "explicit-stop" ? "Repair unavailable" : "Repair exhausted"}</button>` : `<button data-tab-shortcut="request" type="button" class="secondary">Request Change</button>`}
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
  const retryAction = recoveryActions.find((item) =>
    item.action === "resume-stage" && item.enabled !== false
  ) || null;
  const guidedAction = retryAction || runtimeAction || recoveryActions.find((item) => item.enabled !== false) || null;
  const action = guidedAction || state.dashboard?.next_action || {};
  const validation = diagnostics?.validation;
  const status = repairCenterStatus(validation, diagnostics?.stopped);
  const stage = action.stage || state.activeStage;
  if (isRuntimeFirstFailure(firstFailure) && retryAction) {
    return {
      action: "resume-stage",
      label: retryAction.label || "Retry stage",
      detail: `${retryAction.detail || "Retry the stopped stage after inspecting the saved runtime evidence."} Runtime failure does not consume validation repair budget.`,
      attrs: `data-recovery-action="resume-stage" data-recovery-stage="${escapeHtml(retryAction.stage || stage)}"`
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
  if (status === "repair-exhausted" && validation?.repair_extension?.eligible === true) {
    return {
      action: "repair-extension",
      label: "Run one more repair",
      detail: "Run exactly one explicitly authorized repair extension without resetting automatic history or budget.",
      attrs: `data-recovery-action="repair-extension" data-recovery-stage="${escapeHtml(stage)}" data-repair-extension`
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

function renderRecoveryDecisionWorkbench({runtimeFailure, firstFailure, diagnostics, validation, status, evidencePath, primary}) {
  const mode = runtimeFailure ? "runtime" : "validation";
  const runtimeDetail = firstFailure?.detail || "Inspect the first decisive runtime failure before retrying or cancelling.";
  const validationFinding = primaryValidationFindingForValidation(validation);
  const validationLocation = validationFinding ? validationFindingLocation(validationFinding) : validation?.validator_report_path || evidencePath;
  const repairAttempts = validation?.repair_attempts || [];
  const budgetLabel = status === "repair-exhausted"
    ? "exhausted"
    : validation?.repair_budget_remaining ?? validation?.remaining_repair_budget ?? (status === "repair-available" ? "available" : "not reported");
  return `
    <section class="recovery-decision-workbench" data-recovery-mode="${mode}" data-repair-budget="${escapeHtml(budgetLabel)}">
      <div class="recovery-decision-heading">
        <span class="small-badge ${runtimeFailure ? "bad" : status === "repair-exhausted" ? "bad" : "warn"}">${runtimeFailure ? "Runtime recovery" : "Validation recovery"}</span>
        <strong>${runtimeFailure ? "Runtime failure recovery" : "Validation failure recovery"}</strong>
        <p>${escapeHtml(runtimeFailure ? runtimeDetail : validation?.primary_validation_finding?.message || "A validator finding must be repaired or explicitly routed to Request Change.")}</p>
      </div>
      <dl class="recovery-decision-facts">
        <div><dt>First decisive signal</dt><dd data-recovery-decisive-signal>${escapeHtml(runtimeFailure ? (firstFailure?.kind || "runtime failure") : (validationFinding?.rule || validation?.validator_report_path || "validator finding"))}</dd></div>
        <div><dt>Evidence</dt><dd data-recovery-evidence>${escapeHtml(runtimeFailure ? (runtimeFailureEvidencePath(firstFailure, diagnostics) || "runtime log unavailable") : (validationLocation || "validator evidence unavailable"))}</dd></div>
        <div><dt>${runtimeFailure ? "Retry consequence" : "Repair budget"}</dt><dd data-recovery-consequence>${escapeHtml(runtimeFailure ? "Retry does not consume validation repair budget; cancel leaves the durable failed attempt unchanged." : `${budgetLabel} budget; exhaustion fails closed to Request Change.`)}</dd></div>
        <div><dt>Primary action</dt><dd data-recovery-primary>${escapeHtml(primary?.label || (runtimeFailure ? "Open logs" : status === "repair-available" ? "Run Repair" : "Request Change"))}</dd></div>
      </dl>
      <div class="recovery-decision-actions">
        ${runtimeFailure ? `<button data-recovery-action="inspect-runtime-log" data-recovery-stage="${escapeHtml(firstFailure?.stage || state.activeStage)}" type="button">Open logs</button><button data-recovery-action="resume-stage" data-recovery-stage="${escapeHtml(firstFailure?.stage || state.activeStage)}" type="button" ${primary?.action === "resume-stage" ? "" : "disabled"}>Retry stage</button><button data-stop-run type="button" class="danger">Cancel</button>` : `<span class="muted">Use the single bounded recovery action below; this panel is read-only evidence.</span>`}
      </div>
      <span class="muted recovery-decision-attempts">${escapeHtml(runtimeFailure ? "Runtime retry is separate from validation repair attempts." : `${repairAttempts.length} validation repair attempt${repairAttempts.length === 1 ? "" : "s"} retained.`)}</span>
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
    <section class="recovery-workbench" data-recovery-kind="${escapeHtml(recoveryKind)}" data-runtime-failure-kind="${escapeHtml(runtimeFailure ? firstFailure.kind : "")}" data-runtime-stopped="${runtimeFailure ? "true" : "false"}" data-runtime-last-signal="${escapeHtml(runtimeFailure ? evidencePath : "")}" data-validation-repair-budget-consumed="false">
      ${renderRecoveryDecisionWorkbench({runtimeFailure, firstFailure, diagnostics, validation, status, evidencePath, primary})}
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
        primaryAction: {
          action: primary.action,
          label: primary.label,
          stage: state.activeStage,
          enabled: !primary.attrs.includes("disabled")
        }
      })}
      ${!runtimeFailure ? renderRecoveryActionBandReadOnly(diagnostics) : ""}
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

async function renderCockpitContent({skipArtifactLoad = false} = {}) {
  const content = document.getElementById("intentContent");
  if (state.activeTab === "work") {
    if (state.workDetail === "project-home") {
      content.innerHTML = renderInboxSurface();
      return;
    }
    if (["tasks", "runs"].includes(state.workDetail)) {
      if (state.workDetail === "tasks") {
        await renderWorkItemTasks();
      } else {
        await renderWorkItemRuns();
      }
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
    if (!skipArtifactLoad && document.getElementById("studioDocumentCanvas")) {
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
    content.innerHTML = await renderHistoryMode();
    void loadRunComparisonPanel();
  }
}

async function renderCockpit({skipArtifactLoad = false} = {}) {
  try {
    await renderCockpitContent({skipArtifactLoad});
  } finally {
    syncIntentShellRegions();
    syncCurrentDecisionTarget();
  }
}

function syncIntentShellRegions() {
  const content = document.getElementById("intentContent");
  const context = document.getElementById("intentContext");
  const phases = document.getElementById("intentPhaseStepper");
  if (!content || !context || !phases) return;
  context.replaceChildren();
  phases.replaceChildren();
  const contextBar = content.querySelector("[data-studio-context-bar]");
  const phaseStepper = content.querySelector("[data-intent-phase-stepper]");
  const inbox = state.activeTab === "work" && state.workDetail === "project-home";
  const hasWorkItem = Boolean(state.dashboard?.work_item || state.activeRouteWorkItem);
  if (contextBar) {
    context.appendChild(contextBar);
  } else if (!inbox && hasWorkItem && typeof renderActiveStudioContextBar === "function") {
    // Recovery, History, and Flow Complete are rendered by their own surfaces and
    // historically omitted the shared Work Item identity. Keep the target shell
    // persistent without changing those surface-specific documents or actions.
    context.innerHTML = renderActiveStudioContextBar(activeStudioState(), activeStageItem());
  }
  if (phaseStepper) {
    phases.appendChild(phaseStepper);
  } else if (!inbox && hasWorkItem && state.dashboard?.stages?.length && typeof renderIntentPhaseStepper === "function") {
    phases.innerHTML = renderIntentPhaseStepper();
  }
}

function renderInboxSurface() {
  return renderStudioInbox();
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
  document.getElementById("technicalBlockers").innerHTML = `
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
  document.getElementById("technicalEvidence").innerHTML = `
    <details class="secondary-drilldown" ${open ? "open" : ""}>
      <summary><span>Evidence refs</span><span class="small-badge">${escapeHtml(refs.length)}</span></summary>
      <div class="panel-list">${body}</div>
    </details>
  `;
}

function renderRecoveryAssistantPanel() {
  const host = document.getElementById("technicalRecovery");
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
  document.getElementById("technicalRuntime").innerHTML = `
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
  document.getElementById("technicalSafety").innerHTML = `
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

function renderReadinessSurfaces() {
  renderRuntimeSelector();
  renderTopbar();
  renderSafetyPanel();
  const studioReadiness = document.querySelector("[data-studio-runtime-readiness]");
  if (studioReadiness) {
    studioReadiness.outerHTML = renderActiveStudioRuntimeReadiness();
  }
  if (typeof updateSubmitInterventionState === "function") {
    updateSubmitInterventionState();
  }
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
  const host = document.getElementById("technicalActivity");
  if (!host) return;
  host.innerHTML = `
    <div class="technical-region-header">
      <strong>Activity / Events</strong>
      <button id="viewFullLogButton" class="link-button" type="button">View full log</button>
    </div>
    ${renderActivityTableMarkup(activityEvents())}
  `;
}

async function renderHistoryMode() {
  return renderStudioHistory(await loadStudioHistoryTimeline());
}

function renderRecentArtifacts() {
  const refs = state.dashboard?.recent_artifacts || [];
  const host = document.getElementById("technicalArtifacts");
  if (!host) return;
  host.innerHTML = `
    <div class="technical-region-header">
      <strong>Recent artifacts</strong>
      <button id="openStageFolderButton" class="link-button" type="button">Open stage folder</button>
    </div>
    ${refs.length ? refs.map((ref) => `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(ref.stage)}" data-artifact-key="${escapeHtml(ref.key)}" data-artifact-kind="${escapeHtml(ref.kind)}" type="button">
      <span><strong>${escapeHtml(ref.stage)} / ${escapeHtml(ref.key)}</strong>${pathLine(ref.path)}</span>
      <span class="small-badge">${escapeHtml(ref.kind)}</span>
    </button>
  `).join("") : `<div class="empty-state">No artifacts yet.</div>`}
  `;
}

function renderTechnicalRegions() {
  renderActivityTable();
  renderRecentArtifacts();
}

async function renderAll({skipArtifactLoad = false} = {}) {
  document.body.classList.remove("setup-active");
  document.getElementById("openWorkspaceButton").disabled = false;
  document.getElementById("newWorkItemButton").disabled = false;
  renderRuntimeSelector();
  renderTopbar();
  renderProjectHomeRail();
  renderWorkItemTabs();
  renderStageRail();
  renderStageHeader();
  applyActiveStudioShellPresentation();
  updateContextualTabs();
  renderSidebar();
  renderTechnicalRegions();
  renderGlobalNextActionStrip();
  activateTab(state.activeTab, {preserveDetail: true});
  await renderCockpit({skipArtifactLoad});
  revealCockpitOnMobile();
}
