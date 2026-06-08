import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import InvalidCredentialsException, InvalidTokenException
from src.services.auth import AuthService


@pytest.mark.asyncio
async def test_auth_service_token_rotation_and_reuse(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    await auth_service.register_user(
        username="token_rotation_u", password="Password123!"
    )

    # Login to get refresh token
    _, refresh_token_1, _ = await auth_service.login_user(
        username="token_rotation_u",
        password="Password123!",
        ip_address="127.0.0.1",
        user_agent="Rotation Test",
    )

    # 1. Successful rotation
    access_token_rot, refresh_token_2 = await auth_service.refresh_session(
        refresh_token=refresh_token_1,
        ip_address="127.0.0.1",
        user_agent="Rotation Test",
    )
    assert access_token_rot is not None
    assert refresh_token_2 is not None

    # 2. Attempt token reuse (refresh_token_1 should be marked revoked, and revoke all sessions)
    with pytest.raises(InvalidTokenException):
        await auth_service.refresh_session(
            refresh_token=refresh_token_1,
            ip_address="127.0.0.1",
            user_agent="Rotation Test",
        )

    # 3. Verify that refresh_token_2 is also revoked now because of the reuse trigger
    with pytest.raises(InvalidTokenException):
        await auth_service.refresh_session(
            refresh_token=refresh_token_2,
            ip_address="127.0.0.1",
            user_agent="Rotation Test",
        )


@pytest.mark.asyncio
async def test_auth_service_login_non_existent_user(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    with pytest.raises(InvalidCredentialsException):
        await auth_service.login_user(
            username="non_existent_user",
            password="Password123!",
            ip_address="127.0.0.1",
            user_agent="Login Test",
        )


@pytest.mark.asyncio
async def test_auth_service_invalid_refresh_token(db_session: AsyncSession):
    auth_service = AuthService(db_session)
    with pytest.raises(InvalidTokenException):
        await auth_service.refresh_session(
            refresh_token="invalid_refresh_token_format",
            ip_address="127.0.0.1",
            user_agent="Rotation Test",
        )
