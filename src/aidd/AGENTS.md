# AGENTS.md

This directory contains the Python package.

## Rules

- Keep core semantics out of adapters.
- Prefer small, typed modules with narrow ownership.
- Put filesystem policy in core/workspace, runtime process handling in adapters, and validation in validators.
