# Interview prompt for `review-spec`

If the stage cannot proceed responsibly without user clarification:

1. ask concise questions,
2. prefer the smallest number of decisive questions,
3. assign stable ids (`Q1`, `Q2`, ...) and mark each question as `[blocking]` or `[non-blocking]` in `questions.md`,
4. use `[blocking]` when contradictory constraints or missing baseline assumptions block a reliable sign-off decision,
5. use `[non-blocking]` only when review can proceed with explicit bounded assumptions,
6. wait for or incorporate `answers.md`, and treat blocking items as resolved only with matching `[resolved]` answers.

Prioritize questions about:

- contradictory constraints that change readiness outcome,
- missing baseline assumptions required for risk interpretation,
- missing decision authority or acceptance policy for sign-off.

Do not ask questions that can be resolved from the provided documents.
