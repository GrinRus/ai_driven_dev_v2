---
name: release-publish
description: Prepare, publish, or verify AIDD package releases through the release branch and GitHub Release flow, including dry-runs, install evidence, and accepted post-release follow-up.
---

# release-publish

## Use when

- You need to prepare, publish, verify, or record an AIDD package release.
- You need to create or validate a `release/v<project.version>` branch.
- You need to run release dry-runs or inspect release workflow evidence.
- You need to verify PyPI, `pipx`, or `uv tool` installability for a published version.
- You need the post-release version bump and evidence-recording follow-up.

Do not use this skill for manual live E2E execution. Use `live-e2e` for local live
operator audits.

## Select the requested operation

Prepare, inspect, publish, verify, or perform post-release follow-up as requested;
release inspection does not authorize publication or version changes. Read the relevant
sections of [the release checklist](../../../docs/release-checklist.md),
[distribution policy](../../../docs/architecture/distribution-and-development.md), and
`.github/workflows/release.yml`. Use the checklist's current source/release state, not
a release version copied from a historical example.

Complete local preparation before a required external approval. Existing explicit
authorization for the same action, version, and target remains valid; do not ask again.
Branch pushes, remote dry-runs, draft releases, and public body/PR updates are external
writes and must stay within that authorization. This skill grants no additional scope.

## Hard stops

- Do not publish, create a release tag, or trigger release workflow publishing without
  explicit user approval for that publish step, including approval already given.
- Do not use direct tag-push publishing. Never run `git push origin v<tag>` as the
  release trigger.
- Publish only through a GitHub Release `published` event.
- Keep `workflow_dispatch` as a dry-run path for deterministic quality and build jobs only.
- Do not add or run live E2E in GitHub Actions, CI/CD, or release workflows.
- Docker/GHCR is not a supported alpha release channel.
- If the PyPI version already exists, stop and ask for a new version decision. Package
  versions cannot be overwritten.
- If the release tag SHA does not match `origin/release/<tag>`, stop before treating the
  release as valid.

## Pre-release preflight

Confirm the branch, version, and local state before changing or publishing anything:

```bash
git status --short --branch
python - <<'PY'
from pathlib import Path
import tomllib

version = tomllib.loads(Path("pyproject.toml").read_text())["project"]["version"]
print(version)
print(f"release/v{version}")
print(f"v{version}")
PY
uv sync --locked --extra dev
uv run --extra dev ruff check .
uv run --extra dev python -m mypy src scripts
uv run --extra dev pytest -q
```

Before claiming readiness, confirm `README.md`, `docs/product/user-stories.md`, and
`docs/architecture/target-architecture.md` still match the code and release claims.

## Release branch and dry-run

Use the project version as the single source of truth:

- branch: `release/v<project.version>`
- tag: `v<project.version>`
- GitHub Release target: `release/v<project.version>`

Create the release branch from the intended release commit. For a release from updated
`main`, the command shape is below; if another worktree owns that branch, prepare a
release worktree without disturbing it:

```bash
git switch main
git pull --ff-only origin main
git switch -c release/v<project.version>
```

Run preflight on that branch before the authorized push:

```bash
python -m scripts.release.preflight --project-root . --version <project.version>
```

The helper checks command availability,
branch/version, remote tag and PyPI absence, and packaged browser readiness without
publishing. An auth or network error is not evidence that a tag or package is absent.
If `gh` is outside `PATH`, pass its known location with `--gh-binary` as described in
the checklist. A failed check stops publishing preparation until its cause is resolved.

After passing preflight, push within the accepted release scope:

```bash
git push -u origin release/v<project.version>
```

Run deterministic remote dry-runs on the release branch:

```bash
gh workflow run ci.yml --ref release/v<project.version>
gh workflow run release.yml --ref release/v<project.version>
```

For `release.yml` dry-run, `quality` and `build` should pass. Publish and install
verification jobs should be skipped because the event is not `release`.

If GitHub can open a non-empty release PR, open `release/v<project.version> -> main` and
wait for deterministic CI. If the release branch exactly matches `main` and GitHub cannot
open a no-diff PR, record release PR as N/A and keep the `ci.yml` plus `release.yml`
dry-run evidence.

## GitHub Release publish

Before creating a release, refresh the preflight result and inspect
`gh release view v<project.version>`. Distinguish an absent release from authentication,
network, or permissions errors. If the release exists, or the preflight reports
an existing remote tag, stop and inspect. Do not republish
or move tags to bypass the failure.

Create a draft prerelease targeting the release branch:

```bash
gh release create v<project.version> \
  --draft \
  --prerelease \
  --latest=false \
  --target release/v<project.version> \
  --title "v<project.version>" \
  --notes-file /tmp/aidd-v<project.version>-release-notes.md
```

Confirm the draft targets `release/v<project.version>`. Draft releases may not materialize
the tag until publication.

Publish only with explicit user approval, preserving approval already given:

```bash
gh release edit v<project.version> --draft=false --prerelease --latest=false
git fetch origin --tags
git rev-parse refs/tags/v<project.version>^{commit}
git rev-parse origin/release/v<project.version>
```

The release workflow validates that the GitHub Release tag matches `project.version`, that
the release branch is named `release/<tag>`, and that the tag commit matches the remote
release branch HEAD before PyPI publishing.

## Verification evidence

Watch the release workflow from the `release` event:

```bash
gh run list --workflow release.yml --event release --limit 5
gh run watch <run-id> --exit-status
```

Expected successful jobs:

- `quality` for supported Python versions
- `build`
- `publish-pypi`
- `verify-pypi-install`
- `verify-uv-tool-install`

Then independently verify package availability:

```bash
pipx_evidence_root="$(mktemp -d)"
export PIPX_HOME="${pipx_evidence_root}/home"
export PIPX_BIN_DIR="${pipx_evidence_root}/bin"
python -m pipx install --backend pip "ai-driven-dev-v2==<project.version>"
"${PIPX_BIN_DIR}/aidd" --version
"${PIPX_BIN_DIR}/aidd" doctor

uv_evidence_root="$(mktemp -d)"
export UV_TOOL_DIR="${uv_evidence_root}/tools"
export UV_TOOL_BIN_DIR="${uv_evidence_root}/bin"
uv tool install "ai-driven-dev-v2==<project.version>"
"${UV_TOOL_BIN_DIR}/aidd" --version
"${UV_TOOL_BIN_DIR}/aidd" doctor
```

If `python -m pipx` is not installed locally, use an isolated pipx runner through `uv tool`
and record that environment note with the evidence.

The acceptance checks must execute the binaries installed into `PIPX_BIN_DIR` and
`UV_TOOL_BIN_DIR`. Do not substitute `pipx run` or `uv tool run`, because those commands resolve
separate temporary environments and do not prove that the preceding install produced a usable
entry point.

Record accepted evidence in `docs/release-checklist.md`: release URL, workflow run URL,
tag/branch commit, PyPI URL, `pipx` evidence, and `uv tool` evidence.
Use the bounded read-only evidence collector with captured outputs and exit codes:

```bash
python -m scripts.release.evidence_collector release-evidence.json
```

The checklist documents payload fields. The helper validates supplied evidence; it
does not fetch missing evidence or prove a command ran. Inspect its result before
copying it into the accepted release record.

After the release workflow reaches a terminal state, reconcile the public GitHub Release body
with the observed outcome. Record `publish-pypi`, `verify-pypi-install`, and
`verify-uv-tool-install` separately as passed, failed, or skipped. If publication passed but
either install lane lacks passing evidence, classify the package as published-but-unverified.
Name a superseding release when one exists. Never leave draft or candidate-only status text on
a published release.

## Post-release follow-up

When post-release follow-up is part of the accepted task, after a successful prerelease:

1. switch back to updated `main`;
2. create a `codex/post-<version>-release-followup` branch;
3. bump `pyproject.toml` and `uv.lock` to the next `.dev0` version;
4. update `CHANGELOG.md`, `README.md`, and `docs/release-checklist.md` evidence while
   keeping README user/operator-facing;
5. run deterministic checks and `uv build`;
6. commit, push, and open a PR to `main`.

Post-release version wording guardrail:

- The next `.dev0` source version belongs in `pyproject.toml`, `uv.lock`, and
  maintainer/release-state docs such as `docs/release-checklist.md`,
  beta-readiness audits, or distribution policy docs.
- Do not publish, install, or advertise the next `.dev0` source version as the latest or
  current release.
- README install guidance resolves the latest published package from PyPI without
  hardcoding a release number. Keep exact accepted versions in release evidence and
  maintainer state; README may warn that `main` contains unreleased changes.
- Keep docs consistency tests aligned with this split so README cannot reintroduce `.dev0`
  as a public release version.

## Failure handling

- Existing PyPI version: stop and request a new version.
- Missing release branch: create or push `release/v<project.version>` before publishing.
- Tag/branch SHA mismatch: stop; do not publish or accept the evidence until fixed.
- PyPI propagation delay: rerun verification only after confirming the package exists.
- Trusted Publishing failure: record the workflow, environment, package, and claim details.
- Published release body still says draft/candidate: reconcile it with the terminal workflow
  result; do not alter or republish the tag.
- Any live E2E request: keep it local manual operator evidence and outside release gates.
- Bound retries to the accepted release verification window. Preserve failed attempts
  and stop on repeated unchanged infrastructure blockers instead of publishing another
  version or changing credentials automatically.

## Final report format

Report:

- release version and branch;
- GitHub Release URL;
- release workflow run URL and job statuses;
- PyPI URL;
- `pipx` verification result;
- `uv tool` verification result;
- post-release branch or PR;
- any blockers or follow-up risks.
