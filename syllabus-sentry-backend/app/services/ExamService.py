from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exam import Exam
from app.models.user import User
from app.repositories.ExamRepository import ExamRepository
from app.repositories.UserRepository import UserRepository
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException,status
@dataclass
class ExamService:
    exam_repo:ExamRepository
    user_repo:UserRepository
    db:AsyncSession
    async def create_exam(self,user:User,name:str,examdate:datetime,dailystudyhours:int)->Exam:
        now=datetime.now(timezone.utc)
        remaining_days = max(
            0.0, (examdate - now).total_seconds() / 86400
        )
        calculated_hours = round(remaining_days * dailystudyhours, 2)
        mode = "SURVIVAL" if calculated_hours < 15.0 else "NORMAL"
        new=Exam(user_id=user.id,name=name,examDateTime=examdate,availableStudyHours=calculated_hours,mode=mode)
        new2=await self.exam_repo.create(new)
        await self.exam_repo.session.commit()
        return new2
    async def get_exam_by_name(self,user:User,name:str)->Exam:
        ans=await self.exam_repo.get_by_name(user.id,name)
        if ans is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No such Exam Details Present")
        return ans
    async def get_all(self,user:User): 
        if(not user.is_admin):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Forbidden Request")
        ans=await self.exam_repo.get_all_exams()
        if ans is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Exams are Present")
        return ans
    async def recalculate_hours(self,user:User,exam_name:str,dailystudyhours:int)->Exam:
        exam=await self.get_exam_by_name(user,exam_name)
        now=datetime.now(timezone.utc)
        remaining_days=max(0.0,(exam.examDateTime-now).total_seconds()/86400)
        calculated_hours = round(remaining_days * dailystudyhours, 2)
        mode = "SURVIVAL" if calculated_hours < 15.0 else "NORMAL"
        ans=await self.exam_repo.updateHours(user.id,calculated_hours,exam_name,mode)
        if ans is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Exams are Present")
        await self.exam_repo.session.commit()
        return ans
    async def deleteExam(self,user:User,exam_name:str):
        exam=await self.get_exam_by_name(user,exam_name)
        if exam is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No Exams are Present")            
        await self.exam_repo.delete(exam)





