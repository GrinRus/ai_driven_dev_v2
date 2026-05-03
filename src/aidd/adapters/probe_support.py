from __future__ import annotations

import shlex
import shutil
import subprocess

from aidd.adapters.base import CapabilityReport


def contains_any(text: str, markers: tuple[str, ...]) -> bool:
    return any(marker in text for marker in markers)


def normalize_output_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value


def first_non_empty_line(*, stdout: str | bytes | None, stderr: str | bytes | None) -> str | None:
    output = normalize_output_text(stdout).strip() or normalize_output_text(stderr).strip()
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


def discover_version(
    command_path: str,
    *,
    timeout_seconds: float,
    use_timeout_output: bool = False,
) -> str | None:
    try:
        result = subprocess.run(
            [command_path, "--version"],
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        if use_timeout_output:
            return first_non_empty_line(stdout=exc.stdout, stderr=exc.stderr)
        return None
    except (FileNotFoundError, PermissionError, OSError):
        return None

    return first_non_empty_line(stdout=result.stdout, stderr=result.stderr)


def discover_help_text(
    command_path: str,
    *,
    timeout_seconds: float,
    use_timeout_output: bool = False,
) -> str | None:
    try:
        result = subprocess.run(
            [command_path, "--help"],
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        if not use_timeout_output:
            return None
        return (
            normalize_output_text(exc.stdout).strip()
            or normalize_output_text(exc.stderr).strip()
            or None
        )
    except (FileNotFoundError, PermissionError, OSError):
        return None

    output = result.stdout.strip() or result.stderr.strip()
    return output or None


def detect_capability_flags(help_text: str) -> dict[str, bool]:
    normalized = help_text.lower()
    return {
        "supports_structured_log_stream": contains_any(
            normalized,
            ("--json", "--jsonl", "jsonl", "structured output"),
        ),
        "supports_questions": contains_any(
            normalized,
            ("question", "ask-user", "prompt for input"),
        ),
        "supports_resume": contains_any(
            normalized,
            ("--resume", "resume run", "continue run"),
        ),
        "supports_subagents": contains_any(
            normalized,
            ("subagent", "sub-agent"),
        ),
        "supports_non_interactive_mode": contains_any(
            normalized,
            ("--non-interactive", "--ci", "--yes"),
        ),
        "supports_working_directory_control": contains_any(
            normalized,
            ("--cwd", "--workdir", "--working-directory"),
        ),
        "supports_env_injection": contains_any(
            normalized,
            ("--env", "--set-env", "environment variable"),
        ),
    }


def probe_runtime_from_help(
    *,
    runtime_id: str,
    command: str,
    timeout_seconds: float,
    use_timeout_output: bool = False,
) -> CapabilityReport:
    discovered = discover_command(command)
    available = discovered is not None
    version_text = (
        discover_version(
            discovered,
            timeout_seconds=timeout_seconds,
            use_timeout_output=use_timeout_output,
        )
        if discovered
        else None
    )
    detected = (
        detect_capability_flags(
            discover_help_text(
                discovered,
                timeout_seconds=timeout_seconds,
                use_timeout_output=use_timeout_output,
            )
            or ""
        )
        if discovered
        else {}
    )

    return CapabilityReport(
        runtime_id=runtime_id,
        available=available,
        command=discovered or command,
        version_text=version_text,
        supports_raw_log_stream=available,
        supports_structured_log_stream=detected.get("supports_structured_log_stream", False),
        supports_questions=detected.get("supports_questions", False),
        supports_resume=detected.get("supports_resume", False),
        supports_subagents=detected.get("supports_subagents", False),
        supports_non_interactive_mode=detected.get("supports_non_interactive_mode", False),
        supports_working_directory_control=detected.get(
            "supports_working_directory_control",
            False,
        ),
        supports_env_injection=detected.get("supports_env_injection", False),
    )


def probe_basic_runtime(
    *,
    runtime_id: str,
    command: str,
    timeout_seconds: float,
) -> CapabilityReport:
    discovered = discover_command(command)
    available = discovered is not None
    version_text = (
        discover_version(discovered, timeout_seconds=timeout_seconds)
        if discovered
        else None
    )
    return CapabilityReport(
        runtime_id=runtime_id,
        available=available,
        command=discovered or command,
        version_text=version_text,
        supports_raw_log_stream=available,
        supports_structured_log_stream=False,
        supports_questions=False,
        supports_resume=False,
        supports_subagents=False,
        supports_non_interactive_mode=available,
        supports_working_directory_control=available,
        supports_env_injection=available,
    )
