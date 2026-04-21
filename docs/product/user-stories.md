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

- smoke, regression, and live E2E scenarios exist,
- every run produces durable audit artifacts,
- failure classification separates model, document, adapter, and environment failures.

### US-08 — clean adapter extension

As an **adapter author**, I want to add a new runtime by implementing a well-defined adapter protocol so that I do not need to modify core workflow logic.

Success signals:

- the adapter protocol is explicit,
- conformance tests exist,
- adding a runtime mostly changes adapter-local code and the runtime matrix.

### US-09 — installable operator experience

As a **platform engineer**, I want to install and run AIDD through standard delivery channels so that teams can adopt it in local development, CI, and containerized environments.

Success signals:

- the project ships as a Python CLI package,
- the tool works with `pipx`, `uv tool install`, and container images,
- runtime binaries stay external and replaceable.

### US-10 — prompt and workflow change accountability

As a **maintainer**, I want prompt changes and workflow changes to be reviewable and measurable so that behavior does not drift invisibly over time.

Success signals:

- prompt files live in Git and are reviewed like code,
- runs record the prompt file paths, Git commit SHA, and content hashes used,
- evals can be re-run against the same scenario to compare outcomes.

## Out of scope for the first release

The first release is not trying to:

- bundle third-party runtimes,
- guarantee cloud orchestration for every runtime,
- replace human product ownership,
- hide runtime differences when those differences matter for capabilities.
