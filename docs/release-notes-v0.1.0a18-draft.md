# Release Notes: v0.1.0a18

Status: published on 2026-08-10; accepted package-channel evidence.

Published package version: `0.1.0a18`.
GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a18`.
PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a18/`.
Release workflow: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/31415418286`.

## Summary

This alpha prerelease completes the intent-centered Operator UI cleanup. It makes Intent,
phase, decision, and document the primary surfaces while preserving the existing runtime,
workflow, API, and canonical work-item model.

## User-visible changes

- Replace the permanent stage rail, cockpit header, decision strip, sidebar, and bottom dock
  with a compact Intent workspace and one primary scroll owner.
- Use `Intent` consistently in user-facing copy while retaining `work_item` in API, route,
  lineage, and technical-detail contracts.
- Keep the current decision and primary action ahead of maintenance and diagnostics, with
  runtime settings shown only when an execution action needs them.
- Move canonical IDs, run/stage lineage, evidence, history, logs, and recovery details into
  contextual technical disclosures.
- Harden responsive geometry, focus order, touch targets, long-label wrapping, empty/error/
  loading states, and reduced-motion behavior across desktop and mobile.
- Add static and browser coverage for the final shell anchors, Intent vocabulary, technical
  disclosure, and the packaged UI journeys.

## Compatibility and limitations

- The core remains runtime-agnostic and document-first; canonical work-item IDs, routes,
  stage progression, API payloads, and artifact ownership are unchanged.
- Runtime binaries and authentication remain external operator prerequisites.
- Manual live evaluation remains outside GitHub Actions, CI/CD, and release workflows.
- AIDD remains alpha software for local evaluation and controlled operator trials; this release
  does not claim unattended production automation or beta readiness.
- Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.

## Publication checklist

- Release branch: `release/v0.1.0a18`.
- The GitHub Release `published` workflow passed quality, build, PyPI, `pipx`, and
  `uv tool` verification.
