# app/repositories/exam_repository.py
import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.BaseRepository import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    # Only write methods that are unique to Exam!
    async def get_user_by_email(self, email: str) -> Sequence[User]:
        stmt = (
            select(self.model)
            .where(self.model.email == email)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()