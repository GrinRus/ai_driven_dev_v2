# Main User Stories

These user stories define why AIDD exists and what the first release must make possible.

## Primary personas

- **Operator** — runs AI-driven delivery flows on real tasks.
- **Maintainer** — evolves the core, adapters, validators, and prompt packs.
- **Evaluator** — runs harness and eval scenarios to compare behavior and detect regressions.
- **Adapter author** — adds support for a new runtime without changing workflow semantics.

## User stories

### US-01 — runtime portability

As an **operator**, I want to run the same governed delivery flow on different runtimes so that my workflow does not collapse when I switch from one runtime to another.

Success signals:

- the same stage graph works across maintained runtimes,
- runtime-specific details stay inside adapters,
- run artifacts remain comparable across runtimes.

### US-02 — document-first artifacts

As an **operator**, I want every stage to consume and produce Markdown artifacts so that I can inspect, diff, edit, review, and reuse them without special tooling.

Success signals:

- stage inputs and outputs are readable Markdown files,
- required sections are documented and validated,
- frontmatter stays optional metadata rather than the main payload.

### US-03 — validation before progression

As an **operator**, I want stage outputs to be validated before the workflow advances so that incomplete or malformed artifacts do not silently poison later stages.

Success signals:

- each stage has required output documents,
- validation reports are durable artifacts,
- invalid output triggers repair or stop, never silent acceptance.

### US-04 — self-repair on bad outputs

As an **operator**, I want the system to retry a stage with a repair brief when validation fails so that small model misses do not force manual cleanup every time.

Success signals:

- failed validation creates a repair brief,
- repair attempts are budgeted and logged,
- the final stage result preserves the repair history.

### US-05 — user interview when the task is ambiguous

As an **operator**, I want the system to ask me clarifying questions at the right stages so that it does not invent product decisions when the requirement is underspecified.

Success signals:

- questions are surfaced in the CLI,
- questions and answers are persisted as documents,
- unanswered questions block progression when the stage policy requires them.

### US-06 — native runtime visibility

As an **operator**, I want to see native runtime logs while a run is happening so that I can understand what the runtime is doing instead of reading only abstract summaries.

Success signals:

- adapters stream raw stdout and stderr when possible,
- the CLI can show runtime-native logs,
- logs are also saved for replay and eval analysis.

### US-07 — harness and eval from day one

As an **evaluator**, I want harness scenarios, graders, and log analysis built into the product so that runtime changes, prompt changes, and adapter changes can be measured instead of guessed.

Success signals:

- smoke, regression, and manual external audit scenarios exist,
- manual external audit evidence can be refreshed as auditable bundles or explicit environment blockers,
- every run produces durable audit artifacts,
- failure classification separates model, document, adapter, and environment failures.

### US-08 — clean adapter extension

As an **adapter author**, I want to add a new runtime by implementing a well-defined adapter protocol so that I do not need to modify core workflow logic.

Success signals:

- the adapter protocol is explicit,
- conformance tests exist,
- adding a runtime mostly changes adapter-local code and the runtime matrix.

### US-09 — installable operator experience

As a **platform engineer**, I want to install and run AIDD through standard Python delivery channels so that teams can adopt it in local development and controlled CI environments.

Success signals:

- the project ships as a Python CLI package,
- the tool works with PyPI, `pipx`, `uv tool install`, and source checkout,
- release and install evidence is captured for supported delivery channels,
- runtime binaries stay external and replaceable.

### US-10 — prompt and workflow change accountability

As a **maintainer**, I want prompt changes and workflow changes to be reviewable and measurable so that behavior does not drift invisibly over time.

Success signals:

- prompt files live in Git and are reviewed like code,
- runs record the prompt file paths, Git commit SHA, and content hashes used,
- evals can be re-run against the same scenario to compare outcomes.

### US-11 — operator workflow frontend

As an **operator**, I want a frontend for the governed delivery flow so that I can run each stage, answer questions, inspect artifacts, and view runner logs without losing the CLI's workflow semantics.

Success signals:

- the frontend can start and resume the full `idea -> qa` flow and individual stages,
- blocking questions can be answered in the frontend and persist to the standard question and answer documents,
- runtime logs, validation reports, repair history, and stage artifacts are visible with CLI-equivalent provenance,
- after a run reaches a terminal state, the frontend can guide the operator to create a new work item, follow-up flow, cloned flow, eval batch, or archive decision without mutating the completed run.

### US-12 — project-set workflow

As an **operator**, I want one governed flow to cover a monorepo or a defined set of related project roots so that cross-project work stays coordinated without losing per-project ownership and validation evidence.

Success signals:

- project or package roots are declared before execution and remain visible in run artifacts,
- stage artifacts, questions, logs, and validation evidence preserve project ownership and cross-project links,
- execution stays bounded to the declared project set while runtime-specific discovery remains outside core workflow semantics.

## Future beta readiness gate

Beta readiness is a future acceptance gate, not a claim about the current alpha
prerelease line. Before a beta label is used, AIDD needs current evidence for:

- install and upgrade from PyPI through `pipx` and `uv tool`;
- clean `aidd ui` onboarding with no existing `.aidd/` or work item;
- Codex-first real-provider UI execution through at least `idea -> research`, with
  Claude Code and OpenCode evidence or explicit provider/auth blockers;
- browser-verified operator UX for onboarding, runner selection, selected-stage launch,
  long-run visibility, Implement Review, Review Findings, QA Verdict, remediation, and
  stale downstream rerun;
- project-set boundaries that group declared roots and flag out-of-scope changes without
  mixing unrelated repositories;
- prompt/workflow accountability surfaces with prompt paths, hashes, config snapshot,
  runtime id, Git SHA when available, and stage graph;
- runtime approval audit visibility for pending, approved, denied, cancelled, and
  policy-blocked requests;
- release evidence showing GitHub Release, PyPI, `pipx`, and `uv tool` verification.

## Out of scope for the first release

The first release is not trying to:

- bundle third-party runtimes,
- guarantee cloud orchestration for every runtime,
- guarantee multi-repository orchestration beyond explicitly declared local project roots,
- replace human product ownership,
- hide runtime differences when those differences matter for capabilities.
