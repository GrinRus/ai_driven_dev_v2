# Operator intervention prompt

You are rerunning the current AIDD stage because the operator submitted a stage-scoped change request.

Use the operator request as the primary delta to apply. Keep the existing valid sections and stable ids unless the request specifically requires changing them.

Intervention rules:

- change only artifacts owned by the current stage contract;
- do not rewrite a whole document when a narrow patch resolves the request;
- preserve valid sections, evidence, question ids, and attempt history when still accurate;
- do not create or edit `repair-brief.md`;
- treat any model-authored `validator-report.md` as draft-only until AIDD runs post-runtime validation;
- update `stage-result.md` truthfully with this intervention attempt and the resulting state;
- keep unresolved blocking questions explicit instead of inventing answers;
- if the request cannot be safely completed within the current stage scope, record the blocker in `stage-result.md` and questions when needed.
