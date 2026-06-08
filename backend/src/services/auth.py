import datetime
import hashlib
import uuid

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import (
    DuplicateEntityException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
)
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password_async,
    verify_password_async,
)
from src.models.refresh_token import RefreshToken
from src.models.user import User
from src.repositories.refresh_token import RefreshTokenRepository
from src.repositories.user import UserRepository
from src.services.audit import AuditService


class AuthService:
    """Service layer managing user lifecycle, session creation, rotation and revocation."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_repo = RefreshTokenRepository(session)
        self.audit_service = AuditService(session)

    def _hash_token(self, token: str) -> str:
        """Hash token using SHA256 for secure database storage and indexing."""
        return hashlib.sha256(token.encode()).hexdigest()

    async def register_user(self, username: str, password: str) -> User:
        """Register a new user, hashing their password with Argon2id."""
        # Check duplicate
        existing = await self.user_repo.get_by_username(username)
        if existing:
            raise DuplicateEntityException(f"Username '{username}' is already taken.")

        hashed = await hash_password_async(password)
        new_user = User(username=username, hashed_password=hashed)

        await self.user_repo.create(new_user)

        # Log Audit
        await self.audit_service.log_action(
            user_id=new_user.id,
            action="signup",
            entity_type="user",
            entity_id=str(new_user.id),
            metadata={"username": username},
        )

        await self.session.commit()
        return new_user

    async def login_user(
        self, username: str, password: str, ip_address: str, user_agent: str
    ) -> tuple[str, str, User]:
        """Authenticate user, create access/refresh JWT tokens, and store session."""
        user = await self.user_repo.get_by_username(username)
        if not user or not await verify_password_async(password, user.hashed_password):
            raise InvalidCredentialsException()

        # Generate tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))

        # Hash and store refresh token
        token_hash = self._hash_token(refresh_token)
        expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        rt_entity = RefreshToken(
            user_id=user.id, token_hash=token_hash, expires_at=expires_at
        )
        await self.token_repo.create(rt_entity)

        # Log Audit
        await self.audit_service.log_action(
            user_id=user.id,
            action="login",
            entity_type="user",
            entity_id=str(user.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.session.commit()
        return access_token, refresh_token, user

    async def refresh_session(
        self, refresh_token: str, ip_address: str, user_agent: str
    ) -> tuple[str, str]:
        """Rotate refresh token and return new access/refresh pairs."""
        try:
            payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET)
            if payload.get("type") != "refresh":
                raise InvalidTokenException("Invalid token type")
        except jwt.ExpiredSignatureError:
            raise TokenExpiredException("Refresh token expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenException("Invalid refresh token")

        user_id = uuid.UUID(payload["sub"])
        token_hash = self._hash_token(refresh_token)

        # Find token in database
        stored_token = await self.token_repo.get_by_hash(token_hash)
        if not stored_token or stored_token.revoked_at is not None:
            # Refresh token reuse detection: revoke all sessions for safety
            await self.token_repo.revoke_all_for_user(user_id)
            await self.session.commit()
            raise InvalidTokenException("Refresh token was revoked or invalid")

        if stored_token.expires_at.replace(tzinfo=datetime.UTC) < datetime.datetime.now(
            datetime.UTC
        ):
            raise TokenExpiredException("Refresh token expired")

        # Revoke old token
        stored_token.revoked_at = datetime.datetime.now(datetime.UTC)

        # Generate new tokens (rotation)
        new_access_token = create_access_token(subject=str(user_id))
        new_refresh_token = create_refresh_token(subject=str(user_id))

        # Store new token
        new_token_hash = self._hash_token(new_refresh_token)
        new_expires_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        new_rt = RefreshToken(
            user_id=user_id, token_hash=new_token_hash, expires_at=new_expires_at
        )
        await self.token_repo.create(new_rt)

        # Log Audit
        await self.audit_service.log_action(
            user_id=user_id,
            action="refresh",
            entity_type="session",
            entity_id=str(stored_token.id),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        await self.session.commit()
        return new_access_token, new_refresh_token

    async def logout_user(self, refresh_token: str) -> None:
        """Revoke the current refresh token session on logout."""
        try:
            payload = decode_token(refresh_token, settings.JWT_REFRESH_SECRET)
            user_id = uuid.UUID(payload["sub"])
        except Exception:
            return  # Fail silently on logout token decoding

        token_hash = self._hash_token(refresh_token)
        stored_token = await self.token_repo.get_by_hash(token_hash)

        if stored_token:
            stored_token.revoked_at = datetime.datetime.now(datetime.UTC)
            await self.audit_service.log_action(
                user_id=user_id,
                action="logout",
                entity_type="session",
                entity_id=str(stored_token.id),
            )
            await self.session.commit()
