# Adapter Protocol

## 1. Purpose

This document defines how the AIDD core talks to runtime adapters.

The protocol exists so the core can stay runtime-agnostic while adapters own
runtime-specific launch, logging, capability probing, and question-observation behavior.

## 2. Scope

Adapters are responsible for:

- probing runtime availability;
- declaring runtime capabilities;
- launching a prepared stage request;
- streaming and persisting raw runtime logs when the runtime exposes them;
- preserving runtime-native structured output when available;
- surfacing runtime question or pause signals when the adapter can detect them;
- mapping runtime-specific exits into stable AIDD classifications.

Adapters are not responsible for:

- stage semantics;
- document contract interpretation;
- validator policy;
- self-repair policy;
- backlog or roadmap logic;
- deciding whether a stage may progress.

Execution note:

- probe may inspect a raw runtime binary or endpoint;
- stage execution may use either `native` provider CLI mode or a configured
  `adapter-flags` wrapper command;
- the probe target and the execution command do not have to be identical.

## 3. Implemented interface

The current implementation uses a synchronous stage execution boundary:

```text
StageRuntimeRequest -> RuntimeAdapterExecutionResult
```

The core prepares the workspace, stage brief, input bundle, prompt-pack paths,
attempt metadata, repair context, runtime id, execution mode, timeout, and repository
root before calling the adapter surface.

The adapter returns:

- whether the runtime invocation succeeded;
- a normalized details string, usually the adapter exit classification;
- optional paths for emitted structured artifacts such as `runtime.jsonl` and `events.jsonl`;
- an optional path to `questions.md` when runtime-native question events were persisted.

Runtime stdout, stderr, combined raw logs, exit code, and normalized exit classification are
persisted as attempt artifacts such as `runtime.log` and `runtime-exit.json`; they are not
returned as in-memory workflow semantics for the core to interpret.

The request is core-owned. Adapters must not invent stage semantics or silently relocate
stage outputs outside the expected workspace.

### 3.1 Current request fields

The implemented request shape contains:

- `runtime_id`
- `execution_mode`
- `timeout_seconds`
- `stage`
- `work_item`
- `run_id`
- `workspace_root`
- `stage_brief_path`
- `prompt_pack_paths`
- `repository_root`
- `attempt_number`
- `repair_mode`
- `input_bundle_path`
- `repair_brief_path`
- `repair_context_markdown`

The request deliberately names concrete prepared artifacts rather than asking adapters to
resolve contracts or derive stage IO.

## 4. Capability model

Each adapter declares a capability report with at least:

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

The core and CLI use this report to decide whether to proceed, degrade explicitly, or stop.

## 5. Log and event model

AIDD distinguishes three observation layers.

### 5.1 Raw runtime log

The closest possible representation of native runtime stdout/stderr. This is implemented for
CLI-backed adapters through subprocess capture and `runtime.log` persistence.

### 5.2 Structured runtime log

Runtime-native structured output when the runtime exposes it. Support is adapter-defined.

### 5.3 Normalized event stream

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

Normalized events are persisted per attempt when a maintained adapter observes structured
JSONL runtime output. AIDD does not synthesize normalized events from plain text logs. Raw
logs remain mandatory whenever the runtime can expose them.

## 6. Question and resume handling

Question support has two implemented layers:

- stage document routing validates `questions.md` and `answers.md`, blocks unresolved
  `[blocking]` questions, and lets a run resume after answers are present;
- runtime-native question or pause events are mapped into the same `questions.md` path when
  the adapter observes structured question/pause events.

When an adapter cannot detect native question events, the durable document path remains the
fallback. If resume is not supported by the runtime, the adapter must declare that limitation
instead of implying parity.

## 7. Failure taxonomy

Adapter exits, validator outcomes, and harness verdicts use different local vocabularies. The
bridge taxonomy below is the documented source of truth for cross-layer reporting.

| Layer signal | AIDD failure class | Notes |
| --- | --- | --- |
| missing or invalid stage documents | `document_fail` | Produced by structural, semantic, or cross-document validation. |
| unresolved blocking questions | `needs_user_input` | Blocks progression until `answers.md` resolves the question ids. |
| runtime non-zero exit without clearer cause | `model_fail` | Adapter classification may preserve the runtime-local exit value. |
| runtime command unavailable or setup failure | `env_fail` | Includes missing binaries and invalid execution command setup. |
| runtime permission or policy denial | `permission_fail` | Use the earliest decisive permission signal. |
| missing provider authentication | `auth_fail` | Use when the runtime output clearly identifies auth state. |
| timeout | `timeout` | Applies to configured subprocess/runtime budgets. |
| adapter bug, invalid adapter state, or unsupported request | `adapter_fail` | Use when AIDD adapter logic failed before a trustworthy runtime result exists. |
| harness setup, teardown, fixture, or scenario failure | `harness_fail` | Used by eval/harness lanes, not normal stage progression. |

This mapping must prefer the earliest decisive signal, not the final symptom.

## 8. Workspace expectations

The core prepares the workspace before calling the adapter.

Adapters may assume:

- required input documents already exist;
- target output paths are known;
- prompt-pack files are present;
- write permission policy has been resolved by configuration and operator choice.

Adapters must preserve workspace locality. If a runtime writes expected stage documents under
`output/`, the core may promote those misplaced outputs back to the canonical stage root before
validation.

## 9. Conformance expectations

Maintained adapters are checked for:

- probe behavior;
- capability declaration;
- raw log capture;
- exit classification;
- question surfacing where supported;
- timeout behavior;
- workspace targeting.

Normalized event emission is a target conformance dimension, but current adapter support is
partial and should not be claimed for every runtime until the event pipeline is fully wired.

## 10. Registered runtimes

Current registered runtimes:

- `generic-cli` - Tier 1 release-blocking maintained runtime.
- `claude-code` - Tier 1 release-blocking maintained runtime.
- `codex` - Tier 2 actively maintained runtime.
- `opencode` - Tier 3 limited maintained runtime.

Future bridge target:

- `pi-mono`

## 11. Summary

The adapter protocol keeps the boundary simple:

- the core owns workflow semantics and document gates;
- the adapter owns runtime execution and observation;
- Markdown workspace documents remain the source of truth.
