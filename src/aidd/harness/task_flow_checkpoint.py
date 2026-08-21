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
from typing import Literal

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


def _render_markdown(payload: dict[str, object]) -> str:
    identity = payload.get("identity")
    identity = identity if isinstance(identity, dict) else {}
    tasklist = payload.get("tasklist")
    tasklist = tasklist if isinstance(tasklist, dict) else {}
    ledger = payload.get("ledger")
    ledger = ledger if isinstance(ledger, dict) else {}
    finalization = payload.get("finalization")
    finalization = finalization if isinstance(finalization, dict) else {}
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

    tasklist_path = (
        workspace_root
        / "workitems"
        / work_item
        / "stages"
        / "tasklist"
        / "output"
        / "tasklist.md"
    )
    ledger_path = (
        workspace_root
        / "reports"
        / "runs"
        / work_item
        / run_id
        / "stages"
        / "implement"
        / "task-ledger.json"
    )
    tasklist_sha = _sha256(tasklist_path)
    tasklist_text = None
    if tasklist_path.exists():
        try:
            tasklist_text = tasklist_path.read_text(encoding="utf-8")
        except OSError:
            tasklist_text = None
    model = task_view or {}
    ledger = _read_json(ledger_path)
    model_tasks = _task_items(model)
    authored_ids, authored_dependencies = _tasklist_cards(tasklist_text or "")
    findings: list[str] = []
    if tasklist_sha is None:
        findings.append("missing-published-tasklist")
    if not authored_ids:
        findings.append("tasklist-has-no-authored-task-ids")
    if task_view is None:
        findings.append("public-task-read-boundary-unavailable")
    if not model_tasks:
        findings.append("public-task-read-boundary-has-no-tasks")
    model_ids = [str(item.get("id")) for item in model_tasks]
    if authored_ids and model_ids != authored_ids:
        findings.append("public-task-order-or-identity-drift")
    for item in model_tasks:
        task_id = str(item.get("id", ""))
        expected = authored_dependencies.get(task_id)
        actual = _dependencies(item)
        if expected is not None and actual != expected:
            findings.append(f"dependency-drift:{task_id}")

    source_hash = ledger.get("source_tasklist_sha256") if ledger is not None else None
    public_tasklist = model.get("tasklist")
    public_tasklist = public_tasklist if isinstance(public_tasklist, dict) else {}
    public_published_hash = public_tasklist.get("published_sha256")
    public_ledger_hash = public_tasklist.get("ledger_sha256")
    if (
        isinstance(public_published_hash, str)
        and tasklist_sha
        and public_published_hash != tasklist_sha
    ):
        findings.append("public-tasklist-hash-mismatch")
    if (
        isinstance(public_ledger_hash, str)
        and tasklist_sha
        and public_ledger_hash != tasklist_sha
    ):
        findings.append("public-ledger-hash-mismatch")
    if isinstance(source_hash, str) and tasklist_sha and source_hash != tasklist_sha:
        findings.append("durable-ledger-hash-mismatch")
    if stage == "implement" and ledger is None:
        findings.append("missing-durable-task-ledger")

    ready_ids = [str(item.get("id")) for item in model_tasks if item.get("ready") is True]
    expected_next = ready_ids[0] if ready_ids else None
    next_ready = model.get("next_ready_task")
    if next_ready != expected_next:
        findings.append("invalid-core-next-ready-selection")
    if next_ready is not None and next_ready not in model_ids:
        findings.append("next-ready-task-is-unknown")

    finalization = model.get("finalization")
    finalization = finalization if isinstance(finalization, dict) else {}
    finalization_status = str(finalization.get("status", "pending"))
    finalization_attempt_count = finalization.get("attempt_count", 0)
    finalization_evidence = finalization.get("latest_attempt_path")
    if finalization_status == "succeeded":
        if not model.get("all_succeeded"):
            findings.append("premature-aggregate-finalization")
        if not isinstance(finalization_evidence, str) or not finalization_evidence:
            findings.append("missing-finalization-evidence-link")
        elif not (
            workspace_root / finalization_evidence / "finalization-state.json"
        ).exists():
            findings.append("missing-finalization-evidence")
    if stage == "tasklist" and finalization_status == "succeeded":
        findings.append("premature-aggregate-finalization")
    review = model.get("review_eligibility")
    review = review if isinstance(review, dict) else {}
    review_eligible = review.get("eligible") is True or model.get("review_eligible") is True
    durable_aggregate_succeeded = finalization_status == "succeeded"
    if review_eligible != durable_aggregate_succeeded:
        findings.append("review-eligibility-disagrees-with-aggregate-finalization")

    tasks: list[dict[str, object]] = []
    for item in model_tasks:
        task_id = str(item.get("id", ""))
        links = _evidence_links(item)
        terminal_evidence = links[-1] if links else None
        task_payload: dict[str, object] = {
            "id": task_id,
            "order": len(tasks),
            "dependencies": list(_dependencies(item)),
            "status": str(item.get("status", "unknown")),
            "attempt_count": _attempt_count(item),
            "terminal_evidence": terminal_evidence,
        }
        tasks.append(task_payload)
        if stage == "implement" and not _terminal_evidence_valid(
            task=item,
            workspace_root=workspace_root,
        ):
            findings.append(f"missing-terminal-task-evidence:{task_id}")

    classification: TaskFlowCheckpointClassification = "pass" if not findings else "fail"
    payload: dict[str, object] = {
        "schema_version": TASK_FLOW_CHECKPOINT_SCHEMA_VERSION,
        "created_at_utc": (
            datetime.now(UTC)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
        "classification": classification,
        "stage": stage,
        "identity": {
            "scenario_id": scenario_id,
            "work_item": work_item,
            "run_id": run_id,
            "runtime_id": runtime_id,
            "aidd_revision": aidd_revision or "unknown",
            "target_revision": target_revision or "unknown",
        },
        "tasklist": {
            "path": tasklist_path.as_posix(),
            "sha256": tasklist_sha,
            "authored_task_ids": authored_ids,
            "authored_dependencies": {
                key: list(value) for key, value in authored_dependencies.items()
            },
            "hash_matches": not any("hash" in finding for finding in findings),
        },
        "ledger": {
            "path": ledger_path.as_posix() if ledger is not None else None,
            "schema_version": (
                ledger.get("schema_version")
                if ledger is not None
                else None
            ),
            "source_tasklist_sha256": source_hash or public_ledger_hash,
        },
        "tasks": tasks,
        "next_ready_task": next_ready,
        "blocker": _literal_blocker(model),
        "finalization": {
            "status": finalization_status,
            "attempt_count": finalization_attempt_count,
            "evidence": (
                f"{finalization_evidence}/finalization-state.json"
                if isinstance(finalization_evidence, str) and finalization_evidence
                else None
            ),
        },
        "review_eligibility": {
            "eligible": review_eligible,
            "blocker": review.get("reason") or model.get("review_blocker"),
        },
        "findings": findings,
        "collection": {
            "source": "installed-public-ui-api-and-authorized-durable-artifacts",
            "public_surface": public_surface or {"status": "not-recorded"},
            "mutated_target": False,
        },
        "public_projection": model,
    }
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
