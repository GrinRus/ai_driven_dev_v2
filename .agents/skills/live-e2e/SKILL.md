---
name: live-e2e
description: Run or prepare a manual full-flow live end-to-end scenario against a public GitHub repository with repository pinning, curated issue selection, quality checks, and full log capture.
---

# live-e2e

## Use when

- You need to execute or author a scenario from `docs/e2e/live-e2e-catalog.md`.
- You need to compare live provider behavior on a real repository.
- You need to prove the installed operator flow from `idea` through `qa` as a manual external audit.

## Read first

1. `docs/e2e/live-e2e-catalog.md`
2. `docs/e2e/scenario-matrix.md`
3. the selected manifest in `harness/scenarios/live/`

## Procedure

1. Confirm the selected scenario is in `harness/scenarios/live/`, has `automation_lane: manual`, and declares the requested runtime in `runtime_targets`.
2. If the run goes through `.github/workflows/manual-live-e2e.yml`, confirm the corresponding runtime-command GitHub secret is configured:
   - `AIDD_EVAL_CODEX_COMMAND` for `codex`
   - `AIDD_EVAL_OPENCODE_COMMAND` for `opencode`
   The command must be a runner-available wrapper that accepts the AIDD adapter flags.
3. Resolve and record the exact target repository commit before the run starts.
4. Prepare the pinned target repository working copy.
5. Select the first issue from the scenario's curated issue pool and record that selection.
6. Install the AIDD artifact under test with `uv tool`.
7. Seed the prepared target repository with the live-run `aidd.example.toml` that points at the runtime under test.
8. Run installed `aidd` from the target repository root with raw runtime log capture enabled and explicit workflow bounds `idea -> qa`.
9. Run verification and quality commands, then write the execution verdict and quality report.
10. Save install evidence, issue-selection evidence, verification output, validator artifacts, questions, answers, quality artifacts, and the final conclusions.
11. Update the scenario manifest, matrix doc, and catalog if the setup, provider coverage, size classification, quality, or verification recipe had to change.

## Hard rules

- Never treat live E2E as a CI or release lane.
- Never dispatch the manual GitHub workflow without the runtime-command secret for the selected provider.
- Never run a live scenario without storing the resolved repo pin.
- Never run a live scenario without storing the selected issue snapshot.
- Never treat a live scenario as canonical unless it executes `idea -> qa`.
- Never treat a live scenario as passed without install evidence and verification output.
- Never treat a live scenario as clean without `quality-report.md` and `quality-transcript.json`.
- Preserve all runtime logs.
- Keep `.aidd` rooted inside the target repository for installed live runs.
