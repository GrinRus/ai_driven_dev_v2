---
name: project-navigation
description: Map a task to the right AIDD docs, modules, checks, and scenario assets before making changes.
---

# project-navigation

## Use when

- You are starting work in this repository.
- You do not know which module or document set owns the change.

## Procedure

1. Read `AGENTS.md` and `docs/product/user-stories.md`.
2. Classify the task as one of: docs, contracts, core, adapters, validators, harness, evals, or CLI.
3. Read the nearest nested `AGENTS.md` for that area.
4. Identify the expected checks and scenario updates.
5. Name the primary files that should change before editing.

## Output

Produce a short work map: owning area, likely files, checks to run, and whether a scenario update is required.
