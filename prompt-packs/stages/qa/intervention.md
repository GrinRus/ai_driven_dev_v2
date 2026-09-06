# Operator intervention prompt

Apply the operator's stage-scoped change request as a narrow delta to the existing valid content.

- Write only runtime-content targets listed in `stage-brief.md`; preserve valid sections,
  evidence, and stable ids unless the request explicitly changes them.
- Do not write `stage-result.md` or `validator-report.md`; AIDD owns their canonical
  status, validation, history, and publication. Never create, edit, delete, or replace either record.
  Expose any needed correction in substantive content; AIDD derives terminal status and progression.
- Do not create or edit `repair-brief.md`, `answers.md`, or the submitted operator request.
- Keep unresolved blocking questions explicit through the controlled interview path. AIDD merges
  question candidates by stable QID; preserve operator answers and never invent a decision.
- If the request exceeds this stage's scope, record the concrete blocker in the runtime-authored
  content and submit a `[blocking]` question through the controlled interview path.
  Substantive blocker prose alone does not pause AIDD.
- Stop after the requested content change; AIDD performs the canonical validation gate.
