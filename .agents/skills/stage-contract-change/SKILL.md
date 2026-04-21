---
name: stage-contract-change
description: Make a safe change to a stage or document contract by updating contracts, validators, prompts, and scenarios together.
---

# stage-contract-change

## Use when

- You are changing a stage input or output document.
- You are changing validation rules or repair behavior.

## Procedure

1. Update the relevant contract doc first.
2. Update validator logic or validator plan.
3. Update prompt files or prompt-pack references if the runtime needs new instructions.
4. Update stage-result expectations and repair behavior if needed.
5. Add or update at least one smoke or eval scenario.

## Hard rules

- Never change a stage contract in code only.
- Never widen a stage output implicitly.
- Keep Markdown as the canonical runtime-authored output form.
