from __future__ import annotations

import os
import platform
from pathlib import Path

import pytest

from aidd.harness.live_acceptance_isolation import (
    LiveAcceptanceIsolationError,
    prepare_live_acceptance_isolation,
    probe_live_acceptance_isolation_capability,
)
from aidd.harness.live_acceptance_visibility import (
    VisibilityProbeTarget,
    run_live_acceptance_visibility_canary,
)


def _roots(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    source = tmp_path / "source"
    external = tmp_path / "external"
    provider = external / "provider-a"
    sibling = external / "provider-b"
    source.mkdir()
    external.mkdir()
    sibling.mkdir()
    return source, external, provider, sibling


def _targets_by_label(diagnostics: dict[str, object]) -> dict[str, dict[str, object]]:
    targets = diagnostics["targets"]
    assert isinstance(targets, list)
    return {
        str(target["label"]): target
        for target in targets
        if isinstance(target, dict)
    }


def test_private_environment_is_allowlisted_and_uses_provider_roots(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, external, provider, _ = _roots(tmp_path)
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_isolation.shutil.which",
        lambda _name: "/usr/bin/sandbox-exec",
    )
    boundary = prepare_live_acceptance_isolation(
        source_checkout=source,
        external_root=external,
        provider_root=provider,
        inherited_environment={
            "HOME": (tmp_path / "operator-home").as_posix(),
            "PATH": "/usr/bin",
            "LANG": "en_US.UTF-8",
            "AIDD_OWN_CREDENTIAL": "own-secret",
            "AIDD_SIBLING_CREDENTIAL": "sibling-secret",
            "UNRELATED": "must-not-cross",
        },
        credential_environment_keys=("AIDD_OWN_CREDENTIAL",),
        system_name="Darwin",
    )

    assert boundary.backend == "macos-seatbelt"
    assert boundary.environment["PATH"] == "/usr/bin"
    assert boundary.environment["LANG"] == "en_US.UTF-8"
    assert boundary.environment["AIDD_OWN_CREDENTIAL"] == "own-secret"
    assert "AIDD_SIBLING_CREDENTIAL" not in boundary.environment
    assert "UNRELATED" not in boundary.environment
    assert boundary.environment["HOME"] == (
        provider / ".live-provider-private" / "home"
    ).as_posix()
    assert boundary.environment["XDG_CONFIG_HOME"] == (
        provider / ".live-provider-private" / "config"
    ).as_posix()
    assert boundary.environment["AIDD_LIVE_ISOLATION_ACTIVE"] == "1"
    assert all(
        (provider / ".live-provider-private" / name).is_dir()
        for name in ("home", "tmp", "config", "cache", "data", "state")
    )


def test_isolation_rejects_unsupported_platform(tmp_path: Path) -> None:
    source, external, provider, _ = _roots(tmp_path)

    with pytest.raises(LiveAcceptanceIsolationError, match="No enforceable"):
        prepare_live_acceptance_isolation(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
            inherited_environment={"PATH": "/usr/bin"},
            system_name="Plan9",
        )


def test_isolation_rejects_provider_root_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, external, provider, sibling = _roots(tmp_path)
    provider.symlink_to(sibling, target_is_directory=True)
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_isolation.shutil.which",
        lambda _name: "/usr/bin/sandbox-exec",
    )

    with pytest.raises(LiveAcceptanceIsolationError, match="not a symlink"):
        prepare_live_acceptance_isolation(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
            inherited_environment={"PATH": "/usr/bin"},
            system_name="Darwin",
        )


def test_isolation_rejects_private_environment_symlink(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, external, provider, sibling = _roots(tmp_path)
    provider.mkdir()
    (provider / ".live-provider-private").symlink_to(
        sibling,
        target_is_directory=True,
    )
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_isolation.shutil.which",
        lambda _name: "/usr/bin/sandbox-exec",
    )

    with pytest.raises(LiveAcceptanceIsolationError, match="must not be a symlink"):
        prepare_live_acceptance_isolation(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
            inherited_environment={"PATH": "/usr/bin"},
            system_name="Darwin",
        )


def test_linux_backend_requires_bubblewrap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, external, provider, _ = _roots(tmp_path)
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_isolation.shutil.which",
        lambda _name: None,
    )

    with pytest.raises(LiveAcceptanceIsolationError, match="bubblewrap is unavailable"):
        prepare_live_acceptance_isolation(
            source_checkout=source,
            external_root=external,
            provider_root=provider,
            inherited_environment={"PATH": "/usr/bin"},
            system_name="Linux",
        )


def test_linux_backend_hides_external_root_and_restores_only_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, external, provider, _ = _roots(tmp_path)
    operator_home = tmp_path / "operator-home"
    operator_home.mkdir()
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_isolation.shutil.which",
        lambda _name: "/usr/bin/bwrap",
    )

    boundary = prepare_live_acceptance_isolation(
        source_checkout=source,
        external_root=external,
        provider_root=provider,
        inherited_environment={
            "HOME": operator_home.as_posix(),
            "PATH": "/usr/bin",
        },
        system_name="Linux",
    )

    assert boundary.backend == "linux-bubblewrap"
    prefix = boundary.launch_prefix
    assert ("--tmpfs", external.resolve().as_posix()) in tuple(
        zip(prefix, prefix[1:], strict=False)
    )
    assert (
        "--bind",
        provider.resolve().as_posix(),
        provider.resolve().as_posix(),
    ) in tuple(zip(prefix, prefix[1:], prefix[2:], strict=False))
    assert (
        "--ro-bind",
        source.resolve().as_posix(),
        source.resolve().as_posix(),
    ) in tuple(zip(prefix, prefix[1:], prefix[2:], strict=False))


@pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="real Seatbelt verification is macOS-specific",
)
def test_macos_boundary_enforces_visibility_matrix(tmp_path: Path) -> None:
    source, external, provider, sibling = _roots(tmp_path)
    operator_home = tmp_path / "operator-home"
    operator_config = operator_home / ".config"
    operator_cache = operator_home / ".cache"
    operator_config.mkdir(parents=True)
    operator_cache.mkdir()
    target = provider / "target"
    evidence = provider / "evidence"
    target.mkdir(parents=True)
    evidence.mkdir()
    for root in (source, sibling, target, evidence, operator_home, operator_config, operator_cache):
        (root / "marker.txt").write_text(f"{root.name}\n", encoding="utf-8")

    boundary = prepare_live_acceptance_isolation(
        source_checkout=source,
        external_root=external,
        provider_root=provider,
        inherited_environment={
            "HOME": operator_home.as_posix(),
            "PATH": os.environ.get("PATH", ""),
            "AIDD_OWN_CREDENTIAL": "own-secret",
            "AIDD_SIBLING_CREDENTIAL": "sibling-secret",
        },
        credential_environment_keys=("AIDD_OWN_CREDENTIAL",),
    )
    result = run_live_acceptance_visibility_canary(
        targets=tuple(
            VisibilityProbeTarget(label, root, "marker.txt")
            for label, root in (
                ("source", source),
                ("target", target),
                ("evidence", evidence),
                ("sibling-provider", sibling),
                ("operator-home", operator_home),
                ("operator-config", operator_config),
                ("operator-cache", operator_cache),
            )
        ),
        environment_keys=(
            "AIDD_OWN_CREDENTIAL",
            "AIDD_SIBLING_CREDENTIAL",
            "AIDD_LIVE_ISOLATION_ACTIVE",
        ),
        cwd=target,
        environment=boundary.environment,
        launch_prefix=boundary.launch_prefix,
    )

    targets = _targets_by_label(result.diagnostics)
    for label in ("target", "evidence"):
        operations = targets[label]["operations"]
        assert isinstance(operations, dict)
        assert all(operation["allowed"] for operation in operations.values())
    source_operations = targets["source"]["operations"]
    assert isinstance(source_operations, dict)
    assert source_operations["list"]["allowed"] is True
    assert source_operations["read"]["allowed"] is True
    assert source_operations["write"]["allowed"] is False
    for label in (
        "sibling-provider",
        "operator-home",
        "operator-config",
        "operator-cache",
    ):
        operations = targets[label]["operations"]
        assert isinstance(operations, dict)
        assert all(operation["allowed"] is False for operation in operations.values())
    assert result.diagnostics["environment"] == [
        {"key": "AIDD_OWN_CREDENTIAL", "present": True, "non_empty": True},
        {"key": "AIDD_SIBLING_CREDENTIAL", "present": False, "non_empty": False},
        {
            "key": "AIDD_LIVE_ISOLATION_ACTIVE",
            "present": True,
            "non_empty": True,
        },
    ]


def test_platform_capability_uses_negative_canary() -> None:
    if platform.system() == "Linux" and not Path("/usr/bin/bwrap").exists():
        pytest.skip("bubblewrap is unavailable")
    capability = probe_live_acceptance_isolation_capability()

    assert capability.supported is True
    assert capability.detail == "isolation canary passed"
