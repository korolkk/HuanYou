"""Order model — SQLite + PostgreSQL compatible."""

from typing import Optional
from datetime import datetime

from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Order(Base, UUIDMixin, TimestampMixin):
    """订单表."""

    __tablename__ = "orders"

    order_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id"), nullable=False, index=True
    )
    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id"), nullable=False, index=True
    )

    departure_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    num_adults: Mapped[int] = mapped_column(Integer, default=1)
    num_children: Mapped[int] = mapped_column(Integer, default=0)
    num_infants: Mapped[int] = mapped_column(Integer, default=0)
    total_price: Mapped[Optional[float]] = mapped_column(Float)
    paid_amount: Mapped[float] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)

    participants: Mapped[Optional[dict]] = mapped_column(JSON, default=list)

    status: Mapped[str] = mapped_column(String(30), default="inquiry", index=True)
    payment_status: Mapped[str] = mapped_column(String(30), default="unpaid")

    contract_url: Mapped[Optional[str]] = mapped_column(String(500))
    insurance_url: Mapped[Optional[str]] = mapped_column(String(500))

    reserved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    departed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="orders")  # noqa: F821
    trip: Mapped["Trip"] = relationship("Trip", back_populates="orders")  # noqa: F821
    feedbacks: Mapped[list["Feedback"]] = relationship("Feedback", back_populates="order")  # noqa: F821
