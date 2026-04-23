# Operator Handbook

## 1. Purpose

This handbook describes the current operator path for installing, configuring, and running the first commands of `ai_driven_dev_v2` (AIDD).

Use it when you need a repeatable local setup for:

- checking runtime availability;
- initializing a work item workspace;
- validating the baseline toolchain before deeper scenario work.

## 2. Scope and Current Product State

AIDD is in bootstrap mode.

Today:

- `aidd doctor` is functional;
- `aidd init` is functional;
- `aidd run` executes workflow progression for runtime `generic-cli` only;
- `aidd stage run` executes stage orchestration for runtime `generic-cli` only;
- `aidd eval run` executes setup/run/verify/teardown lifecycle and writes a result bundle.
- This runtime gate is a temporary limitation until parity slices `W8-E1-S1` and `W8-E1-S2` are complete.

Plan all operator usage with that constraint in mind.

## 3. Prerequisites

Required:

- Python 3.12+
- `uv`

Optional:

- runtime CLIs you want to probe in `aidd doctor` (for example `claude`, `codex`, `opencode`)

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

By default, `aidd doctor` reads `aidd.example.toml` from the repository root.

Use this as the base operator config template:

```toml
[workspace]
root = ".aidd"

[runtime.generic_cli]
command = "python"

[runtime.claude_code]
command = "claude"

[logging]
mode = "both"

[repair]
max_attempts = 2
```

Current config fields consumed by the bootstrap CLI:

- `workspace.root`
- `runtime.generic_cli.command`
- `runtime.claude_code.command`
- `logging.mode`
- `repair.max_attempts`

`codex` and `opencode` probes currently use command discovery from the local PATH in `aidd doctor`.

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
uv run aidd eval run harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime generic-cli
```

Expected behavior in current bootstrap state:

- `aidd run --runtime generic-cli` performs workflow execution;
- `aidd run --runtime <non-generic>` prints the runtime gate notice and does not execute workflow stages;
- `aidd stage run --runtime generic-cli` performs stage execution;
- `aidd stage run --runtime <non-generic>` returns a runtime gate error;
- `aidd eval run` executes the harness lifecycle and prints status, run id, and bundle paths.

## 7. Operational Notes

- Prefer absolute paths for config and workspace roots in automation scripts.
- Treat `doctor` output as the canonical machine-readiness snapshot before live scenario work.
- Record the exact command outputs for reproducible environment triage.
- Keep runtime authentication state and secrets outside the repository.

## 8. Related References

- [README](../README.md)
- [Distribution and Development](./architecture/distribution-and-development.md)
- [Target Architecture](./architecture/target-architecture.md)
- [Adapter Protocol](./architecture/adapter-protocol.md)
