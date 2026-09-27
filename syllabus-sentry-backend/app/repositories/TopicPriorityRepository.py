import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.TopicPriority import TopicPriority
from app.repositories.BaseRepository import BaseRepository


class TopicPriorityRepository(BaseRepository[TopicPriority]):

    def __init__(self, session: AsyncSession):
        super().__init__(TopicPriority, session)

    async def get_by_topic_id(
        self, topic_id: uuid.UUID
    ) -> TopicPriority | None:
        stmt = select(self.model).where(self.model.topic_id == topic_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_frequency_and_priority(
        self,
        topic_id: uuid.UUID,
        occurance_count: int,
        years_appeared: int,
        frequency_score: float,
        priority_score: float,
        priority_level: str,
        reason: str,
    ) -> TopicPriority | None:
        stmt = (
            update(self.model)
            .where(self.model.topic_id == topic_id)
            .values(
                occuranceCount=occurance_count,
                yearsAppeared=years_appeared,
                frequencyScore=frequency_score,
                priorityScore=priority_score,
                priorityLevel=priority_level,
                reason=reason,
            )
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()