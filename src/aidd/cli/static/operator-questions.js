function decisionWorkbenchTypeLabel(type) {
  return type === "approval" ? "Approval" : "Question";
}

function decisionWorkbenchHeader({
  type,
  reason,
  sourceSnippets = [],
  consequence,
  inputSchema,
  evidence = [],
  primaryAction,
} = {}) {
  const normalizedType = type === "approval" ? "approval" : "question";
  const snippets = sourceSnippets
    .map((snippet) => String(snippet || "").trim())
    .filter(Boolean)
    .slice(0, 3);
  const evidencePaths = evidence
    .map((item) => String(item || "").trim())
    .filter(Boolean)
    .slice(0, 4);
  return `
    <section class="decision-workbench-header" data-decision-workbench-header="${normalizedType}">
      <div class="decision-workbench-heading">
        <span class="small-badge">Decision Workbench</span>
        <strong>${escapeHtml(decisionWorkbenchTypeLabel(normalizedType))} decision</strong>
        <p>${escapeHtml(reason || "Review the supplied context before submitting one durable decision.")}</p>
      </div>
      <dl class="decision-workbench-facts">
        <div><dt>Consequence</dt><dd data-decision-consequence>${escapeHtml(consequence || "The workflow remains unchanged until the decision is saved.")}</dd></div>
        <div><dt>Input schema</dt><dd data-decision-input-schema>${escapeHtml(inputSchema || "Decision-specific input")}</dd></div>
        <div><dt>Primary action</dt><dd data-decision-primary-label>${escapeHtml(primaryAction || "Submit decision")}</dd></div>
      </dl>
      <div class="decision-workbench-evidence">
        <div class="decision-workbench-source">
          <strong>Source snippets</strong>
          ${snippets.length
            ? `<ul>${snippets.map((snippet) => `<li data-decision-source-snippet>${escapeHtml(snippet)}</li>`).join("")}</ul>`
            : `<span class="muted" data-decision-source-empty>Source snippets unavailable; use the durable evidence links below.</span>`}
        </div>
        <div class="decision-workbench-retained-evidence">
          <strong>Decision evidence</strong>
          ${evidencePaths.length
            ? `<ul>${evidencePaths.map((item) => `<li data-decision-evidence>${escapeHtml(item)}</li>`).join("")}</ul>`
            : `<span class="muted" data-decision-evidence-empty>No retained decision evidence yet.</span>`}
        </div>
      </div>
    </section>
  `;
}

function questionControlId(prefix, questionId, index) {
  const safeQuestionId = String(questionId ?? "")
    .trim()
    .replace(/[^A-Za-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `${prefix}-${index + 1}-${safeQuestionId || "question"}`;
}

function questionDisplayStatus(question) {
  if (question.answer_resolution && question.answer_resolution !== "resolved") {
    return question.answer_resolution;
  }
  return question.status || "pending";
}

function questionStatusClass(question) {
  const status = questionDisplayStatus(question);
  if (status === "resolved") return "good";
  if (status === "partial" || status === "deferred") return "warn";
  if (status === "pending-blocking") return "bad";
  return "";
}

function questionRequiresResolvedResume(question) {
  return question?.policy === "blocking";
}

function questionDraftIdentity(questionId) {
  return operatorDraftIdentity("question", questionId);
}

function questionDraft(questionId) {
  return readOperatorDraft(questionDraftIdentity(questionId));
}

function persistQuestionDraft(questionId) {
  const textarea = document.querySelector(`[data-question-text="${CSS.escape(questionId)}"]`);
  const resolution = document.querySelector(`[data-question-resolution="${CSS.escape(questionId)}"]`);
  const evidence = document.querySelector(`[data-question-evidence="${CSS.escape(questionId)}"]`);
  const consequence = document.querySelector(`[data-question-consequence="${CSS.escape(questionId)}"]`);
  if (!textarea) return;
  writeOperatorDraft(questionDraftIdentity(questionId), {
    text: textarea.value,
    resolution: resolution?.value || "resolved",
    evidence_links: (evidence?.value || "").split("\n").map((value) => value.trim()).filter(Boolean),
    unblock_consequence: consequence?.value || ""
  });
}

function updateQuestionResumeButtonState(questionId) {
  const button = document.querySelector(`[data-answer-resume="${CSS.escape(questionId)}"]`);
  if (!button || button.dataset.requiresResolvedResume !== "true") return;
  const resolution = document.querySelector(`[data-question-resolution="${CSS.escape(questionId)}"]`);
  const textarea = document.querySelector(`[data-question-text="${CSS.escape(questionId)}"]`);
  const resolved = (resolution?.value || "resolved") === "resolved";
  const hasText = Boolean(textarea?.value?.trim());
  button.disabled = !(resolved && hasText);
  button.textContent = resolved && hasText
    ? (button.dataset.resumeReadyLabel || "Save answer & resume")
    : !hasText
      ? "Enter an answer to resume"
      : "Select resolved to resume";
  button.title = resolved && hasText
    ? ""
    : !hasText
      ? "Blocking questions need an answer before the stage can resume."
      : "Blocking questions must be saved as resolved before resume.";
}

function updateQuestionResumeButtonStates() {
  document.querySelectorAll("[data-answer-resume]").forEach((button) => {
    updateQuestionResumeButtonState(button.dataset.answerResume);
  });
}

function interviewDecisionCounts(view) {
  const questions = view?.questions || [];
  const unresolved = view?.unresolved_blocking_question_ids || [];
  return {
    total: questions.length,
    required: unresolved.length,
    resolved: questions.filter(
      (question) => question.answer_resolution === "resolved"
    ).length,
    partial: questions.filter(
      (question) => question.answer_resolution === "partial"
    ).length,
    deferred: questions.filter(
      (question) => question.answer_resolution === "deferred"
    ).length
  };
}

function renderInterviewDecisionSpotlight(view) {
  const counts = interviewDecisionCounts(view);
  let tone = "good";
  let title = "No interview questions for this stage";
  let body = (
    "This stage has no model-authored questions. Continue the workflow when runtime "
    + "readiness allows."
  );
  let primary = "Primary action: continue stage flow";
  if (counts.required) {
    tone = "bad";
    title = "Blocking questions need resolved answers";
    body = (
      `${counts.required} blocking question${counts.required === 1 ? "" : "s"} must be `
      + "saved as resolved before the runtime can resume. Answer each active card, choose "
      + "resolved, then resume the stage."
    );
    primary = "Primary action: answer required questions";
  } else if (counts.partial || counts.deferred) {
    tone = "warn";
    title = "Interview answers need final resolution";
    body = (
      `${counts.partial} partial and ${counts.deferred} deferred answer`
      + `${counts.partial + counts.deferred === 1 ? "" : "s"} are saved. Review them before `
      + "treating the stage context as final."
    );
    primary = "Primary action: update partial or deferred answers";
  } else if (counts.resolved) {
    title = "Interview answers saved";
    body = (
      `${counts.resolved} resolved answer${counts.resolved === 1 ? "" : "s"} are saved in `
      + "answers.md. Resume the stage when runtime readiness allows."
    );
    primary = "Primary action: resume stage";
  }
  return `
    <div class="interview-decision-spotlight ${escapeHtml(tone)}"
      data-interview-decision-spotlight role="status" aria-live="polite">
      <div class="interview-decision-copy">
        <span class="small-badge ${escapeHtml(tone)}">interview loop</span>
        <strong>${escapeHtml(title)}</strong>
        <p>${escapeHtml(body)}</p>
        <small>${escapeHtml(primary)}</small>
      </div>
      <div class="interview-decision-facts">
        <span><strong>Required</strong>${escapeHtml(counts.required)}</span>
        <span><strong>Resolved</strong>${escapeHtml(counts.resolved)}</span>
        <span><strong>Partial</strong>${escapeHtml(counts.partial)}</span>
        <span><strong>Deferred</strong>${escapeHtml(counts.deferred)}</span>
        <span><strong>Total</strong>${escapeHtml(counts.total)}</span>
      </div>
    </div>
  `;
}

function renderInterviewSummary(view) {
  const questions = view?.questions || [];
  const unresolved = view?.unresolved_blocking_question_ids || [];
  const answered = questions.filter((question) => question.answer_resolution === "resolved").length;
  const partial = questions.filter((question) => question.answer_resolution === "partial").length;
  const deferred = questions.filter((question) => question.answer_resolution === "deferred").length;
  return `
    <div class="interview-summary">
      <div class="metric"><span>Required answers</span><strong>${escapeHtml(unresolved.length)}</strong></div>
      <div class="metric"><span>Resolved</span><strong>${escapeHtml(answered)}</strong></div>
      <div class="metric"><span>Partial</span><strong>${escapeHtml(partial)}</strong></div>
      <div class="metric"><span>Deferred</span><strong>${escapeHtml(deferred)}</strong></div>
    </div>
    <div class="panel-item">
      <strong>Answers document</strong>
      ${pathLine(view?.answers_path || "answers.md not materialized", 88)}
    </div>
  `;
}

function interviewCandidateRecoveryAction(candidate) {
  const canonical = candidate?.canonical_question;
  if (!candidate || candidate.status !== "rejected") return null;
  const questionId = canonical?.question_id || "";
  const draft = questionId ? questionDraft(questionId)?.value : null;
  const canonicalResolved = canonical?.answer_resolution === "resolved";
  if (questionId && (!canonicalResolved || draft)) {
    return {
      kind: "focus-question",
      questionId,
      label: draft ? "Review restored answer draft" : "Edit canonical answer",
      detail: draft
        ? "The browser-session draft is preserved. Review it in the canonical answer card before resuming."
        : "The runtime candidate is not authoritative. Confirm or edit the canonical answer before resuming."
    };
  }
  if (candidate.eligible_recovery_action === "resume-stage") {
    return {
      kind: "resume-stage",
      label: "Resume with canonical answer",
      detail: "The canonical ledger is resolved; resume is a non-repair attempt and does not spend repair budget."
    };
  }
  return null;
}

function renderInterviewCandidateRecovery(candidate) {
  if (!candidate || candidate.status === "absent" || candidate.status === "accepted") return "";
  const canonical = candidate.canonical_question;
  const action = interviewCandidateRecoveryAction(candidate);
  const canonicalText = canonical?.text || "Canonical question is unavailable.";
  const canonicalAnswer = canonical?.answer_text || "No protected operator answer is recorded.";
  const canonicalResolution = canonical?.answer_resolution || "unresolved";
  const evidencePath = candidate.raw_candidate_path || candidate.disposition_path || "";
  const statusLabel = candidate.status === "permission-unavailable"
    ? "candidate evidence unavailable"
    : candidate.status === "stale"
      ? "stale candidate evidence"
      : "runtime candidate rejected";
  const requestChange = candidate.status === "rejected"
    ? `<button data-recovery-action="request-change" data-recovery-stage="${escapeHtml(state.activeStage)}" type="button" class="secondary" data-decision-alternative="request-change">Request Change</button>`
    : "";
  const inspectEvidence = evidencePath
    ? `<button data-evidence-stage="${escapeHtml(state.activeStage)}" data-evidence-path="${escapeHtml(evidencePath)}" data-evidence-kind="document" data-interview-candidate-evidence type="button" class="secondary">Inspect retained evidence</button>`
    : "";
  let primary = "";
  if (action?.kind === "focus-question") {
    primary = `<button data-primary-action data-decision-submit="true" data-focus-question="${escapeHtml(action.questionId)}" type="button">${escapeHtml(action.label)}</button>`;
  } else if (action?.kind === "resume-stage") {
    primary = `<button data-primary-action data-decision-submit="true" data-recovery-action="resume-stage" data-recovery-stage="${escapeHtml(state.activeStage)}" type="button">${escapeHtml(action.label)}</button>`;
  }
  return `
    <section class="surface interview-candidate-recovery" data-interview-candidate-recovery="${escapeHtml(candidate.status)}" data-decision-item="interview-candidate" data-primary-recovery-slot>
      <div class="surface-title">
        <span>Rejected interview candidate</span>
        <span class="small-badge ${candidate.status === "rejected" ? "bad" : "warn"}" data-interview-candidate-status>${escapeHtml(statusLabel)}</span>
      </div>
      <p class="muted" data-interview-candidate-reason>${escapeHtml(candidate.reason || candidate.eligible_recovery_detail || "Review the retained candidate evidence before choosing a next action.")}</p>
      <dl class="decision-workbench-facts interview-candidate-facts">
        <div><dt>Document</dt><dd data-interview-candidate-document>${escapeHtml(candidate.document || "not identified")}</dd></div>
        <div><dt>Source attempt</dt><dd data-interview-candidate-attempt>${escapeHtml(candidate.source_attempt || "not recorded")}</dd></div>
        <div><dt>Runtime</dt><dd data-interview-candidate-runtime>${escapeHtml(candidate.runtime_id || "not recorded")}</dd></div>
        <div><dt>Attempt mode</dt><dd data-interview-candidate-mode>${escapeHtml(candidate.attempt_mode || "not recorded")}</dd></div>
      </dl>
      <div class="decision-workbench-evidence">
        <div class="decision-workbench-source">
          <strong>Canonical state</strong>
          <p data-interview-candidate-canonical-question>${escapeHtml(canonicalText)}</p>
          <p><span class="small-badge">${escapeHtml(canonicalResolution)}</span> ${escapeHtml(canonicalAnswer)}</p>
          ${canonical?.answer_evidence_links?.length ? `<ul>${canonical.answer_evidence_links.slice(0, 4).map((path) => `<li data-interview-candidate-canonical-evidence>${escapeHtml(path)}</li>`).join("")}</ul>` : `<span class="muted">No canonical answer evidence links retained.</span>`}
        </div>
        <div class="decision-workbench-retained-evidence">
          <strong>Rejected fragment</strong>
          ${candidate.raw_candidate ? `<pre data-interview-candidate-raw>${escapeHtml(candidate.raw_candidate)}${candidate.raw_candidate_truncated ? "\n… [bounded]" : ""}</pre>` : `<span class="muted" data-interview-candidate-raw-empty>Raw candidate is unavailable.</span>`}
          ${candidate.raw_candidate_path ? pathLine(candidate.raw_candidate_path, 88) : ""}
        </div>
      </div>
      ${action?.detail ? `<p class="muted" data-interview-candidate-action-detail>${escapeHtml(action.detail)}</p>` : `<p class="muted" data-interview-candidate-action-detail>${escapeHtml(candidate.eligible_recovery_detail || "No recovery action is eligible until evidence access is restored.")}</p>`}
      <div class="question-actions interview-candidate-actions">
        ${inspectEvidence}
        ${primary}
        ${requestChange}
      </div>
    </section>
  `;
}

function renderBlockedStageContext(view) {
  const diagnostics = activeStageView()?.diagnostics;
  const blocking = diagnostics?.blocking_questions;
  const unresolved = blocking?.unresolved_question_ids || view?.unresolved_blocking_question_ids || [];
  const blocked = unresolved.length > 0;
  return `
    <aside class="surface interview-context-panel">
      <div class="surface-title">
        <span>Interview Loop</span>
        <span class="small-badge ${blocked ? "bad" : "good"}">${blocked ? "blocked" : "clear"}</span>
      </div>
      <div class="panel-item">
        <strong>Blocked stage</strong>
        <span>${blocked ? escapeHtml(stageTitle(state.activeStage)) : "No blocked stage"}</span>
      </div>
      <div class="panel-item">
        <strong>Required question ids</strong>
        <span>${escapeHtml(unresolved.join(", ") || "none")}</span>
      </div>
      <div class="panel-item">
        <strong>Resume rule</strong>
        <span>${blocked ? "Resolve all blocking questions before continuing the runtime." : "Stage can resume when runtime readiness allows."}</span>
      </div>
      <p class="muted recovery-context-note">Use the answer card action after each required answer is ready.</p>
    </aside>
  `;
}

function renderQuestionCards({showResume}) {
  const view = activeStageView()?.questions;
  const questions = view?.questions || [];
  const destination = view?.answers_path || "answers.md not materialized";
  const unresolved = new Set(view?.unresolved_blocking_question_ids || []);
  if (!questions.length) {
    return `<div class="empty-state">No questions for this stage.</div>`;
  }
  const activeQuestions = questions.filter((question) => unresolved.has(question.question_id));
  const historyQuestions = questions.filter((question) => !unresolved.has(question.question_id));
  const renderCards = (items) => items.map((question, index) => {
        const questionLabel = question.question_id || `question ${index + 1}`;
        const questionTextId = questionControlId("question-text", question.question_id, index);
        const answerId = questionControlId("answer", question.question_id, index);
        const resolutionId = questionControlId("resolution", question.question_id, index);
        const evidenceId = questionControlId("evidence", question.question_id, index);
        const consequenceId = questionControlId("consequence", question.question_id, index);
        const displayStatus = questionDisplayStatus(question);
        const savedAnswer = question.answer_resolution
          ? `<div class="saved-answer"><span class="saved-answer-label">Saved ${escapeHtml(question.answer_resolution)} answer</span><span class="saved-answer-text">${escapeHtml(question.answer_text || "Answer recorded in answers.md; blocking question still requires a resolved answer.")}</span></div>`
          : "";
        const draft = questionDraft(question.question_id)?.value || null;
        const answerText = draft?.text ?? question.answer_text ?? "";
        const resolutionValue = draft?.resolution || question.answer_resolution || "resolved";
        const evidenceLinks = draft?.evidence_links || question.answer_evidence_links || [];
        const unblockConsequence = draft?.unblock_consequence ?? question.answer_unblock_consequence ?? "";
        const resumeNeedsResolved = questionRequiresResolvedResume(question);
        const resumeDisabled = resumeNeedsResolved && (
          resolutionValue !== "resolved" || !answerText.trim()
        );
        const resumeLabel = resumeDisabled
          ? !answerText.trim() ? "Enter an answer to resume" : "Select resolved to resume"
          : displayStatus === "resolved" ? "Update & resume" : "Answer & resume";
        return `
          <article class="question-card" data-question-id="${escapeHtml(question.question_id)}" data-question-status="${escapeHtml(displayStatus)}" data-answer-resolution="${escapeHtml(resolutionValue)}" data-decision-item="question" data-decision-source="${escapeHtml(question.text || "")}">
            <div class="question-head">
              <strong>${escapeHtml(question.question_id)}</strong>
              <span class="small-badge ${questionStatusClass(question)}">${escapeHtml(displayStatus)}</span>
            </div>
            <div class="question-meta">
              <span>${escapeHtml(question.policy)}</span>
              <span>${displayStatus === "resolved" ? "Answer accepted for resume; edit if it changed" : "Resolved answer required for recovery"}</span>
            </div>
            <p id="${questionTextId}">${escapeHtml(question.text)}</p>
            ${savedAnswer}
            ${draft ? `<p class="muted question-draft-status" data-question-draft-restored="${escapeHtml(question.question_id)}">Restored unsent session draft.</p>` : ""}
            <label class="sr-only" for="${answerId}">Answer for ${escapeHtml(questionLabel)}</label>
            <textarea id="${answerId}" name="${answerId}" aria-describedby="${questionTextId}" data-question-text="${escapeHtml(question.question_id)}">${escapeHtml(answerText)}</textarea>
            <label class="question-context-field" for="${evidenceId}">
              <span>Evidence links <small>(one path or URL per line)</small></span>
              <textarea id="${evidenceId}" name="${evidenceId}" rows="2" data-question-evidence="${escapeHtml(question.question_id)}" placeholder="reports/qa.md#decision">${escapeHtml(evidenceLinks.join("\n"))}</textarea>
            </label>
            <label class="question-context-field" for="${consequenceId}" data-decision-consequence-field>
              <span>Unblock consequence</span>
              <textarea id="${consequenceId}" name="${consequenceId}" rows="2" data-question-consequence="${escapeHtml(question.question_id)}" placeholder="What can resume after this answer is accepted?">${escapeHtml(unblockConsequence)}</textarea>
            </label>
            <div class="answer-preview-panel" data-answer-preview-panel="${escapeHtml(question.question_id)}" hidden aria-live="polite"></div>
            <div class="question-actions">
              <label class="sr-only" for="${resolutionId}">Resolution for ${escapeHtml(questionLabel)}</label>
              <select id="${resolutionId}" name="${resolutionId}" aria-describedby="${questionTextId}" data-question-resolution="${escapeHtml(question.question_id)}">
                <option value="resolved" ${resolutionValue === "resolved" ? "selected" : ""}>resolved</option>
                <option value="partial" ${resolutionValue === "partial" ? "selected" : ""}>partial</option>
                <option value="deferred" ${resolutionValue === "deferred" ? "selected" : ""}>deferred</option>
              </select>
              <details class="question-save-options">
                <summary>Save draft only</summary>
              <button data-save-answer="${escapeHtml(question.question_id)}" data-decision-alternative="draft" type="button" class="secondary">${displayStatus === "resolved" ? "Update answer" : "Save answer"}</button>
              </details>
              <button data-answer-preview="${escapeHtml(question.question_id)}" type="button" class="secondary">Preview answers.md</button>
              ${showResume ? `<button data-primary-action data-decision-submit="true" data-answer-resume="${escapeHtml(question.question_id)}" data-requires-resolved-resume="${resumeNeedsResolved ? "true" : "false"}" data-resume-ready-label="Save answer & resume" type="button" ${resumeDisabled ? 'disabled title="Blocking questions must be saved as resolved before resume."' : ""}>${escapeHtml(resumeLabel === "Update & resume" || resumeLabel === "Answer & resume" ? "Save answer & resume" : resumeLabel)}</button>` : ""}
              <span class="question-durable-destination" data-answer-destination="${escapeHtml(question.question_id)}"><strong>Durable destination</strong>${pathLine(destination, 88)}</span>
            </div>
          </article>
        `;
      }).join("");
  return `
    <div class="question-list">
      ${activeQuestions.length ? renderCards(activeQuestions) : `<div class="empty-state compact">No unresolved blocking questions.</div>`}
      <details class="question-history" ${activeQuestions.length ? "" : "open"}>
        <summary>Answered and non-blocking questions (${escapeHtml(historyQuestions.length)})</summary>
        <div class="question-list compact">
          ${historyQuestions.length ? renderCards(historyQuestions) : `<div class="empty-state compact">No answered or non-blocking questions yet.</div>`}
        </div>
      </details>
    </div>
  `;
}

function renderQuestions() {
  const view = activeStageView()?.questions;
  const candidate = activeStageView()?.diagnostics?.interview_candidate;
  const questions = view?.questions || [];
  const unresolved = view?.unresolved_blocking_question_ids || [];
  const sourceSnippets = questions.map((question) => `${question.question_id || "Question"}: ${question.text || ""}`);
  const evidence = [view?.answers_path].filter(Boolean);
  return `
    <div class="interview-loop-screen" data-human-decision-surface="question" data-recovery-summary="question" data-decision-workbench="question" data-decision-item-count="${escapeHtml(questions.length)}">
      <section class="surface">
        <div class="surface-title">
          <span>Questions / Interview Loop</span>
          <span class="small-badge ${unresolved.length ? "bad" : "good"}">${escapeHtml(unresolved.length)} required</span>
        </div>
        ${renderQuestionCards({showResume: true})}
        ${decisionWorkbenchHeader({
          type: "question",
          reason: unresolved.length
            ? `${unresolved.length} blocking question${unresolved.length === 1 ? "" : "s"} require an operator decision before the stage can resume.`
            : "Review the question context and record the resolution that should shape the next stage action.",
          sourceSnippets,
          consequence: unresolved.length ? "A resolved answer can unblock stage resume; partial or deferred answers remain visible and fail closed." : "The saved answer becomes durable stage context.",
          inputSchema: "answer text + resolution + evidence links + unblock consequence",
          evidence,
          primaryAction: "Save answer & resume",
        })}
        ${renderInterviewDecisionSpotlight(view)}
        ${renderInterviewSummary(view)}
        ${renderInterviewCandidateRecovery(candidate)}
      </section>
      ${renderBlockedStageContext(view)}
    </div>
  `;
}

async function saveAnswer(questionId) {
  const textarea = document.querySelector(`[data-question-text="${CSS.escape(questionId)}"]`);
  const resolution = document.querySelector(`[data-question-resolution="${CSS.escape(questionId)}"]`);
  const text = textarea?.value?.trim() || "";
  if (!text) {
    toast("Answer text is required.");
    return false;
  }
  const evidence = document.querySelector(`[data-question-evidence="${CSS.escape(questionId)}"]`);
  const consequence = document.querySelector(`[data-question-consequence="${CSS.escape(questionId)}"]`);
  const evidenceLinks = (evidence?.value || "").split("\n").map((value) => value.trim()).filter(Boolean);
  const unblockConsequence = consequence?.value?.trim() || "";
  const key = operatorMutationKey(
    "answer",
    state.dashboard?.work_item || state.activeRouteWorkItem || "no-work-item",
    state.activeRunId || "no-run",
    state.activeStage,
    questionId
  );
  const controls = [
    `[data-save-answer="${questionId}"]`,
    `[data-answer-resume="${questionId}"]`
  ];
  const answerPayload = {
    stage: state.activeStage,
    question_id: questionId,
    text,
    resolution: resolution?.value || "resolved"
  };
  if (evidenceLinks.length) answerPayload.evidence_links = evidenceLinks;
  if (unblockConsequence) answerPayload.unblock_consequence = unblockConsequence;
  const durableQuestion = async () => {
    await fetchDashboard();
    return state.dashboard?.active_stage_view?.questions?.questions?.find(
      (question) => question.question_id === questionId
    ) || null;
  };
  const guarded = await runGuardedMutation({
    key,
    execute: async () => {
      await postJson("/api/answers", answerPayload);
      const readback = await durableQuestion();
      if (
        readback?.answer_text !== text
        || readback?.answer_resolution !== (resolution?.value || "resolved")
        || JSON.stringify(readback?.answer_evidence_links || []) !== JSON.stringify(evidenceLinks)
        || (readback?.answer_unblock_consequence || "") !== unblockConsequence
      ) {
        throw new Error("Answer durable readback did not match the submitted value");
      }
      clearOperatorDraft(questionDraftIdentity(questionId));
      return readback;
    },
    readWinner: durableQuestion,
    onState: (mutation) => setMutationControlsPending(controls, mutation.status === "pending")
  });
  if (guarded.status === "conflict") {
    clearOperatorDraft(questionDraftIdentity(questionId));
    await renderAll();
    toast("Another answer already won. Showing the durable answer.");
    return false;
  }
  toast("Answer saved.");
  return true;
}

async function previewAnswer(questionId) {
  const textarea = document.querySelector(`[data-question-text="${CSS.escape(questionId)}"]`);
  const resolution = document.querySelector(`[data-question-resolution="${CSS.escape(questionId)}"]`);
  const evidence = document.querySelector(`[data-question-evidence="${CSS.escape(questionId)}"]`);
  const consequence = document.querySelector(`[data-question-consequence="${CSS.escape(questionId)}"]`);
  const panel = document.querySelector(`[data-answer-preview-panel="${CSS.escape(questionId)}"]`);
  if (!textarea || !panel) return;
  const text = textarea.value.trim();
  if (!text) {
    panel.hidden = false;
    panel.textContent = "Answer text is required before preview.";
    return;
  }
  panel.hidden = false;
  panel.textContent = "Building durable answers.md preview…";
  try {
    const payload = await postJson("/api/answers", {
      mode: "preview",
      stage: state.activeStage,
      question_id: questionId,
      text,
      resolution: resolution?.value || "resolved",
      evidence_links: (evidence?.value || "").split("\n").map((value) => value.trim()).filter(Boolean),
      unblock_consequence: consequence?.value?.trim() || ""
    });
    panel.innerHTML = `<strong>Preview · ${escapeHtml(payload.answers_path || "answers.md")}</strong><pre>${escapeHtml(payload.markdown || "")}</pre>`;
  } catch (error) {
    panel.textContent = `Preview unavailable: ${error.message}`;
  }
}

async function answerAndResume(questionId) {
  const resolution = document.querySelector(`[data-question-resolution="${CSS.escape(questionId)}"]`);
  if ((resolution?.value || "resolved") !== "resolved") {
    updateQuestionResumeButtonState(questionId);
    toast("Select resolved before resuming a blocking stage.");
    return;
  }
  const saved = await saveAnswer(questionId);
  if (!saved) return;
  await fetchDashboard();
  const unresolved = state.dashboard?.active_stage_view?.questions?.unresolved_blocking_question_ids || [];
  if (unresolved.length) {
    await renderAll();
    toast("Answer saved; remaining blocking questions must be resolved before resume.");
    return;
  }
  await fetchReadiness();
  await startStage(state.activeStage);
}

async function resumeAfterAnswers() {
  await fetchDashboard();
  const unresolved = state.dashboard?.active_stage_view?.questions?.unresolved_blocking_question_ids || [];
  if (unresolved.length) {
    await renderAll();
    toast("Resolve blocking questions before resume.");
    return;
  }
  await fetchReadiness();
  await startStage(state.activeStage);
}
