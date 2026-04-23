from __future__ import annotations

import shlex
import shutil
import subprocess

from aidd.adapters.base import CapabilityReport

_PROBE_TIMEOUT_SECONDS = 5


def _contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def _normalize_output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def _first_non_empty_line(*, stdout: str | bytes | None, stderr: str | bytes | None) -> str | None:
    output = _normalize_output_text(stdout).strip() or _normalize_output_text(stderr).strip()
    if not output:
        return None
    return output.splitlines()[0].strip() or None


def discover_command(command: str) -> str | None:
    stripped = command.strip()
    if not stripped:
        return None

    try:
        tokens = shlex.split(stripped)
    except ValueError:
        return None
    if not tokens:
        return None

    return shutil.which(tokens[0])


def discover_version(command_path: str) -> str | None:
    try:
        result = subprocess.run(
            [command_path, "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return _first_non_empty_line(stdout=exc.stdout, stderr=exc.stderr)
    except (FileNotFoundError, PermissionError, OSError):
        return None

    return _first_non_empty_line(stdout=result.stdout, stderr=result.stderr)


def discover_help_text(command_path: str) -> str | None:
    try:
        result = subprocess.run(
            [command_path, "--help"],
            capture_output=True,
            check=False,
            text=True,
            timeout=_PROBE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        return (
            _normalize_output_text(exc.stdout).strip()
            or _normalize_output_text(exc.stderr).strip()
            or None
        )
    except (FileNotFoundError, PermissionError, OSError):
        return None

    output = result.stdout.strip() or result.stderr.strip()
    return output or None


def detect_capability_flags(help_text: str) -> dict[str, bool]:
    normalized = help_text.lower()
    return {
        "supports_tool_calls": _contains_any(
            normalized,
            ("tool", "mcp", "function call", "tool call"),
        ),
        "supports_structured_log_stream": _contains_any(
            normalized,
            ("--json", "--jsonl", "jsonl", "structured output"),
        ),
        "supports_log_access": _contains_any(
            normalized,
            ("log", "trace", "--log-file", "stream"),
        ),
        "supports_questions": _contains_any(
            normalized,
            ("question", "ask-user", "prompt for input"),
        ),
        "supports_resume": _contains_any(
            normalized,
            ("--resume", "resume run", "continue run"),
        ),
        "supports_interrupts": _contains_any(
            normalized,
            ("interrupt", "cancel", "stop"),
        ),
        "supports_subagents": _contains_any(
            normalized,
            ("subagent", "sub-agent"),
        ),
        "supports_hooks": _contains_any(
            normalized,
            ("hook", "hooks"),
        ),
        "supports_non_interactive_mode": _contains_any(
            normalized,
            ("--non-interactive", "--ci", "--yes"),
        ),
        "supports_working_directory_control": _contains_any(
            normalized,
            ("--cwd", "--workdir", "--working-directory"),
        ),
        "supports_env_injection": _contains_any(
            normalized,
            ("--env", "--set-env", "environment variable"),
        ),
    }


def probe(command: str) -> CapabilityReport:
    discovered = discover_command(command)
    available = discovered is not None
    version_text = discover_version(discovered) if discovered else None
    detected = detect_capability_flags(discover_help_text(discovered) or "") if discovered else {}

    return CapabilityReport(
        runtime_id="claude-code",
        available=available,
        command=discovered or command,
        version_text=version_text,
        supports_tool_calls=detected.get("supports_tool_calls", False),
        supports_raw_log_stream=available,
        supports_structured_log_stream=detected.get("supports_structured_log_stream", False),
        supports_log_access=detected.get("supports_log_access", available),
        supports_questions=detected.get("supports_questions", False),
        supports_resume=detected.get("supports_resume", False),
        supports_interrupts=detected.get("supports_interrupts", False),
        supports_subagents=detected.get("supports_subagents", False),
        supports_hooks=detected.get("supports_hooks", False),
        supports_non_interactive_mode=detected.get("supports_non_interactive_mode", False),
        supports_working_directory_control=detected.get(
            "supports_working_directory_control",
            False,
        ),
        supports_env_injection=detected.get("supports_env_injection", False),
    )
