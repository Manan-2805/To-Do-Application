import asyncio
import datetime
import os
from typing import Any
import uuid

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from src.core.config import settings


_hasher: PasswordHash | None = None
_test_hasher: PasswordHash | None = None


def get_password_hasher() -> PasswordHash:
    """Get the password hasher instance, dynamically optimized for performance testing if enabled."""
    global _hasher, _test_hasher
    is_perf = os.getenv("PERFORMANCE_TEST") == "true" or os.getenv("TESTING") == "true"
    if is_perf:
        if _test_hasher is None:
            _test_hasher = PasswordHash([Argon2Hasher(time_cost=1, memory_cost=512, parallelism=2)])
        return _test_hasher

    if _hasher is None:
        _hasher = PasswordHash.recommended()
    return _hasher


def hash_password(password: str) -> str:
    """Hash password using the recommended Argon2id algorithm."""
    return get_password_hasher().hash(password)


async def hash_password_async(password: str) -> str:
    """Hash password asynchronously using a worker thread."""
    return await asyncio.to_thread(get_password_hasher().hash, password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against its Argon2id hash."""
    return get_password_hasher().verify(password, hashed_password)


async def verify_password_async(password: str, hashed_password: str) -> bool:
    """Verify password asynchronously against its Argon2id hash using a worker thread."""
    return await asyncio.to_thread(get_password_hasher().verify, password, hashed_password)


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
