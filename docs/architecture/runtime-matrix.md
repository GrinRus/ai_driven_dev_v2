# Runtime Matrix

## Support policy

The project distinguishes between:

- **Tier 1 (release-blocking maintained)**
- **Tier 2 (actively maintained, non-blocking)**
- **Tier 3 (limited maintained, best-effort)**
- **Future / experimental (outside current tiers)**

## Runtime table

| Runtime | Status | Integration mode | Native logs | Structured logs | Native questions | Subagents | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `generic-cli` | Tier 1 (release-blocking maintained) | subprocess CLI | yes, if the wrapped tool emits them | adapter-defined | usually no | no | baseline portability adapter |
| `claude-code` | Tier 1 (release-blocking maintained) | CLI-first, optional richer SDK path later | yes | yes when available | yes when available | yes | first-class maintained runtime |
| `codex` | Tier 2 (actively maintained, non-blocking) | CLI-first | yes | yes when JSONL is emitted | yes when JSONL question events are emitted | yes | second-wave maintained runtime |
| `opencode` | Tier 3 (limited maintained, best-effort) | CLI-first / backend attach later | yes | yes when JSONL is emitted | yes when JSONL question events are emitted | yes | third-wave registered runtime |
| `qwen` | Experimental | CLI-first; dual-output bridge targeted | yes | yes when stream JSON is emitted | yes when JSONL question events are emitted | unknown | experimental Qwen Code runtime |
| `pi-mono` | Future / experimental (outside current tiers) | external bridge | adapter-defined | adapter-defined | adapter-defined | adapter-defined | treat as compatibility target first |

## Capability principle

A runtime does not need every capability to participate, but the adapter must declare what is missing and the core must apply an explicit fallback.

## Execution-command note

For CLI-backed runtimes, `aidd doctor` separates provider probing from execution
readiness. Claude Code, Codex, OpenCode, and Qwen default to `native` execution,
where AIDD adapts stage briefs and prompt packs to the raw provider CLI. Advanced
operators may configure `adapter-flags` execution with an AIDD-compatible wrapper
command that accepts the adapter flags for that runtime.

## Permission policy surface

Runtime config now carries an AIDD-owned permission layer:

```toml
[runtime.codex]
permission_policy = "full-access" # full-access | brokered | plan | deny-unapproved
interaction_mode = "batch"        # batch | evented | live
auto_approval_preset = "broad"    # off | conservative | broad
```

`full-access` is the backward-compatible default and keeps the existing provider-default
behavior. Non-full policies route normalized runtime approval requests through the
`RuntimeOperatorBroker`; policy-approved decisions are recorded in
`operator-decisions.jsonl`, and unresolved requests are recorded in
`operator-requests.jsonl` before the stage moves to `blocked`.

Provider adapters use their existing subprocess execution for `full-access`,
`batch`, and `evented` stage runs. In `brokered`/non-full `live` mode, AIDD only
launches a provider when the adapter has a confirmed live approval transport and a
CLI/UI decision provider is present. Current implemented live transports are:

- Qwen dual-file control through `--json-file` and `--input-file`;
- Codex app-server approvals through `codex app-server --listen stdio://`.

OpenCode remains degraded until its `serve` OpenAPI document exposes permission
request/response endpoints. Claude Code remains degraded until the CLI exposes a
permission prompt tool or an equivalent SDK callback path. When a live transport is
not confirmed, non-full policies block before launch rather than running a provider
command that AIDD cannot govern.

Manual real-protocol approval smoke is gated evidence, not a CI requirement. Use a
disposable local project with `permission_policy = "brokered"`,
`interaction_mode = "live"`, and `auto_approval_preset = "broad"` only after
`aidd doctor` reports live support for the target runtime. Preserve the
attempt-local approval artifacts for inspection and do not commit generated
`.aidd/` logs:

- Qwen: `qwen-events.jsonl`, `qwen-input.jsonl`, `operator-requests.jsonl`,
  `operator-decisions.jsonl`, and `runtime.log`.
- Codex: `codex-app-server.jsonl`, `operator-requests.jsonl`,
  `operator-decisions.jsonl`, and `runtime.log`.

## Tier commitments

The repository must ship working support for:

- `generic-cli`
- `claude-code`

before additional runtimes are considered release-blocking.

`codex` and `opencode` are registered execution runtimes for `aidd run`,
`aidd stage run`, `aidd doctor`, and maintained conformance coverage. Their lower
tiers describe release impact and parity expectations, not whether the adapters exist.
