from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
from enum import Enum as PGEnum
import enum
class TopicFrequency(Base):
    __tablename__="topicfrequencies"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    topicid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("topics.id",delete="CASCADE"),nullable=False,index=True)
    reason:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    occuranceCount:Mapped[int]=mapped_column(Integer,nullable=False,index=True)
    yearsAppeared:Mapped[int]=mapped_column(Integer)
    frequencyScore:Mapped[int]=mapped_column(Integer)