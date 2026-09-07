---
name: task-slicing
description: Decompose an accepted AIDD roadmap outcome into independently reviewable local tasks with explicit scope, dependencies, and verification.
---

# task-slicing

Use when a task is too coarse to implement or review. For hierarchy, IDs, and queue
mutations, follow [backlog-ops](../backlog-ops/SKILL.md); do not duplicate its rules.
An analysis request produces a proposed decomposition without updating planning files.

1. State the parent outcome and separate its independently observable outputs.
2. Group changes around one outcome and dominant owner, retaining the contract, code,
   test, and scenario changes needed to prove that outcome. Crossing a file or subsystem
   boundary is not by itself a reason to separate a coherent fix from its regression.
3. Split independent features, broad contract design versus rollout, or unrelated
   verification paths into additional local tasks in the same slice.
4. Give each task a verb-led action, output, allowed scope, dependency, and main
   verification signal. Order dependencies before consumers and preserve active IDs
   according to backlog-ops.
5. Create another slice only for a different meaningful outcome; create another epic
   only when the theme changes. Do not add scope simply to make the hierarchy symmetric.

For example, `Finish the adapter` hides multiple outcomes. Separate command assembly,
raw stream capture, and approval/interview transport when each can be reviewed and
verified independently. Keep a capture fix and the test proving its log fidelity together.
For `implement` work, keep a behavior change with its direct regression when later
cards depend on both; do not split tests merely because they live in another directory.

Return the parent item, proposed or accepted task IDs, dependencies, and each task's
output/scope/verification. Explain only material decomposition choices and unresolved
scope decisions. Before editing the roadmap, use the accepted planning workflow and
its focused integrity check.
