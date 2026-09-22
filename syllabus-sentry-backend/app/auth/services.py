from app.core.security import security
from app.core.config import settings
from app.models.user import User;
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Cookie,HTTPException,status
from datetime import datetime,timezone
import jwt

class AuthService:
    async def get_user_by_email(self,db:AsyncSession,email:str)->User|None:
        stmt=select(User).where(User.email==email)
        result=await db.execute(stmt)
        return result.scalars().first()
    async def register_User(self,db:AsyncSession,email:str,username:str,is_admin:bool,password:str)->User|None:
        user=await self.get_user_by_email(db,email)
        if(user):
            raise ValueError("User already present");
        hashed_password=security.hash_password(password)

        new_user= User(email=email,username=username,hashed_password=hashed_password,
    is_admin=is_admin,)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user
    async def login(self,db:AsyncSession,email:str,password:str):
        user=await self.get_user_by_email(db,email)
        if(user==None):
           raise ValueError("No such user present")
        if not security.compare_passwords(password, user.hashed_password):
            return None

        return user
    async def create_tokens(self,email:str)->dict[str,str]:
       refresh:str=security.generate_refresh_token(email)
       access:str=security.generate_access_token(email)
       return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
        }
    
               
               
    
authService=AuthService()
        
    



