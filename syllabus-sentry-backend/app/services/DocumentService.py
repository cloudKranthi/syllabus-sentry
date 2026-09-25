from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.exam import Exam
from app.models.user import User
from app.models.document import Document,DocumentType
from app.repositories.DocumentRepository import DocumentRepository
from app.services.ExamService import ExamService
from datetime import datetime,timedelta,timezone
from fastapi import HTTPException,status
from uuid import UUID
from app.models.document import DocumentProcessingStatus

@dataclass
class   DocumentService:
    document_repo:DocumentRepository
    exam_service:ExamService
    db:AsyncSession
    async def transition_document_status(self,document_id: UUID, st: DocumentProcessingStatus) -> Document:
        updated_doc = await self.doc_repo.update_status(document_id, st)
        if not updated_doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        await self.document_repo.session.commit()
        return updated_doc
    async def registerDocument(self,user:User,filename:str,examname:str,storagePath:str,st:DocumentProcessingStatus,type:DocumentType)->Document:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        document=Document(exam_id=exam.id,filename=filename,storagePath=storagePath,status=st,type=type)
        res=await self.document_repo.create(document)
        await self.document_repo.session.commit()
        return res
    async def get_exam_all_documents(self,user:User,exam_name:str)->list[Document]:
        exam=await self.exam_service.get_exam_by_name(user,exam_name)
        documents=await self.document_repo.get_all_documents(exam.id)
        return documents
    async def get_exam_type_documents(self,user:User,exam_name:str,type:DocumentType)->list[Document]:
            exam=await self.exam_service.get_exam_by_name(user,exam_name)
            documents=await self.document_repo.get_document_by_type(exam.id,type)
            return documents
    async def get_document_by_name(self,user:User,exam_name:str,filename:str)->Document:
        exam=await self.exam_service.get_exam_by_name(user,exam_name)
        document=await self.document_repo.get_document_by_name(exam.id,filename)
        if document is None:
             raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="No such document present")
        return document
    async def delete(self,user:User,exam_name:str,filename:str):
          exam=await self.exam_service.get_exam_by_name(user,exam_name)
          document=await self.get_document_by_name(user,exam_name,filename)
          await self.document_repo.delete(document)

         


