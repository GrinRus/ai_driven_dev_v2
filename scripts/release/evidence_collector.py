"""Collect bounded release evidence for checklist copy-in."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from urllib.parse import urlparse

_VERSION_PATTERN = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:(?:a|b|rc)[0-9]+)?(?:\.post[0-9]+)?(?:\.dev[0-9]+)?$"
)
_ERROR_OUTPUT_PATTERN = re.compile(
    r"(?im)^(?:error|exception|traceback|failed|fatal)\b"
)


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
    pipx_version_exit_code: int | None = None,
    pipx_doctor_exit_code: int | None = None,
    uv_tool_version_exit_code: int | None = None,
    uv_tool_doctor_exit_code: int | None = None,
) -> ReleaseEvidence:
    version_is_valid = bool(_VERSION_PATTERN.fullmatch(version))
    checks = (
        EvidenceCheck(
            name="semantic-version",
            status="pass" if version_is_valid else "fail",
            detail=version if version_is_valid else "version is not canonical",
        ),
        _url_check(
            "github-release-url",
            github_release_url,
            hostname="github.com",
            path=f"/GrinRus/ai_driven_dev_v2/releases/tag/v{version}",
        ),
        _workflow_url_check(release_workflow_url),
        _url_check(
            "pypi-url",
            pypi_url,
            hostname="pypi.org",
            path=f"/project/ai-driven-dev-v2/{version}/",
        ),
        _output_check(
            "pipx-version",
            pipx_version_output,
            expected_line=f"aidd {version}",
            exit_code=pipx_version_exit_code,
        ),
        _output_check(
            "pipx-doctor",
            pipx_doctor_output,
            expected_line=f"Version {version}",
            exit_code=pipx_doctor_exit_code,
        ),
        _output_check(
            "uv-tool-version",
            uv_tool_version_output,
            expected_line=f"aidd {version}",
            exit_code=uv_tool_version_exit_code,
        ),
        _output_check(
            "uv-tool-doctor",
            uv_tool_doctor_output,
            expected_line=f"Version {version}",
            exit_code=uv_tool_doctor_exit_code,
        ),
    )
    return ReleaseEvidence(
        version=version,
        success=all(check.status == "pass" for check in checks),
        checks=checks,
    )


def collect_release_evidence_from_payload(
    payload: Mapping[str, object],
) -> ReleaseEvidence:
    return collect_release_evidence(
        version=str(payload.get("version", "")),
        github_release_url=str(payload.get("github_release_url", "")),
        release_workflow_url=str(payload.get("release_workflow_url", "")),
        pypi_url=str(payload.get("pypi_url", "")),
        pipx_version_output=str(payload.get("pipx_version_output", "")),
        pipx_doctor_output=str(payload.get("pipx_doctor_output", "")),
        uv_tool_version_output=str(payload.get("uv_tool_version_output", "")),
        uv_tool_doctor_output=str(payload.get("uv_tool_doctor_output", "")),
        pipx_version_exit_code=_payload_exit_code(payload, "pipx_version_exit_code"),
        pipx_doctor_exit_code=_payload_exit_code(payload, "pipx_doctor_exit_code"),
        uv_tool_version_exit_code=_payload_exit_code(
            payload,
            "uv_tool_version_exit_code",
        ),
        uv_tool_doctor_exit_code=_payload_exit_code(
            payload,
            "uv_tool_doctor_exit_code",
        ),
    )


def _payload_exit_code(payload: Mapping[str, object], field: str) -> int | None:
    value = payload.get(field)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _url_check(
    name: str,
    url: str,
    *,
    hostname: str,
    path: str,
) -> EvidenceCheck:
    parsed = urlparse(url)
    valid = (
        parsed.scheme == "https"
        and parsed.hostname == hostname
        and parsed.path == path
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
        and parsed.username is None
        and parsed.password is None
        and parsed.port is None
    )
    status = "pass" if valid else "fail"
    detail = url if valid else f"expected canonical https://{hostname}{path}"
    return EvidenceCheck(name=name, status=status, detail=detail)


def _workflow_url_check(url: str) -> EvidenceCheck:
    parsed = urlparse(url)
    valid = (
        parsed.scheme == "https"
        and parsed.hostname == "github.com"
        and re.fullmatch(
            r"/GrinRus/ai_driven_dev_v2/actions/runs/[1-9][0-9]*",
            parsed.path,
        )
        is not None
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
        and parsed.username is None
        and parsed.password is None
        and parsed.port is None
    )
    return EvidenceCheck(
        name="release-workflow-url",
        status="pass" if valid else "fail",
        detail=(
            url
            if valid
            else (
                "expected canonical GitHub Actions run URL for "
                "GrinRus/ai_driven_dev_v2"
            )
        ),
    )


def _output_check(
    name: str,
    output: str,
    *,
    expected_line: str,
    exit_code: int | None,
) -> EvidenceCheck:
    normalized = output.strip()
    output_lines = tuple(line.strip() for line in normalized.splitlines())
    valid = (
        exit_code == 0
        and expected_line in output_lines
        and _ERROR_OUTPUT_PATTERN.search(normalized) is None
    )
    if exit_code is None:
        detail = "missing structured exit status"
    elif exit_code != 0:
        detail = f"command exited with {exit_code}: {normalized[:200]}"
    elif _ERROR_OUTPUT_PATTERN.search(normalized):
        detail = f"error-bearing transcript: {normalized[:200]}"
    elif expected_line not in output_lines:
        detail = f"expected exact output line: {expected_line}"
    else:
        detail = normalized[:240]
    return EvidenceCheck(
        name=name,
        status="pass" if valid else "fail",
        detail=detail,
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
