.PHONY: install lint typecheck test check doctor init-demo build

install:
	uv sync --locked --extra dev

lint:
	uv run --extra dev ruff check .

typecheck:
	uv run --extra dev python -m mypy src scripts

test:
	uv run --extra dev pytest -q

check: lint typecheck test

doctor:
	uv run aidd doctor

init-demo:
	uv run aidd init --work-item WI-001

build:
	uv build
