# Distribution and Development

## 1. Purpose

This document fixes how AIDD is distributed, installed, and developed.

## 2. Delivery channels

AIDD is intended to ship through three primary channels:

- PyPI for `pipx install ai-driven-dev-v2`
- `uv tool install ai-driven-dev-v2`
- container images such as `ghcr.io/grinrus/ai-driven-dev-v2`

Source checkout remains the default contributor path.

Installed live E2E is a separate manual operator-audit path:

- contributors work from source checkout;
- live scenarios are selected manually from the maintained live catalog;
- the harness installs that wheel via `uv tool` and runs installed `aidd` from the target repository root.

## 3. Runtime binaries

AIDD does not bundle third-party runtimes.

Operators install and authenticate runtime binaries separately, for example:

- Claude Code
- Codex
- OpenCode

The AIDD CLI only probes for them and launches them through adapters.

## 4. Local development toolchain

Required:

- Python 3.12+
- `uv`

Optional, depending on work:

- runtime CLIs for adapter development,
- Docker for container testing.

## 5. Development loop

Standard loop:

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy src
uv run pytest
```

Useful bootstrap commands:

```bash
uv run aidd doctor
uv run aidd init --work-item WI-001
```

## 6. Repository-owned artifacts

The repository itself should contain:

- docs,
- contracts,
- prompt packs,
- scenario manifests,
- Python code,
- tests,
- CI workflows.

Runtime credentials and local operator secrets must stay outside the repository.

## 7. CI layers

Recommended CI structure:

- pull request: lint, typecheck, unit tests, deterministic fixture checks, and package build
- main branch: the same deterministic checks or a wider deterministic matrix
- manual workflows: live external audits
- release: build, publish, installability checks, and container verification

## 8. Release flow

Recommended release flow:

1. tag a release candidate,
2. build the Python package,
3. run installability verification,
4. publish to PyPI,
5. publish container image,
6. publish release notes.

Operator-oriented step-by-step release execution lives in `docs/release-checklist.md`.

## 9. Container image tagging rules

Container images are published to `ghcr.io/<owner>/ai-driven-dev-v2` from release tags that
start with `v`.

Tag set:

- exact release tag, for example `v1.4.2`;
- semantic aliases `v1.4` and `v1`;
- immutable commit tag `sha-<git-sha>`;
- `latest` only for stable tags without a prerelease suffix.

## 10. PyPI release tagging rules

PyPI publishing accepts release tags that:

- start with `v`;
- use `v<major>.<minor>.<patch>` with optional PEP 440 suffix (`aN`, `bN`, `rcN`, `.postN`, `.devN`);
- exactly match `v<project.version>` from `pyproject.toml`.

If a release tag fails format or version-alignment checks, the release workflow fails before package publishing.

## 11. Versioning policy

This bootstrap uses a normal package version for releases.

Document contracts and prompt packs do not use foldered version trees. Provenance is tracked through Git revision and file hashes.

## 12. Summary

AIDD is developed like a normal Python open-source project, but with first-class contracts, prompt packs, scenarios, and runtime adapters.
