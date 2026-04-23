# ai_driven_dev_v2

Runtime-agnostic orchestration for document-first AI software delivery.

> Status: bootstrap repository + executable scaffold.  
> This archive is a **complete, consistent starting repository** for `ai_driven_dev_v2`: it includes architecture, roadmap, contracts, prompt packs, Codex-compatible skills, live E2E manifests, contributor workflows, and a minimal installable Python CLI.

## What this project is

`ai_driven_dev_v2` (AIDD) is a stage-based workflow system for governed AI-assisted software work.

It rebuilds the useful parts of `ai_driven_dev` so they are **not coupled to a single runtime**. The project keeps:

- explicit workflow stages,
- durable Markdown artifacts,
- validator gates,
- self-repair after invalid stage outputs,
- user interview loops,
- native runtime log visibility,
- harness and eval support from the beginning.

The canonical stage flow is:

`idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`

## Why AIDD exists

Most agentic coding systems become tightly bound to one host runtime, one prompt surface, or one plugin API. That makes them harder to port, harder to debug, and harder to evaluate.

AIDD separates:

- **core workflow semantics** from runtime integration,
- **document contracts** from model formatting habits,
- **operator experience** from any one runtime CLI,
- **harness/eval** from ad hoc prompt experimentation.

## What makes AIDD different

- **Runtime-agnostic core**  
  The core never assumes Claude Code, Codex, OpenCode, or any other runtime-specific API.

- **Markdown-first stage IO**  
  Stages read and write human-reviewable Markdown documents. Validation happens after generation.

- **Validation and self-repair**  
  Invalid outputs do not silently pass. The system validates, writes a repair brief, and reruns within a bounded budget.

- **Interview-aware execution**  
  If a stage needs clarification, the runtime can ask the user through the CLI and/or durable `questions.md` / `answers.md` files.

- **Native runtime log visibility**  
  The CLI is designed to stream raw runtime logs as closely as possible to the runtime's own UX.

- **Harness and eval built in**  
  Smoke scenarios, live E2E scenarios, graders, and log analysis are part of the product architecture.

## Primary user stories

The project is anchored in these outcomes:

- an operator can run the same governed flow on different runtimes;
- a team can inspect and edit stage artifacts as Markdown files;
- invalid stage outputs are repaired before the workflow advances;
- the system asks the user clarifying questions when the task is underspecified;
- a maintainer can add a new runtime adapter without rewriting the core;
- an evaluator can run smoke, regression, and live E2E scenarios with log analysis.

See `docs/product/user-stories.md` for the full set.

## Runtime support (current)

Workflow and stage execution today:

- `aidd run` supports runtimes `generic-cli`, `claude-code`, `codex`, and `opencode`.
- `aidd stage run` supports runtimes `generic-cli`, `claude-code`, `codex`, and `opencode`.

Runtime probes in `aidd doctor`:

- `generic-cli`
- `claude-code`
- `codex`
- `opencode`

Unsupported runtime handling:

- `aidd run` and `aidd stage run` fail fast with non-zero exit and `unsupported-runtime` classification when the runtime id is unknown.

Future bridge target:

- `pi-mono`

## Architecture in one sentence

`operator CLI -> AIDD core -> adapter -> runtime -> workspace documents`

The key architecture documents are:

- `docs/architecture/target-architecture.md`
- `docs/architecture/adapter-protocol.md`
- `docs/architecture/document-contracts.md`
- `docs/architecture/runtime-matrix.md`
- `docs/architecture/eval-harness-integration.md`
- `docs/architecture/distribution-and-development.md`

## What is in this repository today

This starter repository already includes:

- root product and contributor documentation,
- a second-pass-decomposed roadmap,
- active backlog files,
- stage and document contract skeletons,
- stage prompt-pack skeletons,
- `.agents/skills/` for Codex-style development workflows,
- live E2E scenario manifests built on public GitHub repositories,
- CI and release workflow skeletons,
- a minimal Python package and CLI bootstrap.

The following parts are still intentionally in-progress:

- release-channel verification against published artifacts (`pipx`, `uv tool install`, GHCR),
- maintained-runtime adapter conformance lane and reporting,
- one durable non-generic live workflow proof lane on a pinned public repository scenario.

That is deliberate: this bundle is meant to be the **starting repository for implementation**, not a falsely complete system.

## Installation from source

### Prerequisites

- Python 3.12+
- `uv`
- optional runtime binaries you want to integrate later, such as Claude Code

### Bootstrap the repo locally

```bash
uv sync --extra dev
uv run aidd --help
uv run aidd doctor
uv run pytest
```

### Create a starter workspace

```bash
uv run aidd init --work-item WI-001
```

This creates a local `.aidd/` workspace tree with stage directories and placeholder artifacts.

## Planned distribution channels

The intended release channels are:

- PyPI for `pipx install ai-driven-dev-v2`
- `uv tool install ai-driven-dev-v2`
- container images such as `ghcr.io/grinrus/ai-driven-dev-v2`
- source checkout for contributors and CI

Runtime binaries remain external dependencies. AIDD does not bundle Claude Code, Codex, OpenCode, or other runtimes.

Container image tagging rules for release tags:

- publish `vX.Y.Z`, `vX.Y`, and `vX`;
- publish `sha-<git-sha>` for traceability;
- publish `latest` only for stable tags without prerelease suffixes.

PyPI publishing tag rules:

- tag format must be `v<major>.<minor>.<patch>` with optional PEP 440 suffix (`aN`, `bN`, `rcN`, `.postN`, `.devN`);
- release tag must exactly match `v<project.version>` from `pyproject.toml`;
- tag-triggered publish jobs fail fast when tag format or tag/version alignment is invalid.

## Quickstart

```bash
# Install the local development environment
uv sync --extra dev

# Inspect runtime availability from local config
uv run aidd doctor

# Create a work-item workspace
uv run aidd init --work-item WI-001

# Read the roadmap before implementing
sed -n '1,200p' docs/backlog/roadmap.md

# Run the smoke tests
uv run pytest
```

## Current CLI surface

The bootstrap CLI already exposes the intended product shape:

```bash
aidd doctor
aidd init --work-item WI-001
aidd run --work-item WI-001 --runtime generic-cli
aidd stage run plan --work-item WI-001 --runtime generic-cli
aidd eval run harness/scenarios/live/typer-styled-help-alignment.yaml --runtime generic-cli
```

Today:

- `doctor` is functional,
- `init` is functional,
- `run` executes workflow progression for `generic-cli`, `claude-code`, `codex`, and `opencode`,
- `stage run` executes single-stage orchestration for `generic-cli`, `claude-code`, `codex`, and `opencode`,
- `run` and `stage run` fail fast for unknown runtime ids with `unsupported-runtime` classification,
- `eval run` executes the harness lifecycle and writes result bundles (`summary.md`, `verdict.md`, `runtime.log`, and validator artifacts).

## Operator documentation

For installation, diagnostics, and issue reporting workflows, use:

- `docs/operator-handbook.md`
- `docs/operator-troubleshooting.md`
- `docs/operator-support-policy.md`

## Live E2E catalog

The repository includes a curated live E2E set built on public GitHub repositories:

- `fastapi/typer`
- `encode/httpx`
- `simonw/sqlite-utils`
- `honojs/hono`

See:

- `docs/e2e/live-e2e-catalog.md`
- `harness/scenarios/live/`

## How to develop this project

Read in this order:

1. `AGENTS.md`
2. `docs/product/user-stories.md`
3. `docs/backlog/roadmap.md`
4. `docs/architecture/target-architecture.md`
5. the nearest nested `AGENTS.md`
6. the relevant skill in `.agents/skills/`

Then use the standard loop:

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy src
uv run pytest
```

## Repository map

- `src/aidd/` — Python package skeleton
- `contracts/` — stage and document contracts
- `prompt-packs/` — file-based stage prompts
- `docs/product/` — product framing and user stories
- `docs/architecture/` — fixed technical decisions and protocols
- `docs/e2e/` — live E2E catalog
- `docs/backlog/` — roadmap and active backlog
- `harness/scenarios/` — smoke and live scenario manifests
- `.agents/skills/` — reusable team skills for Codex-style development
- `tests/` — bootstrap smoke tests
- `MANIFEST.md` — archive contents summary

## Roadmap

The canonical plan lives in `docs/backlog/roadmap.md`.

The short actionable queue lives in `docs/backlog/backlog.md`.

## Compatibility policy

Compatibility guarantees for Python versions and operating platforms live in:

- `docs/compatibility-policy.md`

## Contributing

See `CONTRIBUTING.md`.

The short version:

- pick a local task from the backlog,
- keep the change aligned with the user stories,
- update docs/contracts/prompts when behavior changes,
- keep the core runtime-agnostic,
- run the smallest relevant checks before opening a PR.

## License

This project is licensed under the Apache License 2.0. See `LICENSE`.
