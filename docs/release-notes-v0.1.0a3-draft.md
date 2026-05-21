# Draft Release Notes: v0.1.0a3

Status: draft, not tagged or published.

## Summary

This release candidate prepares AIDD for controlled operator-trial readiness while keeping
the project explicitly in prerelease alpha status until manual live evidence is complete.

## User-visible changes

- Tightened live E2E quality accounting so untracked target-repository changes and
  implementation-report touched-file mismatches cannot be hidden from operator review.
- Clarified review and QA evidence boundaries so optional broader checks do not become
  false release blockers unless they expose a concrete defect.
- Focused Hono live scenario verification on authored-task acceptance surfaces.
- Preserved harness command `PATH` handling for installed live verification commands.
- Added beta-readiness release-process guardrails: deterministic release quality checks,
  locked dependency sync, and explicit CI/CD exclusion for live E2E.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported prerelease contract.

## Known limitations

- AIDD is still not ready for unattended production automation.
- Live E2E remains manual audit evidence and is not a CI/CD or release gate.
- Runtime binaries and authentication are external operator prerequisites.

## Release checklist

- Confirm `pyproject.toml` version is set to `0.1.0a3` before tagging.
- Run deterministic local gates.
- Confirm the release workflow quality, build, publish, `pipx`, and `uv tool` verification
  jobs pass for the tag.
- Refresh manual live evidence separately from release automation when maintainers need an
  operator-quality audit.
