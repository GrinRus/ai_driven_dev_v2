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

## 3. Runtime support tiers

Runtime support is tiered by release impact and maintenance expectation.

| Runtime | Tier | Support expectation | Current notes |
| --- | --- | --- | --- |
| `generic-cli` | Tier 1 (release-blocking maintained) | Regressions are release blockers. Compatibility and behavior drift must be fixed before release. | Baseline portability runtime. |
| `claude-code` | Tier 1 (release-blocking maintained) | Regressions are release blockers. Adapter and operator flows must stay production-usable. | First-class maintained runtime. |
| `codex` | Tier 2 (actively maintained, non-blocking) | Regressions should be fixed promptly but may ship with explicit caveats when Tier 1 remains healthy. | Parity and eval behavior are still being hardened. |
| `opencode` | Tier 3 (planned/limited) | Best-effort support only. Known gaps are acceptable when documented. | Parity lane remains partially blocked by current harness placeholder execution. |

Operational policy:

- Tier 1 defects: highest triage priority, release-blocking.
- Tier 2 defects: normal priority, not release-blocking by default.
- Tier 3 defects: roadmap-prioritized, may remain open with documented limitations.

Promotion/demotion policy:

- A runtime moves up only after sustained conformance in adapter checks and live scenario coverage.
- A runtime may move down when sustained regressions or ecosystem breakages exceed maintenance capacity.

## 4. Live E2E baseline and pinned-revision refresh policy

Live E2E scenarios must remain reproducible and comparable across refreshes.

### 4.1 Pinned revision rules

- Every live scenario manifest must pin upstream repository revision data.
- A pinned revision change must be atomic with:
  - updated scenario manifest pin;
  - updated `docs/e2e/live-e2e-catalog.md` reference metadata;
  - archived replacement reference bundle identifiers.
- Unpinned live scenarios are not allowed in maintained lanes.

### 4.2 Refresh cadence and triggers

Default cadence:

- review live scenario pins at least once per quarter.

Immediate refresh triggers:

- upstream project changes invalidate deterministic verification steps;
- runtime/adapter changes materially alter expected behavior;
- contract or validator changes alter pass/fail interpretation for the lane.

### 4.3 Required refresh procedure

For each refreshed lane:

1. Update pinned revision in the scenario manifest.
2. Re-run required scenario lanes for maintained runtimes first.
3. Compare new run artifacts against the previous baseline.
4. Update `docs/e2e/live-e2e-catalog.md` with:
   - refresh date;
   - runtime used;
   - new reference bundle id;
   - known deltas and limitations.
5. Keep historical references in Git history; do not silently overwrite outcome context.

### 4.4 Failure and rollback policy

- If refreshed baselines regress determinism or verification fidelity, rollback to the previous pin.
- If rollback is impossible, record the lane as degraded and open roadmap follow-up work before promoting the new baseline.

## 5. Change control

Any compatibility policy change must update, in the same change:

- `README.md` references and operator-facing docs when affected;
- CI/release workflow configuration when policy requirements change;
- roadmap status for the corresponding local task.

## 6. Deprecation rules

Deprecations must be explicit, time-bounded, and reversible until the announced removal window closes.

### 6.1 Shared deprecation lifecycle

Every deprecation follows these phases:

1. Announcement:
   - mark deprecated in docs and roadmap notes;
   - describe replacement path;
   - define the planned removal milestone.
2. Transition window:
   - keep legacy behavior available;
   - provide migration guidance and examples.
3. Removal:
   - remove deprecated behavior;
   - update contracts/docs/scenarios to remove stale references.

Minimum notice window:

- at least two tagged releases between deprecation announcement and removal for non-critical changes;
- immediate removal is allowed only for security or severe data-integrity risks, with explicit incident notes.

### 6.2 Contract deprecation rules

Applies to stage/document contracts and contract examples.

- Breaking contract changes require:
  - migration notes describing old vs new contract expectations;
  - synchronized updates to validators, prompts, examples, and affected tests;
  - explicit compatibility statement in release notes.
- Removing a required section or renaming canonical fields without migration notes is not allowed.

### 6.3 Adapter deprecation rules

Applies to runtime adapters and adapter capability surfaces.

- Deprecating an adapter requires:
  - updated runtime support tier entry in this policy;
  - operator-facing impact note;
  - documented fallback runtime path when available.
- Tier 1 adapter deprecation cannot ship without a replacement Tier 1 path.

### 6.4 Scenario manifest deprecation rules

Applies to smoke/interview/live scenario manifests and associated catalog entries.

- Deprecated scenarios must include:
  - replacement scenario id (or explicit no-replacement rationale);
  - reason for deprecation;
  - removal target release.
- Scenario removal must update `docs/e2e/live-e2e-catalog.md` and keep historical evidence discoverable in Git history.
