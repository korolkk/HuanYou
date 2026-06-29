"""User trip recommendation API routes.

Intelligent recommendation powered by RecommendationAgent + RAG.
Fully implemented in Phase 2.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.customer import Customer
from app.schemas.recommendation import RecommendRequest, RecommendResponse
from app.utils.auth import get_current_user

router = APIRouter()


@router.post("", response_model=RecommendResponse)
async def recommend_trips(
    data: RecommendRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get AI-powered trip recommendations based on user requirements.

    This is the core recommendation endpoint that will:
    1. Extract structured needs from natural language query
    2. Retrieve user profile and past preferences (Mem0 + DB)
    3. Search trips via pgvector hybrid RAG
    4. Filter by budget, duration, preferences
    5. Rank and explain recommendations with LLM

    Will be fully implemented in Phase 2 with RecommendationAgent.
    """
    raise HTTPException(
        status_code=501,
        detail="智能推荐功能将在Phase 2实现，届时将集成RecommendationAgent和RAG检索pipeline",
    )
