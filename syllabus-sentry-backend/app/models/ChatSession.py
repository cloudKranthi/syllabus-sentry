from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
from enum import Enum as PGEnum
class ChatSession(Base):
    __tablename__="sessions"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        index=True
    )
    user_id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    exam_id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),ForeignKey("exams.id",ondelete="CASCADE"),nullable=True,index=True)
    title:Mapped[str]=mapped_column(String(255),nullable=False,index=True)
    created_at:Mapped[datetime]=mapped_column(
            DateTime(timezone=True),
            default=lambda:datetime.now(timezone.utc),
            nullable=False
        )
    updated_at:Mapped[datetime]=mapped_column(
                DateTime(timezone=True),
                default=lambda:datetime.now(timezone.utc),
                onupdate=lambda:datetime.now(timezone.utc),
                nullable=False
            )
