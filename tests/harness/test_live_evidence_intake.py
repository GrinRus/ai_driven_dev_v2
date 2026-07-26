from __future__ import annotations

import os
from pathlib import Path

import pytest

from aidd.harness.live_evidence_intake import (
    LiveEvidenceIntakeError,
    intake_live_evidence,
    validate_live_evidence_publication,
)


def _roots(tmp_path: Path) -> tuple[Path, Path]:
    authorized = tmp_path / "provider-a" / "browser"
    destination = tmp_path / "bundle" / "manual-frontend-evidence"
    authorized.mkdir(parents=True)
    destination.parent.mkdir()
    return authorized, destination


def test_intake_live_evidence_publishes_contained_directory_atomically(
    tmp_path: Path,
) -> None:
    authorized, destination = _roots(tmp_path)
    source = authorized / "run-1"
    (source / "screenshots").mkdir(parents=True)
    (source / "notes.md").write_text("browser notes\n", encoding="utf-8")
    (source / "screenshots" / "mobile.png").write_bytes(b"png")

    result = intake_live_evidence(
        source=source,
        authorized_root=authorized,
        destination_root=destination,
    )

    assert result.source_kind == "directory"
    assert [item.relative_path for item in result.files] == [
        "notes.md",
        "screenshots/mobile.png",
    ]
    assert result.total_size_bytes == len(b"browser notes\n") + len(b"png")
    assert len(result.tree_sha256) == 64
    assert (destination / "notes.md").read_text(encoding="utf-8") == "browser notes\n"
    assert (destination / "screenshots" / "mobile.png").read_bytes() == b"png"
    assert not list(destination.parent.glob(".manual-frontend-evidence.staging-*"))


def test_intake_live_evidence_publishes_contained_file(tmp_path: Path) -> None:
    authorized, destination = _roots(tmp_path)
    source = authorized / "browser-notes.md"
    source.write_text("notes\n", encoding="utf-8")

    result = intake_live_evidence(
        source=source,
        authorized_root=authorized,
        destination_root=destination,
    )

    assert result.source_kind == "file"
    assert [item.relative_path for item in result.files] == ["browser-notes.md"]
    assert (destination / "browser-notes.md").read_text(encoding="utf-8") == "notes\n"


@pytest.mark.parametrize("escape_kind", ("sibling", "absolute", "traversal"))
def test_intake_live_evidence_rejects_escape(
    tmp_path: Path,
    escape_kind: str,
) -> None:
    authorized, destination = _roots(tmp_path)
    sibling = tmp_path / "provider-b" / "browser"
    sibling.mkdir(parents=True)
    (sibling / "notes.md").write_text("foreign\n", encoding="utf-8")
    source = sibling
    if escape_kind == "absolute":
        source = Path("/tmp/aidd-live-evidence-escape")
    elif escape_kind == "traversal":
        source = authorized / ".." / ".." / "provider-b" / "browser"

    with pytest.raises(LiveEvidenceIntakeError, match="authorized browser root"):
        intake_live_evidence(
            source=source,
            authorized_root=authorized,
            destination_root=destination,
        )

    assert not destination.exists()
    assert not list(destination.parent.glob(".manual-frontend-evidence.staging-*"))


@pytest.mark.parametrize("symlink_level", ("root", "directory", "file"))
def test_intake_live_evidence_rejects_symlink_at_every_level(
    tmp_path: Path,
    symlink_level: str,
) -> None:
    authorized, destination = _roots(tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    (real / "notes.md").write_text("notes\n", encoding="utf-8")
    if symlink_level == "root":
        authorized.rmdir()
        authorized.symlink_to(real, target_is_directory=True)
        source = authorized
    elif symlink_level == "directory":
        linked = authorized / "linked"
        linked.symlink_to(real, target_is_directory=True)
        source = linked
    else:
        source = authorized / "notes.md"
        source.symlink_to(real / "notes.md")

    with pytest.raises(LiveEvidenceIntakeError, match="symlink"):
        intake_live_evidence(
            source=source,
            authorized_root=authorized,
            destination_root=destination,
        )

    assert not destination.exists()


def test_intake_live_evidence_rejects_hard_link(tmp_path: Path) -> None:
    authorized, destination = _roots(tmp_path)
    source = authorized / "run-1"
    source.mkdir()
    original = source / "notes.md"
    original.write_text("notes\n", encoding="utf-8")
    os.link(original, source / "duplicate.md")

    with pytest.raises(LiveEvidenceIntakeError, match="hard linked"):
        intake_live_evidence(
            source=source,
            authorized_root=authorized,
            destination_root=destination,
        )

    assert not destination.exists()


def test_intake_live_evidence_cleans_staging_after_copy_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authorized, destination = _roots(tmp_path)
    source = authorized / "run-1"
    source.mkdir()
    (source / "notes.md").write_text("notes\n", encoding="utf-8")

    def fail_copy(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise LiveEvidenceIntakeError("injected copy failure")

    monkeypatch.setattr(
        "aidd.harness.live_evidence_intake._copy_regular_file",
        fail_copy,
    )

    with pytest.raises(LiveEvidenceIntakeError, match="injected copy failure"):
        intake_live_evidence(
            source=source,
            authorized_root=authorized,
            destination_root=destination,
        )

    assert not destination.exists()
    assert not list(destination.parent.glob(".manual-frontend-evidence.staging-*"))


def test_published_evidence_digest_detects_later_mutation(tmp_path: Path) -> None:
    authorized, destination = _roots(tmp_path)
    source = authorized / "notes.md"
    source.write_text("original\n", encoding="utf-8")
    result = intake_live_evidence(
        source=source,
        authorized_root=authorized,
        destination_root=destination,
    )
    (destination / "notes.md").write_text("mutated\n", encoding="utf-8")

    with pytest.raises(LiveEvidenceIntakeError, match="inventory changed"):
        validate_live_evidence_publication(
            published_root=result.published_root,
            expected_directories=result.directories,
            expected_files=result.files,
            expected_tree_sha256=result.tree_sha256,
        )
