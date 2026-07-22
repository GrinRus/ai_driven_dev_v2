# Operator UI Chromium race characterization — 2026-07-22

This provider-free record characterizes the four failures that stopped the Wave 36
prod-like preflight on product revision `a3d5aa1`. It is diagnostic evidence, not a
browser acceptance pass. No live provider was invoked.

## Candidate and commands

- Product revision: `a3d5aa190b444d0a6cc82c56775ca23094b89d40`.
- Original lane: full `browser_tests` run, `183 passed, 4 failed`.
- Isolated rerun:

  ```bash
  uv run --extra dev pytest -q \
    'browser_tests/test_journey_intervention_recovery.py::test_allowed_intervention_restores_draft_and_creates_one_request[viewport0]' \
    'browser_tests/test_journey_intervention_recovery.py::test_allowed_intervention_restores_draft_and_creates_one_request[viewport3]' \
    'browser_tests/test_journey_intervention_recovery.py::test_allowed_intervention_restores_draft_and_creates_one_request[viewport4]' \
    'browser_tests/test_terminal_journey.py::test_terminal_outcomes_keep_completed_source_run_immutable[viewport3]'
  ```

- Isolated result: `4 passed in 164.28s`.
- A later natural family rerun passed all five intervention viewports, while the
  terminal family reproduced the same hidden Archive action at `320x568`.
- PR CI reproduced the same terminal class twice at `1280x900`, before the first
  Follow-up action.

## Normalized failure matrix

| Case | Viewport | Original observation | Actual mutation evidence | First decisive boundary |
| --- | --- | --- | --- | --- |
| `intervention-320` | `320x568` | The asynchronous request observer contained zero matching `POST /api/stage/interact` entries after History/Back restoration. | One canonical `stages/idea/operator-requests/request-*.md` existed. The isolated rerun observed exactly one POST and one durable request. | `page.go_back()` did not await `window.aiddRouteRestore`; the subsequent Python filesystem loop did not pump Playwright request events before reading the observer list. |
| `intervention-1280` | `1280x900` | Same zero-count request-observer assertion. | One canonical operator request existed. The isolated rerun observed exactly one POST and one durable request. | Same route/observer synchronization boundary; there is no viewport-specific service-path divergence. |
| `intervention-1440` | `1440x900` | Same zero-count request-observer assertion. | One canonical operator request existed. The isolated rerun observed exactly one POST and one durable request. | Same route/observer synchronization boundary; there is no viewport-specific service-path divergence. |
| `terminal-1280` | `1280x900` | Flow Complete Archive was repeatedly hidden or detached before the delegated click could dispatch. | Zero archive POSTs and no new archive overlay decision; durable dashboard readback remained unarchived. | The initial cockpit render (`R0`) was replaced by a deferred readiness-triggered full render (`R1`) after the disclosure was opened. The replacement disclosure returned closed. |

## Deterministic render probe

The terminal boundary was reproduced by delaying only `GET /api/runtime-readiness`,
opening Archive, retaining the confirmation node, and then releasing readiness:

```text
before_release_connected = true
after_release_connected = false
new_confirm_count = 1
wizard_action = archive-run
```

The logical wizard state survived, but its active DOM node did not. The replacement
was caused by `refresh()` scheduling `fetchReadiness().then(renderAll)`: readiness
owned data caused a second full cockpit render. The same path can close the Flow
Complete disclosure between Playwright resolving a button and dispatching its click.

## Conclusions

1. The three intervention failures were observer synchronization drift, not missing
   durable requests. Browser coverage must await the application route promise and
   use request/response synchronization rather than a blocking filesystem loop.
2. The terminal failures are a product defect: background readiness refresh must not
   replace an unrelated active decision surface.
3. Archive still needs the shared keyed mutation guard and durable readback; otherwise
   duplicate input can append multiple archive decisions.
4. Intervention drafts must be cleared only after a successful matching durable
   submission. An unrelated conflict is not proof that the intervention won.
5. The correction belongs to one render/mutation synchronization contract. Delays or
   viewport-specific retries would hide the defect and are not acceptable.

