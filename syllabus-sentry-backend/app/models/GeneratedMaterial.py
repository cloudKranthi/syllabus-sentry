from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
from enum import Enum as PGEnum
import enum

class GeneratedMaterial(Base):
    __tablename__="generatedmaterials"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    topicid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("topics.id",delete="CASCADE"),nullable=False,index=True)
    type:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    content:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    modelUsed:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    created_at:Mapped[datetime]=mapped_column(
            DateTime(timezone=True),
            default=lambda:datetime.now(timezone.utc),
            nullable=False
        )
   
    