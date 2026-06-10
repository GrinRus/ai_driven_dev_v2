from __future__ import annotations

import json
from pathlib import Path

from aidd.core.markdown import (
    extract_markdown_headings,
    extract_required_sections_from_document_contract,
    extract_stage_required_heading_map,
    normalize_heading,
)
from aidd.core.operator_frontend_common import validate_operator_stage
from aidd.core.operator_frontend_models import (
    OperatorArtifactDocumentView,
    OperatorArtifactRef,
    OperatorEvidenceGraphEdge,
    OperatorEvidenceGraphNode,
    OperatorEvidenceGraphView,
    OperatorStageDocumentDiffInput,
    OperatorStageDocumentReference,
    OperatorStageDocumentRequirement,
    OperatorStageDocumentValidationResult,
    OperatorStageDocumentVersion,
    OperatorStageDocumentWorkbench,
    OperatorStageWorkbenchDocument,
)
from aidd.core.resources import resolve_resource_layout_from_contracts_root
from aidd.core.run_inspection import (
    RunArtifactsSummary,
    StageResultSummary,
    resolve_run_artifacts_summary,
    resolve_stage_result_summary,
)
from aidd.core.run_lookup import latest_attempt_number, latest_run_id
from aidd.core.run_store import (
    RUN_EVENTS_JSONL_FILENAME,
    load_attempt_artifact_index,
    load_stage_metadata,
    run_attempt_root,
)
from aidd.core.runtime_operator import (
    OPERATOR_DECISIONS_FILENAME,
    OPERATOR_REQUESTS_FILENAME,
    load_operator_decisions,
    load_operator_requests,
)
from aidd.core.stage_paths import workspace_relative_path
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    StageManifestLoadError,
    load_stage_manifest,
    resolve_expected_output_documents,
    stage_contract_path,
)

_DEFAULT_ARTIFACT_PREVIEW_BYTES = 64 * 1024
_DEFAULT_ARTIFACT_SOURCE_BYTES = 128 * 1024
_MAX_ARTIFACT_READ_BYTES = 256 * 1024
_SYSTEM_DOCUMENT_KEYS = {
    "answers",
    "input_bundle",
    "operator_request",
    "questions",
    "repair_brief",
    "repair_context",
    "stage_brief",
    "validator_report",
}


def operator_artifact_category(*, key: str, kind: str, path: str) -> str:
    normalized_key = key.replace("-", "_").lower()
    normalized_path = path.replace("\\", "/").lower()
    if kind == "log" or normalized_key in {"runtime_log", "events_jsonl"}:
        return "runtime-evidence"
    if (
        normalized_key
        in {"input_bundle", "stage_brief", "repair_context", "operator_request"}
        or "/operator-requests/" in normalized_path
    ):
        return "runtime-input"
    if normalized_key in {"validator_report", "repair_brief"}:
        return "validation-evidence"
    if "project-set.md" in normalized_path or normalized_key == "project_set_context":
        return "project-evidence"
    if "/remediations/" in normalized_path or "lineage" in normalized_key:
        return "lineage-evidence"
    return "canonical-stage-document"


def operator_artifact_safe_key(key: str) -> str:
    return key.strip().replace("/", "_").replace("\\", "_")


def operator_artifact_is_canonical(*, key: str, kind: str, path: str) -> bool:
    return (
        kind == "document"
        and operator_artifact_category(key=key, kind=kind, path=path)
        == "canonical-stage-document"
    )


def resolve_operator_artifacts_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> RunArtifactsSummary:
    validate_operator_stage(stage)
    return resolve_run_artifacts_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=run_id,
        attempt_number=attempt_number,
    )


def resolve_operator_artifact_document_content(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    key: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
    mode: str = "preview",
    limit_bytes: int | None = None,
) -> OperatorArtifactDocumentView:
    validate_operator_stage(stage)
    normalized_key = key.strip()
    if not normalized_key:
        raise ValueError("Artifact document key is required.")
    normalized_mode = mode.strip().lower() or "preview"
    if normalized_mode not in {"preview", "source"}:
        raise ValueError("mode must be 'preview' or 'source'.")
    if limit_bytes is not None and limit_bytes <= 0:
        raise ValueError("limit_bytes must be greater than zero.")

    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")
    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )
    artifact_index = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_index is None:
        raise ValueError(
            f"Artifact index is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    relative_document_path = artifact_index.documents.get(normalized_key)
    if relative_document_path is None:
        supported = ", ".join(sorted(artifact_index.documents)) or "none"
        raise ValueError(
            f"Artifact document key '{normalized_key}' is not available. "
            f"Available document keys: {supported}."
        )
    return _bounded_operator_artifact_document(
        workspace_root=workspace_root,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        key=normalized_key,
        relative_document_path=relative_document_path,
        mode=normalized_mode,
        limit_bytes=limit_bytes,
    )


def resolve_operator_stage_document_workbench(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    key: str | None = None,
    run_id: str | None = None,
    attempt_number: int | None = None,
    preview_limit_bytes: int | None = None,
    source_limit_bytes: int | None = None,
    contracts_root: Path = DEFAULT_STAGE_CONTRACTS_ROOT,
) -> OperatorStageDocumentWorkbench:
    validate_operator_stage(stage)
    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")
    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )
    artifact_index = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_index is None:
        raise ValueError(
            f"Artifact index is missing for work item '{work_item}', run '{selected_run_id}', "
            f"stage '{stage}', attempt {selected_attempt}."
        )

    selected_key = (key or _preferred_workbench_document_key(artifact_index.documents)).strip()
    if not selected_key:
        raise ValueError("Workbench document key is required.")
    relative_document_path = artifact_index.documents.get(selected_key)
    if relative_document_path is None:
        supported = ", ".join(sorted(artifact_index.documents)) or "none"
        raise ValueError(
            f"Artifact document key '{selected_key}' is not available. "
            f"Available document keys: {supported}."
        )

    preview, preview_error = _try_bounded_workbench_document(
        workspace_root=workspace_root,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        key=selected_key,
        relative_document_path=relative_document_path,
        mode="preview",
        limit_bytes=preview_limit_bytes,
    )
    source, source_error = _try_bounded_workbench_document(
        workspace_root=workspace_root,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        key=selected_key,
        relative_document_path=relative_document_path,
        mode="source",
        limit_bytes=source_limit_bytes,
    )
    document = _workbench_document(
        workspace_root=workspace_root,
        key=selected_key,
        relative_document_path=relative_document_path,
        preview=preview,
        source=source,
        error=preview_error or source_error,
    )

    return OperatorStageDocumentWorkbench(
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        selected_key=selected_key,
        document=document,
        requirements=_document_requirements(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            selected_document=document,
            contracts_root=contracts_root,
        ),
        validation_results=_validation_results(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=selected_run_id,
        ),
        references=_document_references(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=selected_run_id,
            artifact_documents=artifact_index.documents,
            artifact_logs=artifact_index.logs,
        ),
        diff_inputs=_diff_inputs(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=selected_run_id,
            attempt_number=selected_attempt,
            selected_key=selected_key,
            artifact_documents=artifact_index.documents,
        ),
        versions=_document_versions(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=selected_run_id,
            attempt_number=selected_attempt,
            selected_key=selected_key,
        ),
    )


def resolve_operator_evidence_graph_view(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str | None = None,
    attempt_number: int | None = None,
) -> OperatorEvidenceGraphView:
    validate_operator_stage(stage)
    selected_run_id = run_id or latest_run_id(workspace_root=workspace_root, work_item=work_item)
    if selected_run_id is None:
        raise ValueError(f"No runs found for work item '{work_item}'.")
    selected_attempt = attempt_number or latest_attempt_number(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )
    if selected_attempt is None:
        raise ValueError(
            "No attempts found for work item "
            f"'{work_item}', run '{selected_run_id}', stage '{stage}'."
        )

    artifact_index = load_attempt_artifact_index(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
    )
    if artifact_index is None:
        return OperatorEvidenceGraphView(
            run_id=selected_run_id,
            stage=stage,
            attempt_number=selected_attempt,
            mode="flat-table",
            nodes=(),
            edges=(),
            artifact_table=_fallback_artifact_table(
                workspace_root=workspace_root,
                work_item=work_item,
                run_id=selected_run_id,
                stage=stage,
                attempt_number=selected_attempt,
            ),
            incomplete_reasons=("artifact-index-missing",),
        )

    nodes: dict[str, OperatorEvidenceGraphNode] = {}
    edges: dict[tuple[str, str, str], OperatorEvidenceGraphEdge] = {}
    incomplete_reasons: list[str] = []
    artifact_table = _artifact_table_from_index(
        workspace_root=workspace_root,
        stage=stage,
        updated_at_utc=artifact_index.updated_at_utc,
        documents=artifact_index.documents,
        logs=artifact_index.logs,
    )

    result = _try_stage_result_summary(
        workspace_root=workspace_root,
        work_item=work_item,
        stage=stage,
        run_id=selected_run_id,
        incomplete_reasons=incomplete_reasons,
    )
    metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
    )

    stage_node_id = f"stage:{stage}"
    attempt_node_id = f"attempt:{selected_attempt}"
    _add_node(
        nodes,
        OperatorEvidenceGraphNode(
            node_id=stage_node_id,
            label=stage,
            kind="stage",
            stage=stage,
            path=None,
            status=metadata.status if metadata is not None else "unknown",
            detail=f"Stage {stage}",
            byte_size=None,
            updated_at_utc=metadata.updated_at_utc if metadata is not None else None,
        ),
    )
    _add_node(
        nodes,
        OperatorEvidenceGraphNode(
            node_id=attempt_node_id,
            label=f"Attempt {selected_attempt}",
            kind="attempt",
            stage=stage,
            path=workspace_relative_path(
                workspace_root,
                run_attempt_root(
                    workspace_root=workspace_root,
                    work_item=work_item,
                    run_id=selected_run_id,
                    stage=stage,
                    attempt_number=selected_attempt,
                ),
            ),
            status="indexed",
            detail=f"Artifact index updated at {artifact_index.updated_at_utc}.",
            byte_size=None,
            updated_at_utc=artifact_index.updated_at_utc,
        ),
    )
    _add_edge(
        edges,
        OperatorEvidenceGraphEdge(
            source_id=stage_node_id,
            target_id=attempt_node_id,
            kind="attempt",
            label="has attempt",
        ),
    )

    for key, relative_path in sorted(artifact_index.documents.items()):
        node = _artifact_graph_node(
            workspace_root=workspace_root,
            node_id=f"document:{key}",
            label=key,
            kind="document",
            stage=stage,
            relative_path=relative_path,
            updated_at_utc=artifact_index.updated_at_utc,
            result_status=_document_result_status(key=key, result=result),
        )
        _add_node(nodes, node)
        _add_edge(
            edges,
            OperatorEvidenceGraphEdge(
                source_id=attempt_node_id,
                target_id=node.node_id,
                kind="artifact-index",
                label="indexes document",
            ),
        )
        if _is_stage_output_path(stage=stage, relative_path=relative_path):
            _add_edge(
                edges,
                OperatorEvidenceGraphEdge(
                    source_id=stage_node_id,
                    target_id=node.node_id,
                    kind="stage-output",
                    label="stage output",
                ),
            )

    for key, relative_path in sorted(artifact_index.logs.items()):
        node = _artifact_graph_node(
            workspace_root=workspace_root,
            node_id=f"log:{key}",
            label=key,
            kind="log",
            stage=stage,
            relative_path=relative_path,
            updated_at_utc=artifact_index.updated_at_utc,
            result_status=None,
        )
        _add_node(nodes, node)
        _add_edge(
            edges,
            OperatorEvidenceGraphEdge(
                source_id=attempt_node_id,
                target_id=node.node_id,
                kind="runtime-evidence",
                label="captures log",
            ),
        )

    if "document:validator_report" in nodes and "document:stage_result" in nodes:
        _add_edge(
            edges,
            OperatorEvidenceGraphEdge(
                source_id="document:validator_report",
                target_id="document:stage_result",
                kind="validation",
                label="validates stage result",
            ),
        )

    _add_runtime_event_nodes(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        nodes=nodes,
        edges=edges,
        incomplete_reasons=incomplete_reasons,
    )
    _add_approval_nodes(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        nodes=nodes,
        edges=edges,
        incomplete_reasons=incomplete_reasons,
    )

    mode = "graph" if edges else "flat-table"
    if mode == "flat-table" and "graph-edges-unavailable" not in incomplete_reasons:
        incomplete_reasons.append("graph-edges-unavailable")
    return OperatorEvidenceGraphView(
        run_id=selected_run_id,
        stage=stage,
        attempt_number=selected_attempt,
        mode=mode,
        nodes=tuple(sorted(nodes.values(), key=lambda node: node.node_id)),
        edges=tuple(
            sorted(
                edges.values(),
                key=lambda edge: (edge.source_id, edge.target_id, edge.kind),
            )
        ),
        artifact_table=artifact_table,
        incomplete_reasons=tuple(incomplete_reasons),
    )


def _add_node(
    nodes: dict[str, OperatorEvidenceGraphNode],
    node: OperatorEvidenceGraphNode,
) -> None:
    nodes.setdefault(node.node_id, node)


def _add_edge(
    edges: dict[tuple[str, str, str], OperatorEvidenceGraphEdge],
    edge: OperatorEvidenceGraphEdge,
) -> None:
    edges.setdefault((edge.source_id, edge.target_id, edge.kind), edge)


def _try_stage_result_summary(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    incomplete_reasons: list[str],
) -> StageResultSummary | None:
    try:
        return resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError as exc:
        incomplete_reasons.append(f"stage-result-summary-unavailable: {exc}")
        return None


def _document_result_status(*, key: str, result: StageResultSummary | None) -> str | None:
    if result is None:
        return None
    if key == "validator_report":
        return "fail" if result.validator_fail_count else "pass"
    if key == "stage_result":
        return result.final_state
    return None


def _artifact_graph_node(
    *,
    workspace_root: Path,
    node_id: str,
    label: str,
    kind: str,
    stage: str,
    relative_path: str,
    updated_at_utc: str | None,
    result_status: str | None,
) -> OperatorEvidenceGraphNode:
    path = _safe_relative_path(workspace_root, relative_path)
    exists = path is not None and path.exists()
    status = "missing"
    if exists:
        status = result_status or "present"
    return OperatorEvidenceGraphNode(
        node_id=node_id,
        label=label,
        kind=kind,
        stage=stage,
        path=workspace_relative_path(workspace_root, path) if path is not None else relative_path,
        status=status,
        detail=(
            f"Indexed {kind}: {relative_path}"
            if exists
            else f"Indexed {kind} is missing: {relative_path}"
        ),
        byte_size=path.stat().st_size if exists and path is not None else None,
        updated_at_utc=updated_at_utc,
    )


def _is_stage_output_path(*, stage: str, relative_path: str) -> bool:
    return f"/stages/{stage}/" in f"/{relative_path}"


def _attempt_root(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> Path:
    return run_attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )


def _add_attempt_file_node(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
    filename: str,
    node_id: str,
    label: str,
    kind: str,
    nodes: dict[str, OperatorEvidenceGraphNode],
    edges: dict[tuple[str, str, str], OperatorEvidenceGraphEdge],
) -> Path | None:
    path = _attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    ) / filename
    if not path.exists():
        return None
    relative_path = workspace_relative_path(workspace_root, path)
    _add_node(
        nodes,
        OperatorEvidenceGraphNode(
            node_id=node_id,
            label=label,
            kind=kind,
            stage=stage,
            path=relative_path,
            status="present",
            detail=f"Attempt {attempt_number} {kind}: {relative_path}",
            byte_size=path.stat().st_size,
            updated_at_utc=None,
        ),
    )
    _add_edge(
        edges,
        OperatorEvidenceGraphEdge(
            source_id=f"attempt:{attempt_number}",
            target_id=node_id,
            kind="runtime-evidence",
            label="captures log",
        ),
    )
    return path


def _add_runtime_event_nodes(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
    nodes: dict[str, OperatorEvidenceGraphNode],
    edges: dict[tuple[str, str, str], OperatorEvidenceGraphEdge],
    incomplete_reasons: list[str],
) -> None:
    events_path = _add_attempt_file_node(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        filename=RUN_EVENTS_JSONL_FILENAME,
        node_id="log:events_jsonl",
        label="events_jsonl",
        kind="log",
        nodes=nodes,
        edges=edges,
    )
    if events_path is None:
        return
    for line_number, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            incomplete_reasons.append(f"events-jsonl-line-{line_number}-invalid")
            continue
        if not isinstance(payload, dict):
            incomplete_reasons.append(f"events-jsonl-line-{line_number}-not-object")
            continue
        event_name = str(
            payload.get("type")
            or payload.get("event")
            or payload.get("message_type")
            or f"runtime.event.{line_number}"
        )
        node_id = f"event:{line_number}"
        _add_node(
            nodes,
            OperatorEvidenceGraphNode(
                node_id=node_id,
                label=event_name,
                kind="event",
                stage=stage,
                path=workspace_relative_path(workspace_root, events_path),
                status=str(payload.get("level") or "info").lower(),
                detail=str(payload.get("message") or payload.get("text") or payload)[:240],
                byte_size=None,
                updated_at_utc=(
                    str(payload.get("timestamp") or payload.get("time"))
                    if payload.get("timestamp") or payload.get("time")
                    else None
                ),
            ),
        )
        _add_edge(
            edges,
            OperatorEvidenceGraphEdge(
                source_id="log:events_jsonl",
                target_id=node_id,
                kind="event-entry",
                label="records event",
            ),
        )


def _add_approval_nodes(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
    nodes: dict[str, OperatorEvidenceGraphNode],
    edges: dict[tuple[str, str, str], OperatorEvidenceGraphEdge],
    incomplete_reasons: list[str],
) -> None:
    requests_path = _add_attempt_file_node(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        filename=OPERATOR_REQUESTS_FILENAME,
        node_id="log:operator_requests",
        label="operator_requests",
        kind="approval-log",
        nodes=nodes,
        edges=edges,
    )
    decisions_path = _add_attempt_file_node(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        filename=OPERATOR_DECISIONS_FILENAME,
        node_id="log:operator_decisions",
        label="operator_decisions",
        kind="approval-log",
        nodes=nodes,
        edges=edges,
    )
    if requests_path is None:
        return
    try:
        requests = load_operator_requests(requests_path)
        decisions = (
            load_operator_decisions(decisions_path)
            if decisions_path is not None
            else ()
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        incomplete_reasons.append(f"approval-log-unreadable: {exc}")
        return

    decisions_by_request = {decision.request_id: decision for decision in decisions}
    for request in requests:
        decision = decisions_by_request.get(request.id)
        status = "pending"
        if decision is not None:
            status = (
                "approved"
                if decision.is_approval
                else decision.action.value
            )
        request_node_id = f"approval-request:{request.id}"
        _add_node(
            nodes,
            OperatorEvidenceGraphNode(
                node_id=request_node_id,
                label=request.id,
                kind="approval-request",
                stage=stage,
                path=workspace_relative_path(workspace_root, requests_path),
                status=status,
                detail=f"{request.kind.value} request with {request.risk.value} risk.",
                byte_size=None,
                updated_at_utc=request.created_at_utc,
            ),
        )
        _add_edge(
            edges,
            OperatorEvidenceGraphEdge(
                source_id="log:operator_requests",
                target_id=request_node_id,
                kind="approval-request",
                label="records request",
            ),
        )
        if decision is None or decisions_path is None:
            continue
        decision_node_id = f"approval-decision:{request.id}"
        _add_node(
            nodes,
            OperatorEvidenceGraphNode(
                node_id=decision_node_id,
                label=decision.action.value,
                kind="approval-decision",
                stage=stage,
                path=workspace_relative_path(workspace_root, decisions_path),
                status=decision.action.value,
                detail=decision.reason or "Operator decision recorded.",
                byte_size=None,
                updated_at_utc=decision.created_at_utc,
            ),
        )
        _add_edge(
            edges,
            OperatorEvidenceGraphEdge(
                source_id=request_node_id,
                target_id=decision_node_id,
                kind="approval-decision",
                label="resolved by",
            ),
        )


def _artifact_table_from_index(
    *,
    workspace_root: Path,
    stage: str,
    updated_at_utc: str | None,
    documents: dict[str, str],
    logs: dict[str, str],
) -> tuple[OperatorArtifactRef, ...]:
    refs: list[OperatorArtifactRef] = []
    for kind, entries in (("document", documents), ("log", logs)):
        for key, relative_path in sorted(entries.items()):
            available = (workspace_root / relative_path).is_file()
            refs.append(
                OperatorArtifactRef(
                    stage=stage,
                    key=key,
                    kind=kind,
                    path=relative_path,
                    byte_size=_artifact_size(
                        workspace_root=workspace_root,
                        relative_path=relative_path,
                    ),
                    updated_at_utc=updated_at_utc,
                    category=operator_artifact_category(
                        key=key,
                        kind=kind,
                        path=relative_path,
                    ),
                    canonical=operator_artifact_is_canonical(
                        key=key,
                        kind=kind,
                        path=relative_path,
                    ),
                    available=available,
                    safe_key=operator_artifact_safe_key(key),
                )
            )
    return tuple(refs)


def _fallback_artifact_table(
    *,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    stage: str,
    attempt_number: int,
) -> tuple[OperatorArtifactRef, ...]:
    refs: list[OperatorArtifactRef] = []
    seen_paths: set[str] = set()
    stage_root = workspace_root / "workitems" / work_item / "stages" / stage
    attempt_root = _attempt_root(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
    )
    for path in sorted(stage_root.glob("*.md")):
        _append_fallback_artifact_ref(
            refs=refs,
            seen_paths=seen_paths,
            workspace_root=workspace_root,
            stage=stage,
            path=path,
            kind="document",
        )
    if attempt_root.exists():
        for path in sorted(
            candidate for candidate in attempt_root.iterdir() if candidate.is_file()
        ):
            if path.name == "artifact-index.json":
                continue
            _append_fallback_artifact_ref(
                refs=refs,
                seen_paths=seen_paths,
                workspace_root=workspace_root,
                stage=stage,
                path=path,
                kind="document" if path.suffix.lower() == ".md" else "log",
            )
    return tuple(refs)


def _append_fallback_artifact_ref(
    *,
    refs: list[OperatorArtifactRef],
    seen_paths: set[str],
    workspace_root: Path,
    stage: str,
    path: Path,
    kind: str,
) -> None:
    relative_path = workspace_relative_path(workspace_root, path)
    if relative_path in seen_paths:
        return
    seen_paths.add(relative_path)
    refs.append(
        OperatorArtifactRef(
            stage=stage,
            key=_artifact_key_from_filename(path),
            kind=kind,
            path=relative_path,
            byte_size=path.stat().st_size,
            updated_at_utc=None,
            category=operator_artifact_category(
                key=_artifact_key_from_filename(path),
                kind=kind,
                path=relative_path,
            ),
            canonical=operator_artifact_is_canonical(
                key=_artifact_key_from_filename(path),
                kind=kind,
                path=relative_path,
            ),
            safe_key=operator_artifact_safe_key(_artifact_key_from_filename(path)),
        )
    )


def _artifact_key_from_filename(path: Path) -> str:
    if path.suffix.lower() in {".md", ".markdown"}:
        return path.stem.replace("-", "_")
    return path.name.replace(".", "_").replace("-", "_")


def _bounded_operator_artifact_document(
    *,
    workspace_root: Path,
    run_id: str,
    stage: str,
    attempt_number: int,
    key: str,
    relative_document_path: str,
    mode: str,
    limit_bytes: int | None,
) -> OperatorArtifactDocumentView:
    relative = Path(relative_document_path)
    document_path = _safe_relative_path(workspace_root, relative_document_path)
    if document_path is None:
        if relative.is_absolute():
            raise ValueError(f"Artifact path must be workspace-relative: {relative_document_path}")
        raise ValueError(f"Artifact path escapes workspace root: {relative_document_path}")
    if not document_path.exists():
        raise ValueError(f"Artifact document file does not exist: {document_path.as_posix()}.")

    byte_size = document_path.stat().st_size
    default_bytes = (
        _DEFAULT_ARTIFACT_SOURCE_BYTES if mode == "source" else _DEFAULT_ARTIFACT_PREVIEW_BYTES
    )
    requested_bytes = min(limit_bytes or default_bytes, _MAX_ARTIFACT_READ_BYTES)
    start_byte = 0
    end_byte = min(byte_size, requested_bytes)
    with document_path.open("rb") as file_obj:
        raw_text = file_obj.read(end_byte - start_byte)
    text = _decode_bounded_utf8(raw_text, path=document_path, truncated_tail=end_byte < byte_size)

    return OperatorArtifactDocumentView(
        run_id=run_id,
        stage=stage,
        attempt_number=attempt_number,
        key=key,
        path=workspace_relative_path(workspace_root, document_path),
        text=text,
        byte_size=byte_size,
        content_type=_operator_artifact_content_type(document_path),
        mode=mode,
        start_byte=start_byte,
        end_byte=end_byte,
        requested_bytes=requested_bytes,
        max_bytes=_MAX_ARTIFACT_READ_BYTES,
        truncated=start_byte > 0 or end_byte < byte_size,
        truncated_head=start_byte > 0,
        truncated_tail=end_byte < byte_size,
    )


def _preferred_workbench_document_key(documents: dict[str, str]) -> str:
    for key in documents:
        if key not in _SYSTEM_DOCUMENT_KEYS:
            return key
    return next(iter(documents), "")


def _try_bounded_workbench_document(
    *,
    workspace_root: Path,
    run_id: str,
    stage: str,
    attempt_number: int,
    key: str,
    relative_document_path: str,
    mode: str,
    limit_bytes: int | None,
) -> tuple[OperatorArtifactDocumentView | None, str | None]:
    try:
        return (
            _bounded_operator_artifact_document(
                workspace_root=workspace_root,
                run_id=run_id,
                stage=stage,
                attempt_number=attempt_number,
                key=key,
                relative_document_path=relative_document_path,
                mode=mode,
                limit_bytes=limit_bytes,
            ),
            None,
        )
    except ValueError as exc:
        return None, str(exc)


def _workbench_document(
    *,
    workspace_root: Path,
    key: str,
    relative_document_path: str,
    preview: OperatorArtifactDocumentView | None,
    source: OperatorArtifactDocumentView | None,
    error: str | None,
) -> OperatorStageWorkbenchDocument:
    if preview is not None or source is not None:
        content = preview or source
        assert content is not None
        return OperatorStageWorkbenchDocument(
            key=key,
            path=content.path,
            status="present",
            message=None,
            content_type=content.content_type,
            byte_size=content.byte_size,
            preview=preview,
            source=source,
        )
    document_path = _safe_relative_path(workspace_root, relative_document_path)
    if error is not None and "does not exist" in error:
        status = "missing"
    elif error is not None and "not UTF-8 text" in error:
        status = "invalid"
    else:
        status = "invalid"
    return OperatorStageWorkbenchDocument(
        key=key,
        path=(
            workspace_relative_path(workspace_root, document_path)
            if document_path is not None
            else relative_document_path
        ),
        status=status,
        message=error,
        content_type=_operator_artifact_content_type(Path(relative_document_path)),
        byte_size=(
            document_path.stat().st_size
            if document_path is not None and document_path.exists()
            else None
        ),
        preview=None,
        source=None,
    )


def _document_requirements(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    selected_document: OperatorStageWorkbenchDocument,
    contracts_root: Path,
) -> tuple[OperatorStageDocumentRequirement, ...]:
    requirements: list[OperatorStageDocumentRequirement] = []
    try:
        load_stage_manifest(stage=stage, contracts_root=contracts_root)
        expected_outputs = resolve_expected_output_documents(
            stage=stage,
            work_item=work_item,
            workspace_root=workspace_root,
            contracts_root=contracts_root,
        )
    except StageManifestLoadError as exc:
        return (
            OperatorStageDocumentRequirement(
                kind="stage-contract",
                label=stage,
                path=None,
                status="invalid",
                source=str(exc),
            ),
        )

    for expected_output in expected_outputs:
        requirements.append(
            OperatorStageDocumentRequirement(
                kind="required-output",
                label=expected_output.name,
                path=workspace_relative_path(workspace_root, expected_output),
                status="satisfied" if expected_output.exists() else "missing",
                source="stage-contract",
            )
        )

    requirements.extend(
        _section_requirements(
            stage=stage,
            selected_document=selected_document,
            contracts_root=contracts_root,
        )
    )
    return tuple(requirements)


def _section_requirements(
    *,
    stage: str,
    selected_document: OperatorStageWorkbenchDocument,
    contracts_root: Path,
) -> tuple[OperatorStageDocumentRequirement, ...]:
    document_name = Path(selected_document.path).name
    sections: list[tuple[str, str]] = []
    document_contract_path = (
        resolve_resource_layout_from_contracts_root(contracts_root).document_contracts_root
        / document_name
    )
    if document_contract_path.exists():
        for section in extract_required_sections_from_document_contract(
            document_contract_path.read_text(encoding="utf-8")
        ):
            sections.append((section, "document-contract"))
    stage_contract = stage_contract_path(stage, contracts_root)
    if stage_contract.exists():
        stage_requirements = extract_stage_required_heading_map(
            stage_contract.read_text(encoding="utf-8")
        )
        for section in stage_requirements.get(document_name, ()):
            sections.append((section, "stage-contract"))

    if not sections:
        return ()

    headings = (
        {
            normalize_heading(heading.title)
            for heading in extract_markdown_headings(selected_document.source.text)
        }
        if selected_document.source is not None
        else set()
    )
    truncated = bool(selected_document.source and selected_document.source.truncated)
    requirements: list[OperatorStageDocumentRequirement] = []
    for section, source in dict.fromkeys(sections):
        normalized = normalize_heading(section)
        status = (
            "satisfied"
            if normalized in headings
            else "unknown"
            if selected_document.status != "present" or truncated
            else "missing"
        )
        requirements.append(
            OperatorStageDocumentRequirement(
                kind="required-section",
                label=section,
                path=selected_document.path,
                status=status,
                source=source,
            )
        )
    return tuple(requirements)


def _validation_results(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
) -> tuple[OperatorStageDocumentValidationResult, ...]:
    try:
        result = resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError as exc:
        return (
            OperatorStageDocumentValidationResult(
                label="stage-result",
                status="missing",
                path=None,
                detail=str(exc),
            ),
        )
    status = "pass" if result.validator_fail_count == 0 else "fail"
    return (
        OperatorStageDocumentValidationResult(
            label="validator-report",
            status=status,
            path=result.validator_report_path,
            detail=(
                f"{result.validator_pass_count} passing, "
                f"{result.validator_fail_count} failing validator result(s)"
            ),
        ),
        OperatorStageDocumentValidationResult(
            label="stage-result",
            status=result.final_state,
            path=f"workitems/{work_item}/stages/{stage}/stage-result.md",
            detail=(
                f"Stage finished as {result.final_state} "
                f"after {result.attempt_count} attempt(s)."
            ),
        ),
    )


def _document_references(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    artifact_documents: dict[str, str],
    artifact_logs: dict[str, str],
) -> tuple[OperatorStageDocumentReference, ...]:
    refs: list[OperatorStageDocumentReference] = [
        OperatorStageDocumentReference(
            label=key,
            kind="document",
            path=path,
            stage=stage,
            category=operator_artifact_category(key=key, kind="document", path=path),
        )
        for key, path in sorted(artifact_documents.items())
    ]
    refs.extend(
        OperatorStageDocumentReference(
            label=key,
            kind="log",
            path=path,
            stage=stage,
            category=operator_artifact_category(key=key, kind="log", path=path),
        )
        for key, path in sorted(artifact_logs.items())
    )
    try:
        result = resolve_stage_result_summary(
            workspace_root=workspace_root,
            work_item=work_item,
            stage=stage,
            run_id=run_id,
        )
    except ValueError:
        return tuple(refs)
    refs.extend(
        OperatorStageDocumentReference(
            label=Path(path).name,
            kind="repair",
            path=path,
            stage=stage,
            category=operator_artifact_category(
                key=Path(path).stem,
                kind="repair",
                path=path,
            ),
        )
        for path in result.repair_output_paths
    )
    return tuple(refs)


def _diff_inputs(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    attempt_number: int,
    selected_key: str,
    artifact_documents: dict[str, str],
) -> tuple[OperatorStageDocumentDiffInput, ...]:
    inputs = [
        OperatorStageDocumentDiffInput(
            label=f"Current {key}",
            kind="current-document",
            key=key,
            path=path,
            attempt_number=attempt_number,
        )
        for key, path in sorted(artifact_documents.items())
        if key != selected_key
    ]
    for previous_attempt in range(attempt_number - 1, 0, -1):
        previous_index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=previous_attempt,
        )
        if previous_index is None:
            continue
        previous_path = previous_index.documents.get(selected_key)
        if previous_path is None:
            continue
        inputs.append(
            OperatorStageDocumentDiffInput(
                label=f"Attempt {previous_attempt} {selected_key}",
                kind="previous-version",
                key=selected_key,
                path=previous_path,
                attempt_number=previous_attempt,
            )
        )
        break
    return tuple(inputs)


def _document_versions(
    *,
    workspace_root: Path,
    work_item: str,
    stage: str,
    run_id: str,
    attempt_number: int,
    selected_key: str,
) -> tuple[OperatorStageDocumentVersion, ...]:
    stage_metadata = load_stage_metadata(
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        stage=stage,
    )
    trigger_by_attempt = (
        {
            entry.attempt_number: entry.trigger
            for entry in stage_metadata.repair_history
        }
        if stage_metadata is not None
        else {}
    )
    versions: list[OperatorStageDocumentVersion] = []
    for candidate_attempt in range(1, attempt_number + 1):
        artifact_index = load_attempt_artifact_index(
            workspace_root=workspace_root,
            work_item=work_item,
            run_id=run_id,
            stage=stage,
            attempt_number=candidate_attempt,
        )
        if artifact_index is None:
            continue
        path = artifact_index.documents.get(selected_key)
        if path is None:
            continue
        source = trigger_by_attempt.get(candidate_attempt)
        if source is None:
            source = "model-authored" if selected_key not in _SYSTEM_DOCUMENT_KEYS else "system"
        versions.append(
            OperatorStageDocumentVersion(
                label=f"Attempt {candidate_attempt}",
                key=selected_key,
                path=path,
                run_id=run_id,
                attempt_number=candidate_attempt,
                updated_at_utc=artifact_index.updated_at_utc,
                source=source,
            )
        )
    return tuple(versions)


def _operator_artifact_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".markdown"}:
        return "text/markdown"
    if suffix in {".txt", ".log", ".json", ".jsonl", ".yaml", ".yml", ".toml"}:
        return "text/plain"
    return "application/octet-stream"


def _decode_bounded_utf8(raw_text: bytes, *, path: Path, truncated_tail: bool) -> str:
    try:
        return raw_text.decode("utf-8")
    except UnicodeDecodeError as exc:
        if truncated_tail and exc.reason == "unexpected end of data":
            return raw_text[: exc.start].decode("utf-8")
        raise ValueError(f"Artifact document is not UTF-8 text: {path.as_posix()}.") from exc


def _safe_relative_path(workspace_root: Path, relative_path: str) -> Path | None:
    relative = Path(relative_path)
    if relative.is_absolute():
        return None
    resolved_workspace = workspace_root.resolve(strict=False)
    resolved_path = (workspace_root / relative).resolve(strict=False)
    if not resolved_path.is_relative_to(resolved_workspace):
        return None
    return resolved_path


def _artifact_size(*, workspace_root: Path, relative_path: str) -> int | None:
    path = _safe_relative_path(workspace_root, relative_path)
    if path is None or not path.exists():
        return None
    return path.stat().st_size


__all__ = [
    "_artifact_size",
    "_bounded_operator_artifact_document",
    "_safe_relative_path",
    "resolve_operator_artifact_document_content",
    "resolve_operator_artifacts_view",
    "resolve_operator_evidence_graph_view",
    "resolve_operator_stage_document_workbench",
]
