# Wave 36 Candidate Readiness — 2026-08-03 Post-T78

This is the sanitized `candidate-readiness-v1` record for the Codex-scoped,
provider-free `W36-E7-S4-T37` gate after the post-T78 browser completion. It
contains no credentials, credential digests, provider output, mutable target
content, temporary absolute paths, or user-authored snapshot content. No live
evaluator, Claude, large scenario, Qwen lane, or `AIDD-LIVE-013` process was
launched.

## Candidate identity

- Source commit: `ead6dab8d862d3f0b8fed47ef7f303b272485884`
- Source tree: `cfbc108e27b72027141debdc6c33c978cc6fabbd`
- Tracked-index SHA-256: `4b373d3ad79248c182aeb43a001248ef0be1a91ddc4f538544f7af662af5c530`
- Tracked-bytes SHA-256: `dd1880bd66fe793ecf894430b7c958dd25c37ab008802e167d734f9b3f15fa9c`
- Source archive size: `39925760` bytes
- Source archive SHA-256: `9d87bfdbe89e7a2669823e41b9d28244d6f4fdc44ea64c0280158d1e382426cc`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `905271` bytes
- Wheel SHA-256: `dc112481b7535638ac81e305f1277d3ccba7a4c65081893d4d98966b02f3543a`
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
| Full Python suite | pass, `2168/2168` in `650.21s` |
| Exact-SHA full Chromium suite | pass, `188/188` in `2082.58s` |
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
- Provider-private Codex auth status probe: pass before evaluator allocation
- Setup: `bun install`, exit `0`, 759 packages
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- `git diff --check`: pass
- Product checkout after setup: no tracked or untracked mutation; one expected
  ignored dependency-install root
- Classification: `pass`

The accepted smoke used the authored Vitest command and did not depend on future
QA artifacts. An earlier disposable setup root was rejected after the operator
invoked Bun's native test runner instead of the authored Vitest command; no
provider was allocated and that root was not reused. Denied attempts by the
macOS developer toolchain to write its host cache did not affect clone or
checkout.

## Bundle readiness

The installed candidate materialized and atomically sealed a synthetic
`AIDD-LIVE-007` bundle with bundle-relative references. Its source archive and
wheel digests matched the candidate above. Manifest and result-index validation
remained successful after disposable source, work, and target roots and the
original wheel copy were removed.

- Bundle tree SHA-256: `2d516483bc4ca84584be689c72e8ff055d21ef886a8628876438d0ba18c8c226`
- Manifest file count: `13`
- Canonical artifact count: `7`
- Reference mode: `bundle-relative`

## Codex isolation and private-auth readiness

A fresh Codex readiness session used the `macos-seatbelt` backend and the real
subprocess launch boundary. The minimal `.codex/auth.json` snapshot was seeded
into the private home and `codex login status` passed before target readiness.
Session evidence used schema v2, recorded process exit `0`, no integrity
violations, retained private auth, and successful active-session sentinel
cleanup.

A separate no-evaluator canary proved that own target and evidence roots allow
list, read, and write; the AIDD source allows list and read but denies write;
sibling provider root and operator HOME deny list, read, and write; and the
sibling credential marker is absent from the environment. The canary exited `0`
without residue. No credential value, source path, or digest was recorded.

## Source integrity and result

Postflight found the same commit, tree, tracked bytes, tracked file count (`905`),
and empty tracked status. The exact pre-existing excluded untracked inventory
remained `docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`; its bytes were not
read into this record or committed.

Overall result: `ready-for-codex`. External medium Codex acceptance must use the
source commit, tree, target pin, and exact wheel bytes recorded above. This
evidence-record commit is not a replacement candidate and must not cause the
wheel to be rebuilt.
