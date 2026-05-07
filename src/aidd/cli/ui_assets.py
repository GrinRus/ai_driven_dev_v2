from __future__ import annotations

# ruff: noqa: E501
_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AIDD Operator</title>
  <link rel="stylesheet" href="/operator.css">
</head>
<body>
  <header class="topbar">
    <div>
      <h1>AIDD Operator</h1>
      <p id="runLine">No run selected</p>
    </div>
    <div class="run-controls">
      <label for="runtimeSelect">Runtime</label>
      <select id="runtimeSelect">
        <option value="">Select runtime</option>
      </select>
      <button id="runButton" type="button" disabled>Run</button>
    </div>
  </header>
  <main class="layout">
    <nav id="stages" class="stages"></nav>
    <section class="pane">
      <div class="tabs">
        <button data-tab="questions" class="active" type="button">Questions</button>
        <button data-tab="logs" type="button">Logs</button>
        <button data-tab="artifacts" type="button">Artifacts</button>
        <button data-tab="readiness" type="button">Readiness</button>
      </div>
      <div id="stageMeta" class="meta"></div>
      <div id="content" class="content"></div>
    </section>
  </main>
  <script src="/operator.js"></script>
</body>
</html>
"""


_OPERATOR_CSS = """
:root {
  color-scheme: light;
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f7f7f4;
  color: #1d211c;
}
* { box-sizing: border-box; }
body { margin: 0; min-height: 100vh; }
.topbar {
  align-items: center;
  background: #ffffff;
  border-bottom: 1px solid #d8ddd2;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  padding: 16px 24px;
}
h1 { font-size: 20px; line-height: 1.2; margin: 0; }
p { margin: 4px 0 0; }
button {
  background: #285e61;
  border: 1px solid #285e61;
  border-radius: 6px;
  color: #ffffff;
  cursor: pointer;
  font: inherit;
  min-height: 36px;
  padding: 7px 12px;
}
button:disabled {
  background: #aeb8ac;
  border-color: #aeb8ac;
  cursor: not-allowed;
}
button.secondary, .tabs button {
  background: #ffffff;
  border-color: #cdd5c6;
  color: #1d211c;
}
select {
  background: #ffffff;
  border: 1px solid #cdd5c6;
  border-radius: 6px;
  color: #1d211c;
  font: inherit;
  min-height: 36px;
  min-width: 180px;
  padding: 7px 10px;
}
.run-controls {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.run-controls label {
  color: #4d584f;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}
.tabs button.active { border-color: #285e61; color: #285e61; }
.layout {
  display: grid;
  gap: 0;
  grid-template-columns: minmax(180px, 240px) minmax(0, 1fr);
  min-height: calc(100vh - 73px);
}
.stages {
  background: #eef1ea;
  border-right: 1px solid #d8ddd2;
  padding: 12px;
}
.stage-button {
  align-items: center;
  background: transparent;
  border-color: transparent;
  color: #1d211c;
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
  width: 100%;
}
.stage-button.active { background: #dfe9e2; border-color: #9bb7a2; }
.stage-status {
  color: #647067;
  font-size: 12px;
  margin-left: 8px;
}
.pane { padding: 16px 20px; }
.tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.meta {
  border-bottom: 1px solid #d8ddd2;
  color: #4d584f;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 12px;
}
.content { padding-top: 12px; }
.question {
  border-bottom: 1px solid #e0e5dc;
  display: grid;
  gap: 8px;
  padding: 12px 0;
}
.question textarea {
  border: 1px solid #cdd5c6;
  border-radius: 6px;
  font: inherit;
  min-height: 70px;
  padding: 8px;
  resize: vertical;
  width: 100%;
}
pre {
  background: #111614;
  border-radius: 6px;
  color: #e8efe9;
  margin: 0;
  max-height: 66vh;
  overflow: auto;
  padding: 12px;
  white-space: pre-wrap;
}
.list { margin: 0; padding-left: 18px; }
.readiness-table {
  border-collapse: collapse;
  min-width: 960px;
  width: 100%;
}
.readiness-table th,
.readiness-table td {
  border-bottom: 1px solid #d8ddd2;
  padding: 8px;
  text-align: left;
  vertical-align: top;
}
.readiness-table th {
  color: #4d584f;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}
.readiness-scroll { overflow-x: auto; }
.runtime-command {
  background: #eef1ea;
  border-radius: 4px;
  display: inline-block;
  max-width: 360px;
  overflow-wrap: anywhere;
  padding: 2px 4px;
}
@media (max-width: 780px) {
  .layout { grid-template-columns: 1fr; }
  .stages { border-right: 0; border-bottom: 1px solid #d8ddd2; }
  .topbar { align-items: flex-start; flex-direction: column; }
}
"""


_OPERATOR_JS = """
const stages = ["idea", "research", "plan", "review-spec", "tasklist", "implement", "review", "qa"];
let activeStage = "idea";
let activeTab = "questions";
let selectedRuntime = "";

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok || payload.error) throw new Error(payload.error || response.statusText);
  return payload;
}

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

function setRunButtonState() {
  document.getElementById("runButton").disabled = !selectedRuntime;
}

function renderRuntimeSelector(runtimes) {
  const select = document.getElementById("runtimeSelect");
  const runtimeIds = runtimes.map((runtime) => String(runtime.runtime_id || ""));
  if (selectedRuntime && !runtimeIds.includes(selectedRuntime)) {
    selectedRuntime = "";
  }
  select.innerHTML = [
    `<option value="">Select runtime</option>`,
    ...runtimes.map((runtime) => {
      const runtimeId = String(runtime.runtime_id || "");
      const selected = runtimeId === selectedRuntime ? " selected" : "";
      const availability = runtime.provider_available && runtime.execution_command_available ? "ready" : "check readiness";
      return `<option value="${escapeHtml(runtimeId)}"${selected}>${escapeHtml(runtimeId)} (${escapeHtml(availability)})</option>`;
    })
  ].join("");
  setRunButtonState();
}

async function loadRuntimeChoices() {
  const view = await api("/api/runtime-readiness");
  renderRuntimeSelector(view.runtimes || []);
  return view;
}

async function loadRun() {
  try {
    const run = await api("/api/run");
    const metadata = run.metadata;
    setText("runLine", `${metadata.work_item} / ${metadata.run_id} / ${metadata.runtime_id}`);
    const statusByStage = Object.fromEntries(metadata.stages.map((stage) => [stage.stage, stage]));
    document.getElementById("stages").innerHTML = stages.map((stage) => {
      const status = statusByStage[stage]?.status || "pending";
      return `<button class="stage-button ${stage === activeStage ? "active" : ""}" data-stage="${escapeHtml(stage)}" type="button"><span>${escapeHtml(stage)}</span><span class="stage-status">${escapeHtml(status)}</span></button>`;
    }).join("");
  } catch (error) {
    setText("runLine", error.message);
    document.getElementById("stages").innerHTML = stages.map((stage) => `<button class="stage-button ${stage === activeStage ? "active" : ""}" data-stage="${escapeHtml(stage)}" type="button">${escapeHtml(stage)}</button>`).join("");
  }
}

async function loadStage() {
  try {
    const stage = await api(`/api/stage?stage=${encodeURIComponent(activeStage)}`);
    const result = stage.result;
    document.getElementById("stageMeta").innerHTML = [
      `stage: ${result.stage}`,
      `state: ${result.final_state}`,
      `attempts: ${result.attempt_count}`,
      `validator pass/fail: ${result.validator_pass_count}/${result.validator_fail_count}`
    ].map((item) => `<span>${escapeHtml(item)}</span>`).join("");
  } catch (error) {
    document.getElementById("stageMeta").textContent = error.message;
  }
}

async function loadQuestions() {
  const view = await api(`/api/questions?stage=${encodeURIComponent(activeStage)}`);
  if (!view.questions.length) {
    document.getElementById("content").textContent = "No questions";
    return;
  }
  document.getElementById("content").innerHTML = view.questions.map((question) => `
    <div class="question">
      <strong>${escapeHtml(question.question_id)} / ${escapeHtml(question.status)}</strong>
      <div>${escapeHtml(question.text)}</div>
      <textarea data-question="${escapeHtml(question.question_id)}" ${question.status === "resolved" ? "disabled" : ""}></textarea>
      <button class="answer" data-question="${escapeHtml(question.question_id)}" type="button">Answer</button>
    </div>
  `).join("");
}

async function loadLogs() {
  const view = await api(`/api/logs?stage=${encodeURIComponent(activeStage)}`);
  document.getElementById("content").innerHTML = `<pre>${escapeHtml(view.text)}</pre>`;
}

async function loadArtifacts() {
  const view = await api(`/api/artifacts?stage=${encodeURIComponent(activeStage)}`);
  const docs = Object.entries(view.documents).map(([key, value]) => `<li>${escapeHtml(key)}: ${escapeHtml(value)}</li>`).join("");
  const logs = Object.entries(view.logs).map(([key, value]) => `<li>${escapeHtml(key)}: ${escapeHtml(value)}</li>`).join("");
  document.getElementById("content").innerHTML = `<h2>Documents</h2><ul class="list">${docs}</ul><h2>Logs</h2><ul class="list">${logs}</ul>`;
}

function timeoutSummary(value) {
  return value === null || value === undefined ? "none" : `${value}s`;
}

function stageTimeoutSummary(stageTimeouts) {
  const entries = Object.entries(stageTimeouts || {});
  if (!entries.length) return "none";
  return entries.map(([stage, seconds]) => `${stage}: ${timeoutSummary(seconds)}`).join(", ");
}

async function loadReadiness(view = null) {
  view = view || await loadRuntimeChoices();
  const rows = view.runtimes.map((runtime) => `
    <tr>
      <td>${escapeHtml(runtime.runtime_id)}</td>
      <td>${escapeHtml(runtime.support_tier)}</td>
      <td>${escapeHtml(runtime.command_source)}</td>
      <td><code class="runtime-command">${escapeHtml(runtime.command)}</code></td>
      <td>${escapeHtml(runtime.execution_mode)}</td>
      <td>${escapeHtml(runtime.provider_available ? "available" : "unavailable")}</td>
      <td>${escapeHtml(runtime.provider_version || "unknown")}</td>
      <td>${escapeHtml(runtime.provider_command || "unknown")}</td>
      <td>${escapeHtml(runtime.execution_command_available ? "available" : "unavailable")}</td>
      <td>${escapeHtml(timeoutSummary(runtime.default_timeout_seconds))}</td>
      <td>${escapeHtml(stageTimeoutSummary(runtime.stage_timeout_seconds))}</td>
    </tr>
  `).join("");
  document.getElementById("content").innerHTML = `
    <div class="readiness-scroll">
      <table class="readiness-table">
        <thead>
          <tr>
            <th>Runtime</th>
            <th>Tier</th>
            <th>Source</th>
            <th>Command</th>
            <th>Mode</th>
            <th>Provider</th>
            <th>Version</th>
            <th>Probe</th>
            <th>Exec</th>
            <th>Timeout</th>
            <th>Stage timeouts</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

async function refresh() {
  let readinessView = null;
  await loadRun();
  try {
    readinessView = await loadRuntimeChoices();
  } catch (error) {
    document.getElementById("runtimeSelect").innerHTML = `<option value="">Runtime readiness unavailable</option>`;
    selectedRuntime = "";
    setRunButtonState();
  }
  try {
    if (activeTab === "readiness") {
      document.getElementById("stageMeta").innerHTML = `<span>${escapeHtml("runtime readiness")}</span>`;
      await loadReadiness(readinessView);
      return;
    }
    await loadStage();
    if (activeTab === "questions") await loadQuestions();
    if (activeTab === "logs") await loadLogs();
    if (activeTab === "artifacts") await loadArtifacts();
  } catch (error) {
    document.getElementById("content").textContent = error.message;
  }
}

document.addEventListener("click", async (event) => {
  const stage = event.target.closest("[data-stage]")?.dataset.stage;
  if (stage) {
    activeStage = stage;
    await refresh();
    return;
  }
  const tab = event.target.closest("[data-tab]")?.dataset.tab;
  if (tab) {
    activeTab = tab;
    document.querySelectorAll("[data-tab]").forEach((button) => button.classList.toggle("active", button.dataset.tab === tab));
    await refresh();
    return;
  }
  const answerButton = event.target.closest(".answer");
  if (answerButton) {
    const questionId = answerButton.dataset.question;
    const textarea = answerButton.closest(".question")?.querySelector("textarea");
    if (!questionId || !textarea) return;
    await api("/api/answers", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({stage: activeStage, question_id: questionId, text: textarea.value})
    });
    await refresh();
    return;
  }
  if (event.target.id === "runButton") {
    if (!selectedRuntime) return;
    await api("/api/workflow/run", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({runtime: selectedRuntime})
    });
    await refresh();
  }
});

document.addEventListener("change", (event) => {
  if (event.target.id === "runtimeSelect") {
    selectedRuntime = event.target.value;
    setRunButtonState();
  }
});

refresh();
"""


__all__ = ["_INDEX_HTML", "_OPERATOR_CSS", "_OPERATOR_JS"]
