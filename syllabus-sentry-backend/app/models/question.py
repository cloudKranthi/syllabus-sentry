from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey,Float
from datetime import datetime,timezone,timedelta

class Question(Base):
    __tablename__="questions"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    documentid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("documents.id",delete="CASCADE"),nullable=False,index=True)
    questionText:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    questionNumber=Mapped[int]=mapped_column(Integer,nullable=False,index=True)
    year:Mapped[int]=mapped_column(Integer,nullable=False,index=True)
    marks:Mapped[int]=mapped_column(Integer,nullable=False,index=True)
    pageNumber:Mapped[int]=mapped_column(Integer)

    