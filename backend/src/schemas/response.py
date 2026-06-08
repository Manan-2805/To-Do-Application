from typing import Any, Generic, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Detailed error object returned on request failures."""

    code: str
    message: str
    details: Any | None = None


class APIResponse(BaseModel, Generic[T]):
    """Standard generic wrapper returned by all API endpoints."""

    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    correlation_id: str
