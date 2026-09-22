from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import  AsyncSession,create_async_engine,async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings
engine=create_async_engine(
    settings.async_url,
    echo=True,future=True
    )
AsyncSessionLocal=async_sessionmaker(bind=engine,class_=AsyncSession,autoflush=False,expire_on_commit=False)
Base=declarative_base()
async def get_db()->AsyncGenerator[AsyncSession,None]:
    async with AsyncSessionLocal() as session:
       
        try:
             yield session
        except Exception:
             await session.rollback()
             raise
        finally:
             await session.close()
