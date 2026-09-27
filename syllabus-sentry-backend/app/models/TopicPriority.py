import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TopicPriority(Base):
    __tablename__ = "topicpriorities"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        primary_key=True,
        default=uuid.uuid4,
    )

    topic_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    priorityLevel: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g., "HIGH", "MEDIUM", "LOW"
    priorityScore: Mapped[float] = mapped_column(Float, default=0.0)

    # Merged Frequency Fields
    occuranceCount: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    yearsAppeared: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    frequencyScore: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    calculatedAt: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )