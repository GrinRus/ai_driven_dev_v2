# Release Checklist

Use this checklist for tagged releases of `ai_driven_dev_v2`.

## 1. Pre-release preparation

- [ ] Working tree is clean and scoped to intended release changes.
- [ ] `pyproject.toml` `project.version` is set to the intended release version.
- [ ] Local quality gate passes:

```bash
uv sync --extra dev
uv run --extra dev ruff check .
uv run --extra dev python -m mypy src
uv run --extra dev pytest -q
```

- [ ] Optional smoke sanity:

```bash
uv run aidd doctor
```

## 2. Create and push release tag

- [ ] Create an annotated release tag that exactly matches `v<project.version>`.

Example:

```bash
git tag -a v0.1.0a0 -m "Release v0.1.0a0"
git push origin v0.1.0a0
```

- [ ] Confirm the `release` GitHub Actions workflow started from the tag push.

## 3. Package publish checklist (PyPI)

- [ ] `build` job passed.
- [ ] `publish-pypi` job passed.
- [ ] Published version appears on PyPI for `ai-driven-dev-v2`.
- [ ] Installed package resolves and runs:

```bash
pipx install ai-driven-dev-v2==<version>
aidd --version
aidd doctor
```

## 4. Container publish checklist (GHCR)

- [ ] `publish-container` job passed.
- [ ] Container image is available at:
  `ghcr.io/<owner>/ai-driven-dev-v2:<tag>`
- [ ] Required image tags were produced:
  - exact release tag (`vX.Y.Z` or release prerelease tag);
  - immutable `sha-<git-sha>`;
  - semver aliases (`vX.Y`, `vX`) when applicable;
  - `latest` only for stable releases.

## 5. Release verification evidence requirements

- [ ] `verify-pypi-install` job passed and its logs include `aidd --version` and `aidd doctor`.
- [ ] `verify-uv-tool-install` job passed and its logs include `aidd --version` and `aidd doctor`.
- [ ] `verify-ghcr-install` job passed and its logs include containerized `aidd --version` and `aidd doctor`.
- [ ] These three jobs are required release evidence for tagged builds.

Prerequisite refresh before evidence capture:

- a release candidate tag must point at the commit under test;
- PyPI or TestPyPI publishing credentials must be available to the release workflow;
- GHCR publishing credentials and Docker access must be available for container verification;
- if any prerequisite is missing, record an explicit blocker instead of treating release
  evidence as refreshed.

Manual live-audit notes:

- Live E2E is no longer a release gate.
- If maintainers want a post-release operator audit, run `manual-live-e2e` explicitly from GitHub Actions.
- That manual workflow validates the selected provider command before clone/install;
  `AIDD_EVAL_CODEX_COMMAND` or `AIDD_EVAL_OPENCODE_COMMAND` are optional wrapper
  overrides for `adapter-flags` mode.
- That audit is separate from publish/installability evidence and must not block tagged releases.

Suggested package-path verification:

```bash
pipx install ai-driven-dev-v2==<version>
aidd --version
aidd doctor
pipx uninstall ai-driven-dev-v2
```

Suggested `uv tool` verification:

```bash
uv tool install ai-driven-dev-v2==<version>
aidd --version
aidd doctor
uv tool uninstall ai-driven-dev-v2
```

Suggested container-path verification:

```bash
docker run --rm ghcr.io/<owner>/ai-driven-dev-v2:<tag> aidd --version
docker run --rm ghcr.io/<owner>/ai-driven-dev-v2:<tag> aidd doctor
```

## 6. Changelog and release notes checklist

- [ ] Summarize user-visible changes for this release.
- [ ] Include task ids and major behavior/contract updates.
- [ ] Include known limitations and blocked items if they affect operators.
- [ ] Publish GitHub release notes for the tag.

## 7. Post-release follow-up

- [ ] Confirm roadmap/backlog status reflects shipped work.
- [ ] Open follow-up issues for any deferred release defects.
- [ ] Announce release with links to package, container image, and notes.

## Release attempt evidence log

### `v0.1.0a0` attempt on 2026-05-06

- Tag: `v0.1.0a0`
- Commit: `aa3655998227e6da2a979b06d2c87543adbf4734`
- Workflow run: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/25437182363`
- Result: blocked, not accepted release/install evidence.
- Job results: `build` passed, `publish-container` passed, `publish-pypi` failed, `verify-pypi-install` skipped, `verify-uv-tool-install` skipped, `verify-ghcr-install` skipped.
- PyPI blocker: Trusted Publishing token exchange failed with `invalid-publisher`; claims included `sub=repo:GrinRus/ai_driven_dev_v2:environment:pypi`, workflow `.github/workflows/release.yml`, and environment `pypi`.
- Required unblock: configure the PyPI trusted publisher for repository `GrinRus/ai_driven_dev_v2`, workflow `.github/workflows/release.yml`, environment `pypi`, and package `ai-driven-dev-v2`, then rerun release verification without changing the tag/version ad hoc.
- Partial GHCR output: `ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a0`, `ghcr.io/grinrus/ai-driven-dev-v2:sha-aa36559`, and `ghcr.io/grinrus/ai-driven-dev-v2:latest` were pushed with digest `sha256:994a1134a2b10e6c68c7abccfc3c0a4e470e1ec51143979dd9c7e8a9ac408918`; treat this as partial publish evidence only because `verify-ghcr-install` was skipped.
- Follow-up applied after the attempt: release workflow now disables docker/metadata-action automatic `latest` tagging (`flavor: latest=false`) so prerelease tags depend only on the explicit stable-tag `latest` condition.

### `v0.1.0a1` attempt on 2026-05-06

- Tag: `v0.1.0a1`
- Commit: `a58edc0d0267a5ca528efab3f4caaf8e7b9854c6`
- Workflow run: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/25446909468`
- Result: blocked, not accepted release/install evidence.
- Job results: `build` passed, `publish-pypi` passed, `verify-pypi-install` passed, `verify-uv-tool-install` passed, `publish-container` passed, `verify-ghcr-install` failed.
- PyPI output: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a1/`.
- PyPI install evidence was partial only: `pipx` and `uv tool` installed `ai-driven-dev-v2==0.1.0a1`, but installed `aidd --version` and `aidd doctor` still reported `0.1.0a0`.
- GHCR blocker: `verify-ghcr-install` attempted `docker pull ghcr.io/GrinRus/ai-driven-dev-v2:v0.1.0a1`, and Docker rejected the uppercase owner as `invalid reference format`; the publish job itself had produced lowercase tags.
- Partial GHCR output: `ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a1` and `ghcr.io/grinrus/ai-driven-dev-v2:sha-a58edc0` were pushed without `latest`, digest `sha256:b4d8d247288a340801b80458db5fa1a3804a5d79fb939ae687d5f86bd507e32c`.
- Follow-up applied after the attempt: release verification lowercases the GHCR owner before `docker pull`, and the CLI version now resolves from package metadata with a source-tree fallback.

### `v0.1.0a2` accepted evidence on 2026-05-06

- Tag: `v0.1.0a2`
- Commit: `92c893dbd830292ecab5b684a0a4044ef61a67d6`
- Workflow run: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/25448551936`
- Result: accepted release/install evidence.
- Job results: `build` passed, `publish-pypi` passed, `verify-pypi-install` passed, `verify-uv-tool-install` passed, `publish-container` passed, `verify-ghcr-install` passed.
- Build evidence: release tag `v0.1.0a2` matched `project.version` `0.1.0a2`; `uv build` produced `dist/ai_driven_dev_v2-0.1.0a2.tar.gz` and `dist/ai_driven_dev_v2-0.1.0a2-py3-none-any.whl`.
- PyPI output: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a2/`.
- `pipx` verification installed `ai-driven-dev-v2==0.1.0a2`; `aidd --version` returned `aidd 0.1.0a2`, and `aidd doctor` reported `Version 0.1.0a2`.
- `uv tool` verification installed `ai-driven-dev-v2==0.1.0a2`; `aidd --version` returned `aidd 0.1.0a2`, and `aidd doctor` reported `Version 0.1.0a2`.
- GHCR output: `ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a2` and `ghcr.io/grinrus/ai-driven-dev-v2:sha-92c893d` were pushed with digest `sha256:fc344386c4909d0dcfc74753583fc32c469621212e133f52fce2fbd39147d45d`; no `latest` tag was produced for this prerelease.
- GHCR verification pulled `ghcr.io/grinrus/ai-driven-dev-v2:v0.1.0a2`; containerized `aidd --version` returned `aidd 0.1.0a2`, and `aidd doctor` reported `Version 0.1.0a2`.

## Related references

- [Distribution and Development](./architecture/distribution-and-development.md)
- [README](../README.md)
