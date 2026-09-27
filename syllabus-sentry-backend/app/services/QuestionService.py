from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exam import Exam
from app.models.user import User
from app.models.QuestionTopicMatch import QuestionTopicMatch,MatchMethod
from app.models.document import Document,DocumentType
from app.repositories.DocumentRepository import DocumentRepository
from app.services.ExamService import ExamService
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException,status
from uuid import UUID
from app.models.document import DocumentProcessingStatus
from app.models.question import Question
from app.repositories.QuestionRepository import QuestionRepository
from app.repositories.QuestionTopicMatchRepository import QuestionTopicMatchRepository
@dataclass
class   QuestionService:
    document_repo:DocumentRepository
    exam_service:ExamService
    question_repo:QuestionRepository
    question_matchrepo:QuestionTopicMatchRepository
    db:AsyncSession
    async def save_extracted_questions(self,user:User,examname:str,document_id: UUID, questions_data: list[dict]) -> list[Question]:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        current_year=datetime.now(timezone.utc).year
        ans:list[Question]=[]
        for question in questions_data:
            quest=Question(document_id=document_id,exam_id=exam.id,questionText=question.get("questionText"),questionNumber=question.get("questionNumber"),year=question.get("year")|current_year,marks=question.get("marks"))
            res=await self.question_repo.create(quest)
            ans.append(res)
        return ans
    async def get_questions_by_exam(self,user:User,examname:str) -> list[Question]:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        questions=await self.question_repo.get_by_exams(exam.id)
        return questions
    async def get_unmatched_questions(self,user:User,examname:str) -> list[Question]:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        ans:list[Question]=await self.question_repo.get_questions_by_exam(exam.id)
        res:list[Question]=[]
        for q in ans:
            s=await self.question_matchrepo.check_question(q.id)
            if s is None:
                continue
            else:
                res.append(q)
        return res
    async def get_question(self,user:User,examname:str,number:int)->Question:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        question=await self.question_repo.get_by_exam_questionnumber(exam.id,number)
        if question is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,details="No such Question Present")
        return question
    



        


        
            

    