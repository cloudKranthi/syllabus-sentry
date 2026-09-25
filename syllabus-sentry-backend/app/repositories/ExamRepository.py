# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exam import Exam,ExamMode
from app.repositories.BaseRepository import BaseRepository


class ExamRepository(BaseRepository[Exam]):

    def __init__(self, session: AsyncSession):
        super().__init__(Exam, session)

    
    async def get_by_name(self,id:UUID, name: str) -> Exam|None:
        stmt = (
            select(self.model)
            .where(self.model.user_id == id,self.model.name==name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    async def get_all_my_exams(self,id:UUID)->list[Exam]:
        stmt = (
                    select(self.model)
                    .where(self.model.user_id == id)
                    .order_by(Exam.created_at.desc())
                )
        result=await self.session.execute(stmt)
        return list(result.scalars().all())
    async def get_all_exams(self)->list[Exam]:
        stmt=(select(self.model).order_by(self.model.created_at.desc()))
        result=await self.session.execute(stmt)
        return list(result.scalars().all())
    async def updateHours(self,id:UUID,newHours:int,name:str,mode:ExamMode)->Exam|None:
        stmt=update(Exam).where(self.model.name==name,self.model.user_id==id).values(mode=mode,availableStudyHours=newHours).returning(self.model)
        newExam=await self.session.execute(stmt)
        return newExam.one_or_none()
    
    