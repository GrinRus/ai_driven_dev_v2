from __future__ import annotations

import re

IMPLEMENT_FILE_ENTRY_PATTERN = re.compile(r"`(?=[^`\n]*(?:/|\.))[^\n`]+`")
IMPLEMENT_COMMAND_PATTERN = re.compile(
    r"(\$ [^\n]+|\.venv/bin/[^\s`]+|\b("
    r"uv run|pytest|ruff|mypy|python -m|npm|pnpm|yarn|go test|cargo test|"
    r"make|git|grep|rg|echo|printf|flake8|black|prettier|ty check|sqlite-utils|"
    r"bun|bunx|vitest|tsc"
    r")\b|`test\s+[^`\n]+`|`(?:insert|upsert|memory)\b[^`\n]*`)",
    flags=re.IGNORECASE,
)
IMPLEMENT_RESULT_PATTERN = re.compile(
    r"("
    r"->\s*(pass|fail|ok|error|empty|no output|`?\d+`?|exit\s*`?\d+`?)|"
    r"->\s*[^.\n]*(?:\bonly\b|\bshows?\b|\bempty\b|\bno output\b)|"
    r"\b(pass(?:ed)?|fail(?:ed)?|succeeded|error|exit code|exited with status|returned)\b|"
    r"\bexit\s*`?\d+`?|"
    r"`?\bexit[_\s-]?code\b`?\s*(?:==|=|:)?\s*`?\d+`?|"
    r"\b\d+\s+passed\b|"
    r"\bSuccess:|"
    r"\bFound\s+\d+\s+diagnostics\b|"
    r"\bshows?\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|no)\b|"
    r"\bexactly\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+matches\b|"
    r"\b\d+\s+(?:production\s+)?matches\b|"
    r"\b\d+\s+files?\s+changed\b|"
    r"\bzero\s+differences\b|"
    r"\bobserved\s*:|"
    r"\b(?:does|do)\s+not\s+exist\b|"
    r"\bexists\(\)\s+is\s+(?:true|false)\b|"
    r"\btable_names\(\)\s*(?:==|is)\s*\[\]|"
    r"\bno\s+(?:stderr|exception|output|traceback)\b|"
    r"\bprinted\s+`?OK`?\b|"
    r"\bmatches\s+expected\b"
    r")",
    flags=re.IGNORECASE,
)
IMPLEMENT_ARTIFACT_REFERENCE_PATTERN = re.compile(
    r"`[^`]+(?:\.md|\.json|\.log|\.txt)`",
    flags=re.IGNORECASE,
)
IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN = re.compile(
    r"\b(same\s+)?stash/pop\s+procedure\b|"
    r"\bsame\b.{0,80}\b(?:procedure|command|check|run)\b.{0,80}\bas\s+`?(?:T\d+|TL-\d+)`?",
    flags=re.IGNORECASE | re.DOTALL,
)
IMPLEMENT_DEFERRED_VERIFICATION_PATTERN = re.compile(
    r"\b(?:not[-\s]+(?:run|executed)|skipped|deferred|hand[- ]off)\b",
    flags=re.IGNORECASE,
)
IMPLEMENT_COMPLETION_CLAIM_PATTERN = re.compile(
    r"\b(completed|fully|done|implemented|finished)\b",
    flags=re.IGNORECASE,
)
IMPLEMENT_NOOP_JUSTIFICATION_PATTERN = re.compile(
    r"\b(no-op|already (satisfied|implemented)|blocked|external constraint|out of scope)\b",
    flags=re.IGNORECASE,
)


def is_deferred_implementation_verification(verification_item: str) -> bool:
    return IMPLEMENT_DEFERRED_VERIFICATION_PATTERN.search(verification_item) is not None


def has_implementation_command_evidence(verification_item: str) -> bool:
    return (
        IMPLEMENT_COMMAND_PATTERN.search(verification_item) is not None
        or IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN.search(verification_item) is not None
    )


__all__ = [
    "IMPLEMENT_ARTIFACT_REFERENCE_PATTERN",
    "IMPLEMENT_COMMAND_PATTERN",
    "IMPLEMENT_COMPLETION_CLAIM_PATTERN",
    "IMPLEMENT_DEFERRED_VERIFICATION_PATTERN",
    "IMPLEMENT_FILE_ENTRY_PATTERN",
    "IMPLEMENT_NOOP_JUSTIFICATION_PATTERN",
    "IMPLEMENT_RESULT_PATTERN",
    "IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN",
    "has_implementation_command_evidence",
    "is_deferred_implementation_verification",
]
