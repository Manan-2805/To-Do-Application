import time
import uuid
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import InvalidTokenException, TokenExpiredException
from src.core.security import create_access_token
from src.dependencies.auth import get_current_user


@pytest.mark.asyncio
async def test_get_current_user_no_token():
    """Test get_current_user raises exception when access token is missing."""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {}

    with pytest.raises(InvalidTokenException) as exc:
        await get_current_user(mock_request, db=AsyncMock())
    assert "Access token missing" in str(exc.value)


@pytest.mark.asyncio
async def test_get_current_user_invalid_type():
    """Test get_current_user raises exception when token is not type access."""
    token = jwt.encode(
        {"type": "refresh", "sub": "user_id"},
        settings.JWT_ACCESS_SECRET,
        algorithm="HS256",
    )

    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"access_token": token}

    with pytest.raises(InvalidTokenException) as exc:
        await get_current_user(mock_request, db=AsyncMock())
    assert "Invalid token type" in str(exc.value)


@pytest.mark.asyncio
async def test_get_current_user_missing_sub():
    """Test get_current_user raises exception when subject is missing."""
    token = jwt.encode(
        {"type": "access"}, settings.JWT_ACCESS_SECRET, algorithm="HS256"
    )

    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"access_token": token}

    with pytest.raises(InvalidTokenException) as exc:
        await get_current_user(mock_request, db=AsyncMock())
    assert "Token subject payload missing" in str(exc.value)


@pytest.mark.asyncio
async def test_get_current_user_expired():
    """Test get_current_user raises exception when token expiration time is in the past."""
    token = jwt.encode(
        {"type": "access", "sub": str(uuid.uuid4()), "exp": time.time() - 100},
        settings.JWT_ACCESS_SECRET,
        algorithm="HS256",
    )

    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"access_token": token}

    with pytest.raises(TokenExpiredException):
        await get_current_user(mock_request, db=AsyncMock())


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test get_current_user raises exception for malformed JWT token string."""
    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"access_token": "invalid.jwt.token"}

    with pytest.raises(InvalidTokenException) as exc:
        await get_current_user(mock_request, db=AsyncMock())
    assert "Invalid access token" in str(exc.value)


@pytest.mark.asyncio
async def test_get_current_user_non_existent_user(db_session: AsyncSession):
    """Test get_current_user raises exception when user is not found in database."""
    token = create_access_token(subject=str(uuid.uuid4()))

    mock_request = MagicMock(spec=Request)
    mock_request.cookies = {"access_token": token}

    with pytest.raises(InvalidTokenException) as exc:
        await get_current_user(mock_request, db=db_session)
    assert "User associated with token does not exist" in str(exc.value)
