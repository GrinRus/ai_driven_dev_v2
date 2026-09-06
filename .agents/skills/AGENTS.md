# AGENTS.md

This directory holds reusable development workflows for coding agents.

## Rules

- Keep each skill focused on one repeatable workflow.
- Prefer repo-specific instructions over generic advice.
- Update skills when the roadmap, architecture, or contributor workflow changes.
- Keep `SKILL.md` focused on triggers, the essential procedure, and expected evidence. Move
  detailed runbooks into the skill's linked reference documents and load only the relevant one.
- State concrete inputs, outputs, and commands. Distinguish local validation from provider
  execution or publication; preserve authorization already given for the scoped action.
- Run `make check-agents` after instruction or reference changes and inspect the relevant
  command help or focused check when a procedure changes.
