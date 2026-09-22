from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
from enum import Enum as PGEnum
import enum

class StudyPlan(Base):
    __tablename__="studyplans"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    examid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("exams.id",delete="CASCADE"),nullable=False,index=True)
    version:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    totalAvailableHours:Mapped[int]=mapped_column(Integer,index=True,nullable=False)
    generatedAt_at:Mapped[datetime]=mapped_column(
            DateTime(timezone=True),
            default=lambda:datetime.now(timezone.utc),
            nullable=False
        )
   
    