---
name: runtime-log-triage
description: Analyze runtime and adapter logs to identify the first decisive failure signal and classify it correctly.
---

# runtime-log-triage

## Use when

- A scenario or stage run failed.
- You need to separate document, model, adapter, auth, permission, timeout, or environment failures.

## Procedure

1. Read `runtime.log`, `events.jsonl`, and `validator-report.md`.
2. Identify the earliest decisive signal.
3. Separate runtime startup failures from document validation failures.
4. Check whether a user question should have blocked the run.
5. Write a short `log-analysis.md` that names the first cause, not just the final symptom.

## Output

Return the likely failure class and the evidence chain that supports it.
