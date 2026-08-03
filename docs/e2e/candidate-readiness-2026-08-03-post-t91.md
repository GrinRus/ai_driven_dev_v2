# Wave 36 Candidate Readiness — 2026-08-03 Post-T91

This is the sanitized Codex-only `W36-E7-S4-T92` replacement-candidate record after the bounded
tasklist/plan dependency-direction fix. It contains no credential material or digest, provider
payload, mutable target content, temporary absolute path, or user-authored snapshot content. No
live evaluator, Claude, Qwen, large scenario, human session, or `AIDD-LIVE-013` process was
launched.

## Candidate identity

- Source commit: `ae3131a440d9b040a532db89f176bd4cb3a1d2cf`
- Source tree: `696633d03596245ad8daf7b9660fc7e177026775`
- Tracked-index SHA-256: `caf54c89217f0fa3a9a0f0393263bde4f3dbb5f5df04f57a08256d7113a2bdd0`
- Tracked-bytes SHA-256: `959f0adb8f48613d657d3523cf0e2b884bd655309357864b76282f0301869b29`
- Tracked file count: `915`
- Source archive size: `40017920` bytes
- Source archive SHA-256: `aecf4e45d6698791497b2decb882e81e4b3a3e4c47af7bfbf512434ef5a1bb01`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `906585` bytes
- Wheel SHA-256: `2b3e48137bb6663b30457d9d9d03c9deae6982571d1b5981c4cf758bf420ce2c`
- Isolated Python: `3.13.7`
- Codex CLI: `0.144.1`

The wheel was built only from an extracted `git archive` of the immutable source commit. A second
independent build from the same archive produced byte-identical wheel output. The wheel was
installed into a new virtual environment and imported from isolated `site-packages`.

## Provider-free gates

| Gate | Result |
| --- | --- |
| Ruff | pass |
| mypy `src scripts` | pass, 228 source files |
| Full Python suite | pass, `2179/2179` |
| Focused validator/planning group | pass, `55/55` |
| Exact terminal plan dependency extraction | pass, authored acyclic graph only |
| Isolated wheel import and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, native command ready |

The post-T81 exact-SHA Chromium evidence remains the browser gate: `188/188` passed in one
uninterrupted five-viewport run. T91 changes only runtime-agnostic cross-document dependency
parsing, its focused regression, and planning records; UI, Studio, browser, harness execution,
adapters, prompts, and frontend assets are unchanged.

## Target, auth, and integrity readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Isolation backend: `macos-seatbelt`
- Provider-private Codex auth status probe: pass before child execution
- Evaluator sentinel inside the private provider root: pass
- Fresh Hono clone and pinned checkout: pass
- `bun install --frozen-lockfile`: pass, 759 packages
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- `git diff --check`: pass
- Exact source clone commit/tree and clean tracked postflight: pass

The unchanged bundle, manifest, session, isolation, auth, and source-integrity implementation is
also covered by the complete `2179/2179` repository suite. The operator checkout's untracked
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md` was not read into this record or committed.

Overall result: `ready-for-codex`. The next T3 run must use the exact source identity, target pin,
and wheel bytes above in a completely fresh provider root. This evidence-record commit is not a
replacement candidate and must not cause the wheel to be rebuilt.
