from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.StudyPlanRepository import StudyPlanRepository
from app.repositories.StudyPlanItemRepository import StudyPlanItemRepository
from app.services.ExamService import ExamService
from app.models.StudyPlan import StudyPlan
from app.models.StudyPlanItem import StudyPlanItem,PlanItemPriority,StudyItemStatus
from fastapi import HTTPException,status
from app.models.user import User
from app.services.SyllabusService import SyllabusService

@dataclass
class StudyPlanService:
    studyplanrepo:StudyPlanRepository
    studyplanitemrepo:StudyPlanItemRepository
    examService:ExamService
    syllabusService:SyllabusService
    db:AsyncSession
    async def get_active_plan(self,user:User,examname:str) -> StudyPlan:
        exam=await self.examService.get_exam_by_name(user,examname)
        studyPlan=await self.studyplanrepo.get_active_paln(exam.id)
        if studyPlan is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No such study plan found")
        return studyPlan
    async def generate_baseline_plan(self,user:User,examname:str,version:int) -> StudyPlan:
        exam=await self.examService.get_exam_by_name(user,examname)
        new=StudyPlan(examid=exam.id,version=version,totalAvailableHours=exam.availableStudyHours)
        res=await self.studyplanrepo.create(new)
        await self.studyplanrepo.session.commit(res)
        return res
    async def generate_plan_item(self,user:User,examname:str,syllabus_title:str,topic_tilte:str,plannedHours:float,sequence_order:int,priority:PlanItemPriority,status:StudyItemStatus)->StudyPlanItem:
        item=await self.get_active_plan(user,examname)
        topic=await self.syllabusService.getTopicByName(user,examname,syllabus_title,topic_tilte)
        new=StudyPlanItem(item_id=item.id,topic_id=topic.id,plannedHours=plannedHours,sequence_order=sequence_order,priority=priority,status=status)
        res=await self.studyplanitemrepo.create(new)
        return res


    async def update_plan_item_status(self,user:User,examname:str, status: StudyItemStatus) -> StudyPlanItem:
        item=await self.get_active_plan(user,examname)
        res=await self.studyplanitemrepo.get_by_item(item.id)
        res2=await self.update_paln_status(res.id,status)
        return res2
    async def rebalance_plan(self,user:User,examname:str,adjusted_daily_hours: float | None = None) -> StudyPlan:
        exam=await self.examService.get_exam_by_name(user,examname)
        res=await self.studyplanrepo.updateHours(exam.id,adjusted_daily_hours)
        await self.studyplanrepo.session.commit(res)
        return res


