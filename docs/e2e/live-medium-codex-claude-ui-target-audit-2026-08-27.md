# Live medium Codex/Claude UI target audit — 2026-08-27

## Scope

The target design authority is the operator UI reference set in
`docs/architecture/assets/operator-ui-target-v2/`. The audit covered the
provider-free Wave 42 journey matrix against the rendered frontend; it did not
introduce a new renderer or change the existing task-centered routing decision.

## Evidence

Command:

```text
uv run --extra dev pytest -q browser_tests/test_wave42_browser_matrix.py -k 'journey_matrix_is_provider_free_and_rendered_across_viewports' --basetemp /tmp/live-medium-ui-audit-20260827-2
```

Result: `8 passed, 1 deselected in 545.90s (0:09:05)`.

The run retained 40 screenshots: eight journeys across five viewports
(`320x568`, `390x844`, `768x1024`, `1280x900`, `1440x900`). The checks found no
console errors, unexpected network/provider requests, horizontal overflow,
accessibility failures, or geometry failures.

Representative evidence:

- `/tmp/live-medium-ui-audit-20260827-2/test_wave42_journey_matrix_is_0/evidence/screenshots/create-runner-launch-1280x900.png`
- `/tmp/live-medium-ui-audit-20260827-2/test_wave42_journey_matrix_is_2/evidence/screenshots/question-recovery-390x844.png`
- `/tmp/live-medium-ui-audit-20260827-2/test_wave42_journey_matrix_is_7/evidence/screenshots/completion-1440x900.png`

## Comparison and verdict

The reference screenshots and the current fixtures use different sample data
and viewport dimensions, so pixel identity is not expected. The rendered UI
matches the target contract in the material dimensions: task-centered
hierarchy, server-owned grouping, primary-action placement, responsive
composition, focus behavior, and accessible status treatment.

No bounded UI fix was justified by this evidence. The current task-centered
renderer and default routing remain in place. Any future visual change should
be driven by a new concrete mismatch with a retained screenshot and a focused
regression check.
