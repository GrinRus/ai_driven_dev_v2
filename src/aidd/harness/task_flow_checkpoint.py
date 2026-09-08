"""Fail-closed task-aware evidence for installed live-flow runs.

The live harness owns this artifact.  It consumes the task read boundary returned by the
installed operator surface and only reads target files that are already durable.  It does not
execute task transitions or reimplement eligibility decisions in the target workspace.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

TASK_FLOW_CHECKPOINT_SCHEMA_VERSION = 1
TASK_FLOW_CHECKPOINT_JSON_FILENAME = "task-flow-checkpoint.json"
TASK_FLOW_CHECKPOINT_MARKDOWN_FILENAME = "task-flow-checkpoint.md"

TaskFlowCheckpointClassification = Literal["pass", "fail", "blocked"]


@dataclass(frozen=True, slots=True)
class TaskFlowCheckpointResult:
    classification: TaskFlowCheckpointClassification
    payload: dict[str, object]
    json_path: Path
    markdown_path: Path


@dataclass(frozen=True, slots=True)
class _CheckpointPaths:
    tasklist: Path
    ledger: Path
    stage_metadata: Path
    validator_report: Path
    stage_result: Path


@dataclass(frozen=True, slots=True)
class _CheckpointState:
    stage: str
    workspace_root: Path
    paths: _CheckpointPaths
    tasklist_sha: str | None
    ledger: dict[str, object] | None
    stage_metadata: dict[str, object] | None
    stage_status: str | None
    validator_verdict: str | None
    stage_result_status: str | None
    model: dict[str, object]
    public_task_view_available: bool
    model_tasks: list[dict[str, object]]
    authored_ids: list[str]
    authored_dependencies: dict[str, tuple[str, ...]]


def _sha256(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _read_json(path: Path) -> dict[str, object] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _validator_verdict(text: str) -> str | None:
    match = re.search(r"(?im)^\s*-\s*Verdict:\s*`?(pass|fail)\b", text)
    return match.group(1).lower() if match is not None else None


def _stage_result_status(text: str) -> str | None:
    section = re.search(r"(?ims)^##\s+Status\s*$\n(.*?)(?=^##\s+|\Z)", text)
    if section is None:
        return None
    match = re.search(
        r"(?im)^\s*-\s*(?:Status\s*:\s*)?`?(succeeded|failed|blocked|needs-input)\b",
        section.group(1),
    )
    return match.group(1).lower() if match is not None else None


def _tasklist_cards(text: str) -> tuple[list[str], dict[str, tuple[str, ...]]]:
    """Extract the stable task order and dependency section from rich tasklist Markdown."""

    ids = [match.group(1) for match in re.finditer(r"(?m)^###\s+([A-Za-z0-9][\w.-]*)\b", text)]
    dependencies: dict[str, tuple[str, ...]] = {}
    dependency_heading = re.search(r"(?im)^##\s+Dependencies\s*$", text)
    if dependency_heading is not None:
        section = text[dependency_heading.end() :]
        section = re.split(r"(?m)^##\s+", section, maxsplit=1)[0]
        for line in section.splitlines():
            match = re.match(r"^\s*[-*]\s*([A-Za-z0-9][\w.-]*)\s*:\s*(.*)$", line)
            if match is None:
                continue
            raw_dependencies = match.group(2).strip()
            # The tasklist contract places an optional explanatory rationale after an em/en
            # dash (for example, ``T1: none — establishes the runtime behavior``).  Only the
            # machine-readable clause before that separator is part of the dependency graph;
            # parsing every word in the rationale turns ordinary prose into fake task ids and
            # causes a false dependency-drift finding at the installed public boundary.
            dependency_clause = re.split(r"\s+[—–]\s+", raw_dependencies, maxsplit=1)[0].strip()
            normalized_clause = dependency_clause.rstrip(".,;:!?)]}").strip()
            if not normalized_clause or normalized_clause.lower() == "none":
                dependencies[match.group(1)] = ()
            else:
                parsed_dependencies: list[str] = []
                for item in re.findall(r"[A-Za-z0-9][\w.-]*", dependency_clause):
                    normalized_item = item.rstrip(".,;:!?)]}")
                    if normalized_item and normalized_item.lower() != "none":
                        parsed_dependencies.append(normalized_item)
                dependencies[match.group(1)] = tuple(parsed_dependencies)
    return ids, dependencies


def _task_items(model: dict[str, object]) -> list[dict[str, object]]:
    raw = model.get("tasks")
    return [item for item in raw if isinstance(item, dict)] if isinstance(raw, list) else []


def _literal_blocker(model: dict[str, object]) -> str | None:
    selected = model.get("next_ready")
    if isinstance(selected, dict):
        raw_reason = selected.get("reason")
        if isinstance(raw_reason, str) and raw_reason.strip():
            return raw_reason.strip()
    for key in ("review_blocker", "blocker"):
        raw = model.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    return None


def _evidence_links(task: dict[str, object]) -> list[str]:
    raw = task.get("evidence_links")
    return [item for item in raw if isinstance(item, str) and item] if isinstance(raw, list) else []


def _dependencies(task: dict[str, object]) -> tuple[str, ...]:
    raw = task.get("dependencies")
    return tuple(item for item in raw if isinstance(item, str)) if isinstance(raw, list) else ()


def _attempt_count(task: dict[str, object]) -> int:
    raw = task.get("attempt_count")
    if isinstance(raw, int) and raw >= 0:
        return raw
    attempts = task.get("attempts")
    return len(attempts) if isinstance(attempts, list) else 0


def _terminal_evidence_valid(
    *,
    task: dict[str, object],
    workspace_root: Path,
) -> bool:
    if str(task.get("status", "")) != "succeeded":
        return True
    links = _evidence_links(task)
    if not links:
        return False
    # Evidence links are workspace-relative paths emitted by the public read model.  A link
    # must resolve inside the authorized workspace and point at a retained artifact.
    for link in links:
        candidate = (workspace_root / link).resolve(strict=False)
        try:
            candidate.relative_to(workspace_root.resolve(strict=False))
        except ValueError:
            return False
        if candidate.exists():
            return True
    return False


def _checkpoint_paths(
    workspace_root: Path, work_item: str, run_id: str, stage: str
) -> _CheckpointPaths:
    run_root = workspace_root / "reports" / "runs" / work_item / run_id
    tasklist = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    stage_documents = workspace_root / "workitems" / work_item / "stages" / stage
    return _CheckpointPaths(
        tasklist=tasklist,
        ledger=run_root / "stages" / "implement" / "task-ledger.json",
        stage_metadata=run_root / "stages" / stage / "stage-metadata.json",
        validator_report=stage_documents / "validator-report.md",
        stage_result=stage_documents / "stage-result.md",
    )


def _load_checkpoint_state(
    *,
    stage: str,
    workspace_root: Path,
    work_item: str,
    run_id: str,
    task_view: dict[str, object] | None,
) -> _CheckpointState:
    paths = _checkpoint_paths(workspace_root, work_item, run_id, stage)
    tasklist_sha = _sha256(paths.tasklist)
    ledger = _read_json(paths.ledger)
    stage_metadata = _read_json(paths.stage_metadata)
    stage_status = (
        str(stage_metadata.get("status"))
        if stage_metadata is not None and stage_metadata.get("status") is not None
        else None
    )
    validator_verdict = _validator_verdict(_read_text(paths.validator_report))
    stage_result_status = _stage_result_status(_read_text(paths.stage_result))
    model = task_view or {}
    authored_ids, authored_dependencies = _tasklist_cards(
        _read_text(paths.tasklist)
    )
    return _CheckpointState(
        stage=stage,
        workspace_root=workspace_root,
        paths=paths,
        tasklist_sha=tasklist_sha,
        ledger=ledger,
        stage_metadata=stage_metadata,
        stage_status=stage_status,
        validator_verdict=validator_verdict,
        stage_result_status=stage_result_status,
        model=model,
        public_task_view_available=task_view is not None,
        model_tasks=_task_items(model),
        authored_ids=authored_ids,
        authored_dependencies=authored_dependencies,
    )


def _collect_basic_findings(state: _CheckpointState) -> list[str]:
    findings: list[str] = []
    if state.tasklist_sha is None:
        findings.append("missing-published-tasklist")
    if not state.authored_ids:
        findings.append("tasklist-has-no-authored-task-ids")
    if not state.public_task_view_available:
        findings.append("public-task-read-boundary-unavailable")
    if not state.model_tasks:
        findings.append("public-task-read-boundary-has-no-tasks")
    model_ids = [str(item.get("id")) for item in state.model_tasks]
    if state.authored_ids and model_ids != state.authored_ids:
        findings.append("public-task-order-or-identity-drift")
    for item in state.model_tasks:
        task_id = str(item.get("id", ""))
        expected = state.authored_dependencies.get(task_id)
        actual = _dependencies(item)
        if expected is not None and actual != expected:
            findings.append(f"dependency-drift:{task_id}")
    return findings


def _collect_hash_findings(state: _CheckpointState) -> list[str]:
    findings: list[str] = []
    source_hash = state.ledger.get("source_tasklist_sha256") if state.ledger is not None else None
    public_tasklist = state.model.get("tasklist")
    public_tasklist = public_tasklist if isinstance(public_tasklist, dict) else {}
    public_published_hash = public_tasklist.get("published_sha256")
    public_ledger_hash = public_tasklist.get("ledger_sha256")
    if (
        isinstance(public_published_hash, str)
        and state.tasklist_sha
        and public_published_hash != state.tasklist_sha
    ):
        findings.append("public-tasklist-hash-mismatch")
    if (
        isinstance(public_ledger_hash, str)
        and state.tasklist_sha
        and public_ledger_hash != state.tasklist_sha
    ):
        findings.append("public-ledger-hash-mismatch")
    if isinstance(source_hash, str) and state.tasklist_sha and source_hash != state.tasklist_sha:
        findings.append("durable-ledger-hash-mismatch")
    if state.stage == "implement" and state.ledger is None:
        findings.append("missing-durable-task-ledger")
    return findings


def _collect_lifecycle_findings(state: _CheckpointState) -> tuple[list[str], list[str]]:
    failed_task_ids = [
        str(item.get("id"))
        for item in state.model_tasks
        if str(item.get("status", "")) in {"failed", "repair-exhausted"}
    ]
    findings: list[str] = []
    blocked_stage = state.stage_status == "blocked" or state.stage_result_status == "blocked"
    if state.stage == "implement" and blocked_stage and failed_task_ids:
        findings.append(
            "implementation-status-drift:failed-task-stage-blocked:"
            + ",".join(failed_task_ids)
        )
    if state.stage == "implement" and state.validator_verdict == "fail" and blocked_stage:
        findings.append("implementation-status-drift:validator-fail-stage-blocked")
    if (
        state.stage == "implement"
        and state.validator_verdict == "fail"
        and state.stage_result_status == "succeeded"
    ):
        findings.append("implementation-status-drift:validator-fail-stage-succeeded")
    return findings, failed_task_ids


def _collect_progression_findings(state: _CheckpointState) -> list[str]:
    findings: list[str] = []
    ready_ids = [str(item.get("id")) for item in state.model_tasks if item.get("ready") is True]
    expected_next = ready_ids[0] if ready_ids else None
    next_ready = state.model.get("next_ready_task")
    if next_ready != expected_next:
        findings.append("invalid-core-next-ready-selection")
    if next_ready is not None and next_ready not in {
        str(item.get("id")) for item in state.model_tasks
    }:
        findings.append("next-ready-task-is-unknown")

    finalization = state.model.get("finalization")
    finalization = finalization if isinstance(finalization, dict) else {}
    finalization_status = str(finalization.get("status", "pending"))
    finalization_evidence = finalization.get("latest_attempt_path")
    if finalization_status == "succeeded":
        if not state.model.get("all_succeeded"):
            findings.append("premature-aggregate-finalization")
        if not isinstance(finalization_evidence, str) or not finalization_evidence:
            findings.append("missing-finalization-evidence-link")
        elif not (
            state.workspace_root / finalization_evidence / "finalization-state.json"
        ).exists():
            findings.append("missing-finalization-evidence")
    if state.stage == "tasklist" and finalization_status == "succeeded":
        findings.append("premature-aggregate-finalization")
    review = state.model.get("review_eligibility")
    review = review if isinstance(review, dict) else {}
    review_eligible = review.get("eligible") is True or state.model.get("review_eligible") is True
    if review_eligible != (finalization_status == "succeeded"):
        findings.append("review-eligibility-disagrees-with-aggregate-finalization")
    return findings


def _build_task_payloads(state: _CheckpointState) -> tuple[list[dict[str, object]], list[str]]:
    tasks: list[dict[str, object]] = []
    findings: list[str] = []
    for item in state.model_tasks:
        task_id = str(item.get("id", ""))
        links = _evidence_links(item)
        terminal_evidence = links[-1] if links else None
        tasks.append(
            {
                "id": task_id,
                "order": len(tasks),
                "dependencies": list(_dependencies(item)),
                "status": str(item.get("status", "unknown")),
                "attempt_count": _attempt_count(item),
                "terminal_evidence": terminal_evidence,
            }
        )
        if state.stage == "implement" and not _terminal_evidence_valid(
            task=item,
            workspace_root=state.workspace_root,
        ):
            findings.append(f"missing-terminal-task-evidence:{task_id}")
    return tasks, findings


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _build_checkpoint_payload(
    *,
    state: _CheckpointState,
    scenario_id: str,
    work_item: str,
    run_id: str,
    runtime_id: str,
    aidd_revision: str | None,
    target_revision: str | None,
    public_surface: dict[str, object] | None,
    tasks: list[dict[str, object]],
    failed_task_ids: list[str],
    findings: list[str],
) -> dict[str, object]:
    finalization = _mapping(state.model.get("finalization"))
    finalization_status = str(finalization.get("status", "pending"))
    finalization_evidence = finalization.get("latest_attempt_path")
    review = _mapping(state.model.get("review_eligibility"))
    review_eligible = review.get("eligible") is True or state.model.get("review_eligible") is True
    public_tasklist = _mapping(state.model.get("tasklist"))
    public_ledger_hash = public_tasklist.get("ledger_sha256")
    source_hash = (
        state.ledger.get("source_tasklist_sha256") if state.ledger is not None else None
    )
    return {
        "schema_version": TASK_FLOW_CHECKPOINT_SCHEMA_VERSION,
        "created_at_utc": datetime.now(UTC).replace(microsecond=0).isoformat().replace(
            "+00:00", "Z"
        ),
        "classification": "pass" if not findings else "fail",
        "stage": state.stage,
        "identity": {
            "scenario_id": scenario_id,
            "work_item": work_item,
            "run_id": run_id,
            "runtime_id": runtime_id,
            "aidd_revision": aidd_revision or "unknown",
            "target_revision": target_revision or "unknown",
        },
        "tasklist": {
            "path": state.paths.tasklist.as_posix(),
            "sha256": state.tasklist_sha,
            "authored_task_ids": state.authored_ids,
            "authored_dependencies": {
                key: list(value) for key, value in state.authored_dependencies.items()
            },
            "hash_matches": not any("hash" in finding for finding in findings),
        },
        "ledger": {
            "path": state.paths.ledger.as_posix() if state.ledger is not None else None,
            "schema_version": state.ledger.get("schema_version")
            if state.ledger is not None
            else None,
            "source_tasklist_sha256": source_hash or public_ledger_hash,
        },
        "stage_lifecycle": {
            "path": state.paths.stage_metadata.as_posix()
            if state.stage_metadata is not None
            else None,
            "status": state.stage_status,
            "validator_report_path": state.paths.validator_report.as_posix()
            if state.validator_verdict is not None
            else None,
            "validator_verdict": state.validator_verdict,
            "stage_result_path": state.paths.stage_result.as_posix()
            if state.stage_result_status is not None
            else None,
            "stage_result_status": state.stage_result_status,
            "failed_task_ids": failed_task_ids,
        },
        "tasks": tasks,
        "next_ready_task": state.model.get("next_ready_task"),
        "blocker": _literal_blocker(state.model),
        "finalization": {
            "status": finalization_status,
            "attempt_count": finalization.get("attempt_count", 0),
            "evidence": (
                f"{finalization_evidence}/finalization-state.json"
                if isinstance(finalization_evidence, str) and finalization_evidence
                else None
            ),
        },
        "review_eligibility": {
            "eligible": review_eligible,
            "blocker": review.get("reason") or state.model.get("review_blocker"),
        },
        "findings": findings,
        "collection": {
            "source": "installed-public-ui-api-and-authorized-durable-artifacts",
            "public_surface": public_surface or {"status": "not-recorded"},
            "mutated_target": False,
        },
        "public_projection": state.model,
    }


def _write_checkpoint_artifacts(
    *, payload: dict[str, object], output_root: Path
) -> tuple[Path, Path]:
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / TASK_FLOW_CHECKPOINT_JSON_FILENAME
    markdown_path = output_root / TASK_FLOW_CHECKPOINT_MARKDOWN_FILENAME
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    tmp_json = json_path.with_suffix(f".{json_path.suffix.lstrip('.')}.tmp")
    tmp_json.write_text(encoded, encoding="utf-8")
    tmp_json.replace(json_path)
    tmp_markdown = markdown_path.with_suffix(f".{markdown_path.suffix.lstrip('.')}.tmp")
    tmp_markdown.write_text(_render_markdown(payload), encoding="utf-8")
    tmp_markdown.replace(markdown_path)
    return json_path, markdown_path


def _render_markdown(payload: dict[str, object]) -> str:
    identity = payload.get("identity")
    identity = identity if isinstance(identity, dict) else {}
    tasklist = payload.get("tasklist")
    tasklist = tasklist if isinstance(tasklist, dict) else {}
    ledger = payload.get("ledger")
    ledger = ledger if isinstance(ledger, dict) else {}
    finalization = payload.get("finalization")
    finalization = finalization if isinstance(finalization, dict) else {}
    lifecycle = payload.get("stage_lifecycle")
    lifecycle = lifecycle if isinstance(lifecycle, dict) else {}
    review = payload.get("review_eligibility")
    review = review if isinstance(review, dict) else {}
    lines = [
        "# Task-Flow Checkpoint",
        "",
        f"- Schema: `v{payload.get('schema_version', 'unknown')}`",
        f"- Classification: `{payload.get('classification', 'unknown')}`",
        f"- Snapshot stage: `{payload.get('stage', 'unknown')}`",
        "",
        "## Identity",
        "",
        f"- Scenario: `{identity.get('scenario_id', 'unknown')}`",
        f"- Work Item: `{identity.get('work_item', 'unknown')}`",
        f"- Run: `{identity.get('run_id', 'unknown')}`",
        f"- Runtime: `{identity.get('runtime_id', 'unknown')}`",
        f"- AIDD revision: `{identity.get('aidd_revision', 'unknown')}`",
        f"- Target revision: `{identity.get('target_revision', 'unknown')}`",
        "",
        "## Tasklist and Ledger",
        "",
        f"- Published tasklist: `{tasklist.get('path', 'missing')}`",
        f"- Tasklist SHA-256: `{tasklist.get('sha256', 'missing')}`",
        f"- Ledger path: `{ledger.get('path', 'not-materialized')}`",
        f"- Ledger schema: `{ledger.get('schema_version', 'unknown')}`",
        f"- Ledger source hash: `{ledger.get('source_tasklist_sha256', 'missing')}`",
        f"- Hashes match: `{tasklist.get('hash_matches', False)}`",
        f"- Stage metadata: `{lifecycle.get('path', 'missing')}`",
        f"- Stage lifecycle status: `{lifecycle.get('status', 'unknown')}`",
        f"- Failed task ids: `{', '.join(lifecycle.get('failed_task_ids', [])) or 'none'}`",
        "",
        "## Tasks",
        "",
    ]
    tasks = payload.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        lines.append("- none")
    else:
        for task in tasks:
            if not isinstance(task, dict):
                continue
            evidence = task.get("terminal_evidence") or "none"
            dependencies = ", ".join(task.get("dependencies", [])) or "none"
            lines.append(
                f"- `{task.get('id', 'unknown')}` status=`{task.get('status', 'unknown')}` "
                f"attempts=`{task.get('attempt_count', 0)}` deps=`{dependencies}` "
                f"evidence=`{evidence}`"
            )
    lines.extend(
        (
            "",
            "## Progression",
            "",
            f"- Core-selected next-ready task: `{payload.get('next_ready_task') or 'none'}`",
            f"- Blocker: {payload.get('blocker') or 'none'}",
            f"- Aggregate finalization: `{finalization.get('status', 'unknown')}`",
            f"- Finalization attempts: `{finalization.get('attempt_count', 0)}`",
            f"- Finalization evidence: `{finalization.get('evidence') or 'none'}`",
            f"- Review eligible: `{review.get('eligible', False)}`",
            f"- Review blocker: {review.get('blocker') or 'none'}",
            "",
            "## Fail-Closed Findings",
            "",
        )
    )
    findings = payload.get("findings")
    if not isinstance(findings, list) or not findings:
        lines.append("- none")
    else:
        lines.extend(f"- `{item}`" for item in findings)
    return "\n".join(lines).rstrip() + "\n"


def build_task_flow_checkpoint(
    *,
    scenario_id: str,
    work_item: str,
    run_id: str,
    runtime_id: str,
    aidd_revision: str | None,
    target_revision: str | None,
    stage: str,
    workspace_root: Path,
    output_root: Path,
    task_view: dict[str, object] | None,
    public_surface: dict[str, object] | None = None,
) -> TaskFlowCheckpointResult:
    """Validate one public task projection and write an atomic checkpoint bundle."""

    state = _load_checkpoint_state(
        stage=stage,
        workspace_root=workspace_root,
        work_item=work_item,
        run_id=run_id,
        task_view=task_view,
    )
    findings = _collect_basic_findings(state)
    findings.extend(_collect_hash_findings(state))
    lifecycle_findings, failed_task_ids = _collect_lifecycle_findings(state)
    findings.extend(lifecycle_findings)
    findings.extend(_collect_progression_findings(state))
    tasks, task_findings = _build_task_payloads(state)
    findings.extend(task_findings)
    payload = _build_checkpoint_payload(
        state=state,
        scenario_id=scenario_id,
        work_item=work_item,
        run_id=run_id,
        runtime_id=runtime_id,
        aidd_revision=aidd_revision,
        target_revision=target_revision,
        public_surface=public_surface,
        tasks=tasks,
        failed_task_ids=failed_task_ids,
        findings=findings,
    )
    json_path, markdown_path = _write_checkpoint_artifacts(
        payload=payload,
        output_root=output_root,
    )
    classification = cast(TaskFlowCheckpointClassification, payload["classification"])
    return TaskFlowCheckpointResult(
        classification=classification,
        payload=payload,
        json_path=json_path,
        markdown_path=markdown_path,
    )


__all__ = [
    "TASK_FLOW_CHECKPOINT_JSON_FILENAME",
    "TASK_FLOW_CHECKPOINT_MARKDOWN_FILENAME",
    "TASK_FLOW_CHECKPOINT_SCHEMA_VERSION",
    "TaskFlowCheckpointResult",
    "build_task_flow_checkpoint",
]
