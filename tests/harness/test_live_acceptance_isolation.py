from __future__ import annotations

import json
import os
import platform
import shlex
import subprocess
from pathlib import Path

import pytest

from aidd.harness.live_acceptance_isolation import (
    LiveAcceptanceIsolationBoundary,
    LiveAcceptanceIsolationCapability,
    LiveAcceptanceIsolationError,
    main,
    prepare_live_acceptance_isolation,
    probe_live_acceptance_isolation_capability,
)
from aidd.harness.live_acceptance_session import SESSION_INTEGRITY_FILENAME
from aidd.harness.live_acceptance_visibility import (
    VisibilityProbeTarget,
    run_live_acceptance_visibility_canary,
)
from aidd.harness.live_provider_auth_probe import ProviderAuthProbeResult


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


def _git_source(tmp_path: Path) -> Path:
    source = tmp_path / "git-source"
    source.mkdir()
    (source / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    for args in (
        ("init",),
        ("config", "user.email", "fixture@example.test"),
        ("config", "user.name", "Fixture"),
        ("add", "tracked.txt"),
        ("commit", "-m", "fixture"),
    ):
        subprocess.run(
            ("git", *args),
            cwd=source,
            check=True,
            capture_output=True,
            text=True,
        )
    return source


def _operator_auth(
    operator_home: Path,
    *,
    runtime: str,
    content: str,
) -> Path:
    relative = Path(".codex/auth.json") if runtime == "codex" else Path(".claude.json")
    path = operator_home / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)
    return path


def _fake_auth_cli(
    bin_dir: Path,
    *,
    runtime: str,
    source: Path,
    operator_marker: Path,
    sibling_marker: Path,
) -> None:
    executable = bin_dir / ("codex" if runtime == "codex" else "claude")
    relative_auth = ".codex/auth.json" if runtime == "codex" else ".claude.json"
    expected_args = (
        '[ "$1" = "login" ] && [ "$2" = "status" ]'
        if runtime == "codex"
        else (
            '[ "$1" = "auth" ] && [ "$2" = "status" ] '
            '&& [ "$3" = "--json" ]'
        )
    )
    executable.write_text(
        "#!/bin/sh\n"
        f"if ! {expected_args}; then exit 30; fi\n"
        f"if [ -r {shlex.quote(operator_marker.as_posix())} ]; then exit 31; fi\n"
        f"if [ -r {shlex.quote(sibling_marker.as_posix())} ]; then exit 32; fi\n"
        f"if printf 'mutated' >> {shlex.quote((source / 'tracked.txt').as_posix())} "
        "2>/dev/null; then exit 33; fi\n"
        f"if [ ! -f \"$HOME/{relative_auth}\" ]; then "
        "echo 'opaque-fixture-secret' >&2; exit 34; fi\n"
        f"grep -F 'opaque-fixture-secret' \"$HOME/{relative_auth}\" >/dev/null "
        "2>&1 || exit 35\n"
        "exit 0\n",
        encoding="utf-8",
    )
    executable.chmod(0o755)


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


def test_launcher_uses_mandatory_session_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _git_source(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    provider = external / "provider"
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_session."
        "require_live_acceptance_isolation_capability",
        lambda: LiveAcceptanceIsolationCapability(
            backend="macos-seatbelt",
            supported=True,
            detail="fixture capability",
        ),
    )

    def _boundary(**_kwargs: object) -> LiveAcceptanceIsolationBoundary:
        private_root = provider / ".live-provider-private"
        for relative in ("home", "tmp", "config", "cache", "data", "state"):
            (private_root / relative).mkdir(
                parents=True,
                exist_ok=True,
                mode=0o700,
            )
        return LiveAcceptanceIsolationBoundary(
            backend="macos-seatbelt",
            source_checkout=source,
            external_root=external,
            provider_root=provider,
            private_root=private_root,
            operator_home=None,
            tool_read_roots=tuple(),
            environment={"PATH": os.environ.get("PATH", "")},
            launch_prefix=tuple(),
        )

    monkeypatch.setattr(
        "aidd.harness.live_acceptance_isolation.prepare_live_acceptance_isolation",
        _boundary,
    )
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_isolation.probe_provider_auth_state",
        lambda **_kwargs: ProviderAuthProbeResult(
            runtime="codex",
            status="pass",
            exit_code=0,
        ),
    )

    assert (
        main(
            [
                "--source-checkout",
                source.as_posix(),
                "--external-root",
                external.as_posix(),
                "--provider-root",
                provider.as_posix(),
                "--runtime",
                "codex",
                "--",
                "/usr/bin/true",
            ]
        )
        == 0
    )
    payload = json.loads(
        (provider / SESSION_INTEGRITY_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["status"] == "pass"
    assert payload["process_exit_code"] == 0
    assert payload["cleanup"]["sentinel_removed"] is True
    assert payload["schema_version"] == 2
    assert payload["provider_auth"] == {
        "cleanup_status": "no-private-auth",
        "probe_status": "pass",
        "relative_destination": ".codex/auth.json",
        "runtime": "codex",
        "seed_mode": "none",
    }


def test_launcher_rejects_existing_provider_without_explicit_resume(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = _git_source(tmp_path)
    external = tmp_path / "external"
    provider = external / "provider"
    provider.mkdir(parents=True)
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_session."
        "require_live_acceptance_isolation_capability",
        lambda: LiveAcceptanceIsolationCapability(
            backend="macos-seatbelt",
            supported=True,
            detail="fixture capability",
        ),
    )

    exit_code = main(
        [
            "--source-checkout",
            source.as_posix(),
            "--external-root",
            external.as_posix(),
            "--provider-root",
            provider.as_posix(),
            "--runtime",
            "codex",
            "--",
            "/usr/bin/true",
        ]
    )

    assert exit_code == 2
    assert "already allocated or contaminated" in capsys.readouterr().err
    assert not (provider / SESSION_INTEGRITY_FILENAME).exists()


def test_launcher_resume_flag_requires_nested_run_id(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = _git_source(tmp_path)
    external = tmp_path / "external"
    provider = external / "provider"
    provider.mkdir(parents=True)

    exit_code = main(
        [
            "--source-checkout",
            source.as_posix(),
            "--external-root",
            external.as_posix(),
            "--provider-root",
            provider.as_posix(),
            "--runtime",
            "codex",
            "--resume-existing-provider",
            "--",
            "/usr/bin/true",
        ]
    )

    assert exit_code == 2
    assert "requires an explicit nested --run-id" in capsys.readouterr().err


def test_launcher_rejects_seed_during_resume_before_session_allocation(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = _git_source(tmp_path)
    external = tmp_path / "external"
    provider = external / "provider"
    external.mkdir()

    exit_code = main(
        [
            "--source-checkout",
            source.as_posix(),
            "--external-root",
            external.as_posix(),
            "--provider-root",
            provider.as_posix(),
            "--runtime",
            "codex",
            "--seed-provider-auth-from-home",
            "--resume-existing-provider",
            "--",
            "/usr/bin/true",
            "--run-id",
            "run-1",
        ]
    )

    assert exit_code == 2
    assert "incompatible" in capsys.readouterr().err
    assert not provider.exists()


def test_launcher_resume_reuses_private_auth_and_reprobes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _git_source(tmp_path)
    external = tmp_path / "external"
    provider = external / "provider"
    operator_home = tmp_path / "operator-home"
    fake_bin = tmp_path / "fake-bin"
    external.mkdir()
    operator_home.mkdir()
    fake_bin.mkdir()
    _operator_auth(
        operator_home,
        runtime="codex",
        content='{"opaque":"opaque-fixture-secret"}\n',
    )
    codex = fake_bin / "codex"
    codex.write_text(
        "#!/bin/sh\n"
        "[ \"$1\" = \"login\" ] && [ \"$2\" = \"status\" ] || exit 30\n"
        "grep -F 'opaque-fixture-secret' \"$HOME/.codex/auth.json\" "
        ">/dev/null 2>&1 || exit 31\n"
        "exit 0\n",
        encoding="utf-8",
    )
    codex.chmod(0o755)
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_session."
        "require_live_acceptance_isolation_capability",
        lambda: LiveAcceptanceIsolationCapability(
            backend="macos-seatbelt",
            supported=True,
            detail="fixture capability",
        ),
    )

    def _boundary(**_kwargs: object) -> LiveAcceptanceIsolationBoundary:
        private_root = provider / ".live-provider-private"
        for relative in ("home", "tmp", "config", "cache", "data", "state"):
            (private_root / relative).mkdir(
                parents=True,
                exist_ok=True,
                mode=0o700,
            )
        return LiveAcceptanceIsolationBoundary(
            backend="macos-seatbelt",
            source_checkout=source,
            external_root=external,
            provider_root=provider,
            private_root=private_root,
            operator_home=operator_home,
            tool_read_roots=(fake_bin,),
            environment={
                "HOME": (private_root / "home").as_posix(),
                "PATH": f"{fake_bin.as_posix()}:/usr/bin:/bin",
            },
            launch_prefix=tuple(),
        )

    monkeypatch.setattr(
        "aidd.harness.live_acceptance_isolation.prepare_live_acceptance_isolation",
        _boundary,
    )
    common_args = [
        "--source-checkout",
        source.as_posix(),
        "--external-root",
        external.as_posix(),
        "--provider-root",
        provider.as_posix(),
        "--runtime",
        "codex",
    ]

    assert (
        main(
            [
                *common_args,
                "--seed-provider-auth-from-home",
                "--",
                "/usr/bin/true",
            ]
        )
        == 0
    )
    private_auth = (
        provider
        / ".live-provider-private"
        / "home"
        / ".codex"
        / "auth.json"
    )
    first_inode = private_auth.stat().st_ino
    first_bytes = private_auth.read_bytes()

    assert (
        main(
            [
                *common_args,
                "--resume-existing-provider",
                "--",
                "/usr/bin/true",
                "--run-id",
                "run-1",
            ]
        )
        == 0
    )

    assert private_auth.stat().st_ino == first_inode
    assert private_auth.read_bytes() == first_bytes
    payload = json.loads(
        (provider / SESSION_INTEGRITY_FILENAME).read_text(encoding="utf-8")
    )
    assert payload["provider_auth"] == {
        "cleanup_status": "private-auth-retained",
        "probe_status": "pass",
        "relative_destination": ".codex/auth.json",
        "runtime": "codex",
        "seed_mode": "existing-private-home",
    }


@pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="real provider auth Seatbelt verification is macOS-specific",
)
@pytest.mark.parametrize("runtime", ("codex", "claude-code"))
def test_seeded_private_auth_probe_crosses_real_boundary_before_evaluator(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime: str,
) -> None:
    source = _git_source(tmp_path)
    external = tmp_path / "external"
    provider = external / runtime
    sibling = external / "sibling-provider"
    operator_home = tmp_path / "operator-home"
    fake_bin = tmp_path / "fake-bin"
    external.mkdir()
    sibling.mkdir()
    operator_home.mkdir()
    fake_bin.mkdir()
    operator_marker = operator_home / "operator-marker"
    sibling_marker = sibling / "credential-marker"
    operator_marker.write_text("operator-only\n", encoding="utf-8")
    sibling_marker.write_text("sibling-only\n", encoding="utf-8")
    _operator_auth(
        operator_home,
        runtime=runtime,
        content='{"opaque":"opaque-fixture-secret"}\n',
    )
    _fake_auth_cli(
        fake_bin,
        runtime=runtime,
        source=source,
        operator_marker=operator_marker,
        sibling_marker=sibling_marker,
    )
    monkeypatch.setenv("HOME", operator_home.as_posix())
    monkeypatch.setenv(
        "PATH",
        f"{fake_bin.as_posix()}:/usr/bin:/bin",
    )
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_session."
        "require_live_acceptance_isolation_capability",
        lambda: LiveAcceptanceIsolationCapability(
            backend="macos-seatbelt",
            supported=True,
            detail="fixture capability",
        ),
    )
    evaluator_sentinel = provider / "evaluator-launched"

    exit_code = main(
        [
            "--source-checkout",
            source.as_posix(),
            "--external-root",
            external.as_posix(),
            "--provider-root",
            provider.as_posix(),
            "--runtime",
            runtime,
            "--seed-provider-auth-from-home",
            "--tool-read-root",
            fake_bin.as_posix(),
            "--",
            "/bin/sh",
            "-c",
            f"printf launched > {shlex.quote(evaluator_sentinel.as_posix())}",
        ]
    )

    assert exit_code == 0
    assert evaluator_sentinel.read_text(encoding="utf-8") == "launched"
    relative_auth = (
        Path(".codex/auth.json")
        if runtime == "codex"
        else Path(".claude.json")
    )
    private_auth = (
        provider / ".live-provider-private" / "home" / relative_auth
    )
    assert private_auth.is_file()
    assert not (sibling / relative_auth).exists()
    assert (source / "tracked.txt").read_text(encoding="utf-8") == "tracked\n"
    payload_text = (provider / SESSION_INTEGRITY_FILENAME).read_text(
        encoding="utf-8"
    )
    payload = json.loads(payload_text)
    assert payload["provider_auth"] == {
        "cleanup_status": "private-auth-retained",
        "probe_status": "pass",
        "relative_destination": relative_auth.as_posix(),
        "runtime": runtime,
        "seed_mode": "seeded-from-operator-home",
    }
    diagnostic_text = payload_text + capsys.readouterr().err
    assert "opaque-fixture-secret" not in diagnostic_text
    assert operator_home.as_posix() not in diagnostic_text
    assert "credential digest" not in diagnostic_text


@pytest.mark.skipif(
    platform.system() != "Darwin",
    reason="real provider auth Seatbelt verification is macOS-specific",
)
@pytest.mark.parametrize("runtime", ("codex", "claude-code"))
def test_unseeded_private_auth_blocks_evaluator_inside_real_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    runtime: str,
) -> None:
    source = _git_source(tmp_path)
    external = tmp_path / "external"
    provider = external / runtime
    sibling = external / "sibling-provider"
    operator_home = tmp_path / "operator-home"
    fake_bin = tmp_path / "fake-bin"
    external.mkdir()
    sibling.mkdir()
    operator_home.mkdir()
    fake_bin.mkdir()
    operator_marker = operator_home / "operator-marker"
    sibling_marker = sibling / "credential-marker"
    operator_marker.write_text("operator-only\n", encoding="utf-8")
    sibling_marker.write_text("sibling-only\n", encoding="utf-8")
    _operator_auth(
        operator_home,
        runtime=runtime,
        content='{"opaque":"opaque-fixture-secret"}\n',
    )
    _fake_auth_cli(
        fake_bin,
        runtime=runtime,
        source=source,
        operator_marker=operator_marker,
        sibling_marker=sibling_marker,
    )
    monkeypatch.setenv("HOME", operator_home.as_posix())
    monkeypatch.setenv(
        "PATH",
        f"{fake_bin.as_posix()}:/usr/bin:/bin",
    )
    monkeypatch.setattr(
        "aidd.harness.live_acceptance_session."
        "require_live_acceptance_isolation_capability",
        lambda: LiveAcceptanceIsolationCapability(
            backend="macos-seatbelt",
            supported=True,
            detail="fixture capability",
        ),
    )
    evaluator_sentinel = provider / "evaluator-launched"

    exit_code = main(
        [
            "--source-checkout",
            source.as_posix(),
            "--external-root",
            external.as_posix(),
            "--provider-root",
            provider.as_posix(),
            "--runtime",
            runtime,
            "--tool-read-root",
            fake_bin.as_posix(),
            "--",
            "/bin/sh",
            "-c",
            f"printf launched > {shlex.quote(evaluator_sentinel.as_posix())}",
        ]
    )

    assert exit_code == 2
    assert not evaluator_sentinel.exists()
    captured = capsys.readouterr()
    assert "provider-auth blocker" in captured.err
    assert "opaque-fixture-secret" not in captured.err
    payload_text = (provider / SESSION_INTEGRITY_FILENAME).read_text(
        encoding="utf-8"
    )
    payload = json.loads(payload_text)
    assert payload["provider_auth"]["probe_status"] == "fail"
    assert payload["provider_auth"]["cleanup_status"] == "no-private-auth"
    assert payload["provider_auth"]["seed_mode"] == "none"
    assert "opaque-fixture-secret" not in payload_text
