from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.database import SessionDep
from app.integrations.lemonsqueezy.client import LemonSqueezyClient, LemonSqueezyError
from app.repositories.subscription_repository import SubscriptionRepository

router = APIRouter(prefix="/subscription", tags=["subscription"])


class SubscriptionPublic(BaseModel):
    tier: str
    status: str
    monthly_response_quota: int
    current_period_end: str | None = None
    cancelled_at: str | None = None


class CheckoutRequest(BaseModel):
    variant_id: str


class CheckoutResponse(BaseModel):
    url: str


@router.get("", response_model=SubscriptionPublic)
async def get_subscription(
    session: SessionDep, user: CurrentUser
) -> SubscriptionPublic:
    if user.client_id is None:
        raise HTTPException(404)
    sub = await SubscriptionRepository(session).get_by_client(user.client_id)
    if sub is None:
        raise HTTPException(404)
    return SubscriptionPublic(
        tier=sub.tier.value,
        status=sub.status.value,
        monthly_response_quota=sub.monthly_response_quota,
        current_period_end=(
            sub.current_period_end.isoformat() if sub.current_period_end else None
        ),
        cancelled_at=sub.cancelled_at.isoformat() if sub.cancelled_at else None,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    payload: CheckoutRequest, user: CurrentUser
) -> CheckoutResponse:
    if user.client_id is None:
        raise HTTPException(404)
    try:
        url = await LemonSqueezyClient().create_checkout(
            variant_id=payload.variant_id,
            customer_email=user.email,
            custom={"client_id": str(user.client_id)},
        )
    except LemonSqueezyError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return CheckoutResponse(url=url)
