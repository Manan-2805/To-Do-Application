# Makefile — Developer shortcuts for TodoSphere

# ──────────────────────────────────────────
# Variables
# ──────────────────────────────────────────
APP        := todosphere
DC         := docker compose
BACKEND    := todosphere-backend

.DEFAULT_GOAL := help

# ──────────────────────────────────────────
# Help — auto-generated from ## comments
# ──────────────────────────────────────────
.PHONY: help
help:  ## Show this help message
	@python -c "import sys, re; lines = [m.groups() for f in sys.argv[1:] for l in open(f, encoding='utf-8') if (m := re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', l))]; [print(f'  \x1b[36m{k:<22}\x1b[0m {v}') for k, v in sorted(lines)]" $(MAKEFILE_LIST)

# ──────────────────────────────────────────
# Development
# ──────────────────────────────────────────
.PHONY: build
build:  ## Build all dev images fresh (no cache)
	$(DC) build --no-cache

.PHONY: up
up:  ## Start the full dev stack in background
	$(DC) up -d

.PHONY: up-build
up-build:  ## Build and start the full dev stack
	$(DC) up -d --build

.PHONY: down
down:  ## Stop and remove containers (keep volumes)
	$(DC) down --remove-orphans

.PHONY: down-clean
down-clean:  ## Stop containers and remove volumes (DESTROYS DATA)
	$(DC) down -v --remove-orphans

.PHONY: restart
restart:  ## Restart all containers
	$(DC) restart

.PHONY: logs
logs:  ## Follow logs from all containers
	$(DC) logs -f

.PHONY: logs-backend
logs-backend:  ## Follow backend logs only
	$(DC) logs -f backend

.PHONY: logs-frontend
logs-frontend:  ## Follow frontend logs only
	$(DC) logs -f frontend

.PHONY: shell-backend
shell-backend:  ## Open a shell in the running backend container
	$(DC) exec backend bash

.PHONY: shell-frontend
shell-frontend:  ## Open a shell in the running frontend container
	$(DC) exec frontend sh

# ──────────────────────────────────────────
# Database
# ──────────────────────────────────────────
.PHONY: migrate
migrate:  ## Run alembic upgrade head
	$(DC) exec backend sh -c "alembic upgrade head"

.PHONY: migration
migration:  ## Create a new migration: make migration name="add table"
	$(DC) exec backend sh -c "alembic revision --autogenerate -m '$(name)'"

.PHONY: rollback
rollback:  ## Roll back the last migration
	$(DC) exec backend sh -c "alembic downgrade -1"

.PHONY: db-reset
db-reset:  ## Roll back all and re-migrate (DESTROYS DATA)
	$(DC) exec backend sh -c "alembic downgrade base && alembic upgrade head"

.PHONY: db-shell
db-shell:  ## Open a psql shell in the PostgreSQL container
	$(DC) exec db psql -U postgres -d todosphere

.PHONY: redis-shell
redis-shell:  ## Open a redis-cli shell
	$(DC) exec redis redis-cli

.PHONY: seed
seed:  ## Seed the dev database with demo data
	$(DC) exec backend python -B scripts/seed.py

# ──────────────────────────────────────────
# Testing (runs inside backend container)
# ──────────────────────────────────────────
.PHONY: test
test:  ## Run all pytest (unit + integration) with coverage
	$(DC) exec backend python -B -m pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

.PHONY: test-unit
test-unit:  ## Run unit tests only
	$(DC) exec backend python -B -m pytest tests/unit/ -v --tb=short

.PHONY: test-integration
test-integration:  ## Run integration tests with coverage
	$(DC) exec backend python -B -m pytest tests/integration/ -v --tb=short --cov=src --cov-report=term-missing

.PHONY: test-e2e
test-e2e:  ## Run Playwright E2E tests (builds e2e container)
	$(DC) --profile test run --rm e2e

.PHONY: test-perf
test-perf:  ## Run Locust performance tests (30s, 10 users)
	$(DC) exec backend python -B -m locust \
		-f tests/performance/locustfile.py \
		--headless -u 10 -r 2 --run-time 30s \
		--host http://localhost:8000

.PHONY: test-all
test-all: test test-e2e test-perf  ## Run all test types in sequence

# ──────────────────────────────────────────
# CI Pipeline
# ──────────────────────────────────────────
.PHONY: ci
ci:  ## Full clean rebuild + all tests (CI pipeline)
	bash tests/run-tests.sh

# ──────────────────────────────────────────
# Code Quality (runs inside backend container)
# ──────────────────────────────────────────
.PHONY: lint
lint:  ## Run ruff linter on src/ and tests/
	$(DC) exec backend ruff check src/ tests/

.PHONY: lint-fix
lint-fix:  ## Run ruff linter with auto-fix
	$(DC) exec backend ruff check --fix src/ tests/

.PHONY: format
format:  ## Format code with ruff
	$(DC) exec backend ruff format src/ tests/ scripts/

.PHONY: format-check
format-check:  ## Check formatting without making changes
	$(DC) exec backend ruff format --check src/ tests/ scripts/

.PHONY: typecheck
typecheck:  ## Run mypy type checker on src/
	$(DC) exec backend mypy -p src

.PHONY: security
security:  ## Run bandit security scan on src/
	$(DC) exec backend bandit -c pyproject.toml -r src/

.PHONY: audit
audit:  ## Scan dependencies for known CVEs
	$(DC) exec backend pip-audit

.PHONY: check
check: lint format-check typecheck security audit  ## Run all code quality and security checks

# ──────────────────────────────────────────
# Production
# ──────────────────────────────────────────
.PHONY: prod-build
prod-build:  ## Build production images
	$(DC) -f docker-compose.prod.yml build

.PHONY: prod-up
prod-up:  ## Start the production stack
	$(DC) -f docker-compose.prod.yml up -d

.PHONY: prod-down
prod-down:  ## Stop the production stack
	$(DC) -f docker-compose.prod.yml down

# ──────────────────────────────────────────
# Cleanup
# ──────────────────────────────────────────
.PHONY: clean
clean:  ## Remove upload files and stop containers (keep images)
	$(DC) down --remove-orphans
	rm -rf backend/uploads/* 2>/dev/null || true
	rm -rf tests/test-results-logs/* 2>/dev/null || true

.PHONY: clean-all
clean-all:  ## Remove containers, volumes, images and build cache
	$(DC) --profile test down -v --remove-orphans
	docker image rm $(APP)-backend $(APP)-frontend $(APP)-e2e 2>/dev/null || true
	docker builder prune -f
	rm -rf backend/uploads/* 2>/dev/null || true
	rm -rf tests/test-results-logs/* 2>/dev/null || true
