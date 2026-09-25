from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey
from datetime import datetime,timezone,timedelta
import enum
from enum import Enum as PGEnum

class TaskType(str, enum.Enum):
    SYLLABUS_PARSING = "SYLLABUS_PARSING"
    PYQ_PROCESSING = "PYQ_PROCESSING"
    PLAN_GENERATION = "PLAN_GENERATION"
    PLAN_REBALANCING = "PLAN_REBALANCING"
    MATERIAL_SYNTHESIS = "MATERIAL_SYNTHESIS"
class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"       # Task created and written to DB, waiting in Redis queue
    RUNNING = "RUNNING"       # Celery worker picked up the task and is executing it
    COMPLETED = "COMPLETED"   # Finished successfully
    FAILED = "FAILED"         # Failed due to an unhandled exception or parsing error
    CANCELLED = "CANCELLED"   # User aborted the job   
class ProcessingTask(Base):
    __tablename__="processingtasks"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid4
    )
    exam_id:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("exams.id",delete="CASCADE"),nullable=False,index=True)
    title:Mapped[str]=mapped_column(String(255),index=True,nullable=False,primary_key=True)
    sourceDocumentid:Mapped[UUID]=mapped_column(PGUUID(as_uuid=True),ForeignKey("documents.id",delete="CASCADE"),nullable=False,index=False)
    progress: Mapped[int] = mapped_column(
    Integer, 
    default=0, 
    nullable=False
)
    createdAt:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=datetime.now(timezone.utc),nullable=False)
    updated_at:Mapped[datetime]=mapped_column(
            DateTime(timezone=True),
            default=lambda:datetime.now(timezone.utc),
            onupdate=lambda:datetime.now(timezone.utc),
            nullable=False
        )
    status=Mapped[TaskStatus]=mapped_column(PGEnum(TaskStatus,name="task_status"),default=TaskStatus.PENDING,nullable=False,index=True)
    type=Mapped[TaskType]=mapped_column(PGEnum(TaskType,name="task_type"),nullable=False,index=True)