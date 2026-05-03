from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser
from app.database import SessionDep
from app.models.enums import UserRole
from app.repositories.dead_letter_repository import DeadLetterRepository
from app.services.dlq_service import replay
from app.utils.circuit import breaker_states

router = APIRouter(prefix="/admin/monitoring", tags=["admin"])


@router.get("/dlq")
async def list_dlq(session: SessionDep, user: CurrentUser) -> list[dict[str, object]]:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    jobs = await DeadLetterRepository(session).list_unreplayed()
    return [
        {
            "id": j.id,
            "task_name": j.task_name,
            "attempts": j.attempts,
            "last_error": j.last_error,
            "failed_at": j.failed_at.isoformat(),
        }
        for j in jobs
    ]


@router.post("/dlq/{dlq_id}/replay", status_code=status.HTTP_202_ACCEPTED)
async def replay_dlq(dlq_id: int, user: CurrentUser) -> dict[str, str]:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    replay(dlq_id)
    return {"status": "replayed"}


@router.get("/circuits")
async def circuits(user: CurrentUser) -> dict[str, str]:
    if user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return breaker_states()
