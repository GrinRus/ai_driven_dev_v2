# ai_driven_dev_v2

Runtime-agnostic orchestration for document-first AI software delivery.

AIDD runs a governed staged workflow over a local project. It asks a runtime such as
Claude Code, Codex, OpenCode, or a generic CLI to produce Markdown stage artifacts, then
validates those artifacts before the workflow can advance.

The canonical stage flow is:

```text
idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa
```

## Alpha status and safety

Latest published prerelease: `0.1.0a11`, superseded by the current
`0.1.0a12` hotfix candidate for raw-log CLI rendering.
Current release-candidate package version on this branch: `0.1.0a12`.
Latest accepted published prerelease evidence before this candidate: `0.1.0a10`.
The `main` branch is development source and may contain unreleased changes.
Release-candidate source checkouts are not accepted package-channel evidence until the
GitHub Release, PyPI publish, `pipx`, and `uv tool` verification jobs succeed.

AIDD is alpha software for local evaluation and controlled operator trials. It is not
ready for unattended production automation. AIDD launches external runtime CLIs against a
local working tree; review runtime commands before execution and prefer a disposable branch,
workspace, or sandboxed checkout for trials.

Beta-readiness work on `main` is a preparation gate, not a production-readiness claim.
Before any beta-oriented release note is published, maintainers must confirm that the README,
main user stories, and target architecture still match the code, deterministic release checks
pass, and manual live evidence is refreshed outside CI/CD.

Do not commit `.aidd/` unless your repository policy explicitly allows it. The workspace can
contain raw runtime logs, prompts, repository context, operator answers, and other sensitive
evidence.

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

## Install with pipx

Install the latest accepted published prerelease:

```bash
pipx install "ai-driven-dev-v2==0.1.0a10"
aidd --version
aidd doctor
```

## Install with uv tool

Install the latest accepted published prerelease:

```bash
uv tool install "ai-driven-dev-v2==0.1.0a10"
aidd --version
aidd doctor
```

## Container support

AIDD does not publish or support Docker/GHCR images during the alpha phase.
The supported alpha installation paths are PyPI via pipx, uv tool, and source checkout.

Container support may be reconsidered after the runtime permission model, release
provenance, and operator workflows stabilize.

Beta readiness is a future evidence gate, not a current alpha claim. It requires fresh
install evidence, clean UI onboarding, real-provider UI smokes, Browser-verified operator
states, project-set boundaries, remediation, provenance, approval audit, and release
evidence.

## Source checkout

```bash
git clone https://github.com/GrinRus/ai_driven_dev_v2.git
cd ai_driven_dev_v2
uv sync --locked --extra dev
uv run aidd --version
uv run aidd doctor
```

The latest published prerelease is `v0.1.0a11`, but it is superseded by the
current `v0.1.0a12` hotfix candidate for `aidd run logs` raw-log rendering.
Use the pinned `pipx` or `uv tool` install commands above when you need the
latest accepted package-channel behavior before `v0.1.0a12` release evidence
is accepted.

## Run your first local workflow

Start from the local project root that should receive AIDD workflow state:

```bash
cd /path/to/local-project
aidd ui
```

The UI opens setup mode when no work item is provided. Use it to confirm the local project
root, create or resume a work item, seed the request, inspect runtime readiness, select a
runtime, and start the governed flow. The UI still writes the same project-local `.aidd/`
workspace as the CLI and still requires explicit runtime selection before execution.

Scripted and terminal-first flows remain supported:

```bash
cd /path/to/local-project
aidd doctor
aidd init --work-item WI-001 --request "Implement a small, specific task" --root .aidd
aidd run --work-item WI-001 --runtime codex --from-stage idea --to-stage plan --root .aidd
aidd run show --work-item WI-001 --root .aidd
```

This creates `.aidd/` inside the local project and seeds the required intake context
documents for the first stage. Treat `.aidd/` as project-local operator state that may
include sensitive raw runtime logs, prompts, repository context, questions, answers, and
validation evidence.

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
| `generic-cli` | Python | `adapter-flags` | Advanced AIDD-compatible wrapper and deterministic checks |
| `claude-code` | Authenticated `claude` CLI | `native` | Claude Code-backed workflow runs |
| `codex` | Authenticated `codex` CLI | `native` | Codex-backed workflow runs and live evals |
| `opencode` | Authenticated `opencode` CLI | `native` | OpenCode-backed workflow runs and live evals |
| `qwen` | Authenticated `qwen` CLI | `native` | Experimental Qwen Code workflow runs |

Product workflow and stage execution require an explicit runtime id:

```bash
aidd run --work-item WI-001 --runtime codex --root .aidd
aidd stage run plan --work-item WI-001 --runtime opencode --root .aidd
```

Codex, OpenCode, Qwen, and Claude Code default to native provider CLI execution.
`generic-cli` is not the default product onboarding runtime; use it when you
intentionally configure an AIDD-compatible wrapper command with `mode = "adapter-flags"`
for a deterministic or custom execution surface.

Unknown runtime ids fail fast with `unsupported-runtime` classification.

## Inspect artifacts and logs

AIDD stores workflow evidence under `.aidd/`:

```bash
aidd run show --work-item WI-001 --root .aidd
aidd run logs --work-item WI-001 --stage plan --root .aidd
aidd run artifacts --work-item WI-001 --stage plan --root .aidd
aidd stage questions idea --work-item WI-001 --root .aidd
aidd stage interact plan --work-item WI-001 --runtime codex --request "Add rollback risks" --root .aidd
```

Stage documents, runtime logs, validator reports, repair briefs, questions, and answers
remain ordinary files in the local workspace. The core treats Markdown documents as the
contract surface; runtime-authored JSON schemas are not the primary stage output format.
When a CLI stage stops on questions, inspect them with `aidd stage questions`, write
answers to `.aidd/workitems/<work-item>/stages/<stage>/answers.md`, and rerun the stage
with `aidd stage run <stage> --work-item <id> --runtime <runtime> --root .aidd`.
When a stage artifact needs a scoped correction or additional analysis, use
`aidd stage interact <stage>` with `--request` or `--request-file`; AIDD stores the
operator request under `operator-requests/request-000N.md` and runs a normal validated
stage attempt in the current run.

## Operator UI

Start setup mode for a local project, or open an initialized work item directly:

```bash
aidd ui
aidd ui --work-item WI-001 --root .aidd
```

Without `--work-item`, the UI validates the selected project root, resolves `.aidd/`,
discovers existing work items, and creates new work items through the same bootstrap path as
`aidd init`. With `--work-item`, it opens the existing command center directly.

The UI reads the same `.aidd/` state as the CLI. It can show stage status, render stage
Markdown artifacts, show runtime logs, answer questions, show repair history, submit
stage-scoped operator intervention requests, and display runtime readiness details without
introducing a separate workflow engine. Operators can run the full workflow, run or resume
the next eligible stage, run the active stage with **Run selected stage**, or submit
**Request change -> Submit & run** from the selected
stage cockpit; these actions require an explicit runtime selection and there is no hidden
`generic-cli` fallback. New UI launches stream live job logs while the process runs, and
the saved `runtime.log` remains available afterward through the normal log view and CLI.
Successful UI jobs report `/api/jobs/<job_id>` status `completed`; successful stage
progress remains visible as stage state `succeeded` in the rail and artifacts.
The command center also shows an Active Run panel and Timeline tab for long-running jobs:
elapsed time, last output age, runner command, stage timeout summary, cancel action, and
real stage milestones are shown without fake progress percentages.
The UI can write question answers as `[resolved]`, `[partial]`, or `[deferred]` entries
in the standard `answers.md`; only `[resolved]` answers unblock blocking questions, then
rerun the selected stage or workflow after answering. Intervention requests are stored as
durable Markdown input under `.aidd/workitems/<id>/stages/<stage>/operator-requests/`
and are shown in Activity, Evidence Refs, and Recent Artifacts. The UI is a local no-auth
operator surface: the default host is loopback, and non-loopback binds print a warning.

For `implement`, the **Implement Review** tab shows the real project repository diff,
including untracked files, deleted files, bounded diff hunks, `.aidd/` artifacts separated
from source files, allowed-scope status, and mismatches between changed files and
`implementation-report.md`. For `review` and `qa`, structured tabs surface findings,
approval status, QA verdict, residual risks, known issues, and evidence ids. Selected
review findings or QA risks can be sent back to `implement` as a durable remediation
request; the UI then marks downstream `review` and `qa` stale until the operator explicitly
reruns `review -> qa` with a selected runtime. CLI behavior remains document/validator
driven and does not get new default gates from these UI controls.

After terminal `qa`, the command center switches to **Flow Complete**. The completed-run
handoff shows final QA status, final artifacts, blockers, repair counts, approval counts,
answered questions, recommended next-flow actions, and source-run lineage. Operators can
create a new work item, start a follow-up flow, clone the previous flow, hand off to an
eval / scenario batch, or archive the run. Follow-up and clone actions create new
independent work item or run identities with source-run references; archive records local
operator intent without deleting artifacts or mutating the completed source run.

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
- operator intervention requests are persisted as stage-scoped Markdown input and
  validated through the normal stage chain;
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
uv sync --locked --extra dev
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

AIDD includes deterministic harness checks and manual live E2E scenarios. Live E2E is
manual local operator audit evidence, not CI/CD, not a release workflow, not GitHub Actions,
and not a release gate. CI, security, and release workflows must not run live scenarios,
require provider credentials, or depend on public live target repositories.

Example black-box live E2E evaluator command:

```bash
uv run python -m aidd.harness.live_e2e_black_box harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime codex --work-root /tmp/aidd-live-e2e --report-root .aidd/reports/evals
```

Manual live E2E scenarios snapshot tracked AIDD `HEAD` into
`${TMPDIR:-/tmp}/aidd-live-e2e/<run_id>/source/aidd`, build and install through an
isolated `uv tool` home/cache, clone the pinned target repository under
`<work-root>/<run_id>/target/<repo-slug>`, run from the target repository root,
execute each stage through public `aidd stage run` and inspection commands plus
loopback `aidd ui` UI/API checkpoints, write `stage-audits/<stage-run-id>.json`
and `.md` per-stage-run audits, write `target-workspace-evidence.json` / `.md` with
non-gating target diff and workspace-pollution evidence, and preserve durable execution bundles under
`.aidd/reports/evals/`. Live manifest `limits.timeout_minutes` is a per-stage
command budget; aggregate `run-transcript.json` does not report a global timeout
unless the runner actually uses one. The runner does not score deliverable quality or create a
quality report; for product-evaluation runs the launching SWE agent writes
`stage-quality-audits/<stage-run-id>.md` before each resume and may write
`.aidd/reports/evals/<run_id>/quality-report.md` manually after the terminal run,
including iteration history and a human-authored AIDD operator UI/UX decision when
that quality dimension must be judged.
When successful manifest verification creates only new known ignored byproducts
after QA, the runner records `verify-transcript.json.workspace_cleanup` and removes
that verification residue before final target workspace evidence. This is execution
hygiene, not a quality gate.
Manual review should inspect `target-workspace-evidence.*` and, when needed, cite
`git status --short --untracked-files=all`; top-level `workitems/...` duplicates
are severe deliverable pollution, while `aidd.example.toml` is harness config rather
than product diff. New ignored files inside a setup-baseline ignored root, such as
`.venv/.../__pycache__`, are recorded as setup-baseline ignored churn rather than
pollution findings.
The evaluator always builds a local wheel from the clean tracked source checkout
containing the scenario manifest. Published-package install proof is a separate
release/install evidence lane, not part of public-repository live E2E.

Public GitHub repositories are live E2E targets for evaluator evidence only. See:

- `docs/e2e/live-e2e-catalog.md`
- `docs/e2e/scenario-matrix.md`
- `harness/scenarios/live/`

Release and install evidence for PyPI, `pipx`, and `uv tool` is recorded in
`docs/release-checklist.md`. Docker/GHCR is intentionally outside the alpha release
contract.

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

## Security and support

Use `SECURITY.md` for vulnerability reporting and `SUPPORT.md` for operator support scope.
Do not file public issues containing secrets, private repository contents, provider logs, or
tokens. Release notes and user-visible changes are tracked in `CHANGELOG.md`.

## License

This project is licensed under the Apache License 2.0. See `LICENSE`.
