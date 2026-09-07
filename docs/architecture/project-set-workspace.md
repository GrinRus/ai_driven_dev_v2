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

## 4.1 Mode-specific capability matrix

The declared project set is always the provenance and validation scope. Whether it
also acts as a preventive runtime boundary depends on the configured permission mode
and the adapter transport that can enforce it:

| Permission mode | Declaration and attribution | Preventive containment | Outside-set change or request | Runtime discovery |
| --- | --- | --- | --- | --- |
| `full-access` | Resolved roots and project ids remain in context, stage, and run artifacts. | Not promised; provider-default access is preserved. | The post-run detector records exact paths and aggregate progression fails closed until the evidence is reviewed. | Discovery may be observed, but it cannot silently rewrite the declared set. |
| `brokered` | Same declaration and attribution contract. | Enforced where the adapter has a confirmed approval transport; otherwise the request is blocked before launch. | An out-of-root operation is rejected or requires an explicit operator decision; its path remains in evidence. | Discovery cannot expand the set without an explicit operator decision. |
| `plan` | Declaration and requested ownership are recorded before execution. | No provider execution is implied until the approval plan is resolved. | Requests remain approval-gated and do not advance aggregate workflow state while unresolved. | Discovery is not allowed to amend the declaration. |
| `deny-unapproved` | Same declaration and attribution contract. | Unapproved operations are denied; only policy-eligible requests may proceed. | An out-of-root operation is denied and leaves a durable decision/evidence record. | Discovery cannot expand the set. |

The matrix describes product claims, not a second permission engine. Provider-specific
approval mechanics remain adapter-owned, while the core owns declaration, attribution,
post-run detection, and fail-closed workflow progression.

## 4.2 Operator UI grouping

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

Declared project roots are always execution bounds for AIDD-owned planning and
validation. They are also preventive runtime bounds only in the non-full modes and
adapter transports that enforce them; `full-access` uses the same roots for
attribution and post-run detection instead of promising containment.

The core must reject or flag:

- absolute project roots;
- `..` traversal outside the declared local root;
- symlink resolution that escapes the local root;
- duplicate roots that make ownership ambiguous.

Adapters may observe runtime-specific project metadata, but that observation must
not expand the declared project set without an explicit operator decision. An
outside-set change in `full-access` is evidence for the detector and fail-closed
progression gate, not a silently accepted scope expansion.

When aggregate implementation finalization detects an outside-set change, it must
persist `outside-project-set.md` in the finalization attempt with the exact changed
paths and contributing task ids. The finalization status is failed, so the existing
implementation-finalization gate prevents downstream Review and QA from treating
the aggregate as successful.

## 6. Harness and eval expectations

Project-set support is not complete until harness coverage proves:

- a monorepo scenario can declare at least two project roots;
- stage artifacts preserve project ids;
- validation evidence remains attributable to the affected root;
- cross-project links survive result bundling;
- runtime-specific discovery does not change the declared project set.

Manual external eval coverage can be added after deterministic project-set coverage exists.

Current deterministic coverage includes
`harness/scenarios/deterministic/project-set-plan-context.yaml`, which declares
two local roots and verifies that both project ids remain visible in project-set
context, stage-brief evidence, attempt artifact indexes, and input bundles. The
operator artifact read model also exposes `project_set_context` so frontend
consumers can link the project-set context document without parsing stage briefs.

Implementation coverage is provided by
`harness/scenarios/deterministic/project-set-implementation-positive.yaml` and
`harness/scenarios/deterministic/project-set-implementation-outside.yaml`. The positive lane
changes both declared roots and proves successful aggregate finalization. The negative lane
expects the non-zero fail-closed exit, verifies exact outside-root path and task attribution in
`outside-project-set.md`, and confirms that Review and QA do not progress. Deterministic harness
manifests may declare a non-zero `expected_exit_code` when that exit is the acceptance signal;
the actual exit and expectation are retained in the harness metadata.
