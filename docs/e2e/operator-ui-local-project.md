# Operator UI Local-Project E2E Lane

This lane proves the local operator UI path. It is separate from the public-repository
live E2E catalog.

## Purpose

Operator UI E2E answers one question:

> Can an operator install or run AIDD locally, enter a local project root, open `aidd ui`,
> and inspect or continue a governed `.aidd/` work item without moving workflow state
> outside that project?

This lane does not use GitHub issue intake. Public GitHub repositories remain inputs for
manual live E2E evals only.

## Supported Operator Path

The local-project UI lane follows the product operator path:

1. Install or run AIDD locally.
2. Change into the target local project root.
3. Run `aidd doctor` with the intended config.
4. Run `aidd init --work-item <id> --request "<task>" --root .aidd`.
5. Run the workflow through `aidd run --runtime <runtime>` or continue through `aidd ui`.
6. Inspect logs and artifacts through the UI or `aidd run logs` / `aidd run artifacts`.
7. Keep `.aidd/` inside the local project root.

`aidd init --github-issue <url>` is out of product scope for this lane.

## Scope

The maintained operator UI lane covers:

- page load for the local UI shell;
- workflow-run request delegation through the same core service used by the CLI;
- blocking answer persistence to `answers.md`;
- runtime log rendering from attempt artifacts;
- artifact index rendering for stage documents and logs;
- validation visibility through validator pass/fail counts and validator report paths;
- repair-history visibility through `repair-brief.md` paths;
- declared project-set roots through `project-set.md` artifact visibility.

The lane is intentionally deterministic and service-level. It does not add a new harness
scenario class, and it does not start real provider runtimes in CI.

## Deterministic Coverage

Current deterministic coverage lives in:

- `tests/cli/test_ui.py::test_operator_ui_local_project_e2e_lane_covers_core_operator_flow`
- `tests/cli/test_ui.py::test_operator_ui_artifacts_include_declared_project_set_roots`
- `tests/core/test_operator_frontend.py`

These tests exercise `OperatorUiService` and the runtime-agnostic operator read/write
services directly. The workflow-run endpoint is tested through an injected workflow
service seam so it proves request shape and UI/Core delegation without invoking real
runtimes.

## Manual Installed Smoke

A manual installed UI smoke should use a disposable local fixture project:

1. Install or run the AIDD artifact under test locally.
2. Change into the local fixture project root.
3. Run `aidd doctor` with the fixture config.
4. Run `aidd init --work-item <id> --request "<task>" --root .aidd` so `.aidd/` and intake context are created inside the fixture project.
5. Seed request context with `--request` or `--request-file`, then execute a local deterministic work item through `aidd run --runtime <runtime>`.
6. Start `aidd ui --work-item <id> --root .aidd --host 127.0.0.1 --port <port>`.
7. Verify the page loads, `/api/workflow/run` is reachable, blocking answers persist,
   logs and artifacts render, validation state is visible, and repair evidence is linked.
8. Remove the disposable fixture project. Do not commit `.aidd/` artifacts.

Manual smoke evidence is recorded in `docs/backlog/roadmap.md`; generated `.aidd/`
state stays local to the fixture project.

## Source-Install Fixture Smoke

`harness/scenarios/smoke/installed-local-project-fixture.yaml` records the
source-install smoke path for local projects. It uses the existing
`harness/fixtures/minimal-python` fixture as the target project and keeps the
execution cwd as that fixture root.

The scenario uses `uv tool run --from /path/to/ai_driven_dev_v2 aidd` to model
installing or running AIDD from repository source. Operators replace
`/path/to/ai_driven_dev_v2` with the source checkout under test. The target
project remains the local fixture; public GitHub repositories and GitHub issue
URLs are not inputs.

The smoke path covers:

- `aidd doctor` against the fixture config;
- `aidd init --work-item <id> --request ... --root .aidd`;
- a bounded `aidd run` from `idea` to `plan` with `generic-cli`;
- `aidd run show`, `aidd run logs`, and `aidd run artifacts`;
- standard `questions.md` / `answers.md` inspection through `aidd stage questions`;
- `.aidd/` rooted inside the local fixture project.

## Out Of Scope

- `aidd init --github-issue <url>` is not part of this lane.
- Public-repository issue selection belongs to live E2E manifests under
  `harness/scenarios/live/`.
- Provider readiness panels are covered separately by the runtime readiness slice.
