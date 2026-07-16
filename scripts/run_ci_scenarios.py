from __future__ import annotations

import argparse
from pathlib import Path

from aidd.harness.ci_scenario_lane import execute_ci_scenario_lane


def main() -> int:
    parser = argparse.ArgumentParser(description="Execute every deterministic CI scenario.")
    parser.add_argument(
        "--scenario-root",
        type=Path,
        default=Path("harness/scenarios"),
    )
    parser.add_argument("--root", type=Path, default=Path(".aidd-ci"))
    args = parser.parse_args()

    result = execute_ci_scenario_lane(
        scenario_root=args.scenario_root,
        workspace_root=args.root,
    )
    print("Discovered CI scenarios: " + ", ".join(result.discovered_ids))
    for execution in result.executions:
        print(
            f"[{execution.exit_code}] {execution.scenario_id}: "
            f"{execution.path.as_posix()}"
        )
        if execution.stdout_text:
            print(execution.stdout_text.rstrip())
        if execution.stderr_text:
            print(execution.stderr_text.rstrip())
    print("Executed CI scenarios: " + ", ".join(result.executed_ids))
    if result.discovered_ids != result.executed_ids:
        print("CI scenario discovery/execution mismatch.")
        return 1
    return 0 if result.succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
