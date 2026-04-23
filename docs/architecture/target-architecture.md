# Target Architecture for `ai_driven_dev_v2`

## 1. Purpose

Build a runtime-agnostic orchestration system for agentic software delivery that:

- preserves the v1 stage flow,
- keeps repository-local artifacts as the source of truth,
- supports multiple runtimes without core rewrites,
- validates stage outputs before progression,
- includes user interview loops,
- and makes harness/eval/log analysis part of the product.

## 2. Non-goals

- Recreating a host-specific plugin under a different name.
- Making every runtime feature-identical.
- Asking runtimes to emit canonical JSON as the primary stage output.
- Porting large v1 runtime files unchanged.
- Hiding runtime behavior behind adapters so completely that operators lose observability.

## 3. Fixed technology choices

### 3.1 Implementation language

**Python 3.12+** is the implementation language for:

- the CLI,
- core orchestration,
- adapters,
- validators,
- harness and eval tooling,
- repo utilities.

Shell remains acceptable only for tiny operational helpers. Core logic and policy stay in Python.

### 3.2 Runtime-facing data shape

**Markdown is the runtime-facing contract format.**

The runtime reads and writes Markdown documents in the repository workspace. The core validates those documents.

### 3.3 Config and telemetry formats

- Repository and tool configuration: **TOML**
- Harness scenario definitions: **YAML**
- Telemetry and replay artifacts: **JSON / JSONL**
- Human-readable output and durable stage artifacts: **Markdown**

## 4. Architectural principles

1. **Document-first runtime IO**
   - Inputs and outputs for stages are Markdown documents.

2. **Validation before progression**
   - A stage cannot advance until required output documents validate.

3. **Repair instead of silent failure**
   - Validation errors trigger a self-repair loop within a configured attempt budget.

4. **Human questions are first-class**
   - If the runtime needs clarification, the system surfaces the question and persists it.

5. **Raw runtime visibility**
   - The operator CLI must be able to show runtime logs as close as possible to native runtime output.

6. **Adapters stay thin**
   - Adapters launch and observe runtimes. They do not own business semantics.

7. **Harness-first development**
   - Conformance, smoke cases, and evals are mandatory architecture, not optional test extras.

## 5. System layers

```text
operator CLI
  |
  v
core orchestrator
  |-- stage state machine
  |-- document manifest resolver
  |-- validator coordinator
  |-- self-repair controller
  |-- interview controller
  |-- run state / persistence
  |-- telemetry sink
  |
  +--> adapter protocol
          |
          +--> generic-cli adapter
          +--> claude-code adapter
          +--> codex adapter
          +--> opencode adapter
          +--> future pi-mono bridge
  |
  v
repository workspace
  |-- work-item docs
  |-- question / answer docs
  |-- reports
  |-- traces
```

## 6. Repository-local data model

Recommended shape:

```text
.aidd/
  config/
    aidd.toml
  workitems/
    TICKET-123/
      work-item.json
      context/
        intake.md
        user-request.md
        repository-state.md
      stages/
        idea/
          input/
          output/
          stage-brief.md
          questions.md
          answers.md
          validator-report.md
          repair-brief.md
          stage-result.md
        research/
          input/
          output/
          ...
        plan/
          input/
          output/
          ...
        review-spec/
          input/
          output/
          ...
        tasklist/
          input/
          output/
          ...
        implement/
          input/
          output/
          ...
        review/
          input/
          output/
          ...
        qa/
          input/
          output/
          ...
  reports/
    runs/
      TICKET-123/
        run-001/
          run-manifest.json
          stages/
            plan/
              stage-metadata.json
              attempts/
                attempt-0001/
                  input-bundle.md
                  runtime.log
                  artifact-index.json
    evals/
  traces/
    sessions/
    replays/
```

The exact layout may evolve, but the model is fixed:

- work-item documents are durable,
- stage-local canonical documents live in `workitems/<id>/stages/<stage>/`,
- upstream-facing handoff documents are published to `workitems/<id>/stages/<stage>/output/`,
- reports and traces are system-owned,
- runtime-facing artifacts remain local to the repository.

## 7. Stage model

The canonical stage chain remains:

1. idea
2. research
3. plan
4. review-spec
5. tasklist
6. implement
7. review
8. qa

Each stage has:

- a contract file,
- declared input documents,
- declared output documents,
- validation rules,
- question policy,
- repair policy,
- prompt pack.

## 8. Stage execution algorithm

For every stage run:

1. Resolve the stage contract.
2. Collect declared input documents.
3. Run preflight checks for missing or invalid prerequisites.
4. Build a **stage brief** in Markdown for the runtime.
5. Launch the runtime through the selected adapter.
6. Stream raw and normalized logs to the CLI and trace sinks.
7. If the runtime asks questions:
   - show them in the CLI,
   - persist them as `questions.md`,
   - collect answers or pause the run,
   - persist answers as `answers.md`,
   - resume if allowed.
8. After the runtime finishes, validate the declared output documents.
9. If validation passes:
   - write/update `stage-result.md` and `validator-report.md` in the stage root,
   - publish upstream-facing outputs to `workitems/<id>/stages/<stage>/output/`
     (declared primary outputs plus `stage-result.md` and `validator-report.md`),
   - update run state,
   - advance to the next stage if requested.
10. If validation fails:
    - write a repair brief in Markdown,
    - archive validator findings,
    - rerun the stage in repair mode if the attempt budget remains.
11. If repair budget is exhausted:
    - mark the stage as failed or waiting for human input,
    - persist the failure and stop progression.

## 9. Document-first contracts

Runtime-facing stage contracts are defined in Markdown, not JSON schema.

A contract specifies:

- path patterns,
- required input documents,
- required output documents,
- required frontmatter fields,
- required headings/sections,
- required cross-references,
- validation rules,
- repair budget,
- interview triggers.

### Why Markdown contracts

Markdown contracts make the system:

- readable to humans,
- easier to review in Git,
- easier to inspect during failures,
- more portable across runtimes,
- less dependent on model-perfect JSON formatting.

## 10. Stage result model

Every stage produces a Markdown `stage-result.md` document in the stage root and
publishes it to the stage `output/` directory for downstream consumption.

It includes:

- run metadata,
- status,
- output document list,
- validation summary,
- open questions,
- blockers,
- next actions,
- links to runtime logs and report artifacts.

This is the canonical stage summary for workflow progression.

## 11. Validation architecture

Validation is layered:

### 11.1 Structural validation

Checks file existence, frontmatter presence, required headings, section order when relevant, and obvious formatting issues.

### 11.2 Semantic validation

Checks that the content actually contains the required information for the stage.

### 11.3 Cross-document validation

Checks consistency between stage outputs and upstream documents.

### 11.4 Environment validation

For execution-heavy stages, checks evidence such as test logs or command results.

## 12. Self-repair architecture

Validation failure does not mean immediate stage failure.

Instead, the core:

1. writes a repair brief,
2. summarizes validator findings,
3. reruns the stage with the same document targets,
4. records the attempt number,
5. preserves previous invalid snapshots for audit,
6. stops only when:
   - validation passes,
   - budget is exhausted,
   - or human input is required.

Repair is stage-specific. The system should not assume the same repair prompt works equally well for all stages.

## 13. User interview architecture

Some stages require direct human clarification.

The system supports two paths:

### 13.1 Interactive path

The CLI displays the runtime question immediately and collects the answer.

### 13.2 Durable document path

The question is stored in Markdown so that:
- the run can pause,
- the user can answer later,
- the workspace remains self-explanatory.

Interview support is mandatory for at least:

- idea,
- plan,
- review-spec.

It is optional but supported for:

- research,
- implement,
- review,
- qa.

## 14. Adapter architecture

Adapters are responsible for:

- probing runtime availability,
- launching the runtime,
- streaming logs,
- exposing question events,
- mapping capabilities,
- classifying runtime failures.

Adapters are **not** responsible for:

- stage semantics,
- validation rules,
- repair policy,
- business logic,
- artifact ownership.

## 15. Runtime log architecture

The CLI should support three log modes:

- `native`: show raw runtime output as closely as possible,
- `normalized`: show AIDD-normalized events,
- `both`: show normalized summaries while storing raw logs.

Every run stores:

- raw runtime text log,
- structured runtime log when the runtime supports it,
- normalized events,
- stage timing,
- validation and repair history.

## 16. Prompt provenance architecture

Prompt packs are stage-specific Markdown files stored in Git.

The project does **not** use versioned prompt folders such as `v1/`, `v2/`, or `plan@0.1.0` as the primary mechanism.

Instead, every run records:

- the prompt-pack file paths used,
- the Git commit SHA when available,
- the file hash of each prompt file,
- the runtime id and adapter id,
- the stage contract path used for the run.

This gives replay and auditability without introducing version-folder sprawl.

A stage prompt pack normally contains:

- `system.md`
- `run.md`
- `repair.md`
- `interview.md`

Core configuration chooses the pack by path or named profile. Provenance is recorded by Git revision and file hash.

## 17. Harness and eval architecture

Harness is a product subsystem, not only a test helper.

It is responsible for:

- fixture setup,
- scenario execution,
- adapter conformance,
- trace capture,
- log analysis,
- grader execution,
- replay support,
- regression packaging.

Eval output must include log-analysis artifacts because runtime portability problems often show up in logs before they show up in final scores.

## 18. Security and permission model

Different runtimes expose different permission models. The AIDD core must therefore express:

- required capabilities,
- optional capabilities,
- explicit degraded behavior,
- unsafe operation markers,
- and documented fallbacks.

The core must never assume that a runtime's permission system is identical to another runtime's.

## 19. Distribution and deployment

Initial supported delivery channels:

- PyPI package for CLI installation,
- container image for CI and reproducible automation,
- source checkout for contributors.

Runtime binaries are installed and authenticated separately.

## 20. The most important anti-patterns to avoid

- Runtime-authored canonical JSON for stage outputs.
- Hidden business rules in adapters.
- Porting v1 host glue unchanged.
- Treating logs as debug-only instead of product data.
- Treating user clarification as an exceptional corner case.
- Adding evals only after runtime support appears to work.

## 21. Summary

The target v2 architecture is:

- Python-based,
- document-first,
- runtime-agnostic,
- validator-driven,
- repair-capable,
- interview-aware,
- harness-first,
- and fully observable from the CLI.
