from __future__ import annotations

from pathlib import Path

from aidd.core.stages import STAGES


_PLACEHOLDERS: dict[str, str] = {
    "questions.md": "# Questions\n\nNo questions yet.\n",
    "answers.md": "# Answers\n\nNo answers yet.\n",
    "validator-report.md": "# Validator report\n\nNo validator output yet.\n",
    "repair-brief.md": "# Repair brief\n\nNo repair requested yet.\n",
    "stage-result.md": "# Stage result\n\nStage not run yet.\n",
}


def init_workspace(root: Path, work_item: str) -> Path:
    work_item_root = root / "workitems" / work_item
    (work_item_root / "context").mkdir(parents=True, exist_ok=True)

    for stage in STAGES:
        stage_root = work_item_root / "stages" / stage
        (stage_root / "input").mkdir(parents=True, exist_ok=True)
        (stage_root / "output").mkdir(parents=True, exist_ok=True)
        for filename, content in _PLACEHOLDERS.items():
            file_path = stage_root / filename
            if not file_path.exists():
                file_path.write_text(content, encoding="utf-8")

    return work_item_root
