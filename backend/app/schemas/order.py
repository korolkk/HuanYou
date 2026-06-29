"""Order schemas."""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    """Create a new order."""
    trip_id: str
    departure_date: date
    num_adults: int = Field(default=1, ge=1)
    num_children: int = Field(default=0, ge=0)
    num_infants: int = Field(default=0, ge=0)
    participants: list[dict] = []


class OrderUpdate(BaseModel):
    """Update an order (shop owner)."""
    status: Optional[str] = None
    payment_status: Optional[str] = None
    total_price: Optional[float] = None
    paid_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    contract_url: Optional[str] = None
    insurance_url: Optional[str] = None


class OrderListResponse(BaseModel):
    """Order list item."""
    id: str
    order_code: str
    trip_title: str = ""
    trip_destination: str = ""
    departure_date: Optional[str]
    num_adults: int
    num_children: int
    total_price: Optional[float]
    status: str
    payment_status: str
    created_at: str

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderListResponse):
    """Full order detail."""
    trip_id: str
    num_infants: int
    paid_amount: float
    discount_amount: float
    participants: Optional[dict]
    contract_url: Optional[str]
    insurance_url: Optional[str]
    reserved_at: Optional[str]
    confirmed_at: Optional[str]
    paid_at: Optional[str]
    departed_at: Optional[str]
    completed_at: Optional[str]
    cancelled_at: Optional[str]
    updated_at: str

    class Config:
        from_attributes = True


class FeedbackCreate(BaseModel):
    """Submit trip feedback."""
    order_id: str
    rating_overall: int = Field(..., ge=1, le=5)
    rating_guide: Optional[int] = Field(None, ge=1, le=5)
    rating_accommodation: Optional[int] = Field(None, ge=1, le=5)
    rating_transport: Optional[int] = Field(None, ge=1, le=5)
    rating_food: Optional[int] = Field(None, ge=1, le=5)
    rating_itinerary: Optional[int] = Field(None, ge=1, le=5)
    positive_points: Optional[str] = None
    negative_points: Optional[str] = None
    suggestions: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback response."""
    id: str
    order_id: str
    rating_overall: Optional[int]
    positive_points: Optional[str]
    negative_points: Optional[str]
    suggestions: Optional[str]
    status: str
    staff_response: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
