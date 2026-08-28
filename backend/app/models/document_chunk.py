from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from datetime import datetime

from app.core.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False,
        index=True
    )

    chunk_index = Column(
        Integer,
        nullable=False
    )

    chunk_text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )