# AIDD Documentation

Use this page to enter the documentation by role. The root `README.md` is the product overview
and quick start; the documents below own detailed behavior and policy.

## Operators

- [Operator Handbook](./operator-handbook.md) — install, configure, start, resume, and inspect
  workflows through the CLI or local UI.
- [Operator Troubleshooting](./operator-troubleshooting.md) — diagnose installation, runtime,
  workspace, validation, and UI failures.
- [Operator Support Policy](./operator-support-policy.md) — supported surfaces and issue-report
  requirements.
- [Compatibility Policy](./compatibility-policy.md) — supported Python versions, platforms, and
  runtime tiers.

## Contributors and maintainers

- [Contributing Guide](../CONTRIBUTING.md) — development setup, task selection, design rules, and
  pull-request expectations.
- [Agent Development Map](./agent-development.md) — instruction inheritance, ownership, skills,
  and focused Python, Node, and browser checks.
- [Governance](../GOVERNANCE.md) — roles, decisions, merge authority, and project continuity.
- [Release Checklist](./release-checklist.md) — release preparation, publication, and package
  verification.
- [Changelog](../CHANGELOG.md) — user-visible changes by release.

## Product and planning

- [User Stories](./product/user-stories.md) — product personas, outcomes, and scope boundaries.
- [Roadmap](./backlog/roadmap.md) — canonical waves, epics, slices, and local tasks.
- [Backlog](./backlog/backlog.md) — short actionable queue derived from the roadmap.

## Architecture and contracts

- [Target Architecture](./architecture/target-architecture.md) — system boundaries and source of
  truth.
- [Document Contracts](./architecture/document-contracts.md) — Markdown inputs, outputs, and
  validation model.
- [Adapter Protocol](./architecture/adapter-protocol.md) — runtime adapter boundary.
- [Runtime Matrix](./architecture/runtime-matrix.md) — supported runtimes and capabilities.
- [Task Execution](./architecture/task-execution.md) — dependency-aware implementation tasks.
- [Project-set Workspace](./architecture/project-set-workspace.md) — declared multi-root scope.
- [Operator Frontend](./architecture/operator-frontend.md) — UI architecture over the shared
  workflow state.

## Harness, evaluation, and browser quality

- [Scenario Matrix](./e2e/scenario-matrix.md) — maintained deterministic and manual lanes.
- [Manual Evaluation Catalog](./e2e/live-e2e-catalog.md) — pinned external scenarios and evidence
  boundaries.
- [Live Quality Rubric](./e2e/live-quality-rubric.md) — manual outcome assessment.
- [Browser Testing](./architecture/browser-testing.md) — browser fixtures, journeys, and rendered
  acceptance.

Timestamped documents under `analysis/` and `e2e/` are retained audit evidence. Start from the
stable guides above unless a task or release record points to a specific audit.
