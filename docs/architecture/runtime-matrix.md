# Runtime Matrix

## Support policy

The project distinguishes between:

- **MVP maintained**
- **Planned**
- **Future / experimental**

## Runtime table

| Runtime | Status | Integration mode | Native logs | Structured logs | Native questions | Subagents | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `generic-cli` | MVP maintained | subprocess CLI | yes, if the wrapped tool emits them | adapter-defined | usually no | no | baseline portability adapter |
| `claude-code` | MVP maintained | CLI-first, optional richer SDK path later | yes | yes when available | yes when available | yes | first-class maintained runtime |
| `codex` | MVP maintained | CLI-first | yes | partial/adapter-defined | adapter-defined | yes | tier-1 maintained runtime |
| `opencode` | Tier-2 maintained | CLI / backend attach | yes | adapter-defined | adapter-defined | yes | tier-2 runtime after conformance rollout |
| `pi-mono` | Tier-2 maintained | CLI-first bridge | yes | adapter-defined | adapter-defined | adapter-defined | tier-2 bridge runtime after conformance rollout |

## Capability principle

A runtime does not need every capability to participate, but the adapter must declare what is missing and the core must apply an explicit fallback.

## MVP commitment

The repository must ship working support for:

- `generic-cli`
- `claude-code`
- `codex`

before additional runtimes are considered stable.
