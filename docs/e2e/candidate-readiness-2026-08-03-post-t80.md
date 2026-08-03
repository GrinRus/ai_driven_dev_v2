# Wave 36 Candidate Readiness — 2026-08-03 Post-T80

This is the sanitized `candidate-readiness-v1` record for the Codex-scoped,
provider-free `W36-E7-S4-T37` gate after the post-T80 browser completion. It contains no
credentials, credential digests, provider output, mutable target content, temporary absolute
paths, or user-authored snapshot content. No live evaluator, Claude, large scenario, Qwen lane,
or `AIDD-LIVE-013` process was launched.

## Candidate identity

- Source commit: `4880ea4dd2a2d3504602d78c316b4d60cf8b1c7c`
- Source tree: `3ec390437324f3eff4fc48fe200bb2bab7b282a7`
- Tracked-index SHA-256: `bb9c0a092de7949260ad6b2966db0f90a96810adbd4979a5365e0c05d3df408d`
- Tracked-bytes SHA-256: `0e91de256c8ad61c04641dfc7f1a2d7cf69cb1644bbb69001e87bae2da723f29`
- Tracked file count: `909`
- Source archive size: `39956480` bytes
- Source archive SHA-256: `cca520a0935f324e4dcd8a247f8d959ff7c41e84ebf61b530aa19fb97d41fdbe`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `905321` bytes
- Wheel SHA-256: `300bf168c85d59ada03cd35ea1c153aaf7e191d3680f42ff7231b71dfa5d5aff`
- Isolated Python: `3.13.7`
- uv: `0.8.22`
- Ruff: `0.15.22`
- mypy: `2.3.0`
- pytest: `9.1.1`
- Playwright: `1.61.0`
- Chromium: `149.0.7827.55`
- Bun: `1.3.5`
- Codex CLI: `0.144.1`

The source tar was created with `git archive` from the clean tracked commit. The wheel was built
only from the extracted archive, installed into a new virtual environment, and imported from
isolated `site-packages`, not from the checkout.

## Provider-free gates

| Gate | Result |
| --- | --- |
| Ruff | pass |
| mypy `src scripts` | pass, 228 source files |
| Full Python suite | pass, `2170/2170` in `699.73s` |
| Exact-SHA full Chromium suite | pass, `188/188` in `4737.30s` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, Codex CLI `0.144.1`, native command ready |

The exact-SHA Chromium suite completed in one uninterrupted run. No browser or UI process
remained after the gate. Claude readiness was intentionally not run under the current Codex-only
acceptance scope and is not claimed by this record.

## Target readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Isolation backend: `macos-seatbelt`
- Provider-private Codex auth status probe: pass before evaluator allocation
- Fresh clone and checkout inside the production isolation boundary: pass
- Setup: `bun install --frozen-lockfile`, exit `0`, 759 packages
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- `git diff --check`: pass
- Product checkout after setup: no tracked or untracked mutation; expected ignored dependency root only
- Classification: `pass`

## Bundle readiness

The installed candidate materialized and validated a synthetic `AIDD-LIVE-007` result bundle
with nine canonical artifacts and bundle-relative references. Validation remained successful
after the disposable mutable target root was removed.

## Codex isolation and source integrity

A fresh Codex readiness session used the real `macos-seatbelt` subprocess boundary. The minimal
`.codex/auth.json` snapshot was seeded into the private home and `codex login status` passed
before target readiness. Session evidence schema v2 recorded process exit `0`, no integrity
violations, retained private auth, and successful active-session sentinel cleanup.

Postflight found the same commit, tree, tracked bytes, tracked file count (`909`), and empty
tracked status. The exact pre-existing excluded untracked inventory remained
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`; its bytes were not included in this record or
committed.

Overall result: `ready-for-codex`. External medium Codex acceptance must use the source commit,
tree, target pin, and exact wheel bytes recorded above. This evidence-record commit is not a
replacement candidate and must not cause the wheel to be rebuilt.
