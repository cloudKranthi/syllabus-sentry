# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update,Boolean
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.QuestionTopicMatch import QuestionTopicMatch
from app.repositories.BaseRepository import BaseRepository


class QuestionTopicMatchRepository(BaseRepository[QuestionTopicMatch]):

    def __init__(self, session: AsyncSession):
        super().__init__(QuestionTopicMatch, session)

    
    async def get_question_match_by_exam(self,questionid:UUID,topicid:UUID) -> QuestionTopicMatch:
        stmt = (
            select(self.model)
            .where(self.model.questionid ==questionid,self.model.topicid==topicid)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    async def check_question(self,questionid:UUID)->QuestionTopicMatch|None:
        stmt = (
                    select(self.model)
                    .where(self.model.questionid ==questionid).returning(self.model)
                )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    async def get_by_topic(self,id:UUID)->list[QuestionTopicMatch]:
        stmt=(select(self.model).where(self.model.topicid==id))
        res=await self.session.execute(stmt)
        return list(res.scalar().all())
    async def get_by_question(self,id:UUID)->list[QuestionTopicMatch]:
            stmt=(select(self.model).where(self.model.questionid==id))
            res=await self.session.execute(stmt)
            return list(res.scalar().all())
    

    
    
    
    
    
    