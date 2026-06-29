"""Feedback model."""

from typing import Optional

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Feedback(Base, UUIDMixin, TimestampMixin):
    """反馈评价表."""

    __tablename__ = "feedback"

    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("orders.id"), nullable=False, index=True
    )
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=False, index=True
    )

    rating_overall: Mapped[Optional[int]] = mapped_column(Integer)
    rating_guide: Mapped[Optional[int]] = mapped_column(Integer)
    rating_accommodation: Mapped[Optional[int]] = mapped_column(Integer)
    rating_transport: Mapped[Optional[int]] = mapped_column(Integer)
    rating_food: Mapped[Optional[int]] = mapped_column(Integer)
    rating_itinerary: Mapped[Optional[int]] = mapped_column(Integer)

    positive_points: Mapped[Optional[str]] = mapped_column(Text)
    negative_points: Mapped[Optional[str]] = mapped_column(Text)
    suggestions: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default="pending")
    staff_response: Mapped[Optional[str]] = mapped_column(Text)

    order: Mapped["Order"] = relationship("Order", back_populates="feedbacks")  # noqa: F821
    customer: Mapped["Customer"] = relationship("Customer", back_populates="feedbacks")  # noqa: F821
