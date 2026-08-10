# Release Notes: v0.1.0a17

Status: published on 2026-08-04; accepted package-channel evidence.

Published package version: `0.1.0a17`.
GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a17`.
PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a17/`.
Release workflow: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/30897355532`.

## Summary

This alpha prerelease fixes the experimental Qwen Code native command so AIDD uses a valid
approval-mode value with the installed Qwen CLI.

## User-visible changes

- The Qwen native default now uses `qwen --approval-mode auto --output-format stream-json`.
- AIDD recognizes Qwen `--approval-mode auto` as a permission-bypass command when validating
  non-full-access runtime configurations.
- The example configuration, operator handbook, live-runtime configuration, and adapter tests
  use the same supported command.

## Compatibility and limitations

- The core remains runtime-agnostic and document-first; the change is isolated to Qwen
  runtime configuration and adapter coverage.
- Qwen remains experimental. Its CLI installation and authentication are external operator
  prerequisites.
- Manual live evaluation remains outside GitHub Actions, CI/CD, and release workflows.
- The release workflow verified quality, build, PyPI publication, `pipx`, and `uv tool`
  installation for the published package.

## Publication checklist

- Release branch: `release/v0.1.0a17`.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.
