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
root before calling the adapter surface. Runtime permission settings are part of the
request so adapters can either enforce them through a live provider transport or report an
explicit blocked operator request.

The adapter returns:

- whether the runtime invocation succeeded;
- the stable execution status: `succeeded`, `failed`, or `blocked_for_operator`;
- a normalized details string, usually the adapter exit classification;
- the canonical adapter outcome and paths to the committed `runtime.log` and
  `runtime-exit.json` evidence envelope;
- optional paths for emitted structured artifacts such as `runtime.jsonl` and `events.jsonl`;
- an optional path to `questions.md` when runtime-native question events were persisted.
- optional paths for `operator-requests.jsonl` and `operator-decisions.jsonl` when runtime
  approval handling was involved.

Runtime stdout, stderr, combined raw logs, exit code, and adapter-specific exit classification
are persisted as attempt artifacts such as `runtime.log` and `runtime-exit.json`; they are not
returned as in-memory workflow semantics for the core to interpret. The result instead exposes
their durable paths and a canonical adapter outcome.

The request is core-owned. Adapters must not invent stage semantics or silently relocate
stage outputs outside the expected workspace.

### 3.1 Current request fields

The implemented request shape contains:

- `runtime_id`
- `execution_mode`
- `permission_policy`
- `interaction_mode`
- `auto_approval_preset`
- `timeout_seconds`
- `stage`
- `work_item`
- `run_id`
- `workspace_root`
- `stage_brief_path`
- `prompt_pack_paths`
- `repository_root`
- `project_roots`
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
- `supports_permission_policy`
- `supports_live_decisions`
- `supports_deferred_resume`
- `preferred_transport`

The core and CLI use this report to decide whether to proceed, degrade explicitly, or stop.

## 4.1 Runtime operator requests

AIDD separates product questions from runtime approvals:

- product questions remain in stage-level `questions.md` and `answers.md`;
- runtime approvals are attempt artifacts and job state, recorded as
  `operator-requests.jsonl` and `operator-decisions.jsonl`.

Adapters normalize runtime permission prompts into `RuntimeOperatorRequest` values with
runtime id, stage, kind, tool name, payload, cwd, paths, risk, and suggestions. The
`RuntimeOperatorBroker` persists the request, applies the AIDD policy engine, records
policy decisions, and returns a `RuntimeOperatorDecision` when a decision is immediately
available. If a non-full-access request cannot be decided inside the current transport, the
adapter returns `blocked_for_operator`; the core marks the stage blocked and does not run
output validation.

Current subprocess-backed provider adapters do not yet own live decision transports. For
`permission_policy != "full-access"`, they block before launch instead of silently running a
provider in a mode AIDD cannot govern. Live provider paths can land incrementally on the same
request/decision artifacts.

## 5. Log and event model

AIDD distinguishes three observation layers.

### 5.1 Raw runtime log

The closest possible representation of native runtime stdout/stderr. This is implemented for
CLI-backed adapters through subprocess capture and `runtime.log` persistence. Capture is
disk-backed: the sink writes the complete combined stream in observed order while retaining
only the latest 256 KiB of stdout, 256 KiB of stderr, and 512 KiB of combined output in
memory. Schema-v1 `runtime-exit.json` records full byte/character counters and additive tail
truncation metadata. Oversized chunks are written completely to disk and truncated only in the
in-memory tail.

Structured JSONL records are processed incrementally while capture is active, or read from the
provider-native JSONL artifact. Consumers never require the full raw stdout/stderr text in
memory. A callback, writer, or capture failure terminates the owned process group and cannot
publish a successful evidence commit.

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

### 7.1 Runtime outcome and evidence decision table

Every launched, blocked, denied, cancelled, timed-out, or launch-failed adapter attempt commits
one evidence envelope. `runtime.log` is written atomically first and schema-v1
`runtime-exit.json` is the commit marker written last. Writers retain the adapter-specific
`exit_classification` and also publish the canonical `adapter_outcome`.

| Terminal condition | `adapter_outcome` | `stop_reason` | `exit_code` |
| --- | --- | --- | --- |
| runtime completed successfully | `success` | absent | provider/process code |
| runtime exited unsuccessfully | `runtime_failure` | `runtime_failure` | provider/process code |
| runtime budget expired | `timeout` | `timeout` | provider/process code when available |
| execution was cancelled | `cancellation` | `cancellation` | provider/process code when available |
| operator or policy denied execution | `denial` | `denial` | `null` when no provider process result exists |
| execution is waiting for an operator | `blocked` | `blocked` | `null` |
| executable launch failed | `launch_failure` | `launch_failure` | `null` |

Success never has a stop reason. Blocked and launch-failure evidence never fabricates a process
exit code. Workflow policy uses the canonical outcome; adapter-specific classifications remain
available for provider diagnostics.

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
- `qwen` - Experimental registered runtime.

Future bridge target:

- `pi-mono`

## 11. Summary

The adapter protocol keeps the boundary simple:

- the core owns workflow semantics and document gates;
- the adapter owns runtime execution and observation;
- Markdown workspace documents remain the source of truth.
