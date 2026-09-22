from contextlib import asynccontextmanager
from fastapi import FastAPI,Depends,HTTPException,status
from app.core.database import get_db,Base,engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.auth import router as auth_router
import app.models.user;
from app.schemas.auth import UserRegisterResponse
from app.models.user import User
from app.api.deps import validateUser
@asynccontextmanager
async def lifespan(app:FastAPI):
   async with engine.begin() as conn:
     await conn.run_sync(Base.metadata.create_all)
   yield
app=FastAPI(title="Syllabus_Sentry",lifespan=lifespan)


@app.get("/health")
async def health_check() :
     return {
          "status":"healthy",
          "service":"Syllabus_Sentry",
          "version":"0.1.0"

     }
@app.get("/me",response_model=UserRegisterResponse)
async def get_my_Details(user:User=Depends(validateUser)):
    return user
@app.get("/check-connection")
async def connection_check(db:AsyncSession=Depends(get_db)) :
  try:
     result=await db.execute(text("SELECT 1;"))
     scalar_val=result.scalar();
     return {
       "status":"connected",
       "value":scalar_val
     }
  except Exception as e:
     raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(e)}"
        )
app.include_router(auth_router)