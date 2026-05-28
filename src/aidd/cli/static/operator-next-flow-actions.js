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

function renderSetupModeSelector(context) {
  const activeMode = setupModeView(context);
  return `
    <div class="setup-mode-grid" role="radiogroup" aria-label="Execution mode">
      ${SETUP_MODES.map((mode) => {
        const selected = mode.id === activeMode.id;
        const blocked = mode.requiresPreviousRun && !context.available;
        return `
          <button
            class="setup-mode-card${selected ? " selected" : ""}"
            data-setup-mode="${escapeHtml(mode.id)}"
            type="button"
            role="radio"
            aria-checked="${selected ? "true" : "false"}"
            ${blocked ? 'aria-disabled="true" disabled' : ""}
          >
            <strong>${escapeHtml(mode.label)}</strong>
            <span>${escapeHtml(mode.detail)}</span>
            <em>${blocked ? "needs previous run" : selected ? "selected" : "available"}</em>
          </button>
        `;
      }).join("")}
    </div>
  `;
}

function renderPreviousRunContext(context) {
  if (!context.available) {
    return `
      <div class="empty-state previous-run-context">
        No previous-run context selected for this workspace.
      </div>
    `;
  }
  const artifacts = context.finalArtifacts.slice(0, 4).map((artifact) => `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(artifact.stage)}" data-artifact-key="${escapeHtml(artifact.key)}" data-artifact-kind="${escapeHtml(artifact.kind)}" type="button">
      <span><strong>${escapeHtml(artifact.key)}</strong>${pathLine(artifact.path)}</span>
      <span class="small-badge">${escapeHtml(artifact.kind)}</span>
    </button>
  `).join("");
  const approvals = context.approvalCounts
    ? `${context.approvalCounts.approved}/${context.approvalCounts.requested} approved`
    : "not recorded";
  return `
    <div class="previous-run-context">
      <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(context.sourceRunId || "not recorded")}</span></div>
      <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(context.sourceWorkItem || "not recorded")}</span></div>
      <div class="panel-item"><strong>Baseline</strong><span>${escapeHtml(context.baseline || "source run")}</span></div>
      <div class="panel-item"><strong>Approval evidence</strong><span>${escapeHtml(approvals)}</span></div>
      <div class="panel-item"><strong>Blockers</strong><span>${escapeHtml(context.blockers.length)}</span></div>
      <div class="recent-artifacts">${artifacts || '<div class="empty-state">No final artifacts recorded.</div>'}</div>
    </div>
  `;
}

function renderFirstLaunchState() {
  const runtime = selectedRuntimeView();
  const ready = selectedRuntimeReady();
  const context = setupPreviousRunContext();
  const mode = setupModeView(context);
  const detail = !state.selectedRuntime
    ? "Select a runtime to start the first governed workflow run."
    : ready
      ? `${state.selectedRuntime} is ready to start the workflow.`
      : `${state.selectedRuntime} needs a passing readiness check before the first run.`;
  return `
    <section class="surface first-launch-state project-setup-state">
      <div class="surface-title">
        <span>Project Setup</span>
        <span class="small-badge">${escapeHtml(mode.label)}</span>
      </div>
      <div class="project-setup-grid">
        <div class="setup-primary">
          <p>${escapeHtml(detail)}</p>
          ${renderSetupModeSelector(context)}
          <div class="setup-actions">
            <button data-first-launch-run type="button" ${ready && runtime ? "" : "disabled"}>Run workflow</button>
            <span class="muted">Work item ${escapeHtml(state.dashboard?.work_item || "unknown")}</span>
          </div>
        </div>
        <aside class="setup-context" aria-label="Previous-run context">
          <div class="surface-title">
            <span>Previous-run context</span>
            <span class="small-badge ${context.available ? "good" : ""}">${context.available ? "available" : "none"}</span>
          </div>
          ${renderPreviousRunContext(context)}
        </aside>
      </div>
    </section>
  `;
}

function terminalHandoffTone(status) {
  if (status === "completed") return "good";
  if (status === "completed-with-warning" || status === "blocked") return "warn";
  if (status === "failed") return "bad";
  return "";
}

function terminalHandoffTitle(handoff) {
  if (handoff.status === "completed" || handoff.status === "completed-with-warning") {
    return "Flow Complete";
  }
  return "Flow Needs Attention";
}

function renderHandoffMetric({label, value, detail, tone = ""}) {
  return `
    <div class="metric handoff-metric">
      <span>${escapeHtml(label)}</span>
      <strong class="${tone ? `metric-${tone}` : ""}">${escapeHtml(value)}</strong>
      <small>${escapeHtml(detail)}</small>
    </div>
  `;
}

function approvalSummary(counts) {
  if (!counts) return {value: "0 / 0", detail: "No approvals requested."};
  const value = `${counts.approved || 0} / ${counts.requested || 0}`;
  const details = [];
  if (counts.pending) details.push(`${counts.pending} pending`);
  if (counts.denied) details.push(`${counts.denied} denied`);
  if (counts.cancelled) details.push(`${counts.cancelled} cancelled`);
  return {value, detail: details.length ? details.join(", ") : "All requested approvals resolved."};
}

function repairSummary(counts) {
  if (!counts) return {value: "0", detail: "No repair attempts recorded."};
  const details = [];
  if (counts.succeeded) details.push(`${counts.succeeded} succeeded`);
  if (counts.failed) details.push(`${counts.failed} failed`);
  return {value: counts.attempts || 0, detail: details.length ? details.join(", ") : "No repairs applied."};
}

function nextFlowButtonLabel(action) {
  if (action.action === "create-new-work-item") return "Create New";
  if (action.action === "start-follow-up-flow") return "Start Follow-up";
  if (action.action === "clone-flow") return "Clone Flow";
  if (action.action === "run-eval-batch") return "Run Batch";
  if (action.action === "archive-run") return "Archive Run";
  return action.label;
}

function recommendedNextFlowAction(handoff) {
  if (handoff.status === "completed" && !handoff.blockers?.length) {
    return "create-new-work-item";
  }
  return "start-follow-up-flow";
}

function renderNextFlowActions(handoff) {
  const recommended = recommendedNextFlowAction(handoff);
  const actions = handoff.recommended_next_flow_actions || [];
  return `
    <div class="next-flow-actions-grid">
      ${actions.map((action) => {
        const isRecommended = action.action === recommended;
        return `
          <article class="next-flow-action-card${isRecommended ? " recommended" : ""}">
            <div class="action-card-title">
              <strong>${escapeHtml(action.label)}</strong>
              ${isRecommended ? '<span class="small-badge good">recommended</span>' : ""}
            </div>
            <p>${escapeHtml(action.detail)}</p>
            <button data-next-flow-action="${escapeHtml(action.action)}" type="button" ${action.enabled ? "" : "disabled"}>
              ${escapeHtml(nextFlowButtonLabel(action))}
            </button>
          </article>
        `;
      }).join("")}
    </div>
  `;
}

function renderTerminalArtifacts(artifacts) {
  const visible = (artifacts || []).slice(0, 5);
  if (!visible.length) return `<div class="empty-state">No final artifacts recorded.</div>`;
  return visible.map((artifact) => `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(artifact.stage)}" data-artifact-key="${escapeHtml(artifact.key)}" data-artifact-kind="${escapeHtml(artifact.kind)}" type="button">
      <span>
        <strong>${escapeHtml(artifact.key)}</strong>
        ${pathLine(`${artifact.path} / ${artifact.byte_size || 0} bytes`, 76)}
      </span>
      <span class="small-badge">${escapeHtml(artifact.kind)}</span>
    </button>
  `).join("");
}

function renderTerminalBlockers(blockers) {
  if (!blockers?.length) {
    return `<div class="panel-item"><strong>Open blockers</strong><span>No blockers detected in the final QA handoff.</span></div>`;
  }
  return blockers.slice(0, 4).map((blocker) => `
    <button class="artifact-row" data-blocker-stage="${escapeHtml(blocker.stage || state.activeStage)}" data-blocker-kind="${escapeHtml(blocker.kind)}" type="button">
      <span>
        <strong>${escapeHtml(blocker.title)}</strong>
        <span>${escapeHtml(blocker.detail)}</span>
      </span>
      <span class="small-badge ${blocker.severity === "error" ? "bad" : "warn"}">${escapeHtml(blocker.kind)}</span>
    </button>
  `).join("");
}

function renderFlowCompleteState() {
  const handoff = state.dashboard?.terminal_handoff;
  if (!handoff) return "";
  const approvals = approvalSummary(handoff.approval_counts);
  const repairs = repairSummary(handoff.repair_counts);
  const questionsValue = `${handoff.questions_answered_count || 0} / ${handoff.questions_total_count || 0}`;
  const artifactCount = (handoff.final_artifacts || []).length;
  const blockerCount = (handoff.blockers || []).length;
  const evidenceCount = (state.dashboard?.evidence_refs || []).length;
  const runtimeId = state.dashboard?.run?.runtime_id || "not recorded";
  return `
    <section class="surface flow-complete-state">
      <div class="flow-complete-hero">
        <div>
          <div class="surface-title">
            <span>${escapeHtml(terminalHandoffTitle(handoff))}</span>
            <span class="small-badge ${terminalHandoffTone(handoff.status)}">${escapeHtml(handoff.status)}</span>
          </div>
          <h2>${escapeHtml(handoff.final_qa_status)}</h2>
          <p>The QA terminal handoff is ready for operator review and next-flow selection.</p>
        </div>
        <div class="handoff-runtime">
          <strong>Runtime</strong>
          <span>${escapeHtml(runtimeId)}</span>
        </div>
      </div>
      <div class="handoff-metric-grid">
        ${renderHandoffMetric({label: "Final artifacts", value: artifactCount, detail: "QA documents and logs available.", tone: artifactCount ? "good" : "warn"})}
        ${renderHandoffMetric({label: "Open blockers", value: blockerCount, detail: blockerCount ? "Inspect before launch." : "No blockers detected.", tone: blockerCount ? "bad" : "good"})}
        ${renderHandoffMetric({label: "Evidence refs", value: evidenceCount, detail: "Linked stage evidence references.", tone: evidenceCount ? "good" : "warn"})}
        ${renderHandoffMetric({label: "Repair attempts", value: repairs.value, detail: repairs.detail, tone: handoff.repair_counts?.failed ? "warn" : ""})}
        ${renderHandoffMetric({label: "Approvals", value: approvals.value, detail: approvals.detail, tone: handoff.approval_counts?.pending ? "warn" : "good"})}
        ${renderHandoffMetric({label: "Questions answered", value: questionsValue, detail: "Resolved product interview questions.", tone: "good"})}
      </div>
      <div class="start-next-flow-band">
        <div class="surface-title">
          <span>Start Next Flow</span>
          <span class="small-badge">terminal handoff</span>
        </div>
        <p>Choose the next operator action without mutating the completed source run.</p>
        ${renderNextFlowActions(handoff)}
      </div>
      <div class="terminal-summary-grid">
        <section>
          <div class="surface-title">Final artifacts</div>
          <div class="recent-artifacts">${renderTerminalArtifacts(handoff.final_artifacts || [])}</div>
        </section>
        <section>
          <div class="surface-title">Blockers / safety</div>
          <div class="panel-list">
            ${renderTerminalBlockers(handoff.blockers || [])}
            <div class="panel-item"><strong>Source run policy</strong><span>Next-flow actions create new work or navigation decisions; they do not continue the completed run.</span></div>
            <div class="panel-item"><strong>Runtime fallback</strong><span>Uses recorded runtime ${escapeHtml(runtimeId)}; no generic runtime fallback is hidden in the UI.</span></div>
          </div>
        </section>
      </div>
    </section>
  `;
}

function lineageValue(value, fallback = "not recorded") {
  const normalized = String(value || "").trim();
  return normalized || fallback;
}

function lineageCandidateAction(candidate) {
  const relationship = String(candidate.relationship || "").toLowerCase();
  if (relationship.includes("clone")) return "Clone Flow";
  if (relationship.includes("eval")) return "Run Eval Batch";
  return "Start Follow-up";
}

function renderLineageActions(handoff) {
  const actions = handoff?.recommended_next_flow_actions || [];
  if (!actions.length) {
    return `<div class="empty-state">No next-flow actions recorded for this run.</div>`;
  }
  return `
    <div class="lineage-actions">
      ${actions.map((action) => `
        <button data-next-flow-action="${escapeHtml(action.action)}" type="button" ${action.enabled ? "" : "disabled"}>
          ${escapeHtml(nextFlowButtonLabel(action))}
        </button>
      `).join("")}
    </div>
  `;
}

function renderLineageArtifactRefs() {
  const artifacts = state.dashboard?.recent_artifacts || [];
  if (!artifacts.length) {
    return `<div class="empty-state">No linked artifacts recorded for this run.</div>`;
  }
  return artifacts.slice(0, 4).map((artifact) => `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(artifact.stage)}" data-artifact-key="${escapeHtml(artifact.key)}" data-artifact-kind="${escapeHtml(artifact.kind)}" type="button">
      <span>
        <strong>${escapeHtml(`${artifact.stage} / ${artifact.key}`)}</strong>
        ${pathLine(artifact.path, 76)}
      </span>
      <span class="small-badge">${escapeHtml(artifact.kind)}</span>
    </button>
  `).join("");
}

function renderLineageCandidates(candidates) {
  if (!candidates.length) {
    return `
      <article class="lineage-node pending">
        <span class="small-badge">next work item</span>
        <strong>Not created yet</strong>
        <p>Follow-up, clone, and eval actions will create independent work instead of mutating this run.</p>
      </article>
    `;
  }
  return candidates.map((candidate) => `
    <article class="lineage-node child" data-lineage-work-item="${escapeHtml(candidate.work_item_id)}">
      <span class="small-badge good">${escapeHtml(lineageCandidateAction(candidate))}</span>
      <strong>${escapeHtml(candidate.label || candidate.work_item_id)}</strong>
      <p>${escapeHtml(candidate.relationship || "child work item")}</p>
      <div class="panel-item"><strong>Work item</strong><span>${escapeHtml(candidate.work_item_id)}</span></div>
      <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(candidate.source_run_id || state.dashboard?.run?.run_id || "not recorded")}</span></div>
    </article>
  `).join("");
}

function renderLineageRows({run, lineage, candidates}) {
  const sourceRun = lineageValue(lineage.source_run_id, run.run_id || "not recorded");
  const sourceWorkItem = lineageValue(lineage.source_work_item_id, state.dashboard?.work_item || "not recorded");
  const baseline = lineageValue(lineage.baseline_label || lineage.baseline_id, "current run");
  const childRows = candidates.map((candidate) => `
    <tr>
      <td><span class="small-badge good">${escapeHtml(lineageCandidateAction(candidate))}</span></td>
      <td>${escapeHtml(candidate.work_item_id)}</td>
      <td>${escapeHtml(candidate.label || candidate.relationship || "child work item")}</td>
      <td>${escapeHtml(candidate.source_run_id || run.run_id || "not recorded")}</td>
    </tr>
  `).join("");
  return `
    <table class="activity-table lineage-table">
      <thead><tr><th>Relationship</th><th>Run / work item</th><th>Next action</th><th>Source</th></tr></thead>
      <tbody>
        <tr>
          <td><span class="small-badge">parent</span></td>
          <td data-lineage-run-id="${escapeHtml(sourceRun)}">${escapeHtml(sourceRun)}</td>
          <td>${escapeHtml(baseline)}</td>
          <td>${escapeHtml(sourceWorkItem)}</td>
        </tr>
        <tr>
          <td><span class="small-badge good">current</span></td>
          <td data-lineage-run-id="${escapeHtml(run.run_id || "")}">${escapeHtml(run.run_id || "none")}</td>
          <td>${escapeHtml(state.dashboard?.next_action?.label || "Review run")}</td>
          <td>${escapeHtml(state.dashboard?.work_item || "not recorded")}</td>
        </tr>
        ${childRows || `
          <tr>
            <td><span class="small-badge warn">child</span></td>
            <td>not created</td>
            <td>Start Next Flow</td>
            <td>${escapeHtml(run.run_id || "not recorded")}</td>
          </tr>
        `}
      </tbody>
    </table>
  `;
}

function renderRunHistory() {
  const run = state.dashboard?.run || {};
  if (!run.run_id) {
    return `<div class="empty-state">No run history is available before the first run starts.</div>`;
  }
  const lineage = run.lineage || {};
  const candidates = lineage.child_work_item_candidates || [];
  const handoff = state.dashboard?.terminal_handoff || null;
  const sourceRun = lineageValue(lineage.source_run_id, run.run_id);
  const sourceWorkItem = lineageValue(lineage.source_work_item_id, state.dashboard?.work_item || "not recorded");
  const baseline = lineageValue(lineage.baseline_label || lineage.baseline_id, "current run");
  return `
    <section class="surface run-history-state">
      <div class="surface-title">
        <span>Run History / Lineage</span>
        <span class="small-badge">${escapeHtml(run.run_id)}</span>
      </div>
      <div class="lineage-flow">
        <article class="lineage-node parent" data-lineage-run-id="${escapeHtml(sourceRun)}">
          <span class="small-badge">parent run</span>
          <strong>${escapeHtml(sourceRun)}</strong>
          <p>${escapeHtml(sourceWorkItem)}</p>
          <div class="panel-item"><strong>Baseline</strong><span>${escapeHtml(baseline)}</span></div>
        </article>
        <article class="lineage-node current" data-lineage-run-id="${escapeHtml(run.run_id)}">
          <span class="small-badge good">current run</span>
          <strong>${escapeHtml(run.run_id)}</strong>
          <p>${escapeHtml(run.runtime_id || "runtime not recorded")}</p>
          <div class="panel-item"><strong>Status</strong><span>${escapeHtml(handoff?.status || state.dashboard?.next_action?.label || "in progress")}</span></div>
        </article>
        <div class="lineage-children">
          ${renderLineageCandidates(candidates)}
        </div>
      </div>
      <div class="terminal-summary-grid">
        <section>
          <div class="surface-title">Lineage rows</div>
          ${renderLineageRows({run, lineage, candidates})}
        </section>
        <section>
          <div class="surface-title">Run actions</div>
          ${renderLineageActions(handoff)}
          <div class="surface-title compact">Linked artifacts</div>
          <div class="recent-artifacts">${renderLineageArtifactRefs()}</div>
        </section>
      </div>
    </section>
  `;
}

function allSourceFindingItems(payload = state.nextFlowWizard.sourceFindings) {
  return (payload?.groups || []).flatMap((group) => group.items || []);
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

async function openNextFlowWizard(action) {
  state.nextFlowWizard.active = true;
  state.nextFlowWizard.action = action;
  state.nextFlowWizard.step = "sources";
  state.nextFlowWizard.loading = true;
  state.nextFlowWizard.error = "";
  state.nextFlowWizard.sourceFindings = null;
  state.nextFlowWizard.followUpDraft = null;
  state.nextFlowWizard.followUpDraftError = "";
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.preflightError = "";
  state.nextFlowWizard.selectedSourceIds = [];
  activateTab("overview");
  await renderCockpit();
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
    await renderCockpit();
  }
}

async function loadLaunchConfirmation() {
  const wizard = state.nextFlowWizard;
  const draft = wizard.followUpDraft;
  wizard.preflightLoading = true;
  wizard.preflightError = "";
  wizard.step = "confirm";
  await renderCockpit();
  try {
    const payload = {
      source_work_item: draft.source_work_item,
      source_run_id: draft.source_run_id,
      runtime: state.selectedRuntime || state.dashboard?.run?.runtime_id || "",
      baseline_id: state.dashboard?.run?.lineage?.baseline_id || draft.source_run_id
    };
    const response = await fetch("/api/next-flow/preflight", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const result = await response.json();
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
    await renderCockpit();
  }
}

async function loadFollowUpDraft() {
  const wizard = state.nextFlowWizard;
  wizard.followUpDraftLoading = true;
  wizard.followUpDraftError = "";
  wizard.step = "definition";
  await renderCockpit();
  try {
    const payload = await postJson("/api/next-flow/follow-up-draft", {
      source_run_id: state.activeRunId,
      selected_source_ids: wizard.selectedSourceIds
    });
    wizard.followUpDraft = payload.draft;
  } catch (error) {
    wizard.followUpDraftError = error.message;
  } finally {
    wizard.followUpDraftLoading = false;
    await renderCockpit();
  }
}

function renderSourceFindingItem(group, item) {
  const checked = sourceFindingSelected(item.id);
  const artifactButton = item.source_path
    ? `
      <button class="artifact-row" data-artifact-stage="${escapeHtml(item.stage)}" data-artifact-key="${escapeHtml(item.artifact_key)}" data-artifact-kind="${escapeHtml(item.artifact_kind)}" type="button">
        <span><strong>${escapeHtml(item.artifact_key || item.title)}</strong>${pathLine(item.source_path, 76)}</span>
        <span class="small-badge">${escapeHtml(item.artifact_kind || item.kind)}</span>
      </button>
    `
    : `<div class="empty-state">Manual request text will be captured in the next wizard step.</div>`;
  return `
    <article class="source-finding-card">
      <label>
        <input data-source-selection-id="${escapeHtml(item.id)}" type="checkbox" ${checked ? "checked" : ""}>
        <span>
          <strong>${escapeHtml(item.title)}</strong>
          <small>${escapeHtml(group.label)} / ${escapeHtml(item.kind)}</small>
        </span>
      </label>
      <p>${escapeHtml(item.detail)}</p>
      ${artifactButton}
    </article>
  `;
}

function renderSourceFindingGroup(group) {
  return `
    <section class="source-finding-group">
      <div class="surface-title">
        <span>${escapeHtml(group.label)}</span>
        <span class="small-badge">${escapeHtml(group.count)}</span>
      </div>
      <p>${escapeHtml(group.detail)}</p>
      <div class="source-finding-list">
        ${(group.items || []).map((item) => renderSourceFindingItem(group, item)).join("") || `<div class="empty-state">No ${escapeHtml(group.label.toLowerCase())} found for this source run.</div>`}
      </div>
    </section>
  `;
}

function renderNextFlowSourceSelection() {
  const wizard = state.nextFlowWizard;
  if (wizard.step === "definition") {
    return renderFollowUpDefinition();
  }
  if (wizard.step === "confirm") {
    return renderLaunchConfirmation();
  }
  if (wizard.loading) {
    return `<section class="surface next-flow-wizard"><div class="empty-state loading-state">Loading source findings...</div></section>`;
  }
  if (wizard.error) {
    return `<section class="surface next-flow-wizard"><div class="empty-state">Unable to load source findings: ${escapeHtml(wizard.error)}</div></section>`;
  }
  const payload = wizard.sourceFindings;
  if (!payload) {
    return `<section class="surface next-flow-wizard"><div class="empty-state">No source findings loaded.</div></section>`;
  }
  const selectedCount = wizard.selectedSourceIds.length;
  return `
    <section class="surface next-flow-wizard">
      <div class="surface-title">
        <span>Start Next Flow</span>
        <span class="small-badge">source findings</span>
      </div>
      <div class="wizard-context-grid">
        <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(payload.source_run_id)}</span></div>
        <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(payload.source_work_item)}</span></div>
        <div class="panel-item"><strong>Selected sources</strong><span>${escapeHtml(selectedCount)} / ${escapeHtml(payload.counts.total_items)}</span></div>
        <div class="panel-item"><strong>Linked artifacts</strong><span>${escapeHtml(payload.counts.source_artifact_links)}</span></div>
      </div>
      <div class="source-finding-groups">
        ${(payload.groups || []).map((group) => renderSourceFindingGroup(group)).join("")}
      </div>
      <div class="wizard-actions">
        <button data-close-next-flow-wizard type="button" class="secondary">Back to handoff</button>
        <button data-next-flow-continue type="button" ${selectedCount ? "" : "disabled"}>Continue</button>
      </div>
    </section>
  `;
}

function preflightTone(status) {
  if (status === "pass") return "good";
  if (status === "warning") return "warn";
  if (status === "blocked") return "bad";
  return "";
}

function renderPreflightChecks(preflight) {
  return (preflight?.checks || []).map((check) => `
    <div class="preflight-check">
      <span class="small-badge ${check.severity === "blocking" ? "bad" : check.severity === "warning" ? "warn" : "good"}">${escapeHtml(check.severity)}</span>
      <strong>${escapeHtml(check.code)}</strong>
      <p>${escapeHtml(check.message)}</p>
      ${check.detail ? pathLine(check.detail, 74) : ""}
    </div>
  `).join("") || `<div class="empty-state">No preflight checks returned.</div>`;
}

function renderLaunchSourceLinks(draft) {
  return (draft?.selected_sources || []).map((item) => `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(item.stage)}" data-artifact-key="${escapeHtml(item.artifact_key)}" data-artifact-kind="${escapeHtml(item.artifact_kind)}" type="button">
      <span><strong>${escapeHtml(item.title)}</strong>${pathLine(item.source_path || item.detail, 76)}</span>
      <span class="small-badge">${escapeHtml(item.kind)}</span>
    </button>
  `).join("") || `<div class="empty-state">No source artifact links selected.</div>`;
}

function renderAuditPreview(draft, preflight) {
  return `
    <div class="audit-preview">
      <div class="panel-item"><strong>New work item</strong><span>${escapeHtml(draft.new_work_item)}</span></div>
      <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(draft.source_run_id)}</span></div>
      <div class="panel-item"><strong>Runtime</strong><span>${escapeHtml(state.selectedRuntime || state.dashboard?.run?.runtime_id || "not selected")}</span></div>
      <div class="panel-item"><strong>Resolved baseline</strong><span>${escapeHtml(preflight?.resolved_baseline_id || "not resolved")}</span></div>
      <div class="panel-item"><strong>Selected source links</strong><span>${escapeHtml(draft.selected_sources.length)}</span></div>
    </div>
  `;
}

function renderLaunchConfirmation() {
  const wizard = state.nextFlowWizard;
  const draft = wizard.followUpDraft;
  if (!draft) {
    return `<section class="surface next-flow-wizard"><div class="empty-state">No follow-up draft available for launch confirmation.</div></section>`;
  }
  if (wizard.preflightLoading) {
    return `<section class="surface next-flow-wizard"><div class="empty-state loading-state">Running launch preflight...</div></section>`;
  }
  const preflight = wizard.preflight;
  const blocked = !preflight?.can_launch;
  return `
    <section class="surface next-flow-wizard launch-confirmation">
      <div class="surface-title">
        <span>Confirm and Launch Next Flow</span>
        <span class="small-badge ${preflightTone(preflight?.status || "blocked")}">${escapeHtml(preflight?.status || "blocked")}</span>
      </div>
      ${wizard.preflightError ? `<div class="truncation-notice"><strong>Preflight blocked</strong><span>${escapeHtml(wizard.preflightError)}</span></div>` : ""}
      <div class="launch-confirmation-grid">
        <section>
          <div class="surface-title">Preflight results</div>
          <div class="preflight-check-list">${renderPreflightChecks(preflight)}</div>
        </section>
        <aside>
          <div class="surface-title">Audit preview</div>
          ${renderAuditPreview(draft, preflight)}
          <div class="surface-title compact">Source artifact links</div>
          <div class="recent-artifacts">${renderLaunchSourceLinks(draft)}</div>
        </aside>
      </div>
      <div class="wizard-actions">
        <button data-next-flow-back-to-definition type="button" class="secondary">Back to definition</button>
        <button data-launch-flow-now type="button" ${blocked ? "disabled" : ""}>Launch Flow Now</button>
      </div>
    </section>
  `;
}

function renderEditableList(name, items) {
  return (items || []).map((item, index) => `
    <label class="editable-list-row">
      <input data-follow-up-list="${escapeHtml(name)}" data-follow-up-index="${escapeHtml(index)}" type="checkbox" checked>
      <span>${escapeHtml(item)}</span>
    </label>
  `).join("") || `<div class="empty-state">No ${escapeHtml(name)} generated.</div>`;
}

function renderInheritedContextToggles(items) {
  return (items || []).map((item) => `
    <label class="inherited-context-toggle">
      <input data-inherited-context="${escapeHtml(item.id)}" type="checkbox" ${item.enabled ? "checked" : ""}>
      <span>
        <strong>${escapeHtml(item.label)}</strong>
        <small>${escapeHtml(item.detail)}</small>
      </span>
    </label>
  `).join("");
}

function renderFollowUpDefinition() {
  const wizard = state.nextFlowWizard;
  if (wizard.followUpDraftLoading) {
    return `<section class="surface next-flow-wizard"><div class="empty-state loading-state">Generating follow-up definition...</div></section>`;
  }
  if (wizard.followUpDraftError) {
    return `<section class="surface next-flow-wizard"><div class="empty-state">Unable to generate follow-up definition: ${escapeHtml(wizard.followUpDraftError)}</div></section>`;
  }
  const draft = wizard.followUpDraft;
  if (!draft) {
    return `<section class="surface next-flow-wizard"><div class="empty-state">No follow-up definition generated.</div></section>`;
  }
  return `
    <section class="surface next-flow-wizard follow-up-definition">
      <div class="surface-title">
        <span>Define Follow-up Work Item</span>
        <span class="small-badge">editable draft</span>
      </div>
      <div class="wizard-context-grid">
        <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(draft.source_run_id)}</span></div>
        <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(draft.source_work_item)}</span></div>
        <div class="panel-item"><strong>Selected sources</strong><span>${escapeHtml(draft.selected_sources.length)}</span></div>
        <div class="panel-item"><strong>New work item</strong><span>${escapeHtml(draft.new_work_item)}</span></div>
      </div>
      <div class="follow-up-definition-grid">
        <section class="definition-form">
          <label class="form-field">
            <span>Work item id</span>
            <input data-follow-up-field="new_work_item" type="text" value="${escapeHtml(draft.new_work_item)}">
          </label>
          <label class="form-field">
            <span>Title</span>
            <input data-follow-up-field="title" type="text" value="${escapeHtml(draft.title)}">
          </label>
          <label class="form-field">
            <span>First-stage input preview</span>
            <textarea data-follow-up-field="first_stage_input_preview" rows="10">${escapeHtml(draft.first_stage_input_preview)}</textarea>
          </label>
        </section>
        <aside class="definition-side">
          <div class="surface-title">Acceptance criteria</div>
          <div class="editable-list">${renderEditableList("acceptance_criteria", draft.acceptance_criteria)}</div>
          <div class="surface-title compact">Required evidence</div>
          <div class="editable-list">${renderEditableList("required_evidence", draft.required_evidence)}</div>
          <div class="surface-title compact">Inherited context</div>
          <div class="inherited-context-list">${renderInheritedContextToggles(draft.inherited_context)}</div>
        </aside>
      </div>
      <div class="wizard-actions">
        <button data-next-flow-back-to-sources type="button" class="secondary">Back to sources</button>
        <button data-next-flow-confirm-preview type="button">Continue to preflight</button>
      </div>
    </section>
  `;
}

function renderNextActionPanel() {
  const action = state.dashboard?.next_action || {action: "choose-runtime", label: "Select runtime", detail: "Choose a runtime.", enabled: false};
  const noRunWithRuntime = action.action === "choose-runtime" && state.selectedRuntime;
  const runStageResume = action.action === "run-stage" && state.activeRunId && action.enabled;
  const runtimeNeeded = needsRuntime(action.action) || noRunWithRuntime;
  const runtimeBlocked = runtimeNeeded && (!state.selectedRuntime || !selectedRuntimeReady());
  const disabled = !(action.enabled || noRunWithRuntime) || runtimeBlocked;
  const label = noRunWithRuntime
    ? (state.activeRunId ? "Resume workflow" : "Run workflow")
    : runStageResume
      ? `Continue with ${stageTitle(action.stage || state.activeStage)}`
      : action.label;
  const detail = runtimeBlocked && state.selectedRuntime
    ? `${action.detail} ${state.readinessLoading ? "Checking runtime readiness." : "Selected runtime is not ready."}`
    : action.detail;
  document.getElementById("nextActionPanel").innerHTML = `
    <div class="panel-title">Next action</div>
    <p>${escapeHtml(detail)}</p>
    <button id="nextActionButton" class="next-button" data-next-action="${escapeHtml(action.action)}" type="button" ${disabled ? "disabled" : ""}>${escapeHtml(label)}</button>
  `;
}

async function startWorkflow() {
  if (!ensureRunnableRuntime()) return;
  const payload = {runtime: state.selectedRuntime, log_follow: true};
  if (state.activeRunId) payload.run_id = state.activeRunId;
  const job = await postJson("/api/workflow/run", payload);
  await startJobPolling(job);
}

async function startStage(stage = state.activeStage) {
  if (!ensureRunnableRuntime()) return;
  const payload = {stage, runtime: state.selectedRuntime, log_follow: true};
  if (state.activeRunId) payload.run_id = state.activeRunId;
  const job = await postJson("/api/stage/run", payload);
  await startJobPolling(job);
}

async function handleNextAction() {
  const action = state.dashboard?.next_action || {action: "choose-runtime"};
  if (action.action === "choose-runtime") {
    if (state.selectedRuntime) {
      await startWorkflow();
    } else {
      document.getElementById("runtimeSelect").focus();
      toast("Select runtime first.");
    }
    return;
  }
  if (action.action === "run-workflow") {
    await startWorkflow();
    return;
  }
  if (action.action === "run-stage" || action.action === "resume-stage") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    await startStage(action.stage || state.activeStage);
    return;
  }
  if (action.action === "answer-questions") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    activateTab("questions");
    await renderCockpit();
    return;
  }
  if (action.action === "inspect-validation" || action.action === "review-intervention") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    activateTab("validation");
    await renderCockpit();
    return;
  }
  if (action.action === "review-complete") {
    activateTab("artifacts");
    await renderCockpit();
  }
}
