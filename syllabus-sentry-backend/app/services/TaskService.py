from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exam import Exam
from app.models.user import User
from app.models.ProcessingTask import ProcessingTask,TaskType,TaskStatus
from app.repositories.TaskRepository import TaskRepository
from app.services.ExamService import ExamService
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException,status
from uuid import UUID
from app.services.DocumentService import DocumentService

@dataclass
class   TaskService:
    task_repo:TaskRepository
    exam_service:ExamService
    document_service:DocumentService
    db:AsyncSession
    async def update_task_progress(self,user:User,examname,title:str, st: TaskStatus,progress:int) -> ProcessingTask:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        task = await self.get_by_name(exam.id,title)
        updated_task=await self.task_repo.updateProgress(task.id,progress,title,st)
        if not updated_task:
            raise HTTPException(status_code=404, detail="Document not found")
            
        await self.task_repo.session.commit()
        return updated_task
    async def createTask(self,user:User,examname:str,type:TaskType,title:str,filename:str)->ProcessingTask:
        document=await self.document_service.get_document_by_name(user,examname,filename)
        exam=await self.exam_service.get_exam_by_name(user,examname)
        task=ProcessingTask(exam_id=exam.id,status=TaskStatus.RUNNING,type=type,title=title,sourceDocumentid=document.id)
        res=await self.task_repo.create(task)
        await self.document_repo.session.commit()
        return res
    async def get_exam_by_name(self,user:User,exam_name:str,title:str)->ProcessingTask:
        exam=await self.exam_service.get_exam_by_name(user,exam_name)
        task=self.task_repo.get_by_name(exam.id,title)
        if task is None:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,details="No such Task present")
        return task
    async def get_active_tasks(self,user:User,exam_name:str)->list[ProcessingTask]:
            exam=await self.exam_service.get_exam_by_name(user,exam_name)
            tasks=await self.task_repo.get_actice_task(exam.id)
            return tasks
    async def get_task_by_type(self,user:User,exam_name:str,type:TaskType)->list[ProcessingTask]:
        exam=await self.exam_service.get_exam_by_name(user,exam_name)
        tasks=await self.task_repo.get_by_task_type(exam.id)
        return tasks
    async def delete(self,user:User,title:str,examname:str):
          document=await self.get_task_by_name(user,examname,title)
          await self.task_repo.delete(document)

         


