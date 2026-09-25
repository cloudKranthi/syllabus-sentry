from sqlalchemy import String,Boolean,ForeignKey,DateTime,Integer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID,uuid4
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from app.core.database import Base
from sqlalchemy.orm import Mapped,mapped_column
class SyllabusUnit(Base):
    __tablename__="syllabusunits"
    id=Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        default=uuid4,
        nullable=False,
        index=True,
        primary_key=True
    )
    syllabus_id=Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("syllabus.id",delete="CASCADE"),nullable=False,index=True)
    UnitName=Mapped[str]=mapped_column(String(255),nullable=False,index=True,primary_Key=True)
    unitnumber=Mapped[int]=mapped_column(Integer,nullable="false",index=True)
    description=Mapped[str]=mapped_column(String(255),nullable=False,index=True)
    



    