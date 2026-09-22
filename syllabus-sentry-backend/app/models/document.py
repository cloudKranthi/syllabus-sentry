from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
import enum
from sqlalchemy import Enum as SQLEnum
class DocumentType(str, enum.Enum):
    SYLLABUS = "SYLLABUS"            # Tier 1: Baseline topic structure & schedule
    PYQ = "PYQ"                      # Tier 2: Previous year question papers (frequency/recurrence)
    ASSIGNMENT = "ASSIGNMENT"        # Tier 3: Internal homework / assignment questions[cite: 3]
    INTERNAL_EXAM = "INTERNAL_EXAM"  # Tier 3: Midterms / class tests[cite: 3]
    NOTES = "NOTES"
class DocumentProcessingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"   
class Document(Base):
    __tablename__="documents"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    examid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("exams.id",delete="CASCADE"),nullable=False,index=True)
    filename:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    storagePath:Mapped[str]=mapped_column(String(255),index=True,nullable=False)
    uploadedAt:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.now(timezone.utc),nullable=False)
    type:Mapped[DocumentType]=mapped_column(SQLEnum(DocumentType,name="document_type_enum"),nullable=False)
    status:Mapped[DocumentProcessingStatus]=mapped_column(SQLEnum(DocumentProcessingStatus,name="document_processing_status_enum"),default=DocumentProcessingStatus.PENDING,nullable=False)
    

