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
    r"make|git|grep|rg|sed|nl|echo|printf|diff|wc|od|sha256sum|shasum|ls|mkdir|cp|tar|rm|cd|"
    r"flake8|black|prettier|ty check|"
    r"bun|bunx|find|npx|vitest|tsc|perl"
    r")\b[^`\n]*`|" + GENERIC_BACKTICKED_COMMAND_FRAGMENT + r"|"
    r"`(?:\.venv/bin/|\.\/node_modules/\.bin/|node_modules/\.bin/)[^`\n]+`|"
    r"(?:^|\s)(?:\.venv/bin/|\.\/node_modules/\.bin/|node_modules/\.bin/)[^\s`]+|"
    r"\b(uv run|python -m|python -c|sphinx-build|go test|cargo test|ty check)\b|"
    r"\b(aidd|pytest|ruff|mypy|node|npm|pnpm|yarn|make|git|grep|rg|sed|nl|echo|printf|diff|wc|od|sha256sum|shasum|ls|mkdir|cp|tar|rm|cd|flake8|black)\b|"
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
    r"\bper-prefix\s+counts\b|"
    r"->\s*observed\b|"
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
IMPLEMENT_CONTEXT_NOTE_PATTERN = re.compile(
    r"\bnot\s+(?:itself\s+)?a\s+check\b",
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
        "cat",
        "cargo",
        "cd",
        "cp",
        "diff",
        "echo",
        "find",
        "flake8",
        "git",
        "go",
        "grep",
        "ls",
        "mkdir",
        "make",
        "mypy",
        "node",
        "npm",
        "nl",
        "od",
        "npx",
        "pnpm",
        "perl",
        "prettier",
        "printf",
        "pytest",
        "python",
        "python3",
        "rg",
        "rm",
        "ruff",
        "sha256sum",
        "sed",
        "shasum",
        "sh",
        "sphinx-build",
        "tar",
        "test",
        "tsc",
        "ty",
        "uv",
        "vitest",
        "wc",
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
_CLI_RUNNER_INVOCATION_PATTERN = re.compile(
    r"\b(?:click\.)?testing\.CliRunner\b[^\n]*(?:invocation\s+of|\.invoke\b)|"
    r"\bCliRunner\(\)\.invoke\b",
    flags=re.IGNORECASE | re.DOTALL,
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
    return (
        IMPLEMENT_DEFERRED_VERIFICATION_PATTERN.search(verification_item) is not None
        or IMPLEMENT_CONTEXT_NOTE_PATTERN.search(verification_item) is not None
    )


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

    # Check a direct executable before looking for shell compounds.  Arguments
    # such as ``python -c \"...; ...\"`` legitimately contain semicolons, but
    # those separators belong to the quoted program rather than to the shell
    # command.  Classifying the direct executable first keeps valid evidence
    # from being mistaken for an unsupported command chain.
    if not explicit_container:
        executable_name = executable.rsplit("/", 1)[-1]
        if (
            executable in _KNOWN_COMMAND_EXECUTABLES
            or executable_name in _KNOWN_COMMAND_EXECUTABLES
        ):
            return len(tokens) > 1

    shell_compound_candidate = normalized_candidate
    if _SHELL_COMPOUND_PATTERN.fullmatch(shell_compound_candidate) is None:
        inline_result = _INLINE_SHELL_RESULT_SUFFIX_PATTERN.search(shell_compound_candidate)
        if inline_result is not None:
            candidate_without_result = shell_compound_candidate[: inline_result.start()].rstrip()
            if _SHELL_COMPOUND_PATTERN.fullmatch(candidate_without_result) is not None:
                shell_compound_candidate = candidate_without_result

    if _SHELL_COMPOUND_PATTERN.fullmatch(shell_compound_candidate) is not None:
        return any(
            token.strip(";(){}!").lower() in _KNOWN_COMMAND_EXECUTABLES for token in tokens[1:]
        )
    # Shell preambles and simple command chains (for example ``set -o
    # pipefail; uv run pytest ...``) are executable evidence when any command
    # in the chain is known. Keep the check token-based so arbitrary prose or
    # unknown wrappers remain fail-closed.
    if not re.match(r"^(?:if|for|while|until|case)\b", normalized_candidate, re.IGNORECASE) and any(
        operator in normalized_candidate for operator in (";", "&&", "||", "|")
    ):
        return any(token.strip(";(){}!").lower() in _KNOWN_COMMAND_EXECUTABLES for token in tokens)
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
    # Commands are often recorded with an absolute or repository-prefixed
    # interpreter path (for example ``<repo>/.venv/bin/python -m ...``).
    # Treat the basename as the executable while retaining the argument
    # requirement so ordinary prose containing a path is not accepted.
    if executable.rsplit("/", 1)[-1] in _KNOWN_COMMAND_EXECUTABLES:
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


def _executable_command_spans(text: str) -> tuple[tuple[int, int], ...]:
    """Return spans whose result-like words are still command arguments.

    ``IMPLEMENT_RESULT_PATTERN`` intentionally accepts natural-language outcome
    notes, but a broad word such as ``passed`` must not count when it occurs in
    an executable argument (for example ``pytest -k passed``).  Keep this
    distinction local to the semantic result helper so the public pattern can
    remain backwards-compatible for callers that use it for classification.
    """

    spans: list[tuple[int, int]] = []
    for pattern, group_name in (
        (_MULTILINE_BACKTICKED_FRAGMENT_PATTERN, "body"),
        (_BACKTICKED_FRAGMENT_PATTERN, None),
    ):
        for match in pattern.finditer(text):
            candidate = match.group(group_name) if group_name is not None else match.group(1)
            if _looks_like_command(candidate, explicit_container=False):
                start = match.start(group_name) if group_name is not None else match.start(1)
                end = match.end(group_name) if group_name is not None else match.end(1)
                spans.append((start, end))

    for pattern in (_PROMPT_COMMAND_PATTERN, _COMMAND_FIELD_PATTERN):
        for match in pattern.finditer(text):
            if _looks_like_command(match.group(1), explicit_container=True):
                spans.append((match.start(1), match.end(1)))

    for fence in _FENCED_COMMAND_PATTERN.finditer(text):
        body = fence.group("body")
        body_start = fence.start("body")
        for line in re.finditer(r"[^\n]*(?:\n|$)", body):
            candidate = line.group(0).rstrip("\r\n")
            normalized = candidate.strip().removeprefix("$ ").strip()
            if (
                normalized
                and not normalized.startswith("#")
                and _looks_like_command(normalized, explicit_container=True)
            ):
                spans.append((body_start + line.start(), body_start + line.end()))
    return tuple(spans)


def has_implementation_result_evidence(verification_item: str) -> bool:
    """Return whether a verification item contains an observed outcome.

    Result words inside a recognized command span are ignored unless the item
    uses an explicit outcome delimiter or an observation-like separator.  This
    prevents command arguments such as ``-k passed`` from satisfying the
    same-item command-plus-result contract.
    """

    command_spans = _executable_command_spans(verification_item)
    for match in IMPLEMENT_RESULT_PATTERN.finditer(verification_item):
        containing_span = next(
            (span for span in command_spans if span[0] <= match.start() < span[1]),
            None,
        )
        if containing_span is None:
            return True

        matched_text = match.group(0).lstrip()
        if matched_text.startswith("->"):
            return True

        prefix = verification_item[containing_span[0] : match.start()]
        if re.search(r"(?:->|[(:,;])\s*$", prefix):
            return True
    return False


def has_implementation_command_evidence(verification_item: str) -> bool:
    # Authored verification context may describe a concrete Click invocation as
    # ``click.testing.CliRunner`` invocation of ``insert ...`` instead of emitting
    # a shell executable. Treat that explicit runner + invocation shape as command
    # evidence while keeping generic prose (for example, "CliRunner passed") invalid.
    if _CLI_RUNNER_INVOCATION_PATTERN.search(verification_item) is not None:
        return True
    command_candidate = _without_non_command_artifact_text_outside_code(verification_item)
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
            if (
                normalized_line
                and not normalized_line.startswith("#")
                and _looks_like_command(
                    normalized_line,
                    explicit_container=True,
                )
            ):
                return True
    # Markdown inline code spans may contain newlines.  Runtimes commonly emit
    # heredoc verification commands in that form (for example, ``uv run
    # python - <<'PY' ... PY``).  Treat the complete span as one command so
    # valid executable evidence is not mistaken for an unverifiable prose
    # claim.  A closed span and command-shaped prefix are still required.
    for match in _MULTILINE_BACKTICKED_FRAGMENT_PATTERN.finditer(command_candidate):
        if _looks_like_command(match.group("body"), explicit_container=False):
            return True
    if backticked_command_status is False:
        # A valid command span may be followed by nested backticked result
        # references (for example, an assertion and source location). The
        # nested classifier marks the overall line as malformed, so recover
        # only when the first closed span is a complete command and its suffix
        # starts with whitespace; an unclosed nested command has text
        # immediately after the first span and remains rejected.
        for match in _BACKTICKED_FRAGMENT_PATTERN.finditer(command_candidate):
            if (
                "`" not in match.group(1)
                and re.match(r"\s", command_candidate[match.end() :]) is not None
                and _looks_like_command(match.group(1), explicit_container=False)
            ):
                return True
        return False
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
    "has_implementation_command_evidence",
    "has_implementation_result_evidence",
    "is_deferred_implementation_verification",
]
