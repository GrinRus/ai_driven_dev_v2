# Wave 36 Candidate Readiness — 2026-08-03 Post-T83

This is the sanitized Codex-only `W36-E7-S4-T84` candidate record after the QA evidence
traceability fix. It contains no credential material or digest, provider payload, mutable target
content, temporary absolute path, or user-authored snapshot content. No live evaluator, Claude,
Qwen, large scenario, human session, or `AIDD-LIVE-013` process was launched.

## Candidate identity

- Source commit: `912f444bd67d4d30932b1d0c770497b1df5e6737`
- Source tree: `5fb8486f08be079248e74523a3e2517702dd6e74`
- Tracked-index SHA-256: `5741457658795a085b937ac655c45c77ec980d3d731bb75a916dda1f47394f2e`
- Tracked-bytes SHA-256: `36ff0e53b734dedb77dd64ce1f1ffc994c8495049ddee71398c98a641801f52f`
- Tracked file count: `911`
- Source archive size: `39976960` bytes
- Source archive SHA-256: `3260f35b260afc8f4022ffe1f65f18b80d23fc8b148faf0daa5e11a259b6bfff`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `905674` bytes
- Wheel SHA-256: `4e1fe072485ac9dbee61e931b770f5a6183bc94fb05fa03fe60178bcec6f93bd`
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
| Full Python suite | pass, `2172/2172` in `1056.42s` |
| Validator suite | pass, `296/296` |
| Saved terminal QA regression | pass, zero cross-document findings |
| Bundle, manifest, and isolation regression | pass, `29/29` |
| Planning integrity | pass, `9/9` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, native command ready |

The post-T81 exact-SHA Chromium evidence remains the browser gate for this candidate: `188/188`
passed in one uninterrupted five-viewport run. T83 changed only runtime-agnostic Markdown
cross-document validation and its unit tests; UI, Studio, browser, harness, core, adapters,
prompts, contracts, and scenario code did not change. No browser result is claimed for changed
code, and the release record keeps this reuse explicit.

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
