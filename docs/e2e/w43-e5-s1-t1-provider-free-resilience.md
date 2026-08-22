# W43-E5-S1-T1 provider-free resilience suite

This document records the deterministic scenario contract for the Codex-only Wave 43
resilience lane. It does not claim a provider-authenticated run. The suite uses sanitized
fixtures and the production interview/tasklist parsers plus the retained failure-corpus replay
helpers.

## Run

```bash
uv run --extra dev python -m aidd.evals.resilience_scenarios \
  --output .aidd/reports/w43-e5-s1-t1-resilience.json
```

The same suite is available as the manual deterministic scenario
`AIDD-DETERMINISTIC-005` in `harness/scenarios/deterministic/w43-resilience-scenarios.yaml`.

## Coverage

The manifest at
`tests/fixtures/w43-e5-s1-t1-resilience/resilience-scenarios.json` contains ten scenarios:

- missing and contradictory runtime workflow drafts;
- service-owned placeholder content;
- malformed question after resume and a safe candidate variant;
- safe tasklist presentation;
- eleven malformed cards and one malformed card with source locations;
- primary/related root-cause findings;
- non-repair resume accounting.

Each result retains terminal state, attempt modes, automatic repair budget, canonical records,
workflow records, observed/root/related findings, parser issue count, and raw evidence references.
The report is fail-closed: missing evidence, an empty ledger/workflow record, an invalid budget,
an unlocated malformed card, or a ready/blocked state that disagrees with its findings produces a
failed scenario and a non-zero module exit code. Safe presentation variants are accepted only
when the parsed executable task/question meaning is byte-for-byte equivalent at the typed model
level; no semantic fields are inferred.

The suite is provider-free and therefore does not replace the later repair-extension scenarios
or the Codex live repetition lane.
