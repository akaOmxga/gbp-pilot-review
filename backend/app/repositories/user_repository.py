from sqlalchemy import select

from app.models.user import User
from app.repositories.base import CRUDRepository


class UserRepository(CRUDRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email, User.deleted_at.is_(None))
        return (await self.session.scalars(stmt)).first()
