from pydantic import BaseModel,ConfigDict,EmailStr
from uuid import UUID
class UserRegisterRequest(BaseModel) :
    email:EmailStr
    username:str
    password:str
    isadmin:bool=False
class UserRegisterResponse(BaseModel) :
    email:EmailStr
    username:str
    model_config = ConfigDict(from_attributes=True)
class LoginRequest(BaseModel):
    email:EmailStr
    password:str
class TokenCreationResponse(BaseModel) :
    access_token:str
    refresh_token:str
    token_type:str="bearer"