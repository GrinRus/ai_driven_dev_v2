// Design-only fixture. Never import this state machine into the production frontend.
const workspace = document.querySelector('#workspace');
const dialog = document.querySelector('#inspector');
const content = document.querySelector('#inspector-content');
const title = document.querySelector('#inspector-title');
const scenario = document.querySelector('#scenario');
let state = { scenario: 'decision', phase: 'question', nav: 'studio', tab: 'Overview', choice: null };
const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const tag = (label, kind = 'neutral') => `<span class="tag ${kind}">${label}</span>`;
const source = 'Add password reset by email. Tokens expire after 15 minutes. Do not reveal whether an email address has an account. Keep changes inside the auth service.';
const currentSource = () => state.scenario === 'stale' ? source.replace('15 minutes', '10 minutes') : source;
const sourceRevision = () => state.scenario === 'stale' ? 'request-r2' : 'request-r1';
const freshResult = () => ['review','assessed'].includes(state.phase);
const iteration = () => ['running','review','assessed','change'].includes(state.phase) ? 2 : 1;
const evidenceIteration = () => ['review','assessed','change'].includes(state.phase) ? 2 : 1;
const criterionText = (id, revision = sourceRevision()) => id === 'C2' ? 'The response does not disclose account existence.' : id === 'C3' ? (state.choice === 'Keep existing sessions' ? 'Existing sessions remain active after password reset.' : 'Existing sessions are revoked after password reset.') : `Reset tokens expire after ${revision === 'request-r2' ? '10' : '15'} minutes.`;
const decisionLabel = () => state.scenario === 'decision' ? 'Scoped demo decision D-3' : 'Preloaded fixture decision D-3';
const announce = (text) => { document.querySelector('#announcement').textContent = text; };

function openInspector(heading, markup) {
  title.textContent = heading;
  content.innerHTML = markup;
  dialog.showModal();
}
document.querySelector('#close-inspector').addEventListener('click', () => dialog.close());

function sourceInspector() {
  openInspector('Original request', `<p class="caption">Synthetic operator-authored original · request-r1 · retained read-only</p>
    <blockquote>${source}</blockquote>${state.scenario === 'stale' ? `<h3>Current revision · request-r2</h3><blockquote>${currentSource()}</blockquote><p class="notice">Original r1: 15 minutes → current r2: 10 minutes. Both sources are retained; the old receipt still checks r1.</p>` : ''}
    <h3>Constraints</h3><p>Auth service only. Preserve account privacy. Expiry is explicit; session revocation is unspecified.</p>
    <h3>Identity</h3><code>Northstar API / WI-104 / context/user-request.md#brief</code><p class="caption">Original fixture digest: request-r1 · current digest: ${sourceRevision()}</p>`);
}

function evidenceInspector(id = 'C1', historical = false) {
  const receiptRun = historical ? 1 : evidenceIteration();
  const failed = state.scenario === 'failed' && receiptRun === 1;
  const stale = state.scenario === 'stale' && receiptRun === 1;
  const pending = id === 'C3' && receiptRun === 1;
  const receiptId = `R-${receiptRun}-${id}`;
  const receiptSource = receiptRun === 1 ? 'request-r1' : sourceRevision();
  const diff = id === 'C3' ? (state.choice === 'Keep existing sessions' ? '+ preserve active sessions after password reset' : '+ revoke active sessions after password reset') : id === 'C2' ? '+ return the same response for unknown email' : `+ reject reset tokens older than ${receiptRun === 1 ? '15' : state.scenario === 'stale' ? '10' : '15'} minutes`;
  const receipt = pending ? 'NOT RUN for the new product decision' : !historical && state.phase === 'change' ? 'STALE · change request requires renewed proof' : id === 'C1' && failed ? 'FAILED · exit 1 · expired token was accepted' : id === 'C1' && stale ? 'STALE · exit 0 on request-r1; current request-r2 requires 10 minutes' : 'PASSED · exit 0 · retained fixture output';
  openInspector(`${id} · Evidence chain`, `<p class="caption">All records below are synthetic. They demonstrate provenance, not executed verification.</p>
    <h3>1 · Checked source and authority</h3><blockquote>${id === 'C3' ? 'Original request does not specify what happens to existing sessions.' : id === 'C2' ? '“Do not reveal whether an email address has an account.”' : `“Tokens expire after ${receiptSource === 'request-r2' ? '10' : '15'} minutes.”`}</blockquote>
    <p>${id === 'C3' ? (state.choice ? decisionLabel() + ': ' + escapeHtml(state.choice) : 'Proposed behavior · decision required') : 'Source-backed criterion'} · <code>${receiptSource}</code></p>
    ${id === 'C1' && stale ? '<p class="notice">Checked r1: 15 minutes → current r2: 10 minutes. This retained receipt does not verify the current criterion.</p>' : ''}
    <h3>2 · Checked criterion and task</h3><p>${id}: ${criterionText(id, receiptSource)}</p><code>${id === 'C3' ? 'TL-2' : 'TL-1'} → src/auth/reset.py · plan revision ${receiptRun}</code>
    <h3>3 · Changed behavior</h3><pre>${pending ? 'No implementation evidence for this criterion yet.' : diff}</pre>
    <h3>4 · Registered check receipt</h3><code>pytest tests/auth/test_reset.py -q</code><p class="notice">${receipt}</p>
    <p class="caption">${pending ? 'No receipt exists for this criterion yet.' : `Fixture receipt ${receiptId} · run-${receiptRun} / ${id === 'C3' ? 'TL-2' : 'TL-1'} / attempt-1 · auth-tree-r${receiptRun}<br>Captured 2026-10-01 10:42 · checked source: ${receiptSource} · scope: auth service`}</p>
    <h3>5 · Behavioral assessment</h3><p>${!historical && state.phase === 'assessed' ? 'Confirmed in simulated review A-1; terminal QA and handoff are still pending.' : 'Unassessed. A command result alone does not establish all intended behavior.'}</p>
    <h3>Raw record</h3><pre>Fixture only\ncheck: ${id === 'C1' ? 'reset-expiry' : id === 'C2' ? 'account-privacy' : 'session-policy'}\nsource: ${receiptSource}\ncriterion: ${id}\nreport: ${pending ? 'unavailable' : `receipts/${receiptId}.md`}</pre>`);
}

function decisionInspector() {
  openInspector('What happens to existing sessions?', `<p class="caption">Product decision D-3 · affects C3 · scope: auth service</p>
    <blockquote>The request specifies token expiry and privacy. It does not say whether a password reset signs the user out elsewhere.</blockquote>
    <p>Choose the intended behavior. This adds a scoped criterion; it does not approve the whole generated plan.</p>
    <form id="decision-form"><label class="choice"><input type="radio" name="session-policy" value="Revoke existing sessions" required><div><strong>Revoke existing sessions</strong><span>A reset signs the user out on other devices. Adds a session invalidation check.</span></div></label>
    <label class="choice"><input type="radio" name="session-policy" value="Keep existing sessions" required><div><strong>Keep existing sessions</strong><span>Existing sessions remain active. Adds a regression check for retained sessions.</span></div></label>
    <p class="notice">Saving records the simulated answer. Execution stays paused until you explicitly run the next iteration.</p>
    <div class="actions"><button class="primary" type="submit">Save answer · demo</button></div></form>`);
  document.querySelector('#decision-form').addEventListener('submit', (event) => {
    event.preventDefault();
    state.choice = new FormData(event.currentTarget).get('session-policy');
    state.phase = 'saved';
    state.nav = 'studio'; state.tab = 'Overview';
    dialog.close();
    render();
    document.querySelector('[data-action="primary"]').focus();
    announce('Demo answer saved. Execution is still paused. Run the next iteration explicitly.');
  });
}

function reviewInspector() {
  openInspector('Review the intended behavior', `<p class="caption">Fixture review · current iteration 2 · source ${sourceRevision()}</p>
    <p>All three fixture check receipts pass. Behavioral acceptance is still a separate decision.</p>
    <h3>What to assess</h3><p>Try an expired token, compare responses for known and unknown emails, and confirm the selected session policy: ${escapeHtml(state.choice || 'source-backed behavior only')}.</p>
    <h3>Independent expectation</h3><p>Original request and scoped decision D-3, rather than the generated plan, are the assessment reference.</p>
    <div class="actions"><button class="primary" data-review="accept">Record confirmed assessment · demo</button><button data-review="change">Request change · demo</button></div>
    <p class="caption">This records a fictional assessment in the concept. No real software or operator evidence is assessed.</p>`);
  content.querySelectorAll('[data-review]').forEach((button) => button.addEventListener('click', () => {
    state.phase = button.dataset.review === 'accept' ? 'assessed' : 'change';
    dialog.close(); render(); document.querySelector('h1').focus();
    announce(state.phase === 'assessed' ? 'Simulated behavior assessment recorded. Terminal QA and handoff remain pending.' : 'Simulated change request created. Previous proof is retained and stale for the next iteration.');
  }));
}

function nextAction() {
  if (state.phase === 'saved') return ['Answer saved · still paused', `C3 now records “${state.choice}”. Plan revision 2 will add the corresponding task and check. Earlier evidence is retained.`, 'Run next iteration · demo', 'ready'];
  if (state.phase === 'prepared') return ['Recovery plan ready · still paused', 'Plan revision 2 targets the affected expiry behavior and renews its checks. The failed or stale run-1 receipt is retained; no new result exists yet.', 'Run planned iteration · demo', 'ready'];
  if (state.phase === 'running') return ['Iteration 2 · execution preview', 'This is a simulated running state. Earlier evidence is still retained. Load the separate fixture result to inspect new receipts; no runtime executes here.', 'Load fixture check result', 'ready'];
  if (state.phase === 'review') return ['Checks passed · behavior needs review', 'Iteration 2 has three passing fixture receipts. Assess them against the request and your scoped decision before accepting the result.', 'Review result', 'ready'];
  if (state.phase === 'assessed') return ['Assessment recorded · terminal gates pending', 'A simulated assessment is linked to current receipts. Final QA and the immutable handoff are not modeled here. The Work Item is not Complete.', 'Inspect result', 'ready'];
  if (state.phase === 'change') return ['Change requested · proof needs renewal', 'A new child iteration will retain the earlier result, revise the plan, and rerun affected checks. No previous receipt is counted as fresh.', 'Inspect change request', ''];
  if (state.scenario === 'failed') return ['Expiry check failed', 'An expired token was accepted. Open the retained receipt and changed code, then prepare a bounded repair and rerun its checks.', 'Prepare repair · demo', 'failed'];
  if (state.scenario === 'stale') return ['Proof belongs to an earlier request', 'The source now requires a 10-minute expiry. The passing receipt checks 15 minutes. Reconcile the change and renew the affected proof.', 'Prepare replan · demo', ''];
  return ['One product decision needs you', 'The request does not specify whether password reset revokes existing sessions. Resolve that behavior before the next increment.', 'Answer product question', ''];
}

function overview() {
  const [heading, reason, action, kind] = nextAction();
  const isFresh = freshResult();
  const changed = state.phase === 'change';
  const failing = state.scenario === 'failed' && evidenceIteration() === 1;
  const stale = (state.scenario === 'stale' && evidenceIteration() === 1) || changed;
  const c1 = stale ? ['Stale proof','warning'] : failing ? ['Check failed','failed'] : ['Check passed','passed'];
  const c3 = changed ? ['Stale proof','warning'] : isFresh ? ['Check passed','passed'] : state.choice ? ['Not checked','neutral'] : ['Decision needed','warning'];
  const coverage = isFresh ? '3 checked · behavior ' + (state.phase === 'assessed' ? 'confirmed in demo' : 'unassessed') : stale ? 'Affected proof is stale' : failing ? '1 failed · 1 passed · 1 not checked' : state.choice ? '2 checked · 1 not checked' : '2 checked · 1 decision needed';
  return `<section class="panel next ${kind}" aria-label="Next action"><div><span class="eyebrow">Next action</span><h2>${heading}</h2><p>${escapeHtml(reason)}</p></div>
    <div class="actions"><button class="primary" data-action="primary">${action}</button><button data-action="evidence">View evidence</button></div></section>
    <div class="coverage"><section class="panel"><div class="section-head"><div><h2>Requested behavior</h2><p>${coverage}</p></div></div>
      <article class="criterion"><header><h3>C1 · Reset tokens expire after ${state.scenario === 'stale' ? '10' : '15'} minutes</h3>${tag(...c1)}</header><p>Source-backed · request-r${state.scenario === 'stale' ? '2' : '1'} · TL-1</p><button data-evidence="C1">Inspect source → change → check</button></article>
      <article class="criterion"><header><h3>C2 · Keep account existence private</h3>${tag(stale ? 'Retained proof' : 'Check passed',stale ? 'neutral' : 'passed')}</header><p>Source-backed · request-r1 · TL-1</p><button data-evidence="C2">Inspect source → change → check</button></article>
      <article class="criterion"><header><h3>C3 · ${escapeHtml(state.choice || 'Existing sessions after reset')}</h3>${tag(...c3)}</header><p>${state.choice ? `${decisionLabel()} · ${isFresh ? 'current receipt available' : changed ? 'proof requires renewal' : 'new check required'}` : 'Proposed behavior · not specified in the request'}</p><button ${state.choice ? 'data-evidence="C3"' : 'data-action="decision"'}>${state.choice ? 'Inspect decision → plan → check' : 'Inspect and decide this behavior'}</button></article>
    </section><section class="panel"><div class="section-head"><div><h2>Changes & proof</h2><p>Auth service · iteration ${evidenceIteration()} · fixture data</p></div>${tag('2 paths','neutral')}</div>
      <p>Password reset adds expiry enforcement and a uniform response for known and unknown addresses.</p>
      <code class="path">src/auth/reset.py</code><code class="path">tests/auth/test_reset.py</code>
      <div class="check"><header>${tag(...c1)}<strong>Reset behavior checks</strong></header><code>pytest tests/auth/test_reset.py -q</code><p class="caption">${stale ? `Receipt R-${evidenceIteration()}-C1 is retained; affected proof requires renewal.` : failing ? 'Receipt R-1-C1 · exit 1 · expired token accepted.' : `Receipt R-${evidenceIteration()}-C1 · exit 0 · auth-tree-r${evidenceIteration()}.`}</p><button class="text-button" data-action="evidence">Open receipt and changed code</button></div>
      <div class="assessment"><h3>Behavioral assessment</h3><p class="caption">${state.phase === 'assessed' ? 'Confirmed in simulated review A-1. Terminal gates pending; synthetic evidence only.' : 'Not assessed. Passing checks do not automatically accept the intended behavior.'}</p></div>
    </section></div>`;
}

function otherTab() {
  if (state.tab === 'Tasks') return `<div class="list"><article class="panel"><span class="eyebrow">TL-1 · ${state.scenario === 'failed' && !freshResult() ? 'check failed' : state.scenario === 'stale' && !freshResult() ? 'proof stale' : 'implementation retained'}</span><h3>Password reset and privacy</h3><p>Criteria C1, C2 · two changed paths · retained fixture receipts.</p><button class="text-button" data-action="evidence">Inspect task evidence</button></article><article class="panel"><span class="eyebrow">TL-2 · ${freshResult() ? 'checked in iteration 2' : state.choice ? 'planned from D-3' : 'blocked by product ambiguity'}</span><h3>Session behavior</h3><p>${state.choice ? escapeHtml(state.choice) : 'Choose intended behavior before this task can run.'}</p><button class="text-button" ${state.choice ? 'data-evidence="C3"' : 'data-action="decision"'}>${state.choice ? 'Inspect decision and check' : 'Answer the blocking question'}</button></article></div>`;
  if (state.tab === 'Documents') return `<div class="list"><article class="panel"><h3>Original request</h3><p>Operator-authored · protected · ${sourceRevision()}</p><button class="text-button" data-action="source">Read source</button></article><article class="panel"><h3>Plan and verification records</h3><p>Generated plan is read-only. Claims and owned receipts have separate authority.</p><button class="text-button" data-action="evidence">Open linked records</button></article></div>`;
  return history();
}

function history() {
  return `<section class="panel list" aria-label="Run lineage"><h2>How the work changed</h2>
    ${state.choice ? `<article class="history-item"><span class="eyebrow">${decisionLabel()}</span><h3>${escapeHtml(state.choice)}</h3><p>Added C3 and a planned session behavior check. ${state.scenario !== 'decision' ? 'Preloaded by the selected fixture, not answered by this operator. ' : ''}${iteration() === 1 ? 'Next execution has not started.' : 'Linked to the simulated child iteration.'}</p></article>` : ''}
    ${['running','review','assessed','change'].includes(state.phase) ? `<article class="history-item"><span class="eyebrow">run-2 · child of run-1</span><h3>Iteration 2 · plan revision 2</h3><p>${state.phase === 'running' ? 'Execution preview; no new receipts yet.' : 'Previous artifacts retained. New check receipts R-2-C1/C2/C3 and assessment remain separate.'}</p></article>` : ''}
    <article class="history-item"><span class="eyebrow">run-1 · request-r1</span><h3>Iteration 1 · reset and privacy</h3><p>${state.scenario === 'failed' ? 'Receipt R-1-C1 failed: expired token accepted. The failure remains retained.' : state.scenario === 'stale' ? 'Receipt R-1-C1 passed for 15 minutes. It does not prove the revised 10-minute criterion.' : 'TL-1 changed the auth service. Two fixture behavior checks were retained.'}</p><button class="text-button" data-action="historical-evidence">Inspect original evidence</button></article>
    ${state.scenario === 'stale' ? '<article class="history-item"><span class="eyebrow">request-r2 · retained source revision</span><h3>Expiry changed: 15 → 10 minutes</h3><p>Existing r1 receipts remain retained and stale for the changed criterion.</p></article>' : ''}
    <article class="history-item"><span class="eyebrow">WI-104 · original request</span><h3>Add password reset by email</h3><button class="text-button" data-action="source">Read the source request</button></article></section>`;
}

function render() {
  document.querySelectorAll('[data-nav]').forEach((button) => { if (button.dataset.nav === state.nav) button.setAttribute('aria-current','page'); else button.removeAttribute('aria-current'); });
  if (state.nav === 'inbox') {
    const [heading] = nextAction();
    workspace.innerHTML = `<span class="eyebrow">Northstar API · local project</span><div class="heading"><div><h1 tabindex="-1">Project inbox</h1><p>Choose the work that needs your attention.</p></div></div><section class="panel list"><span class="eyebrow">${state.phase === 'assessed' ? 'Ready · terminal gates pending' : state.phase === 'running' ? 'Running · simulated' : 'Needs input'} · 1 Work Item</span><h2>Add password reset by email</h2><p>WI-104 · ${heading}</p><div class="actions"><button class="primary" data-action="open">Open Work Item</button></div></section>`;
  } else if (state.nav === 'history') {
    workspace.innerHTML = `<span class="eyebrow">WI-104 · source and iteration history</span><div class="heading"><h1 tabindex="-1">History</h1><button data-action="open">Return to Studio</button></div>${history()}`;
  } else {
    workspace.innerHTML = `<span class="eyebrow">Northstar API / WI-104</span><div class="heading"><div><h1 tabindex="-1">Add password reset by email</h1><p>Reset access safely, keep account existence private, and limit changes to the auth service.</p></div><button class="source-button" data-action="source">Original request ↗</button></div>
      <div class="meta"><span>Iteration ${iteration()}</span><span>Scope: auth service</span><span>Runner: fixture</span><span>Profile: iterative concept</span></div>
      <div class="tabs" role="tablist" aria-label="Work Item sections">${['Overview','Tasks','Documents','Runs'].map((tab) => `<button role="tab" id="tab-${tab}" aria-controls="tab-panel" aria-selected="${state.tab === tab}" tabindex="${state.tab === tab ? '0' : '-1'}" data-tab="${tab}">${tab}</button>`).join('')}</div>
      <div id="tab-panel" role="tabpanel" aria-labelledby="tab-${state.tab}" tabindex="0">${state.tab === 'Overview' ? overview() : otherTab()}</div>`;
  }
  workspace.querySelectorAll('[data-tab]').forEach((button) => {
    button.addEventListener('click', () => { state.tab = button.dataset.tab; render(); document.querySelector(`[data-tab="${state.tab}"]`).focus(); });
    button.addEventListener('keydown', (event) => {
      const tabs = ['Overview','Tasks','Documents','Runs'];
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
      event.preventDefault();
      state.tab = event.key === 'Home' ? tabs[0] : event.key === 'End' ? tabs[3] : tabs[(tabs.indexOf(state.tab) + (event.key === 'ArrowRight' ? 1 : 3)) % 4];
      render(); document.querySelector(`[data-tab="${state.tab}"]`).focus();
    });
  });
  workspace.querySelectorAll('[data-evidence]').forEach((button) => button.addEventListener('click', () => evidenceInspector(button.dataset.evidence)));
  workspace.querySelectorAll('[data-action]').forEach((button) => button.addEventListener('click', () => {
    const action = button.dataset.action;
    if (action === 'source') return sourceInspector();
    if (action === 'evidence') return evidenceInspector();
    if (action === 'historical-evidence') return evidenceInspector('C1', true);
    if (action === 'decision') return decisionInspector();
    if (action === 'open') { state.nav = 'studio'; state.tab = 'Overview'; render(); return; }
    if (state.phase === 'assessed') return evidenceInspector();
    if (state.phase === 'change') return openInspector('Change request · next iteration', '<p>A scoped change request would create a new child run, revise the plan, and renew affected checks. Earlier evidence remains inspectable.</p><p class="notice">Further iterations are outside this bounded concept. No fresh result is claimed.</p>');
    if (state.phase === 'review') return reviewInspector();
    if (state.phase === 'question' && state.scenario === 'decision') return decisionInspector();
    state.phase = state.phase === 'question' ? 'prepared' : state.phase === 'running' ? 'review' : 'running';
    render(); document.querySelector('[data-action="primary"]').focus();
    announce(state.phase === 'review' ? 'Separate fixture receipts for run-2 loaded. Earlier evidence remains retained; assessment is pending.' : 'Simulation advanced. No new verification result is claimed yet.');
  }));
}
document.querySelectorAll('[data-nav]').forEach((button) => button.addEventListener('click', () => { state.nav = button.dataset.nav; render(); document.querySelector('h1').focus(); }));
scenario.addEventListener('change', () => { state = { scenario: scenario.value, phase: 'question', nav: 'studio', tab: 'Overview', choice: scenario.value === 'decision' ? null : 'Revoke existing sessions' }; render(); announce('Design fixture changed. Previous demo actions have been reset.'); });
render();
