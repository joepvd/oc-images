.PHONY: help
help:
	@echo "venv: create .venv"
	@echo "clean: del the cruft"
	@echo "test: run linters, formatters, unit tests"
	@echo "- unit: run unit tests"
	@echo "- integration: run integration tests"
	@echo "- lint: run linter"
	@echo "- format-check: run format-check"
	@echo "format: Run formatter"

.PHONY: test
test: venv unit lint check-format integration

.PHONY: venv
venv: .venv/bin/python
	uv pip install --editable . --group dev

.venv/bin/python:
	uv venv --python 3.11

.PHONY: lint
lint:
	uv run pylint --errors-only src/ tests/

.PHONY: format
format:
	uv run -m ruff check --select I --fix
	uv run -m ruff format

.PHONY: check-format
check-format:
	uv run ruff check --select I --output-format concise
	uv run -m ruff format --check

.PHONY: unit
unit:
	uv run pytest -m 'not functional'

.PHONY: integration
integration:
	uv run pytest -m 'functional'

.PHONY: clean
clean:
	rm -rf .venv
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	rm -rf .ruff_cache/

