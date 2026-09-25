# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.SyllabusUnit import SyllabusUnit
from app.repositories.BaseRepository import BaseRepository


class SyllabusRepository(BaseRepository[SyllabusUnit]):

    def __init__(self, session: AsyncSession):
        super().__init__(SyllabusUnit, session)
    async def get_by_name(self,id:UUID, title: str) -> SyllabusUnit|None:
        stmt = (
            select(self.model)
            .where(self.model.syllabus_id == id,self.model.UnitName==title)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    async def get_all_syllabus(self,id:UUID)->list[SyllabusUnit]:
        stmt = (
            select(self.model)
            .where(self.model.syllabus_id == id)
        )
        result = await self.session.execute(stmt).returning(self.model)
        return list(result.scalar().all())
    

    
    
    
    
    