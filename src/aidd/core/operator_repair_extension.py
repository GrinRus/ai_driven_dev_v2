from __future__ import annotations

import hashlib
from pathlib import Path

from aidd.core.models.run import RepairExtensionGrant
from aidd.core.operator_frontend_models import (
    OperatorRepairExtensionPreview,
    OperatorValidationFindingView,
)
from aidd.core.operator_frontend_validation import load_validator_report_findings
from aidd.core.repair import (
    count_stage_attempts,
    evaluate_repair_extension_eligibility,
    repair_attempts_used,
)
from aidd.core.run_inspection import StageResultSummary, resolve_run_metadata_summary
from aidd.core.run_store import load_attempt_artifact_index, load_stage_metadata
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stages import STAGES
from aidd.core.workspace import stage_root


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _safe_workspace_path(*, workspace_root: Path, relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    candidate = Path(relative_path)
    if candidate.is_absolute() or "\\" in relative_path:
        return None
    workspace = workspace_root.resolve(strict=False)
    resolved = (workspace / candidate).resolve(strict=False)
    if not resolved.is_relative_to(workspace):
        return None
    return resolved


def _relative_existing_path(*, workspace_root: Path, path: Path | None) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    try:
        return workspace_relative_path(workspace_root, path)
    except ValueError:
        return None


def _stage_result_has_exhaustion_marker(
    *, workspace_root: Path, work_item: str, stage: str
) -> bool:
    result_path = stage_root(workspace_root, work_item, stage) / "stage-result.md"
    try:
        text = result_path.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return "repair-budget-exhausted" in text or "repair budget exhausted" in text


def _attempt_modes(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_count: int,
) -> tuple[str | None, ...]:
    modes: list[str | None] = []
    for attempt_number in range(1, attempt_count + 1):
        try:
            index = load_attempt_artifact_index(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
                stage=stage,
                attempt_number=attempt_number,
            )
        except (OSError, ValueError, KeyError, TypeError):
            index = None
        modes.append(None if index is None else index.attempt_mode)
    return tuple(modes)


def _downstream_succeeded(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
) -> tuple[str, ...]:
    try:
        current_index = STAGES.index(stage)
    except ValueError:
        return ()
    succeeded: list[str] = []
    for downstream_stage in STAGES[current_index + 1 :]:
        metadata = load_stage_metadata(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=downstream_stage,
        )
        if metadata is not None and metadata.status.strip().lower() == "succeeded":
            succeeded.append(downstream_stage)
    return tuple(succeeded)


def _preview(
    *,
    work_item: str,
    run_id: str,
    stage: str,
    runtime_id: str | None,
    eligible: bool,
    disabled_reason: str | None,
    findings: tuple[OperatorValidationFindingView, ...],
    used: int,
    maximum: int,
    manual_grant_used: bool,
    validator_report_path: str | None,
    validator_report_sha256: str | None,
    repair_brief_path: str | None,
    repair_brief_sha256: str | None,
    selected_runner: str | None,
    downstream_succeeded: tuple[str, ...],
    configuration_identity: str | None,
) -> OperatorRepairExtensionPreview:
    return OperatorRepairExtensionPreview(
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        runtime_id=runtime_id,
        eligible=eligible,
        disabled_reason=disabled_reason,
        primary_cause=findings[0] if findings else None,
        current_findings=findings,
        automatic_repair_attempts_used=used,
        automatic_repair_attempts_max=maximum,
        automatic_repair_attempts_remaining=max(0, maximum - used),
        manual_grant_used=manual_grant_used,
        validator_report_path=validator_report_path,
        validator_report_sha256=validator_report_sha256,
        repair_brief_path=repair_brief_path,
        repair_brief_sha256=repair_brief_sha256,
        selected_runner=selected_runner,
        downstream_succeeded=downstream_succeeded,
        configuration_identity=configuration_identity,
    )


def resolve_operator_repair_extension_preview(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    result: StageResultSummary | None = None,
    current_configuration_identity: str | None = None,
    selected_runner: str | None = None,
    active_job: bool = False,
    max_repair_attempts: int = 2,
) -> OperatorRepairExtensionPreview:
    """Resolve repair-extension state without inferring eligibility in the browser."""

    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    if result is None:
        try:
            from aidd.core.run_inspection import resolve_stage_result_summary

            result = resolve_stage_result_summary(
                workspace_root=workspace_root,
                work_item=work_item,
                stage=stage,
                run_id=run_id,
            )
        except (OSError, ValueError, KeyError, TypeError):
            result = None

    runtime_id = selected_runner
    if runtime_id is None:
        try:
            runtime_id = resolve_run_metadata_summary(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=run_id,
            ).runtime_id
        except (OSError, ValueError, KeyError, TypeError):
            runtime_id = None
    runtime_id = runtime_id.strip() if runtime_id else None

    stage_root_path = stage_root(workspace_root, work_item, stage)
    grant = metadata.repair_extension_grant if metadata is not None else None
    manual_grant_used = grant is not None
    latest_history = metadata.repair_history[-1] if metadata and metadata.repair_history else None
    validator_relative = (
        grant.validator_report_path
        if grant is not None
        else latest_history.validator_report_path
        if latest_history is not None and latest_history.validator_report_path
        else result.validator_report_path
        if result is not None
        else None
    )
    repair_relative = (
        grant.repair_brief_path
        if grant is not None
        else latest_history.repair_brief_path
        if latest_history is not None and latest_history.repair_brief_path
        else workspace_relative_path(workspace_root, stage_root_path / "repair-brief.md")
        if (stage_root_path / "repair-brief.md").exists()
        else None
    )
    validator_path = _safe_workspace_path(
        workspace_root=workspace_root,
        relative_path=validator_relative,
    )
    repair_path = _safe_workspace_path(
        workspace_root=workspace_root,
        relative_path=repair_relative,
    )
    validator_sha = _sha256(validator_path) if validator_path is not None else None
    repair_sha = _sha256(repair_path) if repair_path is not None else None
    validator_path_value = _relative_existing_path(
        workspace_root=workspace_root, path=validator_path
    )
    repair_path_value = _relative_existing_path(
        workspace_root=workspace_root, path=repair_path
    )
    findings = load_validator_report_findings(
        workspace_root=workspace_root,
        validator_report_path=validator_path_value,
    )

    attempt_count = count_stage_attempts(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    used = repair_attempts_used(
        stage_attempt_count=attempt_count,
        attempt_modes=_attempt_modes(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_count=attempt_count,
        ),
    )
    maximum = max_repair_attempts
    if maximum < 0:
        maximum = 0
    downstream = _downstream_succeeded(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    status = metadata.status.strip().lower() if metadata is not None else "missing"
    if _stage_result_has_exhaustion_marker(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
    ):
        status = "repair-exhausted"
    latest_mode = latest_history.trigger if latest_history is not None else "initial"

    missing_reason: str | None = None
    if metadata is None:
        missing_reason = (
            "Repair extension preview is unavailable because stage metadata is missing."
        )
    elif runtime_id is None:
        missing_reason = (
            "Selected Runner is unavailable; refresh Runner readiness before repair extension."
        )
    elif validator_path_value is None or validator_sha is None:
        missing_reason = (
            "Repair extension validator evidence is unavailable; refresh the validator report."
        )
    elif repair_path_value is None or repair_sha is None:
        missing_reason = "Repair extension brief evidence is unavailable; refresh the repair brief."
    elif current_configuration_identity is None or not current_configuration_identity.strip():
        missing_reason = (
            "Runtime configuration identity is unavailable; refresh Runner readiness before "
            "repair extension."
        )

    if missing_reason is not None:
        return _preview(
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            runtime_id=runtime_id,
            eligible=False,
            disabled_reason=missing_reason,
            findings=findings,
            used=used,
            maximum=maximum,
            manual_grant_used=manual_grant_used,
            validator_report_path=validator_path_value,
            validator_report_sha256=validator_sha,
            repair_brief_path=repair_path_value,
            repair_brief_sha256=repair_sha,
            selected_runner=runtime_id,
            downstream_succeeded=downstream,
            configuration_identity=current_configuration_identity,
        )

    assert metadata is not None
    assert validator_path_value is not None
    assert validator_sha is not None
    assert repair_path_value is not None
    assert repair_sha is not None
    assert current_configuration_identity is not None

    if grant is None:
        grant = RepairExtensionGrant(
            work_item_id=work_item,
            run_id=run_id,
            stage=stage,
            validator_report_path=validator_path_value,
            validator_report_sha256=validator_sha,
            repair_brief_path=repair_path_value,
            repair_brief_sha256=repair_sha,
            configuration_identity=current_configuration_identity,
            author="operator-preview",
            authorized_at_utc=metadata.updated_at_utc,
            reason="UI preview only",
        )

    decision = evaluate_repair_extension_eligibility(
        grant,
        expected_work_item_id=work_item,
        expected_run_id=run_id,
        expected_stage=stage,
        latest_stage_status=status,
        latest_attempt_mode=latest_mode,
        current_validator_report_sha256=validator_sha,
        current_repair_brief_sha256=repair_sha,
        current_configuration_identity=current_configuration_identity,
        active_job=active_job,
        prior_grant=metadata.repair_extension_grant if metadata is not None else None,
        succeeded_downstream=downstream,
    )
    return _preview(
        eligible=decision.eligible,
        disabled_reason=decision.disabled_reason,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        runtime_id=runtime_id,
        findings=findings,
        used=used,
        maximum=maximum,
        manual_grant_used=manual_grant_used,
        validator_report_path=validator_path_value,
        validator_report_sha256=validator_sha,
        repair_brief_path=repair_path_value,
        repair_brief_sha256=repair_sha,
        selected_runner=runtime_id,
        downstream_succeeded=downstream,
        configuration_identity=current_configuration_identity,
    )


__all__ = ["resolve_operator_repair_extension_preview"]
