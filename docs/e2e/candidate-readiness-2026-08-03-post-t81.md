# Wave 36 Candidate Readiness — 2026-08-03 Post-T81

This is the sanitized candidate-readiness record for the Codex-only `W36-E7-S4-T82`
refresh after T81. It contains no credential material or digest, provider output, mutable target
content, temporary absolute path, or user-authored snapshot content. No live evaluator, Claude,
Qwen, large scenario, human session, or `AIDD-LIVE-013` process was launched.

## Candidate identity

- Source commit: `09b8d6a79af293c6b7d9a0177c98e7fe528b5de2`
- Source tree: `8bba6dd582f3c84598cc262c289959757bf97562`
- Tracked-index SHA-256: `65cc05de38de14c39a74d04467b920de6aaa4474e813ed4345090f440d37983c`
- Tracked-bytes SHA-256: `45997ebd3dd38bcb5eec9dbf1f8bbe73a3bc0e502c1ad64e348509945647e9be`
- Tracked file count: `910`
- Source archive size: `39966720` bytes
- Source archive SHA-256: `9f10c8b3e2c5ade32670405345e4293c9dcece0a846d66cc181d38cbd94372b2`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `905369` bytes
- Wheel SHA-256: `6db06bc15518214c5801b4026703379cd40cdc0f93040a5741c52bac45f30bc3`
- Isolated Python: `3.13.7`
- uv: `0.8.22`
- Ruff: `0.15.22`
- mypy: `2.3.0`
- pytest: `9.1.1`
- Playwright: `1.61.0`
- Chromium: `149.0.7827.55`
- Bun: `1.3.5`
- Codex CLI: `0.144.1`

The source tar was created with `git archive` from the immutable tracked commit. The wheel was
built only from the extracted archive, installed into a new virtual environment, and imported
from isolated `site-packages`, not the checkout. This evidence-record commit is not a replacement
candidate and must not cause the wheel to be rebuilt.

## Provider-free gates

| Gate | Result |
| --- | --- |
| T81 Ruff | pass |
| T81 mypy `src scripts` | pass, 228 source files |
| T81 full Python suite | pass, `2170/2170` |
| Exact-SHA full Chromium suite | pass, `188/188` in `4683.94s` |
| Bundle, manifest, and isolation regression | pass, `29/29` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, native command ready |

The exact-SHA Chromium suite completed in one uninterrupted run. No browser, UI, or fixture
process remained after the gate. Claude readiness was intentionally excluded by the current
Codex-only prerelease scope.

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
- Product checkout after setup: clean tracked state

## Bundle, isolation, and integrity

Focused materialization, manifest, readback, and isolation regressions pass `29/29`. A fresh
Codex readiness session used the real `macos-seatbelt` boundary. Only `.codex/auth.json` was
seeded into the private provider home; `codex login status` passed, the command exited `0`, the
active-session sentinel was removed, and session evidence reported no integrity violation.

Postflight retained the same source commit, tree, tracked bytes, tracked file count (`910`), and
empty tracked status. The only pre-existing excluded untracked path remained
`docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`; its bytes were neither read into this record
nor committed.

Overall result: `ready-for-codex`. The next T3 run must use the exact source identity, target pin,
and wheel bytes recorded above in a completely fresh provider root.
