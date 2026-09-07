# AGENTS.md

This directory owns the CLI, local operator HTTP surface, and packaged UI assets.

## Rules

- Keep command names stable once introduced.
- Keep CLI and UI behavior aligned with the same application/core services and durable state.
  Do not implement workflow transitions or task eligibility independently in a handler.
- Preserve stable routes, artifact provenance, raw log access, and explicit failure states.
  A UI job keeps the project/workspace context captured when it starts.
- Keep HTTP routing, asset delivery, job evidence, and UI presentation in their owning modules.
  Static files have additional rules in `static/AGENTS.md`.
- Run the relevant `tests/cli/` modules. Use `docs/agent-development.md` for Node and browser
  checks when the change affects UI behavior or assets.
