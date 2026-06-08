import contextvars
import json
import logging
import sys


correlation_id_ctx = contextvars.ContextVar("correlation_id", default="")
user_id_ctx = contextvars.ContextVar("user_id", default="")


class StructuredJSONFormatter(logging.Formatter):
    """Custom logging formatter that outputs logs as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "correlation_id": correlation_id_ctx.get() or "",
            "user_id": user_id_ctx.get() or "",
        }

        # Include extra attributes if passed in extra dictionary
        if hasattr(record, "extra_fields"):
            log_record.update(record.extra_fields)

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def configure_logging():
    """Configure structured logging for the application."""
    root_logger = logging.getLogger()

    # Clear existing handlers
    root_logger.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    formatter = StructuredJSONFormatter()
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Suppress verbose library logs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
