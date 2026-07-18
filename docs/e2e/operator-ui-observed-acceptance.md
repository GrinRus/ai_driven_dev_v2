# Observed First-Time-Operator Acceptance

This script is the human-observation lane for Document & Evidence Studio. Automated browser
journeys are prerequisite evidence, not substitutes for participants. A participant must not
have implemented, reviewed, or previously operated this UI.

## Session Setup

- Use a source-installed build at one recorded commit and a disposable provider-free fixture.
- Record only an anonymized participant id, session date, AIDD version/commit, browser/version,
  viewport, and fixture family.
- Do not record names, credentials, local project paths, runtime logs, prompts, generated
  documents, or `.aidd/` contents.
- Ask the participant to think aloud. The facilitator may restate the task but must record any
  hint, navigation instruction, or product explanation as assistance.
- Start each task at its declared entry surface with browser zoom at 100%. Do not point at the
  primary action or explain UI vocabulary before the participant acts.
- Stop a task on durable completion, participant abandonment, unsafe attempted action, or the
  task-specific time box. Reset only through the prepared fixture, never by editing evidence.

## Task Script

For every task, record completion, elapsed time, wrong actions, assistance, confidence `1-5`,
and the first decisive confusion. A wrong action is a deliberate action that moves away from the
stated outcome, invokes an ineligible path, or requires Back/recovery; reading or inspecting
supporting evidence is not inherently wrong.

### O1 — Guided Setup and first launch

- Entry: a valid local project with no selected work item.
- Prompt: “Create a new work item for the supplied request and start the governed flow with the
  available local runtime.”
- Durable outcome: the work item exists and the participant reaches its Inbox/Studio context
  after one launch request.
- Time box: 8 minutes.

### O2 — Inbox triage

- Entry: Inbox with one blocking decision, one ready continuation, one running overlay, and one
  completed flow.
- Prompt: “Find the item that needs you now and open the exact place where you can act.”
- Durable outcome: the highest-priority server-approved item opens in its exact Studio context;
  no unrelated mutation occurs.
- Time box: 4 minutes.

### O3 — Active Studio monitoring

- Entry: an executing stage with live output followed by a reconnect interval.
- Prompt: “Tell me what is running, inspect its latest output, and keep monitoring until durable
  state returns.”
- Durable outcome: the participant identifies stage/status, opens live output, survives
  reconnect without declaring a false failure, and returns to live state.
- Time box: 6 minutes.

### O4 — Blocking question recovery

- Entry: a stage blocked by one required question and one previously saved partial draft.
- Prompt: “Resolve what is blocking this stage and resume it without losing the saved input.”
- Durable outcome: a resolved answer is durably submitted once and the same run/stage resumes.
- Time box: 6 minutes.

### O5 — Runtime and validation recovery

- Entry: one runtime failure followed by an eligible validation repair and an exhausted repair
  state.
- Prompt: “Find the first failure and its evidence, take the safe available recovery action, then
  handle the state where automated repair is no longer available.”
- Durable outcome: runtime logs are inspected, eligible repair is invoked at most once, and
  exhausted recovery opens the stage-scoped Request Change path rather than another repair.
- Time box: 8 minutes.

### O6 — Review/QA remediation

- Entry: Review/QA evidence with a must-fix finding and stale downstream evidence after
  remediation.
- Prompt: “Decide why this flow cannot proceed, send the required issue back, and identify what
  must be rerun before completion is trustworthy.”
- Durable outcome: the exact finding is remediated through the guarded endpoint and the
  participant identifies stale Review/QA plus the required rerun; no terminal progression occurs.
- Time box: 7 minutes.

### O7 — History inspection

- Entry: a run with stage/task/finalization frames, retained comparison evidence, lineage, and an
  archive overlay.
- Prompt: “Find an earlier attempt, compare it with the current evidence, inspect its lineage,
  and return to live state.”
- Durable outcome: the participant selects the retained frame, distinguishes unavailable
  evidence, opens a parent/child relation, and returns to live without mutating either run.
- Time box: 7 minutes.

### O8 — Terminal continuation

- Entry: fresh terminal QA with a core recommendation plus follow-up, clone, eval, and archive
  alternatives.
- Prompt: “Explain the recommended next step, prepare the appropriate continuation, and show me
  where the other outcomes live.”
- Durable outcome: the participant finds the recommendation, prepares one guarded continuation
  or manual handoff, and confirms the completed source run remains available and unchanged.
- Time box: 8 minutes.

## Per-Task Scoring Template

Copy this block once for each `O1..O8` task:

```text
Task id: <O1..O8>
Completion: <completed | not-completed | stopped-for-safety>
Elapsed time: <mm:ss>
Wrong actions: <count>
First wrong action: <action or none>
Assistance: <none | facilitator restatement | navigation hint | product explanation | safety stop>
Operator confidence: <1-5>
First decisive confusion: <verbatim short observation or none>
Durable outcome observed: <non-sensitive outcome or none>
Finding id: <OBS-<session>-<task>-<number> or none>
Facilitator notes: <bounded non-sensitive notes>
```

Confidence means: `1` cannot explain the state or next step; `2` guesses with substantial doubt;
`3` completes but remains unsure; `4` completes and can explain the consequence; `5` completes,
explains the consequence, and can identify the authoritative evidence.

## Session Summary Template

```text
Session id: <anonymous S1..S5>
Date: <YYYY-MM-DD>
AIDD version / source commit: <version / sha>
Browser / version: <browser / version>
Viewport: <width x height>
Fixture family: <non-sensitive fixture id>
Participant eligibility: <first-time operator confirmed>
Tasks completed: <count / 8>
Median confidence: <1-5>
Total wrong actions: <count>
Assisted tasks: <task ids or none>
First decisive confusion: <earliest task/id and observation or none>
Safety stops or blockers: <none or structured summary>
Finding ids: <ordered OBS ids or none>
Sensitive-data review: <passed | failed>
```

The report across five sessions must preserve every task row, including failures and safety
stops. It must not average away a decisive confusion. This template does not declare beta UX
ready: `W36-E7-S3-T3` must close, defer with rationale, or map every `OBS-*` finding to a
reviewable roadmap task before readiness is claimed.
