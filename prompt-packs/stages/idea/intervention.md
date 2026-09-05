# Operator intervention prompt

You are rerunning the current AIDD stage because the operator submitted a stage-scoped change request.

Use the operator request as the primary delta to apply. Keep the existing valid sections and stable ids unless the request specifically requires changing them.

Intervention rules:

- for stage documents, change only `idea-brief.md`, the substantive output owned by the current stage contract;
- do not rewrite a whole document when a narrow patch resolves the request;
- preserve valid sections, evidence, question ids, and attempt history when still accurate;
- do not create or edit `repair-brief.md`;
- Do not write `stage-result.md` or `validator-report.md`; AIDD owns their canonical
  status, validation, history, and publication;
- Never create, edit, delete, or replace either record; if a finding names one, expose the needed
  correction in `idea-brief.md` and let AIDD reconcile the workflow record.
- record the intervention outcome truthfully in substantive runtime content for AIDD reconciliation;
- keep unresolved blocking questions explicit instead of inventing answers;
- if the request cannot be safely completed within the current stage scope, record the blocker in `idea-brief.md` and submit a `[blocking]` question through the controlled interview path. Substantive blocker prose alone does not pause AIDD.
