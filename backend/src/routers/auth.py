from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging_conf import correlation_id_ctx
from src.core.rate_limit import limiter
from src.dependencies.auth import get_current_user
from src.dependencies.database import get_db_session
from src.models.user import User
from src.schemas.response import APIResponse
from src.schemas.user import (
    TokenResponse,
    UserLoginRequest,
    UserResponse,
    UserSignUpRequest,
)
from src.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=APIResponse[UserResponse], status_code=201)
@limiter.limit("5/minute")
async def signup(
    request: Request,  # noqa: ARG001
    payload: UserSignUpRequest,
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[UserResponse]:
    """Register a new user profile with credentials validation."""
    auth_service = AuthService(db)
    user = await auth_service.register_user(
        username=payload.username, password=payload.password
    )

    # Map to schema response
    user_data = UserResponse.model_validate(user)

    return APIResponse(
        success=True,
        data=user_data,
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )


@router.post("/login", response_model=APIResponse[UserResponse])
@limiter.limit("10/minute")
async def login(
    request: Request,
    response: Response,
    payload: UserLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[UserResponse]:
    """Authenticate credentials and issue session tokens via HttpOnly cookies."""
    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    access_token, refresh_token, user = await auth_service.login_user(
        username=payload.username,
        password=payload.password,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    # Store in HttpOnly Cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to False for local HTTP container dev
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    user_data = UserResponse.model_validate(user)

    return APIResponse(
        success=True,
        data=user_data,
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh(
    request: Request, response: Response, db: AsyncSession = Depends(get_db_session)
) -> APIResponse[TokenResponse] | Response:
    """Rotate JWT session tokens using the HttpOnly refresh cookie."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        # Clear cookies if refresh fails or is absent
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        return Response(status_code=401)

    auth_service = AuthService(db)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    try:
        new_access_token, new_refresh_token = await auth_service.refresh_session(
            refresh_token=refresh_token, ip_address=client_ip, user_agent=user_agent
        )
    except Exception as e:
        response.delete_cookie(key="access_token", path="/")
        response.delete_cookie(key="refresh_token", path="/")
        raise e

    # Update Cookies
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return APIResponse(
        success=True,
        data=TokenResponse(message="Tokens rotated successfully"),
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )


@router.post("/logout", response_model=APIResponse[TokenResponse])
async def logout(
    request: Request, response: Response, db: AsyncSession = Depends(get_db_session)
) -> APIResponse[TokenResponse]:
    """Revoke the database refresh token and clear user session cookies."""
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        auth_service = AuthService(db)
        await auth_service.logout_user(refresh_token)

    # Clear cookies
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")

    return APIResponse(
        success=True,
        data=TokenResponse(message="Logged out successfully"),
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserResponse]:
    """Retrieve profile data for the authenticated user session."""
    user_data = UserResponse.model_validate(current_user)
    return APIResponse(
        success=True,
        data=user_data,
        error=None,
        correlation_id=correlation_id_ctx.get(),
    )
