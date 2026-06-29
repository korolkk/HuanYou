"""Customer and CustomerProfile models — SQLite + PostgreSQL compatible."""

from typing import Optional

from sqlalchemy import String, Integer, Float, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, is_postgres

# Conditionally import pgvector
if is_postgres():
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector(1024)
else:
    VECTOR_TYPE = JSON  # Store as JSON array for SQLite


class Customer(Base, UUIDMixin, TimestampMixin):
    """客户基础信息表."""

    __tablename__ = "customers"

    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(256))
    name: Mapped[Optional[str]] = mapped_column(String(100))
    id_number: Mapped[Optional[str]] = mapped_column(String(100))
    gender: Mapped[Optional[str]] = mapped_column(String(10))
    birth_date: Mapped[Optional[Date]] = mapped_column(Date)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    wechat_id: Mapped[Optional[str]] = mapped_column(String(100))
    emergency_contact: Mapped[Optional[str]] = mapped_column(String(100))
    emergency_phone: Mapped[Optional[str]] = mapped_column(String(20))
    role: Mapped[str] = mapped_column(String(20), default="user", index=True)
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Relationships
    profile: Mapped[Optional["CustomerProfile"]] = relationship(
        "CustomerProfile", back_populates="customer", uselist=False, cascade="all, delete-orphan"
    )
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="customer")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="customer")
    feedbacks: Mapped[list["Feedback"]] = relationship("Feedback", back_populates="customer")


class CustomerProfile(Base, UUIDMixin, TimestampMixin):
    """用户画像表."""

    __tablename__ = "customer_profiles"

    customer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("customers.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    age_group: Mapped[Optional[str]] = mapped_column(String(20))
    city: Mapped[Optional[str]] = mapped_column(String(50))
    occupation_category: Mapped[Optional[str]] = mapped_column(String(50))

    # Travel preferences — stored as JSON for SQLite compatibility
    preferred_destinations: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    preferred_categories: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    budget_range_min: Mapped[Optional[float]] = mapped_column(Float)
    budget_range_max: Mapped[Optional[float]] = mapped_column(Float)
    preferred_duration_days: Mapped[Optional[int]] = mapped_column(Integer)
    preferred_season: Mapped[Optional[str]] = mapped_column(String(20))
    preferred_group_size: Mapped[Optional[int]] = mapped_column(Integer)
    travel_style: Mapped[Optional[str]] = mapped_column(String(50))

    booking_frequency: Mapped[Optional[str]] = mapped_column(String(20))
    avg_booking_lead_days: Mapped[Optional[int]] = mapped_column(Integer)
    cancellation_rate: Mapped[Optional[float]] = mapped_column(Float)
    preferred_contact_time: Mapped[Optional[str]] = mapped_column(String(20))

    interest_tags: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    special_requirements: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    mem0_user_id: Mapped[Optional[str]] = mapped_column(String(100))
    profile_summary: Mapped[Optional[str]] = mapped_column(Text)
    profile_embedding: Mapped[Optional[list]] = mapped_column(VECTOR_TYPE)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="profile")
