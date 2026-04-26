# Runtime Matrix

## Support policy

The project distinguishes between:

- **Tier 1 (release-blocking maintained)**
- **Tier 2 (actively maintained, non-blocking)**
- **Tier 3 (planned/limited)**
- **Future / experimental (outside current tiers)**

## Runtime table

| Runtime | Status | Integration mode | Native logs | Structured logs | Native questions | Subagents | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `generic-cli` | Tier 1 (release-blocking maintained) | subprocess CLI | yes, if the wrapped tool emits them | adapter-defined | usually no | no | baseline portability adapter |
| `claude-code` | Tier 1 (release-blocking maintained) | CLI-first, optional richer SDK path later | yes | yes when available | yes when available | yes | first-class maintained runtime |
| `codex` | Tier 2 (actively maintained, non-blocking) | CLI-first | yes | partial/adapter-defined | adapter-defined | yes | second-wave maintained runtime |
| `opencode` | Tier 3 (planned/limited) | CLI / backend attach | yes | adapter-defined | adapter-defined | yes | third-wave runtime |
| `pi-mono` | Future / experimental (outside current tiers) | external bridge | adapter-defined | adapter-defined | adapter-defined | adapter-defined | treat as compatibility target first |

## Capability principle

A runtime does not need every capability to participate, but the adapter must declare what is missing and the core must apply an explicit fallback.

## Execution-command note

For CLI-backed runtimes, `aidd doctor` separates provider probing from execution
readiness. Codex and OpenCode default to `native` execution, where AIDD adapts
stage briefs and prompt packs to the raw provider CLI. Advanced operators may
configure `adapter-flags` execution with an AIDD-compatible wrapper command that
accepts the adapter flags for that runtime.

## Tier 1 commitment

The repository must ship working support for:

- `generic-cli`
- `claude-code`

before additional runtimes are considered stable.
