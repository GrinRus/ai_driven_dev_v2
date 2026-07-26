from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest

from aidd.harness.live_acceptance_visibility import (
    VISIBILITY_CANARY_LAUNCH_BOUNDARY,
    LiveAcceptanceVisibilityError,
    VisibilityProbeTarget,
    run_live_acceptance_visibility_canary,
)

_SIBLING_CREDENTIAL_KEY = "AIDD_TEST_SIBLING_PROVIDER_CREDENTIAL"


def _probe_target(tmp_path: Path, label: str) -> VisibilityProbeTarget:
    root = tmp_path / f"{label}-{os.urandom(6).hex()}"
    root.mkdir()
    (root / "canary-readable.txt").write_text(f"{label}-readable\n", encoding="utf-8")
    return VisibilityProbeTarget(
        label=label,
        root=root,
        read_relative_path="canary-readable.txt",
    )


def _targets_by_label(diagnostics: dict[str, object]) -> dict[str, dict[str, object]]:
    targets = diagnostics["targets"]
    assert isinstance(targets, list)
    return {
        str(target["label"]): target
        for target in targets
        if isinstance(target, dict)
    }


def test_visibility_canary_characterizes_current_sibling_root_and_credential_access(
    tmp_path: Path,
) -> None:
    targets = tuple(
        _probe_target(tmp_path, label)
        for label in (
            "source",
            "target",
            "provider",
            "credential",
            "sibling-provider",
        )
    )
    target_root = next(target.root for target in targets if target.label == "target")
    environment = dict(os.environ)
    sibling_secret = "sibling-provider-secret-must-not-be-rendered"
    environment[_SIBLING_CREDENTIAL_KEY] = sibling_secret

    result = run_live_acceptance_visibility_canary(
        targets=targets,
        environment_keys=(_SIBLING_CREDENTIAL_KEY,),
        cwd=target_root,
        environment=environment,
    )

    assert result.command_result.exit_code == 0
    assert result.diagnostics["schema_version"] == 1
    assert result.diagnostics["launch_boundary"] == VISIBILITY_CANARY_LAUNCH_BOUNDARY
    assert result.diagnostics["cwd"] == target_root.as_posix()
    targets_by_label = _targets_by_label(result.diagnostics)
    assert set(targets_by_label) == {target.label for target in targets}
    for target in targets:
        target_diagnostics = targets_by_label[target.label]
        operations = target_diagnostics["operations"]
        assert isinstance(operations, dict)
        assert {
            name: operation["status"]
            for name, operation in operations.items()
            if isinstance(operation, dict)
        } == {
            "list": "allowed",
            "read": "allowed",
            "write": "allowed",
        }
        read_diagnostics = operations["read"]
        assert isinstance(read_diagnostics, dict)
        expected = f"{target.label}-readable\n".encode()
        assert read_diagnostics["observed_sha256"] == hashlib.sha256(expected).hexdigest()
        assert not tuple(target.root.glob(".aidd-visibility-canary-*"))

    environment_diagnostics = result.diagnostics["environment"]
    assert environment_diagnostics == [
        {
            "key": _SIBLING_CREDENTIAL_KEY,
            "present": True,
            "non_empty": True,
        }
    ]
    assert sibling_secret not in result.command_result.stdout_text


def test_visibility_canary_normalizes_inaccessible_missing_root(
    tmp_path: Path,
) -> None:
    missing = VisibilityProbeTarget(
        label="missing-root",
        root=tmp_path / "does-not-exist",
        read_relative_path="canary-readable.txt",
    )

    result = run_live_acceptance_visibility_canary(
        targets=(missing,),
        environment_keys=("AIDD_TEST_MISSING_CREDENTIAL",),
        cwd=tmp_path,
        environment=dict(os.environ),
    )

    target = _targets_by_label(result.diagnostics)["missing-root"]
    operations = target["operations"]
    assert isinstance(operations, dict)
    assert all(
        isinstance(operation, dict)
        and operation["status"] == "error"
        and operation["allowed"] is False
        and operation["error_type"] == "FileNotFoundError"
        for operation in operations.values()
    )
    assert result.diagnostics["environment"] == [
        {
            "key": "AIDD_TEST_MISSING_CREDENTIAL",
            "present": False,
            "non_empty": False,
        }
    ]


@pytest.mark.parametrize(
    "read_relative_path",
    ("", "/absolute.txt", "../escape.txt", "nested\\escape.txt"),
)
def test_visibility_target_rejects_unsafe_read_path(
    tmp_path: Path,
    read_relative_path: str,
) -> None:
    with pytest.raises(
        LiveAcceptanceVisibilityError,
        match="contained relative POSIX path",
    ):
        VisibilityProbeTarget(
            label="unsafe",
            root=tmp_path,
            read_relative_path=read_relative_path,
        )
