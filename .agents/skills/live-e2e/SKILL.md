---
name: live-e2e
description: Run or prepare a live end-to-end scenario against a public GitHub repository with repository pinning, verification commands, and full log capture.
---

# live-e2e

## Use when

- You need to execute or author a scenario from `docs/e2e/live-e2e-catalog.md`.
- You need to compare runtime behavior on a real repository.

## Procedure

1. Read `docs/e2e/live-e2e-catalog.md` and the selected manifest in `harness/scenarios/live/`.
2. Resolve and record the exact target repository commit before the run starts.
3. Prepare the pinned target repository working copy.
4. Install the AIDD artifact under test for the live run:
   - local wheel via `uv tool` in development and CI;
   - published package via `uv tool` in release verification.
5. Seed the prepared target repository with the live-run `aidd.example.toml` that points at the runtime under test.
6. Run installed `aidd` from the target repository root with raw runtime log capture enabled.
7. Save install evidence, verification output, validator artifacts, questions, answers, and the final verdict.
8. Update the scenario manifest if the setup or verification recipe had to change.

## Hard rules

- Never run a live scenario without storing the resolved repo pin.
- Never treat a live scenario as passed without install evidence and verification output.
- Preserve all runtime logs.
- Keep `.aidd` rooted inside the target repository for installed live runs.
