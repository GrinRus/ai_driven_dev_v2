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
