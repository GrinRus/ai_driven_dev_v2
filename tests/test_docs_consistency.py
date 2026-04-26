from __future__ import annotations

import re
from pathlib import Path

import pytest

from aidd.core.contracts import repo_root_from
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    resolve_prompt_pack_file_paths,
    resolve_prompt_pack_paths,
)
from aidd.core.stages import STAGES

_USER_STORY_ID_PATTERN = re.compile(r"^###\s+(US-\d+)\b", re.MULTILINE)
_ROADMAP_STORY_ID_PATTERN = re.compile(r"\bUS-\d+\b")
_REQUIRED_RELEASE_VERIFICATION_JOB_IDS: tuple[str, ...] = (
    "verify-pypi-install",
    "verify-uv-tool-install",
    "verify-ghcr-install",
)


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def test_roadmap_references_only_existing_user_story_ids() -> None:
    repo_root = _repo_root()
    user_stories_path = repo_root / "docs" / "product" / "user-stories.md"
    roadmap_path = repo_root / "docs" / "backlog" / "roadmap.md"

    declared_story_ids = set(_USER_STORY_ID_PATTERN.findall(user_stories_path.read_text("utf-8")))
    referenced_story_ids = set(_ROADMAP_STORY_ID_PATTERN.findall(roadmap_path.read_text("utf-8")))
    unknown_story_ids = sorted(referenced_story_ids - declared_story_ids)

    assert not unknown_story_ids, (
        "Roadmap references unknown user story ids: "
        f"{', '.join(unknown_story_ids)}"
    )


def test_stage_contract_prompt_pack_paths_exist() -> None:
    contracts_root = DEFAULT_STAGE_CONTRACTS_ROOT
    missing_prompt_pack_paths: list[str] = []

    for stage in STAGES:
        try:
            prompt_pack_paths = resolve_prompt_pack_paths(
                stage=stage,
                contracts_root=contracts_root,
            )
            prompt_pack_file_paths = resolve_prompt_pack_file_paths(
                stage=stage,
                contracts_root=contracts_root,
            )
        except ValueError as exc:
            pytest.fail(f"Stage '{stage}' has invalid prompt-pack declarations: {exc}")
        if not prompt_pack_paths:
            missing_prompt_pack_paths.append(f"{stage}:<none>")
            continue
        for prompt_pack_path, prompt_pack_file_path in zip(
            prompt_pack_paths,
            prompt_pack_file_paths,
            strict=True,
        ):
            if not prompt_pack_file_path.exists():
                missing_prompt_pack_paths.append(f"{stage}:{prompt_pack_path}")

    assert not missing_prompt_pack_paths, (
        "Missing prompt-pack paths declared in stage contracts: "
        f"{', '.join(missing_prompt_pack_paths)}"
    )


def test_release_checklist_requires_verification_job_evidence() -> None:
    release_checklist_path = _repo_root() / "docs" / "release-checklist.md"
    release_checklist = release_checklist_path.read_text(encoding="utf-8")
    missing_job_references = [
        job_id
        for job_id in _REQUIRED_RELEASE_VERIFICATION_JOB_IDS
        if job_id not in release_checklist
    ]

    assert not missing_job_references, (
        "Release checklist is missing required verification job references: "
        f"{', '.join(missing_job_references)}"
    )
    assert "required release evidence for tagged builds" in release_checklist.lower()


def test_operator_docs_describe_live_manual_providers_and_execution_wrappers() -> None:
    readme = (_repo_root() / "README.md").read_text(encoding="utf-8")
    operator_handbook = (_repo_root() / "docs" / "operator-handbook.md").read_text(
        encoding="utf-8"
    )
    adapter_protocol = (
        _repo_root() / "docs" / "architecture" / "adapter-protocol.md"
    ).read_text(encoding="utf-8")
    runtime_matrix = (_repo_root() / "docs" / "architecture" / "runtime-matrix.md").read_text(
        encoding="utf-8"
    )

    assert (
        "aidd eval run harness/scenarios/live/typer-styled-help-alignment.yaml --runtime codex"
        in readme
    )
    assert (
        "aidd eval run harness/scenarios/live/typer-styled-help-alignment.yaml "
        "--runtime generic-cli"
        not in readme
    )
    assert "AIDD-compatible wrapper commands" in readme
    assert "mode = \"native\"" in operator_handbook
    assert "mode = \"adapter-flags\"" in operator_handbook
    assert "codex exec --full-auto --skip-git-repo-check --json -" in operator_handbook
    assert "opencode run --format json --dangerously-skip-permissions" in operator_handbook
    assert "probe target and the execution command do not have to be identical" in adapter_protocol
    assert "`native` execution" in runtime_matrix


def test_live_e2e_skill_describes_local_operator_contract() -> None:
    live_e2e_skill = (_repo_root() / ".agents" / "skills" / "live-e2e" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    aidd_eval_skill = (_repo_root() / ".agents" / "skills" / "aidd-eval" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    for needle in (
        "prepared local **source checkout**",
        "`AIDD_EVAL_CODEX_COMMAND`",
        "`AIDD_EVAL_OPENCODE_COMMAND`",
        "native provider CLI",
        "AIDD-compatible wrapper command",
        "aidd eval doctor",
        (
            "uv run aidd eval run "
            "harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml "
            "--runtime codex"
        ),
        "first listed issue",
        "`idea -> qa`",
        "`.aidd/reports/evals/<run_id>/`",
        "does **not** provision runtime authentication, wrapper scripts, or provider setup",
    ):
        assert needle in live_e2e_skill

    assert "For **local live-run operator guidance**, prefer `live-e2e`." in aidd_eval_skill
