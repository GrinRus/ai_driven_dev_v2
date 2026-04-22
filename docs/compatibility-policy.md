# Compatibility Policy

This document defines the support guarantees for Python versions and operating platforms.

## 1. Python version support window

Policy:

- Minimum supported interpreter: CPython 3.12.
- Supported window: CPython 3.12 through 3.14.
- Versions below 3.12 are unsupported.

Validation policy:

- Release-blocking CI must pass on the baseline interpreter (currently 3.12).
- Regressions on 3.13 and 3.14 are treated as compatibility defects and should be fixed in normal maintenance.
- Adding a new Python minor version to the support window requires:
  - updating project metadata (`requires-python`);
  - updating CI/runtime checks;
  - documenting the change in this policy.

## 2. Platform support policy

Current support tiers:

- Tier 1 (release-blocking):
  - Linux (`ubuntu-latest`, x86_64) in CI and release workflows.
- Tier 2 (best-effort, non-blocking):
  - macOS (Apple Silicon and Intel) for local development and operator workflows.
- Not currently supported:
  - Windows.

Operational notes:

- Platform-specific defects are triaged by tier.
- Tier 1 regressions block release readiness.
- Tier 2 regressions should be fixed promptly but may ship with documented caveats when no Tier 1 impact exists.

## 3. Change control

Any compatibility policy change must update, in the same change:

- `README.md` references and operator-facing docs when affected;
- CI/release workflow configuration when policy requirements change;
- roadmap status for the corresponding local task.
