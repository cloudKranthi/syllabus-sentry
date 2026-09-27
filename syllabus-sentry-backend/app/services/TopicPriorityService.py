from dataclasses import dataclass
from fastapi import HTTPException, status

from app.models.TopicPriority import TopicPriority
from app.models.user import User
from app.repositories.TopicPriorityRepository import TopicPriorityRepository
from app.services.SyllabusService import SyllabusService


@dataclass
class TopicPriorityService:
    priority_repo: TopicPriorityRepository
    syllabus_service: SyllabusService

    async def calculate_and_save_priority(
        self,
        user: User,
        examname: str,
        syllabus_name: str,
        topic_name: str,  # Fixed: changed uuid.UUID to str
        occurance_count: int,
        years_appeared: int,
        exam_mode: str = "NORMAL",
    ) -> TopicPriority:
        topic = await self.syllabus_service.getTopicByName(
            user, examname, syllabus_name, topic_name
        )
        if not topic:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Topic '{topic_name}' not found.",
            )

        # 1. Deterministic Frequency Score (0 to 100 scale)
        raw_score = (occurance_count * 2.0) + (years_appeared * 3.0)
        frequency_score = round(min(100.0, raw_score * 5.0), 2)

        # 2. Derive Priority Score & Priority Level
        priority_score = frequency_score
        if priority_score >= 60.0:
            level = "HIGH"
            reason = f"Appeared {occurance_count} times across {years_appeared} year(s)"
        elif priority_score >= 30.0:
            level = "MEDIUM"
            reason = "Moderate recurrence in historical exams"
        else:
            level = "LOW"
            reason = (
                "Rarely tested"
                if exam_mode == "NORMAL"
                else "Skipped in Survival Mode"
            )

        # 3. Upsert into database
        existing = await self.priority_repo.get_by_topic_id(topic.id)
        if existing:
            updated = (
                await self.priority_repo.update_frequency_and_priority(
                    topic_id=topic.id,
                    occurance_count=occurance_count,
                    years_appeared=years_appeared,
                    frequency_score=frequency_score,
                    priority_score=priority_score,
                    priority_level=level,
                    reason=reason,
                )
            )
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update topic priority record.",
                )
            await self.priority_repo.session.commit()
            return updated
        else:
            new_record = TopicPriority(
                topic_id=topic.id,
                occuranceCount=occurance_count,
                yearsAppeared=years_appeared,
                frequencyScore=frequency_score,
                priorityScore=priority_score,
                priorityLevel=level,
                reason=reason,
            )
            created = await self.priority_repo.create(new_record)
            await self.priority_repo.session.commit()
            return created