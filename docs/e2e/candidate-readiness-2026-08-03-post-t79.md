# Wave 36 Candidate Readiness — 2026-08-03 Post-T79

This is the sanitized `candidate-readiness-v1` record for the Codex-scoped,
provider-free `W36-E7-S4-T37` gate after the post-T79 browser completion. It
contains no credentials, credential digests, provider output, mutable target
content, temporary absolute paths, or user-authored snapshot content. No live
evaluator, Claude, large scenario, Qwen lane, or `AIDD-LIVE-013` process was
launched.

## Candidate identity

- Source commit: `abbc4d62dd3d4aa5da0859b9e7fba8b7a9c451af`
- Source tree: `bc10c57732d439891355c73d15e8d80dd5cd88a7`
- Tracked-index SHA-256: `42b9dcaa19eac13ceabb6dbabeb73764532cfa2a5da74156ce7fd149027faf62`
- Tracked-bytes SHA-256: `990c325e2e0c2b5a7a535f1cbe04a86318ee40eecfc52525c1e9366bd100dc49`
- Tracked file count: `907`
- Source archive size: `39936000` bytes
- Source archive SHA-256: `93a46bca6383104c96c26f7f14ce6cbcf94d04a2a712dfb5ababc087a3494c60`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `905297` bytes
- Wheel SHA-256: `78f4d1150e83db236d73a0a19e55cf33d784f2eb77a30b838a8c563bb324112d`
- Isolated Python: `3.13.7`
- uv: `0.8.22`
- Ruff: `0.15.22`
- mypy: `2.3.0`
- pytest: `9.1.1`
- Playwright: `1.61.0`
- Chromium: `149.0.7827.55`
- Bun: `1.3.5`
- Codex CLI: `0.144.1`

The source tar was created with `git archive` from the clean tracked commit. The
wheel was built only from the extracted archive, installed into a new virtual
environment, and imported from isolated `site-packages`, not from the checkout.
The archive and wheel copied into the sealed bundle are byte-identical to these
recorded inputs.

## Provider-free gates

| Gate | Result |
| --- | --- |
| Ruff | pass |
| mypy `src scripts` | pass, 228 source files |
| Full Python suite | pass, `2168/2168` in `680.33s` |
| Exact-SHA full Chromium suite | pass, `188/188` in `2006.84s` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, Codex CLI `0.144.1`, native command ready |

The exact-SHA Chromium suite completed in one uninterrupted run. No browser or
UI process remained after the gate. Claude readiness was intentionally not run
under the current Codex-only acceptance scope and is not claimed by this record.

## Target readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Session preflight: pass, `macos-seatbelt`, provider-private auth probe required
- Fresh clone and checkout inside macOS Seatbelt: pass
- Provider-private Codex auth status probe: pass before evaluator allocation
- Setup: `bun install`, exit `0`, 759 packages
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- `git diff --check`: pass
- Product checkout after setup: no tracked or untracked mutation; one expected
  ignored dependency-install root
- Classification: `pass`

The accepted smoke used the authored Vitest command and did not depend on future
QA artifacts. Denied attempts by the macOS developer toolchain to write its host
cache did not affect clone, checkout, setup, or verification.

## Bundle readiness

The installed candidate materialized and atomically sealed a synthetic
`AIDD-LIVE-007` bundle with bundle-relative references. Its source archive and
wheel digests matched the candidate above. Manifest and result-index validation
remained successful after the disposable mutable target root and input wheel copy
were removed.

- Bundle tree SHA-256: `0c6f5d2d60c53dea27d2b85e0149c264f52b1b90b45a63e73173b82bd05a118b`
- Manifest file count: `14`
- Canonical artifact count: `8`
- Reference mode: `bundle-relative`

## Codex isolation and private-auth readiness

A fresh Codex readiness session used the `macos-seatbelt` backend and the real
subprocess launch boundary. The minimal `.codex/auth.json` snapshot was seeded
into the private home and `codex login status` passed before target readiness.
Session evidence used schema v2, recorded process exit `0`, no integrity
violations, retained private auth, and successful active-session sentinel cleanup.

A separate no-evaluator capability canary passed for the same macOS backend,
including own-provider write access, read-only source access, sibling-provider
denial, and credential-environment denial. No credential value, source path, or
digest was recorded.

## Source integrity and result

Postflight found the same commit, tree, tracked bytes, tracked-index digest,
tracked file count (`907`), and empty tracked status. The exact pre-existing
excluded untracked inventory remained
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`; its bytes were not read into
this record or committed. The browser/UI process postflight was empty.

Overall result: `ready-for-codex`. External medium Codex acceptance must use the
source commit, tree, target pin, and exact wheel bytes recorded above. This
evidence-record commit is not a replacement candidate and must not cause the
wheel to be rebuilt.
