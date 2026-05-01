from __future__ import annotations

from pathlib import Path


def resolve_stage_brief_path_for_native_prompt(
    *,
    stage_brief_path: Path,
    workspace_root: Path,
) -> Path:
    if stage_brief_path.is_absolute():
        return stage_brief_path.resolve(strict=False)
    return (workspace_root / stage_brief_path).resolve(strict=False)


def resolve_prompt_pack_paths_for_native_prompt(
    *,
    prompt_pack_paths: tuple[Path, ...],
    repository_root: Path | None,
) -> tuple[Path, ...]:
    base_dir = (repository_root or Path.cwd()).resolve(strict=False)
    resolved: list[Path] = []
    for prompt_path in prompt_pack_paths:
        if prompt_path.is_absolute():
            resolved.append(prompt_path.resolve(strict=False))
            continue
        resolved.append((base_dir / prompt_path).resolve(strict=False))
    return tuple(resolved)


def _resolve_workspace_path(
    *,
    path: Path,
    workspace_root: Path,
) -> Path:
    if path.is_absolute():
        return path.resolve(strict=False)
    return (workspace_root / path).resolve(strict=False)


def _read_text_for_prompt(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"[missing file: {path.as_posix()}]\n"


def build_native_prompt_text(
    *,
    runtime_id: str,
    stage: str,
    work_item: str,
    run_id: str,
    workspace_root: Path,
    stage_brief_path: Path,
    prompt_pack_paths: tuple[Path, ...],
    repository_root: Path | None,
    attempt_number: int,
    repair_mode: bool,
    input_bundle_path: Path | None = None,
    repair_brief_path: Path | None = None,
    repair_context_markdown: str | None = None,
) -> str:
    if attempt_number < 1:
        raise ValueError("Native prompt attempt_number must be greater than zero.")

    resolved_workspace_root = workspace_root.resolve(strict=False)
    resolved_stage_brief_path = resolve_stage_brief_path_for_native_prompt(
        stage_brief_path=stage_brief_path,
        workspace_root=resolved_workspace_root,
    )
    resolved_prompt_pack_paths = resolve_prompt_pack_paths_for_native_prompt(
        prompt_pack_paths=prompt_pack_paths,
        repository_root=repository_root,
    )
    resolved_input_bundle_path = (
        _resolve_workspace_path(path=input_bundle_path, workspace_root=resolved_workspace_root)
        if input_bundle_path is not None
        else None
    )
    resolved_repair_brief_path = (
        _resolve_workspace_path(path=repair_brief_path, workspace_root=resolved_workspace_root)
        if repair_brief_path is not None
        else None
    )
    mode_label = "repair" if repair_mode else "initial"

    lines: list[str] = [
        "# AIDD stage runtime request",
        "",
        f"- Runtime: {runtime_id}",
        f"- Stage: {stage}",
        f"- Work item: {work_item}",
        f"- Run id: {run_id}",
        f"- Attempt: {attempt_number}",
        f"- Attempt mode: {mode_label}",
        f"- Workspace root: {resolved_workspace_root.as_posix()}",
        f"- Stage brief: {resolved_stage_brief_path.as_posix()}",
    ]
    if resolved_input_bundle_path is not None:
        lines.append(f"- Input bundle: {resolved_input_bundle_path.as_posix()}")
    if resolved_repair_brief_path is not None:
        lines.append(f"- Repair brief: {resolved_repair_brief_path.as_posix()}")

    lines.extend(
        (
            "",
            "## Stage brief",
            "",
            _read_text_for_prompt(resolved_stage_brief_path).rstrip(),
        )
    )
    if resolved_input_bundle_path is not None:
        lines.extend(
            (
                "",
                "## Input bundle",
                "",
                _read_text_for_prompt(resolved_input_bundle_path).rstrip(),
            )
        )
    if repair_context_markdown is not None and repair_context_markdown.strip():
        lines.extend(
            (
                "",
                "## Repair context",
                "",
                repair_context_markdown.strip(),
            )
        )
    for prompt_pack_path in resolved_prompt_pack_paths:
        lines.extend(
            (
                "",
                f"## Active prompt pack: {prompt_pack_path.as_posix()}",
                "",
                _read_text_for_prompt(prompt_pack_path).rstrip(),
            )
        )
    lines.extend(
        (
            "",
            "## Execution contract",
            "",
            "Use the workspace documents as the source of truth. Write the required "
            "stage output Markdown files under the AIDD workspace for this stage.",
            "",
            "`repair-brief.md` is AIDD-owned read-only repair control evidence. "
            "Read it when present, but do not rewrite it.",
            "",
            "Treat any existing model-authored `validator-report.md` as draft. "
            "AIDD post-runtime validation is the final truth source.",
            "",
            "Do not claim validator pass or stage success unless the artifacts you "
            "write resolve the active findings and remain internally consistent.",
            "",
        )
    )
    return "\n".join(lines)


__all__ = [
    "build_native_prompt_text",
    "resolve_prompt_pack_paths_for_native_prompt",
    "resolve_stage_brief_path_for_native_prompt",
]
