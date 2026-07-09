# Live E2E Matrix Audit

This audit records the authored-task migration and black-box product-evaluation
classification for the maintained manual live matrix.

## Summary

The live matrix now uses authored task specs with explicit `live_matrix_role`.
Small scenarios are flow-regression lanes only. Medium, large, and xlarge scenarios
are product-evaluation lanes with `visible_request`, stage-visible authored task
constraints, operator-only `audit_rubric`, `complexity_axes`, per-stage-run quality
audits, normal review/QA remediation loops, and final manual quality reports.

## Size Classification

| Scenario | Size | Role | Main risk | Current maintained purpose |
| --- | --- | --- | --- | --- |
| `AIDD-LIVE-004` | `small` | `flow-regression` | Docs example quality and unrelated full-suite target instability. | Docs/config smoke proving the live flow still reaches QA. |
| `AIDD-LIVE-005` | `small` | `flow-regression` | Multiple runtime targets increase provider-specific timing variance. | Code-change smoke proving the live flow still handles implementation and tests. |
| `AIDD-LIVE-006` | `xlarge` | `product-evaluation` | Trust-boundary decisions cannot be invented by the model. | Security/interview product task for user-provided Python row generation. |
| `AIDD-LIVE-007` | `medium` | `product-evaluation` | Middleware error handling can affect runtime semantics beyond one test. | Runtime/API compatibility task for non-Error throw handling. |
| `AIDD-LIVE-008` | `xlarge` | `product-evaluation` | Router compatibility is API-sensitive and requires explicit policy choice. | Interview task for `/**` router semantics, compatibility tests, and docs. |
| `AIDD-LIVE-010` | `large` | `product-evaluation` | Codegen output compatibility depends on explicit discriminator policy. | Codegen/interview task for discriminator composition output. |
| `AIDD-LIVE-011` | `xlarge` | `product-evaluation` | Pytest collection and terminal reporting semantics are compatibility-sensitive. | Runtime-internals/interview task for collection error summaries. |
| `AIDD-LIVE-012` | `large` | `product-evaluation` | ASGI streaming, disconnect, background-task, and middleware behavior can regress across async boundaries. | Async runtime task bounded to focused Starlette response/middleware tests and ruff checks. |

## Matrix Quality Notes

- `AIDD-LIVE-001`, `AIDD-LIVE-002`, `AIDD-LIVE-003`, and `AIDD-LIVE-009` are retired
  from maintained coverage; new loader validation intentionally does not preserve
  backward compatibility with those old manifests.
- `AIDD-LIVE-004` is intentionally `small` and `flow-regression`; its expected output is documentation-only, so a
  broad implementation patch would be a quality smell. The historical 2026-05-25 Codex
  run reached `qa` and proved the stage flow, but final manifest verification failed in the
  upstream HTTPX full suite on `test_write_timeout[trio]` with a Trio async-generator
  `ResourceWarning`. That failure is outside the selected docs-only patch, so counted
  verification for this lane now checks tracked docs diff scope, concrete CLI example
  consistency, absence of placeholder runnable URLs, and QA artifact publication without
  calling the public endpoint. Full HTTPX pytest remains useful exploratory operator evidence,
  not the maintained execution gate for this regression scenario.
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
  fields. When a product-evaluation task has `visible_request`, `user-request.md` stays
  focused on that product request while `selected-task.md` also exposes authored constraints
  such as `intent`, `target_change`, `expected_scope`, `quality_bar`, and `size_rationale`.
- Manual `stage-quality-audits/<stage-run-id>.md`, `flow-quality-report.md`,
  `code-quality-report.md`, and `quality-report.md` record repair burden, suspiciously
  small patches for larger tasks, placeholder documentation examples, and target
  workspace hygiene; the live runner does not turn these signals into an automatic
  quality gate.
- Product-evaluation bundles now preserve stage-run ids so normal development loops
  such as `implement -> review -> implement -> review -> qa` can be audited without
  overwriting the first `implement`, `review`, or `qa` evidence. `request-remediation`
  remains a manual flow-control decision for `review` and `qa` only; it uses the
  existing AIDD remediation flow rather than changing the core stage graph.
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
