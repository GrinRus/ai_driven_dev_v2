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
2. Resolve and record the exact repository commit before the run starts.
3. Prepare the workspace using the manifest setup commands.
4. Run the scenario through AIDD with raw runtime log capture enabled.
5. Save verification output, validator artifacts, questions, answers, and the final verdict.
6. Update the scenario manifest if the setup or verification recipe had to change.

## Hard rules

- Never run a live scenario without storing the resolved repo pin.
- Never treat a live scenario as passed without verification output.
- Preserve all runtime logs.
