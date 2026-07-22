from __future__ import annotations

import signal
from pathlib import Path

from semantic_test_support import (
    _SEMANTIC_FIXTURES_ROOT,
    _write_implementation_report,
    _write_workspace_baseline,
)

from aidd.validators.models import ValidationFinding, ValidationIssueLocation
from aidd.validators.semantic import (
    INCOMPLETE_EXECUTION_SUMMARY_CODE,
    MISSING_DIFF_EVIDENCE_CODE,
    UNVERIFIABLE_CHECK_CLAIM_CODE,
    validate_semantic_outputs,
)


def test_validate_semantic_outputs_accepts_valid_implement_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "implement-valid" / "workspace"

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-VALID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_example_style_implementation_report(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-EXAMPLE",
        (
            "# Implementation Report\n\n"
            "## Selected task id\n\n"
            "- `ISSUE-705`, traced to tasklist tasks `TL-1` through `TL-5`.\n\n"
            "## Summary\n\n"
            "Implemented the bounded header-only CSV fix and mapped the source "
            "edits, regression tests, and verification evidence back to the "
            "selected tasklist tasks.\n\n"
            "## Touched files\n\n"
            "- `data_tool/cli.py` -> guard the two existing transform follow-up paths.\n"
            "  - line 1179: `if tracker is not None:` -> "
            "`if tracker is not None and tracker.types:`.\n"
            "  - line 2036: `if tracker is not None:` -> "
            "`if tracker is not None and tracker.types:`.\n"
            "- `tests/test_cli.py` -> add focused header-only CSV/TSV regression tests.\n\n"
            "```diff\n"
            "-        if tracker is not None:\n"
            "+        if tracker is not None and tracker.types:\n"
            "```\n\n"
            "## Verification\n\n"
            "### TL-4 regression and gate evidence\n\n"
            "- `.venv/bin/python -c \"import data_tool.cli\"` -> printed `OK`.\n"
            "- `.venv/bin/pytest tests/` -> `1045 passed, 16 skipped`, exit `0`.\n"
            "- `.venv/bin/data-tool schema test.db` -> "
            "`CREATE TABLE \"people\" (\"name\" TEXT, \"age\" TEXT);` "
            "-> matches expected post-fix schema.\n"
            "- `.venv/bin/mypy data_tool tests` ->\n"
            "  `Success: no issues found in 55 source files`, exit `0`.\n"
            "- `.venv/bin/ty check data_tool` -> `Found 21 diagnostics`, exit `1`.\n"
            "  The output matched the pre-patch baseline exactly.\n\n"
            "### TL-6 audit evidence\n\n"
            "- Command: `Grep` pattern "
            "`transform\\(types=tracker\\.types\\)|if tracker is not None` on "
            "`data_tool/`\n"
            "  -> outcome: 2 production matches in `data_tool/cli.py` and 2 "
            "docstring matches in `data_tool/utils.py`.\n"
            "- Command: `git diff --stat`\n"
            "  -> outcome: 3 files changed, 57 insertions(+), 2 deletions(-); "
            "changed files limited to `data_tool/cli.py`, `tests/test_cli.py`, "
            "and `tests/test_cli_memory.py`.\n\n"
            "### TL-5 evidence bundle\n\n"
            "- `validator-report.md` records the draft self-validator pass.\n"
            "- QA reproduction recipe:\n"
            "  - `printf 'a,b,c\\n' > /tmp/header_only.csv && "
            ".venv/bin/data-tool insert /tmp/test.db tbl /tmp/header_only.csv --csv`\n"
            "    -> exit `0`, no traceback.\n"
            "  - `git stash -- data_tool/cli.py` then "
            "`.venv/bin/pytest tests/test_cli.py -k header_only -v` "
            "-> 5 failures with the original assertion signature.\n\n"
            "## Risks\n\n"
            "- Existing `ty` and `black` findings are pre-existing baseline noise.\n\n"
            "## Follow-up\n\n"
            "- No deferred items before QA.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-EXAMPLE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_requires_setup_ignored_residue_evidence_for_implement(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-IMPLEMENT-EXAMPLE-RESIDUE"
    _write_workspace_baseline(workspace_root, work_item)
    _write_implementation_report(
        workspace_root,
        work_item,
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Task id: `TASK-EXAMPLE-RUNTIME-ERROR`.\n\n"
            "## Change summary\n\n"
            "Implemented the selected example task and added focused regression coverage.\n\n"
            "## Touched files\n\n"
            "- `src/runtime-error.ts` - normalize thrown non-Error values.\n"
            "- `tests/runtime-error.test.ts` - add non-Error throw regression coverage.\n\n"
            "## Verification notes\n\n"
            "- `./node_modules/.bin/vitest --run --coverage.enabled=false "
            "tests/runtime-error.test.ts` -> pass (new regression passed).\n"
            "- `./node_modules/.bin/tsc --noEmit` -> pass.\n\n"
            "## Follow-up notes\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert any(
        finding.code == UNVERIFIABLE_CHECK_CLAIM_CODE
        and "git status --ignored --short --untracked-files=all" in finding.message
        for finding in findings
    )


def test_validate_semantic_outputs_accepts_setup_ignored_residue_evidence_for_implement(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-IMPLEMENT-EXAMPLE-RESIDUE-CLEAN"
    _write_workspace_baseline(workspace_root, work_item)
    _write_implementation_report(
        workspace_root,
        work_item,
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Task id: `TASK-EXAMPLE-RUNTIME-ERROR`.\n\n"
            "## Change summary\n\n"
            "Implemented the selected example task and added focused regression coverage.\n\n"
            "## Touched files\n\n"
            "- `src/runtime-error.ts` - normalize thrown non-Error values.\n"
            "- `tests/runtime-error.test.ts` - add non-Error throw regression coverage.\n\n"
            "## Verification notes\n\n"
            "- `./node_modules/.bin/vitest --run --coverage.enabled=false "
            "tests/runtime-error.test.ts` -> pass (new regression passed).\n"
            "- `./node_modules/.bin/tsc --noEmit` -> pass.\n"
            "- `git status --ignored --short --untracked-files=all` -> pass "
            "(no new `coverage/`, `.coverage*`, `__pycache__/`, build, dist, "
            "or dependency-cache residue beyond setup baseline).\n\n"
            "## Follow-up notes\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_aidd_command_evidence_for_implement(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-IMPLEMENT-AIDD-COMMAND"
    _write_implementation_report(
        workspace_root,
        work_item,
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Task id: `TASK-EXAMPLE-STREAMED-ROWS`.\n\n"
            "## Change summary\n\n"
            "Implemented the selected example task and preserved operator answer alignment.\n\n"
            "## Touched files\n\n"
            "- `data_tool/cli.py` - add yielded rows option handling.\n"
            "- `tests/test_cli_insert.py` - cover yielded rows behavior.\n\n"
            "## Verification notes\n\n"
            "- `aidd stage questions idea --work-item WI-EXAMPLE-INTERVIEW` "
            "-> pass (exit code 0; no unresolved blocking questions).\n\n"
            "## Follow-up notes\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_sed_command_evidence_for_implement(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    work_item = "WI-SEM-IMPLEMENT-EXAMPLE-SED"
    _write_workspace_baseline(workspace_root, work_item)
    _write_implementation_report(
        workspace_root,
        work_item,
        (
            "# Implementation Report\n\n"
            "## Summary\n\n"
            "- Selected task id: `TASK-EXAMPLE-RUNTIME-ERROR`.\n"
            "- Implemented bounded non-Error throw normalization with focused "
            "regression coverage and public type compatibility checks.\n\n"
            "## Touched files\n\n"
            "- `src/pipeline.ts` - normalize composed middleware thrown values.\n"
            "- `src/runtime-error.ts` - normalize direct route thrown values.\n"
            "- `tests/runtime-error.test.ts` - add primitive and object throw regressions.\n"
            "- `tests/pipeline.test.ts` - add composed middleware regression coverage.\n\n"
            "## Verification\n\n"
            "- `./node_modules/.bin/vitest --run --coverage.enabled=false "
            "tests/runtime-error.test.ts tests/pipeline.test.ts` -> pass (235 passed).\n"
            "- `./node_modules/.bin/tsc --noEmit` -> pass (exit code 0).\n"
            "- `sed -n '113,119p' src/types.ts` -> pass (observed `ErrorHandler` "
            "still accepts `err: Error | HTTPResponseError`).\n"
            "- `sed -n '319,334p' src/context.ts` -> pass (observed `Context.error` "
            "remains `Error | undefined`).\n"
            "- `git status --ignored --short --untracked-files=all` -> pass "
            "(no new `coverage/`, `.coverage*`, `__pycache__/`, build, dist, "
            "or dependency-cache residue beyond setup baseline).\n\n"
            "## Risks\n\n"
            "- Public type compatibility remains source-compatible.\n\n"
            "## Follow-up\n\n"
            "- none\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_contract_summary_task_id_and_cli_subcommands(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-SUMMARY-ID",
        (
            "# Implementation Report\n\n"
            "## Summary\n\n"
            "- Task id: `ISSUE-705`\n"
            "- Traced to tasklist: `TL-1` and `TL-2`.\n\n"
            "This change fixes the header-only CSV crash by guarding the "
            "`transform(types=tracker.types)` follow-up path and adding a "
            "focused regression test.\n\n"
            "## Touched files\n\n"
            "- `data_tool/cli.py` - add table-existence guard before transform.\n"
            "- `tests/test_cli.py` - add header-only CSV regression coverage.\n\n"
            "## Verification\n\n"
            "### TL-1 verification\n\n"
            "- `pytest tests/test_cli.py::test_insert_detect_types -v`\n"
            "  - Observed: 3 passed in 0.50s\n"
            "  - Verdict: pass\n\n"
            "- Manual parity check (insert path, header-only CSV):\n"
            "  - `insert ... --csv` with `input=\"name,age\\n\"`: "
            "exit_code 0, no `creatures` table created\n"
            "  - `insert ... --csv --no-detect-types` with same input: "
            "exit_code 0, no `creatures` table created\n"
            "  - Verdict: parity confirmed\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-SUMMARY-ID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_block_scoped_verification_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-BLOCK-EVIDENCE",
        (
            "# Implementation Report\n\n"
            "## Summary\n\n"
            "- Task id: `ISSUE-705`\n"
            "- Traced to tasklist: `TL-1` and `TL-2`.\n\n"
            "Implemented the bounded header-only CSV fix and recorded command "
            "evidence by verification subsection.\n\n"
            "## Touched files\n\n"
            "- `data_tool/cli.py` - add table-existence guard before transform.\n"
            "- `tests/test_cli.py` - add header-only CSV regression coverage.\n\n"
            "## Verification\n\n"
            "### T1 - reproduction evidence\n\n"
            "- Command: `python -m data_tool insert /tmp/t.db t "
            "/tmp/header.csv --csv --detect-types` -> exit code `1`.\n"
            "- Observed stderr from the T1 reproduction command -> "
            "`AssertionError: Cannot transform a table that doesn't exist yet` -> pass.\n"
            "- Baseline shape command: `python -m data_tool insert /tmp/base.db t "
            "/tmp/header.csv --csv --no-detect-types` -> exit code `0`.\n\n"
            "### T4 - scenario verification\n\n"
            "- Command: `.venv/bin/python -m pytest -q` from the repository root.\n"
            "- Outcome: `1041 passed, 16 skipped in 5.97s`, exit code `0` -> pass.\n"
            "- Targeted baseline re-run command: `.venv/bin/python -m pytest "
            "tests/test_cli_insert.py -q` -> `43 passed in 0.55s`, "
            "exit code `0` -> pass.\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-BLOCK-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_flat_example_verification_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-FLAT-EXAMPLE",
        (
            "# Implementation Report\n\n"
            "## Selected task id\n\n"
            "- `ISSUE-705` -- header-only CSV bugfix.\n\n"
            "## Summary\n\n"
            "Implemented the bounded header-only CSV fix and mapped the source "
            "edits, regression tests, and verification evidence back to the "
            "selected tasklist tasks.\n\n"
            "## Touched files\n\n"
            "- `data_tool/cli.py` - add table-existence guard before transform.\n"
            "- `tests/test_cli.py` - add header-only CSV regression coverage.\n\n"
            "## Verification\n\n"
            "- `T1` -- diff inspection: `git diff data_tool/cli.py` shows "
            "two hunks only, each adding the issue-naming comment plus the "
            "`if db.table(...).exists():` gate.\n"
            "- `T1` -- regression reproduction: `uv run python -c \"...\"` invoking "
            "`CliRunner().invoke(...)` -> `exit_code == 0`, `output == \"\"`, "
            "`exception is None`. Observed.\n"
            "- `T2` -- revert sanity check: `git stash push -- data_tool/cli.py "
            "&& uv run pytest tests/test_cli.py::test_insert_detect_types_header_only_csv` "
            "-> `3 failed` with `AssertionError`; `git stash pop` restored the "
            "fix; subsequent re-run -> `3 passed`.\n"
            "- `T3` -- revert sanity check: same stash/pop procedure as `T2` "
            "-> `3 failed` with the same `AssertionError`; restored the fix; "
            "re-run -> `3 passed`.\n"
            "- `T4` -- revert sanity check: stash/pop procedure -> the `None` "
            "parametrization fails with the pre-fix assertion; restored the "
            "fix; re-run -> `3 passed`.\n"
            "- `T5` -- boundary check: `git diff --name-only` -> "
            "`data_tool/cli.py`, `tests/test_cli.py` only. "
            "`git diff data_tool/db.py data_tool/utils.py` -> empty.\n"
            "- `T7` -- not run in this stage; deferred to the `qa` stage.\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-FLAT-EXAMPLE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_rg_verification_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-RG-EVIDENCE",
        (
            "# Implementation Report\n\n"
            "## Selected task id\n\n"
            "- `TASK-123`, decomposed into tasklist item `TL-2`.\n\n"
            "## Summary\n\n"
            "Implemented the scoped task and used command readback to confirm "
            "the repaired document shape and stage status.\n\n"
            "## Touched files\n\n"
            "- `src/example.py` - apply the selected scoped change.\n\n"
            "## Verification\n\n"
            "- Repair readback: `rg -n '^## (Summary|Verification)$|Status:' "
            ".aidd/workitems/WI-123/stages/implement` -> exit code 0; "
            "confirmed expected headings and status markers.\n"
            "- Downstream artifact check: `test -f "
            ".aidd/workitems/WI-123/stages/qa/output/stage-result.md` -> "
            "exit code 1; expected because QA output is downstream of implement.\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-RG-EVIDENCE",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_find_cleanup_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-FIND-CLEANUP",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-EXAMPLE-BOOLEAN-HELP`\n\n"
            "## Summary\n\n"
            "Implemented the selected task and recorded cleanup checks for "
            "workspace hygiene.\n\n"
            "## Touched files\n\n"
            "- `cli_tool/core.py` - update boolean option help rendering.\n"
            "- `tests/test_tutorial/test_parameter_types/test_bool/test_help_rendering.py` "
            "- add focused help output coverage.\n\n"
            "## Verification\n\n"
            "- `find cli_tool tests docs_src -type d -name __pycache__ -print` "
            "-> pass (zero output after cleanup).\n"
            "- `find . -maxdepth 1 -type d -name workitems -print` "
            "-> pass (no top-level `workitems/` directory was created).\n"
            "- `test ! -e .pytest_cache` -> pass (pytest cache removed after verification).\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-FIND-CLEANUP",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_python_c_output_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-PYTHON-C-OUTPUT",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-EXAMPLE-STREAMED-ROWS`\n\n"
            "## Summary\n\n"
            "Implemented the selected yielded-rows CLI behavior and recorded "
            "target-local command evidence for focused tests, help output, "
            "runtime success paths, and invalid-input behavior.\n\n"
            "## Touched files\n\n"
            "- `data_tool/cli.py` - add trusted Python file input handling.\n"
            "- `tests/test_cli_insert.py` - cover rows, yields, and invalid input.\n"
            "- `docs/cli.rst` - document the trusted-code boundary.\n\n"
            "## Verification\n\n"
            "- `python -m pytest tests/test_cli_insert.py -q` "
            "-> output: `52 passed in 1.01s`.\n"
            "- `python -c \"from click.testing import CliRunner; "
            "from data_tool import cli; result = CliRunner().invoke("
            "cli.cli, ['insert', '--help']); print(result.output)\"` "
            "-> output contains: `--python-file FILE`.\n"
            "- `python -c \"from click.testing import CliRunner; "
            "from data_tool import cli; result = CliRunner().invoke("
            "cli.cli, ['insert', '/tmp/test.db', 'people', '--python-file', "
            "'/tmp/rows_test.py']); print(result.exit_code)\"` "
            "-> output: `0`.\n"
            "- `python -c \"from click.testing import CliRunner; "
            "from data_tool import cli; result = CliRunner().invoke("
            "cli.cli, ['insert', '/tmp/test.db', 'items', '--python-file', "
            "'/tmp/rows_test.py', '--csv']); print(result.output); "
            "print(result.exit_code)\"` "
            "-> output: `Error: Cannot use --python-file with --csv\\n1`.\n\n"
            "## Risks\n\n"
            "- No residual product risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-PYTHON-C-OUTPUT",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_sphinx_build_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-SPHINX-BUILD",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-EXAMPLE-STREAMED-ROWS`\n\n"
            "## Summary\n\n"
            "Implemented the selected documentation-bearing CLI behavior and "
            "recorded a concrete documentation build command with observed output.\n\n"
            "## Touched files\n\n"
            "- `docs/cli.rst` - document the new CLI option and trust boundary.\n\n"
            "## Verification\n\n"
            "- `sphinx-build docs docs/_build` -> build succeeded, 16 warnings "
            "(exit code 0).\n\n"
            "## Risks\n\n"
            "- No residual product risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-SPHINX-BUILD",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_example_selected_task_and_not_run_checks(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-EXAMPLE-TASK-ID",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Work item: `WI-EXAMPLE-BOOLEAN`\n"
            "- Stable selected task id: `TASK-EXAMPLE-BOOLEAN-HELP`\n"
            "- Selected task title: boolean option help rendering\n\n"
            "## Summary\n\n"
            "Implemented the selected example task by changing the Rich help label "
            "rendering and adding focused regression coverage for grouped "
            "boolean option labels while preserving default details.\n\n"
            "## Touched files\n\n"
            "- `cli_tool/rich_utils.py` - group boolean option labels when secondary flags exist.\n"
            "- `tests/test_tutorial/test_parameter_types/test_bool/test_tutorial003.py` - add "
            "Rich label and default preservation assertions.\n\n"
            "## Verification\n\n"
            "- Authored Rich-mode command `uv run pytest -q "
            "tests/test_tutorial/test_parameter_types/test_bool` -> blocked before pytest: "
            "`error: failed to open file /Users/example/.cache/uv/sdists-v9/.git: "
            "Operation not permitted (os error 1)`.\n"
            "- Sandbox-compatible Rich command `CACHE_DIR=/tmp/tool-cache uv run pytest -q "
            "tests/test_tutorial/test_parameter_types/test_bool` -> pass, `43 passed in 1.95s`.\n"
            "- QA output existence check `test -f "
            ".aidd/workitems/WI-EXAMPLE-BOOLEAN/stages/qa/output/stage-result.md` "
            "-> not-run, targets a downstream QA-stage artifact that is not produced by "
            "the implement stage.\n\n"
            "## Risks\n\n"
            "- No residual risk remains for the selected task.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-EXAMPLE-TASK-ID",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_bun_verification_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-BUN",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-EXAMPLE-RUNTIME-ERROR`\n"
            "- Selected task title: non-Error throw handling\n\n"
            "## Summary\n\n"
            "Implemented the selected example runtime error-handling task and "
            "recorded focused regression coverage plus broad-suite evidence.\n\n"
            "## Touched files\n\n"
            "- `src/pipeline.ts` - normalize non-Error thrown values before onError.\n"
            "- `src/runtime-error.ts` - normalize dispatch errors before the "
            "example runtime error handler.\n"
            "- `tests/runtime-error.test.ts` - cover primitive and object non-Error throws.\n\n"
            "## Verification\n\n"
            "- `bunx vitest --run tests/pipeline.test.ts tests/runtime-error.test.ts` "
            "-> exit code 0; captured summary `Test Files 2 passed (2)` and "
            "`Tests 241 passed (241)`.\n"
            "- `bunx tsc --noEmit` -> exit code 0; captured output contained no diagnostics.\n"
            "- `./node_modules/.bin/prettier --check src/runtime-error-utils.ts "
            "src/runtime-error.ts` "
            "-> pass, exit code 0; all matched files use Prettier style.\n"
            "- `bun run test` -> exit code 1; captured summary "
            "`Test Files 3 failed | 141 passed (144)`, `Tests 11 failed | "
            "4314 passed | 33 skipped (4358)`, and `Errors 4 errors`.\n"
            "- `bun test` -> not-run: earlier implement evidence recorded this "
            "plain Bun runner as a sandbox-hanging command.\n\n"
            "## Risks\n\n"
            "- Broad-suite verification remains locally blocked by unrelated target "
            "runner failures; focused regression and TypeScript checks passed.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-BUN",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_rejects_plain_tool_prose_as_command_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-PLAIN-TOOLS",
        (
            "# Implementation Report\n\n"
            "## Selected task\n\n"
            "- Stable selected task id: `TASK-EXAMPLE-RUNTIME-ERROR`\n\n"
            "## Summary\n\n"
            "Implemented the selected example runtime task with a scoped source update and "
            "recorded verification notes.\n\n"
            "## Touched files\n\n"
            "- `src/runtime-error.ts` - normalize dispatch errors before the "
            "example runtime error handler.\n\n"
            "## Verification\n\n"
            "- Bun runner passed.\n"
            "- Prettier passed.\n"
            "- TypeScript tsc passed.\n\n"
            "- pytest passed.\n"
            "- Checked with ruff and it succeeded.\n\n"
            "## Risks\n\n"
            "- No residual risk remains.\n\n"
            "## Follow-up\n\n"
            "- None.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-PLAIN-TOOLS",
        workspace_root=workspace_root,
    )

    assert [finding.code for finding in findings] == [
        UNVERIFIABLE_CHECK_CLAIM_CODE,
        UNVERIFIABLE_CHECK_CLAIM_CODE,
        UNVERIFIABLE_CHECK_CLAIM_CODE,
        UNVERIFIABLE_CHECK_CLAIM_CODE,
        UNVERIFIABLE_CHECK_CLAIM_CODE,
    ]
    assert all(finding.severity == "high" for finding in findings)


def test_validate_semantic_outputs_accepts_example_noop_blocker_evidence(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / ".aidd"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-BLOCKER",
        (
            "# Implementation Report\n\n"
            "## Selected task id\n\n"
            "`ISSUE-705`, decomposed into ordered tasks `T1` -> `T2` -> `T3`.\n\n"
            "## Summary\n\n"
            "This attempt executed `T1` only. The pre-write scratch reproduction "
            "observed the documented fail path, so later source-edit tasks were "
            "not started and a blocking plan question was raised.\n\n"
            "## Touched files\n\n"
            "- `data_tool/cli.py` (`scratch-and-revert`, no net change): applied "
            "the guard for the T1 observation, then reverted it. Net diff is empty.\n\n"
            "## Verification\n\n"
            "- VN-1 (scratch guard observation):\n"
            "  - Command: `.venv/bin/python -c \"...\"` invoking `cli.cli` with "
            "`[\"insert\", \"--csv\", \"--detect-types\", <db>, \"data\", <csv>]`.\n"
            "  - Observed: exit code `0`, `result.stderr == \"\"`, "
            "`db[\"data\"].exists() is False`, `db.table_names() == []`.\n"
            "  - Outcome: T1 fail path confirmed; halts the task graph.\n\n"
            "- VN-3 (`insert_all` empty-iterator behaviour):\n"
            "  - Command: `.venv/bin/python -c \"...\"` calling "
            "`Database(db_path)[\"t\"].insert_all([])`.\n"
            "  - Observed: the target table does not exist after the call; "
            "`db.table_names() == []`.\n"
            "  - Outcome: the planned guard cannot satisfy the table-creation clause.\n\n"
            "- VN-4 (post-attempt source diff):\n"
            "  - Command: `git diff data_tool/cli.py tests/test_cli_insert.py`.\n"
            "  - Observed: empty output.\n"
            "  - Outcome: no production-code change leaked from this attempt.\n\n"
            "- T5 full-suite run (`uv run pytest -q || pytest -q`) was not\n"
            "  executed because the bugfix was not applied and the preconditions failed.\n\n"
            "## Risks\n\n"
            "- The plan-stage table-creation expectation is now a confirmed blocker.\n\n"
            "## Follow-up\n\n"
            "- Route the blocking question to a new plan attempt before implementation.\n"
        ),
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-BLOCKER",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_flags_invalid_implement_noop_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "implement-invalid-noop" / "workspace"

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-NOOP",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
            message=(
                "No-op output requires explicit evidence-backed justification "
                "in summary or follow-up notes."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-NOOP/stages/implement/implementation-report.md"
                ),
                line_number=8,
            ),
        ),
        ValidationFinding(
            code=INCOMPLETE_EXECUTION_SUMMARY_CODE,
            message=(
                "No-op output must include an actionable next step in "
                "`Follow-up notes`."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-NOOP/stages/implement/implementation-report.md"
                ),
                line_number=20,
            ),
        ),
        ValidationFinding(
            code=MISSING_DIFF_EVIDENCE_CODE,
            message=(
                "Change summary claims completed implementation but touched-files "
                "list is empty."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-NOOP/stages/implement/implementation-report.md"
                ),
                line_number=8,
            ),
        ),
        ValidationFinding(
            code=UNVERIFIABLE_CHECK_CLAIM_CODE,
            message=(
                "Verification note includes outcome claim without executable "
                "command evidence."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-NOOP/stages/implement/implementation-report.md"
                ),
                line_number=16,
            ),
        ),
    )


def test_validate_semantic_outputs_flags_invalid_implement_verification_fixture_bundle() -> None:
    workspace_root = _SEMANTIC_FIXTURES_ROOT / "implement-invalid-verification" / "workspace"

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-VERIFY",
        workspace_root=workspace_root,
    )

    assert findings == (
        ValidationFinding(
            code=UNVERIFIABLE_CHECK_CLAIM_CODE,
            message=(
                "Verification note must include observed command outcome "
                "(for example `-> pass` or exit code)."
            ),
            severity="medium",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-VERIFY/stages/implement/implementation-report.md"
                ),
                line_number=16,
            ),
        ),
        ValidationFinding(
            code=UNVERIFIABLE_CHECK_CLAIM_CODE,
            message=(
                "Verification note includes outcome claim without executable "
                "command evidence."
            ),
            severity="high",
            location=ValidationIssueLocation(
                workspace_relative_path=(
                    "workitems/WI-SEM-IMPLEMENT-VERIFY/stages/implement/implementation-report.md"
                ),
                line_number=16,
            ),
        ),
    )


def test_validate_semantic_outputs_accepts_bounded_diff_verification_summary(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-DIFF",
        "# Implementation Report\n\n"
        "## Selected task\n\n"
        "- Task id: `TASK-EXAMPLE-STREAMED-ROWS`\n"
        "- Local task ids: T1, T2\n\n"
        "## Change summary\n\n"
        "Implemented the selected yielded-rows feature with scoped code, tests, and docs.\n\n"
        "## Touched files\n\n"
        "- `data_tool/cli.py` - add yielded-row ingestion handling.\n"
        "- `tests/test_cli_insert.py` - cover yielded rows and invalid input.\n"
        "- `docs/cli.rst` - document trusted local Python caveats.\n\n"
        "## Verification\n\n"
        "- `uv run pytest -q` -> 1044 passed, 16 skipped.\n"
        "- `git diff --name-only` -> changes bounded to `data_tool/cli.py`, "
        "`tests/test_cli_insert.py`, `docs/cli.rst`.\n\n"
        "## Risks\n\n"
        "- None observed.\n\n"
        "## Follow-up\n\n"
        "- None.\n",
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-DIFF",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_live_sh_cleanup_verification(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    work_item = "WI-SEM-IMPLEMENT-SHELL-CLEANUP"
    _write_implementation_report(
        workspace_root,
        work_item,
        "# Implementation Report\n\n"
        "## Summary\n\n"
        "- Implemented selected task `T1` with one bounded source change.\n\n"
        "## Touched files\n\n"
        "- `src/compose.ts` - normalize caught non-Error values.\n\n"
        "## Verification\n\n"
        "- `sh -c 'residue=\"$(find . -name __pycache__ -print)\"; "
        "[ -z \"$residue\" ] || { printf \"%s\\n\" \"$residue\"; exit 1; }'` "
        "-> pass (exit code 0; no generated cache residue reported).\n"
        "- `git status --ignored --short --untracked-files=all` -> pass "
        "(exit code 0; no ignored verification residue).\n\n"
        "## Risks\n\n"
        "- None observed.\n\n"
        "## Follow-up\n\n"
        "- Continue with the next dependency-ready task.\n",
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item=work_item,
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_setup_cleanup_residue_note(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-EXAMPLE-CLEANUP",
        "# Implementation Report\n\n"
        "## Selected task\n\n"
        "- Task id: `TASK-EXAMPLE-STREAMED-ROWS`\n\n"
        "## Change summary\n\n"
        "Implemented the selected yielded-rows feature with code, tests, and docs.\n\n"
        "## Touched files\n\n"
        "- `data_tool/cli.py` - add yielded-row ingestion handling.\n"
        "- `tests/test_cli_insert.py` - cover yielded rows and invalid input.\n"
        "- `docs/cli.rst` - document trusted local Python caveats.\n\n"
        "## Verification\n\n"
        "- `uv run pytest -q` -> pass (1055 passed, 16 skipped).\n"
        "- `uv run sphinx-build -W -b html docs docs/_build` -> pass.\n"
        "- Verification residue cleanup: removed `.pytest_cache/`, "
        "`.hypothesis/`, `docs/_build/`, and `__pycache__/` directories "
        "created by the pytest/sphinx checks.\n"
        "- `git status --ignored --short --untracked-files=all` -> pass "
        "(no `.pytest_cache/`, `.hypothesis/`, `docs/_build/`, "
        "`__pycache__/`, `.ruff_cache/`, or `.mypy_cache/` residue remains).\n\n"
        "## Risks\n\n"
        "- None observed.\n\n"
        "## Follow-up\n\n"
        "- None.\n",
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-EXAMPLE-CLEANUP",
        workspace_root=workspace_root,
    )

    assert findings == ()


def test_validate_semantic_outputs_accepts_cache_absence_command_without_hanging(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-CACHE-CHECK",
        "# Implementation Report\n\n"
        "## Selected task\n\n"
        "- Task id: `TASK-EXAMPLE-CACHE-HYGIENE`\n\n"
        "## Change summary\n\n"
        "Implemented the selected cache hygiene check with bounded verification evidence.\n\n"
        "## Touched files\n\n"
        "- `src/cache_hygiene.py` - add cache hygiene guard.\n\n"
        "## Verification\n\n"
        "- `test ! -e coverage && test ! -e .coverage && test ! -e .pytest_cache && "
        "test ! -e .ruff_cache` -> pass (exit code 0; no root-level coverage or "
        "Python tool cache residue).\n\n"
        "## Risks\n\n"
        "- None observed.\n\n"
        "## Follow-up\n\n"
        "- None.\n",
    )

    def _timeout(_signum: int, _frame: object) -> None:
        raise TimeoutError("semantic validation hung on cache absence command evidence")

    previous_handler = signal.signal(signal.SIGALRM, _timeout)
    try:
        signal.setitimer(signal.ITIMER_REAL, 2.0)
        findings = validate_semantic_outputs(
            stage="implement",
            work_item="WI-SEM-IMPLEMENT-CACHE-CHECK",
            workspace_root=workspace_root,
        )
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)

    assert findings == ()


def test_validate_semantic_outputs_accepts_backticked_python_heredoc_verification(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    _write_implementation_report(
        workspace_root,
        "WI-SEM-IMPLEMENT-HEREDOC",
        "# Implementation Report\n\n"
        "## Summary\n\n"
        "- Implemented selected task `TASK-EXAMPLE-BOOLEAN-HELP` with focused "
        "code, docs, and test coverage.\n\n"
        "## Touched files\n\n"
        "- `cli_tool/core.py` - adjust plain boolean option help formatting.\n"
        "- `cli_tool/rich_utils.py` - adjust Rich boolean option help layout.\n"
        "- `tests/test_rich_utils.py` - cover paired and false-only boolean rows.\n\n"
        "## Verification\n\n"
        "- `python - <<'PY' ... current CliRunner boolean help probe ... PY` -> "
        "pass (exit code 0; observed Rich paired and false-only rows plus plain "
        "false-only `-d, --demo`).\n"
        "- `python -m pytest tests/test_rich_utils.py -q` -> pass (10 passed).\n\n"
        "## Risks\n\n"
        "- Rich help layout is column-width dependent.\n\n"
        "## Follow-up\n\n"
        "- none\n",
    )

    findings = validate_semantic_outputs(
        stage="implement",
        work_item="WI-SEM-IMPLEMENT-HEREDOC",
        workspace_root=workspace_root,
    )

    assert findings == ()
