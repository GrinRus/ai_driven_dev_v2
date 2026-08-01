# Wave 36 Candidate Readiness — 2026-08-01 Post-T71

This is the sanitized `candidate-readiness-v1` record for the provider-free
`W36-E7-S4-T37` gate after the T71 macOS lifecycle-isolation correction. It
contains no credentials, credential digests, provider output, mutable target
content, temporary absolute paths, or user-authored snapshot content. No large
scenario, Qwen lane, `AIDD-LIVE-013`, or evaluator process was launched.

## Candidate identity

- Source commit: `9d0bf59dfc43613b1bb9f907e492ca08cb981cd7`
- Source tree: `8354d0a9a939d921d870397344eb4f1980c4cc11`
- Tracked-index SHA-256: `b89a31c62a3e9441e49271b2861fdf45c8c16d2cd5251060e9e5533642fb4991`
- Tracked-bytes SHA-256: `376e1bd312e5148e6443283a2070b8b96e844e137d8f83943d4d6af6a2821c8f`
- Source archive SHA-256: `f4ef417622806266841db719d53d8ecef91e3b063b3d3f1e57792beb223ef592`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `902608` bytes
- Wheel SHA-256: `0964977ddeb9534b849ce93381eb2d047b381a05eb8a3d4d53496247ca32ab10`
- Isolated Python: `3.13.7`
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
| Full Python suite | pass, `2149/2149` in `725.67s` |
| Exact-SHA full Chromium suite | pass, `188/188` in `2184.08s` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, Codex CLI `0.144.1`, native command ready |
| Claude Code `aidd eval doctor` | pass, Claude Code `2.1.85`, native command ready |

The exact-SHA Chromium suite completed in one uninterrupted run. No browser or
UI process remained after the gate.

## Target readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Fresh clone and checkout inside macOS Seatbelt: pass
- Setup: `bun install --frozen-lockfile`, exit `0`, 759 packages
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- Product checkout after setup: no tracked or untracked mutation; one expected
  ignored dependency-install root
- Classification: `pass`

The smoke used only authored commands that do not depend on future QA artifacts
and completed before any provider allocation. Denied attempts by the macOS
developer toolchain to write its host cache did not affect clone or checkout.

## Bundle readiness

The installed candidate materialized and atomically sealed a synthetic
`AIDD-LIVE-007` bundle with bundle-relative references. Its source archive and
wheel digests matched the candidate above. Manifest and result-index validation
remained successful after mutable source, work, and target roots were removed.

- Bundle tree SHA-256: `4e51855a0608f107fca243d390a9230dd75d268fc4c7b05eb30a54280721cc1d`
- Manifest file count: `21`
- Canonical artifact count: `12`
- Reference mode: `bundle-relative`

## Isolation and private-auth readiness

Independent Codex and Claude Code sessions used fresh sibling roots, the
`macos-seatbelt` backend, and the real subprocess launch boundary. Both public
preflights passed and reported `auth_scope=provider-private` with
`auth_state=pending-isolated-probe`.

For both runtime sessions:

- the minimal runtime auth file was seeded into the private home;
- the runtime-specific status probe passed before the `/usr/bin/true` sentinel;
- the own provider root allowed list, read, and write;
- the AIDD source allowed list and read but denied write;
- the sibling provider root and operator home denied list, read, and write;
- unrelated provider credential variables were absent;
- session schema v2 recorded a passing probe, retained private auth, child exit
  `0`, no integrity violations, and successful active-session sentinel cleanup.

Codex seeded only `.codex/auth.json`. Claude Code seeded only `.claude.json` and
received the explicitly selected `ANTHROPIC_AUTH_TOKEN` environment key for its
active host session. No credential value or digest was recorded, and the key was
not exposed to the Codex session.

## Source integrity and result

Postflight found the same commit, tree, tracked bytes, tracked file count (`894`),
and empty tracked status. The exact pre-existing excluded untracked inventory
remained:

- `docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`
- inventory SHA-256:
  `a63d56dc9bae70cffd465cc470d8eb2206117a628a070b27c58650340b20eec7`

Overall result: `ready`. External medium acceptance must use the source commit,
tree, target pin, and exact wheel bytes recorded above. This evidence-record
commit is not a replacement candidate and must not cause the wheel to be rebuilt.
