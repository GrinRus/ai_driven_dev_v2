from __future__ import annotations

import re
import tomllib
from dataclasses import fields
from pathlib import Path

import pytest

from aidd.adapters.surface import RuntimeAdapterExecutionResult
from aidd.core.contracts import repo_root_from
from aidd.core.stage_registry import (
    DEFAULT_STAGE_CONTRACTS_ROOT,
    resolve_prompt_pack_file_paths,
    resolve_prompt_pack_paths,
)
from aidd.core.stages import STAGES
from aidd.runtime_catalog import runtime_definitions, runtime_ids

_USER_STORY_ID_PATTERN = re.compile(r"^###\s+(US-\d+)\b", re.MULTILINE)
_ROADMAP_STORY_ID_PATTERN = re.compile(r"\bUS-\d+\b")
_ACCEPTED_RELEASE_EVIDENCE_HEADING_PATTERN = re.compile(
    r"^### `v(?P<version>\d+\.\d+\.\d+a\d+)` accepted evidence",
    re.MULTILINE,
)
_REQUIRED_RELEASE_VERIFICATION_JOB_IDS: tuple[str, ...] = (
    "verify-pypi-install",
    "verify-uv-tool-install",
)
_CURRENT_CANONICAL_DOCS: tuple[str, ...] = (
    "README.md",
    "docs/operator-handbook.md",
    "docs/operator-troubleshooting.md",
    "docs/operator-support-policy.md",
    "docs/compatibility-policy.md",
    "docs/architecture/adapter-protocol.md",
    "docs/architecture/document-contracts.md",
    "docs/architecture/runtime-matrix.md",
    "docs/architecture/target-architecture.md",
)
_STALE_CURRENT_DOC_WORDING: tuple[str, ...] = (
    "bootstrap repository",
    "executable scaffold",
    "complete, consistent starting repository",
    "starter repository",
    "starting repository",
    "python package skeleton",
    "bootstrap smoke tests",
    "bootstrap cli",
    "bootstrap behavior",
    "bootstrap mode",
    "mvp maintained adapters",
    "planned adapters",
    "planned/limited",
    "as of april 22, 2026",
)


def _repo_root() -> Path:
    return repo_root_from(Path(__file__).resolve())


def _project_version(repo_root: Path) -> str:
    pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    project = pyproject["project"]
    assert isinstance(project, dict)
    version = project["version"]
    assert isinstance(version, str)
    return version


def _latest_accepted_prerelease_version(release_checklist: str) -> str:
    matches = _ACCEPTED_RELEASE_EVIDENCE_HEADING_PATTERN.findall(release_checklist)
    assert matches, "Release checklist must record at least one accepted prerelease evidence entry."
    return matches[0]


def _is_development_version(version: str) -> bool:
    return ".dev" in version


def test_current_docs_do_not_reintroduce_bootstrap_or_planned_adapter_wording() -> None:
    repo_root = _repo_root()
    stale_matches: list[str] = []

    for relative_path in _CURRENT_CANONICAL_DOCS:
        text = (repo_root / relative_path).read_text(encoding="utf-8").lower()
        for stale_wording in _STALE_CURRENT_DOC_WORDING:
            if stale_wording in text:
                stale_matches.append(f"{relative_path}:{stale_wording}")

    assert not stale_matches, (
        "Current canonical docs contain stale bootstrap or planned-adapter wording: "
        f"{', '.join(stale_matches)}"
    )


def test_runtime_support_docs_name_registered_runtimes_and_tiers() -> None:
    repo_root = _repo_root()
    adapter_protocol = (
        repo_root / "docs" / "architecture" / "adapter-protocol.md"
    ).read_text(encoding="utf-8")
    runtime_matrix = (
        repo_root / "docs" / "architecture" / "runtime-matrix.md"
    ).read_text(encoding="utf-8")
    readme = (repo_root / "README.md").read_text(encoding="utf-8")

    for runtime_id in runtime_ids():
        assert f"`{runtime_id}`" in adapter_protocol
        assert f"`{runtime_id}`" in runtime_matrix
        assert runtime_id in readme

    for definition in runtime_definitions():
        expected_tier = definition.support_tier.replace("tier-", "Tier ")
        assert expected_tier in runtime_matrix


def test_adapter_protocol_documents_current_execution_result_surface() -> None:
    repo_root = _repo_root()
    adapter_protocol = (
        repo_root / "docs" / "architecture" / "adapter-protocol.md"
    ).read_text(encoding="utf-8")
    result_fields = {field.name for field in fields(RuntimeAdapterExecutionResult)}

    assert result_fields == {
        "details",
        "events_jsonl_path",
        "operator_decisions_path",
        "operator_requests_path",
        "pending_operator_request_ids",
        "questions_path",
        "runtime_jsonl_path",
        "status",
        "succeeded",
    }
    for expected_text in (
        "whether the runtime invocation succeeded",
        "a normalized details string",
        "`succeeded`, `failed`, or `blocked_for_operator`",
        "`runtime.jsonl` and `events.jsonl`",
        "`operator-requests.jsonl` and `operator-decisions.jsonl`",
        "`questions.md`",
        "in-memory workflow semantics",
    ):
        assert expected_text in adapter_protocol


def test_artifact_ownership_docs_and_prompt_packs_are_consistent() -> None:
    repo_root = _repo_root()
    document_contracts = (
        repo_root / "docs" / "architecture" / "document-contracts.md"
    ).read_text(encoding="utf-8")
    stage_result_contract = (
        repo_root / "contracts" / "documents" / "stage-result.md"
    ).read_text(encoding="utf-8")
    questions_contract = (
        repo_root / "contracts" / "documents" / "questions.md"
    ).read_text(encoding="utf-8")

    assert "`validator-report.md` is AIDD-canonical" in document_contracts
    assert "`repair-brief.md` is not runtime-authored" in document_contracts
    assert "nested or indented bullets" in questions_contract.lower()
    assert "nested or indented bullets" in document_contracts.lower()
    assert "AIDD treats it as the\nworkflow-facing summary" in stage_result_contract

    for stage in STAGES:
        stage_contract = (
            repo_root / "contracts" / "stages" / f"{stage}.md"
        ).read_text(encoding="utf-8")
        run_prompt = (
            repo_root / "prompt-packs" / "stages" / stage / "run.md"
        ).read_text(encoding="utf-8")

        assert "runtime-authored summary draft" in stage_contract
        assert "canonical only after AIDD writes the post-runtime validation report" in (
            stage_contract
        )
        assert "Treat `validator-report.md` as draft evidence" in run_prompt
        assert "Treat `stage-result.md` as a truthful summary draft" in run_prompt


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
    assert "required release evidence for published github release alpha builds" in (
        release_checklist.lower()
    )
    assert "does not publish or support docker/ghcr images during the alpha phase" in (
        release_checklist.lower()
    )


def test_release_readiness_docs_keep_candidate_and_accepted_versions_distinct() -> None:
    repo_root = _repo_root()
    source_version = _project_version(repo_root)
    release_checklist = (repo_root / "docs" / "release-checklist.md").read_text(
        encoding="utf-8"
    )
    latest_accepted_version = _latest_accepted_prerelease_version(release_checklist)
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    changelog = (repo_root / "CHANGELOG.md").read_text(encoding="utf-8")
    beta_audit = (
        repo_root / "docs" / "analysis" / "beta-readiness-source-audit.md"
    ).read_text(encoding="utf-8")

    readme_install_section = readme.split("## Install with pipx", 1)[1].split(
        "## Container support",
        1,
    )[0]
    assert f'ai-driven-dev-v2=={latest_accepted_version}' in readme_install_section
    assert f'ai-driven-dev-v2=={source_version}' not in readme_install_section

    assert latest_accepted_version != source_version

    if _is_development_version(source_version):
        assert source_version not in readme
        assert "Current source development package version" not in readme
        assert (
            f"Latest published prerelease: `{latest_accepted_version}`."
            in readme
        )
        assert (
            "The `main` branch is development source and may contain unreleased changes."
            in readme
        )
        assert "Install the latest published prerelease:" in readme_install_section
        assert f"## {source_version} -" not in changelog
        assert f"`{source_version}`" not in changelog
        assert (
            f"source development package version matches the package state: `{source_version}`"
            in beta_audit
        )
        assert (
            f"latest accepted published prerelease evidence is `{latest_accepted_version}`"
            in beta_audit
        )
        assert "## Maintainer release state" in release_checklist
        assert f"Maintainer source development package version: `{source_version}`." in (
            release_checklist
        )
        assert (
            f"Latest accepted published prerelease evidence: `{latest_accepted_version}`."
            in release_checklist
        )
        assert f"### `v{source_version}` accepted evidence" not in release_checklist
        assert "No current release candidate is accepted from this development version." in (
            release_checklist
        )
    else:
        release_notes_path = (
            repo_root / "docs" / f"release-notes-v{source_version}-draft.md"
        )
        release_notes = release_notes_path.read_text(encoding="utf-8")

        assert (
            f"Current release-candidate package version on this branch: `{source_version}`."
            in readme
        )
        assert (
            "Latest accepted published prerelease evidence before this candidate: "
            f"`{latest_accepted_version}`."
        ) in readme

        assert f"## {source_version} -" in changelog
        assert (
            f"release-candidate package version matches the package state: `{source_version}`"
            in beta_audit
        )
        assert (
            "last accepted published prerelease evidence before this candidate is "
            f"`{latest_accepted_version}`"
        ) in beta_audit
        assert f"Current release-candidate package version: `{source_version}`." in (
            release_checklist
        )
        assert (
            "Latest accepted published prerelease evidence before this candidate: "
            f"`{latest_accepted_version}`."
        ) in release_checklist
        assert f"accepted `v{source_version}` evidence log entry" in release_checklist
        assert f"### `v{source_version}` accepted evidence" not in release_checklist
        assert "Status: draft, not tagged or published." in release_notes
        assert f"Current release-candidate package version: `{source_version}`." in (
            release_notes
        )
        assert (
            "Latest accepted published prerelease evidence before this candidate: "
            f"`{latest_accepted_version}`."
        ) in release_notes
        assert (
            f"`{source_version}` package must not be described as the latest accepted "
            "published prerelease"
        ) in release_notes


def test_operator_ui_docs_and_backlog_queue_stay_synchronized() -> None:
    repo_root = _repo_root()
    source_version = _project_version(repo_root)
    release_checklist = (repo_root / "docs" / "release-checklist.md").read_text(
        encoding="utf-8"
    )
    latest_accepted_version = _latest_accepted_prerelease_version(release_checklist)
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    roadmap = (repo_root / "docs" / "backlog" / "roadmap.md").read_text(
        encoding="utf-8"
    )
    operator_frontend = (
        repo_root / "docs" / "architecture" / "operator-frontend.md"
    ).read_text(encoding="utf-8")
    backlog = (repo_root / "docs" / "backlog" / "backlog.md").read_text(
        encoding="utf-8"
    )
    w24_s1 = roadmap.split("#### Slice W24-E1-S1", 1)[1].split(
        "#### Slice W24-E1-S2",
        1,
    )[0]
    w24_s2 = roadmap.split("#### Slice W24-E1-S2", 1)[1].split("## Wave", 1)[0]
    w26 = roadmap.split("## Wave 26", 1)[1]
    backlog_next = backlog.split("## Next", 1)[1].split("## Soon", 1)[0]
    backlog_soon = backlog.split("## Soon", 1)[1].split("## Parking lot", 1)[0]
    backlog_parking = backlog.split("## Parking lot", 1)[1].split("## Update rules", 1)[0]

    assert (
        "The UI can write question answers as `[resolved]`, `[partial]`, or "
        "`[deferred]` entries"
    ) in readme
    assert "only `[resolved]` answers unblock blocking questions" in readme
    assert "The UI writes question answers as `[resolved]` entries" not in readme

    assert (
        f"latest accepted `{latest_accepted_version}` package-channel evidence"
        in w24_s1
    )
    assert f"`{source_version}` source development state" in w24_s1
    assert "v0.1.0a3" not in w24_s1

    assert "## Wave 24 — beta readiness release preparation (`done`)" in roadmap
    assert "#### Slice W24-E1-S2 — manual live beta evidence refresh (`done`)" in roadmap
    assert "`W24-E1-S2-T1` (done)" in w24_s2
    assert "`W24-E1-S2-T2` (done)" in w24_s2
    assert "`W24-E1-S2-T3` (done)" in w24_s2

    assert "## Wave 26 — completed-flow lineage operator experience (`next`)" in roadmap
    assert "`W26-E0-S1-T1` (done)" in w26
    assert "### Epic W26-E1 — flow lineage core model and launch services (`done`)" in w26
    assert "`W26-E1-S1-T1` (done) Add a terminal-run handoff read model" in w26
    assert "`W26-E1-S1-T2` (done) Add lineage reference fields" in w26
    assert "`W26-E1-S2-T1` (done) Implement a follow-up draft service" in w26
    assert "`W26-E1-S2-T2` (done) Implement a clone-flow draft service" in w26
    assert "`W26-E1-S2-T3` (done) Add launch preflight validation" in w26
    assert "#### Slice W26-E1-S3 — workbench and evidence read models (`done`)" in w26
    assert "#### Slice W26-E2-S0 — static UI refactoring foundation (`done`)" in w26
    assert "`W26-E2-S0-T1` (done) Add a packaged static asset manifest" in w26
    assert "`W26-E2-S0-T2` (done) Split `operator.js`" in w26
    assert "`W26-E2-S0-T3` (done) Split `operator.css`" in w26
    assert "`W26-E2-S0-T4` (done) Split monolithic script-string assertions" in w26
    assert "`W26-E1-S3-T1` (done) Add a stage document workbench read model" in w26
    assert "`W26-E1-S3-T2` (done) Add recovery and diagnostics read-model fields" in w26
    assert "`W26-E1-S3-T3` (done) Add an evidence graph read model" in w26
    assert (
        "`W26-E4-S2-T1` Define the manual live E2E next-flow checkpoint policy"
        in w26
    )
    assert "`W26-E2-S1-T1`" in backlog_next
    assert "`W26-E1-S1-T1`" not in backlog_next
    assert "`W26-E1-S1-T2`" not in backlog_next
    assert "`W26-E1-S2-T1`" not in backlog_next
    assert "`W26-E1-S2-T2`" not in backlog_next
    assert "`W26-E1-S2-T3`" not in backlog_next
    assert "`W26-E2-S0-T1`" not in backlog_next
    assert "`W26-E2-S0-T2`" not in backlog_next
    assert "`W26-E2-S0-T3`" not in backlog_next
    assert "`W26-E2-S0-T4`" not in backlog_next
    assert "`W26-E1-S3-T1`" not in backlog_next
    assert "`W26-E1-S3-T2`" not in backlog_next
    assert "`W26-E1-S3-T3`" not in backlog_next
    assert "`W26-E1-S3-T1`" not in backlog_soon
    assert "`W26-E1-S1-T2`" not in backlog_soon
    assert "`W26-E1-S2-T1`" not in backlog_soon
    assert "`W26-E1-S2-T2`" not in backlog_soon
    assert "`W26-E1-S2-T3`" not in backlog_soon
    assert "`W26-E2-S0-T1`" not in backlog_soon
    assert "`W26-E2-S0-T2`" not in backlog_soon
    assert "`W26-E2-S0-T3`" not in backlog_soon
    assert "`W26-E2-S0-T4`" not in backlog_soon
    assert "`W26-E1-S3-T2`" not in backlog_soon
    assert "`W26-E1-S3-T3`" not in backlog_soon
    assert "`W26-E2-S1-T1`" not in backlog_soon
    assert "`W26-E2-S1-T2`" in backlog_soon
    assert "`W26-E2-S0-T3`" not in backlog_parking
    assert "`W26-E2-S0-T4`" not in backlog_parking
    assert "`W26-E1-S3-T1`" not in backlog_parking
    assert "`W26-E1-S3-T2`" not in backlog_parking
    assert "`W26-E1-S3-T3`" not in backlog_parking
    assert "`W26-E2-S1-T1`" not in backlog_parking
    assert "`W26-E2-S1-T2`" not in backlog_parking
    assert "`W26-E4-S2-T1`" in backlog_parking
    assert "`W26-E4-S2-T2`" in backlog_parking
    assert "`W26-E4-S2-T3`" in backlog_parking
    assert "`W26-E5-S1-T1`" in backlog_parking
    for expected_screen_task in (
        "`W26-E2-S3-T1`",
        "`W26-E2-S3-T2`",
        "`W26-E2-S3-T3`",
        "`W26-E2-S3-T4`",
    ):
        assert expected_screen_task in backlog_parking

    visual_reference_dir = (
        repo_root / "docs" / "architecture" / "assets" / "operator-ui-mission-control"
    )
    visual_references = (
        "01-project-setup-previous-run.png",
        "02-active-run-command-center.png",
        "02b-flow-complete-start-next-flow.png",
        "03-stage-document-workbench.png",
        "04-questions-interview-loop.png",
        "05-validation-repair-center.png",
        "06-runtime-logs-live-console.png",
        "07-artifacts-evidence-graph.png",
        "08-approvals-request-change.png",
        "09-run-history-lineage.png",
        "10-start-next-flow-source-findings.png",
        "11-define-follow-up-work-item.png",
        "12-confirm-launch-next-flow.png",
    )
    for filename in visual_references:
        assert filename in operator_frontend
        assert (visual_reference_dir / filename).is_file()


def test_release_docs_describe_release_branch_publish_flow() -> None:
    repo_root = _repo_root()
    release_checklist = (repo_root / "docs" / "release-checklist.md").read_text(
        encoding="utf-8"
    )
    distribution = (
        repo_root / "docs" / "architecture" / "distribution-and-development.md"
    ).read_text(encoding="utf-8")
    latest_accepted_version = _latest_accepted_prerelease_version(release_checklist)
    release_notes = (
        repo_root / "docs" / f"release-notes-v{latest_accepted_version}-draft.md"
    ).read_text(encoding="utf-8")

    pre_history_checklist = release_checklist.split("## Release attempt evidence log", 1)[0]
    for needle in (
        "release/v<project.version>",
        "Create a draft GitHub Release",
        "Do not push a tag to trigger publishing directly",
        "GitHub Release `published` event",
        "release tag commit to match the remote release branch HEAD",
        "GitHub cannot open a no-diff release",
        "`workflow_dispatch` on the release branch",
    ):
        assert needle in pre_history_checklist

    assert "workflow_dispatch` path is a dry run" in distribution
    assert "release tag commit must match the remote release branch HEAD" in distribution
    assert "Status: published on " in release_notes
    assert (
        "Release workflow quality, build, publish, `pipx`, and `uv tool` "
        "verification jobs passed"
    ) in release_notes


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
        "python -m aidd.harness.live_e2e_black_box "
        "harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml "
        "--runtime codex"
        in readme
    )
    assert "typer-styled-help-alignment.yaml --runtime generic-cli" not in readme
    assert "AIDD-compatible wrapper command" in readme
    assert "Published-package install proof is a separate" in readme
    assert "mode = \"native\"" in operator_handbook
    assert "mode = \"adapter-flags\"" in operator_handbook
    assert (
        "claude -p --output-format stream-json --verbose --dangerously-skip-permissions"
        in operator_handbook
    )
    assert (
        "codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --json -"
        in operator_handbook
    )
    assert "opencode run --format json --dangerously-skip-permissions" in operator_handbook
    assert "probe target and the execution command do not have to be identical" in adapter_protocol
    assert "`native` execution" in runtime_matrix


def test_local_operator_docs_define_product_path_and_github_issue_boundary() -> None:
    readme = (_repo_root() / "README.md").read_text(encoding="utf-8")
    operator_handbook = (_repo_root() / "docs" / "operator-handbook.md").read_text(
        encoding="utf-8"
    )
    operator_ui_lane = (
        _repo_root() / "docs" / "e2e" / "operator-ui-local-project.md"
    ).read_text(encoding="utf-8")
    live_catalog = (_repo_root() / "docs" / "e2e" / "live-e2e-catalog.md").read_text(
        encoding="utf-8"
    )

    for document in (readme, operator_handbook, operator_ui_lane):
        assert "local project root" in document
        assert "aidd doctor" in document
        assert "aidd init --work-item" in document
        assert "--request" in document
        assert "aidd ui --work-item" in document
        assert ".aidd/" in document

    for document in (readme, operator_handbook, operator_ui_lane, live_catalog):
        assert "aidd init --github-issue <url>" in document
        assert "out of product scope" in document

    assert "Public GitHub repositories are live" in readme
    assert "Public GitHub repositories are live E2E targets" in live_catalog


def test_operator_ui_local_project_manual_browser_checklist_is_complete() -> None:
    operator_ui_lane = (
        _repo_root() / "docs" / "e2e" / "operator-ui-local-project.md"
    ).read_text(encoding="utf-8")

    for expected in (
        "## Manual Browser Checklist",
        "### Dashboard Shell",
        "### Cockpit Tabs",
        "### Logs",
        "### Artifacts",
        "### Questions",
        "### Request Change / Intervention",
        "### Viewports",
        "Desktop width",
        "Tablet width",
        "Mobile width",
        "Keyboard focus is visible",
    ):
        assert expected in operator_ui_lane


def test_readme_quickstart_uses_request_context_and_real_runtime_first() -> None:
    readme = (_repo_root() / "README.md").read_text(encoding="utf-8")

    assert (
        'aidd init --work-item WI-001 --request "Implement a small, specific task" '
        "--root .aidd"
    ) in readme
    assert (
        "aidd run --work-item WI-001 --runtime codex --from-stage idea "
        "--to-stage plan --root .aidd"
    ) in readme
    assert (
        "aidd run --work-item WI-001 --runtime generic-cli --from-stage idea "
        "--to-stage plan --root .aidd"
    ) not in readme
    assert "is not the default product onboarding runtime" in readme


def test_live_e2e_skill_describes_local_operator_contract() -> None:
    live_e2e_skill = (_repo_root() / ".agents" / "skills" / "live-e2e" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    aidd_eval_skill = (_repo_root() / ".agents" / "skills" / "aidd-eval" / "SKILL.md").read_text(
        encoding="utf-8"
    )

    for needle in (
        "prepared local **source checkout**",
        "`AIDD_EVAL_CLAUDE_CODE_COMMAND`",
        "`AIDD_EVAL_CODEX_COMMAND`",
        "`AIDD_EVAL_OPENCODE_COMMAND`",
        "native provider CLI",
        "AIDD-compatible wrapper command",
        "aidd eval doctor",
        (
            "uv run python -m aidd.harness.live_e2e_black_box "
            "harness/scenarios/live/sqlite-utils-detect-types-header-only.yaml "
            "--runtime codex"
        ),
        "`--work-root ${TMPDIR:-/tmp}/aidd-live-e2e`",
        "`--report-root .aidd/reports/evals`",
        "`--run-id <id>`",
        "`stage-audits/<stage>.json`",
        "snapshot tracked AIDD `HEAD`",
        "Rerun the same manifest/runtime until it is clean.",
        "plan step, execute through public operator surfaces, inspect artifacts",
        "frontend-checkpoints.json",
        "first listed authored task",
        "any live scenario may block when required answers are missing",
        "`live-full-flow-interview` scenarios are coverage cases",
        "`idea -> qa`",
        "`.aidd/reports/evals/<run_id>/`",
        "does **not** provision runtime authentication, wrapper scripts, or provider setup",
        "the launching agent is the operator-agent",
        "write standard `[resolved]` answers",
        "`- Q1 [resolved] answer text`",
        "answer-analysis.md",
        "operator-quality-analysis.md",
        "The operator audit cannot upgrade machine `fail` or `warn`",
    ):
        assert needle in live_e2e_skill

    assert "For **local live-run operator guidance**, prefer `live-e2e`." in aidd_eval_skill
    assert "the launching agent is the operator-agent" in aidd_eval_skill
    assert "`- Q1 [resolved] answer text`" in aidd_eval_skill
    assert "stage-audits/<stage>.json" in aidd_eval_skill
    assert "${TMPDIR:-/tmp}/aidd-live-e2e/<run_id>/source/aidd" in aidd_eval_skill
    assert "operator-quality-analysis.md" in aidd_eval_skill


def test_live_docs_describe_temp_install_layout_and_stage_audits() -> None:
    repo_root = _repo_root()
    documents = {
        "README.md": (repo_root / "README.md").read_text(encoding="utf-8"),
        "docs/e2e/live-e2e-catalog.md": (
            repo_root / "docs" / "e2e" / "live-e2e-catalog.md"
        ).read_text(encoding="utf-8"),
        "docs/e2e/live-quality-rubric.md": (
            repo_root / "docs" / "e2e" / "live-quality-rubric.md"
        ).read_text(encoding="utf-8"),
        "docs/architecture/eval-harness-integration.md": (
            repo_root / "docs" / "architecture" / "eval-harness-integration.md"
        ).read_text(encoding="utf-8"),
    }

    for relative_path, text in documents.items():
        for needle in (
            "stage-audits/<stage>.json",
            ".aidd/reports/evals",
        ):
            assert needle in text, relative_path

    readme = documents["README.md"]
    assert "--work-root /tmp/aidd-live-e2e" in readme
    assert "--report-root .aidd/reports/evals" in readme
    catalog = documents["docs/e2e/live-e2e-catalog.md"]
    assert "<work-root>/<run_id>/source/aidd" in catalog
    assert "<work-root>/<run_id>/target/<repo-slug>" in catalog
    assert "dirty tracked" in catalog


def test_live_manual_docs_do_not_delegate_answers_to_external_operator_agent() -> None:
    searched_roots = [
        _repo_root() / "docs" / "e2e",
        _repo_root() / "docs" / "operator-troubleshooting.md",
        _repo_root() / ".agents" / "skills" / "live-e2e",
        _repo_root() / ".agents" / "skills" / "aidd-eval",
    ]
    stale_phrases = (
        "external operator-agent",
        "external operator-agent answers",
        "after external operator-agent answers",
        "waiting for an external operator-agent",
    )
    offenders: list[str] = []
    for root in searched_roots:
        paths = [root] if root.is_file() else list(root.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if any(phrase in text for phrase in stale_phrases):
                offenders.append(path.relative_to(_repo_root()).as_posix())

    assert offenders == []


def test_docs_do_not_reference_removed_eval_run_command() -> None:
    searched_roots = [
        _repo_root() / "README.md",
        _repo_root() / "docs",
        _repo_root() / ".agents" / "skills",
        _repo_root() / ".github" / "workflows",
    ]
    offenders: list[str] = []
    for root in searched_roots:
        paths = [root] if root.is_file() else list(root.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            if path.suffix.lower() not in {
                ".md",
                ".txt",
                ".yml",
                ".yaml",
                ".toml",
                ".json",
                ".jsonl",
            }:
                continue
            text = path.read_text(encoding="utf-8")
            if "aidd eval run" in text:
                offenders.append(path.relative_to(_repo_root()).as_posix())

    assert offenders == []


def test_live_docs_do_not_limit_questions_to_interview_scenarios() -> None:
    searched_roots = [
        _repo_root() / "README.md",
        _repo_root() / "docs" / "architecture" / "eval-harness-integration.md",
        _repo_root() / "docs" / "e2e",
        _repo_root() / "docs" / "operator-handbook.md",
        _repo_root() / "docs" / "operator-troubleshooting.md",
        _repo_root() / ".agents" / "skills" / "live-e2e",
    ]
    stale_phrases = (
        "interview scenarios block when required answers are missing",
        "questions.md` / `answers.md` expectations for interview scenarios",
        "interview guidance only for `live-full-flow-interview` scenarios",
    )
    offenders: list[str] = []
    for root in searched_roots:
        paths = [root] if root.is_file() else list(root.rglob("*"))
        for path in paths:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if any(phrase in text for phrase in stale_phrases):
                offenders.append(path.relative_to(_repo_root()).as_posix())

    assert offenders == []


def test_release_publish_skill_describes_release_flow_guardrails() -> None:
    skill = (
        _repo_root() / ".agents" / "skills" / "release-publish" / "SKILL.md"
    ).read_text(encoding="utf-8")

    for needle in (
        "release/v<project.version>",
        "GitHub Release",
        "GitHub Release `published` event",
        "`workflow_dispatch` as a dry-run path",
        "`pipx`",
        "`uv tool`",
        "Do not add or run live E2E in GitHub Actions, CI/CD, or release workflows.",
        "Do not use direct tag-push publishing.",
        "If the PyPI version already exists, stop and ask for a new version decision.",
        "Docker/GHCR is not a supported alpha release channel.",
        "If the release tag SHA does not match `origin/release/<tag>`, stop",
        "Tag v<project.version> already exists on origin",
        "git rev-parse refs/tags/v<project.version>^{commit}",
    ):
        assert needle in skill
