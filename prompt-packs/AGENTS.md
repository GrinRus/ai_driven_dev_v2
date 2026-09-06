# AGENTS.md

This directory stores prompt files used by AIDD stages.

## Rules

- Keep prompts file-based and reviewable in Git.
- Record stage purpose and expected documents in the prompt, not JSON output schemas.
- Track prompt changes with Git history and eval updates.
- Shared fragments must stay runtime-agnostic and have an explicit execution consumer,
  provenance, and regression evidence before use; keep stage-specific output rules in stage packs.
