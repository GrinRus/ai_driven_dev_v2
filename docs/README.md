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

- [Product Positioning](./product/product-positioning.md) — operator promise, product principles,
  and the boundary between current alpha claims and migration targets.
- [User Stories](./product/user-stories.md) — product personas, outcomes, and scope boundaries.
- [User-story traceability view](./product/user-story-traceability.md) — generated, byte-stable
  links from each story to contracts, code boundaries, tests, scenarios, and evidence.
- [User-story traceability registry](./product/user-story-traceability.yaml) — structured source
  data for the generated view.
- [Roadmap](./backlog/roadmap.md) — canonical waves, epics, slices, and local tasks.
- [Backlog](./backlog/backlog.md) — short actionable queue derived from the roadmap.

## Architecture and contracts

- [Target Architecture](./architecture/target-architecture.md) — system boundaries and source of
  truth.
- [Iterative Delivery Decisions](./architecture/iterative-delivery-decisions.md) — accepted
  migration policies, including the direct breaking replacement.
- [Iterative Delivery Contract](./architecture/iterative-delivery-contract.md) — accepted target
  records, ownership, finite routes, lifecycle and migration map; current alpha contracts stay
  in effect until implementation.
- [Document Contracts](./architecture/document-contracts.md) — Markdown inputs, outputs, and
  validation model.
- [Adapter Protocol](./architecture/adapter-protocol.md) — runtime adapter boundary.
- [Runtime Matrix](./architecture/runtime-matrix.md) — supported runtimes and capabilities.
- [Task Execution](./architecture/task-execution.md) — dependency-aware implementation tasks.
- [Project-set Workspace](./architecture/project-set-workspace.md) — declared multi-root scope.
- [Operator Frontend](./architecture/operator-frontend.md) — UI architecture over the shared
  workflow state.
- [Iterative Operator UX](./architecture/iterative-operator-ux.md) — future journey, screens,
  states, authority, and evidence design, with an inspectable concept and current-UI audit.

## Harness, evaluation, and browser quality

- [Scenario Matrix](./e2e/scenario-matrix.md) — maintained deterministic and manual lanes.
- [Manual Evaluation Catalog](./e2e/live-e2e-catalog.md) — pinned external scenarios and evidence
  boundaries.
- [Live Quality Rubric](./e2e/live-quality-rubric.md) — manual outcome assessment.
- [SWE-bench migration fixture proposal](./analysis/swe-bench-migration-evaluation-2026-10-06.md)
  — bounded independent-code-oracle research for the comparison protocol with accepted
  P01–P07 parameters; the full protocol, selection and runtime qualification remain pending.
- [Browser Testing](./architecture/browser-testing.md) — browser fixtures, journeys, and rendered
  acceptance.

Historical audits, completed planning, and superseded release notes are retained in Git history.
The documentation tree contains current guides, contracts, accepted remediation plans, scenario
definitions, and current release/UI acceptance records. New run evidence belongs in its generated
evaluation bundle.
