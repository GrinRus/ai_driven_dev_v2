# Backlog Coverage

Current planning baseline:

- `docs/backlog/backlog.md` has `none` under `Next`, `Soon`, and `Parking lot`.
- `docs/backlog/roadmap.md` marks Wave 15 as `blocked`.
- Wave 15 completed its local deterministic work and explicitly blocked the two external evidence tasks.
- Wave 12 and Wave 13 local task bullets now carry explicit `(done)` markers.

| Roadmap ID | Level (`wave`, `epic`, `slice`, `task`) | Declared status | Evidence in repo | Verified status | Dependency issues | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| W15 | wave | blocked | `docs/backlog/roadmap.md` Wave 15 section and backlog sync notes | blocked | external live/release prerequisites | Local deterministic work is complete; external evidence tasks are blocked. |
| W15-E0 | epic | done | Wave 15 queue restoration section | ready-and-evidenced | none | Governance bootstrap was completed before the active cycle. |
| W15-E0-S1 | slice | done | `W15-E0-S1-T1` marked done | ready-and-evidenced | none | Opened Wave 15 and restored queue entries. |
| W15-E0-S1-T1 | task | done | Roadmap task marked `(done)` | ready-and-evidenced | none | Queue restoration task is closed. |
| W15-E1 | epic | done | Lint gate recovery section | ready-and-evidenced | none | Closed by commit `3a939bb`. |
| W15-E1-S1 | slice | done | `W15-E1-S1-T1` marked done | ready-and-evidenced | none | Lint gate recovery is complete. |
| W15-E1-S1-T1 | task | done | `tests/test_docs_consistency.py` uses adjacent string literals; `uv run ruff check .` passes | ready-and-evidenced | none | Commit: `3a939bb docs(W15-E1-S1-T1): close lint gate recovery`. |
| W15-E2 | epic | done | Roadmap evidence hygiene section | ready-and-evidenced | none | Closed by commit `fb7e976`. |
| W15-E2-S1 | slice | done | `W15-E2-S1-T1` marked done | ready-and-evidenced | none | Wave 12/13 local task markers normalized. |
| W15-E2-S1-T1 | task | done | Marker check returned no unmarked Wave 12/13 task bullets | ready-and-evidenced | none | Commit: `fb7e976 docs(W15-E2-S1-T1): normalize historical task markers`. |
| W15-E3 | epic | blocked | External evidence lanes section | blocked | live wrapper and release prerequisites unavailable | Both child slices are blocked. |
| W15-E3-S1 | slice | blocked | Blocked reason records missing wrapper env vars | blocked | `AIDD_EVAL_CODEX_COMMAND` and `AIDD_EVAL_OPENCODE_COMMAND` unset | Commit: `9296b84 docs(W15-E3-S1-T1): record manual live blocker`. |
| W15-E3-S1-T1 | task | blocked | Live preflight recorded wrapper env vars unset | blocked | no AIDD-compatible runtime wrapper command configured | Do not run live E2E until wrapper/auth prerequisites exist. |
| W15-E3-S2 | slice | blocked | Blocked reason records missing release candidate context | blocked | no release tag at `HEAD`; no local publish token env vars | Commit: `6265473 docs(W15-E3-S2-T1): record release evidence blocker`. |
| W15-E3-S2-T1 | task | blocked | Release preflight recorded missing tag/publish context | blocked | release candidate tag and publishing context unavailable | Do not claim release-channel evidence until a tagged publish path runs. |

False positives / drift fixed:

- The prior report said the lint gate was red; it is now green.
- The prior report said Wave 15 needed opening; Wave 15 is now opened and either done or blocked.
- The prior report said Wave 12/13 task bullets lacked explicit done markers; they now have `(done)` markers.
