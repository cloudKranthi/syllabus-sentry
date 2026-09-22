from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey,Float
from datetime import datetime,timezone,timedelta
from enum import Enum as PGEnum
import enum

class PlanItemPriority(str, enum.Enum):
    CRITICAL = "CRITICAL"    # High frequency / high marks; must study first
    HIGH = "HIGH"            # Core recurring syllabus topic
    MEDIUM = "MEDIUM"        # Standard baseline topic
    LOW = "LOW"              # Low yield, deprioritize under tight time constraints
class StudyItemStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    SKIPPED = "SKIPPED"        # Skipped by student or deprioritized by adaptive rebalancing[cite: 2]


class StudyPlanItem(Base):
    __tablename__ = "study_plan_items"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )

    study_plan_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("studyplans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    topic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Time budget allocated to this topic by the deterministic planner
    planned_hours: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Computed priority level for this run
    priority: Mapped[PlanItemPriority] = mapped_column(
        PGEnum(
            PlanItemPriority,
            name="plan_item_priority_enum",
            native_enum=False,
        ),
        default=PlanItemPriority.MEDIUM,
        nullable=False,
    )

    # The order in which the student should tackle this topic (1, 2, 3...)
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    # Student completion status
    status: Mapped[StudyItemStatus] = mapped_column(
        PGEnum(
            StudyItemStatus,
            name="study_item_status_enum",
            native_enum=False,
        ),
        default=StudyItemStatus.NOT_STARTED,
        nullable=False,
        index=True,
    )