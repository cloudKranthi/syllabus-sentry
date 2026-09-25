from sqlalchemy import String,Boolean,ForeignKey,DateTime,Integer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID,uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.core.database import Base
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import Enum as SQLEnum
import enum
from datetime import datetime,timezone
class TopicPriority(str,enum.Enum):
    LOW="LOW",
    MEDIUM="MEDIUM",
    HIGH="HIGH",
    CRITICAL="CRITICAL"

class Topic(Base):
    __tablename__="topics"
    id=Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        default=uuid4,
        nullable=False,
        index=True,
        primary_key=True
    )
    syllabus_id=Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("syllabus.id",delete="CASCADE"),nullable=False,index=True)
    name=Mapped[str]=mapped_column(String(255),nullable=False,index=True,primary_Key=True)
    unitnumber=Mapped[int]=mapped_column(Integer,nullable="false",index=True)
    description=Mapped[str]=mapped_column(String(255),nullable=False,index=True)
    estimatedHours=Mapped[int]=mapped_column(Integer,nullable="false",index=True)
    priority=Mapped[TopicPriority]=mapped_column(SQLEnum(TopicPriority,name="topic_priority_enum",nativeEnum=True),nullable=False,default=TopicPriority.MEDIUM)
    createdAt:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.now(timezone.utc),nullable=False)



    