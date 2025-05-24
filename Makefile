.PHONY: help
help:
	@echo "clean: del the cruft"
	@echo "test: run linters, formatters, unit tests"
	@echo "venv: create .venv"
	@echo "install: install"

.PHONY: test
test: unit integration

.PHONY: venv
venv:
	uv venv --python 3.11
	uv pip install --editable . --group dev

.PHONY: linters
linters:
	uv run pylint

.PHONY: formatters
formatters:
	@echo "formatters"

.PHONY: unit
unit:
	uv run pytest -m 'not functional'

.PHONY: integration
integration:
	uv run pytest -m 'functional'

.PHONY: clean
clean: clean-build clean-pyc

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	rm -rf .ruff_cache/

