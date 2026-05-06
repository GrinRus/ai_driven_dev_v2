# ai_driven_dev_v2

Runtime-agnostic orchestration for document-first AI software delivery.

AIDD runs a governed staged workflow over a local project. It asks a runtime such as
Claude Code, Codex, OpenCode, or a generic CLI to produce Markdown stage artifacts, then
validates those artifacts before the workflow can advance.

The canonical stage flow is:

```text
idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa
```

## What is AIDD?

`ai_driven_dev_v2` (AIDD) is for teams that want AI-assisted software work to leave
inspectable evidence instead of only chat transcripts or opaque runtime state.

AIDD provides:

- a runtime-agnostic core with adapter-based runtime integration;
- Markdown-first stage inputs and outputs;
- validator gates before stage progression;
- bounded self-repair after invalid outputs;
- durable questions, answers, logs, validation reports, and run artifacts;
- a CLI and local operator UI over the same repository-local `.aidd/` workspace;
- deterministic harnesses and manual live E2E evaluation support.

AIDD does not bundle third-party runtime binaries. Operators install and authenticate
Claude Code, Codex, OpenCode, or other runtime CLIs separately.

## Install

Current published prerelease: `0.1.0a2`.

Install with `pipx`:

```bash
pipx install "ai-driven-dev-v2==0.1.0a2"
aidd --version
aidd doctor
```

Install with `uv tool`:

```bash
uv tool install "ai-driven-dev-v2==0.1.0a2"
aidd --version
aidd doctor
```

Run the container image:

```bash
docker run --rm ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a2 --version
docker run --rm ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a2 doctor
```

The `v0.1.0a2` release evidence passed PyPI publish, `pipx`, `uv tool`, container
publish, and GHCR verification. Published GHCR tags are:

- `ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a2`
- `ghcr.io/grinrus/ai-driven-dev-v2:sha-92c893d`

`latest` is published only for stable releases, not prerelease tags.

## Run your first local workflow

Start from the local project root that should receive AIDD workflow state:

```bash
cd /path/to/local-project
aidd doctor
aidd init --work-item WI-001 --root .aidd
aidd run --work-item WI-001 --runtime generic-cli --from-stage idea --to-stage plan --root .aidd
aidd run show --work-item WI-001 --root .aidd
```

This creates `.aidd/` inside the local project. Treat `.aidd/` as project-local
operator state and do not commit it unless your repository policy explicitly says so.

From a source checkout without installing globally, replace `aidd` with:

```bash
uv tool run --from /path/to/ai_driven_dev_v2 aidd
```

The product operator path starts from a local project root. `aidd init --github-issue <url>`
is out of product scope. Public GitHub repositories are live E2E targets and
support/reporting evidence sources only, not a product intake path.

## Choose a runtime

Use `aidd doctor` to check provider availability, configured execution commands, support
tiers, and default timeout settings.

| Runtime | External dependency | Default execution mode | Typical use |
| --- | --- | --- | --- |
| `generic-cli` | Python | `adapter-flags` | Local smoke path and deterministic checks |
| `claude-code` | Authenticated `claude` CLI | `native` | Claude Code-backed workflow runs |
| `codex` | Authenticated `codex` CLI | `native` | Codex-backed workflow runs and live evals |
| `opencode` | Authenticated `opencode` CLI | `native` | OpenCode-backed workflow runs and live evals |

Workflow and stage execution support the same runtime ids:

```bash
aidd run --work-item WI-001 --runtime codex --root .aidd
aidd stage run plan --work-item WI-001 --runtime opencode --root .aidd
```

Codex, OpenCode, and Claude Code default to native provider CLI execution. Advanced
operators can configure AIDD-compatible wrapper commands with `mode = "adapter-flags"`
when they need a custom execution surface.

Unknown runtime ids fail fast with `unsupported-runtime` classification.

## Inspect artifacts and logs

AIDD stores workflow evidence under `.aidd/`:

```bash
aidd run show --work-item WI-001 --root .aidd
aidd run logs --work-item WI-001 --stage plan --root .aidd
aidd run artifacts --work-item WI-001 --stage plan --root .aidd
aidd stage questions idea --work-item WI-001 --root .aidd
```

Stage documents, runtime logs, validator reports, repair briefs, questions, and answers
remain ordinary files in the local workspace. The core treats Markdown documents as the
contract surface; runtime-authored JSON schemas are not the primary stage output format.

## Operator UI

Start the local UI for an initialized work item:

```bash
aidd ui --work-item WI-001 --root .aidd
```

The UI reads the same `.aidd/` state as the CLI. It can show stage status, stage artifacts,
runtime logs, questions, repair history, and runtime readiness details without introducing a
separate workflow engine.

For the local UI evidence lane, see `docs/e2e/operator-ui-local-project.md`.

## How AIDD works

Architecture in one line:

```text
operator CLI / UI -> AIDD core -> adapter -> runtime -> workspace documents
```

Key design rules:

- the core owns workflow semantics, stage order, validation, repair, and workspace policy;
- adapters own runtime process launch, streaming, and runtime-specific command behavior;
- stage inputs and outputs are Markdown documents;
- validation failures trigger repair or an explicit stop;
- questions and answers are persisted as documents;
- runtime logs are streamed when possible and saved for replay and eval analysis.

Primary architecture docs:

- `docs/architecture/target-architecture.md`
- `docs/architecture/adapter-protocol.md`
- `docs/architecture/document-contracts.md`
- `docs/architecture/runtime-matrix.md`
- `docs/architecture/operator-frontend.md`
- `docs/architecture/project-set-workspace.md`
- `docs/architecture/distribution-and-development.md`

## Development from source

Prerequisites:

- Python 3.12+
- `uv`
- optional provider CLIs for runtime-specific development
- provider authentication configured outside AIDD

Bootstrap and check the repository:

```bash
uv sync --extra dev
uv run aidd --version
uv run aidd doctor
uv run --extra dev ruff check .
uv run --extra dev python -m mypy src
uv run --extra dev pytest -q
```

Contributor workflow:

1. Read `AGENTS.md`.
2. Read `docs/product/user-stories.md`.
3. Pick a local task from `docs/backlog/backlog.md`.
4. Use `docs/backlog/roadmap.md` for the full wave/epic/slice/task hierarchy.
5. Keep the core runtime-agnostic and update docs/contracts/prompts when behavior changes.

## Eval and release evidence

AIDD includes deterministic harness checks and manual live E2E scenarios. Live E2E is a
manual installed-operator audit, not CI and not a release gate.

Example live eval command:

```bash
aidd eval run harness/scenarios/live/typer-styled-help-alignment.yaml --runtime codex
```

Manual live E2E scenarios install AIDD through an isolated `uv tool` path, run from the
target repository root, and preserve audit bundles under `.aidd/reports/evals/`.

Public GitHub repositories are live E2E targets for evaluator evidence only. See:

- `docs/e2e/live-e2e-catalog.md`
- `docs/e2e/scenario-matrix.md`
- `harness/scenarios/live/`

Release and install evidence for PyPI, `pipx`, `uv tool`, and GHCR is recorded in
`docs/release-checklist.md`.

## Docs map

- `docs/operator-handbook.md` — operator install, config, and runtime guidance
- `docs/operator-troubleshooting.md` — diagnostics and common failure modes
- `docs/operator-support-policy.md` — support and evidence expectations
- `docs/product/user-stories.md` — product outcomes and scope boundaries
- `docs/architecture/` — stable architecture decisions and protocols
- `docs/e2e/` — manual live E2E and local operator UI evidence
- `docs/backlog/roadmap.md` — canonical plan
- `docs/backlog/backlog.md` — short actionable queue
- `docs/compatibility-policy.md` — Python and platform compatibility

## Repository map

- `src/aidd/` — Python package with core orchestration, adapters, validators, CLI, harness, and evals
- `contracts/` — stage and document contracts
- `prompt-packs/` — file-based stage prompts
- `harness/scenarios/` — smoke and live scenario manifests
- `.agents/skills/` — reusable team skills for Codex-style development
- `tests/` — deterministic unit, integration, docs, adapter, harness, and eval checks
- `MANIFEST.md` — historical archive contents snapshot, not the current source-of-truth inventory

## Contributing

See `CONTRIBUTING.md`.

The short version:

- keep changes aligned with the user stories;
- keep runtime-specific logic inside adapters;
- update docs, contracts, prompts, scenarios, and tests when behavior changes;
- run the narrowest useful checks locally before opening a PR.

## License

This project is licensed under the Apache License 2.0. See `LICENSE`.
