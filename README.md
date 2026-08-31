# AIDD

[![CI](https://github.com/GrinRus/ai_driven_dev_v2/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/GrinRus/ai_driven_dev_v2/actions/workflows/ci.yml)
[![Security](https://github.com/GrinRus/ai_driven_dev_v2/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/GrinRus/ai_driven_dev_v2/actions/workflows/security.yml)
[![PyPI](https://img.shields.io/pypi/v/ai-driven-dev-v2?include_prereleases&label=PyPI)](https://pypi.org/project/ai-driven-dev-v2/)
[![Python](https://img.shields.io/pypi/pyversions/ai-driven-dev-v2)](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/compatibility-policy.md)
[![License](https://img.shields.io/github/license/GrinRus/ai_driven_dev_v2)](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/LICENSE)

**A reviewable, document-first workflow around the AI coding runtimes you already use.**

AIDD (`ai_driven_dev_v2`) is an open-source orchestration layer for AI-assisted software
delivery. It runs one staged workflow through Claude Code, Codex, OpenCode, Qwen Code, or an
AIDD-compatible CLI without making the workflow depend on one provider.

Instead of turning a prompt directly into an opaque code change, AIDD saves the requirements,
decisions, outputs, questions, validation results, and available runtime logs in the local
project. Each stage produces readable Markdown and must pass its document contract before the
workflow can advance.

## Why AIDD?

Coding agents are useful, but a one-off agent run often leaves important questions unanswered:
What requirements did it use? Why did it make a decision? Was the output checked? Can the same
process run with another provider? What evidence remains after the session ends?

| Common agent workflow | AIDD |
| --- | --- |
| Context lives mainly in chat history | Inputs, decisions, and outputs are ordinary Markdown files |
| The process changes with the provider | One stage graph runs through provider-specific adapters |
| The final response is accepted as-is | Validators gate progression against explicit contracts |
| Small output mistakes require manual cleanup | A bounded repair attempt receives the exact findings |
| Ambiguity is guessed or lost | Blocking questions and answers become workflow artifacts |
| Logs disappear with the session | Runtime logs, attempts, and provenance remain inspectable |

AIDD validates conformance to its declared contracts; it does not guarantee that generated
software is correct. Human product ownership, code review, and appropriate testing remain
essential.

![AIDD project inbox showing work items and their next actions](https://raw.githubusercontent.com/GrinRus/ai_driven_dev_v2/main/docs/assets/aidd-project-inbox.png)

*The local Operator UI presents project work, decisions, documents, and retained run evidence.*

## Project status and safety

AIDD is prerelease alpha software. See [PyPI](https://pypi.org/project/ai-driven-dev-v2/)
for the latest published package and the
[changelog](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/CHANGELOG.md) for release
history. The `main` branch may contain unreleased changes.

> **Warning:** AIDD is intended for local evaluation and controlled operator trials. It is not
> ready for unattended production automation, and its interfaces may change.

Beta readiness is a future evidence gate, not a current production-readiness claim.

Before running AIDD:

- use a disposable branch, sandboxed checkout, or otherwise controlled workspace;
- review the provider command and permission policy—the selected runtime may have broad access
  to the working tree;
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
or model access. Docker/GHCR images are not published or supported during alpha.

## Install

Install the latest published package with either supported tool:

```bash
pipx install ai-driven-dev-v2
```

or:

```bash
uv tool install ai-driven-dev-v2
```

Then verify the installation and inspect runtime readiness:

```bash
aidd --version
aidd doctor
```

To reproduce a specific alpha release, append `==<version>` to the package name. `aidd doctor`
checks local configuration and command availability; it does not prove that provider
authentication, quota, or remote API access will succeed.

## Run your first workflow

Start in the local project root that should receive the workflow state. For a first trial, use a
disposable or feature branch.

### UI-first path

```bash
cd /path/to/local-project
aidd doctor
aidd ui
```

`aidd ui` prints a loopback URL. A new project opens Guided Setup; an existing `.aidd/`
workspace opens the project Inbox. Create or select a work item, then choose a runtime when you
are ready to launch. The UI and CLI use the same project-local files.

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

Inputs, outputs, logs, and reports are retained under the project-local `.aidd/` directory. A run
may stop with blocking questions instead of advancing. That is an explicit operator checkpoint,
not a silent failure.

The complete UI and CLI path is documented in the
[Operator Handbook](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/operator-handbook.md).

## How it works

The canonical workflow is:

```text
idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa
```

Every stage follows the same provider-independent loop:

1. AIDD gathers the declared Markdown inputs and builds a stage brief.
2. The selected adapter launches an external AI runtime.
3. The runtime writes stage documents while AIDD retains available logs and evidence.
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

`generic-cli` is not the default product onboarding runtime. It is a portability baseline for
operators who intentionally provide an AIDD-compatible wrapper command. For exact capabilities
and support commitments, see the
[runtime matrix](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/architecture/runtime-matrix.md).

## Scope and non-goals

AIDD is an orchestration and evidence layer. It is not:

- an AI model, coding agent, IDE, or hosted SaaS product;
- a replacement for human requirements, review, security analysis, or release decisions;
- a guarantee that a runtime will produce correct code or that a repair will succeed;
- a promise of identical capabilities across every AI runtime;
- a production-ready platform for unattended or remote multi-user automation.

The product starts from a local project root. Manual external repository evaluations are
maintainer audit evidence, not a product intake path or release automation. See the
[manual evaluation catalog](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/e2e/live-e2e-catalog.md) and
[scenario matrix](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/e2e/scenario-matrix.md)
for the maintained evaluation boundaries.

## Documentation

| Goal | Read |
| --- | --- |
| Browse documentation by role | [Documentation index](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/README.md) |
| Install, configure, and operate AIDD | [Operator Handbook](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/operator-handbook.md) |
| Diagnose common failures | [Operator Troubleshooting](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/operator-troubleshooting.md) |
| Understand support boundaries | [Support Policy](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/operator-support-policy.md) and [Compatibility Policy](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/compatibility-policy.md) |
| Understand the architecture | [Target Architecture](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/architecture/target-architecture.md) and [Document Contracts](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/architecture/document-contracts.md) |
| Follow product scope and plans | [User Stories](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/product/user-stories.md) and [Roadmap](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/docs/backlog/roadmap.md) |
| Review user-visible changes | [Changelog](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/CHANGELOG.md) |

## Development from source

```bash
git clone https://github.com/GrinRus/ai_driven_dev_v2.git
cd ai_driven_dev_v2
uv sync --locked --extra dev
uv run aidd --version
uv run aidd doctor
```

The [contribution guide](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/CONTRIBUTING.md)
describes the repository structure, quality checks, and review expectations.

## Contributing

Contributions to code, adapters, contracts, prompts, documentation, scenarios, and tests are
welcome. Start with the
[contribution guide](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/CONTRIBUTING.md),
review the [governance model](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/GOVERNANCE.md),
and follow the
[Code of Conduct](https://github.com/GrinRus/ai_driven_dev_v2/blob/main/CODE_OF_CONDUCT.md).

Use the [issue chooser](https://github.com/GrinRus/ai_driven_dev_v2/issues/new/choose) for a
reproducible bug, operator support request, or feature proposal. For a large change, open an issue
or draft pull request before investing in the full implementation.

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
