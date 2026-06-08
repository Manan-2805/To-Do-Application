import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from src.core.logging_conf import correlation_id_ctx, user_id_ctx


logger = logging.getLogger("todosphere.middleware")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Middleware to inject correlation IDs into the request and contextvars."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        corr_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

        # Set context variable for logs
        correlation_token = correlation_id_ctx.set(corr_id)

        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = corr_id
            return response
        finally:
            correlation_id_ctx.reset(correlation_token)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to inject standard security hardening headers."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; frame-ancestors 'none'"
        )
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log details about every HTTP request with duration."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()

        # Reset user ID context var for the new request thread
        user_token = user_id_ctx.set("")

        try:
            response = await call_next(request)
            duration = (time.perf_counter() - start_time) * 1000

            # Log structured data
            logger.info(
                f"HTTP {request.method} {request.url.path} finished with status {response.status_code}",
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": round(duration, 2),
                        "client_ip": request.client.host
                        if request.client
                        else "unknown",
                    }
                },
            )
            return response
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"HTTP {request.method} {request.url.path} failed: {e!s}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": round(duration, 2),
                        "client_ip": request.client.host
                        if request.client
                        else "unknown",
                    }
                },
            )
            raise e
        finally:
            user_id_ctx.reset(user_token)
