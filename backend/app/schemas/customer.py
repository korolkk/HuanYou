"""Customer schemas."""

from typing import Optional
from pydantic import BaseModel


class CustomerProfileResponse(BaseModel):
    """Customer profile data."""
    id: str
    customer_id: str
    age_group: Optional[str]
    city: Optional[str]
    preferred_destinations: list[str]
    preferred_categories: list[str]
    budget_range_min: Optional[float]
    budget_range_max: Optional[float]
    preferred_duration_days: Optional[int]
    preferred_season: Optional[str]
    travel_style: Optional[str]
    booking_frequency: Optional[str]
    interest_tags: list[str]
    special_requirements: list[str]
    profile_summary: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class CustomerListResponse(BaseModel):
    """Customer list item."""
    id: str
    phone: str
    name: Optional[str]
    role: str
    status: str
    created_at: str
    order_count: int = 0
    profile: Optional[CustomerProfileResponse] = None

    class Config:
        from_attributes = True


class CustomerDetailResponse(CustomerListResponse):
    """Customer detail with full profile."""
    email: Optional[str]
    gender: Optional[str]
    birth_date: Optional[str]
    wechat_id: Optional[str]
    emergency_contact: Optional[str]
    emergency_phone: Optional[str]
    updated_at: str

    class Config:
        from_attributes = True


class CustomerSegmentResponse(BaseModel):
    """Customer segment analysis."""
    segment_name: str
    count: int
    percentage: float
    description: str
    customer_ids: list[str] = []


class ProfileRefreshRequest(BaseModel):
    """Request to refresh a customer's AI profile."""
    customer_id: str
