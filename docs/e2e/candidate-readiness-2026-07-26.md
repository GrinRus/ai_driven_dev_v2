# Wave 36 Candidate Readiness — 2026-07-26

This is the sanitized `candidate-readiness-v1` record for the provider-free
`W36-E7-S4-T37` gate. It contains no credentials, provider output, mutable target
content, temporary absolute paths, or user-authored snapshot content.

## Candidate identity

- Source commit: `43d740c26e016b0ccce27346ee3ec29bb4f9bfb7`
- Source tree: `a780ce96c952e672c8d8b6cdc5fcbbbfcf458b00`
- Tracked-index SHA-256: `88c5d180ca9d14beac1578af68f3615378ac3ecd852fad18b04cdab6441703f2`
- Source archive SHA-256: `b416b445ff785c213142dc2b7792fd5cf5114b97a12fef3518a57c55044e069c`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `895946` bytes
- Wheel SHA-256: `b93257d37072bc81cbb5aa181ce9c9f5ebc5a5aa14f09d3ad6158425b8101a5d`
- Python: `3.13.7`
- Chromium: `149.0.7827.55`

The source tar was created with `git archive` from the clean tracked commit. The
wheel was built only from the extracted archive and imported from an isolated
`site-packages`, not from the source checkout.

## Provider-free gates

| Gate | Result |
| --- | --- |
| Ruff | pass |
| mypy `src scripts` | pass, 226 source files |
| Full Python suite | pass, `2126/2126` in `687.00s` |
| Full Chromium suite | pass, `188/188` in `3232.23s` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, Codex CLI `0.144.1`, native command ready |
| Claude `aidd eval doctor` | pass, Claude Code `2.1.85`, native command ready |

`aidd doctor` also reported the isolated environment's generic-cli probe unavailable;
that runtime is not a target of the dual-provider acceptance gate. Both required live
provider commands were available and their scenario execution readiness was `pass`.

## Target readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Fresh clone: pass
- Setup: `bun install`, exit `0`
- Focused Vitest smoke: exit `0`
- TypeScript `tsc --noEmit`: exit `0`
- Classification: `pass`

The smoke used only authored commands that do not depend on future QA artifacts and
completed before any provider allocation.

## Bundle and isolation readiness

The installed candidate materialized and atomically sealed a synthetic
`AIDD-LIVE-007` bundle with bundle-relative references. Its source archive and wheel
digests matched the candidate above. Validation remained successful after the mutable
target root was removed.

- Bundle tree SHA-256: `0d2ff8903cd1e914a51121192d60f27f7e951840f73773b537dc214e3bd089b5`
- Manifest file count: `8`
- Canonical artifact count: `3`
- Reference mode: `bundle-relative`

Independent Codex and Claude Code canaries used the `macos-seatbelt` backend and the
real subprocess launch boundary. For both provider roots:

- own target, evidence, provider root, and private home were read/write;
- the AIDD source was readable but not writable;
- the sibling provider root and operator home were unreadable and unwritable;
- the own credential marker was present and the sibling marker was absent.

Both public live-acceptance preflights passed without allocating a provider run and
reported the candidate commit, tree, tracked-index digest, canonical scenario, native
runtime command, and independent provider layout.

## Source integrity and result

Postflight found no tracked or staged changes. The exact pre-existing excluded
untracked inventory remained:

- `docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`
- SHA-256: `72c8a71a50e8c689c3ee4c87d6df6c25ff7c77881c561eac99159583814644ed`

Overall result: `ready`. External acceptance must use the source commit, tree, and
exact wheel digest recorded above. This evidence-record commit is not a replacement
candidate and must not cause the wheel to be rebuilt.
