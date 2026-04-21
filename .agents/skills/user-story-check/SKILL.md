---
name: user-story-check
description: Check whether a proposed change still fits the main AIDD user stories and update product docs when scope changes.
---

# user-story-check

## Use when

- A change touches workflow semantics, distribution, adapter scope, eval scope, or operator UX.

## Procedure

1. Read `docs/product/user-stories.md`.
2. Identify which user stories the change supports, extends, or threatens.
3. Check whether the change adds new product scope or only implementation detail.
4. Update user stories only if product scope actually changed.
5. Call out any mismatch between the code plan and the documented product intent.

## Output

Return: impacted user stories, whether docs must change, and any scope mismatch.
