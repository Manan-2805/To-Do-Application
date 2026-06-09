# Makefile — Developer shortcuts for TodoSphere

# ──────────────────────────────────────────
# Variables
# ──────────────────────────────────────────
APP        := todosphere
DC         := docker compose
BACKEND    := todosphere-dev-backend

# Performance testing defaults
users      ?= 50
rate       ?= 10
time       ?= 60s

.DEFAULT_GOAL := help

# ──────────────────────────────────────────
# Help — auto-generated from ## comments
# ──────────────────────────────────────────
.PHONY: help
help:  ## Show this help message
	@python -B -c "import sys, re; lines = [m.groups() for f in sys.argv[1:] for l in open(f, encoding='utf-8') if (m := re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', l))]; [print(f'  \x1b[36m{k:<22}\x1b[0m {v}') for k, v in sorted(lines)]" $(MAKEFILE_LIST)

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
# Testing & Code Quality
# ──────────────────────────────────────────
.PHONY: check
check:  ## Run all code quality checks (lint, format, typecheck, security) for backend and frontend
	@powershell -Command "$$failed = $$false; \
	New-Item -ItemType Directory -Force -Path reports -ErrorAction SilentlyContinue | Out-Null; \
	Write-Host '=== [1/11] Running Ruff Linter (Backend) ===' -ForegroundColor Cyan; cd backend; uv run ruff check src/ tests/; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Backend Ruff check failed!' -ForegroundColor Red } else { Write-Host 'Backend Ruff check passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [2/11] Running Ruff Format Check (Backend) ===' -ForegroundColor Cyan; cd backend; uv run ruff format --check src/ tests/ scripts/; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Backend Ruff format check failed!' -ForegroundColor Red } else { Write-Host 'Backend Ruff format check passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [3/11] Running MyPy Typecheck (Backend) ===' -ForegroundColor Cyan; cd backend; uv run mypy -p src; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Backend MyPy typecheck failed!' -ForegroundColor Red } else { Write-Host 'Backend MyPy typecheck passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [4/11] Running Bandit Security Scan (Backend) ===' -ForegroundColor Cyan; cd backend; uv run bandit -c pyproject.toml -r src/; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Backend Bandit scan failed!' -ForegroundColor Red } else { Write-Host 'Backend Bandit scan passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [5/11] Running Pip-Audit (Backend) ===' -ForegroundColor Cyan; cd backend; uv run pip-audit; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Backend Pip-Audit failed!' -ForegroundColor Red } else { Write-Host 'Backend Pip-Audit passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [6/11] Running Prettier Format Check (Frontend) ===' -ForegroundColor Cyan; cd frontend; npm run format:check; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Frontend Prettier format check failed!' -ForegroundColor Red } else { Write-Host 'Frontend Prettier format check passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [7/11] Running ESLint (Frontend) ===' -ForegroundColor Cyan; cd frontend; npm run lint; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Frontend ESLint failed!' -ForegroundColor Red } else { Write-Host 'Frontend ESLint passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [8/11] Running TypeScript Compiler (Frontend) ===' -ForegroundColor Cyan; cd frontend; npx tsc -b; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Frontend TypeScript compilation failed!' -ForegroundColor Red } else { Write-Host 'Frontend TypeScript compilation passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [9/11] Running NPM Audit (Frontend) ===' -ForegroundColor Cyan; cd frontend; npm audit; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Frontend NPM Audit failed!' -ForegroundColor Red } else { Write-Host 'Frontend NPM Audit passed.' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [10/11] Running React Doctor (Frontend) ===' -ForegroundColor Cyan; cd frontend; npx react-doctor@latest --yes --verbose > ../reports/react-doctor-report.txt 2>&1; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'React Doctor found issues or failed! Check reports/react-doctor-report.txt' -ForegroundColor Red } else { Write-Host 'React Doctor completed. Report written to reports/react-doctor-report.txt' -ForegroundColor Green }; cd ..; \
	Write-Host '=== [11/11] Running Lighthouse Audit ===' -ForegroundColor Cyan; cd frontend; npx lighthouse http://localhost:8080/login --only-categories=performance,accessibility,best-practices,seo --output=html --output-path=../reports/lighthouse-report.html > $$null 2>&1; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Lighthouse audit failed! (Is the application running at http://localhost:8080?)' -ForegroundColor Red } else { Write-Host 'Lighthouse audit completed. Report written to reports/lighthouse-report.html' -ForegroundColor Green }; cd ..; \
	if ($$failed) { Write-Host '=== Quality Checks FAILED ===' -ForegroundColor Red; exit 1 } else { Write-Host '=== Quality Checks PASSED ===' -ForegroundColor Green }"

.PHONY: check-fix
check-fix:  ## Run auto-fixes (ruff lint/format, prettier, eslint fix)
	@powershell -Command "$$failed = $$false; \
	Write-Host '=== Auto-fixing Backend Code ===' -ForegroundColor Cyan; cd backend; uv run ruff check --fix src/ tests/; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Backend Ruff check --fix failed!' -ForegroundColor Red }; uv run ruff format src/ tests/ scripts/; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Backend Ruff format failed!' -ForegroundColor Red }; cd ..; \
	Write-Host '=== Auto-fixing Frontend Code ===' -ForegroundColor Cyan; cd frontend; npm run format; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Frontend format failed!' -ForegroundColor Red }; npx eslint . --fix; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Frontend ESLint --fix failed!' -ForegroundColor Red }; cd ..; \
	if ($$failed) { Write-Host '=== Auto-Fix FAILED ===' -ForegroundColor Red; exit 1 } else { Write-Host '=== Auto-Fix COMPLETED ===' -ForegroundColor Green }"

.PHONY: test
test:  ## Run all tests (backend, frontend unit, and Playwright E2E) and gather reports in reports/
	@powershell -Command "$$failed = $$false; \
	Write-Host '=== Preparing reports/ directory ===' -ForegroundColor Cyan; \
	Remove-Item -Path reports -Recurse -Force -ErrorAction SilentlyContinue; \
	New-Item -ItemType Directory -Force -Path reports | Out-Null; \
	\
	Write-Host '=== Detecting Database Password ===' -ForegroundColor Cyan; \
	$$db_pwd = 'postgrespassword'; \
	if ($$env:DB_PASSWORD) { \
		$$db_pwd = $$env:DB_PASSWORD; \
		Write-Host 'Using DB_PASSWORD from environment override.' -ForegroundColor Gray; \
	} elseif (docker ps --filter name=todosphere-prod-db --filter status=running --quiet) { \
		$$db_pwd = 'changeme_in_prod'; \
		Write-Host 'Detected running prod container todosphere-prod-db, using password: changeme_in_prod' -ForegroundColor Gray; \
	} else { \
		Write-Host 'Using default development password: postgrespassword' -ForegroundColor Gray; \
	}; \
	\
	Write-Host '=== Running pytest (Backend Unit + Integration) ===' -ForegroundColor Cyan; \
	$$env:DATABASE_URL=\"postgresql+asyncpg://postgres:$$db_pwd@127.0.0.1:5432/todosphere\"; \
	$$env:REDIS_URL='redis://127.0.0.1:6379/0'; \
	cd backend; uv run python -B -m pytest tests/ -v --tb=short --cov=src --cov-report=html:../reports/backend-coverage --junitxml=../reports/backend-report.xml; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Backend pytest suite failed!' -ForegroundColor Red } else { Write-Host 'Backend pytest suite passed.' -ForegroundColor Green }; cd ..; \
	\
	Write-Host '=== Running Vitest Unit Tests (Frontend) ===' -ForegroundColor Cyan; \
	cd frontend; npx vitest run --coverage --reporter=default --reporter=junit --outputFile=../reports/frontend-report.xml; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Frontend Vitest suite failed!' -ForegroundColor Red } else { Write-Host 'Frontend Vitest suite passed.' -ForegroundColor Green }; cd ..; \
	\
	Write-Host '=== Running Playwright E2E Tests ===' -ForegroundColor Cyan; \
	cd frontend; npx playwright install chromium; $$env:PLAYWRIGHT_HTML_REPORT='../reports/playwright-report'; npx playwright test --reporter=html; if ($$LASTEXITCODE -ne 0) { $$failed = $$true; Write-Host 'Frontend Playwright E2E suite failed!' -ForegroundColor Red } else { Write-Host 'Frontend Playwright E2E suite passed.' -ForegroundColor Green }; cd ..; \
	\
	if ($$failed) { Write-Host '=== Test Suites FAILED ===' -ForegroundColor Red; exit 1 } else { Write-Host '=== Test Suites PASSED ===' -ForegroundColor Green }"

.PHONY: test-perf
test-perf:  ## Run Locust performance tests (customizable: make test-perf users=100 rate=10 time=60s)
	$(DC) exec backend python -B -m locust \
		-f tests/performance/locustfile.py \
		--headless -u $(users) -r $(rate) --run-time $(time) \
		--only-summary \
		--html tests/performance/locust-report.html \
		--host http://localhost:8000

.PHONY: test-stress
test-stress: users = 500
test-stress: rate = 50
test-stress: time = 5m
test-stress:  ## Run Locust stress tests (customizable: make test-stress users=1000 rate=100 time=10m)
	$(DC) exec backend python -B -m locust \
		-f tests/performance/locustfile.py \
		--headless -u $(users) -r $(rate) --run-time $(time) \
		--only-summary \
		--html tests/performance/locust-report.html \
		--host http://localhost:8000

.PHONY: rebuild-backend
rebuild-backend:  ## Rebuild and restart backend container
	$(DC) build backend
	$(DC) up -d --force-recreate backend

.PHONY: rebuild-frontend
rebuild-frontend:  ## Rebuild and restart frontend container
	$(DC) build frontend
	$(DC) up -d --force-recreate frontend

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
	rm -rf frontend/tests/test-results-logs/* 2>/dev/null || true

.PHONY: clean-all
clean-all:  ## Remove containers, volumes, images and build cache
	$(DC) down -v --remove-orphans
	docker image rm $(APP)-backend $(APP)-frontend 2>/dev/null || true
	docker builder prune -f
	rm -rf backend/uploads/* 2>/dev/null || true
	rm -rf frontend/tests/test-results-logs/* 2>/dev/null || true
