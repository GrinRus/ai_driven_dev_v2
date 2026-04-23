from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConformanceRow:
    runtime_id: str
    dimensions: dict[str, str]


@dataclass(frozen=True)
class RuntimeConformanceMatrix:
    dimensions: tuple[str, ...]
    rows: tuple[RuntimeConformanceRow, ...]

    def runtime_ids(self) -> tuple[str, ...]:
        return tuple(row.runtime_id for row in self.rows)


def load_runtime_conformance_matrix(path: Path) -> RuntimeConformanceMatrix:
    table = _find_runtime_table(path.read_text(encoding="utf-8").splitlines(), source_path=path)
    headers = _parse_table_cells(table[0], source_path=path)
    if len(headers) < 2:
        raise ValueError(
            f"Conformance matrix table must include one runtime column and one dimension: {path}"
        )

    dimension_headers = tuple(_normalize_dimension_name(value) for value in headers[1:])
    if len(set(dimension_headers)) != len(dimension_headers):
        raise ValueError(f"Conformance matrix contains duplicate dimension headers: {path}")

    rows: list[RuntimeConformanceRow] = []
    seen_runtimes: set[str] = set()
    for line in table[2:]:
        cells = _parse_table_cells(line, source_path=path)
        if len(cells) != len(headers):
            raise ValueError(
                "Conformance matrix row has mismatched column count: "
                f"expected={len(headers)} got={len(cells)} in {path}"
            )

        runtime_id = _normalize_runtime_id(cells[0])
        if runtime_id in seen_runtimes:
            raise ValueError(f"Conformance matrix contains duplicate runtime row: {runtime_id}")
        seen_runtimes.add(runtime_id)

        dimensions = {
            dimension_name: _normalize_dimension_status(value)
            for dimension_name, value in zip(dimension_headers, cells[1:], strict=True)
        }
        rows.append(RuntimeConformanceRow(runtime_id=runtime_id, dimensions=dimensions))

    if not rows:
        raise ValueError(f"Conformance matrix table must include at least one runtime row: {path}")

    return RuntimeConformanceMatrix(dimensions=dimension_headers, rows=tuple(rows))


def _find_runtime_table(lines: list[str], *, source_path: Path) -> list[str]:
    tables = _collect_markdown_tables(lines)
    for table in tables:
        if len(table) < 3:
            continue
        headers = _parse_table_cells(table[0], source_path=source_path)
        if headers and _normalize_dimension_name(headers[0]) == "runtime":
            return table
    raise ValueError(f"Could not find a runtime conformance matrix table in {source_path}")


def _collect_markdown_tables(lines: list[str]) -> list[list[str]]:
    tables: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.strip().startswith("|"):
            current.append(line)
            continue
        if current:
            tables.append(current)
            current = []
    if current:
        tables.append(current)
    return tables


def _parse_table_cells(line: str, *, source_path: Path) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|"):
        raise ValueError(f"Conformance matrix contains invalid table row in {source_path}: {line}")
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _normalize_runtime_id(value: str) -> str:
    runtime_id = value.strip().strip("`")
    if not runtime_id:
        raise ValueError("Conformance matrix runtime id must be a non-empty string.")
    return runtime_id


def _normalize_dimension_name(value: str) -> str:
    name = value.strip().strip("`").lower().replace(" ", "_")
    if not name:
        raise ValueError("Conformance matrix dimension name must be a non-empty string.")
    return name


def _normalize_dimension_status(value: str) -> str:
    status = value.strip().strip("`").lower()
    if not status:
        raise ValueError("Conformance matrix dimension status must be a non-empty string.")
    return status

