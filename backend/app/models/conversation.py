"""Conversation model."""

from typing import Optional

from sqlalchemy import String, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Conversation(Base, UUIDMixin, TimestampMixin):
    """会话记录表."""

    __tablename__ = "conversations"

    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=False, index=True
    )
    session_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    role: Mapped[str] = mapped_column(String(20))
    agent_name: Mapped[Optional[str]] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="conversations")  # noqa: F821
