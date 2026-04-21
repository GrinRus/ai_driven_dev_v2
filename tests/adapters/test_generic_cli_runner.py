from __future__ import annotations

from pathlib import Path

import pytest

from aidd.adapters.generic_cli.runner import (
    GenericCliStageContext,
    assemble_command,
    command_preview,
)


def _context() -> GenericCliStageContext:
    return GenericCliStageContext(
        stage="plan",
        work_item="WI-001",
        run_id="run-001",
        prompt_pack_path=Path("prompt-packs/stages/plan/system.md"),
    )


def test_assemble_command_appends_stage_context_and_prompt_pack() -> None:
    command = assemble_command(
        configured_command="python -m generic_runtime",
        context=_context(),
    )

    assert command == (
        "python",
        "-m",
        "generic_runtime",
        "--stage",
        "plan",
        "--work-item",
        "WI-001",
        "--run-id",
        "run-001",
        "--prompt-pack",
        "prompt-packs/stages/plan/system.md",
    )


def test_assemble_command_respects_shell_quoted_base_tokens() -> None:
    command = assemble_command(
        configured_command='runtime --profile "fast lane"',
        context=_context(),
    )

    assert command[:3] == ("runtime", "--profile", "fast lane")


def test_assemble_command_rejects_empty_configured_command() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        assemble_command(configured_command="   ", context=_context())


def test_assemble_command_rejects_invalid_shell_syntax() -> None:
    with pytest.raises(ValueError, match="not valid shell syntax"):
        assemble_command(configured_command='"unterminated', context=_context())


def test_command_preview_renders_shell_escaped_output() -> None:
    preview = command_preview(
        configured_command='runtime --profile "fast lane"',
        context=_context(),
    )

    assert preview.startswith("runtime --profile 'fast lane'")
    assert "--prompt-pack prompt-packs/stages/plan/system.md" in preview
