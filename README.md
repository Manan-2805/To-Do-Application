# TodoSphere (DevOps Minimal Edition)

An enterprise-grade, secure, and production-optimized full-stack task management application. Built using FastAPI, React 19, TypeScript, PostgreSQL, and Redis, orchestrated entirely with Docker Compose, and validated with strict static analysis and automated test suites.

---

## 📂 Sub-Project Portals

For detailed documentation, development setup, and API details on each specific layer:

- 💻 **[React Frontend Portal](frontend/README.md)**: React 19, Vite, TypeScript, Vanilla CSS, React Doctor (96/100), and Lighthouse audits.
- ⚙️ **[FastAPI Backend Service](backend/README.md)**: FastAPI, Pydantic, SQLAlchemy, Alembic, uv, and security middleware.

---

## 🛠️ Technical Stack

- **Frontend**: React (v19) + TypeScript + Vite (v8) + Vanilla CSS Variables (Light/Dark mode transitions)
- **Backend**: FastAPI (Python 3.12)
- **Database**: PostgreSQL (SQLAlchemy 2.x, Alembic Migrations)
- **Caching & Rate Limiting**: Redis + SlowAPI
- **Package Managers**: `uv` (Python), `npm` (Node)
- **Security Protocols**: HttpOnly Cookies + JWT Rotation + Argon2id Hashing + Security Headers Middleware
- **Quality Verification**: Ruff, Prettier, ESLint, MyPy, Bandit, Pip-Audit, NPM Audit, React Doctor (Score 96), and Lighthouse
- **Orchestration**: Docker Compose with named volumes, multi-stage caching, and non-root execution contexts
- **Testing Suite**: Pytest (unit/integration), Vitest (component), Playwright (E2E browser), and Locust (load/stress testing)

---

## 🌟 Architectural & DevOps Highlights

1. **Optimized Docker Image Strategy**:
   - Separate development (`Dockerfile.dev`) and production (`Dockerfile`) configurations for both backend and frontend.
   - Development dependencies are baked directly into docker layers and cached. They are **not** mounted from the host machine, keeping environments isolated, clean, and high-performing.
2. **Refresh Token Rotation**: Secures authentication sessions using HttpOnly cookies with token rotation. If an invalid or reused refresh token is detected, all active sessions for that user are revoked.
3. **Database Constraints & Validation**: Enforces check constraints (`expected_end_time >= start_time`, `actual_end_time >= start_time`) directly at the database layer.
4. **State Machine**: Restricts task status progression (e.g. `Done` is a terminal state). Auto-calculates task durations upon completion.
5. **Background Scheduler**: Asynchronously transitions tasks that pass their deadline to a `Missed` status.
6. **Uploads Abstraction & Validation**: Abstract `StorageProvider` supports local and S3 storage stubs. Restricts files to 5 MB and formats `.jpg`, `.jpeg`, `.png`, and `.webp`.
7. **JSON Log Correlation**: Request-scoped middleware generates unique `X-Correlation-ID` values, injected into context variables and written inside structured JSON application logs.
8. **Security Headers Middleware**: Injects `X-Frame-Options`, `X-Content-Type-Options`, and `Referrer-Policy` security headers on all responses.

---

## 🚀 Quick Start Guide

### Prerequisites

- **Docker & Docker Compose**: Required for running the application services.
- **make**: Used for executing automated tasks via the Makefile.

### 1. Spin Up Application Stack
Launch the database, cache, api backend, and frontend interface:
```bash
make up-build
```
Access the application at `http://localhost:8080`. The FastAPI interactive docs are accessible at `http://localhost:8000/docs`.

### 2. Seed Mock Database Data
Create a test account (`demo_user` / `Password123!`) seeded with 10+ historical tasks:
```bash
make seed
```

---

## 💻 Developer command reference

All common developer tasks are orchestrated via the main `Makefile`:

### Docker Operations
- `make build` - Rebuild all dev images fresh (no cache).
- `make up` - Start the full dev stack in the background.
- `make up-build` - Build and start the full dev stack.
- `make down` - Stop and remove containers (keep volumes).
- `make down-clean` - Stop containers and remove volumes (DESTROYS DATA).
- `make restart` - Restart all containers.
- `make logs` - Follow logs from all containers.
- `make logs-backend` - Follow backend logs only.
- `make logs-frontend` - Follow frontend logs only.
- `make shell-backend` - Open a shell in the running backend container.
- `make shell-frontend` - Open a shell in the running frontend container.

### Database Operations
- `make migrate` - Run alembic database upgrade.
- `make migration name="name"` - Create a new alembic revision revision.
- `make rollback` - Roll back the last migration.
- `make db-reset` - Roll back all migrations and re-apply them (DESTROYS DATA).
- `make db-shell` - Open a psql shell inside the PostgreSQL container.
- `make redis-shell` - Open a redis-cli shell.
- `make seed` - Seed the dev database with demo data.

### Consolidated Quality Checking & Code Style
- **`make check`**: Runs all quality checks for backend and frontend sequentially. It prints subtask names and runs to completion, returning exit code `1` at the end if any checks failed.
  - *Included checks:* Ruff, Ruff Formatter, MyPy, Bandit, Pip-Audit, Prettier, ESLint, TypeScript compilation, NPM Audit, React Doctor, and Lighthouse.
- **`make check-fix`**: Automatically runs code fixes and formatters across both backend and frontend code (Ruff check/format, Prettier write, and ESLint fix).

### Automated Testing Suite
- **`make test`**: Resets the local `reports/` folder, runs all unit/integration tests (pytest), vitest components, and Playwright E2E suites, saving coverage and JUnit XML reports to `reports/`.
  - *Note:* The database password is dynamically resolved on the fly: if a running production container `todosphere-prod-db` is detected, it configures authentication password `changeme_in_prod`, else defaults to development password `postgrespassword`.
- **`make test-perf`**: Run Locust performance benchmarking (default: 50 concurrent users, 10 spawn rate, 1 minute).
- **`make test-stress`**: Run Locust stress testing (500 users, 50 spawn rate, 5 minutes).

---

## 📊 Compiled Quality Reports Directory (`reports/`)

All verification tasks save output files inside the root-level `reports/` folder:

- **React Doctor Diagnostics**: `reports/react-doctor-report.txt` (Score: 96/100)
- **Lighthouse Performance HTML Report**: `reports/lighthouse-report.html`
- **Backend Test Coverage (HTML)**: `reports/backend-coverage/index.html`
- **Backend JUnit XML Reports**: `reports/backend-report.xml`
- **Frontend Test Coverage (HTML)**: `reports/frontend-coverage/index.html`
- **Frontend JUnit XML Reports**: `reports/frontend-report.xml`
- **Playwright Browser E2E HTML Report**: `reports/playwright-report/index.html`
