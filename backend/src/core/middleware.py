import logging
import time
import uuid

from src.core.logging_conf import correlation_id_ctx, user_id_ctx


logger = logging.getLogger("todosphere.middleware")


class ConsolidatedMiddleware:
    """Consolidated raw ASGI middleware handling Correlation ID, Security Headers, and Request Logging in a single layer."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.perf_counter()

        # Extract or generate correlation ID
        headers_dict = dict(scope.get("headers", []))
        corr_id_bytes = headers_dict.get(b"x-correlation-id")
        corr_id = corr_id_bytes.decode("utf-8") if corr_id_bytes else str(uuid.uuid4())

        # Set context variables
        correlation_token = correlation_id_ctx.set(corr_id)
        user_token = user_id_ctx.set("")

        status_code = [500]  # default fallback if not intercepted

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message.get("status", 200)
                headers_list = message.setdefault("headers", [])

                # Consolidate header injections
                security_headers = [
                    (b"x-correlation-id", corr_id.encode("utf-8")),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (b"content-security-policy", b"default-src 'self'; frame-ancestors 'none'")
                ]

                for name, value in security_headers:
                    if not any(h[0].lower() == name for h in headers_list):
                        headers_list.append((name, value))

            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            duration = (time.perf_counter() - start_time) * 1000

            method = scope.get("method", "")
            path = scope.get("path", "")
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"

            logger.info(
                f"HTTP {method} {path} finished with status {status_code[0]}",
                extra={
                    "extra_fields": {
                        "method": method,
                        "path": path,
                        "status_code": status_code[0],
                        "duration_ms": round(duration, 2),
                        "client_ip": client_ip,
                    }
                },
            )
        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000
            method = scope.get("method", "")
            path = scope.get("path", "")
            client = scope.get("client")
            client_ip = client[0] if client else "unknown"

            logger.error(
                f"HTTP {method} {path} failed: {e!s}",
                exc_info=True,
                extra={
                    "extra_fields": {
                        "method": method,
                        "path": path,
                        "duration_ms": round(duration, 2),
                        "client_ip": client_ip,
                    }
                },
            )
            raise e
        finally:
            correlation_id_ctx.reset(correlation_token)
            user_id_ctx.reset(user_token)
