#!/usr/bin/env bash
# scripts/run-tests.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$PROJECT_ROOT/frontend/tests/test-results-logs"
CI_DB="todosphere_ci_$(date +%s)"
COMPOSE="docker compose"
DB_CONTAINER="todosphere-db"
DB_USER="postgres"
DB_PASSWORD="postgrespassword"
BACKEND_DB_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${CI_DB}"

# Ensure logs dir exists
mkdir -p "$LOGS_DIR"
LOG_FILE="$LOGS_DIR/ci_run.log"

# Redirect all stdout and stderr to the log file, while keeping output on console
exec > >(tee -i "$LOG_FILE") 2>&1

log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "=========================================="
log "  TodoSphere CI Pipeline (Active Stack Mode)"
log "  DB: ${CI_DB}"
log "  Log: ${LOG_FILE}"
log "=========================================="

log "Step 1: Checking if required docker containers are running..."
REQUIRED_CONTAINERS=("todosphere-db" "todosphere-redis" "todosphere-backend" "todosphere-frontend")
for container in "${REQUIRED_CONTAINERS[@]}"; do
    if ! docker ps --format '{{.Names}}' | grep -Eq "^${container}$"; then
        log "Error: Container '${container}' is not running."
        log "Please start the development environment using 'make up' before running this script."
        exit 1
    fi
done
log "All required containers are running."

log "Step 2: Quality checking backend..."
if $COMPOSE exec -T backend ruff check src/ tests/ && \
   $COMPOSE exec -T backend ruff format --check src/ tests/ scripts/ && \
   $COMPOSE exec -T backend mypy -p src && \
   $COMPOSE exec -T backend bandit -c pyproject.toml -r src/ && \
   $COMPOSE exec -T backend pip-audit; then
    log "Backend quality checks passed."
else
    log "Error: Backend quality checks failed."
    exit 1
fi

log "Step 3: Quality checking frontend..."
if $COMPOSE exec -T frontend npm run lint && \
   $COMPOSE exec -T frontend npx tsc --noEmit; then
    log "Frontend quality checks passed."
else
    log "Error: Frontend quality checks failed."
    exit 1
fi

log "Step 4: Initializing temporary database '${CI_DB}'..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c "CREATE DATABASE \"${CI_DB}\";" postgres

# Setup exit trap to cleanup temp database and restore backend to dev database
cleanup() {
    log "Cleaning up temporary database '${CI_DB}'..."
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${CI_DB}' AND pid <> pg_backend_pid();" \
        postgres 2>/dev/null || true
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c \
        "DROP DATABASE IF EXISTS \"${CI_DB}\";" postgres 2>/dev/null || true
    
    log "Restoring backend container to development database..."
    $COMPOSE up -d backend 2>/dev/null || true
    log "Teardown complete."
}
trap cleanup EXIT

log "Step 5: Redirecting backend container to temporary database..."
DATABASE_URL="$BACKEND_DB_URL" $COMPOSE up -d backend
log "Waiting for backend container to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' todosphere-backend 2>/dev/null | grep -q healthy; do
    sleep 2
done
log "Backend container is healthy on '${CI_DB}'."

log "Step 6: Running migrations on temporary database..."
$COMPOSE exec -T -e "DATABASE_URL=$BACKEND_DB_URL" backend alembic upgrade head

log "Step 7: Seeding temporary database with rich fake data..."
$COMPOSE exec -T -e "DATABASE_URL=$BACKEND_DB_URL" backend python -B scripts/ci_seed.py

PASS=0
FAIL=0
FAILED_SUITES=""

log "------------------------------------------"
log "Step 8.1: Running Unit Tests..."
if $COMPOSE exec -T -e "DATABASE_URL=$BACKEND_DB_URL" backend \
    python -B -m pytest tests/unit/ -v --tb=short 2>&1 | tee "$LOGS_DIR/unit.log"; then
    log "PASS: Unit Tests"
    PASS=$((PASS + 1))
else
    log "FAIL: Unit Tests"
    FAIL=$((FAIL + 1))
    FAILED_SUITES="$FAILED_SUITES Unit Tests;"
fi

log "------------------------------------------"
log "Step 8.2: Running Integration Tests with Coverage..."
if $COMPOSE exec -T -e "DATABASE_URL=$BACKEND_DB_URL" backend \
    python -B -m pytest tests/integration/ -v --tb=short \
    --cov=src --cov-report=term-missing 2>&1 | tee "$LOGS_DIR/integration.log"; then
    log "PASS: Integration Tests"
    PASS=$((PASS + 1))
else
    log "FAIL: Integration Tests"
    FAIL=$((FAIL + 1))
    FAILED_SUITES="$FAILED_SUITES Integration Tests;"
fi

log "------------------------------------------"
log "Step 8.3: Running E2E Playwright Tests..."
if $COMPOSE --profile test run --rm -T e2e 2>&1 | tee "$LOGS_DIR/e2e.log"; then
    log "PASS: E2E Tests"
    PASS=$((PASS + 1))
else
    log "FAIL: E2E Tests"
    FAIL=$((FAIL + 1))
    FAILED_SUITES="$FAILED_SUITES E2E Tests;"
fi

log "------------------------------------------"
log "Step 8.4: Running Locust Performance Tests..."
if $COMPOSE exec -T -e "DATABASE_URL=$BACKEND_DB_URL" backend \
    python -B -m locust \
    -f tests/performance/locustfile.py \
    --headless -u 10 -r 2 --run-time 30s \
    --host http://127.0.0.1:8000 2>&1 | tee "$LOGS_DIR/locust.log"; then
    log "PASS: Performance Tests"
    PASS=$((PASS + 1))
else
    log "FAIL: Performance Tests"
    FAIL=$((FAIL + 1))
    FAILED_SUITES="$FAILED_SUITES Performance Tests;"
fi

log "=========================================="
log "  Results: ${PASS} passed, ${FAIL} failed"
log "  Logs saved to: ${LOGS_DIR}/"
log "=========================================="

if [ "$FAIL" -gt 0 ]; then
    log "CI pipeline failed on suites: ${FAILED_SUITES}"
    exit 1
fi

log "CI pipeline completed successfully. All tests passed."
