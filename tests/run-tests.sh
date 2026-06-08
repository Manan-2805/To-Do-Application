#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS_DIR="$PROJECT_ROOT/tests/test-results-logs"
CI_DB="todosphere_ci_$(date +%s)"
COMPOSE="docker compose"
BACKEND_CONTAINER="todosphere-backend"
DB_CONTAINER="todosphere-db"
DB_USER="postgres"
DB_PASSWORD="postgrespassword"
BACKEND_DB_URL="postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${CI_DB}"

PASS=0
FAIL=0
FAILED_TESTS=""

cd "$PROJECT_ROOT"
mkdir -p "$LOGS_DIR"

log() { echo "[$(date '+%H:%M:%S')] $*"; }
pass() { log "PASS: $1"; PASS=$((PASS + 1)); }
fail() { log "FAIL: $1"; FAIL=$((FAIL + 1)); FAILED_TESTS="$FAILED_TESTS $1"; }

cleanup() {
    log "Cleaning up temporary database '${CI_DB}'..."
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${CI_DB}' AND pid <> pg_backend_pid();" \
        postgres 2>/dev/null || true
    docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c \
        "DROP DATABASE IF EXISTS \"${CI_DB}\";" postgres 2>/dev/null || true
    log "Stopping containers..."
    $COMPOSE down --remove-orphans 2>/dev/null || true
}

trap cleanup EXIT

log "=========================================="
log "  TodoSphere CI Pipeline"
log "  DB: ${CI_DB}"
log "=========================================="

log "Step 1: Full Docker clean (containers, volumes, local images)..."
$COMPOSE --profile test down -v --remove-orphans 2>/dev/null || true
docker image rm todosphere-backend todosphere-frontend todosphere-e2e 2>/dev/null || true
docker builder prune -f 2>/dev/null || true
rm -rf "$PROJECT_ROOT/backend/uploads/"* 2>/dev/null || true

log "Step 2: Starting database and redis..."
$COMPOSE up -d db redis
log "Waiting for db and redis to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' "$DB_CONTAINER" 2>/dev/null | grep -q healthy; do
    sleep 2
done
until docker inspect --format='{{.State.Health.Status}}' todosphere-redis 2>/dev/null | grep -q healthy; do
    sleep 2
done
log "Database and Redis are healthy."

log "Step 3: Creating temporary CI database '${CI_DB}'..."
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c \
    "DROP DATABASE IF EXISTS \"${CI_DB}\";" postgres
docker exec "$DB_CONTAINER" psql -U "$DB_USER" -c \
    "CREATE DATABASE \"${CI_DB}\";" postgres

log "Step 4: Building and starting backend (connected to '${CI_DB}')..."
DATABASE_URL="$BACKEND_DB_URL" $COMPOSE up -d --build backend
log "Waiting for backend to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' "$BACKEND_CONTAINER" 2>/dev/null | grep -q healthy; do
    sleep 3
done
log "Backend is healthy."

log "Step 5: Running Alembic migrations on '${CI_DB}'..."
$COMPOSE exec -T -e "DATABASE_URL=$BACKEND_DB_URL" backend \
    sh -c "alembic upgrade head"

log "Step 6: Seeding CI database with faker data..."
$COMPOSE exec -T -e "DATABASE_URL=$BACKEND_DB_URL" backend \
    python -B scripts/ci_seed.py

log "Step 7: Starting frontend..."
$COMPOSE up -d frontend
log "Waiting for frontend to be healthy..."
until docker inspect --format='{{.State.Health.Status}}' todosphere-frontend 2>/dev/null | grep -q healthy; do
    sleep 3
done
log "Frontend is healthy."

log "------------------------------------------"
log "Step 8.1: Running Unit Tests..."
if $COMPOSE exec -T backend \
    python -B -m pytest tests/unit/ -v --tb=short 2>&1 | tee "$LOGS_DIR/unit.log"; then
    pass "Unit Tests"
else
    fail "Unit Tests"
    cat "$LOGS_DIR/unit.log"
fi

log "------------------------------------------"
log "Step 8.2: Running Integration Tests..."
if $COMPOSE exec -T backend \
    python -B -m pytest tests/integration/ -v --tb=short \
    --cov=src --cov-report=term-missing 2>&1 | tee "$LOGS_DIR/integration.log"; then
    pass "Integration Tests"
else
    fail "Integration Tests"
    cat "$LOGS_DIR/integration.log"
fi

log "------------------------------------------"
log "Step 8.3: Running E2E Playwright Tests..."
if $COMPOSE --profile test run --rm -T e2e 2>&1 | tee "$LOGS_DIR/e2e.log"; then
    pass "E2E Tests"
else
    fail "E2E Tests"
    cat "$LOGS_DIR/e2e.log"
fi

log "------------------------------------------"
log "Step 8.4: Running Locust Performance Tests..."
if $COMPOSE exec -T backend \
    python -B -m locust \
    -f tests/performance/locustfile.py \
    --headless -u 10 -r 2 --run-time 30s \
    --host http://127.0.0.1:8000 2>&1 | tee "$LOGS_DIR/locust.log"; then
    pass "Performance Tests"
else
    fail "Performance Tests"
    cat "$LOGS_DIR/locust.log"
fi

log "=========================================="
log "  Results: ${PASS} passed, ${FAIL} failed"
log "  Logs saved to: tests/test-results-logs/"
log "=========================================="

if [ "$FAIL" -gt 0 ]; then
    log "FAILED TESTS:${FAILED_TESTS}"
    exit 1
fi

log "All tests passed."
