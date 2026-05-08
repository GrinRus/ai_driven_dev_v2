# Support

## Scope

AIDD is in alpha. Maintainer support focuses on reproducible issues in the latest published
prerelease and `main`.

Supported alpha installation paths:

- PyPI package through `pipx`;
- PyPI package through `uv tool`;
- source checkout with `uv sync --locked --extra dev`.

Docker/GHCR images are not supported during the alpha phase.

## Before opening an issue

Run:

```bash
aidd --version
aidd doctor
```

Include:

- AIDD version and installation path;
- operating system and Python version;
- runtime id;
- whether the failure happened in CLI, UI, harness, eval, or release workflow;
- redacted excerpts from `.aidd/` artifacts when they are needed to diagnose the issue.

Do not include secrets, private repository contents, provider tokens, or unredacted raw
runtime logs in public issues.

## Useful docs

- `README.md`
- `docs/operator-handbook.md`
- `docs/operator-troubleshooting.md`
- `docs/operator-support-policy.md`
- `docs/compatibility-policy.md`
