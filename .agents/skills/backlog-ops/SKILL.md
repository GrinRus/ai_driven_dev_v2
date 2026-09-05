---
name: backlog-ops
description: Select, add, promote, or close accepted roadmap work while keeping AIDD's local-task queue synchronized; use when editing roadmap.md or backlog.md.
---

# backlog-ops

Use whenever accepted work changes `docs/backlog/roadmap.md` or
`docs/backlog/backlog.md`. A request to inspect or propose a plan produces findings;
it does not itself require editing the queue.

## Read only the relevant plan

1. Read `docs/backlog/AGENTS.md` and the short queue in `docs/backlog/backlog.md`.
2. Prefer the user's selected task. Otherwise take the first actionable `Next` task,
   accounting for documented dependencies. Search its ID in the roadmap and read the
   parent slice, linked story, and owning architecture section.
3. Before coding, name the exact output, dominant touched area, main verification,
   and satisfied dependencies. If no accepted task fits, define the smallest relevant
   local task before behavior changes rather than taking unrelated queued work.
4. Read archived reconciliation only when investigating that history. Use the roadmap's
   queue-restoration policy if all work is done and the queue is empty.

## Update hierarchy and queue

`roadmap.md` is canonical: `wave -> epic -> slice -> local task`. `backlog.md` is an
ID queue, not a second roadmap. Update the roadmap first; every queued ID must already
exist there. Use [task-slicing](../task-slicing/SKILL.md) when the accepted outcome
contains independently reviewable outputs.

A local task records `W<wave>-E<epic>-S<slice>-T<task>`, a verb-led action, concrete
output, dominant scope, and observable verification. Declare dependencies on the slice;
add task-specific exceptions when ordering alone is insufficient. Preserve the existing
ID for the first surviving piece when splitting active work; give other pieces new IDs.
Create another slice only for a different outcome and another epic only for a new theme.

| Queue section | Admission |
| --- | --- |
| `Next` | Immediately actionable local tasks with satisfied dependencies. |
| `Soon` | Direct successors of current `Next` tasks. |
| `Parking lot` | Consciously deferred work that should remain visible. |

Do not queue slices/epics or invent completion evidence. Mark completed work in the
roadmap only after inspecting its outcome and verification, then remove its queue entry.
Record discovered follow-ups in the roadmap before promoting them. Keep current
reconciliation bounded; preserve dated outcomes in the linked history archive rather
than rewriting old failures or retaining accumulated history in the active queue.

## Check and report

Run `uv run --extra dev pytest -q tests/test_planning_integrity.py` for planning edits.
Inspect IDs, statuses, dependencies, and exit evidence together; a passing parser alone
cannot prove a task is actionable. Report affected task IDs, changed dependencies,
queue movements, and the checks/evidence used. Keep external issue/PR updates within
the user's existing authorization.
