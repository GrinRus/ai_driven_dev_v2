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
- live scenarios under `harness/scenarios/live/` prepare a pinned public-repository working copy, install a local AIDD wheel via `uv tool`, and run installed `aidd` from the target repository root.
- tagged releases additionally verify one published-package live scenario on `AIDD-LIVE-005` with the deterministic `generic-cli` release-proof runtime.

Smoke, conformance, and live operator proof are separate lanes. Do not treat them as interchangeable.

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

By default, `aidd doctor` and other commands look for `aidd.example.toml`.
In a source checkout, that file lives at the repository root as an example config.
Installed operator flows may omit it entirely and rely on defaults or an explicit `--config`.

Use this as the base operator config template:

```toml
[workspace]
root = ".aidd"

[runtime.generic_cli]
command = "python"

[runtime.claude_code]
command = "claude"

[runtime.codex]
command = "codex"

[runtime.opencode]
command = "opencode"

[logging]
mode = "both"

[repair]
max_attempts = 2
```

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
- live `aidd eval run` installs a local wheel with `uv tool`, enters the pinned target repository, and keeps `.aidd/` inside that repository.
- tagged-release live proof installs the published package via `uv tool` and runs `AIDD-LIVE-005` with the release-proof `generic-cli` runtime helper.

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
