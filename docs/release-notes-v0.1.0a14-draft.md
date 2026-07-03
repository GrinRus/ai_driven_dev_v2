# Release Notes: v0.1.0a14

Status: published on 2026-07-03; accepted release/install evidence.

Latest accepted published prerelease evidence: `0.1.0a14`.

The `0.1.0a14` package is accepted package-channel evidence after the GitHub Release
workflow published to PyPI and verified `pipx` plus `uv tool` installability.

## Summary

This prerelease records backlog and live-evaluation preparation work after the accepted
`v0.1.0a13` package-channel evidence. It closes obsolete Wave 30 release-prep state by
reconciling it with accepted release evidence, and it adds a candidate-only Rich live
product-evaluation scenario draft plus setup audit notes for future maintained coverage
decisions.

## User-visible changes

- Wave 30 release-readiness backlog state is closed through reconciliation instead of
  attempting to republish immutable historical package versions.
- The manual external eval catalog now documents candidate-only product-evaluation work
  separately from the maintained scenario set.
- A candidate Rich product-evaluation manifest is available for manual evaluation planning.
- Setup audit evidence records Pydantic, FastAPI, Rich, and Ruff candidate findings.

## Compatibility

- CLI behavior, stage contracts, runtime adapters, and release workflows are unchanged.
- No manual external eval automation is added to CI/CD or release workflows.
- The candidate product-evaluation manifest is not part of the maintained scenario matrix.
- Runtime binaries and authentication remain external operator prerequisites.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported alpha release contract.

## Known limitations

- AIDD remains alpha software for local evaluation and controlled operator trials.
- Manual external eval evidence remains local operator audit evidence and is not CI/CD,
  not a release workflow, not GitHub Actions, and not a release gate.
- Package verification passed through the `v0.1.0a14` GitHub Release workflow and
  independent install checks.

## Release checklist

- GitHub Release target: `release/v0.1.0a14`.
- Release branch: `release/v0.1.0a14`.
- Release workflow: run by GitHub Release `published` event only.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a14/`.
- `pipx` and `uv tool` verification: accepted package-channel evidence.
