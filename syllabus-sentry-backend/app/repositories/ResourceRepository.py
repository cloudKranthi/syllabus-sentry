# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Resource import Resource,ResourceType
from app.repositories.BaseRepository import BaseRepository


class ResourceRepository(BaseRepository[Resource]):

    def __init__(self, session: AsyncSession):
        super().__init__(Resource, session)

    
    async def get_by_topic(self,id:UUID) -> list[Resource]:
        stmt = (
            select(self.model)
            .where(self.model.topicid == id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalar().all())
    
                

    
    
    
    