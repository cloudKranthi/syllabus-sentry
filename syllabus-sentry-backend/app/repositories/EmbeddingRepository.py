# app/repositories/exam_repository.py
from uuid import UUID
from sqlalchemy import select,delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.DocumentEmbedding import DocumentEmbedding
from app.repositories.BaseRepository import BaseRepository


class EmbeddingRepository(BaseRepository[DocumentEmbedding]):

    def __init__(self, session: AsyncSession):
        super().__init__(DocumentEmbedding, session)
    async def save_embeddings(self,embedding_data:list[DocumentEmbedding])->None:
        self.session.add_all(embedding_data)
    async def delete_by_exam_user(self,user_id:UUID,exam_id:UUID)->None:
        query=delete(DocumentEmbedding).where(self.model.user_id==user_id,self.model.exam_id==exam_id)
        await self.session.execute(query)
        await self.session.commit()
    async def search_by_similarity(self,user_id:UUID,exam_id:UUID,vector_store:list[float],unit_number:int|None,limit:int=5)->list[DocumentEmbedding]:
        query=select(DocumentEmbedding).where(self.model.user_id==user_id,self.model.exam_id==exam_id).order_by(DocumentEmbedding.embedding.cosine_distance(vector_store)).limit(limit)
        if unit_number is not None:
            query=query.where(self.model.unit_number==unit_number)
        query=query.order_by(DocumentEmbedding.embedding.cosine_distance(vector_store)).limit(limit)
        res=await self.session.execute(query)
        return list(res.scalars().all())
    