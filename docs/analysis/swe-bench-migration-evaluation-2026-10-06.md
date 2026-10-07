# SWE-bench fixtures for migration evaluation

Research date: **2026-10-06**. Status: proposed fixture source for
`W57-E1-S1-T2`, not a selected benchmark matrix, implemented integration or completed run.
Linked story: `US-07`. The [accepted contract](../architecture/iterative-delivery-contract.md)
and [P01–P07](../architecture/iterative-delivery-decisions.md#baseline-protocol-decisions)
remain authoritative. The [roadmap](../backlog/roadmap.md) owns tasks and completion.

## Recommendation

Use a small, predeclared selection of SWE-bench Verified issues as independent code-behavior
fixtures, preferring candidates also present in Lite when their environment and scope qualify.
Start with a shortlist of three issues, qualify them, and select one for the bounded-fix
class of the existing four-class comparison. The other candidates remain alternatives or
separately declared diagnostic work; this proposal does not add native trials to P06's
twenty-four initial trials per configuration.

Verified was screened for underspecified issues and tests that reject otherwise valid fixes.
That supports its use as a starting point, not an assumption that every current row is a
complete or reproducible oracle. Its release report also identifies public-task contamination
as a limitation. Review issue/test agreement and qualify the actual pinned environment.
[Verified methodology and limitations](https://openai.com/index/introducing-swe-bench-verified/).

| Fixture source | Proposed role | Qualification needed |
| --- | --- | --- |
| Small Verified issues, preferably also in Lite | First choice for the bounded-fix class: original issue, base revision, independently authored fix/regression expectations. | Confirm exact split membership, issue/test agreement, runnable environment and genuinely executed tests. |
| Lite-only issues | Fallback candidates if the preferred shortlist cannot run reproducibly. | Explicit independent review of specification and tests; the Lite label alone does not establish suitability. |
| Multimodal or Multilingual issues | Possible later visual or JS/TS code-correctness extension. | Separate declared scope, runtime capabilities, image/browser/toolchain prerequisites and revision pins; no automatic matrix expansion. |

SWE-bench exposes task identity, repository/base commit, issue text, solution/test patches
and `FAIL_TO_PASS`/`PASS_TO_PASS` expectations. The useful pattern is checking both defect
resolution and preserved behavior against a source established outside our implementing
agent chain. [Dataset fields](https://www.swebench.com/SWE-bench/guides/datasets/).

## Preliminary issue shortlist

The following rows were inspected in the official Lite `test` viewer. A sparse official
Verified metadata query confirmed Astropy membership and test-list counts; it returned no
matching Django row and an HTTP 500 for scikit-learn. Astropy is the recommended first candidate
to qualify from this shortlist. Exact dataset revisions, full test identities, source/test
agreement and runnable environments remain pending; these are metadata observations only.

| Instance / base commit | Original behavior to exercise | Membership and proposed role |
| --- | --- | --- |
| `astropy__astropy-14995` / `b16c7d12ccbc7b2d20364b89fb44285bcbfede54` | Preserve mask propagation semantics in `NDDataRef` arithmetic. Verified metadata lists 1 F2P and 179 P2P cases. | Confirmed in Lite and the observed Verified test snapshot; first bounded-fix candidate to qualify. |
| `scikit-learn__scikit-learn-14983` / `06632c0d185128a53c57ccc73b25b6408e90bb89` | Correct representation of `RepeatedKFold` and `RepeatedStratifiedKFold`; two declared Lite defect tests plus regression expectations. | Observed in Lite; Verified membership unverified after metadata-server failure. Alternative requiring independent review and environment qualification. |
| `django__django-10924` / `bceadd2788dc2dad53eba0caae172bd8522fd483` | Accept a callable for `FilePathField.path` while retaining ordinary path behavior; callable and existing-path tests. | Observed in Lite, absent from the observed Verified query. API/contract-change alternative; review its expectations independently and preserve explicit callable-extension authority. |

Sources: [official Lite viewer, page 0](https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite/viewer/default/test?p=0),
[page 2](https://huggingface.co/datasets/SWE-bench/SWE-bench_Lite/viewer/default/test?p=2),
[Verified dataset](https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified),
[official filter API](https://huggingface.co/docs/dataset-viewer/filter).
Extract complete test lists from the pinned row rather than the clipped HTML view. An upstream
human difficulty annotation is not a measurement of our runtime cost or success probability.
Selecting any case remains T2 protocol work; do not add all three to the native matrix by default.

## Coverage and boundaries

| Existing acceptance need | What SWE-bench contributes | AIDD evidence still required |
| --- | --- | --- |
| Bounded fix | Real repository issue with pre-existing behavioral tests. | Source authority, selected route, genuine command receipts, exact tree identity and completion gates. |
| Ambiguous requirement | A repository can supply technical context. | A separate authored ambiguity and answer script, scoped decision and observable answer application. An intentionally altered issue is an AIDD-derived fixture. |
| Interface/contract change | A suitable issue can exercise a behavioral/API boundary. | Independent contract expectations and route rationale. A visual issue does not observe an operator using AIDD. |
| Correction/replanning with retained work | A repository can supply code and checks. | Controlled feedback, child lineage, addressed invalidation/reuse and refreshed final-tree proof. The feedback script is our fixture, not an original SWE-bench task. |
| Authority, missing/stale proof, fabricated success, crash/cancel | Tests can supply one behavioral oracle. | The accepted adversarial AIDD scenarios and their explicit expected stops. |
| Operator comprehension/recovery | No human observation is supplied. | P05's five real first-time participants, four unassisted successes and serious-error veto, plus rendered browser journeys. |

Keep the existing Hono non-error-throw fixture as an independently declared JS/TS correctness
case. A Python benchmark selection does not retire that coverage. AIDD-derived variations
must retain source attribution and a separate scenario identity; they are not official
SWE-bench scores. A small handpicked subset does not establish a leaderboard result or
population-wide improvement.

## Evaluation design

1. Pin dataset namespace, revision, split, instance ID and row digest; target base/setup
   commits; issue/source bytes; test-patch and exact test identities; harness revision;
   environment/image digest and tool versions. Record mutable tags as observations, not pins.
2. Give the coding runtime the original issue and base checkout in a fresh session. Keep
   gold solutions, evaluator test patches, grading scripts, `hints_text`, F2P/P2P test lists
   and answer-bearing metadata outside its writable/readable task context. Do not include
   future solution commits or pass the whole dataset row as a brief. Declared image assets
   may be original request inputs. Record how solution lookup is prevented or detected;
   a prompt instruction alone does not establish that the runtime could not read an answer.
3. Calibrate the evaluator before comparison: the unchanged base fails the declared defect
   expectation; the reference solution passes it; required preserved behavior remains valid.
   This is pending execution, not evidence obtained by reading the dataset. Run reference
   solutions only in the evaluator qualification environment, never as solver input.
4. Run AIDD's baseline and candidate with matched task/oracle/runtime/model/reasoning and
   environment controls. AIDD owns delivery; use SWE-bench's evaluator for patch assessment,
   without replacing AIDD's orchestration with another benchmark agent's inference loop.
5. Seal the actual final product patch/tree. Evaluate it against the pinned base plus
   evaluator-owned tests in a separate environment, preserving the transformation, command,
   code/test identities, stdout/stderr, timing and per-test outcomes. An eval transcript
   remains harness evidence until a real AIDD-owned execution/assessment path binds it;
   copying a benchmark verdict into a receipt is not verification.
6. Apply P06/P07: three counted candidate outcomes per case; retain all attempted trials,
   diagnose external failures with raw evidence, replace only eligible interrupted trials,
   and refresh affected proof after candidate changes. Other runtime tiers retain their
   existing release consequences. A missing required observation is not a success.

These are proposed harness/eval boundaries; no runtime-specific or benchmark process logic
belongs in the core. Registration of an evaluator command grants execution authority only;
its oracle independence must be established separately. Stage outputs remain Markdown.

For an unmodified benchmark trial, assess one sealed final submission; internal attempts
must not select a winner using hidden benchmark tests. If evaluator feedback is intentionally
fed into corrections, declare an AIDD-derived fixture and its feedback policy rather than
claiming a comparable official score. The official submission checklist separates single
submissions from repeated evaluated attempts and excludes test/hint/solution knowledge.
[Submission protocol](https://github.com/SWE-bench/experiments/blob/main/checklist.md).

## Two verdicts and a cache hazard

Record the official benchmark result separately from AIDD's acceptance result. The reviewed
upstream grader treats `XFAIL` as passing and permits a skipped `PASS_TO_PASS` case as
maintained. Therefore a `resolved` flag alone is insufficient for AIDD's required actual-check
gate. Qualify exact expected statuses and retain missing/skipped/xfail outcomes; choose a
fixture whose mandatory cases can execute and pass rather than silently weakening our gate.
[Reviewed grader](https://github.com/SWE-bench/SWE-bench/blob/main/swebench/harness/grading.py).

The documented evaluator cache uses run and instance IDs without the prediction diff.
Allocate a unique evaluation ID per actual attempt/patch identity and retain the patch digest;
refreshing code while reusing an old cached result would violate proof freshness.
Docker environment preparation is an independent prerequisite with its own logs/blockers.
[Harness and cache behavior](https://www.swebench.com/SWE-bench/reference/harness/).

The evaluation guide distinguishes resolved/unresolved results from instances that could
not be graded and from likely infrastructure/ambiguous failures. Treat those categories as
evidence to diagnose under P07; a heuristic label alone does not authorize discarding a
failed product trial. [Evaluation reporting](https://www.swebench.com/SWE-bench/guides/evaluation/).

## Next output and unverified work

`W57-E1-S1-T2` must record a qualified selected case, exact pins, independent expectations,
baseline inventory, scripts/scoring and the complete predeclared protocol. Protocol choices
are already accepted; fixture selection and runnable-environment evidence are not complete.
The existing native comparison task `W59-E2-S1-T1` later executes the selected protocol.
No additional task is needed merely to record this source proposal.

Multimodal sources currently describe different revisions: its official page reports an
open v2 test split, while the general dataset guide still describes empty test-patch fields.
Any later visual selection must inspect and pin the actual dataset/harness/assets instead
of relying on an older split-access assumption.
[Multimodal release page](https://www.swebench.com/multimodal.html),
[current dataset card](https://huggingface.co/datasets/SWE-bench/SWE-bench_Multimodal).

Research inspected official documentation, dataset metadata and grader source. No repository
task was solved, Docker image built/pulled, provider invoked, gold patch executed, participant
contacted or benchmark score produced by this work.
