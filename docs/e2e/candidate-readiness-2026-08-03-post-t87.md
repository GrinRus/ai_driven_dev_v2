# Wave 36 Candidate Readiness — 2026-08-03 Post-T87

This is the sanitized Codex-only `W36-E7-S4-T88` candidate record after the shell command-list
evidence fix. It contains no credential material or digest, provider payload, mutable target
content, temporary absolute path, or user-authored snapshot content. No live evaluator, Claude,
Qwen, large scenario, human session, or `AIDD-LIVE-013` process was launched.

## Candidate identity

- Source commit: `77260233f8ac46f80bf4c46bccc77f82aeee6983`
- Source tree: `1f89bd22b439cda0eaf88623d5aba0668ef6d5a4`
- Tracked-index SHA-256: `63b1d895637586b9492ba5e708b989335dfbd7bad7995c470d4355cf81f836c5`
- Tracked-bytes SHA-256: `462bc9f49b7e207031cdb80b3a7b6a29e64113b65ae2461b876dab9fb76cc06a`
- Tracked file count: `913`
- Source archive size: `39997440` bytes
- Source archive SHA-256: `9a9cf263529d8142f1ccb78f05812964b901faee9353a5c91cb3dc080f33aab6`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `906191` bytes
- Wheel SHA-256: `29b43f79fa92a3b619491ec0e01610363278fc163b074323b28ca98f7eaa0db9`
- Isolated Python: `3.13.7`
- Codex CLI: `0.144.1`

The wheel was built only from an extracted `git archive` of the immutable source commit,
installed into a new virtual environment, and imported from isolated `site-packages`.

## Provider-free gates

| Gate | Result |
| --- | --- |
| Ruff | pass |
| mypy `src scripts` | pass, 228 source files |
| Full exact-candidate Python suite | pass, `2175/2175` in `795.22s` |
| Validator/prompt/packaging/planning group | pass, `382/382` |
| Saved terminal Implement regression | pass, zero semantic findings |
| Bundle, manifest, and isolation regression | pass, `29/29` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, native command ready |

The post-T81 exact-SHA Chromium evidence remains the browser gate: `188/188` passed in one
uninterrupted five-viewport run. T87 changes only the runtime-agnostic Markdown evidence
classifier, its contract/prompt, focused tests, and scenario audit rubric; UI, Studio, browser,
harness execution, and frontend assets are unchanged.

## Target, auth, and integrity readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Isolation backend: `macos-seatbelt`
- Provider-private Codex auth status probe: pass before evaluator allocation
- Fresh clone and checkout inside the production boundary: pass
- `bun install --frozen-lockfile`: pass, 759 packages
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- `git diff --check`: pass
- Session process exit: `0`; integrity violations: none; sentinel cleanup: pass
- Source postflight exactly matches commit, tree, tracked bytes, and tracked count

The operator checkout's untracked `docs/analysis/ux-live-e2e-snapshot-2026-07-07.md` was not read
into this record or committed.

Overall result: `ready-for-codex`. The next T3 run must use the exact source identity, target pin,
and wheel bytes above in a completely fresh provider root. This evidence-record commit is not a
replacement candidate and must not cause the wheel to be rebuilt.
