# Wave 36 Candidate Readiness — 2026-07-28 Post-T65

This is the sanitized `candidate-readiness-v1` record for the provider-free
`W36-E7-S4-T37` gate after the T65 terminal-cancellation correction. It contains
no credentials, credential digests, provider output, mutable target content,
temporary absolute paths, or user-authored snapshot content. No large scenario,
Qwen lane, `AIDD-LIVE-013`, or evaluator process was launched.

## Candidate identity

- Source commit: `1dbe87ac32d35582a4c0e316747fd62c6aa8208b`
- Source tree: `075e9fa211e457cdc18ab24a6425d7df9fd96069`
- Tracked-index SHA-256: `c11d3071e7cc14a32fc140d0ca6bfc602379da2e50a32a292d4c481711b32525`
- Tracked-bytes SHA-256: `f538275e3469d5c8c7a80208df9d717807328c0004e46eb6f5dad3025322884d`
- Source archive SHA-256: `0f7135dc3cc45db0d258562a7337c9d3c3260d0bd0c3bccf890d1f6e9139ddd8`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `902122` bytes
- Wheel SHA-256: `3b38a55846fa662d28cd9d11b8c63efbe3e98d8b0a4a5f659dd5ad1096511e56`
- Python: `3.13.7`
- uv: `0.8.22`
- Ruff: `0.15.22`
- mypy: `2.3.0`
- pytest: `9.1.1`
- Playwright: `1.61.0`
- Chromium: `149.0.7827.55`
- Bun: `1.3.5`

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
| Full Python suite | pass, `2146/2146` in `1159.03s` |
| Exact-SHA full Chromium suite | pass, `188/188` in `3346.83s` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, Codex CLI `0.144.1`, native command ready |
| Claude Code `aidd eval doctor` | pass, Claude Code `2.1.85`, native command ready |

## Target readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Fresh clone: pass
- Setup: `bun install`, exit `0`
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- Product checkout after setup: no tracked or untracked mutation; expected ignored
  dependency-install inventory only
- Classification: `pass`

The smoke used only authored commands that do not depend on future QA artifacts
and completed before any provider allocation. The process runner initially
rejected a not-yet-created target directory as `cwd`; no command executed in that
attempt, and the clone plus setup then ran from their correct existing roots.

## Bundle readiness

The installed candidate materialized and atomically sealed a synthetic
`AIDD-LIVE-007` bundle with bundle-relative references. Its source archive and
wheel digests matched the candidate above. Manifest and result-index validation
remained successful after the mutable target and work roots were removed.

- Bundle tree SHA-256: `70a727f2bb33077575f8057bcca2b0ceda1b5365d15e91732362f77ad90a4427`
- Manifest file count: `11`
- Canonical artifact count: `6`
- Reference mode: `bundle-relative`

## Isolation and private-auth readiness

Independent Codex and Claude Code sessions used fresh sibling roots, the
`macos-seatbelt` backend, and the real subprocess launch boundary. Both public
preflights passed and reported
`auth_scope=provider-private` with
`auth_state=pending-isolated-probe`.

For both runtime sessions:

- the minimal runtime auth file was seeded into the private home;
- the runtime-specific status probe passed before the sentinel command;
- the own provider root was readable and writable;
- the AIDD source was readable but not writable;
- the sibling provider root and operator home were denied by the isolation
  capability canary;
- unrelated provider credential variables were absent;
- session schema v2 recorded a passing probe, retained private auth, child exit
  `0`, no integrity violations, and successful active-session sentinel cleanup.

Codex seeded only `.codex/auth.json`. Claude Code seeded only `.claude.json` and
received the explicitly selected `ANTHROPIC_AUTH_TOKEN` environment key for its
active host session. No credential value or digest was recorded, and the key was
not exposed to the Codex session.

The child interpreter emitted a denied host-temp xcrun cache warning while still
exiting `0`; this is expected evidence that the original host temp root remained
outside the write allowlist, not an auth or execution failure.

## Source integrity and result

Postflight found the same commit, tree, tracked bytes, tracked file count (`888`),
and empty tracked status. The exact pre-existing excluded untracked inventory
remained:

- `docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`
- SHA-256: `72c8a71a50e8c689c3ee4c87d6df6c25ff7c77881c561eac99159583814644ed`

Overall result: `ready`. External medium acceptance must use the source commit,
tree, target pin, and exact wheel bytes recorded above. This evidence-record
commit is not a replacement candidate and must not cause the wheel to be rebuilt.
