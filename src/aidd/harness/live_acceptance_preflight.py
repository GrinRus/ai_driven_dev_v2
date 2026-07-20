from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

from aidd.core.identifiers import SafeIdentifier
from aidd.harness.live_runtime_config import validate_live_runtime_command
from aidd.harness.scenarios import ScenarioManifestError, load_scenario


class LiveAcceptancePreflightError(ValueError):
    """Raised before a prod-like live run can allocate mutable state."""


@dataclass(frozen=True, slots=True)
class TrackedSourceState:
    revision: str
    tree: str
    tracked_index_sha256: str


@dataclass(frozen=True, slots=True)
class LiveAcceptanceLayout:
    provider_id: str
    source_checkout: Path
    external_root: Path
    provider_root: Path
    work_root: Path
    report_root: Path
    browser_root: Path
    scenario_id: str
    runtime_command: str
    runtime_mode: str
    source_state: TrackedSourceState


def _run_git(source_checkout: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=source_checkout,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown git error"
        raise LiveAcceptancePreflightError(f"Unable to inspect tracked AIDD source: {detail}")
    return completed.stdout


def capture_tracked_source_state(source_checkout: Path) -> TrackedSourceState:
    resolved_source = source_checkout.resolve(strict=False)
    if not (resolved_source / "pyproject.toml").is_file() or not (
        resolved_source / "contracts"
    ).is_dir():
        raise LiveAcceptancePreflightError(
            "Source checkout must be an AIDD repository containing pyproject.toml and contracts/."
        )

    status = _run_git(resolved_source, "status", "--porcelain", "--untracked-files=no")
    if status.strip():
        raise LiveAcceptancePreflightError(
            "Prod-like live acceptance requires a clean tracked AIDD source checkout."
        )

    revision = _run_git(resolved_source, "rev-parse", "HEAD").strip()
    tree = _run_git(resolved_source, "rev-parse", "HEAD^{tree}").strip()
    tracked_index = _run_git(resolved_source, "ls-files", "--stage").encode("utf-8")
    return TrackedSourceState(
        revision=revision,
        tree=tree,
        tracked_index_sha256=hashlib.sha256(tracked_index).hexdigest(),
    )


def assert_tracked_source_unchanged(
    source_checkout: Path,
    expected: TrackedSourceState,
) -> None:
    actual = capture_tracked_source_state(source_checkout)
    if actual != expected:
        raise LiveAcceptancePreflightError(
            "Tracked AIDD source changed during prod-like live acceptance."
        )


def _is_nested(left: Path, right: Path) -> bool:
    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def _validate_layout_roots(
    *,
    source_checkout: Path,
    external_root: Path,
    provider_id: str,
) -> tuple[Path, Path, Path, Path, Path]:
    safe_provider = SafeIdentifier.parse(provider_id, label="provider id").value
    source = source_checkout.resolve(strict=False)
    if not external_root.is_absolute():
        raise LiveAcceptancePreflightError("External live evidence root must be absolute.")
    external = external_root.resolve(strict=False)
    if _is_nested(source, external):
        raise LiveAcceptancePreflightError(
            "External live evidence root and AIDD source checkout must not overlap."
        )
    if not external.is_dir():
        raise LiveAcceptancePreflightError(
            "External live evidence root must already exist as a directory."
        )

    provider_root = (external / safe_provider).resolve(strict=False)
    if provider_root.parent != external or provider_root.name != safe_provider:
        raise LiveAcceptancePreflightError(
            "Provider root must be one unsymlinked component below the external root."
        )
    roots = tuple(
        (provider_root / name).resolve(strict=False)
        for name in ("work", "reports", "browser")
    )
    if any(not root.is_relative_to(provider_root) for root in roots):
        raise LiveAcceptancePreflightError("Provider roots must stay inside one provider subtree.")
    roots_overlap = any(
        _is_nested(left, right)
        for index, left in enumerate(roots)
        for right in roots[index + 1 :]
    )
    if roots_overlap:
        raise LiveAcceptancePreflightError(
            "Provider work, report, and browser roots must be distinct and non-overlapping."
        )
    return external, provider_root, roots[0], roots[1], roots[2]


def prepare_live_acceptance_layout(
    *,
    source_checkout: Path,
    external_root: Path,
    scenario_path: Path,
    provider_id: str,
) -> LiveAcceptanceLayout:
    source = source_checkout.resolve(strict=False)
    scenario = scenario_path.resolve(strict=False)
    if not scenario.is_relative_to(source):
        raise LiveAcceptancePreflightError(
            "Live scenario manifest must come from the tracked AIDD source checkout."
        )
    external, provider_root, work_root, report_root, browser_root = _validate_layout_roots(
        source_checkout=source,
        external_root=external_root,
        provider_id=provider_id,
    )
    source_state = capture_tracked_source_state(source)
    try:
        loaded = load_scenario(scenario, runtime_id=provider_id, workspace_root=Path(".aidd"))
        command = validate_live_runtime_command(runtime_id=provider_id, scenario=loaded)
    except (RuntimeError, ScenarioManifestError, ValueError) as exc:
        raise LiveAcceptancePreflightError(str(exc)) from exc
    if not loaded.is_live or loaded.automation_lane != "manual":
        raise LiveAcceptancePreflightError(
            "Prod-like provider acceptance requires a manual live scenario."
        )
    if loaded.run.stage_start != "idea" or loaded.run.stage_end != "qa":
        raise LiveAcceptancePreflightError(
            "Prod-like provider acceptance requires the complete idea -> qa stage scope."
        )
    if loaded.live_flow is None or loaded.live_flow.frontend_checkpoints is not True:
        raise LiveAcceptancePreflightError(
            "Prod-like provider acceptance requires public frontend checkpoints."
        )

    return LiveAcceptanceLayout(
        provider_id=provider_id,
        source_checkout=source,
        external_root=external,
        provider_root=provider_root,
        work_root=work_root,
        report_root=report_root,
        browser_root=browser_root,
        scenario_id=loaded.scenario_id,
        runtime_command=command.command,
        runtime_mode=command.execution_mode.value,
        source_state=source_state,
    )


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate an isolated prod-like live run layout.")
    parser.add_argument("scenario", type=Path)
    parser.add_argument("--runtime", required=True)
    parser.add_argument("--source-checkout", type=Path, default=Path.cwd())
    parser.add_argument("--external-root", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        layout = prepare_live_acceptance_layout(
            source_checkout=args.source_checkout,
            external_root=args.external_root,
            scenario_path=args.scenario,
            provider_id=args.runtime,
        )
    except LiveAcceptancePreflightError as exc:
        print(f"live acceptance preflight: {exc}")
        return 2
    payload = asdict(layout)
    payload["source_state"] = asdict(layout.source_state)
    for key, value in tuple(payload.items()):
        if isinstance(value, Path):
            payload[key] = value.as_posix()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "LiveAcceptanceLayout",
    "LiveAcceptancePreflightError",
    "TrackedSourceState",
    "assert_tracked_source_unchanged",
    "capture_tracked_source_state",
    "prepare_live_acceptance_layout",
]
