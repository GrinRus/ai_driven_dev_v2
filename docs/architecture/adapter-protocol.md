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

An adapter should support these conceptual operations:

### `probe(config) -> capability report`

Checks whether the runtime binary or endpoint is available and returns capability information.

### `run_stage(request) -> run handle`

Starts a stage execution against a prepared workspace and returns a handle or session id for ongoing observation.

### `stream_events(handle) -> event stream`

Yields:

- raw stdout and stderr chunks,
- normalized lifecycle events,
- optional question or pause events.

### `resume(handle, answer_bundle)`

Resumes a paused run after user answers are available, if the runtime supports resume.

### `cancel(handle)`

Stops an active run and writes the correct final failure classification.

## 4. Stage run request

The core assembles the stage run request. Adapters consume it.

A stage run request should include:

- `run_id`
- `work_item`
- `stage`
- `workspace_root`
- `contract_path`
- `prompt_pack_path`
- `input_documents`
- `target_output_documents`
- `repair_mode`
- `attempt_index`
- `runtime_config`
- `time_budget`
- `permission_policy`
- `log_mode`

The request is core-owned. Adapters should not invent stage semantics.

## 5. Capability model

Each adapter must declare a capability report with at least:

- `runtime_id`
- `available`
- `version_text` when discoverable
- `supports_raw_log_stream`
- `supports_structured_log_stream`
- `supports_questions`
- `supports_resume`
- `supports_subagents`
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
4. calls adapter resume when supported.

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

The MVP maintained adapters are:

- `generic-cli`
- `claude-code`

Planned adapters:

- `codex`
- `opencode`

Future bridge target:

- `pi-mono`

## 12. Summary

The adapter protocol keeps the boundary simple:

- the core owns workflow semantics,
- the adapter owns runtime execution and observation,
- the workspace documents remain the source of truth.
