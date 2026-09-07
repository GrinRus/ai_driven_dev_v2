from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from aidd.adapters.base import CapabilityReport, RuntimeAdapterDescriptor
from aidd.adapters.surface import RuntimeAdapterSurface, get_runtime_adapter_surface
from aidd.core.contracts import repo_root_from
from aidd.core.runtime_operator import (
    ProtectedRuntimePathKind,
    RuntimeOperatorPolicy,
    RuntimeOperatorRequest,
    classify_protected_runtime_path,
)
from aidd.harness.adapter_conformance import evaluate_conformance_matrix_model
from aidd.harness.conformance_matrix import RuntimeConformanceMatrix, RuntimeConformanceRow
from aidd.runtime_catalog import RuntimeExecutionMode, _runtime_definition_from_descriptor
from aidd.runtime_permissions import (
    AutoApprovalPreset,
    RuntimeOperatorDecisionAction,
    RuntimeOperatorRequestKind,
    RuntimePermissionPolicy,
)


def _fixture_descriptor() -> tuple[RuntimeAdapterDescriptor, str]:
    fixture_path = (
        repo_root_from(Path(__file__).resolve()) / "tests" / "fixtures" / "fake_external_adapter.py"
    )
    spec = importlib.util.spec_from_file_location("fake_external_adapter_fixture", fixture_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load test fixture: {fixture_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return cast(RuntimeAdapterDescriptor, module.DESCRIPTOR), cast(str, module.FAKE_RUNTIME_ID)


DESCRIPTOR, FAKE_RUNTIME_ID = _fixture_descriptor()


def _fake_probe(command: str) -> CapabilityReport:
    return CapabilityReport(
        runtime_id=FAKE_RUNTIME_ID,
        available=False,
        command=command,
        supports_raw_log_stream=True,
        supports_structured_log_stream=True,
        supports_questions=True,
        supports_resume=False,
        supports_subagents=False,
        supports_non_interactive_mode=True,
        supports_working_directory_control=True,
        supports_env_injection=True,
    )


def _fake_surface() -> RuntimeAdapterSurface:
    generic_surface = get_runtime_adapter_surface("generic-cli")
    return replace(
        generic_surface,
        runtime_id=FAKE_RUNTIME_ID,
        descriptor=DESCRIPTOR,
        probe=_fake_probe,
        default_execution_mode=RuntimeExecutionMode.NATIVE,
    )


def test_external_descriptor_passes_explicit_conformance_row(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import aidd.harness.adapter_conformance as adapter_conformance

    monkeypatch.setitem(
        adapter_conformance._ADAPTER_CONFORMANCE_SURFACES,
        FAKE_RUNTIME_ID,
        _fake_surface(),
    )
    dimensions = (
        "probe_behavior",
        "capability_declaration",
        "raw_log_capture",
        "failure_mapping",
        "question_surfacing",
        "timeout_behavior",
        "workspace_targeting",
    )
    matrix = RuntimeConformanceMatrix(
        dimensions=dimensions,
        rows=(
            RuntimeConformanceRow(
                runtime_id=FAKE_RUNTIME_ID,
                dimensions={dimension: "required" for dimension in dimensions},
            ),
        ),
    )

    result = evaluate_conformance_matrix_model(matrix=matrix, workspace_root=tmp_path)[0]

    assert result.runtime_id == FAKE_RUNTIME_ID
    assert not result.failed_required_dimensions()


def test_external_descriptor_projects_to_catalog_without_production_registration() -> None:
    definition = _runtime_definition_from_descriptor(DESCRIPTOR)

    assert definition.runtime_id == FAKE_RUNTIME_ID
    assert definition.config_section == "fake_external"
    assert definition.default_command == "fake-external-runtime --json -"
    assert definition.default_execution_mode is RuntimeExecutionMode.NATIVE
    assert definition.supported_execution_modes == (RuntimeExecutionMode.NATIVE,)


def test_external_descriptor_markers_drive_security_policy(tmp_path: Path) -> None:
    project_root = tmp_path / "repo"
    project_root.mkdir()
    protected_markers = (
        *DESCRIPTOR.protected_paths,
        *DESCRIPTOR.credential_paths,
        *DESCRIPTOR.config_paths,
    )

    protected_path = project_root / ".fake-external" / "auth.json"
    assert (
        classify_protected_runtime_path(
            protected_path,
            protected_path_markers=protected_markers,
        )
        is ProtectedRuntimePathKind.SENSITIVE_DATA
    )

    policy = RuntimeOperatorPolicy(
        permission_policy=RuntimePermissionPolicy.BROKERED,
        auto_approval_preset=AutoApprovalPreset.BROAD,
        project_roots=(project_root,),
        workspace_root=tmp_path / ".aidd",
        protected_path_markers=protected_markers,
    )
    request = RuntimeOperatorRequest.create(
        runtime_id=FAKE_RUNTIME_ID,
        stage="implement",
        kind=RuntimeOperatorRequestKind.FILE_WRITE,
        paths=(protected_path,),
    )

    decision = policy.evaluate(request)

    assert decision is not None
    assert decision.action is RuntimeOperatorDecisionAction.DENY


def test_runtime_neutral_sources_have_no_provider_literals() -> None:
    repo_root = repo_root_from(Path(__file__).resolve())
    source_paths = [*sorted((repo_root / "src" / "aidd" / "core").rglob("*.py"))]
    source_paths.extend(
        (repo_root / "src" / "aidd" / name) for name in ("runtime_catalog.py", "config.py")
    )
    provider_literals = (".claude", ".codex", ".opencode", ".qwen", "auth.json")

    for source_path in source_paths:
        source = source_path.read_text(encoding="utf-8")
        assert all(literal not in source for literal in provider_literals), source_path
    assert all(
        FAKE_RUNTIME_ID not in source_path.read_text(encoding="utf-8")
        for source_path in source_paths
    )
