# Release Notes: v0.1.0a16

Status: published on 2026-08-04.

Published package version: `0.1.0a16`.
GitHub Release: `https://github.com/GrinRus/ai_driven_dev_v2/releases/tag/v0.1.0a16`.
PyPI: `https://pypi.org/project/ai-driven-dev-v2/0.1.0a16/`.
Release workflow: `https://github.com/GrinRus/ai_driven_dev_v2/actions/runs/30878924948`.
Release workflow quality, build, publish, `pipx`, and `uv tool` verification jobs passed.

## Summary

This alpha prerelease hardens AIDD's installed live-acceptance path and records a fresh
counted-clean Codex medium run. It improves provider isolation, containment, lifecycle truth,
evidence portability, operator checkpoints, and document validation while preserving the
runtime-agnostic core and document-first workflow.

## User-visible changes

- Live provider runs use private HOME/XDG/temp/cache state, allowlisted environments, isolated
  authentication probes, and operating-system filesystem boundaries.
- Resume, evidence intake, source/target integrity, provider-root separation, terminal
  reconciliation, and cleanup now fail closed on identity or containment violations.
- Live results can be materialized into self-contained bundles with relative links, source/wheel
  provenance, per-file digests, browser identities, and an atomic tree manifest.
- Product summaries distinguish execution pass, manual quality review, counted-clean status,
  manual quality stops, and degraded legacy evidence.
- Logs, ignored inventories, lifecycle events, and command output references are bounded to keep
  evidence growth predictable without discarding canonical raw artifacts.
- Plan, Implement, Review, and QA validation accepts truthful bounded command/evidence forms and
  rejects ambiguous dependency direction or fabricated traceability.

## Acceptance evidence

- Exact provider-free candidate: `ae3131a440d9b040a532db89f176bd4cb3a1d2cf`.
- Candidate wheel SHA-256: `2b3e48137bb6663b30457d9d9d03c9deae6982571d1b5981c4cf758bf420ce2c`.
- Deterministic gates: Ruff, mypy, Python `2179/2179`, maintained Chromium `188/188`, isolated
  install/doctor, target readiness, private Codex auth/isolation, bundle deletion/readback, and
  source integrity.
- Fresh Codex run: `eval-live-007-codex-20260803T205243Z` on `AIDD-LIVE-007`, completing all
  eight stages with manual stage-quality audits, Hono Vitest `236/236`, `tsc --noEmit`, terminal
  Chromium inspection, and `counted_clean=true`.
- Sealed live bundle tree SHA-256:
  `a12758077ead069d694b915700b62d196950223f5f3ee5341410cdc72ad734bb`.

## Compatibility

- The core remains runtime-agnostic and document-first.
- Provider-specific behavior remains in adapters and live harness boundaries.
- Runtime binaries and authentication remain external operator prerequisites.
- Manual live acceptance remains outside GitHub Actions, CI/CD, and release workflows.

## Installation channels

Supported alpha channels remain PyPI through `pipx`, `uv tool`, and source checkout.
Docker/GHCR is not part of the supported alpha release contract.

## Known limitations

- This is an alpha prerelease with Codex-only live acceptance.
- Claude Code, Qwen, large/xlarge scenarios, five first-time-operator sessions, and final
  dual-provider acceptance remain separate beta-readiness gates and are not claimed here.
- The release is accepted package-channel evidence after the published GitHub Release
  workflow verified PyPI, `pipx`, and `uv tool` installation.

## Release checklist

- GitHub Release target: `release/v0.1.0a16`.
- Release branch: `release/v0.1.0a16`.
- Release workflow: GitHub Release `published` event only; manual dispatch is dry-run only.
- Direct tag push is forbidden.
- Publication was completed after explicit maintainer approval.
