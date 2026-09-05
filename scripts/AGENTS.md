# AGENTS.md

This directory contains maintainer checks, scenario entrypoints, and release tooling.

## Rules

- Keep reusable product behavior in the package; scripts should expose bounded maintainer
  operations with explicit inputs, exit status, and inspectable failure evidence.
- Keep check commands deterministic and separate from publishing, provider execution, and
  credential setup. A local validation must not silently start those operations.
- Preserve timeouts, safe argument handling, and temporary workspace isolation for subprocesses.
- Run Ruff and mypy for changed Python scripts plus their focused tests. Keep Makefile,
  contributor guidance, and CI command routing aligned when changing an entrypoint.
- Use the `release-publish` skill before release preparation or publication; existing scoped
  authorization remains valid, and local preflight does not itself authorize a release.
