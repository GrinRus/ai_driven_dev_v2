# Agent development map

This map routes maintainer work to its owners, contracts, skills, and nearest useful checks.
Repository policy lives in [AGENTS.md](../AGENTS.md); reusable procedures live in
[.agents/skills/](../.agents/skills/). Runtime stage instructions live in `prompt-packs/stages/`
and are a separate surface from these maintainer instructions.

## Context and ownership

Read applicable `AGENTS.md` files cumulatively from root to leaf for each touched path. Read
the linked contract section and accepted local task, rather than loading whole architecture
or roadmap files. A nearer instruction overrides only a conflicting rule within its scope.
Compatibility pointers under `prompt-packs/<stage>/` lead to the canonical stage packs; they
do not define additional runtime prompts.

| Change area | Owner and context | Nearest verification |
| --- | --- | --- |
| Agent instructions and skills | `AGENTS.md`, `CLAUDE.md`, `.agents/skills/`; this map | `make check-agents`; inspect referenced paths and examples |
| Planning | `docs/backlog/roadmap.md`, `docs/backlog/backlog.md`; `backlog-ops` and `task-slicing` skills | `uv run --extra dev pytest -q tests/test_planning_integrity.py` |
| Core workflow, task state, workspace policy | `src/aidd/core/`; relevant section of `docs/architecture/target-architecture.md` | Matching `tests/core/` modules; add a deterministic scenario for workflow changes |
| Application composition and reconciliation | `src/aidd/application/`; core owns state semantics, application composes validation/publication | `tests/application/test_stage_reconciliation.py`, `tests/core/test_task_architecture.py`, and relevant CLI entrypoint tests |
| Runtime transport and capabilities | `src/aidd/adapters/`; `docs/architecture/adapter-protocol.md`, `docs/architecture/runtime-matrix.md` | Matching `tests/adapters/` modules; `tests/harness/test_adapter_conformance_lane.py` for protocol changes |
| Raw logs and normalized events | `src/aidd/runtime_logs/`, adapter capture, eval readers | `tests/adapters/test_runtime_log_capture.py`, matching `tests/evals/test_log_analysis_*.py` |
| Stage/document contracts and prompts | `contracts/`, `prompt-packs/stages/`, validators; `stage-contract-change` skill | Matching validator tests, `tests/test_prompt_quality.py`, `tests/test_contract_registry.py`, `tests/test_docs_consistency.py`, `tests/test_packaging_resources.py` |
| Validators | `src/aidd/validators/`; owning Markdown contract | Matching `tests/validators/` modules; contract examples and affected scenario/grader |
| CLI and local HTTP routes | `src/aidd/cli/`; `docs/architecture/operator-frontend.md`, operator handbook | Matching `tests/cli/` modules; route and workflow parity tests |
| Packaged UI behavior and assets | `src/aidd/cli/static/`, asset manifest, `tests/frontend/` | `make check-js`, matching `node --test tests/frontend/<file>.test.mjs`, relevant `browser_tests/` journey |
| Browser behavior, layout, accessibility | `browser_tests/`; `docs/architecture/operator-frontend.md` | `uv run --extra dev pytest -q browser_tests/<test_file>.py`; `make test-browser` for the packaged journey lane |
| Harness and grading | `src/aidd/harness/`, `src/aidd/evals/`, `harness/scenarios/`; `aidd-eval` and `runtime-log-triage` skills | Matching `tests/harness/` or `tests/evals/`; bounded deterministic scenario evidence |
| Maintainer scripts, packaging, CI, releases | `scripts/`, `pyproject.toml`, `.github/workflows/`; `release-publish` skill for release work | Relevant `tests/test_ci_workflow.py`, `tests/test_release_helpers.py`, `tests/test_release_workflow.py`, `tests/test_packaging_resources.py` |
| Product and operator docs | `docs/product/`, `docs/operator-handbook.md`, owning architecture contract; `user-story-check` skill | `tests/test_docs_consistency.py`; inspect the affected operator instructions |

Choose the relevant test module or test node from these entrypoints; a row is not a requirement
to run every named suite for a small change. Behavior changes need a test for the observable
result and, when appropriate, the matching scenario/grader. Do not replace a focused local
regression with a costly provider run.

## Local check commands

Install development dependencies with `uv sync --locked --extra dev`.

| Command | Coverage |
| --- | --- |
| `make check-agents` | Instruction links/paths, skill workflow examples, and planning integrity through the structural script and focused tests |
| `make lint` / `make typecheck` | Python Ruff and strict mypy across `src` and `scripts` |
| `make test` | Default Python suite in `tests/` |
| `make check-js` | Packaged JavaScript syntax through `scripts/check_packaged_javascript.py` |
| `make test-frontend` | Node DOM/state tests in `tests/frontend/` |
| `make check` | All preceding local lanes; browser journeys remain separate |
| `make test-browser` | Registered packaged UI journeys through `scripts/run_packaged_ui_scenarios.py` |

Node.js must be available for JavaScript checks. Browser checks additionally require Playwright
Chromium: `uv run --extra dev python -m playwright install chromium`. Linux environments may
also require `uv run --extra dev python -m playwright install-deps chromium`. These setup
commands are explicit prerequisites; the Makefile does not install them during a check.

The instruction checker validates Markdown links and explicit inline repository/skill paths.
It ignores fenced examples and generated runtime artifact paths. The focused
`tests/test_agent_instructions.py`, `tests/test_agent_workflows.py`, and
`tests/test_planning_integrity.py` tests complement that structural check with workflow examples
and planning invariants; passing a link check alone does not prove a runbook works.

The default `pytest -q` runs `tests/`, not `browser_tests/`. The packaged browser lane covers
registered journeys; select additional browser tests when the changed layout or interaction
falls outside those journeys. Local checks use deterministic fixtures and require no provider
authentication. Manual external evaluations use their separate skill and retain independent
evidence; they are not a prerequisite for ordinary instruction or documentation edits.

## Instruction and evidence maintenance

- Keep root policy short and stable. Add a nested `AGENTS.md` only for distinct local constraints;
  use a skill for a reusable procedure and this map for routing.
- Keep provider details in runtime configuration, profiles, adapters, or an accepted migration
  task. Shared maintainer rules and core semantics remain provider-independent.
- Update current normative docs when behavior changes. Preserve dated reports, run identifiers,
  repository pins, failures, and verification results as historical evidence. Add a dated
  correction or superseding link when needed; do not rewrite an old result as a new success.
- A final report names the changed outcome, checks actually performed, evidence inspected,
  and any unverified work. Existing authorization for a scoped action remains valid; analysis
  requests do not authorize implementation, publication, or release.
