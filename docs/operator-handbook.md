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
- `aidd run` executes workflow progression for `generic-cli`, `claude-code`, `codex`, `opencode`, and experimental `qwen`;
- `aidd stage run` executes stage orchestration for `generic-cli`, `claude-code`, `codex`, `opencode`, and experimental `qwen`;
- `aidd stage interact` records a stage-scoped operator request and runs an
  intervention attempt in the current run through the same adapter boundary;
- `aidd ui` opens local setup mode or the command center with explicit runtime selection,
  long-run visibility, Implement Review diff, structured review/QA tabs, and
  review/QA remediation back to `implement`;
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

For UI-first real-provider smokes, use the manual
[`Real-Provider UI E2E Lane`](./e2e/real-provider-ui-e2e.md). That lane starts with
`codex`, then repeats the same clean `aidd ui` onboarding path for `claude-code`,
`opencode`, and optional experimental `qwen` when local auth is available. Missing
runtime binaries, missing auth, provider quota, and local config problems are recorded as
`auth/env` blockers rather than AIDD defects.

## 3. Prerequisites

Required:

- Python 3.12+
- `uv`

When `uv` is not on `PATH`, launch source-checkout commands through an absolute
`uv` path. The live local-wheel installer honors the `UV` environment value that
`uv run` provides, so the black-box installer can still build and install the
tracked `HEAD` artifact without relying on a shell PATH lookup.

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
# permission_policy = "full-access" # full-access | brokered | plan | deny-unapproved
# interaction_mode = "batch"        # batch | evented | live
# auto_approval_preset = "broad"    # off | conservative | broad
# Optional per-attempt runtime subprocess budget.
# timeout_seconds = 3600

# Optional stage-specific overrides. Stage values take precedence over
# runtime.<provider>.timeout_seconds.
# [runtime.claude_code.stage_timeouts]
# idea = 3600
# research = 3600
# plan = 3600
# review-spec = 3600
# tasklist = 3600
# implement = 3600
# review = 3600
# qa = 3600

[runtime.codex]
command = "codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json -"
mode = "native"
# timeout_seconds = 3600

[runtime.opencode]
command = "opencode run --format json --dangerously-skip-permissions"
mode = "native"
# timeout_seconds = 3600

[runtime.qwen]
command = "qwen --approval-mode yolo --output-format stream-json"
mode = "native"
# timeout_seconds = 3600

[logging]
mode = "both"

[repair]
max_attempts = 2
```

Claude Code, Codex, and OpenCode native mode adapt AIDD stage briefs and prompt
packs to the raw provider CLI. Use `mode = "adapter-flags"` only for wrapper
commands that accept AIDD adapter flags directly.

OpenCode and Qwen native modes can report `document_complete` when they have written the
declared Markdown outputs and then keep the provider process open instead of returning a final
message. AIDD still preserves the raw log and runtime exit metadata and still runs canonical
stage validation before any workflow progression. For initial interview stops, a settled
`questions.md` plus terminal stage documents may complete the adapter call while `answers.md`
is still waiting for operator or harness-provided answers.

If the native OpenCode CLI emits a structured provider API error payload but exits `0`,
AIDD classifies the attempt as `provider_error`, preserves the raw runtime log, and stops
the stage before spending repair attempts on missing model-authored documents.

For `permission_policy = "brokered"` with `auto_approval_preset = "broad"`,
AIDD intentionally allows normal reads and writes inside the local `.aidd/`
workspace. That includes stage documents, reports, runtime logs, metadata, and
attempt artifacts under `.aidd/workitems/...` and `.aidd/reports/...`, even on
early stages. It still does not auto-approve `.env*`, credentials, secrets,
tokens, provider auth/config files, approval ledgers
(`operator-requests.jsonl`, `operator-decisions.jsonl`), AIDD repair control
files such as `repair-brief.md`, file deletes, network/package/publish/git push
actions, or destructive shell commands.

The same broad preset can approve project-local shell verification when the
runtime request runs inside a declared project root and does not include an
unsafe marker. Typical local inspect/test commands such as `git status`,
`.venv/bin/python`, `python -m pytest`, `pytest`, and `uv run pytest` can
proceed without a manual approval. Commands that install packages, access
network URLs, mutate git history or remotes, publish releases, delete files, or
reference paths outside the declared roots remain operator-gated or denied.

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

### 6.1 Start UI onboarding

The recommended first-run path is the local UI setup mode:

```bash
cd /path/to/local-project
aidd ui
```

Setup mode opens before a work item exists. It validates the selected local project root,
resolves the project-local `.aidd/` workspace, discovers existing work items, creates or
resumes a work item, seeds the operator request, shows runtime readiness, and requires the
operator to select a runtime before any workflow or stage execution starts. It uses the
same workspace creation and request seeding behavior as `aidd init`; it does not
introduce a second workflow engine or a hidden `generic-cli` fallback.

After setup completes, the first command-center screen exposes both **Run workflow** for
normal full progression and **Run selected stage** for a bounded active-stage smoke or
retry. Successful UI jobs report `/api/jobs/<job_id>` status `completed`; the stage rail
reports the completed stage state as `succeeded`.

Bare `aidd`, `aidd --help`, and scripted subcommands keep their existing CLI behavior. Use
the CLI steps below when you need a terminal-first or scripted setup.

### 6.2 Probe local environment

```bash
aidd doctor --config /path/to/aidd.example.toml
```

Confirm:

- the expected config path is loaded;
- workspace root is correct;
- each runtime availability result matches your machine state.
- the command is being executed from the intended local project root.

### 6.3 Initialize a work item workspace from the CLI

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

### 6.4 Inspect generated workspace artifacts

Recommended quick checks:

```bash
find .aidd -maxdepth 4 -type f | sort | head -n 40
```

Verify that:

- work item directories were created;
- stage document placeholders exist;
- initialization is repeatable and deterministic for operator use.
- `.aidd/` is rooted inside the local project, not beside it.

### 6.5 Validate execution surfaces

```bash
aidd run --work-item WI-001 --runtime codex --root .aidd --config /path/to/aidd.example.toml
aidd run --work-item WI-001 --runtime claude-code --root .aidd --config /path/to/aidd.example.toml
aidd stage run plan --work-item WI-001 --runtime opencode --root .aidd --config /path/to/aidd.example.toml
aidd stage interact plan --work-item WI-001 --runtime codex --request "Add rollback risks" --root .aidd --config /path/to/aidd.example.toml
aidd ui --root .aidd --config /path/to/aidd.example.toml
aidd ui --work-item WI-001 --root .aidd --config /path/to/aidd.example.toml
```

Expected behavior in the current local implementation:

- `aidd run --runtime <maintained-runtime>` performs workflow execution through the selected adapter;
- `aidd run`, `aidd stage run`, and `aidd stage interact` require an explicit `--runtime`;
- `aidd ui` also requires the operator to select a runtime in the browser before
  launching a workflow or selected stage; the UI does not silently default to `generic-cli`;
- the UI **Run workflow** action requests full workflow progression, while **Run selected
  stage** uses the same single-stage semantics as `aidd stage run <stage>`;
- the UI **Request change** panel uses the same durable intervention semantics as
  `aidd stage interact <stage>`;
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
- live eval bundles include `target-workspace-evidence.json` and `.md` as non-gating
  target repository evidence. Inspect it during manual quality review to separate tracked
  product diff, setup-baseline untracked files, `aidd.example.toml` harness config, top-level
  `workitems/...` pollution, stray `.aidd/` scratch files, and ignored local artifacts such
  as `.venv/`, `.pytest_cache/`, `.ruff_cache/`, `.pdm-build/`, `coverage/`, build, dist,
  or dependency caches. New ignored files inside an ignored root that already existed at setup,
  such as `.venv/.../__pycache__`, are setup-baseline ignored churn rather than
  pollution findings.
- live black-box `limits.timeout_minutes` is a per-stage `aidd stage run` command
  budget. The aggregate `run-transcript.json` keeps `timeout_seconds` as `null`
  unless there is a real global flow timeout, and records the per-stage policy
  under `timeout_policy`.
- live eval bundles are execution-only; write `quality-report.md` manually after
  the terminal run when artifact, code, test, or UI/UX quality must be judged.
  The UI/UX section is a human-authored AIDD operator UI decision, not a runner
  gate: inspect completed-flow visibility, stage/artifact/log/question navigation,
  repair and next-flow handoff states, readability, keyboard/focus behavior, and
  responsive behavior or explicitly record `not inspected`.
  For code/artifact quality, cite `target-workspace-evidence.*` or
  `git status --short --untracked-files=all` plus
  `git status --ignored --short --untracked-files=all`; top-level `workitems/...` duplicates
  normally make deliverable quality `not-counted`, while `aidd.example.toml` is
  harness config rather than product diff. If implementation evidence shows the prepared
  checkout or live harness directories such as `install-home/`, `source/`, `build/`, or
  `target/` were deleted/recreated, treat the deliverable as `not-counted`.
  When manifest verification creates only new known ignored residue after QA, inspect
  `verify-transcript.json.workspace_cleanup`; that runner cleanup is execution hygiene,
  not an automatic deliverable-quality decision.
- repair retries persist `repair-context.md` in the run attempt directory, which lets
  operators trace the exact validator findings that caused each retry.
- live E2E is manual local operator audit evidence, not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- local live E2E uses native provider commands by default and reads runtime-command
  environment overrides only when an adapter-compatible wrapper override is needed.
- public-repository live evals always build a local wheel from clean tracked `HEAD`;
  published-package install proof is recorded in the separate release/install lane.

### 6.6 Inspect logs and artifacts

Use either the local UI or CLI read commands:

```bash
aidd run show --work-item WI-001 --root .aidd
aidd run logs --work-item WI-001 --stage plan --root .aidd
aidd run artifacts --work-item WI-001 --stage plan --root .aidd
aidd stage questions plan --work-item WI-001 --root .aidd
aidd stage interact plan --work-item WI-001 --runtime codex --request-file request.md --root .aidd
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

When an operator needs a scoped correction or additional analysis on an existing stage
artifact, use `aidd stage interact <stage> --request "..."` or the UI **Request change**
tab. AIDD writes the request to
`.aidd/workitems/<id>/stages/<stage>/operator-requests/request-000N.md`, runs an
`intervention` attempt in the current run, and still gates the result through normal
validation. Stage-scoped intervention is for editing or rechecking the current stage.
When `review` or `qa` finds problems after `implement`, use the remediation flow below
instead of mutating downstream artifacts.

During a UI-triggered run, the **Logs** tab follows the in-memory job stream from the
runtime stdout/stderr callbacks. After completion, `aidd run logs` and the UI persisted
log view read the durable attempt `runtime.log`. The **Artifacts** tab renders known
stage document keys from the artifact index as read-only Markdown preview/source views;
it does not allow arbitrary path reads.

For long-running UI jobs, use the right-side **Active Run** panel and the **Timeline** tab.
They show job id, active stage, runner, elapsed time, last output age, stage timeout
summary, runner command, cancel action, live logs shortcut, and real milestones from
stage metadata, attempts, `events.jsonl`, repair history, questions, and artifacts. The
UI does not show fake percentage progress.

The local UI has no authentication in this release. The default bind host is
`127.0.0.1`; binding to `0.0.0.0`, a LAN address, or another non-loopback host is
allowed for local operator experiments but prints a warning and should not be used
on an untrusted network. The private JSON API rejects oversized request bodies and
malformed JSON, but it is still a local operator surface rather than a hardened
multi-user web service.

Keep generated `.aidd/` state inside the local project. Do not move it into the
AIDD source checkout or commit it unless the target repository has its own policy
for committed operator artifacts.

### 6.6.1 Implement review and review/QA remediation

After `implement`, use the UI **Implement Review** tab before moving to `review`.
It reads the selected project repository diff without mutating git state and separates:

- source file changes;
- `.aidd/` artifacts;
- untracked files;
- deleted or modified tracked files;
- bounded/truncated diff hunks;
- files mentioned in `implementation-report.md`;
- files changed but not mentioned;
- files mentioned but unchanged;
- allowed write scope status.

The **Review Findings** tab parses `review-report.md` into approval status and findings.
Use **Proceed to QA** only when the review status and validators allow it. If review is
`rejected` or contains unresolved `must-fix` findings, select the findings and choose
**Send selected to implement**.

The **QA Verdict** tab parses `qa-report.md` into quality verdict, release recommendation,
residual risks, known issues, and evidence ids. If QA is `not-ready`, select the relevant
risks or issues and send them back to `implement`. `ready-with-risks` remains an explicit
operator decision: accept the risk, create follow-up work, or remediate before final
handoff.

Remediation is durable and distinct from stage-scoped intervention. The UI writes
`.aidd/workitems/<id>/remediations/<run_id>/request-000N.md`, includes the latest request
as input to a new `implement` attempt, and requires a selected runtime. After the
remediation `implement` attempt succeeds, downstream `review` and `qa` are marked stale
as overlay metadata. Their canonical stage status is not rewritten, but stale `qa` is not
treated as a fresh terminal handoff. Use the next action **Rerun stale downstream** to
explicitly run `review -> qa` with a selected runtime.

### 6.7 Completed-run handoff and next-flow actions

When a run reaches terminal `qa`, the local UI command center switches to
**Flow Complete**. Treat this screen as the operator handoff point, not as a continuation
of the completed source run. The handoff summarizes final QA status, final artifacts,
open blockers, repair counts, approval counts, answered-question counts, recommended
next-flow actions, runtime/config context, and source-run lineage.

Available next-flow actions:

- **Create New Work Item**: start unrelated follow-on work from a new work item. Use this
  when the completed run is accepted and the next request does not need inherited
  findings.
- **Start Follow-up Flow**: select source findings from QA findings, review notes, failed
  evidence, or a manual operator request. AIDD creates a follow-up draft with editable
  title, acceptance criteria, required evidence, inherited-context toggles, first-stage
  input preview, and durable source-run references.
- **Clone This Flow**: create an editable cloned-flow draft that carries forward runtime
  id, prompt pack, contracts path, branch or commit, resources, and baseline references
  before launch. The clone gets a new run or work item identity.
- **Run Eval / Scenario Batch**: hand the completed source run and selected artifacts to
  eval or scenario planning. This is an operator handoff; it must not silently launch a
  nested public-repository live flow.
- **Archive Run**: record the local operator archive decision, timestamp, and reason.
  Archive does not delete artifacts, hide final QA evidence, or block read-only run
  history inspection.

Follow-up and cloned flows are independent child work items or runs. They reference the
source work item, source run id, selected source artifacts, and baseline metadata, but
they do not mutate the completed source run. Use Run History / Lineage to verify parent
run, current run, child work item candidates, archive state, and linked final artifacts.

Before launch, the next-flow preflight must show visible lineage and evaluate a writable
`.aidd/` workspace, explicit runtime selection, contracts availability, source-run
existence, and baseline availability. Blocking preflight results disable launch until
fixed; warning results may proceed only when the operator intentionally accepts the risk.

Keep the two evidence lanes distinct:

- Local-project UI evidence proves the product operator behavior: Flow Complete,
  Start Next Flow, follow-up draft creation, clone draft review, launch preflight,
  archive behavior, and Run History / Lineage inside the target local project.
- Public-repository live E2E records a terminal next-flow checkpoint after `qa`.
  It is manual audit evidence, not CI/CD. It does not require launching a second
  public-repository flow by default; the optional maintained-scenario follow-up proof
  creates draft lineage evidence only when the operator explicitly enables it.

### 6.8 Product scope boundary

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
