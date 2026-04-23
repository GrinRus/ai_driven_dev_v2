# Operator Handbook

## 1. Purpose

This handbook describes the current operator path for installing, configuring, and running the first commands of `ai_driven_dev_v2` (AIDD).

Use it when you need a repeatable local setup for:

- checking runtime availability;
- initializing a work item workspace;
- running workflow, stage, and eval lanes with durable artifacts.

## 2. Scope and Current Product State

As of April 23, 2026:

- `aidd doctor` probes configured runtimes and capability flags;
- `aidd init` bootstraps workspace documents for a work item;
- `aidd run` executes a workflow window through the orchestrator;
- `aidd stage run` executes a single stage through the same orchestration APIs;
- `aidd eval run` executes a harness scenario and writes eval verdict artifacts.

## 3. Prerequisites

Required:

- Python 3.12+
- `uv`

Optional:

- runtime CLIs you want to run (for example `claude`, `codex`, `opencode`, `pi-mono`)

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

[runtime.codex]
command = "codex"

[runtime.opencode]
command = "opencode"

[runtime.pi_mono]
command = "pi-mono"

[logging]
mode = "both"

[repair]
max_attempts = 2
```

Current config fields consumed by the CLI:

- `workspace.root`
- `runtime.generic_cli.command`
- `runtime.claude_code.command`
- `runtime.codex.command`
- `runtime.opencode.command`
- `runtime.pi_mono.command`
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

### 6.3 Prepare minimum stage inputs

`aidd run` and `aidd stage run` validate required stage inputs. Before first execution,
prepare the context files required by your selected stage window.

Minimum example for `idea`:

```bash
cat > .aidd/workitems/WI-001/context/intake.md <<'EOF'
# Intake

Ship runtime-agnostic execution.
EOF

cat > .aidd/workitems/WI-001/context/user-request.md <<'EOF'
# User request

Need reproducible stage output validation.
EOF
```

### 6.4 Inspect generated workspace artifacts

Recommended quick checks:

```bash
find .aidd -maxdepth 4 -type f | sort | head -n 40
```

Verify that:

- work item directories were created;
- stage document scaffolding exists;
- initialization is repeatable and deterministic for operator use.

### 6.5 Execute workflow, stage, and eval lanes

```bash
uv run aidd run --work-item WI-001 --runtime generic-cli --stage-start idea --stage-target idea
uv run aidd stage run idea --work-item WI-001 --runtime generic-cli
uv run aidd eval run harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex
```

Expected behavior:

- `run` and `stage run` execute orchestration, validation, and repair/interview transitions;
- `eval run` executes harness setup/run/verify/teardown and writes summary/verdict/grader artifacts.

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
