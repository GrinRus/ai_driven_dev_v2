# Product positioning

Status: accepted product direction, recorded on 2026-10-01 in `W57-E1-S1-T3`.
This document owns the product promise and claim boundaries. The
[user stories](user-stories.md) own acceptance signals; the
[roadmap](../backlog/roadmap.md) owns implementation status. Target capabilities below
are migration goals, not features of the current alpha.

## Positioning statement

**AIDD helps developers understand and steer the work they delegate to AI coding agents.**

For developers, technical leads, and maintainers delivering changes in local repositories,
AIDD is a local, runtime-independent delivery workbench. It keeps the original goal,
human decisions, changes, and available verification evidence inspectable throughout the
work. Its target experience connects each important requested behavior to the change and
checks that support it, and makes uncertainty and the next decision visible.

Short product promise: **Know what you asked for, what changed, what was checked, and
what needs your decision.**

## User and problem

The primary user is an operator accountable for the delivered software. They may delegate
implementation, but still own the intended behavior, scope, and acceptance. A maintainer
needs to explain a result after the agent session ends; an evaluator needs comparable
evidence across runs and runtimes.

The problem is a loss of understanding and control between the original request and the
result. A plausible generated plan can omit a constraint, invent a product choice, or
claim a check without sufficient evidence. A long specification and another summary can
add reading without making those errors easier to detect.

The [research and migration rationale](../analysis/iterative-delivery-migration-plan-2026-10-01.md#1-evidence-and-product-problem)
motivates this direction. Low reading of generated specifications is a hypothesis about
operator behavior to test, not a universal fact or a reason to discard durable records.

## Product principles

1. **The requested outcome is the anchor.** Preserve the operator's original words and
   constraints. Generated interpretations have explicit provenance and authority.
2. **Show a useful next action.** Explain the concrete blocker, scope, and consequence
   before asking the operator to act. Avoid routine approval of every generated document.
3. **Connect claims to evidence.** A model claim, an executed check, and behavioral
   acceptance are distinct facts. Missing or outdated proof stays visible.
4. **Keep delivery responsive to feedback.** A new answer or finding can change the plan
   and create another bounded iteration while preserving earlier evidence.
5. **Keep records open and local.** Markdown remains the durable, inspectable interface.
   The UI reveals relevant source excerpts, diffs, and receipts on demand.
6. **Keep runtime choice portable.** Core behavior and authority stay outside providers;
   adapters expose runtime capabilities and retained logs honestly.

Document volume, generated word count, stage count, and time spent reading are not product
success metrics. Documents support understanding and reproducibility; opening a document
never confers product approval.

## Current claims and migration targets

| Area | Current alpha | Target after the accepted migration |
| --- | --- | --- |
| Delivery workflow | A canonical eight-stage workflow with dependency-aware implementation tasks. | A small set of policy-selected preparation routes and bounded delivery iterations. |
| Requirements | Protected operator request and durable questions/answers. | Source-bound criteria, explicit proposals/conflicts, and scoped human product decisions. |
| Validation | Markdown contract validation, repair or explicit stop, and retained reports. | Reference/coverage checks plus independently retained executions of registered checks. |
| Correctness | Inspectable artifacts and available runtime evidence; no guarantee of correct software. | Separate current check receipts and behavioral assessment against an independent oracle. |
| Feedback | Existing stage correction, remediation, and follow-up mechanisms. | Linked child runs, revised task plans, and explicit invalidation of affected evidence. |
| Operator UI | Inbox, Studio, History, questions, documents, task execution, and logs. | Outcome, criterion coverage, changes, proof, and one authoritative next action. |

The current document contract gate cannot be advertised as independent proof that code is
correct. The concept in the [iterative Operator UX](../architecture/iterative-operator-ux.md)
uses synthetic data and demonstrates a future interaction, not a connected runtime.

## Product boundaries

AIDD is a local developer tool around external coding runtimes. It does not bundle model
access or replace an IDE, code review, domain ownership, or testing. Local Operator UI
is a no-auth loopback surface, not a hosted team collaboration service. Alpha readiness,
runtime support, and current-format limits remain governed by the
[README](../../README.md) and [compatibility policy](../compatibility-policy.md).

Product decisions, runtime permissions, and execution controls have different scopes.
Allowing a runtime action does not accept a product behavior. A model review cannot give
itself permission to change the requested outcome. Full-access execution still requires
the existing honest distinction between detection and preventive isolation.

## How to judge the direction

An operator should be able to identify the original goal and constraint, explain the
important change, distinguish checked behavior from an assumption, find a missing or stale
check, and make the next scoped decision. A saved answer should have a visible downstream
effect, with its source, decision, plan revision, and new result connected.

Measure these with matched tasks, independent expected behavior, retained runtime traces,
and genuine operator observations. Predeclare thresholds in `W57-E1-S1-T2`; collect native
and human evidence in `W59-E2-S1-T1/T2`. Reading time is diagnostic. Operator understanding,
correct outcomes, truthful uncertainty, and recovery are the acceptance signals.

The design hypothesis is that this reduces review burden and mistaken acceptance. It
remains unverified until those comparisons and observations are recorded.

## Applying this document

README and public copy should lead with the operator's job and accurately describe current
capabilities. UI work should follow the [iterative UX blueprint](../architecture/iterative-operator-ux.md).
The [accepted iterative contract](../architecture/iterative-delivery-contract.md) defines
authority, ownership, routes and one direct breaking replacement without backward compatibility.
Implement its bounded slices before accepting the complete replacement candidate. Review
every migration slice against the relevant existing user
story; do not weaken a success signal to fit the new presentation.
