from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser
from app.database import SessionDep
from app.repositories.client_settings_repository import ClientSettingsRepository
from app.schemas.settings import ClientSettingsPublic, ClientSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=ClientSettingsPublic)
async def get_settings_(
    session: SessionDep, user: CurrentUser
) -> ClientSettingsPublic:
    if user.client_id is None:
        raise HTTPException(404, "User has no client")
    settings = await ClientSettingsRepository(session).get_by_client(user.client_id)
    if settings is None:
        raise HTTPException(404, "Settings not found")
    return ClientSettingsPublic.model_validate(settings)


@router.patch("", response_model=ClientSettingsPublic)
async def patch_settings(
    payload: ClientSettingsUpdate, session: SessionDep, user: CurrentUser
) -> ClientSettingsPublic:
    if user.client_id is None:
        raise HTTPException(404, "User has no client")
    repo = ClientSettingsRepository(session)
    settings = await repo.get_by_client(user.client_id)
    if settings is None:
        raise HTTPException(404, "Settings not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    await session.commit()
    return ClientSettingsPublic.model_validate(settings)
