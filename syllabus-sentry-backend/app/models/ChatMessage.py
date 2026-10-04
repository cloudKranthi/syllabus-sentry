from app.core.database import Base
from typing import Any
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey,JSON,Text
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime,timezone,timedelta
import enum
from sqlalchemy import Enum as SQLEnum
class Role(str,enum.Enum):
    SYSTEM="system"
    USER="user"
    ASSISTANT="assistant"
class ChatMessage(Base):
    __tablename__="chatmessages"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        index=True
    )
    session_id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),ForeignKey("sessions.id",ondelete="CASCADE"),nullable=False,index=True)
    content:Mapped[str]=mapped_column(Text,nullable=True)
    tool_calls:Mapped[list[dict[str,Any]]|None]=mapped_column(JSONB,nullable=True)
    tool_call_id:Mapped[str|None]=mapped_column(String(255),nullable=True)
    created_at:Mapped[datetime]=mapped_column(
            DateTime(timezone=True),
            default=lambda:datetime.now(timezone.utc),
            nullable=False
        )
    role: Mapped[Role] = mapped_column(  
        SQLEnum(Role, name="chat_role_enum", native_enum=False),
        nullable=False,
    )

