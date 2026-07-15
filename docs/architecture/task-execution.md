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

## Public entrypoint contract

When a validated rich `tasklist.md` exists, every public `implement` mutation is task-aware.
No workflow, CLI, UI, interaction, or remediation entrypoint may convert a generic one-shot
runtime result into implement-stage success. A missing ready task, a tasklist/ledger mismatch, or
a changed source tasklist hash fails closed without publishing aggregate output or making `review`
or `qa` eligible.

| Entrypoint | Task selection | Ledger and finalization transition | Publication and downstream eligibility | Failure and remediation behavior |
| --- | --- | --- | --- | --- |
| Workflow run through `implement` | Execute dependency-ready tasks in authored order until the first non-success result, then finalize once all tasks succeeded. | Allocate one task attempt at a time; successful tasks remain succeeded. Enter aggregate finalization only from a complete successful ledger. | Publish `implementation-report.md` only after aggregate validation and atomic publication. Only that commit may make `review` eligible. | Stop on failed, blocked, or needs-input task. A continuation resumes from durable task evidence; it never replays succeeded tasks. |
| CLI `stage run implement` | Use the same automatic dependency-ready selection as workflow execution. | Use the task ledger and aggregate finalization state; generic stage execution is not available. | Cannot publish or unlock downstream stages outside aggregate finalization. | No ready task, stale source hash, or inconsistent ledger is a terminal command error with no publication. |
| CLI `stage interact implement` | Target the current dependency-ready or resumable task; when all tasks succeeded, target aggregate finalization. | Record the intervention under the selected task attempt or finalization attempt. | Rebuild and validate affected task or aggregate evidence before publication eligibility is restored. | Reject interaction when the target cannot be derived unambiguously. Never write a free-standing implement-stage result. |
| CLI `task run` | Execute the explicitly selected pending, failed, or blocked task only when its dependencies succeeded. | Allocate the next monotonic task attempt and update only that task's ledger entry. | Task success alone does not publish aggregate output or unlock `review`. | Reject unknown, already-succeeded, dependency-blocked, or source-mismatched selections without changing successful entries. |
| CLI `task finalize` | Select no task; require every authored task to be succeeded. | Allocate or resume an aggregate finalization attempt without rewriting task outcomes. | Successful validation and atomic publication commit implement-stage success and `review` eligibility. | Failed finalization remains retryable and retains all successful task outcomes. |
| UI workflow and stage controls | Apply the workflow or stage-run selection rules above through the same core task-aware service. | Observe the same ledger/finalization transitions; the UI owns no alternate execution policy. | A background job id is not success. Eligibility changes only after the durable aggregate commit. | Acquire the shared mutation lease before accepting the job; surface domain conflicts and durable failed/blocked state. |
| UI task and finalize controls | Apply the explicit task-run or aggregate-finalize rules above. | Persist task-local or finalization attempts through the same core service used by the CLI. | Never infer publication eligibility from a successful UI job alone. | Preserve prior successes and expose the resumable task/finalization target after failure. |
| UI interaction and remediation | Resolve the affected task or finalization attempt from durable evidence. | Create a new monotonic attempt and mark downstream evidence stale before rerun. | Revalidate task evidence and, when affected, aggregate publication before restoring `review`/`qa` eligibility. | Fail closed when evidence cannot identify one valid target; remediation cannot bypass the ledger. |
| `review` and `qa` progression | Select no implementation task. | Require a complete successful task ledger plus successful aggregate finalization matching the current tasklist hash. | `review` follows committed implement publication; `qa` additionally follows committed review success. | Forged or generic implement success, incomplete ledger state, stale hash, or failed finalization blocks progression. |

Task-local success is durable across later task, interaction, remediation, and finalization
failures. Remediation invalidates only the evidence that depends on the remediated checkpoint;
it does not erase unrelated successful task attempts.

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
