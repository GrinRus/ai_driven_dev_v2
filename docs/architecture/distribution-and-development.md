# Distribution and Development

## 1. Purpose

This document fixes how AIDD is distributed, installed, and developed during the alpha
phase.

## 2. Alpha delivery channels

AIDD alpha is supported through Python-first delivery channels:

- PyPI package for `pipx install ai-driven-dev-v2`
- `uv tool install ai-driven-dev-v2`
- source checkout for contributors and local development

Docker/GHCR images are not part of the alpha release contract.

Installed live E2E is a separate manual operator-audit path:

- contributors work from source checkout;
- live scenarios are selected manually from the maintained live catalog;
- the harness installs the artifact under test with `uv tool` and runs installed `aidd`
  from the target repository root.

## 3. Container support

AIDD does not publish or support Docker/GHCR images during the alpha phase.

Maintainers should remove or hide stale public GHCR tags, especially any stale `latest`
tag produced by earlier prerelease attempts. That cleanup requires repository/package owner
access and is not release evidence for the current alpha channel.

Container support may be reconsidered after:

- the runtime permission model is stable;
- release provenance is defined for container artifacts;
- operator workflows no longer depend on ambiguous local runtime credential behavior.

Reintroducing container support must be a dedicated design and release task, not an
implicit side effect of the Python package workflow.

## 4. Runtime binaries

AIDD does not bundle third-party runtimes.

Operators install and authenticate runtime binaries separately, for example:

- Claude Code
- Codex
- OpenCode

The AIDD CLI only probes for them and launches them through adapters.

## 5. Local development toolchain

Required:

- Python 3.12+
- `uv`

Optional, depending on work:

- runtime CLIs for adapter development and live E2E audits.

## 6. Development loop

Standard loop:

```bash
uv sync --locked --extra dev
uv run --extra dev ruff check .
uv run --extra dev python -m mypy src
uv run --extra dev pytest -q
```

Useful bootstrap commands:

```bash
uv run aidd doctor
uv run aidd init --work-item WI-001
```

## 7. Repository-owned artifacts

The repository itself should contain:

- docs,
- contracts,
- prompt packs,
- scenario manifests,
- Python code,
- tests,
- CI workflows.

Runtime credentials and local operator secrets must stay outside the repository.

## 8. CI layers

Recommended CI structure:

- pull request: lint, typecheck, unit tests, deterministic fixture checks, security checks,
  and package build
- main branch: the same deterministic checks or a wider deterministic matrix
- manual workflows: live external audits
- release: build, PyPI publish, `pipx` installability verification, and `uv tool`
  installability verification

## 9. Release flow

Recommended release flow:

1. set `pyproject.toml` to the intended release version,
2. tag a release candidate that exactly matches `v<project.version>`,
3. build the Python package,
4. publish to PyPI through Trusted Publishing,
5. verify installability through `pipx`,
6. verify installability through `uv tool`,
7. publish release notes.

Operator-oriented step-by-step release execution lives in `docs/release-checklist.md`.

Install evidence is valid only for a concrete release candidate or tagged release. A source
checkout can refresh prerequisites, workflow shape, and local tool availability, but it must
record missing tags or registry credentials as blockers instead of claiming package-channel
evidence.

## 10. PyPI release tagging rules

PyPI publishing accepts release tags that:

- start with `v`;
- use `v<major>.<minor>.<patch>` with optional PEP 440 suffix (`aN`, `bN`, `rcN`,
  `.postN`, `.devN`);
- exactly match `v<project.version>` from `pyproject.toml`.

If a release tag fails format or version-alignment checks, the release workflow fails before
package publishing.

After publishing a prerelease, `main` should move to the next development version, for
example from `0.1.0a2` to `0.1.0a3.dev0`, so source builds cannot collide with an already
published artifact.

## 11. Versioning policy

This bootstrap uses a normal package version for releases.

Document contracts and prompt packs do not use foldered version trees. Provenance is tracked
through Git revision and file hashes.

## 12. Summary

AIDD is developed like a normal Python open-source project, but with first-class contracts,
prompt packs, scenarios, and runtime adapters. During alpha, the public distribution contract
is PyPI plus `pipx`, `uv tool`, and source checkout.
