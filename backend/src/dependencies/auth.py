import uuid

from fastapi import Depends, Request
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import InvalidTokenException, TokenExpiredException
from src.core.logging_conf import user_id_ctx
from src.core.security import decode_token
from src.dependencies.database import get_db_session
from src.models.user import User
from src.repositories.user import UserRepository


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db_session)
) -> User:
    """Dependency looking up active session user via cookies."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise InvalidTokenException("Access token missing from cookies.")

    try:
        payload = decode_token(access_token, settings.JWT_ACCESS_SECRET)
        if payload.get("type") != "access":
            raise InvalidTokenException("Invalid token type.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenException("Token subject payload missing.")

        user_id = uuid.UUID(user_id_str)
    except ExpiredSignatureError:
        raise TokenExpiredException("Access token has expired.")
    except (InvalidTokenError, ValueError):
        raise InvalidTokenException("Invalid access token.")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise InvalidTokenException("User associated with token does not exist.")

    # Bind User ID to log context
    user_id_ctx.set(str(user.id))

    return user
