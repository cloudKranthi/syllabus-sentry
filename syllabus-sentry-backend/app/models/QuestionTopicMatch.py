from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
import enum
from enum import Enum as SQLEnum
class MatchMethod(str, enum.Enum):
    SEMANTIC = "SEMANTIC"  # Pure embedding vector similarity (e.g., cosine)
    LLM_VERIFIED = "LLM_VERIFIED"  # Vector retrieval followed by LLM confirmation
    KEYWORD = "KEYWORD"  # Exact term/regex match in topic description
    MANUAL = "MANUAL"  # User manually linked or corrected the match
class QuestionTopicMatch(Base):
    __tablename__="questiontopicmatches"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    questionid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("questions.id",delete="CASCADE"),nullable=False,index=True)
    topicid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("topics.id",delete="CASCADE"),nullable=False,index=True)
    match_method: Mapped[MatchMethod] = mapped_column(
        SQLEnum(
            MatchMethod,
            name="match_method_enum",
            native_enum=False,  # stored as VARCHAR with CHECK constraint
        ),
        default=MatchMethod.SEMANTIC,
        nullable=False,
    )

    