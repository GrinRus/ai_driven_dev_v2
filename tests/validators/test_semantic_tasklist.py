from __future__ import annotations

from pathlib import Path

from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _write_tasklist_document,
)

from aidd.validators.semantic import (
    INCOMPLETE_SECTION_CODE,
    validate_semantic_outputs,
)


def test_validate_semantic_outputs_accepts_valid_tasklist_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "tasklist-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_rejects_legacy_compact_tasklist_ids(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist_document(
        workspace_root,
        "WI-SEM-TASKLIST-COMPACT",
        (
            "# Tasklist\n\n"
            "## Task summary\n\n"
            "Decompose the importer fix into ordered, reviewable tasks "
            "with explicit verification coverage.\n\n"
            "## Ordered tasks\n\n"
            "### T1 - Confirm upstream issue shape\n\n"
            "- Dominant output artifact: issue cross-check notes.\n"
            "- Dependencies: none.\n"
            "- Verification note: issue text matches the reproduced assertion.\n\n"
            "### T2 - Add insert regression test\n\n"
            "- Dominant output artifact: `tests/test_cli_insert.py` regression.\n"
            "- Dependencies: `T1`.\n"
            "- Verification note: run `pytest tests/test_cli_insert.py -q`; "
            "this covers the default post-4.0a1 path without treating that "
            "version phrase as a task id.\n\n"
            "### T3 - Guard insert transform call\n\n"
            "- Dominant output artifact: one guard in `data_tool/cli.py`.\n"
            "- Dependencies: `T2`.\n"
            "- Verification note: run the insert regression plus happy-path CSV tests.\n\n"
            "## Dependencies\n\n"
            "- `T1`: none.\n"
            "- `T1 -> T2`: T2 locks the regression contract after issue confirmation.\n"
            "- `T2 -> T3`: T3 applies the guard only after the failing test exists.\n\n"
            "## Verification notes\n\n"
            "- `T1`: recorded issue cross-check evidence.\n"
            "- `T2`: `pytest tests/test_cli_insert.py -q` fails before the guard and "
            "passes after it.\n"
            "- `T3`: `pytest tests/test_cli_insert.py -q` and existing CSV happy-path "
            "tests pass.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-COMPACT",
        workspace_root=workspace_root,
    )

    assert findings
    assert any("missing required field" in finding.message for finding in findings)


def test_validate_semantic_outputs_ignores_tradeoff_ids_when_tasklist_uses_tl_ids(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist_document(
        workspace_root,
        "WI-SEM-TASKLIST-TL",
        (
            "# Tasklist\n\n"
            "## Task summary\n\n"
            "Decompose the importer fix into ordered, reviewable tasks "
            "while retaining references to plan trade-offs T1 and T2 as context.\n\n"
            "## Ordered tasks\n\n"
            "### TL-1 - Add regression tests\n\n"
            "- Dominant output artifact: `tests/test_cli.py` regression.\n"
            "- Dependencies: none.\n"
            "- Verification note: fails before the guard.\n\n"
            "### TL-2 - Apply guard\n\n"
            "- Dominant output artifact: one guard in `data_tool/cli.py`.\n"
            "- Dependencies: `TL-1`.\n"
            "- Verification note: covers trade-off T1 and rejected option T2.\n\n"
            "### TL-3 - Run full suite\n\n"
            "- Dominant output artifact: pytest output.\n"
            "- Dependencies: `TL-2`.\n"
            "- Verification note: records trade-off T3 as non-blocking context.\n\n"
            "## Dependencies\n\n"
            "- `TL-1`: none.\n"
            "- `TL-2`: depends on `TL-1`.\n"
            "- `TL-3`: depends on `TL-2`.\n\n"
            "## Verification notes\n\n"
            "- `TL-1`: targeted regression fails before the patch.\n"
            "- `TL-2`: targeted regression passes after the patch; plan trade-off T1 "
            "is still cited as rationale.\n"
            "- `TL-3`: full suite passes and documents trade-off T3 scope handling.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-TL",
        workspace_root=workspace_root,
    )

    assert findings
    assert any("missing required field" in finding.message for finding in findings)


def test_validate_semantic_outputs_ignores_review_and_acceptance_ids_when_tasklist_uses_t_ids(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_tasklist_document(
        workspace_root,
        "WI-SEM-TASKLIST-T",
        (
            "# Tasklist\n\n"
            "## Task summary\n\n"
            "Decompose the importer fix into compact T-prefixed tasks while "
            "preserving review condition ids RC-1 and RC-2 plus AC-3 as context.\n\n"
            "## Ordered tasks\n\n"
            "### T1 - Pre-write reproduction\n\n"
            "- Dominant output artifact: RC-1 scratch reproduction notes.\n"
            "- Dependencies: none.\n"
            "- Verification note: confirms whether AC-3 can be exercised safely.\n\n"
            "### T2 - Add regression test\n\n"
            "- Dominant output artifact: one pytest function covering RC-2.\n"
            "- Dependencies: `T1`.\n"
            "- Verification note: fails before the guard and includes stderr coverage.\n\n"
            "### T3 - Apply guard\n\n"
            "- Dominant output artifact: one guard in `data_tool/cli.py`.\n"
            "- Dependencies: `T2`.\n"
            "- Verification note: passes the regression and keeps RC-1 satisfied.\n\n"
            "## Dependencies\n\n"
            "- `T1`: none; implements review condition `RC-1`.\n"
            "- `T2`: depends on `T1`; covers `AC-3` and `RC-2`.\n"
            "- `T3`: depends on `T2`; keeps `RC-1` from widening scope.\n\n"
            "## Verification notes\n\n"
            "- `T1`: scratch reproduction records the `RC-1` branch outcome.\n"
            "- `T2`: targeted pytest fails before the guard and satisfies `AC-3`.\n"
            "- `T3`: targeted pytest passes after the guard; `RC-2` stderr assertion remains.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-T",
        workspace_root=workspace_root,
    )

    assert findings
    assert any("missing required field" in finding.message for finding in findings)


def test_validate_semantic_outputs_preserves_mixed_id_and_missing_coverage_findings(
    tmp_path: Path,
) -> None:
    cards = (
        """### TL-1 — Add regression coverage

- Outcome: The regression is reproducible.
- Dominant deliverable: `tests/test_example.py` records the failure.
- In scope: `tests/test_example.py`.
- Acceptance criteria:
  - TL-1-AC1: The regression fails before the fix.
""",
        """### T2 — Apply the bounded fix

- Outcome: The reproduced regression passes.
- Dominant deliverable: `src/example.py` contains the fix.
- In scope: `src/example.py`.
- Acceptance criteria:
  - T2-AC1: The regression passes after the fix.
""",
    )
    expected_messages = {
        "Task cards must not mix compact and prefixed task id styles.",
        "Section `Dependencies` is missing task ids: T2.",
        "Section `Verification notes` is missing task ids: T2.",
    }

    for index, ordered_cards in enumerate((cards, tuple(reversed(cards))), start=1):
        workspace_root = tmp_path / f"case-{index}" / ".aidd"
        work_item = f"WI-SEM-TASKLIST-MIXED-{index}"
        _write_tasklist_document(
            workspace_root,
            work_item,
            (
                "# Tasklist\n\n"
                "## Task summary\n\n"
                "Split the regression into two bounded implementation tasks.\n\n"
                "## Ordered tasks\n\n"
                + "\n".join(ordered_cards)
                + "\n"
                "## Dependencies\n\n"
                "- TL-1: none\n\n"
                "## Verification notes\n\n"
                "- TL-1: `pytest tests/test_example.py -q`\n"
            ),
        )

        findings = validate_semantic_outputs(
            stage="tasklist",
            work_item=work_item,
            workspace_root=workspace_root,
        )

        matched = tuple(finding for finding in findings if finding.message in expected_messages)
        assert {finding.message for finding in matched} == expected_messages
        assert all(finding.code == INCOMPLETE_SECTION_CODE for finding in matched)


def test_validate_semantic_outputs_flags_invalid_tasklist_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "tasklist-invalid" / "workspace"

    findings = validate_semantic_outputs(
        stage="tasklist",
        work_item="WI-SEM-TASKLIST-INVALID",
        workspace_root=workspace_root,
    )

    messages = {finding.message for finding in findings}
    assert (
        "Section `Task summary` is too brief to explain decomposition scope and "
        "sequencing intent."
    ) in messages
    assert "`Ordered tasks` must contain H3 task cards with stable task ids." in messages

