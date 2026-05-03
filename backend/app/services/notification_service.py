from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.resend.client import ResendClient, ResendError
from app.integrations.telegram.client import TelegramClient, TelegramError
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.notification import Notification
from app.repositories.notification_repository import (
    NotificationPreferenceRepository,
    NotificationRepository,
)
from app.services.notification_templates import render

# Events that bypass digest mode (always sent immediately).
IMMEDIATE_EVENT_TYPES = {
    "oauth_revoked",
    "publish_failed",
    "quota_exhausted",
    "publish_succeeded",
}


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
        resend: ResendClient | None = None,
        telegram: TelegramClient | None = None,
    ) -> None:
        self.session = session
        self.resend = resend or ResendClient()
        self.telegram = telegram or TelegramClient()
        self.prefs = NotificationPreferenceRepository(session)
        self.notifications = NotificationRepository(session)

    async def dispatch(
        self,
        *,
        event_type: str,
        client_id: UUID,
        payload: dict[str, Any],
        related_review_id: UUID | None = None,
        related_response_id: UUID | None = None,
    ) -> Notification:
        pref = await self.prefs.get_by_client(client_id)
        from app.repositories.client_settings_repository import ClientSettingsRepository

        settings_repo = ClientSettingsRepository(self.session)
        settings = await settings_repo.get_by_client(client_id)

        channel = pref.primary_channel if pref else NotificationChannel.email
        immediate = event_type in IMMEDIATE_EVENT_TYPES or not (settings and settings.digest_mode)

        notification = Notification(
            client_id=client_id,
            event_type=event_type,
            channel=channel,
            template_code=event_type,
            payload=payload,
            status=NotificationStatus.pending if immediate else NotificationStatus.deferred,
            related_review_id=related_review_id,
            related_response_id=related_response_id,
        )
        self.session.add(notification)
        await self.session.flush()

        if immediate:
            await self._send(notification, pref, payload)

        await self.session.commit()
        return notification

    async def _send(
        self,
        notification: Notification,
        pref: object,
        payload: dict[str, Any],
    ) -> None:
        subject, html, text = render(notification.event_type, payload)
        try:
            if notification.channel == NotificationChannel.telegram and pref is not None:
                chat_id = getattr(pref, "telegram_chat_id", None)
                if chat_id:
                    await self.telegram.send_message(chat_id=chat_id, text=text)
                    notification.status = NotificationStatus.sent
                    notification.sent_at = datetime.now(UTC)
                    return
                # Fallback to email if telegram not configured.
                notification.channel = NotificationChannel.email
            if notification.channel == NotificationChannel.email and pref is not None:
                to = getattr(pref, "email_address", None)
                if to:
                    await self.resend.send_email(to=to, subject=subject, html=html, text=text)
                    notification.status = NotificationStatus.sent
                    notification.sent_at = datetime.now(UTC)
                    return
            notification.status = NotificationStatus.failed
            notification.error = "No deliverable channel"
        except (ResendError, TelegramError) as exc:
            logger.warning("Notification {id} failed: {err}", id=notification.id, err=exc)
            notification.status = NotificationStatus.failed
            notification.failed_at = datetime.now(UTC)
            notification.error = str(exc)[:500]
            notification.attempts = (notification.attempts or 0) + 1
