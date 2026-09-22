from fastapi import HTTPException,status,Cookie,Response,Depends
from app.core.config import settings
from app.core.database import get_db
from app.core.security import security
from app.auth.services import authService
import jwt
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
async def validateUser(db:AsyncSession=Depends(get_db),access_token:str|None=Cookie(default=None))->User:
        credentials_exception=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        if not access_token:
                  raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User not logged in")
        try:
           payload= security.decode_token(access_token)
           email:str|None=payload.get("sub")
           type:str|None=payload.get("type")
           if email is None or type!="access":
               raise credentials_exception
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="session expired please login again")
        except jwt.PyJWTError:
            raise credentials_exception
        user= await authService.get_user_by_email(db,email)
        if user is None:
            raise credentials_exception
        return user
               
