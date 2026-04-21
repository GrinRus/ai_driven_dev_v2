# Analytical Note: `ai_driven_dev` -> `ai_driven_dev_v2`

## Executive summary

The original `ai_driven_dev` is more than a prompt collection. It is a governed workflow system with stage sequencing, artifact contracts, runtime-specific launch glue, hooks, and repository-level review flow.

Its main strength is workflow discipline. Its main weakness is dense coupling to a specific runtime surface and host lifecycle.

For `ai_driven_dev_v2`, the right move is a clean rebuild around contracts, adapters, harnesses, and evals rather than a wholesale port of runtime-specific code.

## Findings about the current project

Key carry-forward semantics from v1:

- canonical stage flow: `idea -> research -> plan -> review-spec -> tasklist -> implement -> review -> qa`
- durable stage results and review artifacts
- explicit workflow gates
- repository-local tooling for verification and review

Key problems that should not be carried over:

- runtime-specific launch glue mixed with business logic
- path and hook coupling
- monolithic runtime files
- assumptions that one host runtime defines the whole operator experience

## Findings about eval and harness practice

The strongest pattern across modern agent systems is outcome-based evaluation:

- evaluate what changed in the environment, not only what the model said;
- capture traces and runtime logs first;
- separate environment failures from model failures;
- turn real failures into replayable scenarios.

That makes harnesses a product subsystem, not an optional helper.

## Findings about runtime landscape

Different runtimes expose different surfaces:

- Claude Code emphasizes CLI/headless runs, skills, hooks, and subagents.
- Codex emphasizes `AGENTS.md`, skills, structured repo instructions, and headless execution.
- OpenCode emphasizes agents, plugins, permissions, and serve/attach workflows.
- Pi-style systems emphasize extensions, minimal harnesses, and bridge-friendly execution.

The common denominator is not one vendor API. It is:

- repository instructions,
- capability declaration,
- headless invocation,
- raw and structured logs,
- optional question or pause handling,
- runtime-local permissions and fallbacks.

## Main recommendation

Build v2 as:

- spec-first,
- contract-driven,
- adapter-based,
- harness-first,
- selective-port rather than wholesale-port.

Port only the load-bearing semantics. Rewrite host glue and runtime launch code from scratch.
