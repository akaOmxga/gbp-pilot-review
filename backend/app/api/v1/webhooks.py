from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request, status
from loguru import logger

from app.database import SessionDep
from app.integrations.lemonsqueezy.webhooks import verify_signature
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/lemonsqueezy", status_code=status.HTTP_200_OK)
async def lemonsqueezy_webhook(
    request: Request,
    session: SessionDep,
    x_signature: Annotated[str | None, Header(alias="X-Signature")] = None,
) -> dict[str, str]:
    raw_body = await request.body()
    if not verify_signature(raw_body, x_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad signature")
    payload = await request.json()
    meta = payload.get("meta", {})
    event_id = meta.get("event_id") or meta.get("webhook_id")
    event_type = meta.get("event_name")
    if not event_id or not event_type:
        raise HTTPException(status_code=400, detail="Missing event_id or event_name")
    try:
        await SubscriptionService(session).handle_event(
            event_id=str(event_id), event_type=str(event_type), payload=payload
        )
    except Exception:
        logger.exception("Lemon Squeezy webhook processing failed")
        raise
    return {"status": "ok"}
