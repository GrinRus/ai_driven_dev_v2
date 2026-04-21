.PHONY: install lint typecheck test check doctor init-demo build

install:
	uv sync --extra dev

lint:
	uv run ruff check .

typecheck:
	uv run mypy src

test:
	uv run pytest -q

check: lint typecheck test

doctor:
	uv run aidd doctor

init-demo:
	uv run aidd init --work-item WI-001

build:
	uv build
