.PHONY: help install install-dev setup format lint type-check test test-cov clean pre-commit

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Install project dependencies
	poetry install --only main

install-dev:  ## Install project with development dependencies
	poetry install

setup: install-dev  ## Set up development environment
	poetry run pre-commit install
	@echo ""
	@echo "Development environment setup complete!"
	@echo "Run 'poetry shell' to activate the virtual environment"

format:  ## Format code with black and ruff
	poetry run black .
	poetry run ruff check --fix .

lint:  ## Run linting checks
	poetry run ruff check .
	poetry run black --check .

type-check:  ## Run type checking with mypy
	@if find . -name '*.py' -not -path '*/\.*' | grep -q .; then \
		poetry run mypy .; \
	else \
		echo "No Python files found, skipping type check"; \
	fi

test:  ## Run tests
	poetry run pytest

test-cov:  ## Run tests with coverage report
	poetry run pytest --cov=. --cov-report=html --cov-report=term

clean:  ## Clean up build artifacts and cache files
	rm -rf build/
	rm -rf dist/
	rm -rf .eggs/
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .tox/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache

pre-commit:  ## Run pre-commit hooks on all files
	poetry run pre-commit run --all-files

update-deps:  ## Update dependencies
	poetry update
	poetry run pre-commit autoupdate
