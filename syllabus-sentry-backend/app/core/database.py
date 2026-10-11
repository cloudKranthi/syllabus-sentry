from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import  AsyncSession,create_async_engine,async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import event
from pgvector.asyncpg import register_vector
from app.core.config import settings
async def init_connection(conn):
     await register_vector(conn)
engine=create_async_engine(
    settings.async_url,
    echo=True,future=True,
    connect_args={
         "server_settings":{"jit":"off"},
         "command_timeout":60,
    }
    )
@event.listens_for(engine.sync_engine, "connect")
def on_connect(dbapi_connection, connection_record):
    # dbapi_connection is an AsyncAdapt_asyncpg_connection wrapper
    # Its underlying asyncpg connection is accessed via ._connection
    def _register(conn):
        return register_vector(conn)

    # Schedule the coroutine on the active asyncpg event loop
    connection_record.info["vector_registered"] = True
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
