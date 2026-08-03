# Wave 36 Candidate Readiness — 2026-08-03 Post-T85

This is the sanitized Codex-only `W36-E7-S4-T86` candidate record after the Implement shell
compound evidence fix. It contains no credential material or digest, provider payload, mutable
target content, temporary absolute path, or user-authored snapshot content. No live evaluator,
Claude, Qwen, large scenario, human session, or `AIDD-LIVE-013` process was launched.

## Candidate identity

- Source commit: `4b2856f19f2a80eb4eebb78512114e8a00fd5161`
- Source tree: `9137bc3c79c513c16755a33f8043149e71b206da`
- Tracked-index SHA-256: `b7bf703de3a101bf681cd16fca115708bf75e6103daadf53236d6510fb906c84`
- Tracked-bytes SHA-256: `c1ea32d54897e431b656e70c23011c9c727f5c74c91909481779bba8d7927660`
- Tracked file count: `912`
- Source archive size: `39987200` bytes
- Source archive SHA-256: `c8769e766ade36769ea58fa26211338bc20e0d485928c16540e02c03a3081b37`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `905951` bytes
- Wheel SHA-256: `f9e9f98c20a1210433cca01648402f68716a4c4acabadcb8e706622832826b12`
- Isolated Python: `3.13.7`
- Codex CLI: `0.144.1`

The source tar was created with `git archive` from the immutable tracked commit. The wheel was
built only from that extracted archive, installed into a new virtual environment, and imported
from isolated `site-packages`.

## Provider-free gates

| Gate | Result |
| --- | --- |
| Ruff | pass |
| mypy `src scripts` | pass, 228 source files |
| Full exact-candidate Python suite | pass, `2174/2174` in `1213.82s` |
| Validator suite | pass, `298/298` |
| Saved terminal Implement regression | pass, zero semantic findings |
| Bundle, manifest, and isolation regression | pass, `29/29` |
| Planning integrity | pass, `9/9` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, native command ready |

The post-T81 exact-SHA Chromium evidence remains the browser gate for this candidate: `188/188`
passed in one uninterrupted five-viewport run. T85 changes the runtime-agnostic Markdown evidence
classifier, its Implement contract/prompt, focused tests, and the scenario audit rubric. UI,
Studio, browser, harness execution, and frontend assets are unchanged, so no browser behavior is
claimed for changed code and the reuse remains explicit.

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

The only pre-existing untracked path in the operator checkout remained
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`; it was not read into this record or committed.

Overall result: `ready-for-codex`. The next T3 run must use the exact source identity, target pin,
and wheel bytes above in a completely fresh provider root. This evidence-record commit is not a
replacement candidate and must not cause the wheel to be rebuilt.
