"""DocumentChunk model for RAG — simplified for SQLite."""

from typing import Optional

from sqlalchemy import String, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin, is_postgres

if is_postgres():
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector(1024)
else:
    VECTOR_TYPE = JSON


class DocumentChunk(Base, UUIDMixin, TimestampMixin):
    """文档块表 — RAG向量存储 (pgvector for PG, JSON for SQLite)."""

    __tablename__ = "document_chunks"

    source_file: Mapped[str] = mapped_column(String(500), nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64))

    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    embedding: Mapped[Optional[list]] = mapped_column(VECTOR_TYPE)
