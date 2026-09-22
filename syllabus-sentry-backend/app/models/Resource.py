from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
from enum import Enum as PGEnum
import enum
class ResourceType(str, enum.Enum):
    VIDEO = "VIDEO"              # YouTube tutorial, NPTEL/MIT OCW lecture
    ARTICLE = "ARTICLE"          # GeeksforGeeks, tutorial blog, documentation
    DOCUMENTATION = "DOCS"       # Official docs, RFCs, reference manuals
    PRACTICE = "PRACTICE"        # Problem set, LeetCode / GeeksforGeeks problem link
    CHEATSHEET = "CHEATSHEET"    # Quick formula sheet or reference card
    TEXTBOOK_REF = "TEXTBOOK"
class Resource(Base):
    __tablename__="resources"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    topicid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("topics.id",delete="CASCADE"),nullable=False,index=True)
    title:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    url:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    source:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    relevantScore:Mapped[int]=mapped_column(Integer,nullable=False,index=True)
    resouceType=Mapped[ResourceType]=mapped_column(PGEnum(ResourceType,name=""),nullable=False,index=True)
   
    