# Semantic validator fixtures

Fixtures for `tests/validators/test_semantic.py` regression coverage.

- `valid/workspace/` contains a bundle that should pass semantic checks for `idea`.
- `invalid/workspace/` contains a bundle with placeholder content that must fail semantic checks.
- `valid-list-format/workspace/` contains a bundle where `Constraints` and `Open questions`
  use bullet-list format and should pass stage-specific semantic checks.
- `invalid-list-format/workspace/` contains a bundle where `Constraints` uses paragraph text
  instead of bullet items and must fail stage-specific semantic checks.
- `research-valid/workspace/` contains a bundle that should pass `research` citation-link checks.
- `research-invalid-missing-source/workspace/` contains a bundle that references unknown citation ids
  and must fail `research` semantic checks.
- `research-invalid-unresolved-question/workspace/` contains a bundle with unresolved evidence in
  findings/evidence trace and must fail `research` semantic checks.
- `plan-valid/workspace/` contains a bundle that should pass `plan` semantic checks for milestone
  ids, risk mitigation notes, dependency lists, and verification-note mapping.
- `plan-invalid/workspace/` contains a bundle with weak risk mitigation, non-list dependencies, and
  missing milestone references in verification notes, and must fail `plan` semantic checks.
- `review-spec-valid/workspace/` contains a bundle that should pass `review-spec` semantic checks
  for issue severity/rationale, recommendation quality, and readiness/decision alignment.
- `review-spec-invalid/workspace/` contains a bundle with missing issue severity/rationale, a
  non-actionable recommendation summary, and inconsistent readiness/decision status, and must fail
  `review-spec` semantic checks.
