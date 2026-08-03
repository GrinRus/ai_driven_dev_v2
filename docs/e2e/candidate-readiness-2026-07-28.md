# Wave 36 Candidate Readiness — 2026-07-28

This is the sanitized `candidate-readiness-v1` record for the provider-free
`W36-E7-S4-T37` gate after the T61 browser-readiness correction. It contains no
credentials, credential digests, provider output, mutable target content, temporary
absolute paths, or user-authored snapshot content. No large scenario or evaluator
process was launched.

## Candidate identity

- Source commit: `98d97c7094d122f940fb617da217c5756eec565e`
- Source tree: `ebda9cdbbae178c3105bf92342228e14e8d14262`
- Tracked-index SHA-256: `01f9da4097916b6d41335681685e6be606d04dd574162b39e55d41f339683578`
- Tracked-bytes SHA-256: `7cba17504513ecb9b8cd0a8caa08affa441b7c28067d397c8ba10af633fe1c79`
- Source archive SHA-256: `098d587ddf1f02a1389afe73b14e7954d33a4927f2769000aa0a9acb34856ff0`
- Wheel: `ai_driven_dev_v2-0.1.0a16.dev0-py3-none-any.whl`
- Wheel size: `901755` bytes
- Wheel SHA-256: `3b6b8cf03eab108b1e66691b08e95f662dd5e450db4715f570820aa5ec8c1251`
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

## Provider-free gates

| Gate | Result |
| --- | --- |
| Ruff | pass |
| mypy `src scripts` | pass, 228 source files |
| Full Python suite | pass, `2145/2145` in `723.60s` |
| Exact-SHA full Chromium suite | pass, `188/188` in `2992.29s` |
| Isolated wheel install and `aidd doctor` | pass |
| Codex `aidd eval doctor` | pass, Codex CLI `0.144.1`, native command ready |
| Claude Code `aidd eval doctor` | pass, Claude Code `2.1.85`, native command ready |

The doctor process used the maintained user-local binary directory in `PATH`; the
first invocation without that directory classified Claude Code as unavailable, and
the corrected readiness invocation passed without changing source, package, or
provider state.

## Target readiness

- Scenario: `AIDD-LIVE-007`
- Target revision: `cf2d2b7edcf07adef2db7614557f4d7f9e2be7ba`
- Fresh clone: pass
- Setup: `bun install`, exit `0`
- Focused Vitest smoke: pass, `233/233`
- TypeScript `tsc --noEmit`: pass
- Classification: `pass`

The smoke used only authored commands that do not depend on future QA artifacts and
completed before any provider allocation. An initial setup command was invoked from
the temporary parent directory and found no package manifest; rerunning the identical
command from the pinned target root passed and left no target mutation beyond the
expected ignored dependency-install baseline.

## Bundle readiness

The installed candidate materialized and atomically sealed a synthetic
`AIDD-LIVE-007` bundle with bundle-relative references. Its source archive and wheel
digests matched the candidate above. Manifest validation remained successful after
the mutable target and work roots were removed.

- Bundle tree SHA-256: `421dcaf87dadeab33a0be32e3b79af6ed112591676a4555db892a0cc474fada5`
- Manifest file count: `11`
- Canonical artifact count: `6`
- Reference mode: `bundle-relative`

## Isolation and private-auth readiness

Independent Codex and Claude Code sessions used fresh roots, the
`macos-seatbelt` backend, and the real subprocess launch boundary. Both public
preflights passed without allocating an evaluator and reported
`auth_scope=provider-private` with `auth_state=pending-isolated-probe`.

For both runtime sessions:

- the minimal runtime auth file was seeded into the private home;
- the runtime-specific status probe passed before the sentinel command;
- the own provider root was readable and writable;
- the AIDD source was readable but not writable;
- the sibling provider root and operator home were unreadable and unwritable;
- unrelated provider credential variables were absent;
- session schema v2 recorded a passing probe, retained private auth, exit `0`, no
  integrity violations, and successful sentinel cleanup.

The active Claude Code host session obtains its authentication from the explicitly
selected `ANTHROPIC_AUTH_TOKEN` environment key rather than from `.claude.json`
alone. The launcher therefore allowlisted that one credential key for the Claude
probe. Its value and digest were not recorded, `ANTHROPIC_BASE_URL` remained absent,
and the credential was not made available to the Codex or sibling provider roots.

## Source integrity and result

Postflight found the same commit, tree, tracked bytes, tracked file count (`885`),
and empty tracked status. The exact pre-existing excluded untracked inventory
remained:

- `docs/analysis/ux-live-e2e-snapshot-2026-07-07.md`
- SHA-256: `72c8a71a50e8c689c3ee4c87d6df6c25ff7c77881c561eac99159583814644ed`

Overall result: `ready`. External medium acceptance must use the source commit,
tree, target pin, and exact wheel bytes recorded above. This evidence-record commit
is not a replacement candidate and must not cause the wheel to be rebuilt.
