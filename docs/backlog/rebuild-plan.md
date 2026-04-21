# Rebuild Plan

## Intent

Build AIDD as a clean, runtime-agnostic system with document-first contracts, maintained adapters for `generic-cli` and `claude-code`, and harness/eval support from the first working slice.

## Phase 0 — bootstrap artifacts

### Deliverables

- root `README.md`, `AGENTS.md`, and `CLAUDE.md`
- main user stories
- architecture and protocol documents
- nested `AGENTS.md` files across major areas
- baseline contracts and prompt-pack skeletons
- `Makefile`, `aidd.example.toml`, `Dockerfile`, and CI skeleton

### Exit criteria

- a new contributor can understand the repository shape and start development
- a coding agent can navigate the repo with lightweight local instructions

## Phase 1 — foundation

### Deliverables

- runnable package skeleton for core, adapters, validators, harness, and evals
- initial contributor skills wired into the repo
- first executable CLI commands beyond placeholders

### Exit criteria

- the package installs locally
- the CLI exposes real health and workspace bootstrap commands

## Phase 2 — contracts first

### Deliverables

- stage contract files
- common document contract files
- validator strategy
- interview and repair policies

### Exit criteria

- at least one canonical stage has a complete document contract and validator plan
- contract docs define required files, not just ideas

## Phase 3 — core runtime loop

### Deliverables

- stage state machine
- run store
- interview controller
- repair controller
- stage result writer

### Exit criteria

- one stage can run end to end with document validation and repair
- unanswered required questions block progression cleanly

## Phase 4 — maintained adapters

### Deliverables

- `generic-cli` adapter
- `claude-code` adapter
- capability probing
- raw runtime log streaming to CLI
- normalized event stream

### Exit criteria

- both maintained adapters can run at least one stage
- capability differences are explicit and documented

## Phase 5 — harness and eval

### Deliverables

- scenario runner
- log capture
- log analysis
- grader output
- verdict writer
- first smoke and live E2E manifests

### Exit criteria

- a scenario run produces full audit artifacts
- log analysis identifies first-failure signals reliably

## Phase 6 — canonical stage set

### Deliverables

- `idea`
- `research`
- `plan`
- `review-spec`
- `tasklist`
- `implement`
- `review`
- `qa`

### Exit criteria

- each stage has contracts, validator coverage, and repair policy
- interview behavior is defined where ambiguity is expected

## Phase 7 — runtime widening

### Deliverables

- `codex` adapter
- `opencode` adapter
- parity scenarios across maintained and planned runtimes

### Exit criteria

- adding a runtime does not require core workflow rewrites
- parity scenarios expose capability gaps clearly

## Phase 8 — release hardening

### Deliverables

- operator handbook
- install docs for PyPI, `pipx`, `uv`, and containers
- CI scenario matrix
- support and maintenance policy

### Exit criteria

- the project is installable, runnable, and measurable in local and CI environments
