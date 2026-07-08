from __future__ import annotations

import re

IMPLEMENT_FILE_ENTRY_PATTERN = re.compile(r"`(?=[^`\n]*(?:/|\.))[^\n`]+`")
GENERIC_BACKTICKED_COMMAND_FRAGMENT = (
    r"`(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*"
    r"(?:\.{0,2}/)?[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+)*"
    r"(?:\s+[^`\n]+)+`"
)
IMPLEMENT_COMMAND_PATTERN = re.compile(
    r"(\$ [^\n]+|"
    r"`[^`\n]*\b("
    r"aidd|uv run|pytest|ruff|mypy|python|sphinx-build|npm|pnpm|yarn|go test|cargo test|"
    r"make|git|grep|rg|sed|echo|printf|flake8|black|prettier|ty check|"
    r"bun|bunx|find|npx|vitest|tsc"
    r")\b[^`\n]*`|"
    + GENERIC_BACKTICKED_COMMAND_FRAGMENT
    + r"|"
    r"`(?:\.venv/bin/|\.\/node_modules/\.bin/|node_modules/\.bin/)[^`\n]+`|"
    r"(?:^|\s)(?:\.venv/bin/|\.\/node_modules/\.bin/|node_modules/\.bin/)[^\s`]+|"
    r"\b(uv run|python -m|python -c|sphinx-build|go test|cargo test|ty check)\b|"
    r"\b(aidd|pytest|ruff|mypy|npm|pnpm|yarn|make|git|grep|rg|sed|echo|printf|flake8|black)\b|"
    r"`test\s+[^`\n]+`)",
    flags=re.IGNORECASE,
)
IMPLEMENT_RESULT_PATTERN = re.compile(
    r"("
    r"->\s*output(?:\s+contains)?:\s*`[^`\n]+`|"
    r"->\s*(pass|fail|ok|error|empty|no output|`?\d+`?|exit\s*`?\d+`?)|"
    r"->\s*[^.\n]*(?:\bonly\b|\bshows?\b|\bempty\b|\bno output\b|\bbounded\b)|"
    r"\b(pass(?:ed)?|fail(?:ed)?|succeeded|error|exit code|exited with status|returned)\b|"
    r"\bexit\s*`?\d+`?|"
    r"`?\bexit[_\s-]?code\b`?\s*(?:==|=|:)?\s*`?\d+`?|"
    r"\b\d+\s+passed\b|"
    r"\bSuccess:|"
    r"\bFound\s+\d+\s+diagnostics\b|"
    r"\b\d+\s+(?:type\s+)?errors?\b|"
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
IMPLEMENT_NON_COMMAND_ARTIFACT_TEXT_PATTERN = re.compile(
    r"`?\.?(?:pytest|ruff|mypy)_cache/?`?|"
    r"`?\.hypothesis/?`?|"
    r"`?__pycache__/?`?|"
    r"\bpytest/sphinx checks\b|"
    r"\btest/build cache residue\b|"
    r"\bverification residue cleanup\b",
    flags=re.IGNORECASE,
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


def _safe_command_pattern_search(text: str) -> bool:
    command_candidate = text
    if command_candidate.count("`") % 2:
        command_candidate = command_candidate.replace("`", "")
    return IMPLEMENT_COMMAND_PATTERN.search(command_candidate) is not None


def _without_non_command_artifact_text_outside_code(text: str) -> str:
    parts = re.split(r"(`[^`\n]*`)", text)
    return "".join(
        part
        if part.startswith("`") and part.endswith("`")
        else IMPLEMENT_NON_COMMAND_ARTIFACT_TEXT_PATTERN.sub("", part)
        for part in parts
    )


def has_implementation_command_evidence(verification_item: str) -> bool:
    command_candidate = _without_non_command_artifact_text_outside_code(verification_item)
    return _safe_command_pattern_search(
        command_candidate
    ) or IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN.search(command_candidate) is not None


__all__ = [
    "IMPLEMENT_ARTIFACT_REFERENCE_PATTERN",
    "IMPLEMENT_COMMAND_PATTERN",
    "IMPLEMENT_COMPLETION_CLAIM_PATTERN",
    "IMPLEMENT_DEFERRED_VERIFICATION_PATTERN",
    "IMPLEMENT_FILE_ENTRY_PATTERN",
    "IMPLEMENT_NOOP_JUSTIFICATION_PATTERN",
    "IMPLEMENT_NON_COMMAND_ARTIFACT_TEXT_PATTERN",
    "IMPLEMENT_RESULT_PATTERN",
    "IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN",
    "has_implementation_command_evidence",
    "is_deferred_implementation_verification",
]
