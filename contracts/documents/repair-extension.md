# Document Contract: `repair-extension.md`

## Purpose

Record one operator-authorized extension of the automatic repair budget. This is an
AIDD-owned control record, not a runtime-authored repair instruction. It authorizes at most
one additional attempt for the latest exhausted stage in the same run; it never rewrites the
automatic budget or existing attempt history.

## Required sections

- `Request`
- `Evidence`
- `Eligibility`
- `Decision`

## Required fields

### Request

- `Work item`: stable work-item id.
- `Run id`: the run that owns the exhausted stage.
- `Stage`: the exact exhausted stage.
- `Author`: the operator or service principal that authorized the request.
- `Authorized at`: an explicit UTC timestamp.
- `Reason`: a non-empty bounded explanation for the additional attempt.

### Evidence

- `Validator report`: workspace-relative path and SHA-256 hash for the latest canonical
  validator report.
- `Repair brief`: workspace-relative path and SHA-256 hash for the latest canonical repair
  brief.
- `Configuration identity`: the launch-relevant configuration identity captured with the
  exhausted attempt.

### Eligibility

The record must state each of these gates explicitly:

- latest stage state is `repair-exhausted`, not a generic failure;
- the selected work item, run, and stage match the evidence identity;
- the validator report and repair brief are current and their hashes match the selection;
- configuration identity has not drifted;
- no job is active for the same stage;
- no earlier extension grant exists for the same run and stage;
- no downstream stage in the same run has succeeded;
- validation will run again before any runtime launch.

An `intervention` attempt, a different run selection, a stale report or brief, configuration
drift, a prior grant, or succeeded downstream work is rejected before runtime execution.

### Decision

- `Status`: `approved` or `rejected`.
- `Disabled reason`: required for a rejected decision and literal enough for an operator to
  understand the failed gate.
- `Validation bypassed`: must always be `no` for an approved record.
- `Request Change`: remains a separate operator action and is never implied by this record.
- `New run`: remains a separate run identity and is never implied by this record.

## Invariants

- The identity tuple `(work item, run, stage)` is immutable.
- A grant is one-time and cannot be copied to another run or stage.
- The automatic repair budget and its exhaustion record remain unchanged.
- The extension is a distinct authorization; it is not an automatic retry or an intervention.
- Current documents are revalidated before a runtime is launched. If they already pass, the
  caller may finalize without starting a runtime.
- This contract does not authorize a second grant, a validation bypass, a downstream reopen,
  or an automatic repair loop.

## Allowed example

```md
# Repair Extension

## Request

- Work item: `WI-001`
- Run id: `run-001`
- Stage: `plan`
- Author: `operator@example.test`
- Authorized at: `2026-08-22T00:00:00Z`
- Reason: `Apply one bounded correction after the automatic budget was exhausted.`

## Evidence

- Validator report: `workitems/WI-001/stages/plan/validator-report.md` (sha256: `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa`)
- Repair brief: `workitems/WI-001/stages/plan/repair-brief.md` (sha256: `bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb`)
- Configuration identity: `codex:config-001`

## Eligibility

- Latest stage state: `repair-exhausted`
- Same work item/run/stage: `yes`
- Evidence current: `yes`
- Configuration drift: `no`
- Active job: `no`
- Prior extension grant: `no`
- Succeeded downstream: `no`
- Revalidate before runtime: `yes`

## Decision

- Status: `approved`
- Disabled reason: `none`
- Validation bypassed: `no`
- Request Change: `separate action`
- New run: `separate run identity`
```

## Rejected examples

The following selections are rejected before runtime execution:

| Selection | Required result |
| --- | --- |
| latest state is `failed`, but not `repair-exhausted` | reject: extension is exhaustion-only |
| validator or brief hash differs from the retained evidence | reject: stale evidence |
| configuration identity differs from the exhausted attempt | reject: configuration drift |
| an earlier extension exists for the same run and stage | reject: one-time grant already used |
| a downstream stage already succeeded | reject: downstream reopen is not allowed |
| selected attempt mode is `intervention` | reject: intervention is a separate action |
| validation would be skipped | reject: validation bypass is forbidden |
| selected run or stage differs from the evidence tuple | reject: same-run selection mismatch |

## Notes

This is a Markdown control contract. The core owns eligibility and persistence. Runtime
adapters may consume the resulting repair brief, but cannot approve, rewrite, or extend the
grant.
