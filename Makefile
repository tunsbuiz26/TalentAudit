.PHONY: install test lint format-check typecheck check

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest

lint:
	ruff check .

format-check:
	ruff format --check .

typecheck:
	mypy src

check: lint format-check typecheck test

