# Reconciliation history archive index

This index records where the historical backlog reconciliation is preserved. It is a
discoverability aid, not a second planning authority: [`roadmap.md`](roadmap.md) owns the
current hierarchy, statuses, and dependencies, while [`backlog.md`](backlog.md) owns the
bounded actionable queue.

## Archived source

- Source path: `docs/backlog/reconciliation-history-2026-09-05.md`
- Immutable Git archive revision: `e46ea4caa21216224cc809555e713ee11859501e`
- Archive size: 509 historical reconciliation bullets
- SHA-256: `6df9386f34441f86e185bae4686363b776bea04eb28a786ac287a6367c0b4d0a`
- Retrieval command: `git show e46ea4caa21216224cc809555e713ee11859501e:docs/backlog/reconciliation-history-2026-09-05.md`

The archive revision is an ancestor of `origin/main`; later cleanup removed the bulky copy
from the active checkout without rewriting the merged history. Historical queue instructions
are therefore retained for audit and search, but cannot change the current queue or status
algebra. Search an archived ID with `git grep -n '<task-id>'
e46ea4caa21216224cc809555e713ee11859501e -- docs/backlog/reconciliation-history-2026-09-05.md`.
