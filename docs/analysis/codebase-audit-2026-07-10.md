# Codebase Audit — 2026-07-10

## Executive summary

This report records a full code-quality and architecture audit of `ai_driven_dev_v2`
at commit `1f8c3e13e63c7c2f6269488e2a16f3efb8a401d8` (`v0.1.0a15`). It covers the
Python product, packaged JavaScript/CSS/HTML, release scripts, tests, contracts,
prompt packs, scenarios, and CI/release configuration. It is not a specialized security
assessment or a production-readiness certification. Security observations are deliberately
limited to defensive invariants and hardening actions; operational reproduction details are
not retained here.

The audit found **50 non-security findings**: **8 P1**, **37 P2**, and **5 P3**.
It also records four defensive security observations (three P1 and one P2). No P0 was
found. The dominant risks are:

- validation gates can accept internally inconsistent durable documents;
- terminal state and evidence publication are not transactional;
- live adapter cancellation, process cleanup, and evidence persistence are inconsistent;
- maintained scenario and release claims can drift from what CI actually executes;
- complexity and churn are concentrated in a few orchestration, UI, and validator modules.

The isolated full suite passed: **1,310 cases passed in 646.08 seconds** with **88% line
coverage**, **75% branch coverage**, and **85% combined coverage**. An earlier
resource-concurrent run produced two timing-sensitive harness failures; both passed in
isolation and the isolated full coverage run passed, but the underlying checkpoint race
is retained as `TEST-03`.

## Scope, method, and evidence policy

The review combines the product-quality characteristics in
[ISO/IEC 25010:2023](https://www.iso.org/standard/78176.html) with the architecture,
entry-point, data-flow, trust-boundary, and business-logic emphasis of the
[OWASP Secure Code Review Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Code_Review_Cheat_Sheet.html).
Automated tools supplied signals only; every promoted finding received manual control/data-flow
review, and confirmed defects received a disposable local reproduction or an unambiguous
logical proof.

Branch misses were treated as test signals, not proof of dead code, following
[Coverage.py branch coverage guidance](https://coverage.readthedocs.io/en/7.13.5/branch.html).
Vulture results were checked against registries, decorators, public surfaces, packaged
resources, callbacks, and compatibility policy because Python is dynamic. Dependency
results were interpreted using the
[pip-audit security model](https://github.com/pypa/pip-audit#security-model): it audits
dependency trees and known advisories, not application reachability or source behavior.

All raw command output is outside the tracked tree under
`/tmp/aidd-code-audit-2026-07-10/`. The only intentional tracked change from this audit
is this report.

## Baseline and reproducibility

| Item | Result |
| --- | --- |
| Commit | `1f8c3e13e63c7c2f6269488e2a16f3efb8a401d8`; detached HEAD; clean worktree before the report |
| Host | macOS `26.5.1`, Darwin `25.5.0`, arm64 |
| Python / uv / Node | CPython `3.13.7`; uv `0.8.22`; Node `25.9.0` |
| Inventory | 53,546 Python product/script lines; 13,267 packaged UI lines; 49,275 test lines; 1,238 test functions / 1,310 collected cases |
| Locked environment | `uv sync --locked --extra dev` succeeded |
| Configured lint | Ruff `0.15.11`: passed |
| Type checking | mypy `1.20.2`, strict project config: passed for 160 source files; `--warn-unreachable` also passed |
| Tests and coverage | `1,310 passed in 646.08s`; 17,902/20,358 statements covered; 4,998/6,660 branches covered |
| Package build | sdist and wheel built successfully |
| Wheel smoke | isolated wheel install, `aidd --version`, and `aidd doctor` passed |
| JavaScript syntax | all 12 packaged JavaScript files passed `node --check` |
| Browser smoke | source-installed UI loaded; runtime readiness and tab navigation worked; no console warnings/errors; 390 px viewport had no horizontal overflow; a disposable generic job reached canonical `cancelled` state through the local API |
| Dependency advisories | pip-audit `2.10.1`: 15 resolved runtime dependencies, zero known advisories |
| Current GitHub checks | CI, Python 3.12–3.14, adapter conformance, build, CodeQL, Scorecard, and Dependabot checks succeeded; dependency review was skipped on the push event as configured |
| Provider-live runs | Not run; authenticated Codex/Claude/OpenCode/Qwen execution is outside this audit |

Tool versions retained with the evidence include ast-index `3.20.0`, Vulture `2.16`,
Radon `6.0.1`, Bandit `1.9.4`, deptry `0.25.1`, jscpd `5.0.12`, and Coverage.py
`7.13.5`.

## Coverage matrix

| Area | Inventory/static pass | Manual risk-first pass | Dynamic evidence | Result |
| --- | --- | --- | --- | --- |
| Core, workspace, persistence, CLI | Complete | State transitions, publication, resume, lineage, immutability, concurrency | Focused temporary reproductions and narrow tests | Findings in `REL-01`, `REL-02`, `REL-07`–`REL-09`, `BUG-06`, `BUG-07`, `ARCH-02`, `ARCH-03`, `COMPAT-03` |
| Adapters, permissions, config | Complete | Process lifecycle, cancel/timeout, capability truth, prompt context, raw evidence | Fake local runtimes; no provider authentication | Findings in `REL-03`–`REL-06`, `BUG-08`, `REL-10`–`REL-12`, `COMPAT-04`–`COMPAT-06`, `PERF-02` |
| Validators, contracts, prompts | Complete for all eight stages | Structural, semantic, cross-document, repair, report vocabulary | 339 focused validator checks plus temporary full-stack fixtures | Findings in `BUG-01`–`BUG-05`, `ARCH-01`, `COMPAT-01`, `COMPAT-02` |
| UI backend and packaged frontend | Complete | HTTP/write boundaries, jobs, escaping, stale state, API drift, responsive behavior | Local source-installed browser/API smoke | `REL-01`, `REL-08`, `REL-09`, `PERF-01`, `TEST-02`; no confirmed XSS sink |
| Harness, evals, scenarios | Complete | Lifecycle budgets, first-failure classification, bundle durability, automation claims | Deterministic fixtures only | `BUG-10`, `BUG-11`, `TEST-01`, `TEST-03`, `DEAD-01`, `REL-13`, `REL-14` |
| Release, CI, dependencies | Complete | Release preflight/evidence, package contents, workflow parity | Build, isolated wheel smoke, advisory lookup | `REL-15`, `BUG-12`, `DEAD-05` |
| Tests and previous audits | Complete | Negative-path quality and prior source/UX conclusions rechecked rather than inherited | Full branch-coverage run | `COMPAT-02`, `TEST-01`–`TEST-03`, `REF-04` |

## Finding index

| ID | Category | Severity | Confidence | Effort | Summary |
| --- | --- | --- | --- | --- | --- |
| BUG-01 | BUG/ARCH | P1 | Confirmed | M | Invalid `stage-result.md` semantics can pass and publish |
| ARCH-01 | ARCH/BUG | P1 | Confirmed | M/L | Cross-document validation omits primary/upstream invariants |
| REL-01 | REL | P1 | Confirmed | L | Conflicting UI mutations can run concurrently on one run |
| REL-02 | REL | P1 | Confirmed | M | Success is durable before output publication completes |
| REL-03 | REL | P1 | Confirmed | M | Native prompt delivery can deadlock before timeout/cancel starts |
| REL-04 | REL | P1 | Confirmed | M | Codex and Qwen live transports ignore job cancellation |
| REL-05 | REL | P1 | Confirmed | M | Live transport termination does not stop the full process tree |
| REL-06 | REL | P1 | Confirmed | S | Fragmented Qwen events can be lost permanently |
| COMPAT-01 | COMPAT/ARCH | P2 | Confirmed | M | Canonical validator report vocabulary differs from its contract |
| COMPAT-02 | COMPAT/TEST | P2 | Confirmed | M | Four success examples fail the current validation stack |
| BUG-02 | BUG | P2 | Confirmed | S | Cross-validation parses question-like bullets outside the authoritative section |
| BUG-03 | BUG | P2 | Confirmed | S | QA mitigation/owner checks apply to a whole section, not each risk |
| BUG-04 | BUG | P2 | Confirmed | S | Mixed task-id styles hide tasks from coverage rules |
| BUG-05 | BUG | P2 | Confirmed | M | Prose tool names can satisfy executable-evidence rules |
| REL-07 | REL | P2 | Confirmed | S | Adapter exceptions leave durable stage state as `executing` |
| REL-08 | REL | P2 | Confirmed | S | Cancelling an operator-waiting job leaks its waiter thread |
| REL-09 | REL | P2 | Confirmed | S | Runtime approval decisions are not immutable or compare-and-set |
| PERF-01 | PERF/REL | P2 | Confirmed | M | UI jobs and live chunks have unbounded retention |
| BUG-06 | BUG | P2 | Confirmed | M | A new CLI workflow cannot practically start after `idea` |
| BUG-07 | BUG | P2 | Confirmed | S | Same-second runs make “latest” resolution inconsistent |
| ARCH-02 | ARCH | P2 | Confirmed | M | Workflow accountability reports only target-stage prompts |
| ARCH-03 | ARCH/REL | P2 | Confirmed | M | Archive mutates completed-run evidence |
| COMPAT-03 | COMPAT | P2 | Confirmed | M | Existing run manifests silently ignore requested runtime/config changes |
| BUG-08 | BUG/REL | P2 | Confirmed | XS | Non-finite timeout values disable enforcement |
| REL-10 | REL | P2 | Confirmed | M | Parent exit can leave streamed execution waiting on inherited pipes |
| BUG-09 | BUG/REL | P2 | Confirmed | S | Codex early failures can be persisted as successful exits |
| REL-11 | REL | P2 | Confirmed | M | Blocked live attempts lose canonical raw-log and exit evidence |
| COMPAT-04 | COMPAT/BUG | P2 | High | S | Qwen drops intervention metadata |
| COMPAT-05 | COMPAT | P2 | High | S | Claude capability reporting can advertise an unavailable execution path |
| COMPAT-06 | COMPAT | P2 | High | M | Codex live mode drops configured command arguments |
| PERF-02 | PERF/REL | P2 | Confirmed | L | Runtime log capture is unbounded and duplicated in memory |
| REL-12 | REL/COMPAT | P2 | Confirmed | M | Most launch failures lack normalized runtime evidence |
| BUG-10 | BUG | P2 | Confirmed | M | Eval failure taxonomy has broad false positives and structured false negatives |
| TEST-01 | TEST/COMPAT | P2 | Confirmed | L | `automation_lane: ci` manifests are not executed as scenarios |
| BUG-11 | BUG/TEST | P2 | Confirmed | S | CI-labelled smoke manifests contain stale execution assumptions |
| DEAD-01 | DEAD | P2 | Confirmed | M/L | Deterministic eval pipeline has no product entry point |
| REL-13 | REL | P2 | Confirmed | M | Harness timeout does not bound the complete lifecycle |
| REL-14 | REL | P2 | Confirmed | M | Hard-linked result bundles are not immutable snapshots |
| REL-15 | REL | P2 | Confirmed | S | Release preflight is not failure-bounded |
| BUG-12 | BUG/COMPAT | P2 | Confirmed | S | Release evidence collector accepts semantically invalid evidence |
| TEST-02 | TEST | P2 | High | M | Packaged JavaScript has no executable CI test lane |
| TEST-03 | TEST/REL | P2 | Confirmed | S/M | Running-stage frontend checkpoint is timing-sensitive |
| REF-01 | REF | P2 | Confirmed | L | Live E2E orchestration is an 8.6k-LOC multi-owner hotspot |
| REF-02 | REF | P2 | Confirmed | L | UI service and dashboard are multi-owner hotspots |
| REF-03 | REF | P2 | Confirmed | L | Permission and adapter execution paths concentrate lifecycle risk |
| DEAD-02 | DEAD | P3 | Confirmed | S | Validator scaffolds and a packaged prompt fragment are unreachable |
| DEAD-03 | DEAD | P3 | High | M | Superseded Claude question/resume code remains in production modules |
| DEAD-04 | DEAD | P3 | High | XS | One core interview capability function is unreferenced |
| DEAD-05 | DEAD | P3 | Confirmed | S | Three direct runtime dependencies are unused |
| REF-04 | REF/TEST | P3 | High | L | Validator and semantic-test hotspots impede contract synchronization |

## Defensive security summary

This table intentionally omits reproduction details and unsafe operational examples.

| ID | Component | Defensive invariant | Impact class | Rating | Recommended hardening |
| --- | --- | --- | --- | --- | --- |
| SEC-01 | `src/aidd/core/runtime_operator.py:318-431,755-771` | Broad brokered decisions must preserve protected-data and core-evidence ownership boundaries | Policy governance and sensitive-data exposure | P1 / Confirmed | Replace permissive lexical inference with typed capability allowlists, apply protection consistently to reads and writes, and require a real sandbox for broadly capable commands |
| SEC-02 | `src/aidd/cli/ui_http.py:51-69`; `src/aidd/cli/ui.py:2283-2361,3193-3203` | Local mutation requests require origin and session integrity, even on loopback | Unauthorized local state mutation | P1 / Confirmed | Add a per-process CSRF/session nonce, strict same-origin/Host checks, and strict JSON content-type enforcement |
| SEC-03 | Core workspace/run paths and harness bundle/run paths | User-controlled identifiers must resolve to one safe component inside the configured root | Filesystem containment and evidence integrity | P1 / Confirmed | Introduce shared typed identifiers, resolve-and-contain before the first write, and reject unsafe or symlinked ancestors |
| SEC-04 | `src/aidd/config.py:407-467,556-690` | Invalid safety-sensitive configuration must fail closed | Configuration integrity | P2 / High | Distinguish missing from blank values, validate known keys, and reject unknown or malformed safety fields |

Bandit reported no high-severity issue; its three medium URL-opening signals were bounded,
constant or loopback-oriented uses after manual review. The locked runtime dependency audit
reported no known advisory. These results reduce known-tool risk but do not prove absence
of application-level defects.

## Detailed P1 findings

### BUG-01 — Invalid `stage-result.md` semantics can pass and publish

- **Location and contract:** `src/aidd/validators/semantic_rules/registry.py:96-100`,
  `src/aidd/validators/structural.py:207-268`, and
  `src/aidd/validators/cross_document.py:243-416` do not enforce the semantic rules in
  `contracts/documents/stage-result.md:65-105,137-146`.
- **Reachable scenario and evidence:** a structurally complete result with the wrong stage,
  a missing declared output, and a skipped downstream stage produced zero findings. The
  normal reconcile/publish path preserved all three invalid claims in the published copy.
- **Impact and rating:** downstream consumers can receive a false durable checkpoint and
  advance using missing or mis-owned evidence. **P1, Confirmed, M.**
- **Remediation and regression:** add a common-document semantic rule for canonical stage,
  status, attempt history, existing declared outputs, blocker coherence, and exact next
  stage; run a final invariant check after normalization. Add an eight-stage parameterized
  publication test for wrong stage, missing output, and skipped next stage.

### ARCH-01 — Cross-document validation omits primary and upstream invariants

- **Location and contract:** `src/aidd/validators/cross_document.py:253-266` reads only
  interview, repair, stage-result, and project-set documents. For example,
  `src/aidd/validators/semantic_rules/implement.py:54-63` does not implement the selected-task,
  scope, and verification obligations in `contracts/stages/implement.md:41-51,105-117`.
- **Reachable scenario and evidence:** a syntactically valid implementation report can name
  a different task, list a nonexistent changed path, and claim verification unrelated to
  authored context while the complete current validation stack returns no finding.
- **Impact and rating:** the document-first gate validates local shape but not the evidence
  relationship that makes a stage trustworthy. **P1, Confirmed, M/L.**
- **Remediation and regression:** introduce stage-specific cross rules and a repository/
  environment evidence layer. For implement, compare exact selected task, observed changed
  paths, allowed scope, and authored verification. Add wrong-task, missing-path,
  out-of-scope, and skipped-authored-command tests; extend analogous rules to tasklist,
  review, and QA.

### REL-01 — Conflicting UI mutations can run concurrently on one run

- **Location and contract:** `src/aidd/cli/ui.py:2523-2539,2701-2718,2989-3030` creates a
  thread for every mutation without a per-run admission check. Attempt allocation in
  `src/aidd/core/run_store.py:181-229` is scan-then-create and JSON writes share a fixed
  temporary name at `:556-565`.
- **Reachable scenario and evidence:** two same-run stage requests were both accepted with
  distinct running jobs; a synchronized allocation exercise made both choose the same next
  attempt and one fail during creation.
- **Impact and rating:** concurrent jobs can lose history, collide on attempts or run IDs,
  race metadata/publication, and leave the state machine inconsistent. **P1, Confirmed, L.**
- **Remediation and regression:** add an atomic single-flight lock keyed by workspace,
  work item, and run, return conflict for overlapping mutations, add cross-process locking
  for CLI/UI coexistence, and allocate identities atomically. Test simultaneous stage,
  workflow, remediation, run, and attempt allocation.

### REL-02 — Success is durable before output publication completes

- **Location and contract:** `src/aidd/core/stage_runner.py:561-597` persists the validation
  transition before `src/aidd/core/stage_validation.py:338-376` reconciles and calls the
  non-transactional copy loop in `src/aidd/core/stage_outputs.py:240-285`.
- **Reachable scenario and evidence:** an injected publication failure raised from the
  normal success path while stage metadata remained `succeeded` and the output mirror was
  absent or incomplete.
- **Impact and rating:** downstream eligibility can observe terminal success without the
  canonical evidence required by that success. **P1, Confirmed, M.**
- **Remediation and regression:** publish to a staged directory, verify completeness,
  atomically commit the mirror, and persist success last. Inject failures at directory
  creation, copy, replace, and reconciliation; none may leave success or a partial mirror.

### REL-03 — Native prompt delivery can deadlock before timeout/cancel starts

- **Location and contract:** `src/aidd/adapters/subprocess_streaming.py:146-181` and
  `src/aidd/adapters/qwen/live.py:95-112` write the complete prompt synchronously before
  readers and the deadline/cancellation loop are active.
- **Reachable scenario and evidence:** a disposable runtime that emitted a large response
  before consuming a large prompt remained alive beyond the configured timeout; no result
  was available because both pipe directions blocked before supervision began.
- **Impact and rating:** realistic large input bundles can make a supposedly bounded stage
  hang indefinitely. **P1, Confirmed, M.**
- **Remediation and regression:** start readers and deadline first, feed stdin through a
  managed writer, and propagate writer failure/cancellation. Test a large bidirectional
  exchange and assert both timeout and explicit cancellation remain effective.

### REL-04 — Codex and Qwen live transports ignore job cancellation

- **Location and contract:** `src/aidd/adapters/surface.py:545-556,744-755` does not pass
  `StageRuntimeRequest.cancel_requested` into the live loops in
  `src/aidd/adapters/codex/live.py:333-369` and `src/aidd/adapters/qwen/live.py:118-141`.
- **Reachable scenario and evidence:** a fake live transport with cancellation already
  requested ended only at timeout; with no timeout configured the loop has no cancellation
  exit.
- **Impact and rating:** the UI advertises cancellation that cannot stop the two implemented
  live approval transports. **P1, Confirmed, M.**
- **Remediation and regression:** propagate cancellation through initialization, event
  polling, and approval waits, then classify and persist `cancelled`. Cover startup,
  active turn, and operator-wait cancellation for both adapters.

### REL-05 — Live termination does not stop the full process tree

- **Location and contract:** live launches at `src/aidd/adapters/codex/live.py:228-237` and
  `src/aidd/adapters/qwen/live.py:95-104` do not create a process group;
  `src/aidd/adapters/live_transport.py:143-151` stops only the parent.
- **Reachable scenario and evidence:** a disposable live parent with a child was stopped by
  the product lifecycle helper while the child remained alive.
- **Impact and rating:** timeout, denial, or cancellation can be reported while descendant
  work continues and retains resources. **P1, Confirmed, M.**
- **Remediation and regression:** share the process-group lifecycle used by the streamed
  runner, with graceful provider shutdown followed by bounded group termination. Assert
  descendant exit for timeout, cancellation, denial, and callback failure.

### REL-06 — Fragmented Qwen events can be lost permanently

- **Location and contract:** `src/aidd/adapters/qwen/live.py:219-226` advances the committed
  read offset to end-of-file before verifying that the final JSONL record is complete.
- **Reachable scenario and evidence:** an approval event split across two file appends was
  discarded as two invalid fragments and never delivered to the decision provider.
- **Impact and rating:** the provider can wait forever for a response to an event AIDD no
  longer has enough bytes to parse. **P1, Confirmed, S.**
- **Remediation and regression:** keep an incomplete trailing buffer or commit the offset
  only through the last newline. Split a representative event at every byte boundary and
  also cover malformed complete lines and duplicate IDs.

## Detailed P2 findings

### COMPAT-01 — Canonical validator report vocabulary differs from its contract

- **Location and contract:** `src/aidd/validators/reports.py:125-131` renders field names
  different from `contracts/documents/validator-report.md:42-45,69-80`; production issue
  codes also differ from contract and repair-prompt vocabulary.
- **Scenario and evidence:** canonical production output uses the implementation vocabulary,
  while existing consumers in `src/aidd/evals/log_analysis.py:67` and
  `src/aidd/core/run_inspection.py:718` parse that same implementation-specific form.
- **Impact and rating:** changing either side independently breaks compatibility and repair
  guidance. **P2, Confirmed, M.**
- **Remediation and regression:** create one field/code registry, synchronize renderer,
  contract, prompts, examples, and consumers, and preserve dual-read compatibility for a
  documented removal window. Test every emitted field and issue code against the registry.

### COMPAT-02 — Four success examples fail the current validation stack

- **Location and contract:** the tasklist, implement, review, and QA success examples under
  `contracts/examples/` use heading/evidence shapes that disagree with current document
  contracts, prompts, or semantic rules.
- **Scenario and evidence:** full-stack validation of one success example for each stage
  produced zero findings for idea, research, plan, and review-spec, but four findings each
  for tasklist, implement, review, and QA.
- **Impact and rating:** fixtures teach incompatible authoring forms and cannot protect
  contract evolution end to end. **P2, Confirmed, M.**
- **Remediation and regression:** select one canonical heading set, version intentional
  aliases, update examples and fixtures, and add an eight-stage success-example test plus
  invalid/repair examples that assert their exact expected codes.

### BUG-02 — Cross-validation parses question-like bullets outside the authoritative section

- **Location and contract:** `src/aidd/validators/cross_document.py:80-155` duplicates the
  interview grammar instead of using the section-aware parser in
  `src/aidd/core/interview.py:135-191`, contrary to the section boundary in the questions
  and answers contracts.
- **Scenario and evidence:** a valid `Questions` section containing `none` plus an example
  bullet in a later non-authoritative section was treated as an unanswered blocking
  question by cross-validation, while the canonical parser returned no question.
- **Impact and rating:** explanatory examples can block a valid stage. **P2, Confirmed, S.**
- **Remediation and regression:** reuse the canonical interview parser/section extractor and
  test question-shaped prose under Notes and Examples.

### BUG-03 — QA mitigation/owner checks apply to a whole section, not each risk

- **Location and contract:** `src/aidd/validators/semantic_rules/qa.py:149-180` checks
  severity per item but searches mitigation/owner tokens across the complete Risks section,
  contrary to `contracts/stages/qa.md:80-82`.
- **Scenario and evidence:** in a two-risk report, metadata on the first risk satisfied the
  rule for a second risk that had no treatment or owner; validation returned no finding.
- **Impact and rating:** untreated material risks can pass QA. **P2, Confirmed, S.**
- **Remediation and regression:** validate treatment metadata inside each risk item and
  report its line; add a neighboring-risk isolation test.

### BUG-04 — Mixed task-id styles hide tasks from coverage rules

- **Location and contract:** `src/aidd/validators/semantic_rules/ids.py:20-28` returns only
  `TL-*` identifiers whenever any are present, so tasklist rules at `:151-164,200-234`
  never inspect remaining `T*` tasks.
- **Scenario and evidence:** a mixed-style tasklist left one task without dependency and
  verification entries but produced no finding.
- **Impact and rating:** malformed tasklists can silently omit execution obligations.
  **P2, Confirmed, S.**
- **Remediation and regression:** return all IDs, separately reject mixed styles, and assert
  dependency/verification coverage for every discovered task.

### BUG-05 — Prose tool names can satisfy executable-evidence rules

- **Location and contract:** the command pattern in
  `src/aidd/validators/semantic_rules/evidence.py:11-24`, consumed by implement validation
  at `:225-267`, accepts bare tool vocabulary rather than command-shaped evidence required
  by `contracts/stages/implement.md:69-75`.
- **Scenario and evidence:** a prose verification bullet mentioning a tool and a passing
  outcome was accepted as executed command evidence.
- **Impact and rating:** implementation can claim verification without an executable command
  or captured assertion. **P2, Confirmed, M.**
- **Remediation and regression:** accept only fenced/backticked commands, prompt-prefixed
  commands, explicit `Command:` fields, or structured artifact/assertion references. Add
  positive and negative tables for prose, command, artifact, and outcome shapes.

### REL-07 — Adapter exceptions leave durable stage state as `executing`

- **Location and contract:** `src/aidd/core/stage_runner.py:380-428,454-476` handles a
  returned adapter failure but does not persist a terminal state when the executor raises.
- **Scenario and evidence:** an injected adapter exception escaped while stage metadata
  remained `executing`; the existing exception test checks repair-context restoration but
  not durable state.
- **Impact and rating:** resume and operator views can treat a crashed attempt as still live.
  **P2, Confirmed, S.**
- **Remediation and regression:** catch ordinary adapter exceptions at the orchestration
  boundary, restore owned documents in `finally`, persist failed state and diagnostic
  evidence, then re-raise if required. Assert `executing -> failed`.

### REL-08 — Cancelling an operator-waiting job leaks its waiter thread

- **Location and contract:** `src/aidd/cli/ui.py:291-329,2455-2483` marks the job cancelled
  without signalling the decision condition used by the waiting execution thread.
- **Scenario and evidence:** after cancellation the job was terminal but the waiter remained
  alive; a later decision could still wake the cancelled runtime path.
- **Impact and rating:** threads and execution state leak across terminal job boundaries.
  **P2, Confirmed, S.**
- **Remediation and regression:** cancellation must notify the condition and return an
  explicit cancellation decision; reject decisions for terminal jobs. Assert bounded
  thread exit and no post-cancel continuation.

### REL-09 — Runtime approval decisions are not immutable or compare-and-set

- **Location and contract:** `src/aidd/cli/ui.py:2494-2520` appends every submitted decision;
  `src/aidd/core/runtime_operator.py:1047-1069` builds a last-write-wins read model.
- **Scenario and evidence:** two opposite decisions for one request were both appended; the
  runtime could consume the first while the UI/audit view later reported the second.
- **Impact and rating:** execution and durable audit truth can contradict each other.
  **P2, Confirmed, S.**
- **Remediation and regression:** atomically resolve each pending request once; make an
  identical repeat idempotent and reject a conflict. A concurrent opposite-decision test
  must yield one winner shared by runtime and ledger.

### PERF-01 — UI jobs and live chunks have unbounded retention

- **Location and contract:** `_jobs` and each job's chunk list at
  `src/aidd/cli/ui.py:161-186,349-357,376-391` only grow; no byte limit, terminal-job TTL,
  count eviction, or response cap exists.
- **Scenario and evidence:** source inspection and a synthetic high-volume job show every
  chunk and every terminal job remains reachable for the server lifetime.
- **Impact and rating:** a long-lived local UI can consume unbounded memory even though full
  runtime logs are already durable on disk. **P2, Confirmed, M.**
- **Remediation and regression:** use a byte-bounded ring buffer with absolute cursors and
  truncation metadata, cap each response, and evict terminal jobs by TTL/count. Stress tests
  must hold memory within a fixed budget.

### BUG-06 — A new CLI workflow cannot practically start after `idea`

- **Location and contract:** `src/aidd/cli/run.py:136-166,218-228` always creates a new run
  and exposes no run ID for continuation, while `src/aidd/core/stage_graph.py:150-203`
  requires same-run upstream metadata even when published outputs exist.
- **Scenario and evidence:** a CLI run bounded from research to plan allocated a new run and
  stopped before invoking research solely because idea was not complete in that new run.
- **Impact and rating:** advertised `--from-stage` bounds are unusable for every non-first
  start in the normal CLI path. **P2, Confirmed, M.**
- **Remediation and regression:** expose an explicit resumable run identity or define
  out-of-window prerequisites through verified published artifacts. Test every non-first
  starting stage.

### BUG-07 — Same-second runs make “latest” resolution inconsistent

- **Location and contract:** timestamp formatting at `src/aidd/core/run_store.py:46-48`
  drops sub-second precision; resolvers in `src/aidd/core/run_inspection.py:234-276` and
  `src/aidd/core/run_lookup.py:141-153,266-288` apply different tie behavior.
- **Scenario and evidence:** two sequential manifests created in one second shared a
  timestamp; one API chose a run deterministically while inspection/resume rejected the
  same state as ambiguous.
- **Impact and rating:** commands documented to default to the latest run behave
  inconsistently. **P2, Confirmed, S.**
- **Remediation and regression:** retain microseconds or a monotonic sequence and use one
  resolver/tie-break policy. Test two real manifests created in the same second.

### ARCH-02 — Workflow accountability reports only target-stage prompts

- **Location and contract:** `src/aidd/core/run_provenance.py:70-86` is called from manifest
  creation for one target stage, while `src/aidd/core/run_accountability.py:70-110` ignores
  per-attempt indexes that contain actual stage prompt hashes.
- **Scenario and evidence:** accountability for an idea-through-QA workflow listed only the
  QA prompt set and omitted idea and all intermediate stages.
- **Impact and rating:** US-10 accountability does not represent prompts actually used by a
  multi-stage run. **P2, Confirmed, M.**
- **Remediation and regression:** aggregate immutable per-attempt provenance, including
  attempt mode, across executed stages. A full-flow test must expose every stage's active
  prompt set.

### ARCH-03 — Archive mutates completed-run evidence

- **Location and contract:** `src/aidd/core/run_store.py:779-811`, called from
  `src/aidd/cli/ui.py:2950-2974`, inserts operator archive state and changes the timestamp
  in the source `run-manifest.json`, contrary to completed-run immutability in the target
  architecture and README.
- **Scenario and evidence:** byte comparison before and after archive shows the completed
  manifest changes; existing UI tests encode that mutation.
- **Impact and rating:** source-run hashes and provenance are no longer immutable after an
  operator navigation action. **P2, Confirmed, M.**
- **Remediation and regression:** store archive intent in a separate append-only operator
  overlay/index and join it in read models. Hash the source run before and after archive and
  require byte identity.

### COMPAT-03 — Existing run manifests silently ignore requested runtime/config changes

- **Location and contract:** `src/aidd/core/run_store.py:706-727` returns an existing
  manifest without comparing requested immutable identity/config fields; same-run rerun and
  remediation paths can choose a different runtime.
- **Scenario and evidence:** a second manifest request with different runtime, target, and
  config returned the original file unchanged while later execution was free to use the new
  request.
- **Impact and rating:** authoritative run accountability can disagree with actual attempts.
  **P2, Confirmed, M.**
- **Remediation and regression:** reject mismatched immutable fields on reuse, or formally
  support mixed-runtime runs with truthful per-attempt snapshots and an aggregate model.
  Accept identical resume and test every identity/config mismatch.

### BUG-08 — Non-finite timeout values disable enforcement

- **Location and contract:** `src/aidd/config.py:499-553` accepts floating-point non-finite
  values because only `<= 0` is checked; `src/aidd/adapters/subprocess_streaming.py:181,196`
  then constructs a deadline that cannot expire normally.
- **Scenario and evidence:** both global and stage-specific non-finite TOML values loaded
  successfully in a disposable config and produced non-finite runtime budgets.
- **Impact and rating:** configuration that appears bounded can become unbounded.
  **P2, Confirmed, XS.**
- **Remediation and regression:** require a finite numeric value greater than zero at both
  config and execution boundaries. Test non-finite values, booleans, zero, negatives, and
  valid finite numbers.

### REL-10 — Parent exit can leave streamed execution waiting on inherited pipes

- **Location and contract:** the loop at `src/aidd/adapters/subprocess_streaming.py:211-224`
  exits only after the parent has ended and both reader pipes report EOF.
- **Scenario and evidence:** an immediate parent that left a short-lived child holding its
  pipes delayed the result for the child's lifetime; an unbounded child makes a no-timeout
  run wait indefinitely.
- **Impact and rating:** parent completion is not a bounded lifecycle boundary. **P2,
  Confirmed, M.**
- **Remediation and regression:** after parent exit, allow a short drain grace period, then
  stop the remaining process group and close/drain pipes deterministically. Cover finite and
  indefinite inherited-pipe children with and without a runtime timeout.

### BUG-09 — Codex early failures can be persisted as successful exits

- **Location and contract:** early-stop branches in `src/aidd/adapters/codex/live.py:533-595`
  build a run result without a stop reason; persistence in
  `src/aidd/adapters/surface.py:568-589` therefore classifies a terminated process as
  success.
- **Scenario and evidence:** a denied/early-stopped fake session returned a failed outer
  status while `runtime-exit.json` recorded success with a terminated exit code.
- **Impact and rating:** earliest-failure analysis, UI recovery, and durable adapter evidence
  contradict each other. **P2, Confirmed, S.**
- **Remediation and regression:** carry explicit classifications for denial, startup timeout,
  adapter failure, and intentional shutdown. Assert both outer status and persisted exit
  metadata for every early-stop branch.

### REL-11 — Blocked live attempts lose canonical raw-log and exit evidence

- **Location and contract:** blocked results return `run_result=None` from
  `src/aidd/adapters/codex/live.py:533-555` and `src/aidd/adapters/qwen/live.py:157-169`;
  early returns in `src/aidd/adapters/surface.py:557-567,756-766` skip normal persistence.
- **Scenario and evidence:** a fake live approval wait with no immediate decision retained
  only the provider transcript; canonical `runtime.log` and `runtime-exit.json` were absent.
- **Impact and rating:** the most useful recovery evidence disappears on the blocked path.
  **P2, Confirmed, M.**
- **Remediation and regression:** persist capture inside the live transport or return runtime
  evidence independently from execution status. Both live adapters must retain stdout,
  stderr, raw log, and a blocked exit record.

### COMPAT-04 — Qwen drops intervention metadata

- **Location and contract:** `StageRuntimeRequest` carries attempt mode and operator request
  fields at `src/aidd/adapters/runtime_execution.py:35-42`, but
  `src/aidd/adapters/surface.py:720-732` and `src/aidd/adapters/qwen/runner.py:28-40,207-226`
  do not propagate them.
- **Scenario and evidence:** a Qwen intervention request reaches its command context without
  intervention mode or the operator-request channel, so the generated prompt identifies the
  attempt as initial.
- **Impact and rating:** Qwen semantics differ from other adapters and durable intervention
  lineage is incomplete. **P2, High, S.**
- **Remediation and regression:** add the fields to Qwen context, environment, and native
  prompt. Cover native and adapter-flags intervention specs.

### COMPAT-05 — Claude capability reporting can advertise an unavailable execution path

- **Location and contract:** `src/aidd/adapters/claude_code/probe.py:34-67` can report live
  decision support, while `src/aidd/adapters/surface.py:435-451` blocks every non-full Claude
  request before launch and never invokes a live Claude transport.
- **Scenario and evidence:** a help surface containing the expected provider flag produces a
  positive capability report, but the registered execution surface still has no matching
  transport.
- **Impact and rating:** `aidd doctor` can report readiness that execution cannot honor.
  **P2, High, S.**
- **Remediation and regression:** advertise only adapter-implemented capabilities, or wire
  the transport before enabling the flag. Add probe-to-execution conformance for every
  claimed live transport.

### COMPAT-06 — Codex live mode drops configured command arguments

- **Location and contract:** `src/aidd/adapters/codex/live.py:218-230` keeps only the first
  configured token and constructs a fixed app-server command.
- **Scenario and evidence:** model, profile, or configuration arguments present in the
  configured command disappear when switching from full-access subprocess mode to brokered
  live mode, with no warning or validation error.
- **Impact and rating:** a permission-mode change can also change provider behavior and
  accountability. **P2, High, M.**
- **Remediation and regression:** explicitly map supported options into app-server/thread
  parameters and reject unsupported arguments. Test one preserved option and one
  deterministic rejection.

### PERF-02 — Runtime log capture is unbounded and duplicated in memory

- **Location and contract:** `src/aidd/adapters/subprocess_streaming.py:177-179,226-242`,
  `src/aidd/adapters/live_transport.py:43-59`, and adapter captures retain complete stdout,
  stderr, and combined logs, then create additional full strings during joins/persistence.
- **Scenario and evidence:** source inspection shows no byte/chunk bound on any capture;
  output is retained in per-stream and combined collections simultaneously.
- **Impact and rating:** a verbose or stuck provider can exhaust process memory before the
  durable log is written. **P2, Confirmed, L.**
- **Remediation and regression:** stream the full log directly to attempt files and retain
  only bounded tails/counters in memory. A high-volume fake runtime must preserve the disk
  artifact while staying within a defined resident-memory budget.

### REL-12 — Most launch failures lack normalized runtime evidence

- **Location and contract:** `src/aidd/adapters/subprocess_streaming.py:134-144` re-raises a
  launch error unless an adapter supplies a classification; only Claude opts in. The CLI
  fallback at `src/aidd/cli/stage_run.py:389-393` has no run result to persist.
- **Scenario and evidence:** missing Generic CLI, Codex, OpenCode, and Qwen executables
  produce a CLI launch error without normal `runtime.log` or `runtime-exit.json` artifacts.
- **Impact and rating:** equivalent failures are not comparable across adapters and disappear
  from normal attempt inspection. **P2, Confirmed, M.**
- **Remediation and regression:** define adapter-failure classification for every runtime and
  persist synthetic stderr/exit evidence consistently. Add a missing-executable conformance
  case for every registered runtime.

### BUG-10 — Eval failure taxonomy has broad false positives and structured false negatives

- **Location and contract:** `src/aidd/evals/log_analysis.py:441-455` uses broad text
  fragments, while normalized-event paths at `:502-539,643-689` inspect event kind but omit
  relevant structured event details; two public classification APIs can diverge.
- **Scenario and evidence:** an ordinary assertion containing environment-like wording was
  classified as an environment failure, while a structured request-failure event containing
  environment evidence was either unclassified or placed at the runtime boundary.
- **Impact and rating:** the harness can select the wrong earliest failure, fallback, or
  remediation route. **P2, Confirmed, M.**
- **Remediation and regression:** create one typed classifier over event kind, structured
  event fields, exit metadata, and narrowly defined text fallbacks. Test assertions, HTTP errors,
  executable/file absence, DNS, timeout, and agreement between both public APIs.

### TEST-01 — `automation_lane: ci` manifests are not executed as scenarios

- **Location and contract:** four maintained manifests declare `automation_lane: ci` and
  are listed that way in `docs/e2e/scenario-matrix.md:120-127`, but
  `.github/workflows/ci.yml:17-53` runs general pytest only. `src/aidd/cli/eval.py:17-84`
  exposes doctor/summary, not a deterministic run command.
- **Scenario and evidence:** repository search found tests that parse and assert manifest
  taxonomy, but no CI or product entry point executes their setup, run, verification, and
  bundle lifecycle.
- **Impact and rating:** CI can remain green while CI-labelled scenario commands or fixture
  assumptions are broken. **P2, Confirmed, L.**
- **Remediation and regression:** add a deterministic `eval run` entry point and a CI job that
  discovers and executes every `automation_lane: ci` manifest with an appropriate local
  runtime. Assert the discovered and executed manifest sets are identical.

### BUG-11 — CI-labelled smoke manifests contain stale execution assumptions

- **Location and contract:** `harness/scenarios/smoke/plan-stage-minimal-fixture.yaml:25-29`
  names a verification file absent from `harness/fixtures/minimal-python/`; the stagepack
  smoke command at `plan-stagepack-smoke.yaml:20-25` assumes AIDD exists in a fixture that
  does not declare it.
- **Scenario and evidence:** filesystem and clean-fixture inspection confirm the named test
  is absent and the stated command is not available from fixture dependencies.
- **Impact and rating:** once executed, both CI-labelled lanes fail before validating their
  intended behavior. **P2, Confirmed, S.**
- **Remediation and regression:** make each fixture self-contained, point to the real test,
  and define the installed/source AIDD command explicitly. Execute each manifest in a fresh
  materialized fixture.

### DEAD-01 — Deterministic eval pipeline has no product entry point

- **Location and contract:** `prepare_eval_run` in
  `src/aidd/harness/eval_preparation.py:130-165`, `persist_eval_reports` in
  `src/aidd/harness/eval_reports.py:548+`, and runner functions at
  `src/aidd/harness/runner.py:178-278,332-368` form a lifecycle with no CLI/CI caller.
- **Signals and manual exclusion:** AST-index plus repository search found no production
  caller for the first two and test-only callers for the latter two; the harness root exports
  none of them, and dynamic registry/command checks found no hidden entry point.
- **Impact and rating:** a substantial test-only architecture can drift while manifests claim
  a deterministic automation lane. **P2, Confirmed, M/L.**
- **Remediation and regression:** connect it through the deterministic entry point proposed
  in `TEST-01`, or remove/collapse it after a compatibility check. A product smoke must cover
  prepare through teardown and bundle persistence.

### REL-13 — Harness timeout does not bound the complete lifecycle

- **Location and contract:** setup, verification, and teardown at
  `src/aidd/harness/runner.py:101-143` have no timeout; the configured budget at `:226-256`
  applies only to the AIDD subprocess and does not supervise the full process group.
- **Scenario and evidence:** disposable lifecycle commands demonstrated that auxiliary steps
  can wait indefinitely and that a timed-out parent can leave descendant work active.
- **Impact and rating:** an evaluator can hang or continue mutating a fixture after reporting
  timeout. **P2, Confirmed, M.**
- **Remediation and regression:** enforce one lifecycle budget, launch each step in an owned
  process group, and perform bounded cleanup with evidence. Cover setup, run, verify, and
  teardown timeouts plus descendant exit.

### REL-14 — Hard-linked result bundles are not immutable snapshots

- **Location and contract:** `src/aidd/harness/result_bundle.py:349-359` prefers hard links
  when materializing evidence; writes at `:156-159` are also not committed as a bundle-level
  transaction.
- **Scenario and evidence:** after bundle creation, changing the source artifact changed the
  destination through the shared inode.
- **Impact and rating:** completed audit evidence can change without a bundle operation.
  **P2, Confirmed, M.**
- **Remediation and regression:** copy to a unique temporary destination, verify size/hash,
  atomically replace, and record a digest manifest. Later source mutation or deletion must
  not change the bundle; injected copy failure must leave no partial destination.

### REL-15 — Release preflight is not failure-bounded

- **Location and contract:** remote tag inspection at
  `scripts/release/preflight.py:81-113,165-177` has no subprocess timeout; the registry probe
  at `:180-188` handles only the expected not-found HTTP case.
- **Scenario and evidence:** an injected offline registry failure escaped as an exception
  instead of becoming a structured check; a stalled remote command has no bound.
- **Impact and rating:** a required maintainer preflight can hang or terminate without its
  promised JSON blocker evidence. **P2, Confirmed, S.**
- **Remediation and regression:** add command timeouts and convert timeout, transport, TLS,
  DNS, and server failures into explicit failed/blocked checks. Every failure case must still
  produce valid structured output.

### BUG-12 — Release evidence collector accepts semantically invalid evidence

- **Location and contract:** `scripts/release/evidence_collector.py:53-65,85-99` validates
  URLs and captured outputs with host-agnostic fragments and substring version checks,
  weaker than `docs/release-checklist.md:155-165`.
- **Scenario and evidence:** unrelated hosts, error text containing the expected token, and a
  longer version sharing the expected prefix all produced an overall successful evidence
  result in disposable inputs.
- **Impact and rating:** an unrelated link or failed install transcript can be recorded as
  accepted release evidence. **P2, Confirmed, S.**
- **Remediation and regression:** allowlist repository/registry host and path shapes, parse an
  exact semantic version, and require structured exit status. Test unrelated authorities,
  ambiguous versions, and error-bearing transcripts.

### TEST-02 — Packaged JavaScript has no executable CI test lane

- **Location and contract:** `.github/workflows/ci.yml:40-53` runs Python checks only;
  `tests/cli/test_ui_assets_contracts.py` mainly checks asset text, fragments, and static
  relationships across 8,882 lines in 12 JavaScript files.
- **Scenario and evidence:** no Node syntax or DOM-level command is present in CI. All 12
  files passed the audit's local `node --check`, so this is a test gap rather than a current
  syntax defect.
- **Impact and rating:** syntax, module ordering, stale async state, and browser-only error
  paths can regress while CI stays green. **P2, High, M.**
- **Remediation and regression:** add `node --check` immediately, then lightweight DOM-level
  tests for API-state ordering, escaping, cancellation, and error rendering. An intentional
  syntax error and an out-of-order mocked response must fail CI.

### TEST-03 — Running-stage frontend checkpoint is timing-sensitive

- **Location and contract:** `src/aidd/harness/live_e2e_black_box_orchestration.py:5221-5409`
  checks running state before sequential UI probes; the stage may finish between that check
  and the dashboard/stage responses. The observer begins at `:6880-6906`.
- **Scenario and evidence:** an initial resource-concurrent full run failed two tests because
  a stage changed from executing to succeeded during the checkpoint. Both tests passed in
  isolation, and the isolated 1,310-case coverage run passed.
- **Impact and rating:** machine load can turn a valid transition into a gating harness
  failure. **P2, Confirmed, S/M.**
- **Remediation and regression:** make the checkpoint transition-aware: re-read state after
  probes and classify a completed stage as a skipped running snapshot followed by the normal
  post-stage checkpoint. Add a barrier-based transition-during-probe test.

### REF-01 — Live E2E orchestration is an 8.6k-LOC multi-owner hotspot

- **Location and metrics:** `src/aidd/harness/live_e2e_black_box_orchestration.py` has 8,663
  lines, 251 top-level symbols, 42 file touches, and 12,241 lines of historical churn.
  Radon reports CC 53, 43, 39, and 36 in central command, frontend, stage, and checkpoint
  functions.
- **Concrete cost:** one module owns process supervision, flow state, resume, UI probes,
  quality gates, stage audits, next-flow, artifact copying, and reporting. The checkpoint
  race and several duplication clusters are inside this file.
- **Rating:** **P2, Confirmed, L.** This is a measurable change-isolation and test-selection
  risk, not a style preference.
- **Remediation and regression:** split process supervision, durable flow state, checkpoint
  probes, quality policy, and report writers behind typed results. Characterize current
  lifecycle behavior and retain black-box bundle tests across the extraction.

### REF-02 — UI service and dashboard are multi-owner hotspots

- **Location and metrics:** `src/aidd/cli/ui.py` has 3,276 lines and 42 file touches;
  `handle_get` is CC 43 and `handle_post` CC 27. The related
  `src/aidd/core/operator_frontend_dashboard.py` has 2,321 lines with CC 37, 28, 23, and 21.
  `operator-next-flow-actions.js` adds 2,884 lines and 51 touches.
- **Concrete cost:** HTTP routing, onboarding, jobs, approvals, workflow execution,
  remediation, next-flow, evidence reduction, presentation policy, and rendering evolve in
  the same hotspots; concurrency, cancellation, and stale-state defects cluster there.
- **Rating:** **P2, Confirmed, L.**
- **Remediation and regression:** extract a thin router, keyed job/admission service,
  immutable approval service, pure dashboard state reducer, evidence collectors, and
  separate next-flow controller/view modules. Preserve API contract fixtures and browser
  state tests at each boundary.

### REF-03 — Permission and adapter execution paths concentrate lifecycle risk

- **Location and metrics:** `src/aidd/core/runtime_operator.py` has 1,103 lines and several
  CC 11–13 classification functions; `src/aidd/adapters/surface.py` has 908 lines with
  repeated provider context/run/persist pipelines; `run_streamed_subprocess` is CC 22 with
  more than 50 statements.
- **Concrete cost:** request classification, process ownership, cancellation, exit mapping,
  and evidence persistence are interleaved or repeated, matching the defect clusters in
  `REL-03`–`REL-12`.
- **Rating:** **P2, Confirmed, L.**
- **Remediation and regression:** separate typed request policy, process supervisor, stop
  reasons, and evidence commit; use one execution template with adapter-local protocol hooks.
  First create cross-adapter characterization and lifecycle conformance tests.

## Detailed P3 findings

### DEAD-02 — Validator scaffolds and a packaged prompt fragment are unreachable

- **Location:** `src/aidd/validators/documents.py:6-13`, unused constants at
  `src/aidd/validators/semantic_rules/common.py:124-127,171`, and
  `prompt-packs/common/run-rules.md:1-7`.
- **Independent signals and exclusions:** AST-index and repository search found no callers;
  Vulture/coverage supported the code signal; manual review found no registry, export,
  decorator, callback, compatibility entry, or prompt-assembler reference. The prompt file
  is nevertheless included in the wheel.
- **Impact and rating:** stale helpers and a misleading packaged resource increase contract
  surface without behavior. **P3, Confirmed, S.**
- **Remediation and regression:** remove the code or connect the shared prompt fragment with
  explicit provenance. Normal validator and prompt-pack resource tests are sufficient after
  a final public-import check.

### DEAD-03 — Superseded Claude question/resume code remains in production modules

- **Location:** `src/aidd/adapters/claude_code/runner.py:394-682` plus unused text helpers in
  Claude, Codex, and OpenCode runners.
- **Independent signals and exclusions:** AST-index found only unit-test imports, textual
  search found no production caller, the symbols are not exported, and the registered
  runtime surface uses the shared `aidd.adapters.runtime_events` implementation instead.
- **Impact and rating:** roughly 289 lines duplicate active shared behavior and can drift.
  **P3, High, M** because undocumented direct external imports cannot be proven absent.
- **Remediation and regression:** complete a public-compatibility check, remove the obsolete
  block/helpers and implementation-only tests, and retain integration tests through the
  registered adapter surface.

### DEAD-04 — One core interview capability function is unreferenced

- **Location:** `src/aidd/core/interview.py:494-495`.
- **Independent signals and exclusions:** AST-index and repository-wide search found only the
  definition; manual review found no export, registry, decorator, resource callback,
  compatibility inventory, or documented entry point.
- **Impact and rating:** minor misleading API surface. **P3, High, XS.**
- **Remediation and regression:** remove after the final public-import check; the existing
  interview suite covers the active behavior.

### DEAD-05 — Three direct runtime dependencies are unused

- **Location:** `pyproject.toml:43-45` declares `python-frontmatter`, `markdown-it-py`, and
  `pydantic`.
- **Independent signals and exclusions:** deptry reported all three unused; AST-index and
  textual import search found no product use; manual resource/plugin checks found no dynamic
  import. The product implements its own frontmatter/Markdown parsing and does use PyYAML.
- **Impact and rating:** unnecessary install size, resolution work, and supply-chain surface.
  **P3, Confirmed, S.**
- **Remediation and regression:** remove the declarations in a dedicated compatibility task,
  regenerate the lock, build/install the wheel, and run package/validator tests.

### REF-04 — Validator and semantic-test hotspots impede contract synchronization

- **Location and metrics:** `src/aidd/validators/cross_document.py:243` is CC 23,
  `reports.py:57` CC 20, `review_spec.py:224` CC 19, and `plan.py:26` CC 18.
  `tests/validators/test_semantic.py` is 4,232 lines with 43 touches and 4,802 lines of
  churn; required-section and path-resolution logic is duplicated.
- **Concrete cost:** despite 89% validator branch coverage in the focused run, the false-pass
  cases in `BUG-01`–`BUG-05` were absent, and contract vocabulary drift reached examples,
  prompts, renderer, and consumers.
- **Rating:** **P3, High, L.**
- **Remediation and regression:** split cross rules by invariant/stage, derive section
  resolution from one registry, partition tests by stage, and add a shared full-stack fixture
  runner. Keep a small set of literal prompt checks and express the rest as invariant tables.

## Automated signal disposition

| Signal source | Raw signal | Disposition |
| --- | --- | --- |
| Configured Ruff | No findings | Passed baseline |
| Expanded Ruff | 2,184 signals, dominated by 548 `TRY003`, 119 `PLR0913`, 42 `TRY004`, 26 `PLR0912`, 22 `PLR0911` | Style-only items rejected; complexity contributed only where manual review found a concrete hotspot/defect cluster |
| Strict mypy + unreachable | No findings in 160 source files | Passed baseline |
| Vulture 100/90 | One `format` variable signal | Rejected: required `BaseHTTPRequestHandler.log_message` override signature |
| Vulture 60 | 149 signals | Dataclass fields, public helpers, Typer callbacks, dynamic registries, compatibility surfaces, and resources manually classified; only `DEAD-01`–`DEAD-04` promoted with independent evidence |
| ast-index | 298 files, 9,544 symbols, 37,836 references | Used to confirm callers/exports and project map; unused-symbol output never promoted alone |
| Radon | 113 rank C, 23 D, 3 E, 4 F functions/methods | Promoted only as `REF-01`–`REF-04` where size, churn, ownership, and concrete defects align |
| jscpd | 110 clones; 1,906 duplicated lines (2.86%) | Most adapter/scenario symmetry intentional; duplication retained as hotspot evidence, not separate findings |
| deptry | Nine reports | Five dev/docs packages rejected as expected for a product-source scan; PyYAML mapped correctly; three runtime packages promoted as `DEAD-05` |
| Bandit/Ruff security | No high Bandit issues; bounded medium URL signals; subprocess flags | Manually classified; defensive observations summarized without operational detail |
| pip-audit | Zero known advisories in 15 locked runtime dependencies | Passed, subject to dependency-tree and advisory-feed limits |
| Branch coverage | 1,662 missing branches | Treated as test targeting data; no branch was declared dead from coverage alone |

Intentional or rejected items include Typer-decorated commands, compatibility facades and
prompt-pack entries inside their documented removal window, always-present questions/answers
ledgers, stage-local intervention prompt duplication, `shell=False` argv subprocess calls,
and documented manual-only provider scenarios. Authentication and other productionization
topics already marked out of scope in prior roadmap work were not silently inherited as
new defects; only independently confirmed defensive invariants appear in the summary above.

## Needs-follow-up hypotheses

The following did not meet the main-register confidence threshold:

- follow-up draft creation may accept a missing source-run identity in one internal path;
- clone/follow-up flows may adopt a partially initialized work item and rewrite lineage;
- changing the text behind a resolved stable question ID may retain an answer whose meaning
  no longer matches;
- crash/power-loss durability is unclear because replace-based JSON writes do not define an
  `fsync` policy;
- empty stage prompt-pack directories may be contributor scaffolding rather than removable
  residue;
- real-provider Qwen event shapes and provider-specific question events require an
  authenticated live run and were not promoted.

## Recommended remediation sequence

No roadmap/backlog file was changed by this audit. If remediation is approved, create
roadmap-backed local tasks with the repository's `task-slicing` and `backlog-ops` workflows.
The recommended slice order is:

1. **Restore validation trust:** implement common `stage-result` semantics, stage-specific
   cross-document rules, and canonical validator vocabulary/examples (`BUG-01`, `ARCH-01`,
   `COMPAT-01`, `COMPAT-02`).
2. **Make terminal evidence transactional:** persist success after atomic publication,
   separate operator archive overlays, and validate manifest reuse (`REL-02`, `ARCH-03`,
   `COMPAT-03`).
3. **Unify execution lifecycle:** activate readers/deadlines before stdin, propagate live
   cancellation, own process groups, and persist every blocked/failed exit (`REL-03`–`REL-06`,
   `REL-10`–`REL-12`, `BUG-09`).
4. **Serialize operator mutations:** add keyed admission, atomic identity allocation,
   immutable decisions, waiter cancellation, and bounded UI retention (`REL-01`, `REL-08`,
   `REL-09`, `PERF-01`).
5. **Make automation claims executable:** add a deterministic scenario entry point, repair
   CI-labelled fixtures, bound the harness lifecycle, and snapshot evidence by copy/hash
   (`TEST-01`, `BUG-11`, `DEAD-01`, `REL-13`, `REL-14`, `TEST-03`).
6. **Repair secondary contract gaps:** address item-level validator defects, runtime
   capability/config propagation, eval taxonomy, release validation, and provenance
   (`BUG-02`–`BUG-08`, `ARCH-02`, `COMPAT-04`–`COMPAT-06`, `BUG-10`, `REL-15`, `BUG-12`).
7. **Reduce change amplification:** characterize and split the harness, UI/dashboard,
   adapter lifecycle, and validator hotspots; then remove confirmed dead code/dependencies
   (`REF-01`–`REF-04`, `DEAD-02`–`DEAD-05`).
8. **Schedule defensive hardening separately:** address the four defensive security
   observations through authorized, narrowly scoped tasks without expanding this report into
   a specialized security assessment.

## Exit assessment and limitations

The repository has strong baseline discipline: configured lint/type checks pass, the full
isolated test/coverage run passes across 1,310 cases, release artifacts build and install,
packaged JavaScript parses, supported Python CI is green, and known dependency advisories are
clear at the audit time. Those strengths do not offset the P1 invariant and lifecycle gaps:
the system can still accept invalid durable evidence, publish terminal state out of order,
and fail to bound live execution reliably.

This audit reviewed source and deterministic local behavior only. It did not run paid or
authenticated providers, certify performance under production workloads, test unsupported
Windows behavior, perform a specialized security exercise, or assert production readiness. The local
browser smoke covered initial/no-run UI state, runtime readiness, navigation, responsive
overflow, console health, and deterministic cancellation; it does not replace a full
provider-backed unhappy-path browser matrix.
