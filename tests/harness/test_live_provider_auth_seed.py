from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from aidd.harness.live_provider_auth_seed import (
    MAX_PROVIDER_AUTH_SEED_BYTES,
    LiveProviderAuthSeedError,
    ProviderAuthSeedRequest,
    seed_provider_auth_state,
)


def _homes(tmp_path: Path) -> tuple[Path, Path]:
    operator_home = tmp_path / "operator-home"
    private_home = tmp_path / "external" / "provider" / "private-home"
    operator_home.mkdir()
    private_home.mkdir(parents=True)
    return operator_home, private_home


def _write_auth(operator_home: Path, runtime: str, content: bytes) -> Path:
    relative = Path(".codex/auth.json") if runtime == "codex" else Path(".claude.json")
    path = operator_home / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    # This writes only synthetic fixtures under pytest's private temporary directory.
    # codeql[py/clear-text-storage-sensitive-data]
    path.write_bytes(content)
    path.chmod(0o600)
    return path


@pytest.mark.parametrize(
    ("runtime", "relative_destination"),
    (
        ("codex", ".codex/auth.json"),
        ("claude-code", ".claude.json"),
    ),
)
def test_seed_provider_auth_state_copies_only_allowlisted_opaque_file(
    tmp_path: Path,
    runtime: str,
    relative_destination: str,
) -> None:
    operator_home, private_home = _homes(tmp_path)
    secret = b'{"opaque":"credential-secret"}\n'
    _write_auth(operator_home, runtime, secret)
    (operator_home / ".history").write_text("must-not-copy\n", encoding="utf-8")

    result = seed_provider_auth_state(
        ProviderAuthSeedRequest(
            runtime=runtime,
            operator_home=operator_home,
            provider_private_home=private_home,
        )
    )

    destination = private_home / relative_destination
    assert result.runtime == runtime
    assert result.relative_destination == relative_destination
    assert result.size_bytes == len(secret)
    assert result.status == "seeded"
    assert destination.read_bytes() == secret
    assert stat.S_IMODE(private_home.stat().st_mode) == 0o700
    assert stat.S_IMODE(destination.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert not (private_home / ".history").exists()
    safe_result = repr(result)
    assert "credential-secret" not in safe_result
    assert operator_home.as_posix() not in safe_result
    assert "sha256" not in safe_result


def test_seed_provider_auth_state_rejects_runtime_traversal(tmp_path: Path) -> None:
    operator_home, private_home = _homes(tmp_path)

    with pytest.raises(LiveProviderAuthSeedError, match="runtime"):
        seed_provider_auth_state(
            ProviderAuthSeedRequest(
                runtime="../codex",
                operator_home=operator_home,
                provider_private_home=private_home,
            )
        )

    assert list(private_home.rglob("*")) == []


@pytest.mark.parametrize("symlink_level", ("home", "directory", "file"))
def test_seed_provider_auth_state_rejects_source_symlink_at_every_level(
    tmp_path: Path,
    symlink_level: str,
) -> None:
    operator_home, private_home = _homes(tmp_path)
    real_home = tmp_path / "real-home"
    real_auth = _write_auth(real_home, "codex", b"secret")
    if symlink_level == "home":
        operator_home.rmdir()
        operator_home.symlink_to(real_home, target_is_directory=True)
    elif symlink_level == "directory":
        (operator_home / ".codex").symlink_to(
            real_auth.parent,
            target_is_directory=True,
        )
    else:
        (operator_home / ".codex").mkdir()
        (operator_home / ".codex" / "auth.json").symlink_to(real_auth)

    with pytest.raises(LiveProviderAuthSeedError, match="symlink"):
        seed_provider_auth_state(
            ProviderAuthSeedRequest(
                runtime="codex",
                operator_home=operator_home,
                provider_private_home=private_home,
            )
        )

    assert not (private_home / ".codex" / "auth.json").exists()


def test_seed_provider_auth_state_rejects_destination_symlink(tmp_path: Path) -> None:
    operator_home, private_home = _homes(tmp_path)
    _write_auth(operator_home, "codex", b"secret")
    outside = tmp_path / "outside"
    outside.mkdir()
    (private_home / ".codex").symlink_to(outside, target_is_directory=True)

    with pytest.raises(LiveProviderAuthSeedError, match="symlink"):
        seed_provider_auth_state(
            ProviderAuthSeedRequest(
                runtime="codex",
                operator_home=operator_home,
                provider_private_home=private_home,
            )
        )

    assert not (outside / "auth.json").exists()


def test_seed_provider_auth_state_rejects_hard_link(tmp_path: Path) -> None:
    operator_home, private_home = _homes(tmp_path)
    auth = _write_auth(operator_home, "codex", b"secret")
    os.link(auth, operator_home / "auth-copy.json")

    with pytest.raises(LiveProviderAuthSeedError, match="hard linked"):
        seed_provider_auth_state(
            ProviderAuthSeedRequest(
                runtime="codex",
                operator_home=operator_home,
                provider_private_home=private_home,
            )
        )

    assert not (private_home / ".codex" / "auth.json").exists()


def test_seed_provider_auth_state_rejects_oversized_file(tmp_path: Path) -> None:
    operator_home, private_home = _homes(tmp_path)
    auth = _write_auth(operator_home, "claude-code", b"")
    auth.write_bytes(b"x" * (MAX_PROVIDER_AUTH_SEED_BYTES + 1))

    with pytest.raises(LiveProviderAuthSeedError, match="1 MiB"):
        seed_provider_auth_state(
            ProviderAuthSeedRequest(
                runtime="claude-code",
                operator_home=operator_home,
                provider_private_home=private_home,
            )
        )

    assert not (private_home / ".claude.json").exists()


def test_seed_provider_auth_state_cleans_partial_staging_after_copy_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    operator_home, private_home = _homes(tmp_path)
    _write_auth(operator_home, "codex", b"credential-secret")

    def fail_after_partial_copy(
        source_descriptor: int,
        destination_descriptor: int,
    ) -> tuple[int, bytes]:
        del source_descriptor
        os.write(destination_descriptor, b"partial")
        raise LiveProviderAuthSeedError("injected copy failure")

    monkeypatch.setattr(
        "aidd.harness.live_provider_auth_seed._copy_file_bytes",
        fail_after_partial_copy,
    )

    with pytest.raises(LiveProviderAuthSeedError, match="injected copy failure"):
        seed_provider_auth_state(
            ProviderAuthSeedRequest(
                runtime="codex",
                operator_home=operator_home,
                provider_private_home=private_home,
            )
        )

    assert not (private_home / ".codex" / "auth.json").exists()
    assert not list((private_home / ".codex").glob(".provider-auth-seed-*"))


def test_seed_provider_auth_state_does_not_overwrite_existing_private_auth(
    tmp_path: Path,
) -> None:
    operator_home, private_home = _homes(tmp_path)
    _write_auth(operator_home, "codex", b"new-secret")
    existing = _write_auth(private_home, "codex", b"existing-secret")

    with pytest.raises(LiveProviderAuthSeedError, match="already exists"):
        seed_provider_auth_state(
            ProviderAuthSeedRequest(
                runtime="codex",
                operator_home=operator_home,
                provider_private_home=private_home,
            )
        )

    assert existing.read_bytes() == b"existing-secret"
