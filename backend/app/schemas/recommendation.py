"""Recommendation schemas."""

from typing import Optional
from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    """User request for trip recommendations."""
    query: str = Field(..., description="自然语言描述需求，或结构化需求")
    destination_pref: Optional[str] = None
    budget_max: Optional[float] = None
    duration_days: Optional[int] = None
    departure_date: Optional[str] = None
    group_size: Optional[int] = None
    category_pref: Optional[str] = None
    interests: list[str] = []


class NeedExtraction(BaseModel):
    """Structured needs extracted from user input."""
    destination_preference: Optional[str] = None
    budget_range: Optional[dict] = None
    duration_preference: Optional[str] = None
    group_composition: Optional[str] = None
    season: Optional[str] = None
    category: Optional[str] = None
    interests: list[str] = []
    special_requirements: list[str] = []


class RecommendResult(BaseModel):
    """A single recommendation result."""
    trip_id: str
    title: str
    destination: str
    duration_days: int
    price_adult: Optional[float]
    highlights: list[str]
    cover_image_url: Optional[str]
    match_score: float
    match_reasons: list[str]
    match_tags: list[str]
    category: str


class RecommendResponse(BaseModel):
    """Full recommendation response."""
    query: str
    extracted_needs: Optional[NeedExtraction]
    recommendations: list[RecommendResult]
    explanation: str
    profile_used: bool = False


class SupportQuery(BaseModel):
    """Trip support query from user."""
    order_id: Optional[str] = None
    trip_id: Optional[str] = None
    query: str
    query_type: str = Field(
        default="general",
        description="pre_trip / in_trip / post_trip / general"
    )


class SupportResponse(BaseModel):
    """AI support response."""
    query: str
    answer: str
    relevant_info: dict = {}
    actions: list[dict] = []
    query_type: str
