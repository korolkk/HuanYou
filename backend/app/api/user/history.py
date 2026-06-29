"""User trip history and statistics API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.customer import Customer
from app.models.trip import Trip
from app.models.order import Order
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("/stats")
async def travel_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get user travel statistics."""
    # Total orders
    total_orders = (await db.execute(
        select(func.count()).select_from(Order).where(Order.customer_id == current_user.id)
    )).scalar() or 0

    # Completed orders
    completed_orders = (await db.execute(
        select(func.count()).select_from(Order).where(
            Order.customer_id == current_user.id,
            Order.status == "completed",
        )
    )).scalar() or 0

    # Total spend
    total_spend = (await db.execute(
        select(func.sum(Order.total_price)).where(
            Order.customer_id == current_user.id,
            Order.status.in_(["completed", "in_trip"]),
        )
    )).scalar() or 0

    # Get distinct destinations visited
    orders = (await db.execute(
        select(Order).where(
            Order.customer_id == current_user.id,
            Order.status == "completed",
        )
    )).scalars().all()

    destinations = set()
    for o in orders:
        trip_result = await db.execute(select(Trip).where(Trip.id == o.trip_id))
        trip = trip_result.scalar_one_or_none()
        if trip:
            destinations.add(trip.destination)

    return {
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "total_spend": float(total_spend or 0),
        "destinations_visited": len(destinations),
        "destinations_list": list(destinations),
    }


@router.get("/timeline")
async def travel_timeline(
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get user's travel timeline (chronological list of all trips)."""
    result = await db.execute(
        select(Order)
        .where(Order.customer_id == current_user.id)
        .order_by(Order.departure_date.desc().nullslast())
    )
    orders = result.scalars().all()

    timeline = []
    for o in orders:
        trip_result = await db.execute(select(Trip).where(Trip.id == o.trip_id))
        trip = trip_result.scalar_one_or_none()

        timeline.append({
            "order_id": str(o.id),
            "order_code": o.order_code,
            "trip_title": trip.title if trip else "",
            "trip_destination": trip.destination if trip else "",
            "departure_date": o.departure_date.isoformat() if o.departure_date else None,
            "duration_days": trip.duration_days if trip else None,
            "status": o.status,
            "total_price": o.total_price,
            "cover_image_url": trip.cover_image_url if trip else None,
            "created_at": o.created_at.isoformat() if o.created_at else "",
        })

    return {"timeline": timeline, "count": len(timeline)}
