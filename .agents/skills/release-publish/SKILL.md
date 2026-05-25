---
name: release-publish
description: Prepare, publish, verify, and record AIDD Python package releases through this repository's release/v<version> branch and GitHub Release published-event flow; use when cutting a new prerelease or release, running release dry-runs, checking PyPI/pipx/uv tool evidence, or performing post-release version-bump follow-up.
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

## Read first

1. `AGENTS.md`
2. `README.md`
3. `docs/product/user-stories.md`
4. `docs/architecture/target-architecture.md`
5. `docs/architecture/distribution-and-development.md`
6. `docs/release-checklist.md`
7. `.github/workflows/release.yml`

## Hard stops

- Do not publish, create a release tag, or trigger release workflow publishing without
  explicit user approval for that publish step.
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
git status --short --branch --untracked-files=no
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
uv run --extra dev python -m mypy src
uv run --extra dev pytest -q
```

Before claiming readiness, confirm `README.md`, `docs/product/user-stories.md`, and
`docs/architecture/target-architecture.md` still match the code and release claims.

## Release branch and dry-run

Use the project version as the single source of truth:

- branch: `release/v<project.version>`
- tag: `v<project.version>`
- GitHub Release target: `release/v<project.version>`

Create and push the release branch from the intended release commit:

```bash
git switch main
git pull --ff-only origin main
git switch -c release/v<project.version>
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

Before creating a release, verify the release and tag do not already exist:

```bash
if gh release view v<project.version> >/dev/null 2>&1; then
  echo "GitHub Release v<project.version> already exists" >&2
  exit 1
fi

if git ls-remote --exit-code --tags origin refs/tags/v<project.version> >/dev/null 2>&1; then
  echo "Tag v<project.version> already exists on origin" >&2
  exit 1
fi
```

If either exists unexpectedly, stop and inspect. Do not republish or move tags casually.

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

Publish only after explicit user approval:

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
python -m pipx run --spec "ai-driven-dev-v2==<project.version>" aidd --version
python -m pipx run --spec "ai-driven-dev-v2==<project.version>" aidd doctor
uv tool run --from "ai-driven-dev-v2==<project.version>" aidd --version
uv tool run --from "ai-driven-dev-v2==<project.version>" aidd doctor
```

If `python -m pipx` is not installed locally, use an isolated pipx runner through `uv tool`
and record that environment note with the evidence.

Record accepted evidence in `docs/release-checklist.md`: release URL, workflow run URL,
tag/branch commit, PyPI URL, `pipx` evidence, and `uv tool` evidence.

## Post-release follow-up

After a successful prerelease:

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
- README install, status, and source-checkout positioning must name the latest accepted
  published prerelease and may warn that `main` is development source with unreleased
  changes.
- Keep docs consistency tests aligned with this split so README cannot reintroduce `.dev0`
  as a public release version.

## Failure handling

- Existing PyPI version: stop and request a new version.
- Missing release branch: create or push `release/v<project.version>` before publishing.
- Tag/branch SHA mismatch: stop; do not publish or accept the evidence until fixed.
- PyPI propagation delay: rerun verification only after confirming the package exists.
- Trusted Publishing failure: record the workflow, environment, package, and claim details.
- Any live E2E request: keep it local manual operator evidence and outside release gates.

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
