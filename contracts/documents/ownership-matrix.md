# Document Contract: stage-document ownership matrix

## Purpose

This matrix is the canonical ownership boundary for stage-local documents and retained
attempt evidence. Each declared stage document appears exactly once below. A document may be
read by another stage, but the reader does not become its owner or gain mutation authority.

The matrix deliberately does not change the eight-stage graph, existing filenames, workspace
paths, or historical run manifests. It makes the existing boundary executable: runtime adapters
author content, while AIDD owns validation, lifecycle, control, publication, and evidence
records.

## Ownership classes

- **Runtime content** — substantive stage content requested from the runtime/model.
- **AIDD workflow record** — canonical lifecycle or validator output derived by core services.
- **AIDD control document** — a core/operator control input or recovery instruction, never a
  runtime completion target.
- **Interview ledger** — durable questions, operator answers, and their merge history.
- **Raw candidate evidence** — append-only runtime/adapter evidence retained for diagnosis; it is
  not a validated stage output.

## Canonical matrix

| Declared document path pattern | Stage(s) | Ownership class | Create | Mutate | Validate | Publish | UI authoring |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `workitems/<id>/stages/<stage>/output/idea-brief.md` | `idea` | Runtime content | Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | No; read-only |
| `workitems/<id>/stages/<stage>/output/research-notes.md` | `research` | Runtime content | Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | No; read-only |
| `workitems/<id>/stages/<stage>/output/plan.md` | `plan` | Runtime content | Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | No; read-only |
| `workitems/<id>/stages/<stage>/output/review-spec-report.md` | `review-spec` | Runtime content | Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | No; read-only |
| `workitems/<id>/stages/<stage>/output/tasklist.md` | `tasklist` | Runtime content | Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | No; read-only |
| `workitems/<id>/stages/<stage>/output/implementation-report.md` | `implement` | Runtime content | Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | No; read-only |
| `workitems/<id>/stages/<stage>/output/review-report.md` | `review` | Runtime content | Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | No; read-only |
| `workitems/<id>/stages/<stage>/output/qa-report.md` | `qa` | Runtime content | Runtime adapter | Runtime attempt only | AIDD validator | AIDD core after validation | No; read-only |
| `workitems/<id>/stages/<stage>/output/questions.md` | Any stage | Interview ledger | AIDD interview controller | AIDD interview controller | AIDD interview controller | AIDD core | Controlled Write/Preview |
| `workitems/<id>/stages/<stage>/output/answers.md` | Any stage | Interview ledger | Operator answer service | AIDD merge service | AIDD interview controller | AIDD core | Controlled Write/Preview |
| `workitems/<id>/stages/<stage>/stage-result.md` | Any stage | AIDD workflow record | AIDD lifecycle service | AIDD lifecycle service | AIDD validator coordinator | AIDD publication service | No; read-only |
| `workitems/<id>/stages/<stage>/validator-report.md` | Any stage | AIDD workflow record | AIDD validator coordinator | AIDD validator coordinator | AIDD validator coordinator | AIDD publication service | No; read-only |
| `workitems/<id>/stages/<stage>/repair-brief.md` | Any stage | AIDD control document | AIDD repair controller | AIDD repair controller | AIDD repair controller | AIDD repair controller | No; read-only |
| `workitems/<id>/stages/<stage>/operator-requests/request-<n>.md` | Any stage | AIDD control document | Operator request service | Operator request service | AIDD input validator | AIDD intervention service | Controlled Write/Preview |
| `reports/runs/<id>/attempts/<attempt>/runtime.log` | Any stage | Raw candidate evidence | Runtime adapter | Runtime adapter append-only | AIDD evidence reader | AIDD evidence index | No; read-only |
| `reports/runs/<id>/attempts/<attempt>/runtime.jsonl` | Any stage | Raw candidate evidence | Runtime adapter | Runtime adapter append-only | AIDD evidence reader | AIDD evidence index | No; read-only |
| `reports/runs/<id>/attempts/<attempt>/events.jsonl` | Any stage | Raw candidate evidence | Runtime adapter | Runtime adapter append-only | AIDD evidence reader | AIDD evidence index | No; read-only |
| `reports/runs/<id>/attempts/<attempt>/runtime-exit.json` | Any stage | Raw candidate evidence | Runtime adapter | AIDD attempt finalizer | AIDD evidence reader | AIDD evidence index | No; read-only |
| `reports/runs/<id>/attempts/<attempt>/operator-requests.jsonl` | Any stage | Raw candidate evidence | AIDD adapter bridge | AIDD adapter bridge append-only | AIDD evidence reader | AIDD evidence index | No; read-only |
| `reports/runs/<id>/attempts/<attempt>/operator-decisions.jsonl` | Any stage | Raw candidate evidence | Operator decision service | AIDD decision ledger append-only | AIDD evidence reader | AIDD evidence index | No; read-only |

`context/*.md`, upstream stage inputs, and generated `artifact-index.json`/run manifests are
read-only inputs or system telemetry rather than stage-local declared documents; their existing
ownership remains covered by the workspace and run-manifest contracts. They must not be added as a
second owner for any row above.

## Permission rules

1. A runtime adapter may write only the Runtime content rows for its current attempt and append
   Raw candidate evidence. It must not create or mutate AIDD workflow, control, or interview
   records as if they were stage completion outputs.
2. AIDD validators may read runtime content and raw evidence and may create canonical workflow
   records. They do not rewrite the substantive runtime content to hide a validation failure.
3. AIDD publication may expose a validated record downstream, but publication is not an
   additional owner and does not grant UI editing permission.
4. Operator authoring is limited to the explicitly marked controlled Write/Preview rows. A UI
   must never edit generated runtime content, validator reports, stage results, repair briefs, or
   raw evidence in place.
5. Any path declared in a stage contract but absent from this matrix is a contract error. Any
   path appearing in more than one row or with conflicting ownership classes is a contract
   error; fail closed before stage execution.
