# Release Notes: v0.1.0a12

Status: published on 2026-06-22 and accepted after package-channel verification.

Published package version: `0.1.0a12`.
Latest accepted published prerelease: `0.1.0a12`.

Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed
for `v0.1.0a12`.

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
- The `0.1.0a12` package is accepted package-channel evidence after GitHub Release,
  PyPI, `pipx`, and `uv tool` verification succeeded.

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
- The hotfix release used the completed source/local-wheel `AIDD-LIVE-011` pass
  as live evidence. Exact-PyPI live proof for `0.1.0a12` can be collected after
  publication, but is not a release blocker.
- Provider smoke reproducibility depends on the operator shell environment;
  provider binaries outside the Codex app's default non-interactive PATH should
  be run through a login shell or explicit PATH prefix.
- Package verification is accepted: the GitHub Release workflow and independent local
  `pipx` plus `uv tool` checks passed for `0.1.0a12`.

## Release checklist

- GitHub Release target: `release/v0.1.0a12`.
- Release branch: `release/v0.1.0a12`.
- Release workflow: run by GitHub Release `published` event only.
- PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a12/`.
- `pipx` and `uv tool` verification: accepted package-channel evidence.
