# Wave 36 Candidate Readiness — 2026-08-03 Post-T89

This is the sanitized Codex-only `W36-E7-S4-T90` replacement-candidate record after the bounded
QA-local command-evidence fix. It contains no credential material or digest, provider payload,
mutable target content, temporary absolute path, or user-authored snapshot content. No live
evaluator, Claude, Qwen, large scenario, human session, or `AIDD-LIVE-013` process was launched.

## Candidate identity

- Source commit: `5a536143db36f0451db96e2b984b0f9f690cc767`
- Source tree: `b1877a8fd207cfb1271054a3b6181b744fdc1d4d`
- Tracked-index SHA-256: `1cb765780f70b0e6af4662cb9ed085df8f9c12bf6c30f7c5ddb257a1fb0bfd4f`
- Tracked-bytes SHA-256: `3cf659d00f645365ef0d2556274037bfb1a90449a5ec28770c57d4aace51c8c8`
- Tracked file count: `914`
- Source archive size: `40007680` bytes
- Source archive SHA-256: `143e40637745aa5a9e2400c6b854d4e02bef4ce022e83ce2fd81bdd2c3b4cfbc`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `906516` bytes
- Wheel SHA-256: `e057790e9a7943e8ca27dc6e98315872fcf7e2b975827e1937bc41196e80b3dc`
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
| Full Python suite | pass, `2178/2178` |
| Validator/prompt/scenario/planning group | pass, `432/432` |
| Exact terminal QA regression | pass, zero cross-document findings |
| Bundle, manifest, session, isolation, and auth regression | pass, `52/52` |
| Isolated wheel import and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, native command ready |

The post-T81 exact-SHA Chromium evidence remains the browser gate: `188/188` passed in one
uninterrupted five-viewport run. T89 changes only the runtime-agnostic Markdown QA evidence
validator, its contract and prompts, focused tests, scenario audit rubric, and planning records;
UI, Studio, browser, harness execution, adapters, and frontend assets are unchanged.

## Target, auth, and integrity readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Isolation backend: `macos-seatbelt`
- Provider-private Codex auth status probe: pass before child execution
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
