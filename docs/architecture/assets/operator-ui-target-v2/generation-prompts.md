# AIDD target operator UI v2 — generation prompts

These prompts produced the visual reference set for
[`operator-frontend-target-ux.md`](../../operator-frontend-target-ux.md). The images are
design targets, not proof of implemented behavior. Product semantics, actions, states, and
responsive rules in the architecture document take precedence over incidental generated text.

## Shared visual direction

- A calm, high-density desktop operations product rather than a marketing dashboard.
- Navy project/work-item rail, off-white workspace, cobalt primary actions, restrained green,
  amber, and red semantic states, no gradients or decorative hero art.
- One stable hierarchy: `Project -> Work Item -> Stage -> Task/Decision -> Run -> Document`.
- Exact stage order: Idea, Research, Plan, Review Spec, Tasklist, Implement, Review, QA.
- Runner selection is contextual and appears only beside an action that launches work.
- Generated Markdown and evidence are read-only; operator-authored requests and answers use
  explicit Write/Preview surfaces.
- No fake progress, invented history, chat-shaped workflow, or kanban-first task management.

## Screen prompts

1. **Project work items** — Group work by `Needs input`, `Running`, `Ready`, and `Complete`;
   select one item and expose its single required next action in a contextual inspector.
2. **Create work item** — Use a focused form with title, stable work-item ID, destination,
   operator-request Markdown Write/Preview, and one `Create work item` action. Do not select a
   runner before a runnable action exists.
3. **Work item launch** — Show the work overview, exact eight-stage strip, readiness, scope,
   and a Runner selector immediately beside `Launch workflow`.
4. **Task workspace** — Use grouped task lists (`Ready`, `Running`, `Blocked`, `Done`), a
   selected-task detail surface, acceptance criteria, linked documents, and contextual Runner
   plus `Run task`.
5. **Active task run** — Keep the task selected; show factual elapsed time, last output,
   milestone, attempt identity, cancellation semantics, and a collapsible live terminal tray.
6. **Decision workbench** — Put the blocking question first, cite source snippets, and collect
   an operator-authored Markdown answer with `Resolved`, `Partial`, or `Deferred` status.
7. **Validation repair** — Anchor a validation finding to the retained Markdown line; show rule,
   severity, repair hint, attempt/budget, exact brief, contextual Runner, and `Run repair`.
8. **Markdown workspace** — Group documents by role; show role/stage/attempt/freshness,
   Read/Source/Compare, heading map, anchored context, and one `Request change` action. Keep
   canonical stage output visibly read-only.
9. **Implementation review** — Combine changed-file navigation, real unified diff, claims versus
   actual verification, evidence, risk, contextual Runner, and `Proceed to Review`.
10. **Review and QA remediation** — Select concrete findings and evidence, author a Markdown
    remediation request, show downstream staleness, and send only selected findings back to
    Implement with an explicit Runner.
11. **Run history** — Provide filters, chronological runs, retained attempts, exact event
    timeline, raw logs/artifacts, and evidence lineage. Do not show a Runner selector.
12. **Flow complete** — Show all stages complete, immutable handoff, final documents/evidence,
    QA result, retained run IDs, one recommended `Create new work item` action, and quieter
    follow-up actions.
13. **Mobile decision** — At a 390x844 viewport, put the blocking question and answer status in
    the first reading flow, collapse evidence, preserve Write/Preview and draft state, and pin
    `Save resolved answer` as the only primary action.
