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
uv run --extra dev python -m mypy src scripts
uv run --extra dev pytest -q
```

- [ ] Optional smoke sanity:

```bash
uv run aidd doctor
```

- [ ] GitHub CLI is available to the maintainer shell. If `command -v gh` is empty but
  Homebrew installed the binary, use an explicit path for the release session, for
  example:

```bash
command -v gh || true
/opt/homebrew/bin/gh --version
GH_CLI="${GH_CLI:-/opt/homebrew/bin/gh}"
"${GH_CLI}" auth status
```

  Use `"${GH_CLI}" ...` for `pr`, `workflow`, `run`, and `release` commands in that
  shell. This is only a local maintainer ergonomics fallback; it does not change the
  release trigger. Releases still publish only through a GitHub Release `published`
  event, and direct tag-push publishing remains forbidden.

- [ ] Run the read-only release preflight helper before publishing. It checks local
  `uv`/`gh` availability, source version, branch name, remote tag absence, and PyPI
  version absence. It never creates tags, releases, or uploads:

```bash
python -m scripts.release.preflight --project-root . --version <version>
```

  If `gh` is installed outside `PATH`, pass the explicit binary:

```bash
python -m scripts.release.preflight --project-root . --version <version> --gh-binary "${GH_CLI}"
```

- [ ] Source-of-truth audit is current for the release-prep slice:
  `README.md`, `docs/product/user-stories.md`, and
  `docs/architecture/target-architecture.md` match the code and release claims.
- [ ] The explicit `uv` version used by every hosted CI and release setup step passes
  `uv lock --check` and a locked dependency-sync dry run.
- [ ] Manual external eval scenarios are not wired into GitHub Actions, CI/CD, or release workflows.

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
git switch -c release/v0.1.0a6 main
git push -u origin release/v0.1.0a6
```

Release workflow validation requires:

- the release tag to exactly match `v<project.version>`;
- the branch to be named exactly `release/<tag>`, for example `release/v0.1.0a6`;
- the release tag commit to match the remote release branch HEAD.

## 3. Package publish checklist (PyPI)

- [ ] `quality` job passed on Python 3.12, 3.13, and 3.14.
- [ ] `build` job passed.
- [ ] `publish-pypi` job passed.
- [ ] Published version appears on PyPI for `ai-driven-dev-v2`.
- [ ] Installed package resolves and runs:

```bash
pipx_release_root="$(mktemp -d)"
export PIPX_HOME="${pipx_release_root}/home"
export PIPX_BIN_DIR="${pipx_release_root}/bin"
python -m pipx install --backend pip ai-driven-dev-v2==<version>
"${PIPX_BIN_DIR}/aidd" --version
"${PIPX_BIN_DIR}/aidd" doctor
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
- [ ] Reconcile the published GitHub Release notes with the terminal workflow outcome. Record
  `publish-pypi`, `verify-pypi-install`, and `verify-uv-tool-install` separately as passed,
  failed, or skipped. Mark a package published-but-unverified if either install lane lacks
  passing evidence, and name a superseding release when one exists. Never leave draft or
  candidate-only status text on a published release.

Prerequisite refresh before evidence capture:

- the GitHub Release tag must point at the release branch HEAD under test;
- PyPI or TestPyPI publishing credentials must be available to the release workflow;
- if any prerequisite is missing, record an explicit blocker instead of treating release
  evidence as refreshed.

Manual external-audit notes:

- Manual external eval is not a release gate.
- Manual external eval is local operator audit evidence, not CI/CD, not a release workflow,
  not GitHub Actions, and not a release gate.
- Manual external eval scenarios must not be added to GitHub Actions, CI/CD, or release workflows.
- If maintainers want a post-release operator audit, use the runbooks and artifact
  policy in `docs/e2e/`.
- That audit is separate from publish/installability evidence and must not block package releases.

Suggested package-path verification:

```bash
pipx_evidence_root="$(mktemp -d)"
export PIPX_HOME="${pipx_evidence_root}/home"
export PIPX_BIN_DIR="${pipx_evidence_root}/bin"
python -m pipx install --backend pip ai-driven-dev-v2==<version>
"${PIPX_BIN_DIR}/aidd" --version
"${PIPX_BIN_DIR}/aidd" doctor
python -m pipx uninstall ai-driven-dev-v2
```

Suggested `uv tool` verification:

```bash
uv_evidence_root="$(mktemp -d)"
export UV_TOOL_DIR="${uv_evidence_root}/tools"
export UV_TOOL_BIN_DIR="${uv_evidence_root}/bin"
uv tool install ai-driven-dev-v2==<version>
"${UV_TOOL_BIN_DIR}/aidd" --version
"${UV_TOOL_BIN_DIR}/aidd" doctor
uv tool uninstall ai-driven-dev-v2
```

For isolated evidence, execute the entry points created in `PIPX_BIN_DIR` and
`UV_TOOL_BIN_DIR`. Do not replace them with `pipx run` or `uv tool run`, which resolve separate
temporary environments instead of proving that the preceding install produced a usable binary.

For checklist copy-in, maintainers may collect bounded release evidence with the
read-only evidence helper. The helper validates URLs and captured command outputs only;
it does not query GitHub, create releases, publish packages, or mutate local state:

```bash
python -m scripts.release.evidence_collector release-evidence.json
```

`release-evidence.json` should include `version`, `github_release_url`,
`release_workflow_url`, `pypi_url`, `pipx_version_output`, `pipx_doctor_output`,
`uv_tool_version_output`, and `uv_tool_doctor_output`.

## Maintainer release state

Maintainer source development package version: `0.1.0a22.dev0`.
Latest accepted published prerelease evidence: `0.1.0a21`.
No current release candidate is accepted from this development version.

Future beta readiness is not implied by alpha package publication. Beta claims require the
provider, browser, onboarding, project-set, provenance, approval, and install evidence defined
in `docs/product/user-stories.md`.

README install instructions resolve the latest published package from PyPI. The development
version is not a published release. Keep only the latest accepted package evidence below;
previous release notes and verification records remain in Git history and GitHub Releases.

A beta-oriented claim requires fresh evidence for the exact candidate.

Beta-oriented release note criteria:

- candidate identity is explicit: exact package version, release branch, GitHub Release
  target, commit, PyPI URL, and `pipx` plus `uv tool` verification evidence;
- clean UI onboarding evidence is fresh for the candidate and covers project selection,
  work item creation or resume, mandatory runner selection, selected-stage launch, logs,
  timeline, artifacts, and terminal active-run cleanup;
- provider evidence names the blocker class or pass result for `codex`, `claude-code`,
  `opencode`, and optional `qwen`; unavailable providers must remain explicit
  `auth/env` blockers and must not be replaced by `generic-cli`;
- Browser evidence covers onboarding, runner cards, selected-stage controls, Active Run,
  Timeline, Implement Review, Review Findings, QA Verdict, remediation, stale downstream
  badges, and Run History comparison, with screenshots/API snapshots kept out of Git
  unless they are intentionally curated;
- product-surface status is explicit for project-set grouping, prompt/workflow
  accountability, run comparison, remediation/backflow, and approval audit visibility;
- release notes include known limitations and blocked items without implying beta
  readiness, production readiness, or accepted package-channel evidence before publish
  verification succeeds.

## 6. Changelog and release notes checklist

- [ ] Summarize user-visible changes for this release.
- [ ] Include task ids and major behavior/contract updates.
- [ ] Include known limitations and blocked items if they affect operators.
- [ ] If release notes make a beta-oriented claim, cite the fresh candidate-specific
  provider, Browser, install, remediation, project-set, provenance/comparison, approval
  audit, and security evidence required above.
- [ ] Do not describe a `.dev0` source version as an accepted package release.
- [ ] Publish GitHub release notes through the GitHub Release.
- [ ] Replace draft/candidate status in the published GitHub Release body with each observed
  PyPI and install-verification job result, including explicit published-but-unverified,
  failure, skipped, or supersession status when applicable.

## 7. Post-release follow-up

- [ ] Confirm roadmap/backlog status reflects shipped work.
- [ ] Open follow-up issues for any deferred release defects.
- [ ] Announce release with links to package and notes.

## Latest accepted release evidence

### `v0.1.0a21` accepted evidence on 2026-09-01

- Tag: `v0.1.0a21`
- Release branch: `release/v0.1.0a21`
- Commit: `1d49477ee70145e80de760bf37e41bd2f211ced8`
- GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a21`
- Workflow run: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/33546307202`
- Result: accepted published prerelease and package-channel evidence.
- Job results: `quality` passed on Python 3.12, 3.13, and 3.14; `build` passed;
  `publish-pypi` passed; `verify-pypi-install` passed; `verify-uv-tool-install` passed.
- Build evidence: the release tag matched `project.version` `0.1.0a21`, and the tag commit
  matched the remote `release/v0.1.0a21` branch HEAD.
- PyPI output: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a21/`.
- Independent local `pipx` verification used an isolated `uv tool run --from pipx` runner;
  the installed `aidd` binary returned `aidd 0.1.0a21` and `aidd doctor` completed.
- Independent local `uv tool` verification installed `ai-driven-dev-v2==0.1.0a21`;
  the installed `aidd` binary returned `aidd 0.1.0a21` and `aidd doctor` completed.
- No Docker/GHCR artifact was published.
