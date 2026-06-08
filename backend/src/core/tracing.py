import logging
from collections.abc import Callable
from types import TracebackType
from typing import Any, Literal


logger = logging.getLogger("todosphere.tracing")


class Tracer:
    """Scaffolding class for future OpenTelemetry integration."""

    def __init__(self, service_name: str = "todosphere-api") -> None:
        self.service_name = service_name
        logger.info(f"Initialized tracer scaffolding for service: {service_name}")

    def start_span(
        self, name: str, attributes: dict[str, Any] | None = None
    ) -> "SpanContext":
        """Mock span generator."""
        return SpanContext(name, attributes)


class SpanContext:
    """Mock context manager representing a trace span."""

    def __init__(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.name = name
        self.attributes = attributes or {}

    def __enter__(self) -> "SpanContext":
        logger.debug(
            f"[Trace Span Start] {self.name} with attributes {self.attributes}"
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        if exc_type:
            logger.debug(f"[Trace Span End - Error] {self.name} failed: {exc_val}")
        else:
            logger.debug(f"[Trace Span End - Success] {self.name}")
        return False  # Do not suppress exception


tracer = Tracer()


def trace_span(
    span_name: str, attributes: dict[str, Any] | None = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to trace a function call using mock span context."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        import functools

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            span_attrs = attributes or {}
            span_attrs.update({"function_name": func.__name__})
            with SpanContext(span_name, attributes=span_attrs):
                return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            span_attrs = attributes or {}
            span_attrs.update({"function_name": func.__name__})
            with SpanContext(span_name, attributes=span_attrs):
                return await func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
