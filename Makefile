.PHONY: help install dev lint format typecheck test test-fast test-cov clean docs docker-build docker-run

PYTHON := python
PIP := pip
PYTEST := pytest
RUFF := ruff
MYPY := mypy

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install package in production mode
	$(PIP) install -e .

dev: ## Install package with all dev dependencies
	$(PIP) install -e ".[dev,docs,all]"
	pre-commit install --install-hooks

lint: ## Run linter (ruff check)
	$(RUFF) check src/ tests/

format: ## Auto-format code
	$(RUFF) format src/ tests/
	$(RUFF) check --fix src/ tests/

typecheck: ## Run mypy type checking
	$(MYPY) src/podifyr/

test: ## Run full test suite
	$(PYTEST) tests/ -v

test-fast: ## Run unit tests only (no network, no slow)
	$(PYTEST) tests/unit/ -v -m "not slow"

test-cov: ## Run tests with coverage report
	$(PYTEST) tests/ --cov=podifyr --cov-report=html --cov-report=term-missing

clean: ## Remove build artifacts and caches
	rm -rf build/ dist/ *.egg-info .mypy_cache .pytest_cache .ruff_cache
	rm -rf htmlcov/ coverage.xml .coverage
	rm -rf src/*.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

docs: ## Build documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

docker-build: ## Build Docker image
	docker build -t podifyr:latest .

docker-run: ## Run podifyr in Docker (pass ARGS="generate ./repo")
	docker run --rm -v $$(pwd):/workspace -e OPENAI_API_KEY podifyr:latest $(ARGS)

release-check: ## Pre-release checks (lint + typecheck + test)
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
