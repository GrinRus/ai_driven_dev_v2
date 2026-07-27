from __future__ import annotations

import json
import subprocess
from pathlib import Path
from subprocess import TimeoutExpired

import pytest

from aidd.evals.repository_changes import (
    LiveWorkspaceSnapshot,
    classify_live_workspace_changes,
    collect_live_workspace_snapshot,
    collect_repository_changes,
    live_workspace_snapshot_from_payload,
)


def _run(args: tuple[str, ...], *, cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


def _init_git_repo(repo_root: Path) -> None:
    _run(("git", "init"), cwd=repo_root)
    _run(("git", "config", "user.email", "tests@example.com"), cwd=repo_root)
    _run(("git", "config", "user.name", "AIDD Tests"), cwd=repo_root)
    (repo_root / "tracked.txt").write_text("baseline\n", encoding="utf-8")
    _run(("git", "add", "tracked.txt"), cwd=repo_root)
    _run(("git", "commit", "-m", "baseline"), cwd=repo_root)


def test_collect_repository_changes_includes_tracked_and_untracked_files(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / "tracked.txt").write_text("changed\n", encoding="utf-8")
    (tmp_path / "new.txt").write_text("new\n", encoding="utf-8")
    (tmp_path / ".aidd").mkdir()
    (tmp_path / ".aidd" / "generated.md").write_text("ignore\n", encoding="utf-8")

    changes = collect_repository_changes(tmp_path)

    assert changes.changed_files == ("tracked.txt", "new.txt")
    assert changes.tracked_files == ("tracked.txt",)
    assert changes.untracked_files == ("new.txt",)
    assert "tracked.txt" in changes.diff_summary
    assert "new.txt" in changes.diff_summary
    assert ".aidd/generated.md" not in changes.changed_files
    assert changes.command_errors == tuple()


def test_collect_repository_changes_records_git_execution_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)

    def raise_os_error(*_args: object, **_kwargs: object) -> None:
        raise OSError("git unavailable")

    monkeypatch.setattr(subprocess, "run", raise_os_error)

    changes = collect_repository_changes(tmp_path)

    assert changes.changed_files == tuple()
    assert changes.tracked_files == tuple()
    assert changes.untracked_files == tuple()
    assert len(changes.command_errors) == 3
    assert all("failed to execute" in error for error in changes.command_errors)
    assert "Git change collection errors:" in changes.diff_summary


def test_collect_repository_changes_records_git_timeout(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)

    def raise_timeout(command: object, **_kwargs: object) -> None:
        raise TimeoutExpired(command, timeout=10)

    monkeypatch.setattr(subprocess, "run", raise_timeout)

    changes = collect_repository_changes(tmp_path)

    assert changes.changed_files == tuple()
    assert len(changes.command_errors) == 3
    assert all("timed out after 10s" in error for error in changes.command_errors)


def test_collect_live_workspace_snapshot_includes_aidd_untracked_files(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".aidd").mkdir()
    (tmp_path / ".aidd" / "research_repro.py").write_text("print('x')\n", encoding="utf-8")
    (tmp_path / "aidd.example.toml").write_text("[runtime]\n", encoding="utf-8")

    snapshot = collect_live_workspace_snapshot(tmp_path)

    assert ".aidd/research_repro.py" in snapshot.untracked_files
    assert "aidd.example.toml" in snapshot.untracked_files
    assert ".aidd/research_repro.py" in snapshot.status_short
    assert snapshot.ignored_files == tuple()
    assert snapshot.command_errors == tuple()


def test_collect_live_workspace_snapshot_records_ignored_workspace_files(
    tmp_path: Path,
) -> None:
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(
        ".venv/\ncoverage/\n.pdm-build/\n.pytest_cache/\n",
        encoding="utf-8",
    )
    _run(("git", "add", ".gitignore"), cwd=tmp_path)
    _run(("git", "commit", "-m", "ignore local artifacts"), cwd=tmp_path)
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "pyvenv.cfg").write_text("home = test\n", encoding="utf-8")
    (tmp_path / "coverage").mkdir()
    (tmp_path / "coverage" / "index.html").write_text("coverage\n", encoding="utf-8")
    (tmp_path / ".pdm-build").mkdir()
    (tmp_path / ".pdm-build" / "wheel").write_text("wheel\n", encoding="utf-8")
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".pytest_cache" / "CACHEDIR.TAG").write_text("cache\n", encoding="utf-8")

    snapshot = collect_live_workspace_snapshot(tmp_path)

    assert ".venv/pyvenv.cfg" in snapshot.ignored_files
    assert "coverage/index.html" in snapshot.ignored_files
    assert ".pdm-build/wheel" in snapshot.ignored_files
    assert ".pytest_cache/CACHEDIR.TAG" in snapshot.ignored_files
    assert snapshot.command_errors == tuple()


def test_classify_live_workspace_changes_separates_baseline_harness_and_pollution() -> None:
    baseline = LiveWorkspaceSnapshot(
        tracked_files=tuple(),
        untracked_files=("setup.log", "aidd.example.toml"),
        status_short="?? setup.log\n?? aidd.example.toml",
        command_errors=tuple(),
        ignored_files=tuple(),
    )
    final = LiveWorkspaceSnapshot(
        tracked_files=("src/app.py",),
        untracked_files=(
            "setup.log",
            "aidd.example.toml",
            "workitems/WI-1/stages/qa/stage-result.md",
            ".aidd/research_repro.py",
            ".aidd/harness-cache/runtime-prompts/run-1/plan/opencode-prompt.md",
            ".aidd/workitems/WI-1/stages/qa/output/qa-report.md",
            "new_product.py",
        ),
        status_short="",
        command_errors=tuple(),
        ignored_files=(
            ".venv/pyvenv.cfg",
            "coverage/index.html",
        ),
    )

    classification = classify_live_workspace_changes(
        baseline_snapshot=baseline,
        final_snapshot=final,
    )

    assert classification.tracked_files == ("src/app.py",)
    assert classification.baseline_untracked_files == ("setup.log", "aidd.example.toml")
    assert classification.known_harness_files == ("aidd.example.toml",)
    assert classification.new_untracked_files == (
        "workitems/WI-1/stages/qa/stage-result.md",
        ".aidd/research_repro.py",
        ".aidd/harness-cache/runtime-prompts/run-1/plan/opencode-prompt.md",
        ".aidd/workitems/WI-1/stages/qa/output/qa-report.md",
        "new_product.py",
    )
    assert classification.baseline_ignored_files == tuple()
    assert classification.setup_baseline_ignored_churn_files == tuple()
    assert classification.new_ignored_files == (
        ".venv/pyvenv.cfg",
        "coverage/index.html",
    )
    assert classification.unexpected_ignored_workspace_files == (
        ".venv/pyvenv.cfg",
        "coverage/index.html",
    )
    assert classification.unexpected_top_level_workitems_files == (
        "workitems/WI-1/stages/qa/stage-result.md",
    )
    assert classification.unexpected_aidd_internal_files == (".aidd/research_repro.py",)
    assert classification.unexpected_non_aidd_untracked_files == (
        "workitems/WI-1/stages/qa/stage-result.md",
        "new_product.py",
    )
    assert [finding.kind for finding in classification.non_gating_findings] == [
        "unexpected-top-level-workitems-artifact",
        "unexpected-non-aidd-untracked-file",
        "unexpected-aidd-internal-scratch-file",
        "unexpected-ignored-workspace-artifact",
        "unexpected-ignored-workspace-artifact",
    ]


def test_classify_live_workspace_changes_separates_baseline_ignored_churn() -> None:
    baseline = LiveWorkspaceSnapshot(
        tracked_files=tuple(),
        untracked_files=tuple(),
        status_short="",
        command_errors=tuple(),
        ignored_files=(
            ".venv/pyvenv.cfg",
            ".pdm-build/wheel",
        ),
    )
    final = LiveWorkspaceSnapshot(
        tracked_files=tuple(),
        untracked_files=tuple(),
        status_short="",
        command_errors=tuple(),
        ignored_files=(
            ".venv/pyvenv.cfg",
            ".pdm-build/wheel",
            ".venv/lib/python3.10/site-packages/pkg/__pycache__/mod.cpython-310.pyc",
            ".pdm-build/pkg.dist-info/RECORD",
            ".pytest_cache/CACHEDIR.TAG",
            "starlette/__pycache__/responses.cpython-313.pyc",
        ),
    )

    classification = classify_live_workspace_changes(
        baseline_snapshot=baseline,
        final_snapshot=final,
    )

    assert classification.new_ignored_files == (
        ".venv/lib/python3.10/site-packages/pkg/__pycache__/mod.cpython-310.pyc",
        ".pdm-build/pkg.dist-info/RECORD",
        ".pytest_cache/CACHEDIR.TAG",
        "starlette/__pycache__/responses.cpython-313.pyc",
    )
    assert classification.setup_baseline_ignored_churn_files == (
        ".venv/lib/python3.10/site-packages/pkg/__pycache__/mod.cpython-310.pyc",
        ".pdm-build/pkg.dist-info/RECORD",
    )
    assert classification.unexpected_ignored_workspace_files == (
        ".pytest_cache/CACHEDIR.TAG",
        "starlette/__pycache__/responses.cpython-313.pyc",
    )
    assert [finding.kind for finding in classification.non_gating_findings] == [
        "unexpected-ignored-workspace-artifact",
        "unexpected-ignored-workspace-artifact",
    ]


def test_collect_live_workspace_snapshot_records_git_execution_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _init_git_repo(tmp_path)

    def raise_os_error(*_args: object, **_kwargs: object) -> None:
        raise OSError("git unavailable")

    monkeypatch.setattr(subprocess, "run", raise_os_error)

    snapshot = collect_live_workspace_snapshot(tmp_path)

    assert snapshot.tracked_files == tuple()
    assert snapshot.untracked_files == tuple()
    assert len(snapshot.command_errors) == 4
    assert all("failed to execute" in error for error in snapshot.command_errors)


def test_ignored_inventory_is_digest_backed_and_bounded_at_large_scale() -> None:
    ignored_files = tuple(
        f"node_modules/package-{index:05d}/cache/file-{index:05d}.js"
        for index in range(20_000)
    )
    snapshot = LiveWorkspaceSnapshot(
        tracked_files=("src/modified.py", "src/deleted.py"),
        untracked_files=("src/new.py",),
        status_short=" M src/modified.py\n D src/deleted.py\n?? src/new.py",
        command_errors=tuple(),
        ignored_files=ignored_files,
        modified_files=("src/modified.py",),
        deleted_files=("src/deleted.py",),
    )

    payload = snapshot.to_payload()
    inventory = payload["ignored_inventory"]
    assert isinstance(inventory, dict)
    assert inventory["total_count"] == 20_000
    assert inventory["group_count"] == 1
    assert inventory["groups"] == [
        {"root": "node_modules/", "type": "dependency", "count": 20_000}
    ]
    assert len(inventory["sample"]) == 50
    assert inventory["truncated"] is True
    assert inventory["groups_truncated"] is False
    assert len(inventory["sha256"]) == 64
    assert "ignored_files" not in payload
    assert len(json.dumps(payload)) < 10_000
    assert payload["tracked_files"] == ["src/modified.py", "src/deleted.py"]
    assert payload["untracked_files"] == ["src/new.py"]
    assert payload["modified_files"] == ["src/modified.py"]
    assert payload["deleted_files"] == ["src/deleted.py"]

    restored = live_workspace_snapshot_from_payload(payload)
    assert restored.ignored_inventory is not None
    assert restored.ignored_inventory.total_count == 20_000
    assert restored.ignored_inventory.sha256 == inventory["sha256"]
    assert restored.tracked_files == snapshot.tracked_files
    assert restored.untracked_files == snapshot.untracked_files
    assert restored.modified_files == snapshot.modified_files
    assert restored.deleted_files == snapshot.deleted_files

    classification = classify_live_workspace_changes(
        baseline_snapshot=LiveWorkspaceSnapshot(
            tracked_files=tuple(),
            untracked_files=tuple(),
            status_short="",
            command_errors=tuple(),
        ),
        final_snapshot=snapshot,
    )
    classification_payload = classification.to_payload()
    new_inventory = classification_payload["new_ignored_inventory"]
    assert isinstance(new_inventory, dict)
    assert new_inventory["total_count"] == 20_000
    assert new_inventory["sha256"] == inventory["sha256"]
    assert len(json.dumps(classification_payload)) < 20_000
    ignored_findings = tuple(
        finding
        for finding in classification.non_gating_findings
        if finding.kind.startswith("unexpected-ignored-workspace-artifact")
    )
    assert len(ignored_findings) == 51
