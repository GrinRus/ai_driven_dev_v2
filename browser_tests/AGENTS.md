# AGENTS.md

This directory verifies the rendered operator UI with local fixtures and Playwright Chromium.

## Rules

- Keep browser tests independent of real provider authentication and private workspaces.
- Exercise visible controls and inspect resulting UI and durable state. Preserve evidence for
  loading, failure, reconnect, keyboard/focus, accessibility, and responsive behavior as relevant.
- Reuse the existing browser fixture and evidence helpers. Keep temporary state isolated and
  retain diagnostic artifacts on failure without changing a failed outcome to success.
- Run the affected test with `uv run --extra dev pytest -q browser_tests/<test_file>.py`.
  `make test-browser` runs registered packaged journeys; default `pytest -q` omits this directory.
- Chromium setup is documented in `docs/agent-development.md`; report missing prerequisites.
