"""Shop owner customer management API routes.

AI-powered customer profile analysis will be implemented in Phase 3.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.customer import Customer, CustomerProfile
from app.models.order import Order
from app.schemas.customer import (
    CustomerListResponse, CustomerDetailResponse, CustomerProfileResponse,
    ProfileRefreshRequest,
)
from app.utils.auth import get_current_user, get_shop_owner

router = APIRouter()


@router.get("", response_model=dict)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str = Query(None),
    status: str = Query(None),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """List all customers with basic profile info."""
    query = select(Customer)

    if role:
        query = query.where(Customer.role == role)
    if status:
        query = query.where(Customer.status == status)
    if search:
        query = query.where(
            Customer.name.ilike(f"%{search}%") | Customer.phone.ilike(f"%{search}%")
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(Customer.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    customers = result.scalars().all()

    items = []
    for c in customers:
        # Count orders
        order_count = (await db.execute(
            select(func.count()).select_from(Order).where(Order.customer_id == c.id)
        )).scalar()

        profile = None
        if c.profile:
            profile = CustomerProfileResponse(
                id=str(c.profile.id),
                customer_id=str(c.profile.customer_id),
                age_group=c.profile.age_group,
                city=c.profile.city,
                preferred_destinations=c.profile.preferred_destinations or [],
                preferred_categories=c.profile.preferred_categories or [],
                budget_range_min=c.profile.budget_range_min,
                budget_range_max=c.profile.budget_range_max,
                preferred_duration_days=c.profile.preferred_duration_days,
                preferred_season=c.profile.preferred_season,
                travel_style=c.profile.travel_style,
                booking_frequency=c.profile.booking_frequency,
                interest_tags=c.profile.interest_tags or [],
                special_requirements=c.profile.special_requirements or [],
                profile_summary=c.profile.profile_summary,
                created_at=c.profile.created_at.isoformat() if c.profile.created_at else "",
                updated_at=c.profile.updated_at.isoformat() if c.profile.updated_at else "",
            )

        items.append(CustomerListResponse(
            id=str(c.id),
            phone=c.phone,
            name=c.name,
            role=c.role,
            status=c.status,
            created_at=c.created_at.isoformat() if c.created_at else "",
            order_count=order_count or 0,
            profile=profile,
        ))

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Get full customer detail."""
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="客户不存在")

    order_count = (await db.execute(
        select(func.count()).select_from(Order).where(Order.customer_id == c.id)
    )).scalar()

    profile = None
    if c.profile:
        profile = CustomerProfileResponse(
            id=str(c.profile.id),
            customer_id=str(c.profile.customer_id),
            age_group=c.profile.age_group,
            city=c.profile.city,
            preferred_destinations=c.profile.preferred_destinations or [],
            preferred_categories=c.profile.preferred_categories or [],
            budget_range_min=c.profile.budget_range_min,
            budget_range_max=c.profile.budget_range_max,
            preferred_duration_days=c.profile.preferred_duration_days,
            preferred_season=c.profile.preferred_season,
            travel_style=c.profile.travel_style,
            booking_frequency=c.profile.booking_frequency,
            interest_tags=c.profile.interest_tags or [],
            special_requirements=c.profile.special_requirements or [],
            profile_summary=c.profile.profile_summary,
            created_at=c.profile.created_at.isoformat() if c.profile.created_at else "",
            updated_at=c.profile.updated_at.isoformat() if c.profile.updated_at else "",
        )

    return CustomerDetailResponse(
        id=str(c.id),
        phone=c.phone,
        name=c.name,
        role=c.role,
        status=c.status,
        email=c.email,
        gender=c.gender,
        birth_date=c.birth_date.isoformat() if c.birth_date else None,
        wechat_id=c.wechat_id,
        emergency_contact=c.emergency_contact,
        emergency_phone=c.emergency_phone,
        created_at=c.created_at.isoformat() if c.created_at else "",
        updated_at=c.updated_at.isoformat() if c.updated_at else "",
        order_count=order_count or 0,
        profile=profile,
    )


@router.post("/{customer_id}/refresh-profile")
async def refresh_profile(
    customer_id: str,
    data: ProfileRefreshRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Trigger AI-powered customer profile refresh.

    Will be fully implemented in Phase 3 with CustomerProfileAgent.
    """
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    c = result.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="客户不存在")

    raise HTTPException(
        status_code=501,
        detail="AI客户画像刷新功能将在Phase 3实现，届时将集成CustomerProfileAgent和Mem0",
    )
