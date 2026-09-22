from fastapi import APIRouter,Depends,HTTPException,status,Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.services import authService
from app.schemas.auth import UserRegisterRequest,UserRegisterResponse,LoginRequest,TokenCreationResponse
from app.core.database import get_db
from app.models.user import User
from app.api.deps import validateUser
from app.core.config import settings
router=APIRouter(prefix="/api",tags=["Authentication"])

@router.post("/register",response_model=UserRegisterResponse,status_code=status.HTTP_201_CREATED)
async def registerroute(payload:UserRegisterRequest,db:AsyncSession=Depends(get_db)):
    try:
       user=await authService.register_User(db,payload.email,payload.username,payload.isadmin,payload.password)
       return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) 

@router.post("/login")
async def login(payload:LoginRequest,response:Response,db:AsyncSession=Depends(get_db)):
    try:
       user=await authService.login(db,payload.email,payload.password)
    except ValueError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,detail="Invalid email/password")
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED,detail="Invalid Email or password")
    tokens=await authService.create_tokens(payload.email)
    response.set_cookie(key="access_token",value=tokens["access_token"],secure=False,httponly=True,samesite="lax",max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES*60)
    response.set_cookie(key="refresh_token",value=tokens["refresh_token"],secure=False,httponly=True,samesite="lax",max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS*60)
    return {
        "message":"Login succesfull",
        "email":payload.email
    }

