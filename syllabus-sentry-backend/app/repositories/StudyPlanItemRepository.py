# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.StudyPlanItem import StudyPlanItem,StudyItemStatus,PlanItemPriority
from app.repositories.BaseRepository import BaseRepository


class StudyPlanItemRepository(BaseRepository[StudyPlanItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(StudyPlanItem, session) 
    async def update_paln_status(self,id:UUID,status:StudyItemStatus) -> StudyPlanItem|None:
        stmt = (
            update(StudyPlanItem)
            .where(self.model.id == id).values(status=status)
        )
        result = await self.session.execute(stmt).returning(self.model)
        return result.scalar_one_or_none()
    async def get_by_item(self,id:UUID)->StudyPlanItem|None:
        stmt=(
            select(self.model).where(self.model.item_id==id)
        )
        res=await self.session.execute(stmt).returning(self.model)
        return res.scalar_one_or_none()
    



    
    
    
    
    