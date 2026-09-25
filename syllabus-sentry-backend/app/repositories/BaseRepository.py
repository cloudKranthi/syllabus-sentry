from uuid import UUID
from app.core.database import Base
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Any,Generic,TypeVar,Type,Sequence
ModelType=TypeVar("ModelType",bounds=Any)
class BaseRepository(ModelType[Generic]):
    def __init__(self,model:Type[ModelType],session:AsyncSession):
        self.model=model
        self.session=session
    async def get_by_id(self,uuid:UUID)->ModelType|Any:
        return await self.session.get(self.model,uuid)
    async def create(self,**kwargs:Any)->ModelType:
        instance=self.model(**kwargs)
        await self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance
    async def delete(self,instance:ModelType)->None:
        await self.session.delete(instance)
        await self.session.flush()
    async def get_all(self,limit:int=100,offset:int=0)->Sequence[ModelType]:
        stmt=select(self.model).limit(limit).offset(offset)
        result=await self.session.execute(stmt)
        return  result.scalars().all()
