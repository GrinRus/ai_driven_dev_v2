# AGENTS.md

This directory owns evaluation policies, target catalogs, and dated execution evidence.

## Rules

- Prefer public repositories with stable setup and bounded patch budgets.
- Record exact repository pins in scenario runs.
- Treat verification commands as mandatory, not advisory.
- Distinguish current policy from historical reports. Preserve failed attempts, run identifiers,
  pins, logs, and reported results; record later corrections or superseding evidence explicitly.
- Use the relevant evaluation skill for execution and evidence collection; documentation edits
  alone do not require launching a provider or preparing a target repository.
