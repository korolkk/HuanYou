"""VideoScript model with CapCut export fields."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class VideoScript(Base, UUIDMixin, TimestampMixin):
    """视频脚本表."""

    __tablename__ = "video_scripts"

    trip_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("trips.id"), nullable=False, index=True
    )
    created_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("customers.id"))

    title: Mapped[Optional[str]] = mapped_column(String(200))
    platform: Mapped[str] = mapped_column(String(50), default="抖音")
    duration_seconds: Mapped[int] = mapped_column(Integer, default=300)
    style: Mapped[Optional[str]] = mapped_column(String(20))  # 活泼/文艺/专业/感性

    script_content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    script_json: Mapped[Optional[dict]] = mapped_column(JSON)  # ScriptSegment[]

    hook_text: Mapped[Optional[str]] = mapped_column(Text)
    highlights_text: Mapped[Optional[str]] = mapped_column(Text)
    detail_text: Mapped[Optional[str]] = mapped_column(Text)
    cta_text: Mapped[Optional[str]] = mapped_column(Text)

    image_assignments: Mapped[Optional[dict]] = mapped_column(JSON)

    # Quality evaluation
    quality_score: Mapped[Optional[float]] = mapped_column(Float)
    engagement_score: Mapped[Optional[float]] = mapped_column(Float)
    accuracy_score: Mapped[Optional[float]] = mapped_column(Float)
    completeness_score: Mapped[Optional[float]] = mapped_column(Float)

    generation_version: Mapped[int] = mapped_column(Integer, default=1)
    polish_iterations: Mapped[int] = mapped_column(Integer, default=0)
    model_used: Mapped[Optional[str]] = mapped_column(String(50))
    generation_time_ms: Mapped[Optional[int]] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(20), default="draft")
    approved_by: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("customers.id"))

    # CapCut export fields
    capcut_draft_id: Mapped[Optional[str]] = mapped_column(String(100))
    export_status: Mapped[str] = mapped_column(String(20), default="none")
    exported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    trip: Mapped["Trip"] = relationship("Trip", back_populates="video_scripts")  # noqa: F821
