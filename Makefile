.PHONY: install lint typecheck check-complexity test check-agents check-docs check-js test-frontend test-browser check doctor init-demo build

install:
	uv sync --locked --extra dev

lint:
	uv run --extra dev ruff check .

typecheck:
	uv run --extra dev python -m mypy src scripts

check-complexity:
	uv run --extra dev python scripts/check_complexity.py

test:
	uv run --extra dev pytest -q

check-agents:
	uv run --extra dev python scripts/check_agent_instructions.py
	uv run --extra dev pytest -q tests/test_agent_instructions.py tests/test_agent_workflows.py tests/test_planning_integrity.py

check-docs:
	uv run --extra dev python scripts/generate_user_story_traceability.py --check

check-js:
	uv run --extra dev python scripts/check_packaged_javascript.py

test-frontend:
	node --test tests/frontend/*.test.mjs

test-browser:
	uv run --extra dev python scripts/run_packaged_ui_scenarios.py

check: check-agents check-docs lint typecheck check-complexity check-js test-frontend test

doctor:
	uv run aidd doctor

init-demo:
	uv run aidd init --work-item WI-001

build:
	uv build
