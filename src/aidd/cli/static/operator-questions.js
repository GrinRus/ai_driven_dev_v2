function questionControlId(prefix, questionId, index) {
  const safeQuestionId = String(questionId ?? "")
    .trim()
    .replace(/[^A-Za-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return `${prefix}-${index + 1}-${safeQuestionId || "question"}`;
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
        const savedAnswer = resolved && question.answer_text
          ? `<div class="saved-answer"><span class="saved-answer-label">Saved answer</span><span class="saved-answer-text">${escapeHtml(question.answer_text)}</span></div>`
          : "";
        return `
          <article class="question-card">
            <div class="question-head">
              <strong>${escapeHtml(question.question_id)}</strong>
              <span class="small-badge ${question.status === "pending-blocking" ? "warn" : resolved ? "good" : ""}">${escapeHtml(question.status)}</span>
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
  return `<section class="surface">${renderQuestionCards({showResume: true})}</section>`;
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
