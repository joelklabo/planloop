PYTHON=.venv/bin/python

.PHONY: setup
setup: ## Set up development environment with uv
	@bash setup-dev.sh

.PHONY: test
test: ## Run all tests
	$(PYTHON) -m pytest tests/ -v

.PHONY: test-fast
test-fast: ## Run tests without coverage
	$(PYTHON) -m pytest tests/ -v --no-cov

.PHONY: test-cov
test-cov: ## Run tests with coverage report
	$(PYTHON) -m pytest tests/ -v --cov=planloop --cov-report=term --cov-report=html

.PHONY: lint
lint: ## Run linters (ruff + mypy)
	$(PYTHON) -m ruff check src/ tests/
	$(PYTHON) -m mypy src/

.PHONY: format
format: ## Format code with ruff
	$(PYTHON) -m ruff format src/ tests/
	$(PYTHON) -m ruff check --fix src/ tests/

.PHONY: clean
clean: ## Remove build artifacts and caches
	rm -rf .venv .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
