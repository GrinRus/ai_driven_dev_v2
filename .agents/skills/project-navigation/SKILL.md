---
name: project-navigation
description: Locate the owning code, contracts, instructions, and nearest checks for an AIDD task when ownership or context is unclear.
---

# project-navigation

Use this skill to resolve ownership, not to load the whole repository before every edit.

1. Classify the request as analysis, planning, implementation, or external coordination;
   preserve its accepted scope and prior authorization.
2. Read root policy and consult the relevant row in
   [the agent development map](../../../docs/agent-development.md). It covers core,
   application, adapters, runtime logs/configuration, contracts/prompts, CLI, packaged
   frontend, harness/evals, planning, releases, and maintainer instructions.
3. Locate the owning files with `rg --files` or a targeted `rg` search. Read applicable
   `AGENTS.md` files cumulatively from root to leaf for every touched path; a sibling's
   instructions do not apply automatically.
4. For behavior changes, locate the accepted local task ID in
   `docs/backlog/backlog.md`, search that ID in `docs/backlog/roadmap.md`, and read
   its parent slice and dependencies. Do not load the complete roadmap or dated audit
   history unless the question requires it. Map the outcome to the relevant user story
   and owning architecture/contract section.
5. Name the primary changed output, owning files, nearest observable verification,
   and whether an affected scenario/grader must change. Use the matrix to identify
   browser checks when frontend behavior is involved; Python tests alone do not cover it.

Return a short work map with those decisions and any material uncertainty. An analysis
request ends in findings; finding the implementation path does not authorize edits.
