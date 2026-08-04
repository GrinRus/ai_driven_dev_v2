# Release Notes: v0.1.0a17

Status: prepared candidate; not yet published.

Candidate package version: `0.1.0a17`.
GitHub Release target: `release/v0.1.0a17`.

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

## Publication checklist

- Create a draft GitHub prerelease targeting `release/v0.1.0a17`.
- Publish only after explicit maintainer approval.
- The GitHub Release `published` workflow must pass quality, build, PyPI, `pipx`, and
  `uv tool` verification before this candidate is described as accepted.
