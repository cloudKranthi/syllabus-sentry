from datetime import datetime,timezone
from uuid import UUID,uuid4
from typing import Optional
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy import String,Boolean,DateTime,Text
from app.core.database import Base

class User(Base):
    __tablename__="users"
    id:Mapped[UUID]=mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        index=True,
        default=uuid4

    )
    email:Mapped[str]=mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    username:Mapped[str]=mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password:Mapped[str]=mapped_column(
        String(255),
        nullable=False
    )
    is_admin:Mapped[bool]=mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        default=None,
    )
    created_at:Mapped[datetime]=mapped_column(
        DateTime(timezone=True),
        default=lambda:datetime.now(timezone.utc),
        nullable=False
    )
    updated_at:Mapped[datetime]=mapped_column(
        DateTime(timezone=True),
        default=lambda:datetime.now(timezone.utc),
        onupdate=lambda:datetime.now(timezone.utc),
        nullable=False
    )
    