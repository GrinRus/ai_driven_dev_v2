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
3. Run `aidd init --work-item <id>` so `.aidd/` is created inside the fixture project.
4. Seed or execute a local deterministic work item.
5. Start `aidd ui --work-item <id> --root .aidd --host 127.0.0.1 --port <port>`.
6. Verify the page loads, `/api/workflow/run` is reachable, blocking answers persist,
   logs and artifacts render, validation state is visible, and repair evidence is linked.
7. Remove the disposable fixture project. Do not commit `.aidd/` artifacts.

Manual smoke evidence is recorded in `docs/backlog/roadmap.md`; generated `.aidd/`
state stays local to the fixture project.

## Out Of Scope

- `aidd init --github-issue <url>` is not part of this lane.
- Public-repository issue selection belongs to live E2E manifests under
  `harness/scenarios/live/`.
- Provider readiness panels are covered separately by the runtime readiness slice.
