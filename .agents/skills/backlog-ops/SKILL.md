---
name: backlog-ops
description: Select, split, create, promote, and close roadmap tasks while keeping `roadmap.md` and `backlog.md` synchronized.
---

# backlog-ops

Use this skill whenever you touch `docs/backlog/roadmap.md` or `docs/backlog/backlog.md`.

## Planning sources

Read these in order:

1. `docs/backlog/backlog.md`
2. `docs/backlog/roadmap.md`
3. `docs/product/user-stories.md`
4. the nearest `AGENTS.md` for the code or docs area you will touch

## Canonical rules

- `docs/backlog/roadmap.md` is the canonical hierarchy.
- `docs/backlog/backlog.md` is the short actionable queue.
- Work must always fit `wave -> epic -> slice -> local task`.
- A local task must be reviewable without another decomposition pass.
- Update `roadmap.md` first, then update `backlog.md`.

## Taking a task

1. Read the `Next` section in `docs/backlog/backlog.md`.
2. Pick the first local task marked `next` unless it is blocked by a documented dependency.
3. Read the full parent slice in `docs/backlog/roadmap.md`.
4. Read the linked user stories and architecture notes for the touched area.
5. Restate the task in your own words before coding:
   - exact output;
   - touched module or file family;
   - main verification signal;
   - dependencies that must already exist.

Do not start coding if you cannot name all four items above.

## Local-task quality bar

A valid local task has:

- one clear output artifact or code change;
- one dominant touched area;
- one main verification path;
- explicit upstream dependencies;
- wording that starts with a concrete verb.

A task must be split immediately if any of these are true:

- it touches more than one subsystem family, such as core + adapter + harness;
- it mixes contract design and broad downstream rollout;
- it has multiple independent outputs that could be reviewed separately;
- it has no single pass/fail check;
- it would require another planning discussion during implementation.

## Local-task template

When you create or rewrite a local task, make it fit this template:

- **ID** — `W<wave>-E<epic>-S<slice>-T<task>`
- **Action** — starts with a verb such as `Define`, `Implement`, `Write`, `Add`, `Expose`, `Render`
- **Output** — name the artifact, module, or command that changes
- **Scope** — keep one dominant touched area
- **Verification** — state how the task will be proven done

Example:

- `W4-E1-S2-T4` Implement stdout and stderr streaming to the CLI while the subprocess runs.

That is good because it names the subsystem, the behavior, and the direct review target.

## Creating a new local task

Create a new local task when the discovered work:

- clearly belongs to an existing slice goal;
- can be reviewed independently;
- has one dominant output and one verification signal.

Workflow:

1. Add the new task under the correct slice in `roadmap.md`.
2. Keep the existing slice goal unless the outcome changed materially.
3. Preserve the current task id for the first surviving piece whenever you split active work.
4. Append new task ids after the preserved one.
5. Update slice dependencies, touched areas, or exit evidence if the new task changes them.
6. Pull the new task into `backlog.md` only if it is immediately actionable.

## Creating a new slice

Create a new slice only when the discovered work is a different meaningful outcome, for example:

- a new stage contract;
- a new adapter capability;
- a separate harness scenario lane;
- a separate operator command surface.

Do **not** create a new slice just because the current task is too large. Split into more local tasks first.

A good slice has:

- one outcome sentence in the goal;
- explicit primary outputs;
- touched areas;
- dependencies;
- exit evidence.

## Creating a new epic

Create a new epic only when the theme changes enough that the work is no longer one coherent track, for example:

- moving from validators into runtime adapters;
- moving from harness execution into release operations.

If the work still serves the same theme, keep it inside the current epic.

## Splitting workflow

When a task or slice is too large:

1. Identify the dominant outputs hidden inside the oversized work.
2. Keep the current id for the first smallest reviewable piece.
3. Create follow-up task ids for the remaining pieces.
4. Reword each new task so it names the output directly.
5. Check whether the parent slice still has one clear outcome.
6. Update `backlog.md` so only the immediate next pieces stay in `Next`.

## Dependency rules

- Dependencies belong on the slice, not repeated on every task unless there is an exception.
- A task may assume slice dependencies are already satisfied.
- If one task inside a slice depends on another task in the same slice, order the tasks so the dependency is obvious.
- If discovered work depends on another wave or epic, add that dependency explicitly to the slice.

## Promotion rules for `backlog.md`

Use `backlog.md` as a queue, not as a second roadmap.

- `Next` contains immediately actionable local tasks only.
- `Soon` contains tasks that are likely next but still depend on `Next`.
- `Parking lot` holds later-wave tasks that should stay visible.
- Never place a slice or epic in `backlog.md`; only local task ids belong there.
- Never add a task to `backlog.md` unless it already exists in `roadmap.md`.

## Closing work

After implementation:

1. Mark the task or slice state in `roadmap.md` if it materially changed.
2. Remove completed tasks from `backlog.md`.
3. Add follow-up tasks to `roadmap.md` before mentioning them elsewhere.
4. Delete stale wording instead of leaving historical clutter.
5. Make sure the new plan still reads cleanly from wave to task.

## Sync checklist

Any change to planning files should leave all of these true:

- every backlog id exists in the roadmap;
- every `Next` item is a local task, not a slice;
- no task wording is ambiguous or multi-output;
- parent slices still have one meaningful outcome;
- dependencies and exit evidence still match the work.

## Output when reporting planning work

When you finish a planning update, report:

- the local task you took or the slice you decomposed;
- new or changed task ids;
- any new dependencies you added;
- which items moved into `Next`, `Soon`, or `Parking lot`.
