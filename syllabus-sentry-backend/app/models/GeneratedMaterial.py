import enum
import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base


class MaterialType(str, enum.Enum):
    CHEATSHEET = "CHEATSHEET"
    FORMULA_SHEET = "FORMULA_SHEET"
    SUMMARY = "SUMMARY"
    PRACTICE_SET = "PRACTICE_SET"


class GeneratedMaterial(Base):
    __tablename__ = "generated_materials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Optional: can be tied to a specific topic or cover the whole exam
    topic_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # 1. Added human-readable title / identifier
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    material_type: Mapped[MaterialType] = mapped_column(
        SQLEnum(MaterialType, name="material_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )

    # 2. Changed from String(255) to Text for large markdown content
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )