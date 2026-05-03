from fastapi import HTTPException, status

from app.models.enums import UserRole
from app.models.user import User


def require_role(user: User, role: UserRole) -> None:
    if user.role != role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def require_admin(user: User) -> None:
    require_role(user, UserRole.admin)


def require_client_owner(user: User, client_id: object) -> None:
    if user.role == UserRole.admin:
        return
    if user.client_id != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed for this client"
        )
