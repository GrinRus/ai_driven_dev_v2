# Operator Handbook

## 1. Purpose

This handbook describes the current operator path for installing, configuring, and running the first commands of `ai_driven_dev_v2` (AIDD).

Use it when you need a repeatable local setup for:

- checking runtime availability;
- initializing a work item workspace;
- running AIDD from a target local project root;
- validating the baseline toolchain before deeper scenario work;
- understanding the installed live E2E operator path.

## 2. Scope and Current Product State

AIDD has an implemented local CLI, stage orchestration core, maintained runtime adapters,
validators, and harness/eval tooling. Live public-repository E2E remains a manual installed
operator audit lane, not a CI or release gate.

Today:

- `aidd doctor` is functional;
- `aidd init` is functional and can seed first-stage intake context from `--request` or `--request-file`;
- `aidd run` executes workflow progression for `generic-cli`, `claude-code`, `codex`, and `opencode`;
- `aidd stage run` executes stage orchestration for `generic-cli`, `claude-code`, `codex`, and `opencode`;
- `python -m aidd.harness.live_e2e_black_box` executes the manual black-box
  live E2E evaluator and writes a result bundle;
- live scenarios under `harness/scenarios/live/` are a manual external-audit lane:
  they prepare a pinned public-repository working copy, install a local AIDD wheel via
  `uv tool`, and drive installed `aidd` from the target repository root through public
  stage and inspection commands.

Smoke, conformance, and live operator proof are separate lanes. Do not treat them as interchangeable.

The supported product path is local-project operation: install or run AIDD locally,
enter the target project root, create `.aidd/` there, and inspect artifacts from
that same project. `aidd init --github-issue <url>` is out of product scope.
Public GitHub repositories are used by live E2E eval manifests and support evidence,
not by a product issue-intake command.

For local manual live audits, Codex, OpenCode, and Claude Code use native provider
commands by default. A locally available command override is optional when the operator
wants a custom wrapper:

- `AIDD_EVAL_CODEX_COMMAND`
- `AIDD_EVAL_OPENCODE_COMMAND`
- `AIDD_EVAL_CLAUDE_CODE_COMMAND`

Those values should point to wrapper commands that accept the AIDD adapter flags;
when they are unset, the harness validates the default native provider command.

## 3. Prerequisites

Required:

- Python 3.12+
- `uv`

Optional:

- runtime CLIs you want to probe in `aidd doctor` (for example `claude`, `codex`, `opencode`)
- provider auth for the runtimes you want to execute
- AIDD-compatible wrapper commands for advanced `adapter-flags` execution mode

Runtime binaries are external dependencies and are not bundled by AIDD.

## 4. Installation (Source Checkout)

From a repository checkout root:

```bash
uv sync --locked --extra dev
uv run aidd --help
```

Recommended baseline verification:

```bash
uv run --extra dev ruff check .
uv run --extra dev python -m mypy src
uv run --extra dev pytest -q
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
mode = "adapter-flags"

[runtime.claude_code]
command = "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
mode = "native"
# Optional per-attempt runtime subprocess budget.
# timeout_seconds = 1200

# Optional stage-specific overrides. Stage values take precedence over
# runtime.<provider>.timeout_seconds.
# [runtime.claude_code.stage_timeouts]
# research = 1500
# tasklist = 1800
# implement = 1800
# review = 1800
# qa = 1800

[runtime.codex]
command = "codex exec --full-auto --skip-git-repo-check --json -"
mode = "native"
# timeout_seconds = 900

[runtime.opencode]
command = "opencode run --format json --dangerously-skip-permissions"
mode = "native"
# timeout_seconds = 900

[logging]
mode = "both"

[repair]
max_attempts = 2
```

Claude Code, Codex, and OpenCode native mode adapt AIDD stage briefs and prompt
packs to the raw provider CLI. Use `mode = "adapter-flags"` only for wrapper
commands that accept AIDD adapter flags directly.

OpenCode native mode can report `document_complete` when it has written the declared
Markdown outputs and then keeps the provider process open instead of returning a final
message. AIDD still preserves the raw log and runtime exit metadata and still runs canonical
stage validation before any workflow progression. For initial interview stops, a settled
`questions.md` plus terminal stage documents may complete the adapter call while `answers.md`
is still waiting for operator or harness-provided answers.

Current config fields consumed by the CLI:

- `workspace.root`
- `runtime.generic_cli.command`
- `runtime.claude_code.command`
- `runtime.codex.command`
- `runtime.opencode.command`
- `runtime.<provider>.mode`
- `runtime.<provider>.timeout_seconds`
- `runtime.<provider>.stage_timeouts.<stage>`
- `logging.mode`
- `repair.max_attempts`

## 6. First-Run Procedure

Run product commands from the target local project root, not from the AIDD source
checkout, unless the source checkout is also the project under test. If AIDD is
not installed globally, prefix each command with:

```bash
uv tool run --from /path/to/ai_driven_dev_v2 aidd
```

### 6.1 Probe local environment

```bash
aidd doctor --config /path/to/aidd.example.toml
```

Confirm:

- the expected config path is loaded;
- workspace root is correct;
- each runtime availability result matches your machine state.
- the command is being executed from the intended local project root.

### 6.2 Initialize a work item workspace

```bash
aidd init --work-item WI-001 --request "Implement a small, specific task" --root .aidd
```

This creates the `.aidd/` workspace tree inside the current local project and
adds stage document scaffolding plus the first-stage context documents:

- `.aidd/workitems/WI-001/context/intake.md`
- `.aidd/workitems/WI-001/context/user-request.md`
- `.aidd/workitems/WI-001/context/repository-state.md`

Use `--request-file <path>` when the operator request already lives in a file. Existing
generated context docs are preserved by default; pass `--force-context` only when you
intentionally want to overwrite `intake.md`, `user-request.md`, and `repository-state.md`.

Running `aidd init` without a request still initializes the workspace tree, but the work
item is not runnable until the intake context exists.

### 6.3 Inspect generated workspace artifacts

Recommended quick checks:

```bash
find .aidd -maxdepth 4 -type f | sort | head -n 40
```

Verify that:

- work item directories were created;
- stage document placeholders exist;
- initialization is repeatable and deterministic for operator use.
- `.aidd/` is rooted inside the local project, not beside it.

### 6.4 Validate execution surfaces

```bash
aidd run --work-item WI-001 --runtime codex --root .aidd --config /path/to/aidd.example.toml
aidd run --work-item WI-001 --runtime claude-code --root .aidd --config /path/to/aidd.example.toml
aidd stage run plan --work-item WI-001 --runtime opencode --root .aidd --config /path/to/aidd.example.toml
aidd ui --work-item WI-001 --root .aidd --config /path/to/aidd.example.toml
```

Expected behavior in the current local implementation:

- `aidd run --runtime <maintained-runtime>` performs workflow execution through the selected adapter;
- `aidd run` and `aidd stage run` require an explicit `--runtime`;
- `aidd ui` also requires the operator to select a runtime in the browser before
  launching a workflow or selected stage; the UI does not silently default to `generic-cli`;
- the UI **Run workflow** action requests full workflow progression, while **Run selected
  stage** uses the same single-stage semantics as `aidd stage run <stage>`;
- `aidd stage run --runtime <supported-non-generic>` executes through the corresponding adapter path;
- `generic-cli` is an advanced wrapper/test lane, not the default product onboarding runtime;
- `python -m aidd.harness.live_e2e_black_box` executes the black-box evaluator
  lifecycle and prints status, run id, and bundle paths;
- live black-box E2E is a manual external audit that installs a local wheel with
  `uv tool`, enters the pinned target repository, and keeps `.aidd/` inside that
  repository while invoking only public AIDD CLI surfaces.
- live eval bundles include `stage-timing.json`, `stage-timing.md`, `self-repair-matrix.json`,
  and `self-repair-matrix.md` for per-step duration, deterministic repair-probe coverage,
  and terminal document consistency audit.
- repair retries persist `repair-context.md` in the run attempt directory, which lets
  operators trace the exact validator findings that caused each retry.
- live E2E is manual local operator audit evidence, not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- local live E2E uses native provider commands by default and reads runtime-command
  environment overrides only when an adapter-compatible wrapper override is needed.
- published-package live evals use `AIDD_EVAL_PUBLISHED_PACKAGE_SPEC`, for example
  `AIDD_EVAL_PUBLISHED_PACKAGE_SPEC="ai-driven-dev-v2==0.1.0a5" uv run python -m aidd.harness.live_e2e_black_box ...`;
  local-wheel live evals require the scenario manifest to live in, or be run from, an
  AIDD source checkout.

### 6.5 Inspect logs and artifacts

Use either the local UI or CLI read commands:

```bash
aidd run show --work-item WI-001 --root .aidd
aidd run logs --work-item WI-001 --stage plan --root .aidd
aidd run artifacts --work-item WI-001 --stage plan --root .aidd
aidd stage questions plan --work-item WI-001 --root .aidd
```

The UI uses the same `.aidd/` root:

```bash
aidd ui --work-item WI-001 --root .aidd --config /path/to/aidd.example.toml
```

The CLI does not post answers through a separate command in this release. When a stage
is blocked, use `aidd stage questions <stage>` to locate the standard question and answer
documents, write resolved answers to
`.aidd/workitems/<work-item>/stages/<stage>/answers.md`, then rerun
`aidd stage run <stage> --work-item <id> --runtime <runtime> --root .aidd`.

In the UI, answer unresolved questions in the **Questions** tab. The browser writes
`[resolved]` answers to the same `answers.md`; use **Run selected stage** or **Run
workflow** after answering. Partial and deferred answer states remain file-mode CLI
semantics for this release.

During a UI-triggered run, the **Logs** tab follows the in-memory job stream from the
runtime stdout/stderr callbacks. After completion, `aidd run logs` and the UI persisted
log view read the durable attempt `runtime.log`. The **Artifacts** tab renders known
stage document keys from the artifact index as read-only Markdown preview/source views;
it does not allow arbitrary path reads.

The local UI has no authentication in this release. The default bind host is
`127.0.0.1`; binding to `0.0.0.0`, a LAN address, or another non-loopback host is
allowed for local operator experiments but prints a warning and should not be used
on an untrusted network. The private JSON API rejects oversized request bodies and
malformed JSON, but it is still a local operator surface rather than a hardened
multi-user web service.

Keep generated `.aidd/` state inside the local project. Do not move it into the
AIDD source checkout or commit it unless the target repository has its own policy
for committed operator artifacts.

### 6.6 Product scope boundary

There is no supported `aidd init --github-issue <url>` product command. GitHub
issue URLs may appear in historical live E2E reports or support reports, but current
live E2E manifests use authored tasks and `feature-selection.json`; GitHub issues are
not a local operator intake surface.

## 7. Operational Notes

- Prefer absolute paths for config and workspace roots in automation scripts.
- Treat `doctor` output as the canonical machine-readiness snapshot before live scenario work.
- Record the exact command outputs for reproducible environment triage.
- For live E2E, distinguish the AIDD artifact root from the target repository cwd.
- For local product operation, keep `.aidd/` inside the target local project root.
- Keep runtime authentication state and secrets outside the repository.

## 8. Related References

- [README](../README.md)
- [Distribution and Development](./architecture/distribution-and-development.md)
- [Target Architecture](./architecture/target-architecture.md)
- [Adapter Protocol](./architecture/adapter-protocol.md)
