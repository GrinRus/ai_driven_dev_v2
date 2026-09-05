# AGENTS.md

This directory composes core services, validation, and artifact publication for entrypoints.

## Rules

- Keep workflow and task-state semantics in core; adapters own provider integration.
- Expose one shared operation to CLI and UI where behavior must agree. Avoid importing CLI
  handlers or browser presentation into application operations.
- Preserve mutation leases, run identity checks, fail-closed publication, and durable
  reconciliation evidence when changing an operation.
- Verify the application operation and affected CLI/UI entrypoints; use the ownership and
  check matrix in `docs/agent-development.md`.
