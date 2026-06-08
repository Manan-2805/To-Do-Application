import datetime
import uuid
from typing import Any

import jwt
from pwdlib import PasswordHash

from src.core.config import settings


password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash password using the recommended Argon2id algorithm."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against its Argon2id hash."""
    return password_hash.verify(password, hashed_password)


def create_access_token(
    subject: str, expires_delta: datetime.timedelta | None = None
) -> str:
    """Generate JWT Access Token."""
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(
        to_encode, settings.JWT_ACCESS_SECRET, algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(
    subject: str, expires_delta: datetime.timedelta | None = None
) -> str:
    """Generate JWT Refresh Token with unique JTI to prevent hash collisions."""
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(
        to_encode, settings.JWT_REFRESH_SECRET, algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str, secret: str) -> dict[str, Any]:
    """Decode JWT token using specific secret, raising exception if invalid."""
    return jwt.decode(token, secret, algorithms=[settings.JWT_ALGORITHM])
