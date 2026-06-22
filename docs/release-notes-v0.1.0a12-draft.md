# Release Notes: v0.1.0a12

Status: draft, not tagged or published.

These are prerelease notes for the `v0.1.0a12` hotfix candidate.

Current release-candidate package version: `0.1.0a12`.
Latest published prerelease before this candidate: `0.1.0a11`, superseded by this
hotfix candidate.
Latest accepted published prerelease evidence before this candidate: `0.1.0a10`.

## Summary

This prerelease is a narrow hotfix for `aidd run logs`. It supersedes the
published `0.1.0a11` package, where exact-PyPI `AIDD-LIVE-011` found that raw
runtime logs containing Rich-markup-like bracket text could crash CLI log
inspection. AIDD remains alpha software for local evaluation and controlled
operator trials.

## User-visible changes

- `aidd run logs` now prints saved raw runtime logs literally, with Rich markup
  and highlighting disabled for the log body.
- The command shape and output intent are unchanged: headers, log paths,
  `--tail`, `--lines`, latest-run resolution, missing-run handling, and
  ambiguous-run handling are preserved.
- Focused CLI regression coverage now includes raw log text such as
  `[/, /a, /a/b, /a/b/c.py]`.
- Source/local-wheel `AIDD-LIVE-011` run `eval-live-011-opencode-20260622T133433Z`
  passed through terminal QA after the fix, including the prior public log
  inspection boundary.

## Compatibility

- Existing CLI behavior remains compatible for `aidd`, `aidd --help`,
  `aidd doctor`, `aidd init`, `aidd run`, `aidd stage ...`, and
  `aidd ui --work-item ...`.
- Runtime adapters, runtime protocol, stage contracts, prompts, manifests, and
  UI APIs are unchanged.
- Runtime launches still require an explicit runtime id; no hidden fallback is
  added.
- Runtime binaries and authentication remain external operator prerequisites.
- The `0.1.0a12` package must not be described as the latest accepted published prerelease until GitHub Release, PyPI, `pipx`, and `uv tool` verification succeeds.

## Installation channels

Supported prerelease channels remain:

- PyPI package installed with `pipx`
- `uv tool install`
- source checkout

Docker/GHCR remains outside the supported alpha release contract.

## Known limitations

- AIDD remains alpha software for local evaluation and controlled operator
  trials.
- Live E2E evidence remains local manual audit evidence and is not CI/CD, not a
  release workflow, not GitHub Actions, and not a release gate.
- The hotfix release uses the completed source/local-wheel `AIDD-LIVE-011` pass
  as live evidence. Exact-PyPI live proof for `0.1.0a12` can be collected after
  publication, but is not a release blocker.
- Provider smoke reproducibility depends on the operator shell environment;
  provider binaries outside the Codex app's default non-interactive PATH should
  be run through a login shell or explicit PATH prefix.
- Package verification is not accepted until the GitHub Release workflow and
  independent local `pipx` plus `uv tool` checks pass for `0.1.0a12`.

## Release checklist

- GitHub Release target: `release/v0.1.0a12`.
- Release branch: `release/v0.1.0a12`.
- Release workflow: run by GitHub Release `published` event only.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a12/` after publish.
- `pipx` and `uv tool` verification: required before accepting package-channel
  evidence.
