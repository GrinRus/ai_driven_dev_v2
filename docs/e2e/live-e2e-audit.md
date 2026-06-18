# Live E2E Matrix Audit

This audit records the authored-task migration and size classification for the maintained
manual live matrix.

## Summary

The live matrix now uses authored task specs. This keeps the public repository and resolved
revision as real execution evidence, while the work item itself is controlled by the scenario
manifest with explicit acceptance criteria and verification intent.

## Size Classification

| Scenario | Size | Quality of existing execution evidence | Main risk | Authored task rewrite |
| --- | --- | --- | --- | --- |
| `AIDD-LIVE-001` | `small` | Weak: setup-blocked baseline remains non-canonical. | Pinned Typer setup fails before runtime boundary. | Keep as focused styled-help alignment bugfix with regression criteria. |
| `AIDD-LIVE-002` | `medium` | Unproven in latest local audit set. | Help rendering can drift across formatter behavior and tests. | Define explicit boolean help rendering acceptance criteria and non-regression expectations. |
| `AIDD-LIVE-003` | `small` | Historical reference failed before clean verification. | HTTPX full-suite setup can be sensitive to dependency state. | Make invalid-header diagnostic output and regression coverage explicit. |
| `AIDD-LIVE-004` | `tiny` | Recent Codex run reached QA but failed final full-suite target pytest on `test_write_timeout[trio]`; stage artifacts and tracked diff were docs-only. | Docs example quality and unrelated full-suite target instability. | Define docs-only CLI sync with no placeholder endpoints and docs-only counted verification. |
| `AIDD-LIVE-005` | `small` | Best current smoke lane; latest maintained budgets are long enough for native providers. | Multiple runtime targets increase provider-specific timing variance. | Keep header-only CSV crash fix as localized bug plus regression test. |
| `AIDD-LIVE-006` | `large` | Interview flow commonly blocks without prepared answers. | Trust-boundary decisions cannot be invented by the model. | Encode interview topics directly on the authored task and keep answer evidence mandatory. |
| `AIDD-LIVE-007` | `medium` | Historical verification failure in reference evidence. | Middleware error handling can affect runtime semantics beyond one test. | Define non-Error throw normalization with primitive/object regression coverage. |
| `AIDD-LIVE-008` | `xlarge` | Historical interview run blocked before answers. | Router compatibility is API-sensitive and requires explicit policy choice. | Treat as xlarge interview task with compatibility, docs, and router test obligations. |
| `AIDD-LIVE-010` | `large` | New candidate; no counted local run yet. | Codegen output compatibility depends on explicit discriminator policy. | Encode mapped/unmapped discriminator decisions as interview answers with focused Vitest and type checks. |
| `AIDD-LIVE-011` | `xlarge` | New candidate; no counted local run yet. | Pytest collection and terminal reporting semantics are compatibility-sensitive. | Treat as xlarge interview task with exit-code, maxfail, and summary-output policy answers. |
| `AIDD-LIVE-012` | `large` | New candidate; no counted local run yet. | ASGI streaming, disconnect, background-task, and middleware behavior can regress across async boundaries. | Keep the task bounded to focused Starlette response/middleware tests and ruff checks. |

## Matrix Quality Notes

- `AIDD-LIVE-004` is intentionally `tiny`; its expected output is documentation-only, so a
  broad implementation patch would be a quality smell. The historical 2026-05-25 Codex
  run reached `qa` and proved the stage flow, but final manifest verification failed in the
  upstream HTTPX full suite on `test_write_timeout[trio]` with a Trio async-generator
  `ResourceWarning`. That failure is outside the selected docs-only patch, so counted
  verification for this lane now checks tracked docs diff scope, concrete CLI example
  consistency, absence of placeholder runnable URLs, and QA artifact publication without
  calling the public endpoint. Full HTTPX pytest remains useful exploratory operator evidence,
  not the maintained clean-pass gate for this tiny scenario.
- `AIDD-LIVE-002` was re-audited locally on `2026-05-09` with Codex. The run reached
  `review-spec` repair but timed out at the 20-minute harness boundary before `tasklist`;
  this proved the medium Codex full-flow budget was too small for the installed operator
  lane. The Typer full-suite verification also failed on the pinned baseline with current
  dependencies, so this lane now uses a 90-minute budget and focused boolean/help-rendering
  verification in Rich/default and `TYPER_USE_RICH=0` modes. The authored task explicitly
  covers false-only boolean declarations so quality review does not leave leading separator
  behavior as a residual follow-up.
- `AIDD-LIVE-007` uses focused Hono runtime and compose tests with Vitest coverage
  disabled plus `tsc --noEmit` through the repository-local `node_modules/.bin`
  tools installed by scenario setup.
  The pinned Hono repository's broad `bun test` command currently exercises unrelated
  runner/runtime surfaces and fails outside the selected non-Error throw task, so it is not
  a maintained clean-run gate for this medium scenario. The focused Vitest command keeps
  coverage reports out of the target workspace because `coverage/` is manual quality
  evidence, not a required deliverable artifact.
- `AIDD-LIVE-008` is intentionally `xlarge`; router wildcard semantics are API-sensitive and
  should not be treated as an ordinary large feature.
- `AIDD-LIVE-010`, `AIDD-LIVE-011`, and `AIDD-LIVE-012` expand the maintained
  public-repository set for complex live exercises only. They are manual evidence lanes,
  not release gates, until at least one clean counted run is preserved for the selected
  runtime and manifest pin.
- Future live evidence refreshes should normally rotate across products and feature
  families before repeating the same manifest. Repeats are still useful for targeted
  blocker confirmation, runtime comparison, repin validation, or canonical smoke proof, but
  diverse products and feature shapes make the live E2E success analysis more meaningful.
- Interview scenarios must keep top-level `interview.required: true` plus authored task
  `interview` guidance so the manifest, bootstrap context, and quality review agree.
- `feature-selection.json` is the durable selection artifact.
- Scenario setup commands run under a non-interactive harness environment. Package managers
  and Corepack must not wait for hidden terminal prompts during live evidence collection.

## Flow Improvements Tracked By This Audit

- Bootstrap context now writes `selected-task.md`, `acceptance-criteria.md`,
  `allowed-write-scope.md`, and command-specific `verification-output.md` from authored task
  fields.
- Manual `quality-report.md` review records repair burden, suspiciously small patches for
  larger tasks, placeholder documentation examples, and target workspace hygiene; the live
  runner does not turn these signals into an automatic quality gate.
- Stage briefs now include exact skeleton hints for primary stage documents plus
  richer `stage-result.md` and `validator-report.md` skeletons to reduce first-pass
  contract churn.
- Native runtime prompts now make turn completion explicit after the final required
  document write so providers that have already produced valid Markdown artifacts do not
  keep the adapter call open until a stage timeout.
- OpenCode and Qwen native runs can now finish with `document_complete` when required stage
  documents settle but the provider process does not return a final message; canonical
  validation still decides whether the stage blocks, repairs, or advances.
- The OpenCode completion rule treats a settled blocking-question bundle as terminal even
  when `answers.md` remains the unanswered placeholder; canonical validation and the
  black-box flow decide whether operator answers are still required.
- Idea semantic validation still rejects absolute success claims, but allows negated
  security-guarantee caveats such as "without implying a broader guarantee" because those
  phrases document risk rather than overclaiming certainty.
- Interview validation now treats malformed `questions.md` structure plus unresolved blocking
  questions as a repairable document failure, not a clean wait state for prepared answers.
  The `idea` prompt also forbids nested question bullets, which previously produced malformed
  interview documents in live runs.
