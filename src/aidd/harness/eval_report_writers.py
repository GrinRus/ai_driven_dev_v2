from __future__ import annotations

from pathlib import Path

from aidd.evals.verdicts import ScenarioVerdict, write_scenario_verdict_markdown
from aidd.harness.result_bundle import ResultBundleLayout


def write_eval_source_artifacts(
    *,
    layout: ResultBundleLayout,
    runtime_log_source: str,
    validator_report_source: str,
    verdict: ScenarioVerdict,
) -> tuple[Path, Path, Path]:
    sources_root = layout.run_root / "_sources"
    sources_root.mkdir(parents=True, exist_ok=True)
    runtime_log_source_path = sources_root / "runtime.log"
    validator_report_source_path = sources_root / "validator-report.md"
    verdict_source_path = sources_root / "verdict.md"

    runtime_log_source_path.write_text(runtime_log_source, encoding="utf-8")
    validator_report_source_path.write_text(validator_report_source, encoding="utf-8")
    write_scenario_verdict_markdown(path=verdict_source_path, verdict=verdict)
    return runtime_log_source_path, validator_report_source_path, verdict_source_path


__all__ = ["write_eval_source_artifacts"]
