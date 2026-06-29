"""Trip business logic service."""

from typing import Optional
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip, TripSchedule


class TripService:
    """Service for trip-related business operations."""

    @staticmethod
    async def search_trips(
        db: AsyncSession,
        destination: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        duration_days: Optional[int] = None,
        search: Optional[str] = None,
        status: str = "active",
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """Search trips with multiple filters."""
        query = select(Trip).where(Trip.status == status)

        if destination:
            query = query.where(Trip.destination.ilike(f"%{destination}%"))
        if category:
            query = query.where(Trip.category == category)
        if max_price:
            query = query.where(Trip.price_adult <= max_price)
        if min_price:
            query = query.where(Trip.price_adult >= min_price)
        if duration_days:
            query = query.where(Trip.duration_days == duration_days)
        if search:
            query = query.where(
                or_(
                    Trip.title.ilike(f"%{search}%"),
                    Trip.destination.ilike(f"%{search}%"),
                    Trip.summary.ilike(f"%{search}%"),
                )
            )

        total = (await db.execute(
            select(func.count()).select_from(query.subquery())
        )).scalar()

        query = query.order_by(Trip.is_featured.desc(), Trip.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)

        return {
            "items": result.scalars().all(),
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    @staticmethod
    async def get_full_trip(db: AsyncSession, trip_id: str) -> Optional[Trip]:
        """Get trip with schedules eagerly loaded."""
        result = await db.execute(
            select(Trip).where(Trip.id == trip_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_featured_trips(db: AsyncSession, limit: int = 6) -> list[Trip]:
        """Get featured/ highlighted trips."""
        result = await db.execute(
            select(Trip)
            .where(Trip.status == "active", Trip.is_featured == True)  # noqa: E712
            .limit(limit)
        )
        return list(result.scalars().all())
