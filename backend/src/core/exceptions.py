from typing import Any


class TodoSphereException(Exception):
    """Base application exception for TodoSphere."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        status_code: int = 500,
        details: Any | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class InvalidCredentialsException(TodoSphereException):
    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(message=message, code="UNAUTHORIZED", status_code=401)


class TokenExpiredException(TodoSphereException):
    def __init__(self, message: str = "Session has expired"):
        super().__init__(message=message, code="TOKEN_EXPIRED", status_code=401)


class InvalidTokenException(TodoSphereException):
    def __init__(self, message: str = "Invalid or tampered token"):
        super().__init__(message=message, code="INVALID_TOKEN", status_code=401)


class EntityNotFoundException(TodoSphereException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, code="NOT_FOUND", status_code=404)


class ForbiddenActionException(TodoSphereException):
    def __init__(self, message: str = "Action forbidden for current user"):
        super().__init__(message=message, code="FORBIDDEN", status_code=403)


class DuplicateEntityException(TodoSphereException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, code="CONFLICT", status_code=409)


class BadRequestException(TodoSphereException):
    def __init__(self, message: str, details: Any | None = None):
        super().__init__(
            message=message, code="BAD_REQUEST", status_code=400, details=details
        )


class StorageException(TodoSphereException):
    def __init__(self, message: str):
        super().__init__(message=message, code="STORAGE_ERROR", status_code=500)
