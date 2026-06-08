import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import DuplicateEntityException, InvalidCredentialsException
from src.services.auth import AuthService


@pytest.mark.asyncio
async def test_auth_service_signup_success(db_session: AsyncSession):
    """Test successful user registration flow."""
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(
        username="unit_test_user", password="Password123!"
    )

    assert user.id is not None
    assert user.username == "unit_test_user"


@pytest.mark.asyncio
async def test_auth_service_signup_duplicate(db_session: AsyncSession):
    """Test registration block on duplicate usernames."""
    auth_service = AuthService(db_session)
    await auth_service.register_user(username="unit_test_dup", password="Password123!")

    with pytest.raises(DuplicateEntityException):
        await auth_service.register_user(
            username="unit_test_dup", password="DifferentPassword123!"
        )


@pytest.mark.asyncio
async def test_auth_service_login_success(db_session: AsyncSession):
    """Test successful login returns valid tokens and session registration."""
    auth_service = AuthService(db_session)
    user = await auth_service.register_user(
        username="unit_test_login", password="Password123!"
    )

    access_token, refresh_token, logged_in_user = await auth_service.login_user(
        username="unit_test_login",
        password="Password123!",
        ip_address="127.0.0.1",
        user_agent="Unit Test Client",
    )

    assert access_token is not None
    assert refresh_token is not None
    assert logged_in_user.id == user.id


@pytest.mark.asyncio
async def test_auth_service_login_invalid_credentials(db_session: AsyncSession):
    """Test login rejection on incorrect password."""
    auth_service = AuthService(db_session)
    await auth_service.register_user(username="unit_test_fail", password="Password123!")

    with pytest.raises(InvalidCredentialsException):
        await auth_service.login_user(
            username="unit_test_fail",
            password="WrongPassword123!",
            ip_address="127.0.0.1",
            user_agent="Unit Test Client",
        )
