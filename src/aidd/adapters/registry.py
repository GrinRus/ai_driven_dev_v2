"""The built-in adapter registry.

This module is the only place where the maintained adapter packages are assembled.  The
runtime-agnostic catalog consumes the descriptors exposed here, while individual adapter
packages remain responsible for their own runtime/configuration compatibility metadata.
"""

from __future__ import annotations

from aidd.adapters.base import RuntimeAdapterDescriptor
from aidd.adapters.claude_code import DESCRIPTOR as CLAUDE_CODE_DESCRIPTOR
from aidd.adapters.codex import DESCRIPTOR as CODEX_DESCRIPTOR
from aidd.adapters.generic_cli import DESCRIPTOR as GENERIC_CLI_DESCRIPTOR
from aidd.adapters.opencode import DESCRIPTOR as OPENCODE_DESCRIPTOR
from aidd.adapters.qwen import DESCRIPTOR as QWEN_DESCRIPTOR

BUILTIN_RUNTIME_ADAPTER_DESCRIPTORS: tuple[RuntimeAdapterDescriptor, ...] = (
    GENERIC_CLI_DESCRIPTOR,
    CLAUDE_CODE_DESCRIPTOR,
    CODEX_DESCRIPTOR,
    OPENCODE_DESCRIPTOR,
    QWEN_DESCRIPTOR,
)


def runtime_adapter_descriptors() -> tuple[RuntimeAdapterDescriptor, ...]:
    """Return maintained adapter descriptors in their stable compatibility order."""

    return BUILTIN_RUNTIME_ADAPTER_DESCRIPTORS


__all__ = ["BUILTIN_RUNTIME_ADAPTER_DESCRIPTORS", "runtime_adapter_descriptors"]
