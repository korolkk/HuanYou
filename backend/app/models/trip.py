"""Trip and TripSchedule models — SQLite + PostgreSQL compatible."""

from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, Text, ForeignKey, Time, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin, is_postgres

if is_postgres():
    from pgvector.sqlalchemy import Vector
    VECTOR_TYPE = Vector(1024)
else:
    VECTOR_TYPE = JSON


class Trip(Base, UUIDMixin, TimestampMixin):
    """行程主表."""

    __tablename__ = "trips"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(200))
    destination: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    destinations_detail: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    country: Mapped[str] = mapped_column(String(50), default="中国")
    province: Mapped[Optional[str]] = mapped_column(String(50))
    city: Mapped[Optional[str]] = mapped_column(String(50))

    category: Mapped[str] = mapped_column(String(30), index=True)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_nights: Mapped[Optional[int]] = mapped_column(Integer)
    departure_city: Mapped[Optional[str]] = mapped_column(String(50))
    best_season: Mapped[Optional[str]] = mapped_column(String(100))

    price_adult: Mapped[Optional[float]] = mapped_column(Float)
    price_child: Mapped[Optional[float]] = mapped_column(Float)
    price_infant: Mapped[Optional[float]] = mapped_column(Float)
    single_room_supplement: Mapped[Optional[float]] = mapped_column(Float)
    price_includes: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    price_excludes: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    summary: Mapped[Optional[str]] = mapped_column(Text)
    highlights: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    recommendation_reasons: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    detailed_description: Mapped[Optional[str]] = mapped_column(Text)

    group_size_min: Mapped[int] = mapped_column(Integer, default=1)
    group_size_max: Mapped[Optional[int]] = mapped_column(Integer)
    departure_dates: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    image_urls: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    brochure_url: Mapped[Optional[str]] = mapped_column(String(500))

    content_embedding: Mapped[Optional[list]] = mapped_column(VECTOR_TYPE)

    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("customers.id")
    )

    schedules: Mapped[list["TripSchedule"]] = relationship(
        "TripSchedule", back_populates="trip", cascade="all, delete-orphan",
        order_by="TripSchedule.sort_order"
    )
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="trip")
    video_scripts: Mapped[list["VideoScript"]] = relationship("VideoScript", back_populates="trip")


class TripSchedule(Base, UUIDMixin, TimestampMixin):
    """每日行程明细表."""

    __tablename__ = "trip_schedules"

    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )

    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    theme: Mapped[Optional[str]] = mapped_column(String(100))
    schedule_type: Mapped[str] = mapped_column(String(30), default="景点")
    time_start: Mapped[Optional[str]] = mapped_column(Time)
    time_end: Mapped[Optional[str]] = mapped_column(Time)

    location: Mapped[Optional[str]] = mapped_column(String(200))
    activity: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)

    meal_included: Mapped[Optional[str]] = mapped_column(String(50))
    hotel_name: Mapped[Optional[str]] = mapped_column(String(200))
    hotel_stars: Mapped[Optional[int]] = mapped_column(Integer)
    hotel_description: Mapped[Optional[str]] = mapped_column(Text)

    transport_type: Mapped[Optional[str]] = mapped_column(String(50))
    transport_detail: Mapped[Optional[str]] = mapped_column(Text)

    tips: Mapped[Optional[str]] = mapped_column(Text)

    image_urls: Mapped[Optional[list]] = mapped_column(JSON, default=list)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    schedule_embedding: Mapped[Optional[list]] = mapped_column(VECTOR_TYPE)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="schedules")
