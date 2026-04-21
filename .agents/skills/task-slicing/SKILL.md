---
name: task-slicing
description: Turn a coarse roadmap item into reviewable local tasks with one output, one dominant touched area, and one main verification signal.
---

# task-slicing

Use this skill when a roadmap task or slice still feels too vague to implement directly.

## What "good slicing" means

A strong local task has:

- one concrete output;
- one dominant touched area;
- one main verification path;
- wording that starts with a verb;
- a scope small enough for one focused review.

## Smells that mean "split again"

Split again if the proposed task:

- touches core plus adapter plus harness together;
- mixes contract design with broad rollout;
- produces multiple independent artifacts;
- needs different verification strategies at once;
- still contains words like `implement stage`, `finish adapter`, `wire everything`, or `support all cases`.

## Split order

Always try this order:

1. split into more local tasks in the same slice;
2. create a new slice only if there is a different meaningful outcome;
3. create a new epic only if the theme changes.

## Recipe

1. Name the parent outcome in one sentence.
2. List the concrete outputs hidden inside it.
3. Group outputs by touched area.
4. Turn each group into a verb-led task.
5. Check that each task has one main verification signal.
6. Reorder tasks so dependencies read top to bottom.

## Examples

Too broad:

- `Implement the Claude Code adapter.`

Better:

- `Implement Claude Code command assembly from stage brief, workspace path, and prompt-pack inputs.`
- `Stream raw Claude Code stdout and stderr to the operator CLI in real time.`
- `Persist a full runtime.log that matches the raw streamed output as closely as possible.`
- `Detect Claude Code question or pause events when the runtime exposes them.`

Too broad:

- `Finalize the implement stage.`

Better:

- `Define the required implement inputs, including task selection, repository state, and allowed write scope.`
- `Define the required implement outputs, including change summary, touched files, and verification notes.`
- `Define validator rules for missing diffs, unverifiable claims, and incomplete execution summaries.`
- `Create the implement prompt-pack scaffold with explicit edit and verification guidance.`

## Output

When you use this skill, report:

- the parent item you decomposed;
- the new task ids;
- why the old task was too broad;
- the output and verification signal for each new task.
