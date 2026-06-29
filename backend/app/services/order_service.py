"""Order business logic service."""

from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order


class OrderService:
    """Service for order-related business operations."""

    VALID_TRANSITIONS = {
        "inquiry": ["reserved", "cancelled"],
        "reserved": ["confirmed", "cancelled"],
        "confirmed": ["paid", "cancelled"],
        "paid": ["pre_trip", "refunded", "cancelled"],
        "pre_trip": ["in_trip", "cancelled"],
        "in_trip": ["completed"],
        "completed": [],
        "cancelled": [],
        "refunded": [],
    }

    @staticmethod
    async def transition_status(
        db: AsyncSession, order: Order, new_status: str,
    ) -> Order:
        """Transition order to a new status with validation.

        Automatically sets the appropriate timestamp for the new status.
        """
        valid_next = OrderService.VALID_TRANSITIONS.get(order.status, [])
        if new_status not in valid_next:
            raise ValueError(
                f"订单状态不能从 {order.status} 转换到 {new_status}。"
                f"允许的状态: {valid_next}"
            )

        order.status = new_status
        now = datetime.now(timezone.utc)

        timestamp_map = {
            "reserved": "reserved_at",
            "confirmed": "confirmed_at",
            "paid": "paid_at",
            "pre_trip": None,
            "in_trip": "departed_at",
            "completed": "completed_at",
            "cancelled": "cancelled_at",
        }

        attr = timestamp_map.get(new_status)
        if attr:
            setattr(order, attr, now)

        await db.flush()
        return order

    @staticmethod
    async def generate_order_code(db: AsyncSession) -> str:
        """Generate a unique order code: HY + date + sequence."""
        date_str = datetime.now().strftime("%Y%m%d")
        count = (await db.execute(
            select(func.count()).select_from(Order).where(
                Order.order_code.like(f"HY{date_str}%")
            )
        )).scalar() or 0
        return f"HY{date_str}{count + 1:04d}"

    @staticmethod
    async def get_orders_by_status(
        db: AsyncSession, customer_id: str, status: Optional[str] = None,
    ) -> list[Order]:
        """Get orders for a customer, optionally filtered by status."""
        query = select(Order).where(Order.customer_id == customer_id)
        if status:
            query = query.where(Order.status == status)
        query = query.order_by(Order.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())
