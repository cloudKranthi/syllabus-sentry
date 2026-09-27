from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Text
from app.models.Resource import Resource,ResourceType
from app.services.ExamService import ExamService
from app.repositories.ResourceRepository import ResourceRepository
from app.services.SyllabusService import SyllabusService
from  app.models.user import User
from fastapi import HTTPException,status
@dataclass
class GeneratedMaterialService:
    exam_service:ExamService
    syllabus_service:SyllabusService
    resource_repo:ResourceRepository
    async def add_resource_to_topic(self,user:User,examname:str,topic_title:str,syllabus_tile:str, title: str, url: str, resource_type: ResourceType, source: str,score:int) -> Resource:
        topic=await self.syllabus_service.getTopicByName(user,examname,syllabus_tile,topic_title)
        new=Resource(topicid=topic.id,title=title,url=url,resourceType=resource_type,relevant_score=score,source=source)
        res=await self.resource_repo.create(new)
        return res
    async def get_resources_by_topic(self,user:User,examname:str,topic_title:str,syllabus_tile:str) -> list[Resource]:
        topic=await self.syllabus_service.getTopicByName(user,examname,syllabus_tile,topic_title)
        ans=await self.resource_repo.get_by_topic(topic.id)
        return ans
    async def batch_save_resources(self,user:User,examname:str,topic_title:str,syllabus_tile:str, resources: list[dict]) -> list[Resource]:
        topic=await self.syllabus_service.getTopicByName(user,examname,syllabus_tile,topic_title)
        ans:list[Resource]=[]
        for r in resources:
            new=Resource(topicid=topic.id,title=r["title"],url=r["url"],resourceType=r["resource_type"],relevant_score=r["score"],source=r["source"])
            ans.append(new)
        return ans



