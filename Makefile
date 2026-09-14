.PHONY: help install sync lint lint-fix format test check run interactive visualize clean

# Default prompt when running 'make run' without arguments
PROMPT ?= "Fetch past 2 weeks python roles jobs and opening in linkedin and summarize them in a table with title, company, location, and link, and save it job.md file"

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: sync ## Install and sync dependencies with uv
sync: ## Synchronize uv virtual environment
	uv sync --all-extras

lint: ## Check code style and errors using Ruff
	uv run ruff check .

lint-fix: ## Auto-fix linting issues using Ruff
	uv run ruff check --fix .

format: ## Format codebase using Ruff
	uv run ruff format .

test: ## Run the pytest test suite
	uv run pytest -v tests/

check: lint test ## Run both linter and tests (CI verification)

run: ## Run automation agent with a prompt (e.g., make run PROMPT="your task")
	uv run python main.py $(PROMPT)

interactive: ## Run agent in interactive prompt mode
	uv run python main.py -i

visualize: ## Export LangGraph workflow diagram as Mermaid and PNG
	uv run python main.py --visualize

clean: ## Clean up temporary files, build artifacts, and caches
	rm -rf .pytest_cache .ruff_cache __pycache__ src/**/__pycache__ tests/__pycache__
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
