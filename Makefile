PYTHON ?= python
APP = cvt_dashboard:create_app

.PHONY: help install run init-db build-collector test lint format check build security

help:
	@echo "install          Install the package and development tools"
	@echo "run              Start the local Flask dashboard"
	@echo "init-db          Create the SQLite schema"
	@echo "build-collector  Compile the C collector"
	@echo "test             Run integration and regression tests"
	@echo "lint             Check Python style and formatting"
	@echo "format           Format the maintained Python source and tests"
	@echo "check            Run lint and tests"
	@echo "build            Build source and wheel distributions"
	@echo "security         Run static and dependency security scans"

install:
	$(PYTHON) -m pip install -e '.[dev]'

run:
	$(PYTHON) -m flask --app $(APP) run

init-db:
	$(PYTHON) -m flask --app $(APP) init-db

build-collector:
	$(PYTHON) -m flask --app $(APP) build-collector

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m ruff format .

check: lint test

build:
	$(PYTHON) -m build

security:
	$(PYTHON) -m bandit -r src examples -ll
	$(PYTHON) -m pip_audit --skip-editable
