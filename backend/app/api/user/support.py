"""User trip support API routes.

AI-powered pre-trip, in-trip, and post-trip support.
Fully implemented in Phase 2/3.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.customer import Customer
from app.schemas.recommendation import SupportQuery, SupportResponse
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("", response_model=SupportResponse)
async def trip_support(
    data: SupportQuery,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """AI trip support — covers pre-trip, in-trip, and post-trip queries.

    The TripSupportAgent will handle:
    - Pre-trip: booking info, weather, packing list, visa, meeting points
    - In-trip: weather checks, attraction guides, food recs, emergency contacts
    - Post-trip: feedback, complaints, document retrieval, next trip suggestions

    Will be fully implemented in Phase 2 with TripSupportAgent.
    """
    raise HTTPException(
        status_code=501,
        detail="行程智能客服功能将在Phase 2实现，届时将集成TripSupportAgent覆盖全流程服务",
    )
