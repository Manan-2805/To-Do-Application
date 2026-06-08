import asyncio
import contextlib
import logging
import os

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from src.core.config import settings
from src.core.exceptions import TodoSphereException
from src.core.logging_conf import configure_logging, correlation_id_ctx
from src.core.middleware import (
    CorrelationIdMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)
from src.core.rate_limit import limiter
from src.routers.audit import router as audit_router
from src.routers.auth import router as auth_router
from src.routers.health import router as health_router
from src.routers.tasks import router as tasks_router
from src.services.scheduler import run_scheduler


# Configure structured logger
configure_logging()
logger = logging.getLogger("todosphere.main")


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager starting and stopping background tasks."""
    if os.getenv("TESTING") == "True":
        yield
        return
    scheduler_task = asyncio.create_task(run_scheduler(interval_seconds=60))
    yield
    scheduler_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await scheduler_task


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# SlowAPI setup
app.state.limiter = limiter

# Standard CORS Middleware (environment-driven)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middlewares
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIdMiddleware)


# Exception Handlers
@app.exception_handler(TodoSphereException)
async def todosphere_exception_handler(
    request: Request, exc: TodoSphereException
) -> JSONResponse:
    """Handle custom application exceptions and format using API envelope."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {"code": exc.code, "message": exc.message, "details": exc.details},
            "correlation_id": correlation_id_ctx.get() or "",
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic input validation exceptions and return formatted field error details."""
    errors = []
    for error in exc.errors():
        loc = " -> ".join(str(item) for item in error.get("loc", []))

        msg = error.get("msg", "Validation failed")
        errors.append({"field": loc, "issue": msg})

    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed.",
                "details": errors,
            },
            "correlation_id": correlation_id_ctx.get() or "",
        },
    )


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Handle SlowAPI rate limits and return standardized error response envelope."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "TOO_MANY_REQUESTS",
                "message": "Rate limit exceeded. Please slow down your requests.",
            },
            "correlation_id": correlation_id_ctx.get() or "",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback catch-all handler for unhandled exceptions."""
    logger.exception(f"Unhandled server error: {exc!s}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred.",
            },
            "correlation_id": correlation_id_ctx.get() or "",
        },
    )


# Mount Routers
# Health endpoints mounted at root for Kubernetes / Orchestrator simplicity
app.include_router(health_router)

# Versioned API routes
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(tasks_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
