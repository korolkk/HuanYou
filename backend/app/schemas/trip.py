"""Trip schemas for request/response validation."""

from datetime import date, time
from typing import Optional
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Trip Schedule ──

class ScheduleBase(BaseModel):
    day_number: int = Field(..., ge=1, le=30)
    theme: Optional[str] = None
    schedule_type: str = Field(default="景点")
    time_start: Optional[time] = None
    time_end: Optional[time] = None
    location: Optional[str] = None
    activity: Optional[str] = None
    description: Optional[str] = None
    meal_included: Optional[str] = None
    hotel_name: Optional[str] = None
    hotel_stars: Optional[int] = None
    hotel_description: Optional[str] = None
    transport_type: Optional[str] = None
    transport_detail: Optional[str] = None
    tips: Optional[str] = None
    image_urls: list[str] = []
    sort_order: int = 0


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleResponse(ScheduleBase):
    id: str
    trip_id: str

    class Config:
        from_attributes = True


# ── Trip ──

class TripBase(BaseModel):
    code: str = Field(..., max_length=50)
    title: str = Field(..., max_length=200)
    subtitle: Optional[str] = None
    destination: str = Field(..., max_length=100)
    destinations_detail: list[str] = []
    country: str = "中国"
    province: Optional[str] = None
    city: Optional[str] = None
    category: str = "国内游"
    duration_days: int = Field(..., ge=1)
    duration_nights: Optional[int] = None
    departure_city: Optional[str] = None
    best_season: Optional[str] = None
    price_adult: Optional[float] = None
    price_child: Optional[float] = None
    price_infant: Optional[float] = None
    single_room_supplement: Optional[float] = None
    price_includes: list[str] = []
    price_excludes: list[str] = []
    detailed_description: Optional[str] = None
    group_size_min: int = 1
    group_size_max: Optional[int] = None
    departure_dates: list[str] = []
    cover_image_url: Optional[str] = None
    image_urls: list[str] = []
    is_featured: bool = False


class TripCreate(TripBase):
    """Create a new trip."""
    schedules: list[ScheduleCreate] = []


class TripUpdate(BaseModel):
    """Update an existing trip (all fields optional)."""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    destination: Optional[str] = None
    category: Optional[str] = None
    duration_days: Optional[int] = None
    price_adult: Optional[float] = None
    price_child: Optional[float] = None
    detailed_description: Optional[str] = None
    cover_image_url: Optional[str] = None
    image_urls: Optional[list[str]] = None
    departure_dates: Optional[list[str]] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None


class TripListResponse(BaseModel):
    """Trip list item."""
    id: str
    code: str
    title: str
    subtitle: Optional[str]
    destination: str
    category: str
    duration_days: int
    price_adult: Optional[float]
    cover_image_url: Optional[str]
    summary: Optional[str]
    highlights: list[str]
    is_featured: bool
    status: str
    created_at: str

    class Config:
        from_attributes = True


class TripDetailResponse(TripListResponse):
    """Full trip detail."""
    destinations_detail: list[str]
    country: str
    province: Optional[str]
    city: Optional[str]
    duration_nights: Optional[int]
    departure_city: Optional[str]
    best_season: Optional[str]
    price_child: Optional[float]
    price_infant: Optional[float]
    single_room_supplement: Optional[float]
    price_includes: list[str]
    price_excludes: list[str]
    recommendation_reasons: list[str]
    detailed_description: Optional[str]
    group_size_min: int
    group_size_max: Optional[int]
    departure_dates: list[str]
    image_urls: list[str]
    brochure_url: Optional[str]
    schedules: list[ScheduleResponse] = []
    updated_at: str

    class Config:
        from_attributes = True


class TripSummaryRequest(BaseModel):
    """Request AI summary generation for a trip."""
    regenerate: bool = False
