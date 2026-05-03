import re
from datetime import UTC, datetime
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.client_settings import ClientSettings
from app.models.enums import (
    NotificationChannel,
    SubscriptionStatus,
    SubscriptionTier,
    UserRole,
)
from app.models.notification_preference import NotificationPreference
from app.models.subscription import Subscription
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security.auth import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

_TIER_QUOTAS = {
    SubscriptionTier.starter: 10,
    SubscriptionTier.pro: 50,
    SubscriptionTier.business: 1_000_000,
}


def _slug_from_business_name(name: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return base or "client"


class AuthError(HTTPException):
    def __init__(self, detail: str, code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(status_code=code, detail=detail)


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)

    async def signup(self, *, email: str, password: str, business_name: str) -> User:
        if await self.users.get_by_email(email):
            raise AuthError("Email already registered", code=status.HTTP_409_CONFLICT)

        client = Client(business_name=business_name, slug=_slug_from_business_name(business_name))
        self.session.add(client)
        await self.session.flush()

        # Try to ensure unique slug — append short uuid suffix if collision
        try:
            await self.session.flush()
        except IntegrityError:
            await self.session.rollback()
            client.slug = f"{client.slug}-{str(client.id)[:8]}"
            self.session.add(client)
            await self.session.flush()

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=UserRole.client,
            client_id=client.id,
        )
        self.session.add(user)

        self.session.add(
            Subscription(
                client_id=client.id,
                tier=SubscriptionTier.starter,
                status=SubscriptionStatus.trial,
                monthly_response_quota=_TIER_QUOTAS[SubscriptionTier.starter],
            )
        )
        self.session.add(ClientSettings(client_id=client.id))
        self.session.add(
            NotificationPreference(
                client_id=client.id,
                primary_channel=NotificationChannel.email,
                email_address=email,
            )
        )
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def login(self, *, email: str, password: str) -> tuple[User, str, str]:
        user = await self.users.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Invalid credentials", code=status.HTTP_401_UNAUTHORIZED)
        user.last_login_at = datetime.now(UTC)
        await self.session.commit()
        access = create_access_token(user.id, role=user.role.value)
        refresh = create_refresh_token(user.id)
        return user, access, refresh

    async def refresh(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except jwt.PyJWTError as exc:
            raise AuthError("Invalid token", code=status.HTTP_401_UNAUTHORIZED) from exc
        if payload.get("type") != "refresh":
            raise AuthError("Wrong token type", code=status.HTTP_401_UNAUTHORIZED)
        user_id = UUID(payload["sub"])
        user = await self.users.get(user_id)
        if user is None or user.deleted_at is not None:
            raise AuthError("User not found", code=status.HTTP_401_UNAUTHORIZED)
        return create_access_token(user.id, role=user.role.value)

    async def issue_email_verification(self, user_id: UUID) -> str:
        return create_email_verification_token(user_id)

    async def verify_email(self, token: str) -> User:
        try:
            payload = decode_token(token)
        except jwt.PyJWTError as exc:
            raise AuthError("Invalid token") from exc
        if payload.get("type") != "email_verify":
            raise AuthError("Wrong token type")
        user = await self.users.get(UUID(payload["sub"]))
        if user is None:
            raise AuthError("User not found", code=status.HTTP_404_NOT_FOUND)
        user.email_verified_at = datetime.now(UTC)
        await self.session.commit()
        return user

    async def request_password_reset(self, email: str) -> str | None:
        user = await self.users.get_by_email(email)
        if user is None:
            return None
        return create_password_reset_token(user.id)

    async def reset_password(self, token: str, new_password: str) -> User:
        try:
            payload = decode_token(token)
        except jwt.PyJWTError as exc:
            raise AuthError("Invalid token") from exc
        if payload.get("type") != "password_reset":
            raise AuthError("Wrong token type")
        user = await self.users.get(UUID(payload["sub"]))
        if user is None:
            raise AuthError("User not found", code=status.HTTP_404_NOT_FOUND)
        user.password_hash = hash_password(new_password)
        await self.session.commit()
        return user
