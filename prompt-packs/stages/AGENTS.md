# AGENTS.md

This directory holds one prompt pack per workflow stage.

## Rules

- Each stage pack should stay aligned with the matching contract in `contracts/stages/`.
- Keep `system.md`, `run.md`, `repair.md`, `interview.md`, and `intervention.md` small and explicit.
- Never require canonical JSON as the main stage output.
- Tell the runtime which Markdown files it must read and write; preserve the contract's
  distinction between runtime-authored documents and AIDD-owned artifacts.
- Keep repair guidance specific to validator findings. Use `interview.md` for question-asking
  behavior, not for normal stage execution.
- Follow the `stage-contract-change` skill for behavior changes and verify the composed request,
  matching validator expectations, and packaged prompt provenance.
