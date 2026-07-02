# Live E2E Candidate Setup Audits

This document records `W33-E3-S1-T1` setup proof for possible future
product-evaluation lanes. These rows are candidate evidence only. They do not add
maintained coverage and they do not replace the maintained matrix in
[`scenario-matrix.md`](./scenario-matrix.md).

Audit workspace: `/tmp/aidd-live-candidate-audits`

## Decision Table

| Candidate | Repo | Pin | Setup command | Focused baseline | Outcome | Blocker status | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Pydantic | `https://github.com/pydantic/pydantic` | `9dc25d6b97303ad9587051e90584489b16fa54c5` | `uv sync --frozen --all-packages --group dev --group linting` | `uv run pytest -q tests/test_config.py tests/test_serialize.py` | Setup passed in 219.31s; baseline passed with 172 passed, 1 skipped in 24.50s. | No functional blocker; setup builds local `pydantic-core`, so the lane has high first-run cost. | `candidate` |
| FastAPI | `https://github.com/fastapi/fastapi` | `cecd96d9c6c318e0df1c40cedbc2e953381ddfd3` | `uv sync --frozen --group tests` | `uv run pytest -q tests/test_stream_bare_type.py tests/test_serialize_response.py tests/test_response_model_data_filter.py` | Setup passed in 56.56s; baseline passed with 8 passed in 20.66s. | No functional blocker; setup installs a broad test dependency group, including docs and provider-adjacent packages. | `candidate` |
| Rich | `https://github.com/Textualize/rich` | `9d8f9a372cc5916fd4781fec207ced7ddac2f08f` | `uv venv && uv pip install -e . pytest pytest-cov attrs typing-extensions` | `.venv/bin/python -m pytest -q tests/test_console.py tests/test_table.py tests/test_markup.py` | Setup passed in 6.56s; baseline passed with 142 passed in 2.58s. | Upstream contributor docs prefer Poetry, but Poetry is not required for this focused candidate setup. | `candidate` |
| Ruff | `https://github.com/astral-sh/ruff` | `c5ee52a357d2ecd864b3723384e7fe15c6c473fb` | `uv sync --only-group dev --locked` | `cargo check -p ruff --locked` | Setup passed in 3.83s; baseline passed in 190.58s after the first Rust compile. | No functional blocker; Rust toolchain and first-run compile cost make it less suitable for the immediate draft. | `candidate` |

All four disposable clones had clean tracked `git status --short` after setup and
baseline verification.

## Candidate Task Ideas

These task ideas are audit notes, not runtime-facing prompt text. Only the selected
draft scenario below receives a manifest.

| Candidate | Candidate task idea | Selection note |
| --- | --- | --- |
| Pydantic | Improve one bounded model serialization or configuration edge case with focused tests in `tests/test_config.py` or `tests/test_serialize.py`. | Good product signal, but local `pydantic-core` build makes first setup materially slower. |
| FastAPI | Improve one response serialization or bare stream response edge case with focused tests across response-model and stream tests. | Good API/runtime signal, but setup brings a large dependency surface for a draft lane. |
| Rich | Improve literal bracketed markup rendering in console/table output while preserving existing markup-enabled behavior. | Best immediate candidate: fastest setup, focused tests, Python-only scope, and strong observability relevance for terminal output. |
| Ruff | Improve one lint or formatter rule edge case with cargo-level verification. | Useful future lane, but first-run Rust compile and snapshot conventions make it a heavier draft than Rich. |

## Selected Draft Candidate

`AIDD-LIVE-013` is drafted from the Rich audit. It stays candidate-only until a
separate proof run and planning update promote it to maintained coverage.
