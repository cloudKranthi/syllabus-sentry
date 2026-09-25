# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.syllabus import Syllabus
from app.repositories.BaseRepository import BaseRepository


class SyllabusRepository(BaseRepository[Syllabus]):

    def __init__(self, session: AsyncSession):
        super().__init__(Syllabus, session)

    
    async def get_by_name(self,id:UUID, title: str) -> Syllabus|None:
        stmt = (
            select(self.model)
            .where(self.model.exam_id == id,self.model.title==title)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    
    
    
    