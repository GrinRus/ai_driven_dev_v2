# Draft Release Notes: v0.1.0a3

Status: draft, not tagged or published.

## Summary

This release candidate prepares AIDD for controlled operator-trial readiness while keeping
the project explicitly in prerelease alpha status until manual live evidence is complete.

## User-visible changes

- Tightened live E2E quality accounting so untracked target-repository changes and
  implementation-report touched-file mismatches cannot be hidden from operator review.
- Hardened live quality parsing for review verdict prefixes, QA verdict labels, and
  implementation evidence shapes so quality gates reflect the generated evidence more
  consistently.
- Clarified review and QA evidence boundaries so optional broader checks do not become
  false release blockers unless they expose a concrete defect.
- Focused Hono live scenario verification on authored-task acceptance surfaces.
- Preserved harness command `PATH` handling for installed live verification commands.
- Added beta-readiness release-process guardrails: deterministic release quality checks,
  locked dependency sync, and explicit GitHub Actions exclusion for live E2E.
- Preserved operator ownership of `answers.md` across runtime attempts: model output can no
  longer create, rewrite, delete, or resolve operator-owned answers, and malformed
  runtime-created answers for newly asked questions are normalized back to canonical empty
  answers.
- Fixed selected trust-boundary handling in QA so generated QA output can be evaluated
  without silently widening the intended review scope.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported prerelease contract.

## Known limitations

- AIDD is still not ready for unattended production automation.
- Live E2E remains local manual audit evidence and is not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- Runtime binaries and authentication are external operator prerequisites.

## Release checklist

- Confirm `pyproject.toml` version is set to `0.1.0a3` before creating the GitHub
  Release.
- Run deterministic local gates.
- Create `release/v0.1.0a3`, publish a GitHub Release tagged `v0.1.0a3` from that
  branch, and confirm the release workflow quality, build, publish, `pipx`, and `uv tool`
  verification jobs pass for the GitHub Release.
- Refresh manual live evidence locally, separately from release automation, when maintainers
  need an operator-quality audit.
