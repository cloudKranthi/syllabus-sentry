from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ChatMessage import ChatMessage, Role
from app.repositories.BaseRepository import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage]):
    def __init__(self, session: AsyncSession):
        super().__init__(ChatMessage, session)

    async def extractMessages(self, id: UUID) -> list[ChatMessage]:
        """Fetch the latest 10 conversation turns in chronological order."""
        stmt = (
            select(self.model)
            .where(
                self.model.session_id == id,
                self.model.role.in_([Role.USER, Role.ASSISTANT]),
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(10)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())[::-1]

    async def getSystemMessages(self, id: UUID) -> list[ChatMessage]:
        """Fetch system instructions in chronological order."""
        stmt = (
            select(self.model)
            .where(
                self.model.session_id == id,
                self.model.role == Role.SYSTEM,
            )
            .order_by(ChatMessage.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())