from pathlib import Path

import pytest

from aidd.core.allowed_write_scope import (
    AllowedWriteScopeError,
    parse_allowed_write_scope,
    resolve_allowed_write_scope,
)


def _parse(markdown: str) -> object:
    return parse_allowed_write_scope(markdown, source_path=Path("allowed-write-scope.md"))


def test_parse_allowed_write_scope_preserves_order_normalizes_and_deduplicates() -> None:
    scope = _parse("# Allowed Write Scope\n\n- `./src/`\n- `pyproject.toml`\n- `src`\n")

    assert scope.prefixes == ("src", "pyproject.toml")
    assert scope.source_path == Path("allowed-write-scope.md")


@pytest.mark.parametrize(
    ("prefix", "candidate", "allowed"),
    [
        ("app.py", "app.py", True),
        ("app.py", "app.py/child", True),
        ("src", "src", True),
        ("src", "src/a.py", True),
        ("src/pkg", "src/pkg/a.py", True),
        ("src", "src2/a.py", False),
        ("src/pkg", "src/package/a.py", False),
    ],
)
def test_allowed_write_scope_uses_path_component_prefix_semantics(
    prefix: str,
    candidate: str,
    allowed: bool,
) -> None:
    scope = _parse(f"- `{prefix}`\n")
    assert scope.allows(candidate) is allowed


@pytest.mark.parametrize(
    "value",
    [
        "",
        ".",
        "..",
        "../src",
        "src/../other",
        "/src",
        "\\\\server\\share",
        "C:\\src",
        "src\\file.py",
        "src//file.py",
        "src/*",
        "src/[ab].py",
        "src/$file",
    ],
)
def test_parse_allowed_write_scope_rejects_unsafe_or_platform_specific_values(
    value: str,
) -> None:
    with pytest.raises(AllowedWriteScopeError):
        _parse(f"- `{value}`\n")


def test_parse_allowed_write_scope_rejects_empty_or_unbackticked_documents() -> None:
    with pytest.raises(AllowedWriteScopeError):
        _parse("# Allowed Write Scope\n\n- src\n")


def test_allows_rejects_unsafe_candidate() -> None:
    scope = _parse("- `src`\n")
    with pytest.raises(AllowedWriteScopeError):
        scope.allows("../src/a.py")


def test_resolve_allowed_write_scope_uses_canonical_context_path(tmp_path: Path) -> None:
    workspace = tmp_path / ".aidd"
    context = workspace / "workitems" / "WI-1" / "context"
    context.mkdir(parents=True)
    source = context / "allowed-write-scope.md"
    source.write_text("- `src`\n", encoding="utf-8")

    scope = resolve_allowed_write_scope(workspace, "WI-1")

    assert scope is not None
    assert scope.source_path == source
    assert scope.prefixes == ("src",)


def test_resolve_allowed_write_scope_distinguishes_missing_document(tmp_path: Path) -> None:
    assert resolve_allowed_write_scope(tmp_path / ".aidd", "WI-1") is None
