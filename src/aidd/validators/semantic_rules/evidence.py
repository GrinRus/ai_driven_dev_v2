from __future__ import annotations

import re
import shlex

IMPLEMENT_FILE_ENTRY_PATTERN = re.compile(r"`(?=[^`\n]*(?:/|\.))[^\n`]+`")
GENERIC_BACKTICKED_COMMAND_FRAGMENT = (
    r"`(?:[A-Za-z_][A-Za-z0-9_]*=\S+\s+)*"
    r"(?:\.{0,2}/)?[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+)*"
    r"(?:\s+[^`\n]+)+`"
)
IMPLEMENT_COMMAND_PATTERN = re.compile(
    r"(\$ [^\n]+|"
    r"`[^`\n]*\b("
    r"aidd|ast-index|uv run|pytest|ruff|mypy|python|node|sphinx-build|npm|pnpm|yarn|"
    r"go test|cargo test|"
    r"make|git|grep|rg|sed|nl|echo|printf|flake8|black|prettier|ty check|"
    r"bun|bunx|find|npx|vitest|tsc|perl"
    r")\b[^`\n]*`|"
    + GENERIC_BACKTICKED_COMMAND_FRAGMENT
    + r"|"
    r"`(?:\.venv/bin/|\.\/node_modules/\.bin/|node_modules/\.bin/)[^`\n]+`|"
    r"(?:^|\s)(?:\.venv/bin/|\.\/node_modules/\.bin/|node_modules/\.bin/)[^\s`]+|"
    r"\b(uv run|python -m|python -c|sphinx-build|go test|cargo test|ty check)\b|"
    r"\b(aidd|pytest|ruff|mypy|node|npm|pnpm|yarn|make|git|grep|rg|sed|nl|echo|printf|flake8|black)\b|"
    r"`test\s+[^`\n]+`)",
    flags=re.IGNORECASE,
)
IMPLEMENT_RESULT_PATTERN = re.compile(
    r"("
    r"->\s*output(?:\s+contains)?:\s*`[^`\n]+`|"
    r"->\s*(pass|fail|ok|error|empty|no output|`?\d+`?|exit\s*`?\d+`?)|"
    r"->\s*(?:no|without|clean|clear)[-_][A-Za-z0-9][A-Za-z0-9_-]*|"
    r"->\s*(?:no|without|clean|clear)\s+[^.\n]+|"
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
IMPLEMENT_ASSERTION_REFERENCE_PATTERN = re.compile(
    r"`(?:exit[_\s-]?code|result\.(?:exit_code|stdout|stderr|exception)|stdout|stderr|"
    r"[A-Za-z_][A-Za-z0-9_.]*\(\))\s*(?:==|!=|is|contains)\s*[^`]+`",
    flags=re.IGNORECASE,
)
IMPLEMENT_TEST_REFERENCE_PATTERN = re.compile(
    r"`(?:[^`\n/]+/)*tests?/[^`\n]+::[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z0-9_]+)*`",
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

_KNOWN_COMMAND_EXECUTABLES = frozenset(
    {
        "aidd",
        "ast-index",
        "bash",
        "black",
        "bun",
        "bunx",
        "cargo",
        "echo",
        "find",
        "flake8",
        "git",
        "go",
        "grep",
        "make",
        "mypy",
        "node",
        "npm",
        "nl",
        "npx",
        "pnpm",
        "perl",
        "prettier",
        "printf",
        "pytest",
        "python",
        "python3",
        "rg",
        "ruff",
        "sed",
        "sh",
        "sphinx-build",
        "test",
        "tsc",
        "ty",
        "uv",
        "vitest",
        "yarn",
        "zsh",
    }
)
_SHELL_ASSIGNMENT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=\S+$")
_BACKTICKED_FRAGMENT_PATTERN = re.compile(r"`([^`\n]+)`")
_MULTILINE_BACKTICKED_FRAGMENT_PATTERN = re.compile(r"`(?P<body>[^`]*\n[^`]*)`", re.DOTALL)
_BACKTICKED_RESULT_DELIMITER_PATTERN = re.compile(r"`\s*->\s*")
_PROMPT_COMMAND_PATTERN = re.compile(r"^\s*\$\s+(.+?)\s*$", re.MULTILINE)
_COMMAND_FIELD_PATTERN = re.compile(
    r"^\s*(?:-\s*)?Command\s*:\s*(.+?)\s*$",
    flags=re.IGNORECASE | re.MULTILINE,
)
_FENCED_COMMAND_PATTERN = re.compile(
    r"```(?:bash|console|sh|shell|zsh)?\s*\n(?P<body>.*?)```",
    flags=re.IGNORECASE | re.DOTALL,
)
_SHELL_COMPOUND_PATTERN = re.compile(
    r"^(?:(?:[A-Za-z_][A-Za-z0-9_]*=\$\([^;)]++\)|"
    r"[A-Za-z_][A-Za-z0-9_]*=(?!\$\()[^;\s]++);\s*+)*+(?:"
    r"if\s+.+;\s*then\s+.+;\s*(?:else\s+.+;\s*)?fi|"
    r"(?:for|while|until)\s+.+;\s*do\s+.+;\s*done|"
    r"case\s+.+\s+in\s+.+(?:;;\s*)?esac"
    r")(?:;\s*.+)?$",
    flags=re.IGNORECASE | re.DOTALL,
)
_INLINE_SHELL_RESULT_SUFFIX_PATTERN = re.compile(
    r"\s+->\s*(?:pass|fail|ok|error|empty|no output|`?\d+`?|"
    r"exit\s*(?:code\s*)?`?\d+`?)\s*$",
    flags=re.IGNORECASE,
)


def is_deferred_implementation_verification(verification_item: str) -> bool:
    return IMPLEMENT_DEFERRED_VERIFICATION_PATTERN.search(verification_item) is not None


def _without_non_command_artifact_text_outside_code(text: str) -> str:
    parts = re.split(r"(`[^`\n]*`)", text)
    return "".join(
        part
        if part.startswith("`") and part.endswith("`")
        else IMPLEMENT_NON_COMMAND_ARTIFACT_TEXT_PATTERN.sub("", part)
        for part in parts
    )


def _command_tokens(candidate: str) -> tuple[str, ...]:
    normalized = candidate.strip().strip("`").strip()
    if not normalized:
        return ()
    try:
        return tuple(shlex.split(normalized))
    except ValueError:
        return ()


def _looks_like_command(candidate: str, *, explicit_container: bool) -> bool:
    normalized_candidate = candidate.strip().strip("`").strip()
    tokens = list(_command_tokens(candidate))
    if not tokens:
        return False
    if tokens[0] == "env":
        tokens.pop(0)
    while tokens and _SHELL_ASSIGNMENT_PATTERN.fullmatch(tokens[0]):
        tokens.pop(0)
    if not tokens:
        return False
    executable = tokens[0].lower()

    # ``shlex`` tokenizes ``output=$(git status ...)`` as an assignment token
    # followed by ``status``. Inspect the command substitution's first token
    # before evaluating the outer command shape so this remains executable
    # evidence instead of an unverifiable prose claim.
    for substitution in re.finditer(r"\$\(\s*([^\s;|&()]+)", normalized_candidate):
        if substitution.group(1).lower() in _KNOWN_COMMAND_EXECUTABLES:
            return True

    shell_compound_candidate = normalized_candidate
    if _SHELL_COMPOUND_PATTERN.fullmatch(shell_compound_candidate) is None:
        inline_result = _INLINE_SHELL_RESULT_SUFFIX_PATTERN.search(
            shell_compound_candidate
        )
        if inline_result is not None:
            candidate_without_result = shell_compound_candidate[: inline_result.start()].rstrip()
            if _SHELL_COMPOUND_PATTERN.fullmatch(candidate_without_result) is not None:
                shell_compound_candidate = candidate_without_result

    if _SHELL_COMPOUND_PATTERN.fullmatch(shell_compound_candidate) is not None:
        return any(
            token.strip(";(){}!").lower() in _KNOWN_COMMAND_EXECUTABLES
            for token in tokens[1:]
        )
    if explicit_container:
        return (
            re.fullmatch(
                r"(?:\.{0,2}/)?[A-Za-z0-9_.+-]+(?:/[A-Za-z0-9_.+-]+)*",
                executable,
            )
            is not None
        )
    if executable in _KNOWN_COMMAND_EXECUTABLES:
        return len(tokens) > 1
    return executable.startswith(("./", "../", "/", ".venv/bin/", "node_modules/.bin/"))


def _classify_backticked_command_with_result(text: str) -> bool | None:
    """Recognize a command span whose payload contains literal backticks.

    Markdown's single-backtick code spans cannot represent an unescaped
    JavaScript template literal, but runtimes commonly emit exactly that shape
    in one-line verification notes.  The terminal ``->`` marker gives us an
    unambiguous right boundary; we still require balanced nested delimiters and
    a command-shaped payload so prose or malformed spans remain fail-closed.
    """

    saw_malformed_nested_command = False
    for line in text.splitlines():
        backtick_openings = tuple(match.start() for match in re.finditer("`", line))
        delimiters = tuple(_BACKTICKED_RESULT_DELIMITER_PATTERN.finditer(line))
        for opening in backtick_openings:
            prefix = line[:opening].strip()
            if prefix and not prefix.endswith(":"):
                continue
            for delimiter in reversed(delimiters):
                if delimiter.start() <= opening:
                    continue
                candidate = line[opening + 1 : delimiter.start()]
                if "`" not in candidate:
                    continue
                normalized_candidate = candidate.replace("`", "")
                if candidate.count("`") % 2 == 0 and _looks_like_command(
                    normalized_candidate,
                    explicit_container=False,
                ):
                    return True
                if _command_starts_with_known_executable(normalized_candidate):
                    saw_malformed_nested_command = True
    return False if saw_malformed_nested_command else None


def _command_starts_with_known_executable(candidate: str) -> bool:
    """Recognize a command prefix even when malformed quoting blocks ``shlex``."""

    tokens = candidate.strip().split()
    if tokens and tokens[0].lower() == "env":
        tokens.pop(0)
    while tokens and _SHELL_ASSIGNMENT_PATTERN.fullmatch(tokens[0]):
        tokens.pop(0)
    return bool(tokens and tokens[0].lower() in _KNOWN_COMMAND_EXECUTABLES and len(tokens) > 1)


def has_implementation_command_evidence(verification_item: str) -> bool:
    command_candidate = _without_non_command_artifact_text_outside_code(verification_item)
    if IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN.search(command_candidate) is not None:
        return True
    backticked_command_status = _classify_backticked_command_with_result(command_candidate)
    if backticked_command_status is True:
        return True
    if any(
        _looks_like_command(match.group(1), explicit_container=True)
        for pattern in (_PROMPT_COMMAND_PATTERN, _COMMAND_FIELD_PATTERN)
        for match in pattern.finditer(command_candidate)
    ):
        return True
    for fence in _FENCED_COMMAND_PATTERN.finditer(command_candidate):
        for line in fence.group("body").splitlines():
            normalized_line = line.strip().removeprefix("$ ").strip()
            if normalized_line and not normalized_line.startswith("#") and _looks_like_command(
                normalized_line,
                explicit_container=True,
            ):
                return True
    if backticked_command_status is False:
        return False
    # Markdown inline code spans may contain newlines.  Runtimes commonly emit
    # heredoc verification commands in that form (for example, ``uv run
    # python - <<'PY' ... PY``).  Treat the complete span as one command so
    # valid executable evidence is not mistaken for an unverifiable prose
    # claim.  A closed span and command-shaped prefix are still required.
    for match in _MULTILINE_BACKTICKED_FRAGMENT_PATTERN.finditer(command_candidate):
        if _looks_like_command(match.group("body"), explicit_container=False):
            return True
    return any(
        _looks_like_command(match.group(1), explicit_container=False)
        for match in _BACKTICKED_FRAGMENT_PATTERN.finditer(command_candidate)
    )


__all__ = [
    "IMPLEMENT_ARTIFACT_REFERENCE_PATTERN",
    "IMPLEMENT_ASSERTION_REFERENCE_PATTERN",
    "IMPLEMENT_COMMAND_PATTERN",
    "IMPLEMENT_COMPLETION_CLAIM_PATTERN",
    "IMPLEMENT_DEFERRED_VERIFICATION_PATTERN",
    "IMPLEMENT_FILE_ENTRY_PATTERN",
    "IMPLEMENT_NOOP_JUSTIFICATION_PATTERN",
    "IMPLEMENT_NON_COMMAND_ARTIFACT_TEXT_PATTERN",
    "IMPLEMENT_RESULT_PATTERN",
    "IMPLEMENT_TEST_REFERENCE_PATTERN",
    "IMPLEMENT_REUSED_COMMAND_EVIDENCE_PATTERN",
    "has_implementation_command_evidence",
    "is_deferred_implementation_verification",
]
