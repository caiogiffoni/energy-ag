.PHONY: install test test-verbose test-cov lint format format-check typecheck check run

install:
	uv sync --dev

test:
	uv run pytest -q

test-verbose:
	uv run pytest -v

test-cov:
	uv run pytest --cov=workflow --cov=utils --cov=libraries --cov-report=term-missing

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy .

check:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

run:
	uv run python -m robocorp.tasks run tasks.py
