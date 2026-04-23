# Adapter Protocol

## 1. Purpose

This document defines how the AIDD core talks to runtime adapters.

The protocol exists so the core can stay runtime-agnostic while adapters own runtime-specific launch, logging, and question-handling behavior.

## 2. Scope

Adapters are responsible for:

- probing runtime availability,
- declaring capabilities,
- launching a stage run,
- streaming raw runtime logs,
- emitting normalized lifecycle events,
- surfacing runtime questions or pauses,
- mapping runtime-specific failures into AIDD failure classes.

Adapters are not responsible for:

- stage semantics,
- document contract interpretation,
- validator policy,
- self-repair policy,
- backlog or roadmap logic.

## 3. Conceptual interface

The runtime adapter contract is defined as:

### `probe() -> RuntimeCapabilities`

Checks runtime availability and returns declared capabilities.

### `start(request) -> RuntimeStartResult`

Starts one stage attempt against a prepared workspace and returns execution outcome metadata.

### `send(session_id, payload) -> None`

Sends operator input to an active runtime session when interactive routing is supported.

### `interrupt(session_id) -> None`

Requests interruption for an active runtime session when interrupt support is declared.

### `stream_events(session_id) -> tuple[RuntimeEvent, ...]`

Returns runtime event chunks for adapters that expose stream polling.

### `stop(session_id) -> None`

Stops runtime execution and finalizes adapter-side teardown.

## 4. Stage run request

The core assembles the stage run request. Adapters consume it.

A stage run request should include:

- `run_id`
- `work_item`
- `stage`
- `workspace_root`
- `attempt_path`
- `stage_brief_path`
- `prompt_pack_paths`
- `timeout_seconds`
- `extra_env`
- `repository_root`

The request is core-owned. Adapters should not invent stage semantics.

## 5. Capability model

Each adapter must declare a capability report with at least:

- `runtime_id`
- `available`
- `version_text` when discoverable
- `supports_tool_calls`
- `supports_raw_log_stream`
- `supports_structured_log_stream`
- `supports_log_access`
- `supports_questions`
- `supports_resume`
- `supports_interrupts`
- `supports_subagents`
- `supports_hooks`
- `supports_non_interactive_mode`
- `supports_working_directory_control`
- `supports_env_injection`

The core uses this report to decide whether to proceed, degrade gracefully, or stop.

## 6. Log model

AIDD distinguishes three log layers:

### 6.1 Raw runtime log

The closest possible representation of native runtime output.

### 6.2 Structured runtime log

Runtime-native structured output when the runtime exposes it.

### 6.3 Normalized event stream

AIDD-owned lifecycle events such as:

- `run_started`
- `runtime_stdout`
- `runtime_stderr`
- `question_raised`
- `question_answered`
- `runtime_exit`
- `validation_started`
- `validation_failed`
- `repair_requested`
- `stage_passed`
- `stage_failed`

Adapters must preserve raw logs even when normalized events are also produced.

## 7. Question and resume handling

If a runtime can ask questions, the adapter should emit a normalized `question_raised` event with:

- the question text,
- any runtime-specific metadata,
- whether the runtime is waiting for an answer,
- whether resume is supported.

The core then:

1. shows the question in the CLI,
2. writes `questions.md`,
3. collects or waits for `answers.md`,
4. calls adapter `send()` when interactive continuation is supported, or reruns by policy when not.

If resume is not supported, the adapter must say so explicitly.

## 8. Failure mapping

Adapters must map runtime-local failures into one of the AIDD classes:

- `document_fail`
- `model_fail`
- `env_fail`
- `permission_fail`
- `auth_fail`
- `timeout`
- `adapter_fail`
- `harness_fail`
- `needs_user_input`

This mapping must prefer the earliest decisive signal, not the final symptom.

## 9. Workspace expectations

The core prepares the workspace before calling the adapter.

Adapters may assume:

- required input documents already exist,
- target output paths are known,
- prompt pack files are present,
- write permission policy has been resolved.

Adapters must not silently relocate outputs outside the expected workspace.

## 10. Conformance expectations

Every adapter must eventually pass conformance checks for:

- probe behavior,
- capability declaration,
- raw log capture,
- normalized event emission,
- exit classification,
- question surfacing,
- timeout behavior,
- workspace targeting.

## 11. Maintained adapters

Tier-1 maintained adapters are:

- `generic-cli`
- `claude-code`
- `codex`

Tier-2 adapters:

- `opencode`
- `pi-mono`

## 12. Summary

The adapter protocol keeps the boundary simple:

- the core owns workflow semantics,
- the adapter owns runtime execution and observation,
- the workspace documents remain the source of truth.
