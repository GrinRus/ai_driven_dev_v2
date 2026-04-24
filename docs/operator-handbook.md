# Operator Handbook

## 1. Purpose

This handbook describes the current operator path for installing, configuring, and running the first commands of `ai_driven_dev_v2` (AIDD).

Use it when you need a repeatable local setup for:

- checking runtime availability;
- initializing a work item workspace;
- validating the baseline toolchain before deeper scenario work;
- understanding the installed live E2E operator path.

## 2. Scope and Current Product State

AIDD is in bootstrap mode.

Today:

- `aidd doctor` is functional;
- `aidd init` is functional;
- `aidd run` executes workflow progression for `generic-cli`, `claude-code`, `codex`, and `opencode`;
- `aidd stage run` executes stage orchestration for `generic-cli`, `claude-code`, `codex`, and `opencode`;
- `aidd eval run` executes setup/run/verify/teardown lifecycle and writes a result bundle;
- live scenarios under `harness/scenarios/live/` are a manual external-audit lane: they prepare a pinned public-repository working copy, install a local AIDD wheel via `uv tool`, and run installed `aidd` from the target repository root.

Smoke, conformance, and live operator proof are separate lanes. Do not treat them as interchangeable.

For the GitHub Actions manual live lane, the selected live provider must be wired
through a runner-available command override secret:

- `AIDD_EVAL_CODEX_COMMAND`
- `AIDD_EVAL_OPENCODE_COMMAND`

Those values should point to wrapper commands that accept the AIDD adapter flags.

## 3. Prerequisites

Required:

- Python 3.12+
- `uv`

Optional:

- runtime CLIs you want to probe in `aidd doctor` (for example `claude`, `codex`, `opencode`)
- AIDD-compatible execution commands or wrapper commands for any runtime you want
  to use with workflow, stage, or live eval execution

Runtime binaries are external dependencies and are not bundled by AIDD.

## 4. Installation (Source Checkout)

From a repository checkout root:

```bash
uv sync --extra dev
uv run aidd --help
```

Recommended baseline verification:

```bash
uv run ruff check .
uv run mypy src
uv run pytest
```

## 5. Configuration

By default, `aidd doctor` and other commands look for `aidd.example.toml`.
In a source checkout, that file lives at the repository root as an example config.
Installed operator flows may omit it entirely and rely on defaults or an explicit `--config`.

Use this as the base operator config template:

```toml
[workspace]
root = ".aidd"

[runtime.generic_cli]
command = "python /path/to/aidd_generic_runtime_wrapper.py"

[runtime.claude_code]
command = "/path/to/aidd-claude-code-wrapper"

[runtime.codex]
command = "/path/to/aidd-codex-wrapper"

[runtime.opencode]
command = "/path/to/aidd-opencode-wrapper"

[logging]
mode = "both"

[repair]
max_attempts = 2
```

These command values are execution-surface examples, not promises that the raw
upstream provider binaries accept AIDD adapter flags directly. The configured
command must be AIDD-compatible for the selected runtime.

Current config fields consumed by the bootstrap CLI:

- `workspace.root`
- `runtime.generic_cli.command`
- `runtime.claude_code.command`
- `runtime.codex.command`
- `runtime.opencode.command`
- `logging.mode`
- `repair.max_attempts`

## 6. First-Run Procedure

### 6.1 Probe local environment

```bash
uv run aidd doctor
```

Confirm:

- the expected config path is loaded;
- workspace root is correct;
- each runtime availability result matches your machine state.

### 6.2 Initialize a work item workspace

```bash
uv run aidd init --work-item WI-001
```

This creates the `.aidd/` workspace tree and stage document scaffolding for the work item.

### 6.3 Inspect generated workspace artifacts

Recommended quick checks:

```bash
find .aidd -maxdepth 4 -type f | sort | head -n 40
```

Verify that:

- work item directories were created;
- stage document placeholders exist;
- initialization is repeatable and deterministic for operator use.

### 6.4 Validate execution surfaces

```bash
uv run aidd run --work-item WI-001 --runtime generic-cli
uv run aidd run --work-item WI-001 --runtime claude-code
uv run aidd stage run plan --work-item WI-001 --runtime generic-cli
uv run aidd stage run plan --work-item WI-001 --runtime opencode
uv run aidd eval run harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex
```

Expected behavior in current bootstrap state:

- `aidd run --runtime <maintained-runtime>` performs workflow execution through the selected adapter;
- `aidd stage run --runtime generic-cli` performs stage execution;
- `aidd stage run --runtime <supported-non-generic>` executes through the corresponding adapter path;
- `aidd eval run` executes the harness lifecycle and prints status, run id, and bundle paths;
- live `aidd eval run` is a manual external audit that installs a local wheel with `uv tool`, enters the pinned target repository, and keeps `.aidd/` inside that repository.
- the GitHub `manual-live-e2e` workflow additionally requires the runtime-command
  secret for the selected provider and fails fast before eval if it is missing.

## 7. Operational Notes

- Prefer absolute paths for config and workspace roots in automation scripts.
- Treat `doctor` output as the canonical machine-readiness snapshot before live scenario work.
- Record the exact command outputs for reproducible environment triage.
- For live E2E, distinguish the AIDD artifact root from the target repository cwd.
- Keep runtime authentication state and secrets outside the repository.

## 8. Related References

- [README](../README.md)
- [Distribution and Development](./architecture/distribution-and-development.md)
- [Target Architecture](./architecture/target-architecture.md)
- [Adapter Protocol](./architecture/adapter-protocol.md)
