from __future__ import annotations

from pathlib import Path

import pytest

from aidd.validators.document_loader import (
    DocumentLoadError,
    DocumentPathError,
    MarkdownReadFailure,
    MarkdownReadProbeResult,
    classify_document_type,
    load_markdown_document,
    probe_markdown_document,
)
from aidd.validators.protocol import DocumentReadFailureKind


@pytest.mark.parametrize("path_kind", ("absolute", "parent-traversal", "symlink"))
def test_markdown_reads_reject_workspace_escape_without_changing_outside_bytes(
    tmp_path: Path, path_kind: str
) -> None:
    workspace_root = tmp_path / ".aidd"
    workspace_root.mkdir()
    outside_path = tmp_path / "outside.md"
    original = b"# Outside\n\nPrivate source bytes.\n"
    outside_path.write_bytes(original)
    if path_kind == "absolute":
        candidate = outside_path
    elif path_kind == "parent-traversal":
        candidate = workspace_root / ".." / outside_path.name
    else:
        candidate = workspace_root / "linked.md"
        candidate.symlink_to(outside_path)

    with pytest.raises(DocumentPathError, match="must stay inside workspace"):
        load_markdown_document(path=candidate, workspace_root=workspace_root)

    probe = probe_markdown_document(path=candidate, workspace_root=workspace_root)

    assert not probe.readable
    assert probe.document is None
    assert probe.failure is not None
    assert probe.failure.kind is DocumentReadFailureKind.UNREADABLE
    assert probe.failure.code == "STRUCT-DOCUMENT-UNREADABLE"
    assert "must stay inside workspace" in probe.failure.message
    assert outside_path.read_bytes() == original


def test_load_markdown_document_returns_raw_body_and_metadata(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    doc_path.parent.mkdir(parents=True)

    body = "# Plan\n\n- item\n"
    doc_path.write_text(body, encoding="utf-8")

    loaded = load_markdown_document(path=doc_path, workspace_root=workspace_root)

    assert loaded.body == body
    assert loaded.metadata.path == doc_path.resolve()
    assert loaded.metadata.workspace_relative_path == Path(
        "workitems/WI-001/stages/plan/output/plan.md"
    )
    assert loaded.metadata.document_type == "stage-output"
    assert loaded.metadata.size_bytes == len(body.encode("utf-8"))
    assert loaded.metadata.modified_time_epoch_s > 0


def test_load_markdown_document_rejects_non_markdown_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.txt"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_text("not markdown", encoding="utf-8")

    with pytest.raises(DocumentPathError, match="Expected a Markdown file"):
        load_markdown_document(path=doc_path, workspace_root=workspace_root)


def test_load_markdown_document_rejects_missing_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"

    with pytest.raises(DocumentLoadError, match="does not exist"):
        load_markdown_document(path=doc_path, workspace_root=workspace_root)


def test_load_markdown_document_parses_optional_frontmatter(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    doc_path.parent.mkdir(parents=True)
    body = "---\ndoc_kind: aidd.plan\nstage: plan\n---\n# Plan\n\nBody.\n"
    doc_path.write_text(body, encoding="utf-8")

    loaded = load_markdown_document(path=doc_path, workspace_root=workspace_root)

    assert loaded.frontmatter == {"doc_kind": "aidd.plan", "stage": "plan"}
    assert loaded.body == body


def test_load_markdown_document_keeps_frontmatter_optional(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_text("# Plan\n\nNo frontmatter.\n", encoding="utf-8")

    loaded = load_markdown_document(path=doc_path, workspace_root=workspace_root)

    assert loaded.frontmatter is None


def test_load_markdown_document_rejects_unclosed_frontmatter(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_text("---\ndoc_kind: aidd.plan\nstage: plan\n# Plan\n", encoding="utf-8")

    with pytest.raises(DocumentLoadError, match="closing '---' delimiter"):
        load_markdown_document(path=doc_path, workspace_root=workspace_root)


def test_probe_markdown_document_returns_readable_document(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_text("# Plan\n", encoding="utf-8")

    result = probe_markdown_document(path=doc_path, workspace_root=workspace_root)

    assert result.readable
    assert result.document is not None
    assert result.failure is None


@pytest.mark.parametrize(
    ("content", "kind", "code"),
    [
        ("missing", DocumentReadFailureKind.UNREADABLE, "STRUCT-DOCUMENT-UNREADABLE"),
        ("directory", DocumentReadFailureKind.NON_FILE, "STRUCT-DOCUMENT-NON-FILE"),
        (b"# Plan\n\xff", DocumentReadFailureKind.INVALID_UTF8, "STRUCT-DOCUMENT-INVALID-UTF8"),
        (
            "---\nmalformed\n",
            DocumentReadFailureKind.MALFORMED_FRONTMATTER,
            "STRUCT-DOCUMENT-MALFORMED-FRONTMATTER",
        ),
    ],
)
def test_probe_markdown_document_returns_typed_failure_matrix(
    tmp_path: Path,
    content: str | bytes,
    kind: DocumentReadFailureKind,
    code: str,
) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    doc_path.parent.mkdir(parents=True)
    if content == "missing":
        assert not doc_path.exists()
    elif content == "directory":
        doc_path.mkdir()
    elif isinstance(content, bytes):
        doc_path.write_bytes(content)
    else:
        doc_path.write_text(content, encoding="utf-8")

    result = probe_markdown_document(path=doc_path, workspace_root=workspace_root)

    assert not result.readable
    assert result.document is None
    assert result.failure is not None
    assert result.failure.kind is kind
    assert result.failure.code == code
    assert result.failure.message


def test_probe_markdown_document_normalizes_os_read_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace_root = tmp_path / ".aidd"
    doc_path = workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    doc_path.parent.mkdir(parents=True)
    doc_path.write_text("# Plan\n", encoding="utf-8")

    def raise_permission_error(*_args: object, **_kwargs: object) -> str:
        raise PermissionError("permission denied")

    monkeypatch.setattr(Path, "read_text", raise_permission_error)
    result = probe_markdown_document(path=doc_path, workspace_root=workspace_root)

    assert result.document is None
    assert result.failure is not None
    assert result.failure.kind is DocumentReadFailureKind.UNREADABLE
    assert result.failure.code == "STRUCT-DOCUMENT-UNREADABLE"
    assert result.failure.message == "permission denied"


def test_markdown_read_probe_result_rejects_ambiguous_outcomes(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="exactly one outcome"):
        MarkdownReadProbeResult(path=tmp_path / "plan.md")
    with pytest.raises(ValueError, match="exactly one outcome"):
        MarkdownReadProbeResult(
            path=tmp_path / "plan.md",
            document=object(),  # type: ignore[arg-type]
            failure=MarkdownReadFailure(
                kind=DocumentReadFailureKind.UNREADABLE,
                message="read failed",
            ),
        )


def test_load_markdown_document_normalizes_workspace_relative_path(tmp_path: Path) -> None:
    workspace_root = tmp_path / ".aidd"
    canonical_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "plan.md"
    )
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text("# Plan\n", encoding="utf-8")

    aliased_path = (
        workspace_root / "workitems" / "WI-001" / "stages" / "plan" / "output" / "." / "plan.md"
    )
    loaded = load_markdown_document(path=aliased_path, workspace_root=workspace_root)

    assert loaded.metadata.workspace_relative_path == Path(
        "workitems/WI-001/stages/plan/output/plan.md"
    )


def test_classify_document_type_detects_common_document() -> None:
    path = Path("workitems/WI-001/stages/plan/stage-result.md")
    assert classify_document_type(path) == "common:stage-result"


def test_classify_document_type_detects_stage_input_document() -> None:
    path = Path("workitems/WI-001/stages/plan/input/research-notes.md")
    assert classify_document_type(path) == "stage-input"


def test_classify_document_type_returns_unknown_for_non_stage_path() -> None:
    path = Path("reports/evals/run-001/validator-report.md")
    assert classify_document_type(path) == "unknown"
