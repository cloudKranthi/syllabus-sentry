from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.SyllabusUnit import SyllabusUnit
from app.models.user import User
from app.models.document import Document
from app.models.syllabus import Syllabus
from app.models import Topic,TopicPriority
from app.services.ExamService import ExamService
from app.services.DocumentService import DocumentService
from app.repositories.DocumentRepository import DocumentRepository
from app.repositories.SyllabusRepository import SyllabusRepository
from app.repositories.SyllabusUnitRepository import SyllabusUnitRepository
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException,status
from app.repositories.TopicRepository import TopicRepository,TopicPriority as topicPriority

@dataclass
class SyllabusService:
    exam_service:ExamService
    document_service:DocumentService
    syllabus_repo:SyllabusRepository
    document_repo:DocumentRepository
    syllabus_unit_repo:SyllabusUnitRepository
    topic_repo:TopicRepository

    db:AsyncSession
    async def create_syllabus_structure(self,user:User,examname:str,title:str,filename:str)->Syllabus:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        document=await self.document_service.get_document_by_name(user,examname,filename)
        syllabus=Syllabus(examid=exam.id,title=title,sourceDocuemntid=document.id)
        res=await self.syllabus_repo.create(syllabus)
        return res
    async def create_syllabus_unit(self,examname:str,user:User,title:str,unitName:str,unitNumber:int,description:str)->SyllabusUnit:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        syllabus=await self.syllabus_repo.get_by_name(exam.id,title)
        new=SyllabusUnit(syllabus_id=syllabus.id,unitName=unitName,description=description)
        syllabusUnit=await self.syllabus_unit_repo.create(new)
        return syllabusUnit
    async def getTopicByName(self,user:User,examname:str,title:str,TopicName:str)->Topic:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        syllabus=await self.syllabus_repo.get_by_name(exam.id,title)
        topic=await self.topic_repo.get_by_name(syllabus.id,TopicName)
        if topic is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,details="No such topic is found")
        return topic
    async def updateTopicBasePriority(self,user:User,examname:str,title:str,TopicName:str,pr:topicPriority)->Topic:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        syllabus=await self.syllabus_repo.get_by_name(exam.id,title)
        topic=await self.topic_repo.get_by_name(syllabus.id,TopicName)
        await self.topic_repo.updateTopicPriority(topic.id,pr)
    





    