# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.question import Question
from app.repositories.BaseRepository import BaseRepository

class QuestionRepository(BaseRepository[Question]):

    def __init__(self, session: AsyncSession):
        super().__init__(Question, session)

    
    async def get_questions_by_exam(self,id:UUID) -> list[Question]:
        stmt = (
            select(self.model)
            .where(self.model.exam_id == id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    async def get_by_exam_questionnumber(self,id:UUID,did:UUID,number:int)->Question|None:
        stmt=(select(self.model).where(self.model.exam_id==id,self.model.questionNumber==number))
        result =await self.session.execute(stmt).returning(self.model)
        return result.scalar_one_or_none()
    

     
    
    
    
    
    
    