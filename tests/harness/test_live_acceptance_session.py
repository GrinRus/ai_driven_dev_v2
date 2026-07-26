from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from aidd.harness.live_acceptance_isolation import (
    LiveAcceptanceIsolationCapability,
    LiveAcceptanceIsolationError,
)
from aidd.harness.live_acceptance_session import (
    SESSION_INTEGRITY_FILENAME,
    LiveAcceptanceSession,
    LiveAcceptanceSessionError,
    capture_source_integrity,
)


@pytest.fixture(autouse=True)
def _isolation_capability(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_session."
        "require_live_acceptance_isolation_capability",
        lambda: LiveAcceptanceIsolationCapability(
            backend="macos-seatbelt",
            supported=True,
            detail="fixture capability",
        ),
    )


def _git(repository: Path, *args: str) -> None:
    subprocess.run(
        ("git", *args),
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )


def _source_checkout(tmp_path: Path) -> Path:
    source = tmp_path / "source"
    source.mkdir()
    (source / "tracked.txt").write_text("tracked baseline\n", encoding="utf-8")
    _git(source, "init")
    _git(source, "config", "user.email", "fixture@example.test")
    _git(source, "config", "user.name", "Fixture")
    _git(source, "add", "tracked.txt")
    _git(source, "commit", "-m", "fixture")
    return source


def _roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    source = _source_checkout(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    return source, external, external / "provider"


def test_session_preserves_source_and_publishes_cleanup_evidence(
    tmp_path: Path,
) -> None:
    source, external, provider = _roots(tmp_path)
    user_file = source / "user-notes.md"
    user_file.write_text("keep me\n", encoding="utf-8")
    baseline = capture_source_integrity(source)

    with LiveAcceptanceSession(
        source_checkout=source,
        external_root=external,
        provider_root=provider,
    ) as session:
        (provider / "work").mkdir()
        session.record_process_exit(0)

    assert session.result is not None
    assert session.result.status == "pass"
    assert session.result.source_baseline == baseline
    assert session.result.source_postflight == baseline
    assert session.result.process_exit_code == 0
    assert session.result.cleanup["sentinel_removed"] is True
    assert user_file.read_text(encoding="utf-8") == "keep me\n"
    payload = json.loads(
        (provider / SESSION_INTEGRITY_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["status"] == "pass"
    assert payload["violations"] == []
    assert not (provider / ".live-acceptance-session-active").exists()


def test_dirty_tracked_source_fails_before_provider_allocation(tmp_path: Path) -> None:
    source, external, provider = _roots(tmp_path)
    (source / "tracked.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(LiveAcceptanceSessionError, match="clean tracked source"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            pytest.fail("session body must not run")

    assert not provider.exists()


def test_capability_failure_does_not_allocate_provider_layout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, external, provider = _roots(tmp_path)

    def _unsupported() -> LiveAcceptanceIsolationCapability:
        raise LiveAcceptanceIsolationError("backend unavailable")

    monkeypatch.setattr(
        "aidd.harness.live_acceptance_session."
        "require_live_acceptance_isolation_capability",
        _unsupported,
    )

    with pytest.raises(LiveAcceptanceSessionError, match="backend unavailable"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            pytest.fail("session body must not run")

    assert not provider.exists()


def test_new_source_file_invalidates_session(tmp_path: Path) -> None:
    source, external, provider = _roots(tmp_path)

    with pytest.raises(LiveAcceptanceSessionError, match="untracked file set changed"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            (source / "injected-harness-payload.txt").write_text(
                "unexpected\n",
                encoding="utf-8",
            )

    payload = json.loads(
        (provider / SESSION_INTEGRITY_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["status"] == "fail"
    assert "source untracked file set changed" in payload["violations"]


def test_changed_tracked_bytes_invalidate_session(tmp_path: Path) -> None:
    source, external, provider = _roots(tmp_path)

    with pytest.raises(LiveAcceptanceSessionError, match="tracked bytes changed"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            (source / "tracked.txt").write_text("mutated\n", encoding="utf-8")

    payload = json.loads(
        (provider / SESSION_INTEGRITY_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["status"] == "fail"
    assert "source tracked bytes changed" in payload["violations"]


def test_changed_existing_untracked_bytes_invalidate_session(tmp_path: Path) -> None:
    source, external, provider = _roots(tmp_path)
    user_file = source / "user-notes.md"
    user_file.write_text("baseline\n", encoding="utf-8")

    with pytest.raises(LiveAcceptanceSessionError, match="untracked bytes changed"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            user_file.write_text("mutated\n", encoding="utf-8")


def test_preexisting_target_contamination_blocks_fresh_session(
    tmp_path: Path,
) -> None:
    source, external, provider = _roots(tmp_path)
    (provider / "work").mkdir(parents=True)
    (provider / "work" / "unexpected.txt").write_text(
        "contamination\n",
        encoding="utf-8",
    )

    with pytest.raises(LiveAcceptanceSessionError, match="already allocated or contaminated"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            pytest.fail("session body must not run")

    assert not (provider / ".live-acceptance-session-active").exists()
    assert not (provider / SESSION_INTEGRITY_FILENAME).exists()


def test_explicit_resume_allows_existing_canonical_provider_root(
    tmp_path: Path,
) -> None:
    source, external, provider = _roots(tmp_path)
    (provider / "work").mkdir(parents=True)

    with LiveAcceptanceSession(
        source_checkout=source,
        external_root=external,
        provider_root=provider,
        allow_existing_provider=True,
    ) as session:
        session.record_process_exit(0)

    assert session.result is not None
    assert session.result.target_baseline.provider_root_existed is True
    assert session.result.target_baseline.expected_root_presence["work"] is True


def test_provider_overlap_fails_before_layout_allocation(tmp_path: Path) -> None:
    source = _source_checkout(tmp_path)
    external = source / "external"
    external.mkdir()
    provider = external / "provider"

    with pytest.raises(LiveAcceptanceSessionError, match="must not overlap"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            pytest.fail("session body must not run")

    assert not provider.exists()


def test_target_root_symlink_invalidates_postflight(tmp_path: Path) -> None:
    source, external, provider = _roots(tmp_path)
    outside = tmp_path / "outside-target"
    outside.mkdir()

    with pytest.raises(LiveAcceptanceSessionError, match="became a symlink"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            (provider / "work").symlink_to(outside, target_is_directory=True)

    payload = json.loads(
        (provider / SESSION_INTEGRITY_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["status"] == "fail"
    assert payload["cleanup"]["sentinel_removed"] is True
    assert payload["target_postflight"]["expected_roots"]["work"] == {
        "contained": False,
        "exists": True,
        "is_symlink": True,
        "path": (provider / "work").as_posix(),
    }


def test_cleanup_failure_invalidates_session_and_is_recorded(tmp_path: Path) -> None:
    source, external, provider = _roots(tmp_path)

    with pytest.raises(LiveAcceptanceSessionError, match="sentinel was not removed"):
        with LiveAcceptanceSession(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
        ):
            (provider / ".live-acceptance-session-active").unlink()

    payload = json.loads(
        (provider / SESSION_INTEGRITY_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["status"] == "fail"
    assert payload["cleanup"]["sentinel_removed"] is False
    assert payload["cleanup"]["errors"]
    assert "session cleanup sentinel was not removed" in payload["violations"]
