# Operator intervention prompt

Apply the operator's stage-scoped change request as a narrow delta to the existing valid content.

- Write only runtime-content targets listed in `stage-brief.md`; preserve valid sections,
  evidence, and stable ids unless the request explicitly changes them.
- Do not write `stage-result.md` or `validator-report.md`; AIDD records this attempt, validates
  content, derives terminal status, and decides progression.
- Do not create or edit `repair-brief.md`, `answers.md`, or the submitted operator request.
- Keep unresolved blocking questions explicit through the controlled interview path. AIDD merges
  question candidates by stable QID; preserve operator answers and never invent a decision.
- If the request exceeds this stage's scope, record the concrete blocker in the runtime-authored
  content and surface a blocking question when an operator decision is needed.
- Stop after the requested content change; AIDD performs the canonical validation gate.
