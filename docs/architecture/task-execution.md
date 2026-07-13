# Task Execution Architecture

## Decision

`tasklist.md` is the immutable runtime-authored source of task definitions. AIDD parses the
validated Markdown into a typed task plan and stores only derived execution state in the
system-owned `task-ledger.json` under the implement-stage run evidence.

The canonical eight-stage graph does not change. `implement` owns an internal dependency-aware
task loop; `review` and `qa` run once after every task succeeds and the aggregate
`implementation-report.md` is published.

## Task definition

Each H3 task card has a stable task id, imperative title, outcome, dominant deliverable,
in-scope boundary expressed as safe repository-relative path prefixes, task-local acceptance ids,
dependencies, and verification. Optional context,
constraints, and out-of-scope notes do not replace the required fields.

## Persistence and execution

- the ledger stores the source tasklist SHA-256, task status, attempt count, blocker, and latest
  task-evidence path;
- task evidence lives below `stages/implement/tasks/<task-id>/attempts/attempt-000N/`;
- every attempt captures repository status before and after execution plus runtime/repair evidence;
- attempt preparation uses a staging directory and durable attempt state so an interrupted
  `executing` task can be terminalized as abandoned and resumed with a new monotonic attempt;
- task readiness is derived from succeeded dependencies rather than persisted independently;
- auto execution stops on the first blocked or failed task; explicit task execution may resume
  pending, blocked, or failed tasks but never a succeeded task;
- changing the source tasklist hash invalidates the ledger and requires a continuation run.
- task-owned questions and operator answers survive blocked resume and are copied into task-local
  evidence; unresolved input does not allocate an empty resume attempt;
- task diff, report agreement, task-local scope, global scope, and acceptance evidence participate
  in the normal implement repair budget before a task may succeed;
- aggregate publication has a separate ledger finalization state and attempt history. Failed
  validation or atomic publication never changes successful task outcomes and can be retried with
  `aidd task finalize`.

Run mutations use the shared filesystem lease. Same-host dead owners may be reclaimed; live,
remote-host, or malformed owners remain conflicts. UI mutation endpoints acquire the lease before
returning a background job id. Stage success remains uncommitted until the final aggregate
implementation report passes validation and atomic publication succeeds.

## Alternatives rejected

- Rewriting task statuses into `tasklist.md` would mix runtime-authored intent with mutable system
  state and invalidate the published source artifact.
- One runtime invocation for the whole list would not provide task-local repair, resume, or
  evidence.
- A separate implement/review/QA cycle per task would change the canonical stage graph and make
  aggregate product review harder to interpret.

## Compatibility

The rich task-card contract is intentionally breaking. Compact legacy tasklists are not converted
or executed through a one-shot fallback.
