from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from aidd.cli.support import console
from aidd.core.workspace import WorkspaceBootstrapService


def init(
    work_item: Annotated[
        str,
        typer.Option("--work-item", help="Work item identifier, for example WI-001."),
    ] = "WI-001",
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    """Create a starter AIDD workspace for one work item."""
    bootstrap_service = WorkspaceBootstrapService(root=root)
    work_item_root = bootstrap_service.bootstrap_work_item(work_item=work_item)
    console.print(f"Initialized workspace: {work_item_root.resolve()}")
