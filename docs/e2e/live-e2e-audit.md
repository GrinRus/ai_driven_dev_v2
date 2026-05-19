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
| `AIDD-LIVE-004` | `tiny` | Recent Codex run reached QA but failed target pytest; artifacts narrowed to docs-only. | Docs example quality and full-suite target instability. | Define docs-only CLI sync with no placeholder endpoints and requirements-based pytest. |
| `AIDD-LIVE-005` | `small` | Best current smoke lane; latest maintained budgets are long enough for native providers. | Multiple runtime targets increase provider-specific timing variance. | Keep header-only CSV crash fix as localized bug plus regression test. |
| `AIDD-LIVE-006` | `large` | Interview flow commonly blocks without prepared answers. | Trust-boundary decisions cannot be invented by the model. | Encode interview topics directly on the authored task and keep answer evidence mandatory. |
| `AIDD-LIVE-007` | `medium` | Historical verification failure in reference evidence. | Middleware error handling can affect runtime semantics beyond one test. | Define non-Error throw normalization with primitive/object regression coverage. |
| `AIDD-LIVE-008` | `xlarge` | Historical interview run blocked before answers. | Router compatibility is API-sensitive and requires explicit policy choice. | Treat as xlarge interview task with compatibility, docs, and router test obligations. |

## Matrix Quality Notes

- `AIDD-LIVE-004` is intentionally `tiny`; its expected output is documentation-only, so a
  broad implementation patch would be a quality smell.
- `AIDD-LIVE-002` was re-audited locally on `2026-05-09` with Codex. The run reached
  `review-spec` repair but timed out at the 20-minute harness boundary before `tasklist`;
  this proved the medium Codex full-flow budget was too small for the installed operator
  lane. The Typer full-suite verification also failed on the pinned baseline with current
  dependencies, so this lane now uses a 90-minute budget and focused boolean/help-rendering
  verification in Rich/default and `TYPER_USE_RICH=0` modes. The authored task explicitly
  covers false-only boolean declarations so quality review does not leave leading separator
  behavior as a residual follow-up.
- `AIDD-LIVE-008` is intentionally `xlarge`; router wildcard semantics are API-sensitive and
  should not be treated as an ordinary large feature.
- Interview scenarios must keep top-level `interview.required: true` plus authored task
  `interview` guidance so the manifest, bootstrap context, and quality review agree.
- `feature-selection.json` is the durable selection artifact.

## Flow Improvements Tracked By This Audit

- Bootstrap context now writes `selected-task.md`, `acceptance-criteria.md`,
  `allowed-write-scope.md`, and command-specific `verification-output.md` from authored task
  fields.
- Quality scoring now flags heavy repair burden, suspiciously small patches for larger tasks,
  and placeholder documentation examples.
- Stage briefs now include exact skeleton hints for `stage-result.md` and
  `validator-report.md` to reduce first-pass contract churn.
- Native runtime prompts now make turn completion explicit after the final required
  document write so providers that have already produced valid Markdown artifacts do not
  keep the adapter call open until a stage timeout.
- OpenCode native runs can now finish with `document_complete` when required stage
  documents settle but the provider process does not return a final message; canonical
  validation still decides whether the stage blocks, repairs, or advances.
- Idea semantic validation still rejects absolute success claims, but allows negated
  security-guarantee caveats such as "without implying a broader guarantee" because those
  phrases document risk rather than overclaiming certainty.
