from uuid import UUID
from typing import Sequence
from sqlalchemy import select,update,delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document,DocumentProcessingStatus,DocumentType
from app.repositories.BaseRepository import BaseRepository
class DocumentRepository(BaseRepository[Document]):
    def __init__(self,session:AsyncSession,document:Document):
        super().__init__(session,document)
    async def updatestatus(self,Document_id:UUID,status:DocumentProcessingStatus)->Document|None:
        stmt=update(Document).where(Document.id==Document_id).values(status=status)
        result=await self.session.execute(stmt).returning(self.model)
        return result.scalar_one_or_none()
    async def get_document_by_name(self,filename:str,exam_id:UUID)->Document|None:
        stmt=(select(self.model).where(self.model.exam_id==exam_id,self.model.filename==filename))
        res=await self.session.execute(stmt)
        return res.scalar_one_or_none()
    async def get_all_documents(self,id:UUID)->list(Document):
        stmt=(select(self.model).where(self.model.exam_id==id))
        res=await self.session.execute(stmt)
        return list(res.scalar().all())
    async def get_document_by_type(self,id:UUID,type:DocumentType)->list(Document):
        stmt=(select(self.model).where(self.model.exam_id==id))
        res=await self.session.execute(stmt)
        return list(res.scalar().all())

        
    
