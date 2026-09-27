# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.StudyPlan import StudyPlan
from app.repositories.BaseRepository import BaseRepository


class StudyPlanRepository(BaseRepository[StudyPlan]):

    def __init__(self, session: AsyncSession):
        super().__init__(StudyPlan, session)

    
    async def get_active_paln(self,id:UUID) -> StudyPlan:
        stmt = (
            select(self.model)
            .where(self.model.examid == id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    async def updateHours(self,id:UUID,hours:int)->StudyPlan:
        stmt = (
                    update(StudyPlan)
                    .where(self.model.examid == id).values(totalAvailableHours=hours).returning(self.model)
                )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    
    
    
    
    