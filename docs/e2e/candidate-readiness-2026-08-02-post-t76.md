# Wave 36 Candidate Readiness — 2026-08-02 Post-T76

This is the sanitized `candidate-readiness-v1` record for the Codex-scoped,
provider-free `W36-E7-S4-T37` gate after explicit verification-only task support.
It contains no credentials, credential digests, provider output, mutable target
content, temporary absolute paths, or user-authored snapshot content. No live
evaluator, Claude, large scenario, Qwen lane, or `AIDD-LIVE-013` process was
launched.

## Candidate identity

- Source commit: `c26820c70b133b849d409317693e06c951839b49`
- Source tree: `a46ed39ab20fe87fdd89133a135f66ae46b2bcb1`
- Tracked-index SHA-256: `e2acd4f4c879850501498617363c3d81d5a55466571873ab1f474a906a5bfac0`
- Tracked-bytes SHA-256: `f11101fc3cf3aedffcd166a3394c9a2ddb5304406b4c873accad086209af28fd`
- Source archive size: `39895040` bytes
- Source archive SHA-256: `45f61747b844378c0307754d5f698f0c5441f6574d2d1ac81132f64a74a2b399`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `904868` bytes
- Wheel SHA-256: `469df0b0cd487f105ad66709b36c737d09f31c89d7e80a4c0fd9b8c0b4c8af41`
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
| Full Python suite | pass, `2165/2165` in `673.87s` |
| Exact-SHA full Chromium suite | pass, `188/188` in `2070.66s` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, Codex CLI `0.144.1`, native command ready |

The exact-SHA Chromium suite completed in one uninterrupted run. No browser or
UI process remained after the gate. Claude readiness was intentionally not run
under the current Codex-only acceptance scope and is not claimed by this record.

## Target readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Public preflight: pass, `macos-seatbelt`, provider-private auth pending probe
- Fresh clone and checkout inside macOS Seatbelt: pass
- Setup: `bun install`, exit `0`, 759 packages
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- `git diff --check`: pass
- Product checkout after setup: no tracked or untracked mutation; one expected
  ignored dependency-install root
- Classification: `pass`

The smoke used only authored commands that do not depend on future QA artifacts
and completed before any evaluator allocation. Denied attempts by the macOS
developer toolchain to write its host cache did not affect clone or checkout.

## Bundle readiness

The installed candidate materialized and atomically sealed a synthetic
`AIDD-LIVE-007` bundle with bundle-relative references. Its source archive and
wheel digests matched the candidate above. Manifest and result-index validation
remained successful after mutable source, work, and target roots and the original
wheel were removed.

- Bundle tree SHA-256: `1a4aeee2b604cf4822ac4d333e2847b7228a0e1befcdb0eb41c950b5e1303dd2`
- Manifest file count: `17`
- Canonical artifact count: `10`
- Reference mode: `bundle-relative`

## Codex isolation and private-auth readiness

Fresh Codex sessions used the `macos-seatbelt` backend and the real subprocess
launch boundary. The minimal `.codex/auth.json` snapshot was seeded into the
private home and `codex login status` passed before target readiness and before
a standalone no-evaluator visibility canary.

The canary proved that own target and evidence roots allow list, read, and write;
the AIDD source allows list and read but denies write; sibling provider root and
operator HOME deny list, read, and write; and the sibling credential marker is
absent from the environment. Session schema v2 records probe pass, process exit
`0`, no integrity violations, retained private auth, and successful active-session
sentinel cleanup. No credential value, source path, or digest was recorded.

## Source integrity and result

Postflight found the same commit, tree, tracked bytes, tracked file count (`903`),
and empty tracked status. The exact pre-existing excluded untracked inventory
remained `docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`; its bytes were not
read into this record or committed.

Overall result: `ready-for-codex`. External medium Codex acceptance must use the
source commit, tree, target pin, and exact wheel bytes recorded above. This
evidence-record commit is not a replacement candidate and must not cause the
wheel to be rebuilt.
