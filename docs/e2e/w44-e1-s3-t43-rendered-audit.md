# W44-E1-S3-T43 rendered audit

Date: 2026-08-26  
Implementation merge: PR #412 (`831be726`)  
Target reference: `docs/architecture/assets/operator-ui-target-v2/03-work-item-launch.png`

## Change under review

Work Item detail routes now collapse the generic desktop breadcrumb/status topbar. The detail
surface keeps the fixed navigation rails and the real runtime-settings disclosure needed by launch
and recovery flows, while Inbox and setup retain their top-level chrome. Mobile and compact tablet
layouts retain their existing topbar behavior.

## Fresh rendered evidence

The fresh `1280x900` detail capture is retained locally as `/tmp/w44-t43-detail-1280-v2.png`.
The title begins at approximately y=37 and the generic topbar has zero rendered height. The detail
identity, tabs, and stage strip remain in the first viewport, with no horizontal overflow. The
comparison also records the next bounded gap: the internal context header still renders a stacked
`WORK ITEM WORKSPACE` eyebrow, phase/status line, and separate Work Item/current-status identity
rows, placing tabs around y=153 rather than near the target's compact title-to-tabs rhythm. This is
tracked as `W44-E1-S3-T44`; it is intentionally not included in T43.

## Verification

- `uv run --extra dev pytest -q browser_tests/test_w44_desktop_shell.py` — 12 passed.
- `node --test tests/frontend/*.test.mjs` — 136 passed.
- UI contract suite — 183 passed.
- `uv run --extra dev pytest -q tests/test_docs_consistency.py tests/test_planning_integrity.py` — 50 passed.
- Ruff and mypy — passed.
- Targeted Inbox desktop regressions — 2 passed after durable identity helper adjustment.
- PR CI — Python 3.12/3.13/3.14, deterministic scenarios, adapter conformance, security, build, and
  packaged UI browser all passed; packaged browser duration was 23m19s.

## Compatibility and decision

Existing Work Item ids, routes, DOM ids, launch/recovery runtime settings, status semantics, and
historical evidence remain unchanged. The desktop detail topbar collapse is accepted as a bounded
presentation change. The target-equivalence loop remains open pending T44's compact internal context
header; default task-centered routing remains provisional.
