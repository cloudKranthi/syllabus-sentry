import jwt
import bcrypt
from app.models import User
from datetime import datetime,timezone,timedelta
from app.core.config import settings
from typing import Any,Optional
class Security:
  def hash_password(self,password:str)->str:
    s=bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"),s).decode("utf-8")
  def compare_passwords(self,p1:str,p2:str)->bool:
    return bcrypt.checkpw(
        p1.encode("utf-8"),
        p2.encode("utf-8")
    )
  def generate_access_token(self,subject:str|Any,expires_delta:Optional[timedelta]=None):
    if expires_delta:
        expires=datetime.now(timezone.utc)+expires_delta
    else:
        expires=datetime.now(timezone.utc)+timedelta(minutes=settings. ACCESS_TOKEN_EXPIRE_MINUTES)
    ac={
            "sub":str(subject),
            "exp":expires,
            "type":"access"
        }
    return jwt.encode(ac,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
  def generate_refresh_token(self,subject:str|Any):
    expires=datetime.now(timezone.utc)+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    ac={
                "sub":str(subject),
                "exp":expires,
                "type":"refresh"
            }
    return jwt.encode(ac,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
  def decode_token(self,token:str)->dict:
    return jwt.decode(token,settings.SECRET_KEY,algorithms=settings.ALGORITHM)
  
security=Security()