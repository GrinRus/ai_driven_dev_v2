# AGENTS.md

These Node tests exercise packaged UI modules and DOM/state behavior without a provider.

## Rules

- Run an affected module with `node --test tests/frontend/<file>.test.mjs`; the full lane is
  `make test-frontend`.
- Keep fixtures deterministic and assert observable state, navigation, and interaction behavior.
  Preserve production module loading and cross-module boundaries when using a minimal DOM.
- Use `browser_tests/` for browser layout, accessibility, and end-to-end interaction evidence;
  a Node test alone does not verify rendering.
