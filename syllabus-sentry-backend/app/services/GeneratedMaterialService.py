from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Text
from app.models.GeneratedMaterial import GeneratedMaterial,MaterialType
from app.services.ExamService import ExamService
from app.repositories.GeneratedMaterialRepository import GeneratedMaterialRepository
from app.services.SyllabusService import SyllabusService
from  app.models.user import User
from fastapi import HTTPException,status
@dataclass
class GeneratedMaterialService:
    exam_service:ExamService
    syllabus_service:SyllabusService 
    generated_repo:GeneratedMaterialRepository
    async def create_material(self,user:User,examname:str,material_tile:str,content:Text,type:MaterialType)->GeneratedMaterial:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        new=GeneratedMaterial(exam_id=exam.id,content=content,material_type=type)
        res=await self.generated_repo.create(new)
        return res
    async def create_material_topic(self,user:User,examname:str,material_tile:str,content:Text,type:MaterialType,syllabus_title:str,topic_title:str)->GeneratedMaterial:
            exam=await self.exam_service.get_exam_by_name(user,examname)
            topic=await self.syllabus_service.getTopicByName(user,examname,syllabus_title,topic_title)
            new=GeneratedMaterial(exam_id=exam.id,content=content,material_type=type,topic_id=topic.id)
            res=await self.generated_repo.create(new)
            return res
    async def get_material(self,user:User,examname:str,material_tile:str)->GeneratedMaterial:
         exam=await self.exam_service.get_exam_by_name(user,examname)
         ans=await self.generated_repo.get_by_name(exam.id,material_tile)
         if ans is None:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No such Material Found")
         return ans
    async def get_material_topic(self,user:User,examname:str,material_tile:str,syllabus_title:str,topic_title:str)->GeneratedMaterial:
         exam=await self.exam_service.get_exam_by_name(user,examname)
         topic=await self.syllabus_service.getTopicByName(user,examname,syllabus_title,topic_title)
         ans=await self.generated_repo.get_by_name_topic(exam.id,topic.id,material_tile)
         if ans is None:
              raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No such Material Found")
         return ans
