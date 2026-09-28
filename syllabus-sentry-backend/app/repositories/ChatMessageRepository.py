from uuid import UUID
from typing import Sequence
from sqlalchemy import select,update,delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ChatMessage import ChatMessage,Role
from app.repositories.BaseRepository import BaseRepository
class ChatMessageRepository(BaseRepository[ChatMessage]):
    def __init__(self,session:AsyncSession,):
        super().__init__(ChatMessage,session)
    async def extractMessages(self,id:UUID)->list[ChatMessage]:
        stmt=(select(self.model).where(self.model.session_id==id).order_by(ChatMessage.created_at.desc()).limit(10))
        result=await self.session.execute(stmt)
        return list(result.scalars().all()).reverse()
    
        
    
