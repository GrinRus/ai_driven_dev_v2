# Project-Set Workspace Contract

## 1. Purpose

Project-set workflow support lets one AIDD flow operate on a declared set of
local project roots, including monorepo package roots.

The goal is to coordinate cross-project work while preserving:

- one governed stage graph;
- document-first artifacts;
- per-project ownership;
- bounded execution;
- comparable validation and eval evidence.

This contract defines product and architecture boundaries before implementation.

## 2. Scope

Supported target model:

- one repository or local workspace root;
- one `.aidd/` workspace for the governed flow;
- one or more declared project roots inside that local root;
- stable project ids used in artifacts and reports.

Out of scope until a separate architecture decision:

- implicit repository discovery;
- cloud orchestration;
- cloning or coordinating unrelated remote repositories;
- cross-repository auth, branch, PR, or release management;
- runtime-specific project discovery in core workflow semantics.

## 3. Declaration shape

The supported configuration shape is:

```toml
[[project_set.projects]]
id = "api"
root = "services/api"
role = "primary"
```

Rules:

- `id` is required, stable, unique, and safe for artifact labels;
- `root` is required, repository-relative, and must not escape the declared local root;
- `role` is optional descriptive metadata and does not change workflow semantics;
- duplicate ids or roots are invalid;
- missing roots are preflight failures unless an explicit future mode allows planned roots.

The first resolver implementation parses this declaration and validates that each
root exists inside the repository root. The stage-integration slice persists the
resolved project set in the work-item context as
`.aidd/workitems/<id>/context/project-set.md` and includes that document in stage
briefs and attempt input bundles when a config declares projects.

## 4. Artifact ownership

Project-set artifacts must make ownership visible without replacing the existing
stage document model.

Required behavior:

- stage briefs must state the declared project set when a flow uses one;
- stage outputs that affect a project should name the relevant project id;
- `stage-result.md` must include `Project-set evidence` when
  `workitems/<id>/context/project-set.md` exists, citing the context path plus
  every declared project id and repository-relative root;
- validation evidence should preserve which project root was checked;
- runtime logs should keep the current runtime/adapter provenance and may add
  project labels only as metadata;
- cross-project references should name both source and target project ids.

The core should keep canonical stage documents in the existing work-item tree.
Project-specific evidence may be referenced from those documents or from reports,
but it must remain traceable from the stage result.

## 4.1 Operator UI grouping

The operator UI may group read-only surfaces by declared root, but it must not create a
second project-set authority.

Required UI behavior:

- `Implement Review` groups source diff rows by `root_id`, `root_label`, and
  `root_relative_root` when `workitems/<id>/context/project-set.md` exists;
- source changes outside declared roots are flagged as `outside-project-set`;
- `.aidd/` artifacts stay separate from source changes and are not treated as editable
  project roots;
- single-project clients that ignore optional grouping fields continue to see the same
  source and artifact arrays;
- unrelated repositories must be opened through separate UI sessions or work items, not
  mixed into one project-local `.aidd/`.

## 5. Execution bounds

Declared project roots are execution bounds for AIDD-owned planning and
validation.

The core must reject or flag:

- absolute project roots;
- `..` traversal outside the declared local root;
- symlink resolution that escapes the local root;
- duplicate roots that make ownership ambiguous.

Adapters may observe runtime-specific project metadata, but that observation must
not expand the allowed project set without an explicit operator decision.

## 6. Harness and eval expectations

Project-set support is not complete until harness coverage proves:

- a monorepo scenario can declare at least two project roots;
- stage artifacts preserve project ids;
- validation evidence remains attributable to the affected root;
- cross-project links survive result bundling;
- runtime-specific discovery does not change the declared project set.

Live E2E coverage can be added after deterministic project-set coverage exists.

Current deterministic coverage includes
`harness/scenarios/deterministic/project-set-plan-context.yaml`, which declares
two local roots and verifies that both project ids remain visible in project-set
context, stage-brief evidence, attempt artifact indexes, and input bundles. The
operator artifact read model also exposes `project_set_context` so frontend
consumers can link the project-set context document without parsing stage briefs.
