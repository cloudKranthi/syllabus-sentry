from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.question import Question
from app.models.QuestionTopicMatch import QuestionTopicMatch,MatchMethod
from app.models.TopicPriority import TopicPriority
from app.repositories.QuestionTopicMatchRepository import    QuestionTopicMatchRepository
from app.services.ExamService import ExamService
from app.repositories.TopicRepository import TopicRepository
from app.services.QuestionService import QuestionService
from app.models.user import User
from app.models import Syllabus
from app.services.SyllabusService import SyllabusService
from app.repositories.QuestionRepository import QuestionRepository
from app.services.DocumentService import DocumentService
from uuid import UUID
from fastapi import HTTPException,status
@dataclass
class TopicMatchService:
    question_match_repo:QuestionTopicMatchRepository
    exam_service:ExamService
    question_service:QuestionService
    topic_repo:TopicRepository
    question_repo:QuestionRepository
    syllabus_service:SyllabusService
    document_service:DocumentService
    async def record_match(self,user:User,examname:str,questionnumber:int,syllabus_title:str, topic_title:str, score: float, method: MatchMethod) -> QuestionTopicMatch:
        
        question=await self.question_service.get_question(user,examname,questionnumber)
        topic=await self.syllabus_service.getTopicByName(user,examname,syllabus_title,topic_title)
        question_match=QuestionTopicMatch(questionid=question.id,topicid=topic.id,match_method=method,similarity_score=score)
        res=await self.question_match_repo.create(question_match)
        return res
    async def get_matches_for_topic(self,user:User,examname:str,syllabus_title:str, topic_title:str) -> list[QuestionTopicMatch]:
        topic=await self.syllabus_service.getTopicByName(user,examname,syllabus_title,topic_title)
        res=await self.question_match_repo.get_by_topic(topic.id)
        return res
    async def delete_weak_matches(self,user:User,examname:str,questionnumber:int,min_score: float) -> int:
        question=await self.question_service.get_question(user,examname,questionnumber)
        matches=await self.question_match_repo.get_by_question(question.id)
        ans:int=0
        for m in matches:
            if m.similarity_score<=min_score:
                res=self.question_match_repo.delete(m)
                ans+=1
        return ans




    




