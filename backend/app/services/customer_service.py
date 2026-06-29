"""Customer business logic service."""

from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.customer import Customer, CustomerProfile
from app.models.order import Order
from app.models.trip import Trip


class CustomerService:
    """Service for customer-related business operations."""

    @staticmethod
    async def get_or_create_profile(
        db: AsyncSession, customer_id: str,
    ) -> CustomerProfile:
        """Get existing profile or create a new one."""
        result = await db.execute(
            select(CustomerProfile).where(
                CustomerProfile.customer_id == customer_id
            )
        )
        profile = result.scalar_one_or_none()

        if not profile:
            profile = CustomerProfile(customer_id=customer_id)
            db.add(profile)
            await db.flush()

        return profile

    @staticmethod
    async def calculate_customer_stats(
        db: AsyncSession, customer_id: str,
    ) -> dict:
        """Calculate summary statistics for a customer."""
        orders_result = await db.execute(
            select(Order).where(Order.customer_id == customer_id)
        )
        orders = orders_result.scalars().all()

        total_orders = len(orders)
        completed = sum(1 for o in orders if o.status == "completed")
        total_spend = sum(o.total_price or 0 for o in orders)

        destinations = set()
        total_days = 0
        for o in orders:
            if o.status in ("completed", "in_trip"):
                trip_result = await db.execute(
                    select(Trip).where(Trip.id == o.trip_id)
                )
                trip = trip_result.scalar_one_or_none()
                if trip:
                    destinations.add(trip.destination)
                    total_days += trip.duration_days

        return {
            "total_orders": total_orders,
            "completed_orders": completed,
            "total_spend": float(total_spend),
            "destinations_visited": len(destinations),
            "destinations_list": list(destinations),
            "total_travel_days": total_days,
        }

    @staticmethod
    async def segment_customers(db: AsyncSession) -> list[dict]:
        """Segment customers into groups based on behavior."""
        # Get all customers with order counts
        segments = {
            "high_value": {"name": "高价值客户", "description": "消费5000以上且≥2次", "count": 0},
            "regular": {"name": "常客", "description": "消费1000-5000或多次下单", "count": 0},
            "new": {"name": "新客户", "description": "只有1次咨询或订单", "count": 0},
            "dormant": {"name": "沉睡客户", "description": "6个月以上无订单", "count": 0},
        }

        # TODO: Implement actual segmentation logic with SQL
        return list(segments.values())
