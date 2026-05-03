from fastapi import APIRouter, status

from app.api.deps import CurrentUser
from app.database import SessionDep
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=UserPublic)
async def get_me(user: CurrentUser) -> UserPublic:
    return UserPublic.model_validate(user)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(user: CurrentUser, session: SessionDep) -> None:
    from datetime import UTC, datetime

    user.deleted_at = datetime.now(UTC)
    await session.commit()
