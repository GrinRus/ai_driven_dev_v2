# W44-E1-S3-T44 rendered audit

Date: 2026-08-26  
Implementation merge: PR #414 (`2534cdef`)  
Target reference: `docs/architecture/assets/operator-ui-target-v2/03-work-item-launch.png`

## Change under review

Work Item detail context is now a compact target-style header. The title uses the available canvas,
the phase/status line and durable Work Item/current-status identity share a dense metadata row, and
the decorative `Work Item Workspace` eyebrow plus stacked duplicate identity treatment are removed
from the desktop/tablet visual flow. Desktop keeps the collapsed generic topbar from T43; mobile
keeps its established full context treatment and topbar.

## Fresh rendered evidence

Fresh captures are retained locally as `/tmp/w44-t44-detail-1280-v2.png` and
`/tmp/w44-t44-detail-768.png`. At `1280x900`, the context bar is 76.94px high, the title begins at
y=8, tabs at y=90.94, and the canonical stage strip at y=145.94; the title is one line and the
durable identity/status remain visible without horizontal overflow. The desktop rhythm is materially
closer to the target title → tabs → stage strip hierarchy.

The `768x1024` capture remains technically contained but records the next independent responsive
gap: the legacy tablet topbar occupies a tall navy block and the global tabs appear before the
context header (tabs y=239, context y=294). This ordering/density issue is tracked as
`W44-E1-S3-T45`, not folded into T44.

## Verification

- `uv run --extra dev pytest -q browser_tests/test_w44_desktop_shell.py` — 15 passed.
- `uv run --extra dev pytest -q browser_tests/test_journey_active_studio.py` — 5 passed.
- `node --test tests/frontend/*.test.mjs` — 136 passed.
- UI contract suite — 183 passed.
- `uv run --extra dev pytest -q tests/test_docs_consistency.py tests/test_planning_integrity.py` — 50 passed.
- Ruff and mypy — passed.
- PR CI — Python 3.12/3.13/3.14, deterministic scenarios, adapter conformance, security, build, and
  packaged UI browser all passed; packaged browser duration was 14m53s.

## Compatibility and decision

Existing Work Item ids, routes, DOM ids, launch/recovery controls, stage order, status semantics, and
historical evidence remain unchanged. The compact context header is accepted for T44. Target
convergence remains open pending the tablet shell ordering/density fix in T45; default task-centered
routing remains provisional.
