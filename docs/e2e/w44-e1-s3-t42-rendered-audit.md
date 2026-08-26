# W44-E1-S3-T42 rendered audit

Date: 2026-08-26  
Revision: `3ef38644` (`main` after PR #410)  
Capture lane: provider-free Playwright operator harness  
Comparison viewports: `1440x900`, `1280x900`, `768x1024`, `390x844`, `320x568`

## Result

Work Item detail surfaces now use the target route-scoped two-level shell. The primary navigation
rail is 84px wide, the secondary project/Work Items rail is 236px wide, and the Work Item canvas
starts at the combined 320px boundary. The project Inbox intentionally keeps one 244px navigation
rail; the secondary rail is removed rather than duplicated. Mobile and tablet keep the existing
collapsed rail behavior.

Selection, stable Work Item ids, route/deep-link reload, keyboard navigation, server-owned item
ordering, and mutation services remain unchanged. The new rail control is accessible at the shared
desktop target size, and the split does not add a second primary action or a provider request.

## Evidence

- Focused shell/legacy/inbox browser checks: `35 passed`.
- Provider-free five-viewport matrix: `9 passed`.
- Frontend Node suite: `136 passed`.
- UI contracts plus docs/planning checks: `110 passed`.
- Ruff, mypy, deterministic scenarios, adapter conformance, security, build, and packaged UI
  browser CI passed.
- Fresh `1280x900` capture: `/tmp/w44-t42-shell-1280-v2.png` (temporary, not a product fixture);
  diagnostics were clean and horizontal overflow was absent.

## Remaining target gap

The detail capture still renders the generic breadcrumb/status topbar above the Work Item context
header. This leaves an extra approximately 64px chrome layer: the current Work Item title begins
around `y=116`, while the target detail references begin the title/header near `y=30` and use one
truthful context row. The topbar contains duplicated project/Work Item/stage context and generic
status/actions on detail surfaces; removing or collapsing that layer must not hide launch-specific
Runner controls or alter Inbox/Create/History routes. This is the next bounded task,
`W44-E1-S3-T43`, not a Wave 44 exit claim.
