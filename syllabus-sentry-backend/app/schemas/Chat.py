from pydantic import BaseModel
from uuid import UUID
class ChatRequest(BaseModel):
    message:str
    session_title:str
class ChatSessionRequest(BaseModel):
    exam_id:UUID=None
    title:str
