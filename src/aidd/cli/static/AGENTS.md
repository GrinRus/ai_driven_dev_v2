# AGENTS.md

This directory contains packaged JavaScript, CSS, and other operator UI assets.

## Rules

- Reuse the existing UI modules, components, and design tokens. Keep assets registered through
  the asset manifest; new files must be available from the built wheel as well as a checkout.
- Render service-owned state and actions without inventing workflow transitions in the browser.
  Preserve project/work-item/run scope for navigation, drafts, polling, and mutation intents.
- Preserve loading, empty, failure, reconnect, focus, keyboard, and narrow-screen behavior.
  Validate visible outcomes and accessible names when an interaction changes.
- Run `make check-js` and the relevant Node test in `tests/frontend/`. Run the matching
  `browser_tests/` test for rendered behavior; use `make test-browser` for packaged journeys.
- Do not add a frontend build tool or dependency without an accepted task and packaging plan.
