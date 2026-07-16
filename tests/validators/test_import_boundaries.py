from __future__ import annotations

from importlib.util import find_spec

from aidd.core.task_plan import parse_task_plan
from aidd.validators import cross_document
from aidd.validators.semantic_rules import common
from aidd.validators.semantic_rules.ids import extract_tasklist_task_ids


def test_removed_validator_scaffolds_are_not_importable() -> None:
    assert find_spec("aidd.validators.documents") is None
    for name in (
        "CITATION_ID_PATTERN",
        "MILESTONE_ID_PATTERN",
        "STAGE_HEADING_REQUIREMENT_PATTERN",
        "TASKLIST_TASK_ID_PATTERN",
    ):
        assert not hasattr(common, name)


def test_canonical_tasklist_and_cross_document_surfaces_remain_available() -> None:
    assert callable(parse_task_plan)
    assert callable(extract_tasklist_task_ids)
    assert callable(cross_document.validate_cross_document_consistency)
