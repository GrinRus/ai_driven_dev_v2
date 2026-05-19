# Live Quality Rubric

This rubric defines the second live-E2E decision layer that sits next to the execution verdict.

Execution verdict answers:

> Did the installed live run complete, verify, and preserve the required evidence?

Quality gate answers:

> Is the resulting flow, artifact set, and generated code strong enough to treat the run as clean?

## Canonical outputs

Every live eval bundle should write:

- `quality-report.md`
- `quality-transcript.json`
- a `quality` section in `grader.json`
- `stage-audits/<stage>.json` and `.md` so the final quality report can cite
  stage-local state, validator verdict, repair/interview behavior, runtime log
  visibility, and implement evidence shape

The default durable bundle root for these artifacts is `.aidd/reports/evals/<run_id>/`.

## Manual operator overlay

The machine quality gate is the minimum clean-pass requirement. For manual live
E2E, the launching agent is also the operator-agent and must write
`operator-quality-analysis.md` before counting a terminal run.

The operator audit can only downgrade the counted/not-counted decision. It cannot
upgrade a machine `fail` or `warn` quality gate to a counted clean pass.

For counted manual clean passes, `operator-quality-analysis.md` records:

- runtime, manifest, run id, and bundle path;
- execution verdict, quality gate, QA verdict, and review status;
- flow fidelity, artifact quality, and code quality assessment;
- final decision: `counted-clean`, `not-counted`, or
  `blocked/infra/provider/model-quality`;
- explicit blockers, or `none`.

## Dimensions

Each dimension uses a fixed integer score from `0` to `3`.

### `flow_fidelity`

What it measures:

- the run stayed inside the installed live contract;
- the selected authored task was recorded;
- workflow bounds stayed `idea -> qa`;
- question, repair, and verification behavior remained truthful;
- the run did not silently skip required stages or artifacts.
- `stage-audits/<stage>.json` exists for every reached stage and agrees with
  final `flow-state.json`.

Interpretation:

- `0` — contract break or no-op path
- `1` — major drift or incomplete full-flow evidence
- `2` — acceptable full-flow evidence with minor caveats
- `3` — strong full-flow evidence with no material drift

### `artifact_quality`

What it measures:

- stage outputs validate against contracts;
- review and QA documents are evidence-backed;
- cross-stage consistency is preserved;
- required findings, risks, and recommendations are explicit and usable.
- repair burden is bounded and does not show repeated first-pass contract misses.

Interpretation:

- `0` — invalid or unsupported artifacts
- `1` — weak or incomplete but partially usable artifacts
- `2` — solid artifacts with bounded weaknesses
- `3` — strong, review-ready artifact set

### `code_quality`

What it measures:

- repo-local quality commands passed;
- verification is adequate for the selected authored task;
- unresolved `must-fix` review findings are absent;
- QA did not conclude `not-ready`;
- the resulting change remains bounded and reviewable.
- implementation size is plausible for the authored task's declared scope.
- implement-stage audit records changed files, diff summary, and whether
  implementation-report verification claims are backed by executable/check
  evidence or explicit `not-run:` reasons.
- documentation examples avoid placeholder or non-runnable endpoints presented as runnable.
- optional broader checks outside the authored task's verification boundary do not become
  release conditions unless they expose a concrete defect or contradict acceptance criteria.

Interpretation:

- `0` — quality gate failure or clearly unsafe code result
- `1` — technically working but materially weak code result
- `2` — acceptable code result with bounded risks
- `3` — strong code result with clean evidence

## Gate mapping

- `quality_gate = fail` when any quality command fails, any dimension score is `0`, review leaves unresolved `must-fix` findings, or QA verdict is `not-ready`.
- `quality_gate = warn` when execution passed but review is `approved-with-conditions`, QA is `ready-with-risks`, or any dimension score is `1`.
- `quality_gate = pass` only when all dimensions are `2` or higher, review is `approved`, QA is `ready` or `ready-with-risks`, and all quality commands pass.

## Quality verdict

The quality layer records:

- `ready`
- `ready-with-risks`
- `not-ready`

This verdict comes from the generated QA evidence and does not replace the execution verdict in `verdict.md`.

## Follow-up policy

Quality reporting may include suggested backlog follow-ups, but it must not update `docs/backlog/roadmap.md` or `docs/backlog/backlog.md` automatically during a live run.
