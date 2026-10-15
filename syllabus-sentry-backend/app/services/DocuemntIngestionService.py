from uuid import UUID
from typing import Optional
from app.models.DocumentEmbedding import DocumentEmbedding
from app.repositories.EmbeddingRepository import EmbeddingRepository
from app.services.EmbeddingService import EmbeddingService
from app.services.ExamService import ExamService
from app.models.user import User
from app.services.PDFProcessor import PDFProcessor
from app.models.document import DocumentType
from dataclasses import dataclass
@dataclass
class DocumentIngestionService:
    embedding_repo:EmbeddingRepository
    embedding_service:EmbeddingService
    doc_processor:PDFProcessor
    exam_service:ExamService
    async def record(self,user:User,examname:str,sourceType:DocumentType,pdf_bytes:bytes,unit_number:Optional[int]=None)->None:
        exam=await self.exam_service.get_exam_by_name(user,examname)
        text=self.doc_processor.get_text(pdf_bytes)
        chunks=self.doc_processor.get_chunks(text)
        if not chunks:
            return 
        embeddings= self.embedding_service.get_chunk_embeddings(chunks)

        new:list[DocumentEmbedding]=[DocumentEmbedding(user_id=user.id,exam_id=exam.id,source_type=sourceType,content=chunk,embedding=vector,unit_number=unit_number,chunk_index=idx)
                                     for idx,(chunk,vector) in enumerate(zip(chunks,embeddings))]
        await self.embedding_repo.save_embeddings(new)
    async def search(self,user:User,examname:str,question:str,limit:int=5,unitNumber:Optional[int]=None)->list[DocumentEmbedding]:
        vector= self.embedding_service.get_embeddings(question)
        exam=await self.exam_service.get_exam_by_name(user,examname)
        embeddings=await self.embedding_repo.search_by_similarity(user.id,exam.id,vector,unitNumber,limit)
        return embeddings                               
    
    
        

    
