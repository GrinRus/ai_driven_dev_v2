from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from aidd.core.stages import is_valid_stage


@dataclass(frozen=True, slots=True)
class StageDocumentDeclaration:
    path: str
    required: bool = True

    def __post_init__(self) -> None:
        normalized_path = self.path.strip()
        if not normalized_path:
            raise ValueError("Document path must be a non-empty string.")
        candidate = Path(normalized_path)
        if candidate.is_absolute():
            raise ValueError(f"Document path must be relative, got: {self.path}")
        object.__setattr__(self, "path", normalized_path)


@dataclass(frozen=True, slots=True)
class StageManifest:
    stage: str
    required_inputs: tuple[StageDocumentDeclaration, ...]
    required_outputs: tuple[StageDocumentDeclaration, ...]
    optional_inputs: tuple[StageDocumentDeclaration, ...] = ()
    purpose: str | None = None

    def __post_init__(self) -> None:
        if not is_valid_stage(self.stage):
            raise ValueError(f"Unknown stage: {self.stage}")
        if not self.required_inputs:
            raise ValueError("Stage manifest must declare at least one required input document.")
        if not self.required_outputs:
            raise ValueError("Stage manifest must declare at least one required output document.")

        self._assert_unique_paths(self.required_inputs, "required_inputs")
        self._assert_unique_paths(self.optional_inputs, "optional_inputs")
        self._assert_unique_paths(self.required_outputs, "required_outputs")
        self._assert_disjoint_paths(
            left=self.required_inputs,
            left_name="required_inputs",
            right=self.optional_inputs,
            right_name="optional_inputs",
        )

    @staticmethod
    def _assert_unique_paths(
        declarations: tuple[StageDocumentDeclaration, ...],
        field_name: str,
    ) -> None:
        seen_paths: set[str] = set()
        for declaration in declarations:
            if declaration.path in seen_paths:
                raise ValueError(
                    f"Duplicate document declaration in {field_name}: {declaration.path}"
                )
            seen_paths.add(declaration.path)

    @staticmethod
    def _assert_disjoint_paths(
        *,
        left: tuple[StageDocumentDeclaration, ...],
        left_name: str,
        right: tuple[StageDocumentDeclaration, ...],
        right_name: str,
    ) -> None:
        left_paths = {declaration.path for declaration in left}
        right_paths = {declaration.path for declaration in right}
        overlap = sorted(left_paths & right_paths)
        if overlap:
            joined = ", ".join(overlap)
            raise ValueError(
                f"Document declaration cannot appear in both {left_name} and "
                f"{right_name}: {joined}"
            )

    @classmethod
    def from_document_paths(
        cls,
        *,
        stage: str,
        required_inputs: Iterable[str],
        required_outputs: Iterable[str],
        optional_inputs: Iterable[str] = (),
        purpose: str | None = None,
    ) -> StageManifest:
        return cls(
            stage=stage,
            required_inputs=tuple(
                StageDocumentDeclaration(path=path, required=True) for path in required_inputs
            ),
            optional_inputs=tuple(
                StageDocumentDeclaration(path=path, required=False) for path in optional_inputs
            ),
            required_outputs=tuple(
                StageDocumentDeclaration(path=path, required=True) for path in required_outputs
            ),
            purpose=purpose.strip() if purpose else None,
        )

    @property
    def required_input_paths(self) -> tuple[str, ...]:
        return tuple(declaration.path for declaration in self.required_inputs)

    @property
    def optional_input_paths(self) -> tuple[str, ...]:
        return tuple(declaration.path for declaration in self.optional_inputs)

    @property
    def required_output_paths(self) -> tuple[str, ...]:
        return tuple(declaration.path for declaration in self.required_outputs)
