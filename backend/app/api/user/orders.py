"""User order management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.customer import Customer
from app.models.trip import Trip
from app.models.order import Order
from app.models.feedback import Feedback
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderListResponse, OrderDetailResponse,
    FeedbackCreate, FeedbackResponse,
)
from app.utils.auth import get_current_user

router = APIRouter()


@router.get("", response_model=dict)
async def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """List current user's orders."""
    query = select(Order).where(Order.customer_id == current_user.id)

    if status:
        query = query.where(Order.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(Order.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    orders = result.scalars().all()

    items = []
    for o in orders:
        trip_result = await db.execute(select(Trip).where(Trip.id == o.trip_id))
        trip = trip_result.scalar_one_or_none()
        items.append(OrderListResponse(
            id=str(o.id),
            order_code=o.order_code,
            trip_title=trip.title if trip else "",
            trip_destination=trip.destination if trip else "",
            departure_date=o.departure_date.isoformat() if o.departure_date else None,
            num_adults=o.num_adults,
            num_children=o.num_children,
            total_price=o.total_price,
            status=o.status,
            payment_status=o.payment_status,
            created_at=o.created_at.isoformat() if o.created_at else "",
        ))

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=OrderDetailResponse, status_code=201)
async def create_order(
    data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Create a new order for a trip."""
    # Verify trip exists and is active
    trip_result = await db.execute(
        select(Trip).where(Trip.id == data.trip_id, Trip.status == "active")
    )
    trip = trip_result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在或已下架")

    # Generate order code
    from datetime import datetime
    date_str = datetime.now().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count()).select_from(Order).where(Order.order_code.like(f"HY{date_str}%"))
    )
    count = count_result.scalar() or 0
    order_code = f"HY{date_str}{count + 1:04d}"

    # Calculate price
    total_price = (
        (trip.price_adult or 0) * data.num_adults +
        (trip.price_child or 0) * data.num_children +
        (trip.price_infant or 0) * data.num_infants
    )

    order = Order(
        order_code=order_code,
        customer_id=current_user.id,
        trip_id=data.trip_id,
        departure_date=data.departure_date,
        num_adults=data.num_adults,
        num_children=data.num_children,
        num_infants=data.num_infants,
        total_price=total_price,
        participants=data.participants,
        status="reserved",
    )
    db.add(order)
    await db.flush()

    return OrderDetailResponse(
        id=str(order.id),
        order_code=order.order_code,
        trip_id=str(order.trip_id),
        trip_title=trip.title,
        trip_destination=trip.destination,
        departure_date=order.departure_date.isoformat() if order.departure_date else None,
        num_adults=order.num_adults,
        num_children=order.num_children,
        num_infants=order.num_infants,
        total_price=order.total_price,
        paid_amount=order.paid_amount,
        discount_amount=order.discount_amount,
        participants=order.participants,
        status=order.status,
        payment_status=order.payment_status,
        contract_url=order.contract_url,
        insurance_url=order.insurance_url,
        reserved_at=order.reserved_at.isoformat() if order.reserved_at else None,
        confirmed_at=None,
        paid_at=None,
        departed_at=None,
        completed_at=None,
        cancelled_at=None,
        created_at=order.created_at.isoformat() if order.created_at else "",
        updated_at=order.updated_at.isoformat() if order.updated_at else "",
    )


@router.get("/{order_id}", response_model=OrderDetailResponse)
async def get_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get order detail."""
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.customer_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    trip_result = await db.execute(select(Trip).where(Trip.id == order.trip_id))
    trip = trip_result.scalar_one_or_none()

    return OrderDetailResponse(
        id=str(order.id),
        order_code=order.order_code,
        trip_id=str(order.trip_id),
        trip_title=trip.title if trip else "",
        trip_destination=trip.destination if trip else "",
        departure_date=order.departure_date.isoformat() if order.departure_date else None,
        num_adults=order.num_adults,
        num_children=order.num_children,
        num_infants=order.num_infants,
        total_price=order.total_price,
        paid_amount=order.paid_amount,
        discount_amount=order.discount_amount,
        participants=order.participants,
        status=order.status,
        payment_status=order.payment_status,
        contract_url=order.contract_url,
        insurance_url=order.insurance_url,
        reserved_at=order.reserved_at.isoformat() if order.reserved_at else None,
        confirmed_at=order.confirmed_at.isoformat() if order.confirmed_at else None,
        paid_at=order.paid_at.isoformat() if order.paid_at else None,
        departed_at=order.departed_at.isoformat() if order.departed_at else None,
        completed_at=order.completed_at.isoformat() if order.completed_at else None,
        cancelled_at=order.cancelled_at.isoformat() if order.cancelled_at else None,
        created_at=order.created_at.isoformat() if order.created_at else "",
        updated_at=order.updated_at.isoformat() if order.updated_at else "",
    )


@router.post("/{order_id}/feedback", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    order_id: str,
    data: FeedbackCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Submit feedback for a completed trip."""
    # Verify order belongs to user and is completed
    result = await db.execute(
        select(Order).where(Order.id == order_id, Order.customer_id == current_user.id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "completed":
        raise HTTPException(status_code=400, detail="只能对已完成的行程进行评价")

    # Check duplicate feedback
    existing = await db.execute(
        select(Feedback).where(Feedback.order_id == order_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="您已对该行程进行过评价")

    feedback = Feedback(
        order_id=order_id,
        customer_id=current_user.id,
        rating_overall=data.rating_overall,
        rating_guide=data.rating_guide,
        rating_accommodation=data.rating_accommodation,
        rating_transport=data.rating_transport,
        rating_food=data.rating_food,
        rating_itinerary=data.rating_itinerary,
        positive_points=data.positive_points,
        negative_points=data.negative_points,
        suggestions=data.suggestions,
    )
    db.add(feedback)
    await db.flush()

    return FeedbackResponse(
        id=str(feedback.id),
        order_id=str(feedback.order_id),
        rating_overall=feedback.rating_overall,
        positive_points=feedback.positive_points,
        negative_points=feedback.negative_points,
        suggestions=feedback.suggestions,
        status=feedback.status,
        staff_response=feedback.staff_response,
        created_at=feedback.created_at.isoformat() if feedback.created_at else "",
    )
