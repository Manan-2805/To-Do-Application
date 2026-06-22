# TodoSphere Backend Service

This directory contains the source code for the high-performance, secure, and enterprise-grade Python API backend that powers the TodoSphere ecosystem.

---

## Technical Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Database**: PostgreSQL (with SQLAlchemy 2.0 and Alembic migrations)
- **Caching & Rate Limiting**: Redis + SlowAPI (limiting endpoint abuse)
- **Object Storage**: AWS S3 / LocalStack (fully async via aiobotocore)
- **Validation**: Pydantic v2
- **Package Manager & Runner**: `uv` (fast dependency resolution)
- **Password Hashing**: Argon2id (highly secure password verification)
- **Authentication**: JWT authentication with access/refresh tokens and refresh token rotation

---

## Directory Layout & Architecture

The backend implements a clean separation of concerns using a **Controller-Service-Repository** pattern:

```text
backend/
├── alembic/                      # Database migrations scripts
├── alembic.ini                   # Alembic configuration
├── pyproject.toml                # Project configurations & dependency declarations
├── Dockerfile                    # Production multi-stage Dockerfile
├── Dockerfile.dev                # Development Dockerfile (caches virtual env)
└── src/
    ├── main.py                   # FastAPI Application Entrypoint
    ├── core/                     # Cross-cutting concerns (middleware, configs, logging)
    ├── dependencies/             # Injection dependencies (auth context, database sessions)
    ├── models/                   # SQLAlchemy database schemas
    ├── repositories/             # Database transaction query layers
    ├── services/                 # Business logic implementation and transactions
    │   └── storage/              # Storage providers (base storage, local filesystem, async S3)
    └── utils/                    # Data export helpers (Excel / PDF formatting)
```

### Architectural Highlights

1. **Repository-Service Pattern**:
   - Routers in `src/main.py` handle inputs and outputs.
   - Services in `src/services/` execute core business rules and transaction boundaries.
   - Repositories in `src/repositories/` query the database via SQLAlchemy sessions.
2. **Asynchronous S3 Storage integration**:
   - Built on `aiobotocore` for completely non-blocking async file storage requests.
   - Switchable via `STORAGE_PROVIDER` (either `local` or `s3`).
   - Supports local simulation (LocalStack) and cloud environments (real AWS S3 buckets) through environment variables.
3. **Refresh Token Rotation**:
   - Protects credentials by generating an HttpOnly refresh cookie.
   - Session tokens rotate on every usage. Reusing an old refresh token immediately invalidates the user's active session.
4. **Structured JSON Logs with Correlation IDs**:
   - Request-scoped middleware checks or generates `X-Correlation-ID` values.
   - Correlated logs allow developers to trace request lifecycles across concurrent operations.
5. **Rate Limiting Protection**:
   - Integrates Redis for reliable state management and SlowAPI for request throttling.

---

## Environment Configuration

Adjust backend configuration variables by editing `backend/.env` (or via docker-compose environment blocks). Key variables include:

| Variable | Description | Default / Dev Value |
|---|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string | `postgresql+asyncpg://postgres:postgrespassword@db:5432/todosphere` |
| `REDIS_URL` | Redis endpoint | `redis://redis:6379/0` |
| `STORAGE_PROVIDER` | Active file persistence driver (`local` or `s3`) | `local` |
| `UPLOAD_DIR` | Filesystem destination for local storage | `/app/uploads` |
| `S3_BUCKET_NAME` | Target S3 bucket for uploads | `todosphere-attachments` |
| `S3_ACCESS_KEY` | AWS / LocalStack Access Key ID | `minio_dev_access_key` |
| `S3_SECRET_KEY` | AWS / LocalStack Secret Access Key | `minio_dev_secret_key` |
| `S3_ENDPOINT_URL` | Endpoint for LocalStack S3 simulation (blank for real AWS) | `http://localhost:4566` |

---

## Local Setup

Ensure you have [uv](https://github.com/astral-sh/uv) installed on your system.

### 1. Initialize Virtual Environment & Dependencies
Create a virtual environment, activate it, and install dependencies:
```powershell
uv venv
.venv\Scripts\Activate.ps1
uv sync
```

### 2. Configure Environment Variables
Copy `.env.example` from the project root into `backend/.env` and adjust the settings:
```bash
cp ../.env.example .env
```

### 3. Database Migrations
Apply alembic database migrations to bootstrap your local PostgreSQL instance:
```bash
alembic upgrade head
```

### 4. Seed Mock Data
Seed the local database with demo tasks and a test user (`demo_user` / `Password123!`):
```bash
uv run python -B scripts/seed.py
```

### 5. Start the API Server
Start the development server:
```bash
uv run python -B -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## Development Checks & Tests

Execute quality checks and tests locally within the virtual environment:

### Ruff (Linting & Formatting)
```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```
To auto-fix style violations:
```bash
uv run ruff check --fix src/ tests/
uv run ruff format src/ tests/
```

### MyPy (Static Type Checking)
```bash
uv run mypy -p src
```

### Bandit (Security Analysis)
```bash
uv run bandit -c pyproject.toml -r src/
```

### Pip-Audit (Dependency Vulnerabilities)
```bash
uv run pip-audit
```

### Pytest (Backend Test Suites)
Make sure PostgreSQL, Redis, and LocalStack are running (or run `docker compose -f docker-compose.test.yml up -d` to spin up the entire test suite dependencies), then execute:
```bash
uv run python -B -m pytest tests/ -v
```

---

## Connection to the Main Ecosystem

This backend service is part of the larger TodoSphere application. For detailed details on running the full stack with Docker Compose or automation scripts:
- Refer to the main [README.md](../README.md).
