# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.Topic import Topic,TopicPriority
from app.repositories.BaseRepository import BaseRepository


class TopicRepository(BaseRepository[Topic]):

    def __init__(self, session: AsyncSession):
        super().__init__(Topic, session)

    
    async def get_by_name(self,id:UUID, name: str) -> Topic|None:
        stmt = (
            select(self.model)
            .where(self.model.syllabus_id == id,self.model.name==name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    async def updateTopicPriority(self,id:UUID,pr:TopicPriority):
        stmt=(update(Topic).where(self.model.id==id).values(priority=pr))
        res=await self.session.execute(stmt).returning(self.model)
        await self.session.commit(res)
                

    
    
    
    