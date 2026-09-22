from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
class Exam(Base):
    __tablename__="exams"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        index=True
    )
    name:Mapped[str]=mapped_column(
        String(255),
        primary_key=True,
        nullable=False,
        index=True
    )
    user_id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),ForeignKey("users.id",onDelete="CASCADE"),nullable=False,index=True)
    
    examDateTime:Mapped[datetime]=mapped_column(
        DateTime(timezone=True),nullable=False
    )
    availableStudyHours=Mapped[int]=mapped_column(Integer,nullable=False)
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
