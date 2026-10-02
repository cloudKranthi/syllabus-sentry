from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ChatSession import ChatSession
from app.repositories.BaseRepository import BaseRepository


class ChatSessionRepository(BaseRepository[ChatSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(ChatSession, session)

    async def get_by_userid_title(self, id: UUID, title: str) -> ChatSession | None:
        """Fetch a single chat session by owner user ID and title."""
        stmt = select(self.model).where(
            self.model.user_id == id,
            self.model.title == title,
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
    async def get_by_userid(self,id:UUID)->list[ChatSession]:
        stmt=(select(self.model).where(self.model.user_id==id).order_by(ChatSession.created_at.desc))
        result=await self.session.execute(stmt)
        return list(result.scalars().all())