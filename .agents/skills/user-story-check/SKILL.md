---
name: user-story-check
description: Check a proposed AIDD workflow, runtime, distribution, evaluation, or operator UX change against product scope and user-story acceptance signals.
---

# user-story-check

Read the relevant stories in [user-stories.md](../../../docs/product/user-stories.md)
and the accepted change's parent slice. Identify the operator/maintainer outcome,
which acceptance signals it supports or threatens, and whether it adds product scope
or changes implementation only. Include task execution and project ownership when
cross-stage, frontend, or multi-project behavior is affected.

For analysis or review, return the mismatch and needed document changes without
implementing them. When implementation is already authorized, update product docs only
if scope or acceptance behavior changed; retain unrelated stories and historical evidence.
Do not convert an implementation limitation into a weaker product requirement merely
because a test failed.

Report impacted story IDs, the observable acceptance signal, whether documentation
must change, and any unresolved scope decision. Use
[the development map](../../../docs/agent-development.md) to locate checks for the
actual behavior rather than adding a prose-only test for every wording change.
