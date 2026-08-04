# AIDD

[![CI](https://github.com/GrinRus/ai_driven_dev_v2/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GrinRus/ai_driven_dev_v2/actions/workflows/ci.yml)
[![Security](https://github.com/GrinRus/ai_driven_dev_v2/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/GrinRus/ai_driven_dev_v2/actions/workflows/security.yml)
[![PyPI](https://img.shields.io/pypi/v/ai-driven-dev-v2?include_prereleases&label=PyPI)](https://pypi.org/project/ai-driven-dev-v2/)
[![Python](https://img.shields.io/pypi/pyversions/ai-driven-dev-v2)](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/compatibility-policy.md)
[![License](https://img.shields.io/github/license/GrinRus/ai_driven_dev_v2)](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/LICENSE)

**A reviewable, document-first workflow around the AI coding runtimes you already use.**

AIDD (`ai_driven_dev_v2`) is an open-source orchestration layer for AI-assisted software
delivery. It runs one governed workflow through Claude Code, Codex, OpenCode, Qwen Code, or
an AIDD-compatible CLI, while keeping the workflow itself independent of any one provider.

Instead of turning a prompt directly into an opaque code change, AIDD moves a work item
through explicit stages. Each stage produces readable Markdown, is checked against a
document contract, and either advances, attempts a bounded repair, or pauses for human input.
Artifacts, questions, validation results, and runtime logs remain available in the local
project for inspection.

[Quick start](#run-your-first-workflow) · [How it works](#how-it-works) ·
[Documentation](#documentation) · [Contributing](#contributing)

## Why AIDD?

Coding agents are useful, but a one-off agent run often leaves important questions
unanswered: What requirements did it use? Why did it make a decision? Was the output checked?
Can the same process run with another provider? What evidence remains after the session ends?

| Common agent workflow | AIDD |
| --- | --- |
| Context lives mainly in chat history | Inputs, decisions, and outputs are ordinary Markdown files |
| The process changes with the provider | One stage graph runs through provider-specific adapters |
| The final response is accepted as-is | Validators gate progression against explicit contracts |
| Small output mistakes require manual cleanup | A bounded repair attempt receives the exact findings |
| Ambiguity is guessed or lost | Blocking questions and answers are durable workflow artifacts |
| Logs disappear with the session | Runtime logs, attempts, and provenance remain inspectable |

AIDD validates conformance to its declared contracts; it does not guarantee that generated
software is correct. Human product ownership, code review, and appropriate testing remain
essential.

## How it works

The canonical workflow is:

```text
idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa
```

Every stage follows the same runtime-agnostic loop:

1. AIDD gathers the declared Markdown inputs and builds a stage brief.
2. The selected adapter launches an external AI runtime.
3. The runtime writes the stage documents while AIDD retains available logs and evidence.
4. AIDD validates the output against structural, semantic, and cross-document rules.
5. A valid result advances. An invalid result receives a bounded repair attempt. A blocking
   question pauses the run until the operator answers it.

```text
operator CLI / UI
        |
        v
    AIDD core ------> validator / repair / interview
        |
        v
     adapter -------> external AI runtime
        |
        v
project-local .aidd/ documents, logs, and evidence
```

The core owns workflow semantics, stage order, validation, and artifact policy. Adapters own
runtime-specific process launch, streaming, and capability mapping. See the
[target architecture](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/architecture/target-architecture.md)
for the complete model.

## Project status and safety

Latest published prerelease: `0.1.0a16`.
Latest accepted published prerelease evidence: `0.1.0a16`.
Current release-candidate package version on this branch: `0.1.0a17`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a16`.
The `main` branch is development source and may contain unreleased changes.

> [!WARNING]
> AIDD is alpha software for local evaluation and controlled operator trials. It is not
> ready for unattended production automation, and its interfaces may change.

Beta readiness is a future evidence gate, not a current production-readiness claim.

Before running AIDD:

- use a disposable branch, sandboxed checkout, or otherwise controlled workspace;
- review the configured provider command and permission policy—alpha defaults may give the
  selected runtime broad access to the working tree;
- install and authenticate the provider CLI separately;
- treat `.aidd/` as sensitive local state because it can contain prompts, repository context,
  operator answers, raw logs, and provider evidence;
- do not commit `.aidd/` unless your repository policy explicitly allows it;
- keep the local Operator UI on loopback unless you have deliberately reviewed the exposure.
  It is a local, no-auth operator surface rather than a remote multi-user service.

## Requirements

- CPython 3.12, 3.13, or 3.14
- Linux for the release-blocking platform path, or macOS on a best-effort basis
- `pipx` or `uv` for installation
- an installed and authenticated provider CLI, or a configured generic wrapper, for runtime
  execution

Windows is not currently supported. AIDD does not bundle AI runtimes, provider credentials,
or model access.

## Install with pipx

Install the latest published prerelease:

```bash
pipx install "ai-driven-dev-v2==0.1.0a16"
aidd --version
aidd doctor
```

## Install with uv tool

```bash
uv tool install "ai-driven-dev-v2==0.1.0a16"
aidd --version
aidd doctor
```

`aidd doctor` checks local configuration and runtime command availability. It does not prove
that provider authentication, quota, or remote API access will succeed.

## Container support

AIDD does not publish or support Docker/GHCR images during the alpha phase. Use the PyPI
package or a source checkout.

## Run your first workflow

Start in the local project root that should receive the workflow state. For a first trial,
use a disposable or feature branch.

### UI-first path

```bash
cd /path/to/local-project
aidd doctor
aidd ui
```

`aidd ui` starts a loopback server and prints its local URL. Open that URL in a browser. Without `--work-item`, it chooses the entry surface from the durable project state: when the project has
no accessible local `.aidd/` directory, Guided Setup lets you create or resume a work item, enter
the request, inspect runtime readiness, and select a runtime before launch. When an accessible
`.aidd/` directory already exists, a bare restart opens the project Inbox instead of onboarding;
it does not need an existing work-item marker. The Inbox has an explicit **New work item** action
for independent work; creating it does not require selecting a runtime or disturb existing work.
Select a runtime only when you choose to launch a workflow or stage. The UI and CLI use the same
project-local `.aidd/` workspace.

To open an initialized work item directly:

```bash
aidd ui --work-item WI-001 --root .aidd
```

### CLI-first path

This bounded example runs only the strategy stages through `plan`; it does not reach the
code-changing `implement` stage:

```bash
cd /path/to/local-project
aidd doctor
aidd init --work-item WI-001 --request "Implement a small, specific task" --root .aidd
aidd run --work-item WI-001 --runtime codex --from-stage idea --to-stage plan --root .aidd
aidd run show --work-item WI-001 --root .aidd
```

Initialization creates project-local state similar to:

```text
.aidd/
├── config/
├── workitems/
│   └── WI-001/
│       ├── context/
│       └── stages/
│           ├── idea/
│           ├── research/
│           └── ...
└── reports/
    └── runs/
```

A run may stop with blocking questions instead of advancing. That is a normal governed
outcome, not a silent failure.

## Supported runtimes

Support tiers describe maintenance and release impact, not feature identity. Runtime
capabilities can differ, and AIDD reports explicit degraded behavior when needed.

| Runtime | Support status | What you install |
| --- | --- | --- |
| `claude-code` | Tier 1 — release-blocking maintained | Authenticated `claude` CLI |
| `generic-cli` | Tier 1 — portability and conformance baseline | Configured AIDD-compatible wrapper command |
| `codex` | Tier 2 — actively maintained, non-blocking | Authenticated `codex` CLI |
| `opencode` | Tier 3 — limited maintained, best effort | Authenticated `opencode` CLI |
| `qwen` | Experimental | Authenticated Qwen Code CLI |

`generic-cli` is not the default product onboarding runtime. Use it when you intentionally
provide an AIDD-compatible wrapper command using `adapter-flags` mode. For exact capabilities
and support commitments, see the
[runtime matrix](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/architecture/runtime-matrix.md).

## Inspect and steer a run

The UI and CLI expose the same durable evidence:

```bash
aidd run show --work-item WI-001 --root .aidd
aidd run logs --work-item WI-001 --stage plan --root .aidd
aidd run artifacts --work-item WI-001 --stage plan --root .aidd
aidd stage questions idea --work-item WI-001 --root .aidd
aidd stage interact plan --work-item WI-001 --runtime codex \
  --request "Add rollback risks" --root .aidd
```

When a CLI stage stops on a question, inspect it with `aidd stage questions`, write the answer
to `.aidd/workitems/<work-item>/stages/<stage>/answers.md`, and rerun the stage. The UI can write question answers as `[resolved]`, `[partial]`, or `[deferred]` entries; only `[resolved]` answers unblock blocking questions.

Use `aidd stage interact <stage>` for a scoped correction or additional analysis. The request
is saved as stage-local Markdown input and the new result still passes through the normal
validator gate.

## Operator UI

The local **Document & Evidence Studio** is a browser surface over the same workflow state as
the CLI, not a second workflow engine. Guided Setup handles only missing, non-directory, or inaccessible workspace
context, Inbox is the restart entry for an existing project and surfaces decisions plus explicit
new-work creation, Studio keeps the current document and one next action together, and History
exposes retained attempts and lineage. Progress is factual: completed canonical stages, current
state, and retained live/terminal evidence rather than an invented percentage.

After terminal `qa`, the command center switches to **Flow Complete**.
It summarizes the final QA status, final artifacts, and blockers.
It also retains repair counts, approval counts, answered questions, recommended next-flow actions,
and source-run lineage. From there, operators can:

- create a new work item;
- start a follow-up flow;
- clone the previous flow;
- hand off to an eval / scenario batch; or
- archive the run without deleting artifacts or mutating the completed source run.

The detailed operator path lives in the
[Operator Handbook](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/operator-handbook.md).

## Scope and non-goals

AIDD is an orchestration and evidence layer. It is not:

- an AI model, coding agent, IDE, or hosted SaaS product;
- a replacement for human requirements, review, security analysis, or release decisions;
- a guarantee that a runtime will produce correct code or that a repair will succeed;
- a promise of identical capabilities across every AI runtime;
- a production-ready platform for unattended or remote multi-user automation.

The product operator path starts from a local project root. `aidd init --github-issue <url>`
is out of product scope. Public GitHub repositories are evaluator evidence sources only, not a
product intake path.

## Harness and evaluations

AIDD includes deterministic scenario loading, adapter conformance checks, graders, failure
classification, and report generation. Manual external repository evaluations are local
operator audit evidence; they are not CI/CD or release automation.

See the
[manual evaluation catalog](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/e2e/live-e2e-catalog.md)
and [scenario matrix](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/e2e/scenario-matrix.md)
for the maintained evaluation boundaries.

## Documentation

| Goal | Read |
| --- | --- |
| Install, configure, and operate AIDD | [Operator Handbook](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/operator-handbook.md) |
| Diagnose common failures | [Operator Troubleshooting](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/operator-troubleshooting.md) |
| Understand support boundaries | [Support Policy](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/operator-support-policy.md) and [Compatibility Policy](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/compatibility-policy.md) |
| Understand the architecture | [Target Architecture](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/architecture/target-architecture.md) and [Document Contracts](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/architecture/document-contracts.md) |
| Follow product scope and plans | [User Stories](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/product/user-stories.md), [Roadmap](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/backlog/roadmap.md), and [Backlog](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/backlog/backlog.md) |
| Review user-visible changes | [Changelog](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/CHANGELOG.md) |

## Development from source

```bash
git clone https://github.com/GrinRus/ai_driven_dev_v2.git
cd ai_driven_dev_v2
uv sync --locked --extra dev
uv run aidd --version
uv run aidd doctor
```

Run the repository quality checks:

```bash
uv run --extra dev ruff check .
uv run --extra dev python -m mypy src scripts
uv run --extra dev pytest -q
```

To use a source checkout against another local project without installing it globally:

```bash
uv tool run --from /path/to/ai_driven_dev_v2 aidd
```

The main code and extension points are:

- `src/aidd/core/` — runtime-agnostic orchestration and workspace policy
- `src/aidd/adapters/` — provider-specific integration
- `src/aidd/validators/` — document validation
- `contracts/` — stage and document contracts
- `prompt-packs/` — version-controlled stage prompts
- `src/aidd/harness/` and `src/aidd/evals/` — scenarios, graders, and reports
- `tests/` — deterministic regression and conformance coverage

## Contributing

Contributions to code, adapters, contracts, prompts, documentation, scenarios, and tests are
welcome. Start with the
[contribution guide](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/CONTRIBUTING.md)
and [Code of Conduct](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/CODE_OF_CONDUCT.md).
For a large change, open an
[issue](https://github.com/GrinRus/ai_driven_dev_v2/issues/new/choose) or a draft pull request
before investing in the full implementation.

## Security and support

Report vulnerabilities through the process in
[SECURITY.md](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/SECURITY.md). Do not put
tokens, private repository contents, provider credentials, or unredacted runtime logs in a
public issue.

For reproducible operator problems, see
[SUPPORT.md](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/SUPPORT.md).

## License

AIDD is available under the
[Apache License 2.0](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/LICENSE).
