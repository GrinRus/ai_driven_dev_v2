# AGENTS.md

This directory contains the Python package.

## Rules

- Keep core semantics out of adapters.
- Prefer small, typed modules with narrow ownership.
- Put filesystem policy in core/workspace, runtime process handling in adapters, and validation in validators.
- Keep application composition in `application/`; CLI and HTTP handlers invoke services and
  preserve their results. Packaged browser assets live in `cli/static/`.
- Use existing standard-library models and declared dependencies. A new runtime dependency
  needs an explicit product need and compatible packaging evidence.
