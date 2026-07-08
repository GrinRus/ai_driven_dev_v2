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

function renderSetupReadinessChecklist({ready, context}) {
  const checklist = [
    {
      label: "Runtime adapter",
      status: state.readinessLoading
        ? "checking"
        : state.selectedRuntime
          ? ready
            ? "ready"
            : "needs check"
          : "not selected",
      tone: ready ? "good" : state.selectedRuntime || state.readinessLoading ? "warn" : ""
    },
    {
      label: "Contracts path",
      status: "local contract surface",
      tone: "good"
    },
    {
      label: "Validators",
      status: "enforced before progression",
      tone: "good"
    },
    {
      label: "Previous-run context",
      status: context.available ? "available" : "none selected",
      tone: context.available ? "good" : ""
    },
    {
      label: "Log stream",
      status: "enabled for workflow runs",
      tone: "good"
    }
  ];
  return `
    <section class="setup-readiness-checklist" aria-label="Readiness Checklist">
      <div class="surface-title compact">
        <span>Readiness Checklist</span>
        <span class="small-badge ${ready ? "good" : "warn"}">${ready ? "runnable" : "review"}</span>
      </div>
      <div class="setup-readiness-list">
        ${checklist.map((item) => `
          <div class="setup-readiness-item">
            <span class="small-badge ${escapeHtml(item.tone)}">${escapeHtml(item.tone === "good" ? "pass" : item.tone === "warn" ? "check" : "info")}</span>
            <span><strong>${escapeHtml(item.label)}</strong><small>${escapeHtml(item.status)}</small></span>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}

function renderFirstLaunchState() {
  const runtime = selectedRuntimeView();
  const ready = selectedRuntimeReady();
  const hasWorkItemContext = Boolean(state.dashboard?.work_item);
  const context = setupPreviousRunContext();
  const mode = setupModeView(context);
  const detail = !hasWorkItemContext
    ? "Create or resume a work item before starting the governed workflow."
    : !state.selectedRuntime
    ? "Select a runtime to start the first governed workflow run."
    : ready
      ? `${state.selectedRuntime} is ready to start the workflow.`
      : `${state.selectedRuntime} needs a passing readiness check before the first run.`;
  const canRun = hasWorkItemContext && ready && runtime;
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
            <button data-first-launch-run type="button" ${canRun ? "" : "disabled"}>Run workflow</button>
            <button data-first-launch-stage type="button" class="secondary" ${canRun ? "" : "disabled"}>Run selected stage</button>
            <span class="muted">Work item ${escapeHtml(state.dashboard?.work_item || "unknown")}</span>
          </div>
        </div>
        <aside class="setup-context" aria-label="Previous-run context">
          <div class="surface-title">
            <span>Previous-run context</span>
            <span class="small-badge ${context.available ? "good" : ""}">${context.available ? "available" : "none"}</span>
          </div>
          ${renderPreviousRunContext(context)}
          ${renderSetupReadinessChecklist({ready, context})}
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

function recommendedNextFlowDecision(handoff) {
  const actionId = recommendedNextFlowAction(handoff);
  const actions = handoff.recommended_next_flow_actions || [];
  const action = actions.find((candidate) => candidate.action === actionId) || actions[0] || {};
  const blockerCount = (handoff.blockers || []).length;
  const finalStatus = handoff.status || "unknown";
  let reason = "Use this path before choosing a less common next-flow option.";
  if (actionId === "create-new-work-item") {
    reason = "QA is ready and no open blockers are recorded; start unrelated work only after reviewing final evidence.";
  } else if (finalStatus === "failed") {
    reason = "Terminal QA failed; carry failed evidence into a follow-up instead of treating this run as done.";
  } else if (blockerCount) {
    reason = `${blockerCount} blocker${blockerCount === 1 ? "" : "s"} remain; carry them into follow-up work before starting new scope.`;
  } else {
    reason = "The terminal handoff still needs attention; carry the current findings into follow-up work first.";
  }
  return {
    action: actionId,
    label: action.label || nextFlowButtonLabel({action: actionId, label: "Start Follow-up"}),
    detail: action.detail || "",
    enabled: action.enabled !== false,
    reason
  };
}

function renderRecommendedNextFlowDecision(handoff) {
  const decision = recommendedNextFlowDecision(handoff);
  return `
    <div class="next-flow-decision-spotlight">
      <div>
        <span class="small-badge good">recommended next decision</span>
        <strong>${escapeHtml(decision.label)}</strong>
        <p>${escapeHtml(decision.reason)}</p>
        ${decision.detail ? `<small>${escapeHtml(decision.detail)}</small>` : ""}
      </div>
      <button data-next-flow-action="${escapeHtml(decision.action)}" type="button" ${decision.enabled ? "" : 'disabled aria-disabled="true"'}>
        ${escapeHtml(nextFlowButtonLabel(decision))}
      </button>
    </div>
  `;
}

function renderNextFlowActions(handoff) {
  const recommended = recommendedNextFlowAction(handoff);
  const actions = handoff.recommended_next_flow_actions || [];
  return `
    <div class="next-flow-actions-grid">
      ${actions.map((action) => {
        const isRecommended = action.action === recommended;
        return `
          <article class="next-flow-action-card${isRecommended ? " recommended" : ""}${action.enabled ? "" : " disabled"}">
            <div class="action-card-title">
              <strong>${escapeHtml(action.label)}</strong>
              ${isRecommended ? '<span class="small-badge good">recommended</span>' : ""}
              ${action.enabled ? "" : '<span class="small-badge warn">unavailable</span>'}
            </div>
            <p>${escapeHtml(action.detail)}</p>
            <button data-next-flow-action="${escapeHtml(action.action)}" type="button" ${action.enabled ? "" : 'disabled aria-disabled="true"'}>
              ${escapeHtml(nextFlowButtonLabel(action))}
            </button>
          </article>
        `;
      }).join("")}
    </div>
  `;
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

function renderTerminalRepairHighlights(highlights) {
  if (!highlights?.length) return "";
  return `
    <div class="repair-highlight-spotlight">
      <div class="surface-title">
        <span>Resolved Repairs</span>
        <span class="small-badge good">visible in handoff</span>
      </div>
      <p>These validation issues were retried and resolved before QA handoff.</p>
      <div class="repair-highlight-list">
        ${highlights.map((highlight) => {
          const stageLabel = stageTitle(highlight.stage);
          const outcome = String(highlight.outcome || "recorded");
          const outcomeTone = outcome.toLowerCase().includes("fail") ? "warn" : "good";
          return `
            <article class="repair-highlight-card">
              <div>
                <span class="small-badge ${outcomeTone}">${escapeHtml(outcome)}</span>
                <strong>${escapeHtml(stageLabel)} retry ${escapeHtml(highlight.attempt_number || "")}</strong>
                <p>${escapeHtml(highlight.reason || "Repair reason was not recorded.")}</p>
              </div>
              <div class="repair-highlight-evidence">
                ${highlight.repair_brief_path ? `<button data-open-artifact="${escapeHtml(highlight.repair_brief_path)}" type="button">Repair brief</button>` : ""}
                ${highlight.validator_report_path ? `<button data-open-artifact="${escapeHtml(highlight.validator_report_path)}" type="button">Validator report</button>` : ""}
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </div>
  `;
}

function renderFollowUpCandidates(handoff) {
  const blockerCandidates = (handoff.blockers || []).map((blocker) => ({
    label: blocker.title,
    detail: blocker.detail,
    tone: blocker.severity === "error" ? "bad" : "warn"
  }));
  const statusCandidate = handoff.status !== "completed"
    ? [{
        label: "Final QA needs follow-up",
        detail: `Terminal status ${handoff.status}; carry source findings into a new work item.`,
        tone: handoff.status === "failed" ? "bad" : "warn"
      }]
    : [];
  const candidates = [...blockerCandidates, ...statusCandidate];
  if (!candidates.length) {
    return `<div class="panel-item"><strong>No forced follow-up</strong><span>Create New Work Item is recommended unless the operator selects manual scope.</span></div>`;
  }
  return candidates.slice(0, 4).map((candidate) => `
    <div class="panel-item">
      <strong>${escapeHtml(candidate.label)}</strong>
      <span>${escapeHtml(candidate.detail)}</span>
      <span class="small-badge ${escapeHtml(candidate.tone)}">candidate</span>
    </div>
  `).join("");
}

function renderBaselineSnapshot() {
  const run = state.dashboard?.run || {};
  const lineage = run.lineage || {};
  const baseline = lineage.baseline_label || lineage.baseline_id || run.run_id || "current run";
  return `
    <div class="panel-list">
      <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(lineage.source_run_id || run.run_id || "not recorded")}</span></div>
      <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(lineage.source_work_item_id || state.dashboard?.work_item || "not recorded")}</span></div>
      <div class="panel-item"><strong>Baseline</strong><span>${escapeHtml(baseline)}</span></div>
      <div class="panel-item"><strong>Safety</strong><span>Follow-up, clone, and eval actions create independent work and keep source artifacts read-only.</span></div>
    </div>
  `;
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
        <div class="flow-complete-title-row">
          <span class="flow-complete-mark" aria-hidden="true">OK</span>
          <div>
          <div class="surface-title">
            <span>${escapeHtml(terminalHandoffTitle(handoff))}</span>
            <span class="small-badge ${terminalHandoffTone(handoff.status)}">${escapeHtml(handoff.status)}</span>
          </div>
          <h2>${escapeHtml(handoff.final_qa_status)}</h2>
          <p>The QA terminal handoff is ready for operator review and next-flow selection.</p>
          </div>
        </div>
        <div class="handoff-runtime">
          <strong>Runtime</strong>
          <span>${escapeHtml(runtimeId)}</span>
        </div>
      </div>
      ${renderTerminalRepairHighlights(handoff.repair_highlights || [])}
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
        ${renderRecommendedNextFlowDecision(handoff)}
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
        <section>
          <div class="surface-title">Follow-up candidates</div>
          <div class="panel-list">${renderFollowUpCandidates(handoff)}</div>
        </section>
        <section>
          <div class="surface-title">Baseline snapshot</div>
          ${renderBaselineSnapshot()}
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
  const hasParentRun = Boolean(lineage.source_run_id && lineage.source_run_id !== run.run_id);
  const sourceRun = lineageValue(lineage.source_run_id, "not recorded");
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
        ${hasParentRun ? `
          <tr>
            <td><span class="small-badge">parent</span></td>
            <td data-lineage-run-id="${escapeHtml(sourceRun)}">${escapeHtml(sourceRun)}</td>
            <td>${escapeHtml(baseline)}</td>
            <td>${escapeHtml(sourceWorkItem)}</td>
          </tr>
        ` : ""}
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

function defaultComparisonBaselineRunId(run, lineage) {
  return lineage.source_run_id || lineage.baseline_id || run.run_id || "";
}

function comparisonBaselineRunId(run, lineage) {
  return (state.runComparisonBaselineInput || defaultComparisonBaselineRunId(run, lineage)).trim();
}

function comparisonDeltasByStatus(items) {
  const counts = {changed: 0, added: 0, removed: 0, same: 0};
  (items || []).forEach((item) => {
    const status = item.status || "same";
    counts[status] = (counts[status] || 0) + 1;
  });
  return counts;
}

function renderComparisonStatusBadge(status) {
  const normalized = status || "same";
  const tone = normalized === "same" ? "good" : normalized === "changed" ? "warn" : "bad";
  return `<span class="small-badge ${tone}">${escapeHtml(normalized)}</span>`;
}

function renderComparisonHash(value) {
  return value ? escapeHtml(value.slice(0, 12)) : "not present";
}

function renderRunComparisonRows(items, mapper, emptyMessage) {
  const rows = (items || []).filter((item) => item.status !== "same").slice(0, 8);
  if (!rows.length) return `<div class="empty-state">${escapeHtml(emptyMessage)}</div>`;
  return `
    <table class="activity-table comparison-table">
      <thead><tr><th>Item</th><th>Baseline</th><th>Target</th><th>Status</th></tr></thead>
      <tbody>
        ${rows.map(mapper).join("")}
      </tbody>
    </table>
  `;
}

function renderRunComparisonPanel() {
  const run = state.dashboard?.run || {};
  if (!run.run_id) return "";
  const lineage = run.lineage || {};
  const baselineRunId = comparisonBaselineRunId(run, lineage);
  const targetRunId = run.run_id || "";
  const loadedComparison = state.runComparison;
  const comparison = loadedComparison
    && loadedComparison.baseline?.run_id === baselineRunId
    && loadedComparison.target?.run_id === targetRunId
      ? loadedComparison
      : null;
  const error = state.runComparisonError;
  const loading = state.runComparisonLoading;
  const promptCounts = comparisonDeltasByStatus(comparison?.prompt_hash_deltas);
  const stageCounts = comparisonDeltasByStatus(comparison?.stage_status_deltas);
  const artifactCounts = comparisonDeltasByStatus(comparison?.artifact_hash_deltas);
  const validatorCounts = comparisonDeltasByStatus(comparison?.validator_outcome_deltas);
  return `
    <section id="runComparisonPanel" class="surface run-comparison-panel">
      <div class="surface-title">
        <span>Run comparison</span>
        <span class="small-badge">${escapeHtml(baselineRunId || "baseline")} -> ${escapeHtml(targetRunId || "target")}</span>
      </div>
      <div class="comparison-controls">
        <label>
          <span>Baseline run id</span>
          <input id="runComparisonBaseline" type="text" value="${escapeHtml(baselineRunId)}" placeholder="run-..." autocomplete="off">
        </label>
        <button data-run-comparison-refresh type="button" ${loading ? "disabled" : ""}>Refresh comparison</button>
      </div>
      ${error ? `<div class="empty-state bad">${escapeHtml(error)}</div>` : ""}
      ${loading ? `<div class="empty-state loading-state">Loading run comparison...</div>` : ""}
      ${comparison ? `
        ${renderWarnings(comparison.warnings)}
        <div class="metric-grid">
          <div class="metric"><span>Prompt drift</span><strong>${escapeHtml(promptCounts.changed + promptCounts.added + promptCounts.removed)}</strong></div>
          <div class="metric"><span>Stage status drift</span><strong>${escapeHtml(stageCounts.changed + stageCounts.added + stageCounts.removed)}</strong></div>
          <div class="metric"><span>Artifact drift</span><strong>${escapeHtml(artifactCounts.changed + artifactCounts.added + artifactCounts.removed)}</strong></div>
          <div class="metric"><span>Validator drift</span><strong>${escapeHtml(validatorCounts.changed + validatorCounts.added + validatorCounts.removed)}</strong></div>
        </div>
        <div class="terminal-summary-grid">
          <section>
            <div class="surface-title compact">Prompt hash deltas</div>
            ${renderRunComparisonRows(
              comparison.prompt_hash_deltas,
              (item) => `
                <tr>
                  <td>${escapeHtml(item.path)}</td>
                  <td>${renderComparisonHash(item.baseline_sha256)}</td>
                  <td>${renderComparisonHash(item.target_sha256)}</td>
                  <td>${renderComparisonStatusBadge(item.status)}</td>
                </tr>
              `,
              "No prompt hash drift detected."
            )}
          </section>
          <section>
            <div class="surface-title compact">Stage status deltas</div>
            ${renderRunComparisonRows(
              comparison.stage_status_deltas,
              (item) => `
                <tr>
                  <td>${escapeHtml(item.stage)}</td>
                  <td>${escapeHtml(item.baseline_status || "missing")}</td>
                  <td>${escapeHtml(item.target_status || "missing")}</td>
                  <td>${renderComparisonStatusBadge(item.status)}</td>
                </tr>
              `,
              "No stage status drift detected."
            )}
          </section>
          <section>
            <div class="surface-title compact">Artifact hash deltas</div>
            ${renderRunComparisonRows(
              comparison.artifact_hash_deltas,
              (item) => `
                <tr>
                  <td>${escapeHtml(`${item.stage}/${item.kind}/${item.key}`)}</td>
                  <td>${renderComparisonHash(item.baseline_sha256)}${item.baseline_truncated ? " truncated" : ""}</td>
                  <td>${renderComparisonHash(item.target_sha256)}${item.target_truncated ? " truncated" : ""}</td>
                  <td>${renderComparisonStatusBadge(item.status)}</td>
                </tr>
              `,
              "No artifact hash drift detected."
            )}
          </section>
          <section>
            <div class="surface-title compact">Validator outcome deltas</div>
            ${renderRunComparisonRows(
              comparison.validator_outcome_deltas,
              (item) => `
                <tr>
                  <td>${escapeHtml(item.stage)}</td>
                  <td>${escapeHtml(item.baseline_verdict || "missing")}</td>
                  <td>${escapeHtml(item.target_verdict || "missing")}</td>
                  <td>${renderComparisonStatusBadge(item.status)}</td>
                </tr>
              `,
              "No validator outcome drift detected."
            )}
          </section>
        </div>
      ` : !loading && !error ? `<div class="empty-state">Run comparison has not loaded yet.</div>` : ""}
    </section>
  `;
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

function renderRunHistory() {
  const run = state.dashboard?.run || {};
  if (!run.run_id) {
    return `<div class="empty-state">No run history is available before the first run starts.</div>`;
  }
  const lineage = run.lineage || {};
  const candidates = lineage.child_work_item_candidates || [];
  const handoff = state.dashboard?.terminal_handoff || null;
  const archive = run.archive || {};
  const hasParentRun = Boolean(lineage.source_run_id && lineage.source_run_id !== run.run_id);
  const sourceRun = lineageValue(lineage.source_run_id, "not recorded");
  const sourceWorkItem = lineageValue(lineage.source_work_item_id, state.dashboard?.work_item || "not recorded");
  const baseline = lineageValue(lineage.baseline_label || lineage.baseline_id, "current run");
  return `
    <section class="surface run-history-state">
      <div class="surface-title">
        <span>Run History / Lineage</span>
        <span class="small-badge">${escapeHtml(run.run_id)}</span>
      </div>
      <div class="lineage-flow">
        ${hasParentRun ? `
          <article class="lineage-node parent" data-lineage-run-id="${escapeHtml(sourceRun)}">
            <span class="small-badge">parent run</span>
            <strong>${escapeHtml(sourceRun)}</strong>
            <p>${escapeHtml(sourceWorkItem)}</p>
            <div class="panel-item"><strong>Baseline</strong><span>${escapeHtml(baseline)}</span></div>
          </article>
        ` : ""}
        <article class="lineage-node current" data-lineage-run-id="${escapeHtml(run.run_id)}">
          <span class="small-badge ${archive.archived ? "warn" : "good"}">${archive.archived ? "archived" : "current run"}</span>
          <strong>${escapeHtml(run.run_id)}</strong>
          <p>${escapeHtml(run.runtime_id || "runtime not recorded")}</p>
          <div class="panel-item"><strong>Status</strong><span>${escapeHtml(handoff?.status || state.dashboard?.next_action?.label || "in progress")}</span></div>
          <div class="panel-item"><strong>Archive</strong><span>${escapeHtml(archive.archived ? `${archive.archived_at_utc || "recorded"} / ${archive.reason || "no reason"}` : "open")}</span></div>
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
    ${renderRunComparisonPanel()}
  `;
}

function sourceFindingPriority(item) {
  return Number.isFinite(Number(item?.priority)) ? Number(item.priority) : 50;
}

function sourceFindingDisplayLabel(item) {
  return item.display_label || item.title || item.id || "Source finding";
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
    await renderCockpit();
    return;
  }
  state.nextFlowWizard.loading = true;
  state.nextFlowWizard.error = "";
  state.nextFlowWizard.sourceFindings = null;
  state.nextFlowWizard.followUpDraft = null;
  state.nextFlowWizard.followUpDraftError = "";
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.preflightError = "";
  state.nextFlowWizard.createdDraft = null;
  state.nextFlowWizard.launchLoading = false;
  state.nextFlowWizard.launchError = "";
  state.nextFlowWizard.archiveRunId = "";
  state.nextFlowWizard.archiveReason = "";
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

async function openNewWorkItemHandoff() {
  state.nextFlowWizard.active = true;
  state.nextFlowWizard.action = "create-new-work-item";
  state.nextFlowWizard.step = "new-work-item";
  state.nextFlowWizard.loading = false;
  state.nextFlowWizard.error = "";
  state.nextFlowWizard.followUpDraft = null;
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.createdDraft = null;
  state.nextFlowWizard.launchError = "";
  state.nextFlowWizard.archiveRunId = "";
  state.nextFlowWizard.archiveReason = "";
  activateTab("overview");
  await renderCockpit();
}

async function openEvalBatchHandoff() {
  state.nextFlowWizard.active = true;
  state.nextFlowWizard.action = "run-eval-batch";
  state.nextFlowWizard.step = "eval-batch";
  state.nextFlowWizard.loading = false;
  state.nextFlowWizard.error = "";
  state.nextFlowWizard.followUpDraft = null;
  state.nextFlowWizard.preflight = null;
  state.nextFlowWizard.createdDraft = null;
  state.nextFlowWizard.launchError = "";
  state.nextFlowWizard.archiveRunId = "";
  state.nextFlowWizard.archiveReason = "";
  activateTab("overview");
  await renderCockpit();
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
  wizard.launchError = "";
  wizard.createdDraft = null;
  wizard.archiveRunId = "";
  wizard.archiveReason = "";
  wizard.preflightLoading = true;
  activateTab("overview");
  await renderCockpit();
  try {
    const payload = await postJson("/api/next-flow/clone-draft/create", {
      source_work_item: nextFlowSourceWorkItem(),
      source_run_id: nextFlowSourceRunId(),
      new_work_item: nextFlowDefaultWorkItem("CLONE"),
      title: `Clone ${nextFlowSourceWorkItem()} from ${nextFlowSourceRunId()}`
    });
    wizard.followUpDraft = cloneDraftFromPayload(payload);
    wizard.createdDraft = payload.created;
    toast("Clone draft created for launch review.");
    await loadLaunchConfirmation();
  } catch (error) {
    wizard.preflightLoading = false;
    wizard.preflightError = error.message;
    await renderCockpit();
  }
}

async function loadLaunchConfirmation() {
  const wizard = state.nextFlowWizard;
  const draft = readFollowUpDraftForm() || wizard.followUpDraft;
  if (!draft) {
    wizard.preflightError = "No next-flow draft is available for preflight.";
    wizard.step = "confirm";
    await renderCockpit();
    return;
  }
  const definitionError = followUpDraftValidationError(draft);
  if (definitionError) {
    wizard.preflightLoading = false;
    wizard.preflightError = definitionError;
    wizard.step = "definition";
    await renderCockpit();
    return;
  }
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

function followUpDraftValidationError(draft) {
  if (state.nextFlowWizard.action !== "start-follow-up-flow") return "";
  if (!String(draft?.new_work_item || "").trim()) return "Work item id is required before preflight.";
  if (!String(draft?.title || "").trim()) return "Title is required before preflight.";
  if (!String(draft?.first_stage_input_preview || "").trim()) return "First-stage input preview is required before preflight.";
  if (!(draft?.acceptance_criteria || []).some((item) => String(item || "").trim())) {
    return "At least one acceptance criterion is required before preflight.";
  }
  if (!(draft?.required_evidence || []).some((item) => String(item || "").trim())) {
    return "At least one required evidence item is required before preflight.";
  }
  return "";
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
  state.nextFlowWizard.createdDraft = null;
  state.nextFlowWizard.launchError = "";
  document.querySelector("[data-follow-up-definition-error]")?.remove();
}

async function createFollowUpDraftForLaunch(draft) {
  if (state.nextFlowWizard.createdDraft) return state.nextFlowWizard.createdDraft;
  const payload = await postJson("/api/next-flow/follow-up-draft/create", {
    source_work_item: draft.source_work_item,
    source_run_id: draft.source_run_id,
    selected_source_ids: state.nextFlowWizard.selectedSourceIds,
    new_work_item: draft.new_work_item,
    title: draft.title,
    first_stage_input: draft.first_stage_input_preview,
    acceptance_criteria: draft.acceptance_criteria || [],
    required_evidence: draft.required_evidence || [],
    inherited_context: draft.inherited_context_lines || inheritedContextLinesFromItems(draft.inherited_context)
  });
  state.nextFlowWizard.createdDraft = payload.created;
  return payload.created;
}

async function launchNextFlowNow() {
  const wizard = state.nextFlowWizard;
  const draft = readFollowUpDraftForm() || wizard.followUpDraft;
  if (!draft) {
    toast("No next-flow draft is ready to launch.");
    return;
  }
  if (!ensureRunnableRuntime()) return;
  wizard.launchLoading = true;
  wizard.launchError = "";
  await renderCockpit();
  try {
    if (wizard.action === "start-follow-up-flow") {
      await createFollowUpDraftForLaunch(draft);
    }
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
    wizard.active = false;
    toast(`Launching ${draft.new_work_item}.`);
    await startJobPolling(job);
  } catch (error) {
    wizard.launchError = error.message;
    toast(error.message);
    await renderCockpit();
  } finally {
    wizard.launchLoading = false;
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
  state.nextFlowWizard.launchError = "";
  state.nextFlowWizard.archiveRunId = runId;
  state.nextFlowWizard.archiveReason = state.dashboard?.terminal_handoff
    ? `Archived from Flow Complete handoff with status ${state.dashboard.terminal_handoff.status}.`
    : "Archived from Run History.";
  activateTab("overview");
  await renderCockpit();
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

function renderArchiveConfirmation() {
  const sourceRun = state.nextFlowWizard.archiveRunId || nextFlowSourceRunId() || "not recorded";
  const sourceWorkItem = nextFlowSourceWorkItem() || "not recorded";
  const reason = state.nextFlowWizard.archiveReason || "Archived from Flow Complete handoff.";
  const artifacts = state.dashboard?.terminal_handoff?.final_artifacts || [];
  return `
    <section class="surface next-flow-wizard archive-confirmation">
      <div class="surface-title">
        <span>Confirm Archive Run</span>
        <span class="small-badge warn">confirmation required</span>
      </div>
      <div class="wizard-context-grid">
        <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(sourceRun)}</span></div>
        <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(sourceWorkItem)}</span></div>
        <div class="panel-item"><strong>Final artifacts</strong><span>${escapeHtml(artifacts.length)}</span></div>
        <div class="panel-item"><strong>Mutation</strong><span>archive metadata only</span></div>
      </div>
      <div class="archive-confirmation-body">
        <div class="truncation-notice" role="status">
          <strong>Archive keeps evidence readable</strong>
          <span>This records a local navigation decision. It does not delete final artifacts, runtime logs, or stage documents.</span>
        </div>
        <div class="panel-list">
          <div class="panel-item"><strong>Reason preview</strong><span>${escapeHtml(reason)}</span></div>
          <div class="panel-item"><strong>Source-run policy</strong><span>The completed run stays immutable; archive only changes run navigation metadata.</span></div>
        </div>
      </div>
      <div class="wizard-actions">
        <button data-close-next-flow-wizard type="button" class="secondary">Back to handoff</button>
        <button data-archive-confirm type="button" class="danger">Confirm Archive Run</button>
      </div>
    </section>
  `;
}

function renderSourceFindingItem(group, item) {
  const checked = sourceFindingSelected(item.id);
  const recommended = item.recommended ? '<span class="small-badge good">recommended</span>' : "";
  const supporting = item.collapsible ? '<span class="small-badge">supporting</span>' : "";
  const artifactButton = item.source_path
    ? `
      <button class="artifact-row" data-artifact-stage="${escapeHtml(item.stage)}" data-artifact-key="${escapeHtml(item.artifact_key)}" data-artifact-kind="${escapeHtml(item.artifact_kind)}" type="button">
        <span><strong>${escapeHtml(item.display_label || item.artifact_key || item.title)}</strong>${pathLine(item.source_path, 76)}</span>
        <span class="small-badge">${escapeHtml(item.artifact_kind || item.kind)}</span>
      </button>
    `
    : `<div class="empty-state">Manual request text will be captured in the next wizard step.</div>`;
  return `
    <article class="source-finding-card${item.recommended ? " recommended" : ""}${item.collapsible ? " supporting" : ""}">
      <label>
        <input data-source-selection-id="${escapeHtml(item.id)}" type="checkbox" ${checked ? "checked" : ""}>
        <span>
          <strong>${escapeHtml(sourceFindingDisplayLabel(item))}</strong>
          <small>${escapeHtml(group.label)} / ${escapeHtml(item.kind)} ${recommended}${supporting}</small>
        </span>
      </label>
      <p>${escapeHtml(item.detail)}</p>
      ${artifactButton}
    </article>
  `;
}

function renderSourceFindingGroup(group) {
  const items = [...(group.items || [])].sort((left, right) => sourceFindingPriority(left) - sourceFindingPriority(right));
  const primaryItems = items.filter((item) => !item.collapsible || item.recommended || sourceFindingSelected(item.id));
  const supportingItems = items.filter((item) => item.collapsible && !item.recommended && !sourceFindingSelected(item.id));
  return `
    <section class="source-finding-group">
      <div class="surface-title">
        <span>${escapeHtml(group.label)}</span>
        <span class="small-badge">${escapeHtml(group.count)}</span>
      </div>
      <p>${escapeHtml(group.detail)}</p>
      <div class="source-finding-list">
        ${primaryItems.map((item) => renderSourceFindingItem(group, item)).join("") || `<div class="empty-state">No primary ${escapeHtml(group.label.toLowerCase())} found for this source run.</div>`}
      </div>
      ${supportingItems.length ? `
        <details class="source-finding-supporting">
          <summary>Supporting evidence (${escapeHtml(supportingItems.length)})</summary>
          <div class="source-finding-list">
            ${supportingItems.map((item) => renderSourceFindingItem(group, item)).join("")}
          </div>
        </details>
      ` : ""}
    </section>
  `;
}

function nextFlowWizardStepState(stepId) {
  const current = state.nextFlowWizard.step;
  const selected = state.nextFlowWizard.selectedSourceIds.length;
  if (state.nextFlowWizard.action === "clone-flow") {
    if (stepId === "type") return "done";
    if (stepId === "definition") {
      if (current === "definition") return "active";
      if (current === "confirm") return "done";
      return "pending";
    }
    if (stepId === "confirm") return current === "confirm" ? "active" : "pending";
    return "pending";
  }
  if (stepId === "type") return "done";
  if (stepId === "sources") {
    if (current === "sources") return "active";
    if (current === "definition" || current === "confirm") return "done";
    return selected ? "done" : "pending";
  }
  if (stepId === "definition") {
    if (current === "definition") return "active";
    if (current === "confirm") return "done";
    return "pending";
  }
  if (stepId === "confirm") return current === "confirm" ? "active" : "pending";
  return "pending";
}

function nextFlowWizardTypeLabel() {
  const labels = {
    "create-new-work-item": "New Work Item",
    "start-follow-up-flow": "Follow-up Flow",
    "clone-flow": "Clone This Flow",
    "run-eval-batch": "Eval / Scenario Batch"
  };
  return labels[state.nextFlowWizard.action] || "Next Flow";
}

function renderNextFlowWizardProgress() {
  const selected = state.nextFlowWizard.selectedSourceIds.length;
  const draft = state.nextFlowWizard.followUpDraft;
  const steps = state.nextFlowWizard.action === "clone-flow"
    ? [
        ["type", "Choose Flow Type", nextFlowWizardTypeLabel()],
        ["definition", "Review Clone Draft", draft?.new_work_item || "Review inherited configuration"],
        ["confirm", "Confirm Launch", "Review preflight and audit preview"]
      ]
    : [
        ["type", "Choose Flow Type", nextFlowWizardTypeLabel()],
        ["sources", "Select Source Findings", selected ? `${selected} selected` : "Select findings to carry forward"],
        ["definition", "Define Work Item", draft?.new_work_item || "Configure new work item"],
        ["confirm", "Confirm Launch", "Review preflight and audit preview"]
      ];
  return `
    <aside class="next-flow-stepper" aria-label="Flow Launch Wizard">
      <div class="surface-title compact">Flow Launch Wizard</div>
      <ol>
        ${steps.map(([id, label, detail], index) => {
          const stepState = nextFlowWizardStepState(id);
          return `
            <li class="${escapeHtml(stepState)}">
              <span class="wizard-step-index">${escapeHtml(index + 1)}</span>
              <span>
                <strong>${escapeHtml(label)}</strong>
                <small>${escapeHtml(detail)}</small>
              </span>
            </li>
          `;
        }).join("")}
      </ol>
      <div class="wizard-policy-note">
        <strong>Independent flow</strong>
        <span>The completed source run stays immutable; launch creates a new work item and run identity.</span>
      </div>
    </aside>
  `;
}

function renderNextFlowWizardShell({sectionClass = "next-flow-wizard", title, badge, badgeTone = "", body}) {
  return `
    <section class="surface ${sectionClass}">
      <div class="next-flow-wizard-frame">
        ${renderNextFlowWizardProgress()}
        <div class="next-flow-wizard-content">
          <div class="surface-title">
            <span>${escapeHtml(title)}</span>
            <span class="small-badge ${escapeHtml(badgeTone)}">${escapeHtml(badge)}</span>
          </div>
          ${body}
        </div>
      </div>
    </section>
  `;
}

function renderSourceSelectionSummary(payload, selectedCount) {
  const counts = payload.counts || {};
  const recommendedCount = Number(counts.recommended_items || 0);
  const linkedArtifacts = Number(counts.source_artifact_links || 0);
  const totalItems = Number(counts.total_items || 0);
  const recommendation = payload.recommendation || "Select the source findings to carry forward.";
  const noSelection = selectedCount === 0;
  return `
    <div class="source-selection-summary" role="status">
      <div>
        <strong>${escapeHtml(selectedCount)} selected / ${escapeHtml(totalItems)} available</strong>
        <span>${escapeHtml(recommendation)}</span>
      </div>
      <div class="source-selection-metrics">
        <span class="small-badge">${escapeHtml(linkedArtifacts)} linked artifacts</span>
        <span class="small-badge ${recommendedCount ? "good" : ""}">${escapeHtml(recommendedCount)} recommended</span>
        ${noSelection ? '<span class="small-badge warn">select at least one</span>' : ""}
      </div>
      <div class="source-selection-actions">
        <button data-source-selection-mode="recommended" type="button" class="secondary" ${recommendedCount ? "" : "disabled"}>Select recommended</button>
        <button data-source-selection-mode="clear" type="button" class="secondary" ${selectedCount ? "" : "disabled"}>Clear selection</button>
      </div>
    </div>
  `;
}

function renderNextFlowSourceSelection() {
  const wizard = state.nextFlowWizard;
  if (wizard.step === "new-work-item") {
    return renderNewWorkItemHandoff();
  }
  if (wizard.step === "eval-batch") {
    return renderEvalBatchHandoff();
  }
  if (wizard.step === "archive-confirm") {
    return renderArchiveConfirmation();
  }
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
  return renderNextFlowWizardShell({
    title: "Start Next Flow",
    badge: "source findings",
    body: `
      <div class="wizard-context-grid">
        <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(payload.source_run_id)}</span></div>
        <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(payload.source_work_item)}</span></div>
        <div class="panel-item"><strong>Selected sources</strong><span>${escapeHtml(selectedCount)} / ${escapeHtml(payload.counts.total_items)}</span></div>
        <div class="panel-item"><strong>Linked artifacts</strong><span>${escapeHtml(payload.counts.source_artifact_links)}</span></div>
      </div>
      ${renderSourceSelectionSummary(payload, selectedCount)}
      <div class="source-finding-groups">
        ${(payload.groups || []).map((group) => renderSourceFindingGroup(group)).join("")}
      </div>
      ${selectedCount ? "" : '<div class="truncation-notice"><strong>Selection required</strong><span>Choose at least one source finding before defining the follow-up work item.</span></div>'}
      <div class="wizard-actions">
        <button data-close-next-flow-wizard type="button" class="secondary">Back to handoff</button>
        <button data-next-flow-continue type="button" ${selectedCount ? "" : "disabled"}>Continue to Define Work Item</button>
      </div>
    `
  });
}

function renderNewWorkItemHandoff() {
  const sourceRun = nextFlowSourceRunId() || "not recorded";
  const sourceWorkItem = nextFlowSourceWorkItem() || "not recorded";
  return `
    <section class="surface next-flow-wizard">
      <div class="surface-title">
        <span>Create New Work Item</span>
        <span class="small-badge">fresh scope</span>
      </div>
      <div class="wizard-context-grid">
        <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(sourceRun)}</span></div>
        <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(sourceWorkItem)}</span></div>
        <div class="panel-item"><strong>Inheritance</strong><span>none by default</span></div>
        <div class="panel-item"><strong>Policy</strong><span>source run stays immutable</span></div>
      </div>
      <div class="truncation-notice" role="status">
        <strong>Fresh work item handoff</strong>
        <span>Create unrelated work from the target project root with a new request. Use Follow-up or Clone when this completed run should be inherited.</span>
      </div>
      <pre>aidd init --work-item &lt;new-id&gt; --request "&lt;new request&gt;" --root .aidd
aidd ui --work-item &lt;new-id&gt; --root .aidd</pre>
      <div class="wizard-actions">
        <button data-close-next-flow-wizard type="button" class="secondary">Back to handoff</button>
      </div>
    </section>
  `;
}

function renderEvalBatchHandoff() {
  const sourceRun = nextFlowSourceRunId() || "not recorded";
  const sourceWorkItem = nextFlowSourceWorkItem() || "not recorded";
  const artifacts = state.dashboard?.terminal_handoff?.final_artifacts || [];
  return `
    <section class="surface next-flow-wizard">
      <div class="surface-title">
        <span>Run Eval / Scenario Batch</span>
        <span class="small-badge">handoff</span>
      </div>
      <div class="wizard-context-grid">
        <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(sourceRun)}</span></div>
        <div class="panel-item"><strong>Source work item</strong><span>${escapeHtml(sourceWorkItem)}</span></div>
        <div class="panel-item"><strong>Final artifacts</strong><span>${escapeHtml(artifacts.length)}</span></div>
        <div class="panel-item"><strong>Scenario checkpoint</strong><span>manual checkpoint only</span></div>
      </div>
      <div class="truncation-notice" role="status">
        <strong>Eval batch handoff only</strong>
        <span>Use completed-run evidence for scenario planning or manual checkpoint review. This UI action does not launch a nested public-repository flow.</span>
      </div>
      <div class="recent-artifacts">${renderTerminalArtifacts(artifacts)}</div>
      <div class="wizard-actions">
        <button data-close-next-flow-wizard type="button" class="secondary">Back to handoff</button>
        <button data-tab-shortcut="history" type="button">Open Run History</button>
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

function renderLaunchSourceLink(item) {
  if (!item.source_path) {
    return `
      <div class="panel-item manual-source-row">
        <strong>${escapeHtml(item.title)}</strong>
        <span>${escapeHtml(item.detail || "Manual request text is captured in the follow-up request context.")}</span>
      </div>
    `;
  }
  return `
    <button class="artifact-row" data-artifact-stage="${escapeHtml(item.stage)}" data-artifact-key="${escapeHtml(item.artifact_key)}" data-artifact-kind="${escapeHtml(item.artifact_kind)}" type="button">
      <span><strong>${escapeHtml(item.title)}</strong>${pathLine(item.source_path, 76)}</span>
      <span class="small-badge">${escapeHtml(item.kind)}</span>
    </button>
  `;
}

function renderLaunchSourceLinks(draft) {
  return (draft?.selected_sources || []).map((item) => renderLaunchSourceLink(item)).join("")
    || `<div class="empty-state">No source links selected.</div>`;
}

function renderAuditPreview(draft, preflight) {
  const sources = draft.selected_sources || [];
  const artifactLinks = sources.filter((item) => item.source_path).length;
  return `
    <div class="audit-preview">
      <div class="panel-item"><strong>New work item</strong><span>${escapeHtml(draft.new_work_item)}</span></div>
      <div class="panel-item"><strong>Source run</strong><span>${escapeHtml(draft.source_run_id)}</span></div>
      <div class="panel-item"><strong>Runtime</strong><span>${escapeHtml(state.selectedRuntime || state.dashboard?.run?.runtime_id || "not selected")}</span></div>
      <div class="panel-item"><strong>Resolved baseline</strong><span>${escapeHtml(preflight?.resolved_baseline_id || "not resolved")}</span></div>
      <div class="panel-item"><strong>Selected sources</strong><span>${escapeHtml(sources.length)}</span></div>
      <div class="panel-item"><strong>Source artifact links</strong><span>${escapeHtml(artifactLinks)}</span></div>
    </div>
  `;
}

function renderLaunchConfirmation() {
  const wizard = state.nextFlowWizard;
  const draft = wizard.followUpDraft;
  if (!draft) {
    return `<section class="surface next-flow-wizard"><div class="empty-state">${escapeHtml(wizard.preflightError || "No next-flow draft available for launch confirmation.")}</div></section>`;
  }
  if (wizard.preflightLoading) {
    return `<section class="surface next-flow-wizard"><div class="empty-state loading-state">Running launch preflight...</div></section>`;
  }
  const preflight = wizard.preflight;
  const blocked = !preflight?.can_launch;
  const backLabel = wizard.action === "clone-flow" ? "Back to handoff" : "Back to definition";
  return renderNextFlowWizardShell({
    sectionClass: "next-flow-wizard launch-confirmation",
    title: "Confirm and Launch Next Flow",
    badge: preflight?.status || "blocked",
    badgeTone: preflightTone(preflight?.status || "blocked"),
    body: `
      ${wizard.preflightError ? `<div class="truncation-notice"><strong>Preflight blocked</strong><span>${escapeHtml(wizard.preflightError)}</span></div>` : ""}
      ${wizard.launchError ? `<div class="truncation-notice"><strong>Launch failed</strong><span>${escapeHtml(wizard.launchError)}</span></div>` : ""}
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
        <button data-next-flow-back-to-definition type="button" class="secondary">${escapeHtml(backLabel)}</button>
        <button data-launch-flow-now type="button" ${blocked || wizard.launchLoading ? "disabled" : ""}>${wizard.launchLoading ? "Launching..." : "Launch Flow Now"}</button>
      </div>
    `
  });
}

function renderEditableList(name, items, selectedItems = null) {
  const selected = selectedItems ? new Set(selectedItems.map((item) => String(item))) : null;
  return (items || []).map((item, index) => `
    <div class="editable-list-row">
      <input data-follow-up-list="${escapeHtml(name)}" data-follow-up-index="${escapeHtml(index)}" type="checkbox" ${!selected || selected.has(String(item)) ? "checked" : ""} aria-label="Include ${escapeHtml(item || name)}">
      <input data-follow-up-list-text="${escapeHtml(name)}" data-follow-up-index="${escapeHtml(index)}" type="text" value="${escapeHtml(item)}">
    </div>
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
  const acceptanceItems = draft.acceptance_criteria_all || draft.acceptance_criteria;
  const evidenceItems = draft.required_evidence_all || draft.required_evidence;
  return renderNextFlowWizardShell({
    sectionClass: "next-flow-wizard follow-up-definition",
    title: "Define Follow-up Work Item",
    badge: "editable draft",
    body: `
      ${wizard.preflightError ? `<div class="truncation-notice" data-follow-up-definition-error><strong>Definition needs attention</strong><span>${escapeHtml(wizard.preflightError)}</span></div>` : ""}
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
          <div class="editable-list">${renderEditableList("acceptance_criteria", acceptanceItems, draft.acceptance_criteria_all ? draft.acceptance_criteria : null)}</div>
          <div class="surface-title compact">Required evidence</div>
          <div class="editable-list">${renderEditableList("required_evidence", evidenceItems, draft.required_evidence_all ? draft.required_evidence : null)}</div>
          <div class="surface-title compact">Inherited context</div>
          <div class="inherited-context-list">${renderInheritedContextToggles(draft.inherited_context)}</div>
        </aside>
      </div>
      <div class="wizard-actions">
        <button data-next-flow-back-to-sources type="button" class="secondary">Back to sources</button>
        <button data-next-flow-confirm-preview type="button">Continue to preflight</button>
      </div>
    `
  });
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

function activeJobLiveMessage(job) {
  const status = job?.status || "running";
  if (status === "waiting-for-operator") return "Waiting for operator approval";
  if (status === "cancelling") return "Cancelling runtime job";
  return "Running now";
}

function renderGlobalLiveProgress(job) {
  if (!job) return "";
  const status = job.status || "running";
  const stage = job.stage || state.activeStage || "workflow";
  const stageLabel = stage ? stageTitle(stage) : "Run";
  const logChunkCount = state.activeJobLogChunks?.length || 0;
  return `
    <div class="live-progress-strip" role="status" aria-live="polite">
      <div class="live-progress-copy">
        <span class="small-badge ${escapeHtml(statusClass(status))}">${escapeHtml(status)}</span>
        <div>
          <strong>${escapeHtml(stageLabel)}: ${escapeHtml(activeJobLiveMessage(job))}</strong>
          <span>${escapeHtml(job.message || "Runtime is active; live logs are the current evidence stream.")}</span>
        </div>
      </div>
      <div class="run-progress-meta live-progress-meta">
        <span><strong>Elapsed</strong>${escapeHtml(secondsLabel(job.elapsed_seconds))}</span>
        <span><strong>Runtime output</strong>${escapeHtml(runtimeOutputFreshnessLabel(job))}</span>
        <span><strong>Live log chunks</strong>${escapeHtml(logChunkCount)}</span>
      </div>
      <div class="live-progress-actions">
        <button data-tab-shortcut="logs" type="button" class="secondary">Open live logs</button>
        <button data-cancel-job="${escapeHtml(job.job_id || state.activeJobId || "")}" type="button" class="danger" ${activeJobIsTerminal() ? "disabled" : ""}>${escapeHtml(activeJobCancelLabel())}</button>
      </div>
    </div>
  `;
}

function decisionPeekCountLabel(count, singular, plural = `${singular}s`) {
  return `${count} ${count === 1 ? singular : plural}`;
}

function reviewDecisionPeek(view) {
  const status = view?.approval_status || "not detected";
  const findings = view?.findings || [];
  const mustFix = findings.filter((finding) => finding.disposition === "must-fix").length;
  if (status === "approved") {
    return {
      tone: "good",
      badge: status,
      title: "Review approved",
      detail: `${decisionPeekCountLabel(findings.length, "finding")} recorded; QA is the next governed stage.`
    };
  }
  if (status === "rejected") {
    return {
      tone: "bad",
      badge: status,
      title: "Review rejected",
      detail: mustFix
        ? `${decisionPeekCountLabel(mustFix, "must-fix finding")} should go back to implement before QA.`
        : "Inspect review findings or request intervention before QA."
    };
  }
  return {
    tone: "warn",
    badge: status,
    title: "Review status unclear",
    detail: "Inspect review findings or request intervention before QA."
  };
}

function qaDecisionPeek(view) {
  const verdict = view?.quality_verdict || "not detected";
  const risks = view?.residual_risks || [];
  const issues = view?.known_issues || [];
  const total = risks.length + issues.length;
  if (verdict === "ready" && !total) {
    return {
      tone: "good",
      badge: verdict,
      title: "QA ready",
      detail: "No structured risks or known issues; accept complete when reviewed."
    };
  }
  if (verdict === "ready") {
    return {
      tone: "warn",
      badge: verdict,
      title: "QA ready with follow-up context",
      detail: `${decisionPeekCountLabel(total, "risk or issue", "risks or issues")} remain documented for accept or follow-up.`
    };
  }
  if (verdict === "not-ready") {
    return {
      tone: "bad",
      badge: verdict,
      title: "QA not ready",
      detail: total
        ? `${decisionPeekCountLabel(total, "risk or issue", "risks or issues")} should go back to implement before accept.`
        : "Inspect QA evidence before accepting or launching follow-up."
    };
  }
  return {
    tone: "warn",
    badge: verdict,
    title: "QA verdict unclear",
    detail: "Inspect QA evidence before accepting or launching follow-up."
  };
}

function terminalRepairDecisionPeek() {
  const highlight = state.dashboard?.terminal_handoff?.repair_highlights?.[0];
  if (!highlight) return null;
  return {
    tone: "good",
    badge: "repair resolved",
    title: `${stageTitle(highlight.stage)} retry ${highlight.attempt_number} resolved`,
    detail: highlight.reason || "Validation passed after repair before terminal handoff."
  };
}

function activeModeDecisionPeek() {
  if (state.activeTab !== "work") return null;
  if (state.workDetail === "review-findings" && state.reviewFindingsRunId === state.activeRunId && state.reviewFindingsView) {
    return reviewDecisionPeek(state.reviewFindingsView);
  }
  if (state.workDetail === "qa-verdict" && state.qaVerdictRunId === state.activeRunId && state.qaVerdictView) {
    return qaDecisionPeek(state.qaVerdictView);
  }
  return null;
}

function staleDownstreamStages() {
  return (state.dashboard?.stages || []).filter((item) => item.stale);
}

function staleDownstreamStageLabel(items) {
  const labels = items.map((item) => stageTitle(item.stage));
  if (!labels.length) return "downstream stages";
  return labels.join(" -> ");
}

function staleDownstreamInvalidator(items) {
  const invalidators = [...new Set(items.map((item) => item.stale_invalidated_by).filter(Boolean))];
  return invalidators.join(", ") || "remediation request";
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

function renderStaleDownstreamSummary(action) {
  const items = staleDownstreamStages();
  if (!items.length && action?.action !== "rerun-stale-downstream") return "";
  const stageLabel = staleDownstreamStageLabel(items);
  const invalidatedBy = staleDownstreamInvalidator(items);
  const runtimeGate = staleDownstreamRuntimeGate();
  const firstReason = items.find((item) => item.stale_reason)?.stale_reason
    || action?.detail
    || "A remediation attempt invalidated downstream stage evidence.";
  return `
    <div class="stale-downstream-summary" data-stale-downstream-summary role="status" aria-live="polite">
      <div class="stale-downstream-copy">
        <span class="small-badge warn">stale downstream</span>
        <strong>Rerun ${escapeHtml(stageLabel)} after remediation</strong>
        <p>${escapeHtml(firstReason)}</p>
        <small>Terminal QA handoff stays blocked until stale downstream evidence is refreshed.</small>
      </div>
      <div class="stale-downstream-facts">
        <span><strong>Stale stages</strong>${escapeHtml(stageLabel)}</span>
        <span><strong>Invalidated by</strong>${escapeHtml(invalidatedBy)}</span>
        <span><strong>Runtime</strong>${escapeHtml(runtimeGate.label)}</span>
        <span><strong>Next step</strong>${escapeHtml(runtimeGate.nextStep)}</span>
      </div>
    </div>
  `;
}

function renderModeDecisionPeek() {
  const peek = activeModeDecisionPeek() || terminalRepairDecisionPeek();
  if (!peek) return "";
  return `
    <div class="mode-decision-peek ${escapeHtml(peek.tone)}" aria-label="Current screen decision summary">
      <span class="small-badge ${escapeHtml(peek.tone)}">${escapeHtml(peek.badge)}</span>
      <strong>${escapeHtml(peek.title)}</strong>
      <span>${escapeHtml(peek.detail)}</span>
    </div>
  `;
}

function renderNextActionPanel() {
  const action = state.dashboard?.next_action || {action: "choose-runtime", label: "Select runtime", detail: "Choose a runtime.", enabled: false};
  const noRunWithRuntime = action.action === "choose-runtime" && state.selectedRuntime;
  const runStageResume = action.action === "run-stage" && state.activeRunId && action.enabled;
  const runtimeNeeded = needsRuntime(action.action) || noRunWithRuntime;
  const runtimeBlocked = runtimeNeeded && (!state.selectedRuntime || !selectedRuntimeReady());
  const activeJobState = activeJobNextActionState(action);
  const disabled = Boolean(activeJobState) || !(action.enabled || noRunWithRuntime) || runtimeBlocked;
  const label = activeJobState?.label || (noRunWithRuntime
    ? (state.activeRunId ? "Resume workflow" : "Run workflow")
    : runStageResume
      ? `Continue with ${stageTitle(action.stage || state.activeStage)}`
      : action.label);
  const baseDetail = activeJobState?.detail || (noRunWithRuntime
    ? runtimeBlocked
      ? "Runtime selected. Resolve readiness before starting the governed workflow."
      : "Runtime selected and ready to start the governed workflow."
    : action.detail);
  const detail = runtimeBlocked && state.selectedRuntime && !noRunWithRuntime
    ? `${baseDetail} ${state.readinessLoading ? "Checking runtime readiness." : "Selected runtime is not ready."}`
    : baseDetail;
  const finding = action.action === "inspect-validation" || action.action === "review-intervention"
    ? primaryValidationFinding()
    : null;
  document.getElementById("nextActionPanel").innerHTML = `
    <div class="panel-title">Run Next Action</div>
    <p>${escapeHtml(detail)}</p>
    ${renderValidationFindingSummary(finding, {compact: true})}
    <button id="nextActionButton" class="next-button" data-next-action="${escapeHtml(action.action)}" type="button" ${disabled ? "disabled" : ""}>${escapeHtml(label)}</button>
  `;
}

function renderGlobalNextActionStrip() {
  const host = document.getElementById("globalNextActionStrip");
  if (!host) return;
  syncLiveJobBodyClass();
  if (state.activeTab === "recovery" || state.onboarding?.setupRequired) {
    host.hidden = true;
    host.innerHTML = "";
    host.classList.remove("live-progress-active");
    return;
  }
  host.hidden = false;
  const action = state.dashboard?.next_action || {action: "choose-runtime", label: "Select runtime", detail: "Choose a runtime.", enabled: false};
  const noRunWithRuntime = action.action === "choose-runtime" && state.selectedRuntime;
  const runtimeNeeded = needsRuntime(action.action) || noRunWithRuntime;
  const runtimeBlocked = runtimeNeeded && (!state.selectedRuntime || !selectedRuntimeReady());
  const activeJobState = activeJobNextActionState(action);
  const disabled = Boolean(activeJobState) || !(action.enabled || noRunWithRuntime) || runtimeBlocked;
  const label = activeJobState?.label || (noRunWithRuntime
    ? (state.activeRunId ? "Resume workflow" : "Run workflow")
    : action.action === "run-stage" && state.activeRunId && action.enabled
      ? `Continue with ${stageTitle(action.stage || state.activeStage)}`
      : action.label);
  const detail = activeJobState?.detail || (noRunWithRuntime
    ? runtimeBlocked
      ? "Runtime selected. Resolve readiness before starting the workflow."
      : "Runtime selected. Start the workflow from the current work item."
    : action.detail);
  const stage = activeJobState?.stage || (action.stage ? stageTitle(action.stage) : state.dashboard?.active_stage || "run");
  const run = activeJobState?.run || state.activeRunId || "not started";
  const finding = action.action === "inspect-validation" || action.action === "review-intervention"
    ? primaryValidationFinding()
    : null;
  host.classList.toggle("live-progress-active", Boolean(activeJobState));
  host.innerHTML = `
    ${activeJobState ? renderGlobalLiveProgress(state.activeJobStatus) : ""}
    <div class="next-action-copy">
      <span class="next-action-icon" aria-hidden="true">&gt;</span>
      <div>
        <p class="eyebrow">Run Next Action</p>
        <h2>${escapeHtml(label)}</h2>
        <p>${escapeHtml(detail)}</p>
        ${renderValidationFindingSummary(finding)}
        ${renderStaleDownstreamSummary(action)}
        ${renderModeDecisionPeek()}
      </div>
    </div>
    <div class="next-action-controls">
      <div class="next-action-meta">
        <span><strong>Stage</strong>${escapeHtml(stage)}</span>
        <span><strong>Runtime</strong>${escapeHtml(state.selectedRuntime || state.dashboard?.run?.runtime_id || "required")}</span>
        <span><strong>Run</strong>${escapeHtml(run)}</span>
      </div>
      <button id="globalNextActionButton" class="next-button" type="button" ${disabled ? "disabled" : ""}>${escapeHtml(label)}</button>
    </div>
  `;
}

async function startWorkflow() {
  if (state.onboarding?.setupRequired || !state.dashboard?.work_item) {
    toast("Create or resume a work item before starting the workflow.");
    return;
  }
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

async function rerunStaleDownstream() {
  if (!ensureRunnableRuntime()) return;
  if (!state.activeRunId) {
    toast("No run selected.");
    return;
  }
  const job = await postJson("/api/remediation/rerun-downstream", {
    runtime: state.selectedRuntime,
    run_id: state.activeRunId,
    log_follow: true
  });
  await startJobPolling(job);
}

async function handleNextAction() {
  const action = state.dashboard?.next_action || {action: "choose-runtime"};
  if (activeJobBlocksNextAction(action)) {
    activateTab("logs");
    await renderCockpit();
    toast("Current job is still running. Inspect logs before starting another action.");
    return;
  }
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
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    await startStage(action.stage || state.activeStage);
    return;
  }
  if (action.action === "rerun-stale-downstream") {
    await rerunStaleDownstream();
    return;
  }
  if (action.action === "answer-questions") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeStageExplicit = true;
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
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    activateTab("validation");
    await renderCockpit();
    return;
  }
  if (action.action === "review-findings" || action.action === "qa-verdict") {
    if (action.stage && action.stage !== state.activeStage) {
      state.activeStage = action.stage;
      state.activeStageExplicit = true;
      state.activeArtifactKey = "";
      await fetchDashboard();
      await renderAll();
    }
    activateTab(action.action);
    await renderCockpit();
    return;
  }
  if (action.action === "review-complete") {
    activateTab("artifacts");
    await renderCockpit();
  }
}
