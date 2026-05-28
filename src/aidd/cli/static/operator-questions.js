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
      <button data-answer-resume-all type="button" ${blocked ? "disabled" : ""}>Resume stage</button>
    </aside>
  `;
}

function renderQuestionCards({showResume}) {
  const view = activeStageView()?.questions;
  const questions = view?.questions || [];
  if (!questions.length) {
    return `<div class="empty-state">No questions for this stage.</div>`;
  }
  return `
    <div class="question-list">
      ${questions.map((question, index) => {
        const resolved = question.status === "resolved";
        const questionLabel = question.question_id || `question ${index + 1}`;
        const questionTextId = questionControlId("question-text", question.question_id, index);
        const answerId = questionControlId("answer", question.question_id, index);
        const resolutionId = questionControlId("resolution", question.question_id, index);
        const displayStatus = questionDisplayStatus(question);
        const savedAnswer = question.answer_resolution
          ? `<div class="saved-answer"><span class="saved-answer-label">Saved ${escapeHtml(question.answer_resolution)} answer</span><span class="saved-answer-text">${escapeHtml(question.answer_text || "Answer recorded in answers.md; blocking question still requires a resolved answer.")}</span></div>`
          : "";
        return `
          <article class="question-card">
            <div class="question-head">
              <strong>${escapeHtml(question.question_id)}</strong>
              <span class="small-badge ${questionStatusClass(question)}">${escapeHtml(displayStatus)}</span>
            </div>
            <div class="question-meta">
              <span>${escapeHtml(question.policy)}</span>
              <span>${resolved ? "Answer accepted for resume" : "Answer required for recovery"}</span>
            </div>
            <p id="${questionTextId}">${escapeHtml(question.text)}</p>
            ${savedAnswer}
            <label class="sr-only" for="${answerId}">Answer for ${escapeHtml(questionLabel)}</label>
            <textarea id="${answerId}" name="${answerId}" aria-describedby="${questionTextId}" data-question-text="${escapeHtml(question.question_id)}" ${resolved ? "disabled" : ""}></textarea>
            <div class="question-actions">
              <label class="sr-only" for="${resolutionId}">Resolution for ${escapeHtml(questionLabel)}</label>
              <select id="${resolutionId}" name="${resolutionId}" aria-describedby="${questionTextId}" data-question-resolution="${escapeHtml(question.question_id)}" ${resolved ? "disabled" : ""}>
                <option value="resolved">resolved</option>
                <option value="partial">partial</option>
                <option value="deferred">deferred</option>
              </select>
              <button data-save-answer="${escapeHtml(question.question_id)}" type="button" ${resolved ? "disabled" : ""}>Save answer</button>
              ${showResume ? `<button data-answer-resume="${escapeHtml(question.question_id)}" type="button" ${resolved ? "disabled" : ""}>Answer & resume</button>` : ""}
            </div>
          </article>
        `;
      }).join("")}
    </div>
  `;
}

function renderQuestions() {
  const view = activeStageView()?.questions;
  return `
    <div class="interview-loop-screen">
      <section class="surface">
        <div class="surface-title">
          <span>Questions / Interview Loop</span>
          <span class="small-badge ${view?.unresolved_blocking_question_ids?.length ? "bad" : "good"}">${escapeHtml(view?.unresolved_blocking_question_ids?.length || 0)} required</span>
        </div>
        ${renderInterviewSummary(view)}
        ${renderQuestionCards({showResume: true})}
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
  await postJson("/api/answers", {
    stage: state.activeStage,
    question_id: questionId,
    text,
    resolution: resolution?.value || "resolved"
  });
  toast("Answer saved.");
  return true;
}

async function answerAndResume(questionId) {
  const saved = await saveAnswer(questionId);
  if (!saved) return;
  await fetchDashboard();
  const unresolved = state.dashboard?.active_stage_view?.questions?.unresolved_blocking_question_ids || [];
  if (unresolved.length) {
    await renderAll();
    toast("Answer saved; remaining blocking questions must be resolved before resume.");
    return;
  }
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
  await startStage(state.activeStage);
}
