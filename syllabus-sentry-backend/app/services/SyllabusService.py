from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.SyllabusUnit import SyllabusUnit
from app.models.user import User
from app.models.document import Document,DocumentProcessingStatus,DocumentType
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
        document=await self.document_repo.get_document_by_name(filename,exam.id)
        if not document:
            document = await self.document_service.registerDocument(
            user=user,
            filename=filename,
            examname=examname,
            storagePath=f"/uploads/{filename}",
            st=DocumentProcessingStatus.PROCESSING,
            type=DocumentType.SYLLABUS)

        syllabus=Syllabus(exam_id=exam.id,title=title,sourceDocumentid=document.id)
        res=await self.syllabus_repo.create(syllabus)
        return res
    async def create_syllabus_unit(self,examname:str,user:User,title:str,unitName:str,unitNumber:int,description:str)->SyllabusUnit:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        syllabus=await self.syllabus_repo.get_by_name(exam.id,title)
        new=SyllabusUnit(syllabus_id=syllabus.id,unit_name=unitName,description=description,unit_number=unitNumber)
        syllabusUnit=await self.syllabus_unit_repo.create(new)
        return syllabusUnit
    async def getTopicByName(self,user:User,examname:str,title:str,TopicName:str)->Topic:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        syllabus=await self.syllabus_repo.get_by_name(exam.id,title)
        topic=await self.topic_repo.get_by_name(syllabus.id,TopicName)
        if topic is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,details="No such topic is found")
        return topic
    async def get_syllabus_by_name(self,user:User,examname:str,syllabusTitle:str)->Syllabus:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        syllabus=await self.syllabus_repo.get_by_name(exam.id,syllabusTitle)
        if not syllabus:
            syllabus=await self.create_syllabus_structure(user,examname,syllabusTitle,examname)
        return syllabus
    async def updateTopicBasePriority(self,user:User,examname:str,title:str,TopicName:str,pr:topicPriority)->Topic:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        syllabus=await self.syllabus_repo.get_by_name(exam.id,title)
        topic=await self.topic_repo.get_by_name(syllabus.id,TopicName)
        await self.topic_repo.updateTopicPriority(topic.id,pr)
    async def createTopic(self,user:User,examname:str,syllabusTitle:str,Topicname:str,description:str,priority:TopicPriority,unitNumber:int,estimatedHours:int)->Topic:
        syllabus=await self.get_syllabus_by_name(user,examname,syllabusTitle)
        topic=Topic(syllabus_id=syllabus.id,name=Topicname,description=description,estimatedHours=estimatedHours,priority=priority,unitnumber=unitNumber)
        st=await self.topic_repo.create(topic)
        await self.topic_repo.session.commit()
        return st
    
    





    