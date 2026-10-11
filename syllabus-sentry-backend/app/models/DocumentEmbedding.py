from app.core.database import Base
from uuid import UUID,uuid4
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID;
from app.models.document import DocumentType
from sqlalchemy import String,Boolean,DateTime,Integer,ForeignKey,Enum as SQLEnum,Text
from pgvector.sqlalchemy import Vector
from datetime import datetime,timezone,timedelta
class DocumentEmbedding(Base):
    __tablename__="chat_embeddings"
    id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
        index=True
    )
    user_id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),ForeignKey("users.id",ondelete="CASCADE"),nullable=False,index=True)
    exam_id:Mapped[UUID]=mapped_column(
        PGUUID(as_uuid=True),ForeignKey("exams.id",ondelete="CASCADE"),nullable=False,index=True)
    source_type:Mapped[DocumentType]=mapped_column(SQLEnum(DocumentType,name="document_type_enum",native_enum=False),nullable=False)
    unit_number:Mapped[int|None]=mapped_column(Integer,nullable=True)
    chunk_index:Mapped[int]=mapped_column(Integer,nullable=False)
    embedding:Mapped[list[float]]=mapped_column(Vector(384),nullable=False)
    content:Mapped[Text]=mapped_column(Text,nullable=False)
    created_at:Mapped[datetime]=mapped_column(
            DateTime(timezone=True),
            default=lambda:datetime.now(timezone.utc),
            nullable=False
        )