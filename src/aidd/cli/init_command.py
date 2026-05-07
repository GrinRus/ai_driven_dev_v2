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
    request: Annotated[
        str | None,
        typer.Option(
            "--request",
            help="Seed intake context with an operator request.",
        ),
    ] = None,
    request_file: Annotated[
        Path | None,
        typer.Option(
            "--request-file",
            help="Read operator request text from a file and seed intake context.",
        ),
    ] = None,
    force_context: Annotated[
        bool,
        typer.Option(
            "--force-context",
            help="Overwrite existing generated context docs when seeding a request.",
        ),
    ] = False,
    root: Annotated[
        Path,
        typer.Option("--root", help="Root AIDD storage directory."),
    ] = Path(".aidd"),
) -> None:
    """Create a starter AIDD workspace for one work item."""
    if request is not None and request_file is not None:
        raise typer.BadParameter("Use either --request or --request-file, not both.")

    request_text = request
    if request_file is not None:
        try:
            request_text = request_file.read_text(encoding="utf-8")
        except OSError as exc:
            raise typer.BadParameter(
                f"Could not read --request-file {request_file.as_posix()}: {exc}"
            ) from exc

    bootstrap_service = WorkspaceBootstrapService(root=root)
    work_item_root = bootstrap_service.bootstrap_work_item(work_item=work_item)
    console.print(f"Initialized workspace: {work_item_root.resolve()}")
    if request_text is None:
        console.print(
            "No intake context was seeded. Add context/intake.md or rerun "
            "with --request/--request-file before `aidd run`."
        )
        return

    try:
        seeded = bootstrap_service.seed_request_context(
            work_item=work_item,
            request_text=request_text,
            project_root=Path.cwd(),
            force=force_context,
        )
    except (FileExistsError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    action = "Updated" if seeded.overwritten else "Seeded"
    console.print(f"{action} request context:")
    for path in seeded.paths:
        console.print(f"- {path.resolve(strict=False).as_posix()}")
