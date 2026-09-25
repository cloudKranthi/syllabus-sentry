from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta

class Syllabus(Base):
    __tablename__="syllabus"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    examid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("exams.id",delete="CASCADE"),nullable=False,index=True)
    title:Mapped[str]=mapped_column(String(255),index=True,nullable=False,primary_key=True)
    sourceDocumentid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("documents.id",delete="CASCADE"),nullable=False,index=False)
    createdAt:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.now(timezone.utc),nullable=False)
    