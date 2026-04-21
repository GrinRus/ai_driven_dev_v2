# AGENTS.md

This directory owns runtime-agnostic workflow semantics.

## Rules

- Do not import runtime-specific code here except through adapter interfaces.
- Keep stage order, workspace layout, and contract discovery explicit.
- Prefer durable state and small pure helpers.
