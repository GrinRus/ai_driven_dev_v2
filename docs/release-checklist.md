# Release Checklist

Use this checklist for GitHub Release-driven package releases of `ai_driven_dev_v2`.

## 1. Pre-release preparation

- [ ] Working tree is clean and scoped to intended release changes.
- [ ] `pyproject.toml` `project.version` is set to the intended release version.
- [ ] If the previous version was already published, `main` has first moved to the next
  development version and the release branch uses a unique unpublished version.
- [ ] Local quality gate passes:

```bash
uv sync --locked --extra dev
uv run --extra dev ruff check .
uv run --extra dev python -m mypy src
uv run --extra dev pytest -q
```

- [ ] Optional smoke sanity:

```bash
uv run aidd doctor
```

- [ ] Source-of-truth audit is current for the release-prep slice:
  `README.md`, `docs/product/user-stories.md`, and
  `docs/architecture/target-architecture.md` match the code and release claims.
- [ ] Live E2E is not wired into GitHub Actions, CI/CD, or release workflows.

## 2. Create release branch and GitHub Release

- [ ] Create a release branch named exactly `release/v<project.version>`.
- [ ] Push the release branch.
- [ ] Open a release PR from `release/v<project.version>` to `main` and wait for
  deterministic CI to pass before publishing.
- [ ] If the release branch matches `main` exactly and GitHub cannot open a no-diff release
  PR, mark the release PR as N/A and run both `ci.yml` and `release.yml` through
  `workflow_dispatch` on the release branch instead.
- [ ] Create a draft GitHub Release with tag `v<project.version>` targeting the
  `release/v<project.version>` branch.
- [ ] Publish the GitHub Release only after the release branch is final.
- [ ] Do not push a tag to trigger publishing directly. The release workflow publishes only
  from the GitHub Release `published` event.
- [ ] Confirm the `release` GitHub Actions workflow started from the GitHub Release event.

Example:

```bash
git switch -c release/v0.1.0a3 main
git push -u origin release/v0.1.0a3
```

Release workflow validation requires:

- the release tag to exactly match `v<project.version>`;
- the branch to be named exactly `release/<tag>`, for example `release/v0.1.0a3`;
- the release tag commit to match the remote release branch HEAD.

## 3. Package publish checklist (PyPI)

- [ ] `quality` job passed on Python 3.12, 3.13, and 3.14.
- [ ] `build` job passed.
- [ ] `publish-pypi` job passed.
- [ ] Published version appears on PyPI for `ai-driven-dev-v2`.
- [ ] Installed package resolves and runs:

```bash
pipx install ai-driven-dev-v2==<version>
aidd --version
aidd doctor
```

## 4. Container support

AIDD does not publish or support Docker/GHCR images during the alpha phase.

- [ ] Release notes do not advertise Docker or GHCR as supported alpha channels.
- [ ] Owner cleanup task is tracked for stale public GHCR tags from earlier prerelease
  attempts, especially any stale `latest` tag.
- [ ] Reintroducing container support is tracked as a future design/release task, not a
  hidden part of the current release.

## 5. Release verification evidence requirements

- [ ] `verify-pypi-install` job passed and its logs include `aidd --version` and `aidd doctor`.
- [ ] `verify-uv-tool-install` job passed and its logs include `aidd --version` and `aidd doctor`.
- [ ] These two jobs are required release evidence for published GitHub Release alpha builds.

Prerequisite refresh before evidence capture:

- the GitHub Release tag must point at the release branch HEAD under test;
- PyPI or TestPyPI publishing credentials must be available to the release workflow;
- if any prerequisite is missing, record an explicit blocker instead of treating release
  evidence as refreshed.

Manual local live-audit notes:

- Live E2E is no longer a release gate.
- Live E2E is manual local operator audit evidence, not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- Live E2E must not be added to GitHub Actions, CI/CD, or release workflows.
- If maintainers want a post-release operator audit, run the local black-box evaluator
  from a prepared source checkout:

```bash
uv run python -m aidd.harness.live_e2e_black_box <manifest> --runtime <runtime> --work-root /tmp/aidd-live-e2e --report-root .aidd/reports/evals
```

- The local evaluator validates the selected provider command before clone/install;
  `AIDD_EVAL_CODEX_COMMAND`, `AIDD_EVAL_OPENCODE_COMMAND`, or
  `AIDD_EVAL_CLAUDE_CODE_COMMAND` are optional wrapper overrides for `adapter-flags` mode.
- That audit is separate from publish/installability evidence and must not block package releases.

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

## 6. Changelog and release notes checklist

- [ ] Summarize user-visible changes for this release.
- [ ] Include task ids and major behavior/contract updates.
- [ ] Include known limitations and blocked items if they affect operators.
- [ ] Publish GitHub release notes through the GitHub Release.

## 7. Post-release follow-up

- [ ] Confirm roadmap/backlog status reflects shipped work.
- [ ] Open follow-up issues for any deferred release defects.
- [ ] Announce release with links to package and notes.

## Release attempt evidence log

Historical release attempts below may mention GHCR because earlier alpha candidates
temporarily published container images. That evidence is retained for traceability only and
does not make Docker/GHCR a supported alpha distribution channel.

### `v0.1.0a4` accepted evidence on 2026-05-23

- Tag: `v0.1.0a4`
- Release branch: `release/v0.1.0a4`
- Commit: `40a611373c25a90244c188d9c0ecdd2e3e778033`
- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a4`
- Workflow run: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/26325967424`
- Result: accepted release/install evidence.
- Job results: `quality` passed on Python 3.12, 3.13, and 3.14; `build` passed;
  `publish-pypi` passed; `verify-pypi-install` passed; `verify-uv-tool-install` passed.
- Build evidence: release tag `v0.1.0a4` matched `project.version` `0.1.0a4`, and the
  release tag commit matched the remote `release/v0.1.0a4` branch HEAD.
- PyPI output: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a4/`.
- PyPI files: `ai_driven_dev_v2-0.1.0a4-py3-none-any.whl` and
  `ai_driven_dev_v2-0.1.0a4.tar.gz`.
- `pipx` verification installed `ai-driven-dev-v2==0.1.0a4`; `aidd --version` returned
  `aidd 0.1.0a4`, and `aidd doctor` reported `Version 0.1.0a4`.
- `uv tool` verification installed `ai-driven-dev-v2==0.1.0a4`; `aidd --version` returned
  `aidd 0.1.0a4`, and `aidd doctor` reported `Version 0.1.0a4`.
- Independent local package smoke resolved `ai-driven-dev-v2==0.1.0a4` through
  isolated `pipx` and `uv tool` runs and returned `aidd 0.1.0a4`.
- No Docker/GHCR artifact is part of the supported `v0.1.0a4` release contract.

### `v0.1.0a3` accepted evidence on 2026-05-22

- Tag: `v0.1.0a3`
- Release branch: `release/v0.1.0a3`
- Commit: `b229f480f071db914ed8ef3b86792d99b1071033`
- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a3`
- Workflow run: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/26283095065`
- Result: accepted release/install evidence.
- Job results: `quality` passed on Python 3.12, 3.13, and 3.14; `build` passed;
  `publish-pypi` passed; `verify-pypi-install` passed; `verify-uv-tool-install` passed.
- Build evidence: release tag `v0.1.0a3` matched `project.version` `0.1.0a3`, and the
  release tag commit matched the remote `release/v0.1.0a3` branch HEAD.
- PyPI output: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a3/`.
- `pipx` verification installed `ai-driven-dev-v2==0.1.0a3`; `aidd --version` returned
  `aidd 0.1.0a3`, and `aidd doctor` reported `Version 0.1.0a3`.
- `uv tool` verification installed `ai-driven-dev-v2==0.1.0a3`; `aidd --version` returned
  `aidd 0.1.0a3`, and `aidd doctor` reported `Version 0.1.0a3`.
- Independent local package smoke also resolved `ai-driven-dev-v2==0.1.0a3` through
  isolated `pipx` and `uv tool` runs and returned `aidd 0.1.0a3`.
- No Docker/GHCR artifact is part of the supported `v0.1.0a3` release contract.

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
