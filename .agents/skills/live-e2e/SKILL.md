---
name: live-e2e
description: Run or prepare a full-flow live end-to-end scenario against a public GitHub repository with repository pinning, curated issue selection, quality checks, and full log capture.
---

# live-e2e

## Use when

- You need to execute or author a scenario from `docs/e2e/live-e2e-catalog.md`.
- You need to compare runtime behavior on a real repository.
- You need to prove the installed operator flow from `idea` through `qa`.

## Procedure

1. Read `docs/e2e/live-e2e-catalog.md` and the selected manifest in `harness/scenarios/live/`.
2. Resolve and record the exact target repository commit before the run starts.
3. Prepare the pinned target repository working copy.
4. Select the first issue from the scenario's curated issue pool and record that selection.
5. Install the AIDD artifact under test for the live run:
   - local wheel via `uv tool` in development and CI;
   - published package via `uv tool` in release verification.
6. Seed the prepared target repository with the live-run `aidd.example.toml` that points at the runtime under test.
7. Run installed `aidd` from the target repository root with raw runtime log capture enabled and explicit workflow bounds `idea -> qa`.
8. Run verification and quality commands, then write the execution verdict and quality report.
9. Save install evidence, issue-selection evidence, verification output, validator artifacts, questions, answers, quality artifacts, and the final conclusions.
10. Update the scenario manifest if the setup, quality, or verification recipe had to change.

## Hard rules

- Never run a live scenario without storing the resolved repo pin.
- Never run a live scenario without storing the selected issue snapshot.
- Never treat a live scenario as canonical unless it executes `idea -> qa`.
- Never treat a live scenario as passed without install evidence and verification output.
- Never treat a live scenario as clean without `quality-report.md` and `quality-transcript.json`.
- Preserve all runtime logs.
- Keep `.aidd` rooted inside the target repository for installed live runs.
