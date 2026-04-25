# Blockers and Next Actions

## Critical blockers

1. **`W15-E3-S1-T1` is blocked by missing live wrapper configuration.**
   Evidence: `AIDD_EVAL_CODEX_COMMAND` and `AIDD_EVAL_OPENCODE_COMMAND` are unset, while `.agents/skills/live-e2e/SKILL.md` requires an AIDD-compatible wrapper command for local live runs.
   Impact: a manual public-repository live E2E run cannot be completed safely in this environment.

2. **`W15-E3-S2-T1` is blocked by missing release candidate context.**
   Evidence: no release tag points at `HEAD`, and local publish-token environment variables are unset.
   Impact: PyPI, `uv tool`, and GHCR release-channel evidence cannot be captured from the current local state.

## Important gaps

1. **No fresh manual live eval bundle exists for Wave 15.**
   This is expected while `W15-E3-S1-T1` remains blocked.

2. **No fresh release-channel verification transcript exists for Wave 15.**
   This is expected while `W15-E3-S2-T1` remains blocked.

3. **`reports/` and `uv.lock` remain untracked.**
   They were present before this final audit pass; report contents were refreshed, but no tracked source file depends on them.

## Fast documentation corrections

1. **Completed in this pass: refresh stale readiness reports.**
   The prior reports still described an empty pre-Wave-15 queue and a failing ruff gate. The refreshed reports now match the current Wave 15 state.

2. **No additional backlog correction is needed right now.**
   The active backlog is empty because all local tasks are done and both remaining external tasks are explicitly blocked.

## Implementation-ready next steps

1. **`Wave 15 -> external evidence lanes -> fresh manual live evidence -> W15-E3-S1-T1`**
   Export a valid `AIDD_EVAL_CODEX_COMMAND` or `AIDD_EVAL_OPENCODE_COMMAND`, confirm provider auth, then run `uv run aidd eval run harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml --runtime <runtime>`.

2. **`Wave 15 -> external evidence lanes -> release-channel evidence capture -> W15-E3-S2-T1`**
   Create a release candidate tag matching `pyproject.toml`, run the release workflow, and preserve `verify-pypi-install`, `verify-uv-tool-install`, and `verify-ghcr-install` logs.

3. **Next local implementation wave**
   If external evidence will remain blocked, open a new wave via the `W8-E3-S1` queue-restoration policy before writing more implementation code.

## Backlog corrections required

1. **None for the current local state.**
   `Next`, `Soon`, and `Parking lot` are empty; roadmap records both external blockers.

2. **Do not silently treat blocked external evidence as done.**
   `W15-E3-S1-T1` and `W15-E3-S2-T1` should stay blocked until their prerequisites are actually available and evidence is captured.
