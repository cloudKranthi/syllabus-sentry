# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.GeneratedMaterial import GeneratedMaterial
from app.repositories.BaseRepository import BaseRepository


class GeneratedMaterialRepository(BaseRepository[GeneratedMaterial]):

    def __init__(self, session: AsyncSession):
        super().__init__(GeneratedMaterial, session)

    
    async def get_by_name(self,id:UUID, name: str) -> GeneratedMaterial|None:
        stmt = (
            select(self.model)
            .where(self.model.exam_id == id,self.model.title==name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    async def get_by_name_topic(self,id:UUID,tid:UUID, name: str) -> GeneratedMaterial|None:
            stmt = (
                select(self.model)
                .where(self.model.exam_id == id,self.model.title==name,self.model.topic_id==tid)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
    
                

    
    
    
    