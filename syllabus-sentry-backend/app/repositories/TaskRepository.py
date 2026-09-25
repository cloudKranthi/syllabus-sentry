# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.ProcessingTask import ProcessingTask,TaskType,TaskStatus
from app.repositories.BaseRepository import BaseRepository


class TaskRepository(BaseRepository[ProcessingTask]):

    def __init__(self, session: AsyncSession):
        super().__init__(ProcessingTask, session)

    
    async def get_by_name(self,id:UUID, name: str) -> ProcessingTask|None:
        stmt = (
            select(self.model)
            .where(self.model.exam_id == id,self.model.name==name)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    async def get_actice_task(self,id:UUID)->list[ProcessingTask]:
        stmt = (
                    select(self.model)
                    .where(self.model.exam_id == id,self.model.status==TaskStatus.RUNNING)
                    .order_by(ProcessingTask.created_at.desc())
                )
        result=await list(self.session.execute(stmt))
        return list(result.scalars().all())
    async def get_by_task_type(self,id:UUID,type:TaskType)->list[ProcessingTask]:
        stmt = (
                        select(self.model)
                        .where(self.model.exam_id == id,self.model.type==type)
                        .order_by(ProcessingTask.created_at.desc())
                    )
        result=await list(self.session.execute(stmt))
        return list(result.scalars().all())
    async def updateProgress(self,id:UUID,progress:int,name:str,status:TaskStatus)->ProcessingTask|None:
        stmt=update(ProcessingTask).where(self.model.name==name,self.model.exam_id==id).values(progress=progress,status=TaskStatus).returning(self.model)
        newExam=await self.session.execute(stmt)
        return newExam.one_or_none()
    
    