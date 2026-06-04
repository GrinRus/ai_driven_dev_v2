"""Collect bounded release evidence for checklist copy-in."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class EvidenceCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class ReleaseEvidence:
    version: str
    success: bool
    checks: tuple[EvidenceCheck, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        rows = "\n".join(
            f"- `{check.name}`: `{check.status}` - {check.detail}"
            for check in self.checks
        )
        verdict = "accepted" if self.success else "blocked"
        return (
            f"### `v{self.version}` release evidence\n\n"
            f"- Result: {verdict}.\n"
            f"{rows}\n"
        )


def collect_release_evidence(
    *,
    version: str,
    github_release_url: str,
    release_workflow_url: str,
    pypi_url: str,
    pipx_version_output: str,
    pipx_doctor_output: str,
    uv_tool_version_output: str,
    uv_tool_doctor_output: str,
) -> ReleaseEvidence:
    checks = (
        _url_check("github-release-url", github_release_url, f"/tag/v{version}"),
        _url_check("release-workflow-url", release_workflow_url, "/actions/runs/"),
        _url_check("pypi-url", pypi_url, f"/{version}/"),
        _output_check("pipx-version", pipx_version_output, f"aidd {version}"),
        _output_check("pipx-doctor", pipx_doctor_output, f"Version {version}"),
        _output_check("uv-tool-version", uv_tool_version_output, f"aidd {version}"),
        _output_check("uv-tool-doctor", uv_tool_doctor_output, f"Version {version}"),
    )
    return ReleaseEvidence(
        version=version,
        success=all(check.status == "pass" for check in checks),
        checks=checks,
    )


def collect_release_evidence_from_payload(
    payload: Mapping[str, object],
) -> ReleaseEvidence:
    kwargs = {
        "version": str(payload.get("version", "")),
        "github_release_url": str(payload.get("github_release_url", "")),
        "release_workflow_url": str(payload.get("release_workflow_url", "")),
        "pypi_url": str(payload.get("pypi_url", "")),
        "pipx_version_output": str(payload.get("pipx_version_output", "")),
        "pipx_doctor_output": str(payload.get("pipx_doctor_output", "")),
        "uv_tool_version_output": str(payload.get("uv_tool_version_output", "")),
        "uv_tool_doctor_output": str(payload.get("uv_tool_doctor_output", "")),
    }
    return collect_release_evidence(**kwargs)


def _url_check(name: str, url: str, expected_fragment: str) -> EvidenceCheck:
    parsed = urlparse(url)
    valid = parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    contains_fragment = expected_fragment in url
    status = "pass" if valid and contains_fragment else "fail"
    detail = url if status == "pass" else f"expected URL containing {expected_fragment}"
    return EvidenceCheck(name=name, status=status, detail=detail)


def _output_check(name: str, output: str, expected: str) -> EvidenceCheck:
    normalized = output.strip()
    return EvidenceCheck(
        name=name,
        status="pass" if expected in normalized else "fail",
        detail=normalized[:240] if normalized else f"expected output containing {expected}",
    )


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", help="JSON file with release evidence fields.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    return parser.parse_args(tuple(argv))


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    with open(args.payload, encoding="utf-8") as file_obj:
        payload = json.load(file_obj)
    if not isinstance(payload, dict):
        raise ValueError("evidence payload must be a JSON object")
    evidence = collect_release_evidence_from_payload(payload)
    print(evidence.to_json() if args.json else evidence.to_markdown())
    return 0 if evidence.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
