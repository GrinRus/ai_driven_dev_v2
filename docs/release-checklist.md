# Release Checklist

Use this checklist for tagged releases of `ai_driven_dev_v2`.

## 1. Pre-release preparation

- [ ] Working tree is clean and scoped to intended release changes.
- [ ] `pyproject.toml` `project.version` is set to the intended release version.
- [ ] Local quality gate passes:

```bash
uv sync --extra dev
uv run ruff check .
uv run mypy src
uv run pytest
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

Manual live-audit notes:

- Live E2E is no longer a release gate.
- If maintainers want a post-release operator audit, run `manual-live-e2e` explicitly from GitHub Actions.
- That manual workflow requires the selected provider's runtime-command secret:
  `AIDD_EVAL_CODEX_COMMAND` or `AIDD_EVAL_OPENCODE_COMMAND`.
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

## Related references

- [Distribution and Development](./architecture/distribution-and-development.md)
- [README](../README.md)
