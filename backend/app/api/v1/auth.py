from typing import Annotated

from fastapi import APIRouter, Cookie, HTTPException, Response, status
from loguru import logger

from app.config import get_settings
from app.database import SessionDep
from app.schemas.auth import (
    EmailVerify,
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    SignupRequest,
    TokenPair,
    UserPublic,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        httponly=True,
        secure=settings.environment != "development",
        samesite="lax",
        max_age=settings.jwt_refresh_ttl_days * 86400,
        path="/api/v1/auth",
    )


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, session: SessionDep) -> UserPublic:
    service = AuthService(session)
    user = await service.signup(
        email=payload.email,
        password=payload.password,
        business_name=payload.business_name,
    )
    verification_token = await service.issue_email_verification(user.id)
    if get_settings().environment == "development":
        logger.info("Email verification token (dev): {t}", t=verification_token)
    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, session: SessionDep, response: Response) -> TokenPair:
    service = AuthService(session)
    _, access, refresh = await service.login(email=payload.email, password=payload.password)
    _set_refresh_cookie(response, refresh)
    return TokenPair(access_token=access)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    session: SessionDep,
    refresh_token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE)] = None,
) -> TokenPair:
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    access = await AuthService(session).refresh(refresh_token)
    return TokenPair(access_token=access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path="/api/v1/auth")


@router.post("/verify-email", response_model=UserPublic)
async def verify_email(payload: EmailVerify, session: SessionDep) -> UserPublic:
    user = await AuthService(session).verify_email(payload.token)
    return UserPublic.model_validate(user)


@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
async def password_reset_request(payload: PasswordResetRequest, session: SessionDep) -> None:
    token = await AuthService(session).request_password_reset(payload.email)
    if token and get_settings().environment == "development":
        logger.info("Password reset token (dev): {t}", t=token)


@router.post("/password-reset/confirm", response_model=UserPublic)
async def password_reset_confirm(payload: PasswordResetConfirm, session: SessionDep) -> UserPublic:
    user = await AuthService(session).reset_password(payload.token, payload.password)
    return UserPublic.model_validate(user)
