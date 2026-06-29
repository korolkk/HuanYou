"""Shop owner trip management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.customer import Customer
from app.models.trip import Trip, TripSchedule
from app.schemas.trip import (
    TripCreate, TripUpdate, TripListResponse, TripDetailResponse,
    TripSummaryRequest, ScheduleCreate, ScheduleResponse,
)
from app.utils.auth import get_current_user, get_shop_owner

router = APIRouter()


@router.get("", response_model=dict)
async def list_trips(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    destination: str = Query(None),
    category: str = Query(None),
    status: str = Query("active"),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """List all trips with filtering and pagination."""
    query = select(Trip)

    if status:
        query = query.where(Trip.status == status)
    if destination:
        query = query.where(Trip.destination.ilike(f"%{destination}%"))
    if category:
        query = query.where(Trip.category == category)
    if search:
        query = query.where(
            Trip.title.ilike(f"%{search}%") | Trip.destination.ilike(f"%{search}%")
        )

    # Total count
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Trip.updated_at.desc())
    result = await db.execute(query)
    trips = result.scalars().all()

    return {
        "items": [
            TripListResponse(
                id=str(t.id),
                code=t.code,
                title=t.title,
                subtitle=t.subtitle,
                destination=t.destination,
                category=t.category,
                duration_days=t.duration_days,
                price_adult=t.price_adult,
                cover_image_url=t.cover_image_url,
                summary=t.summary,
                highlights=t.highlights or [],
                is_featured=t.is_featured,
                status=t.status,
                created_at=t.created_at.isoformat() if t.created_at else "",
            )
            for t in trips
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{trip_id}", response_model=TripDetailResponse)
async def get_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get full trip detail with schedules."""
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id).options(selectinload(Trip.schedules))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    return TripDetailResponse(
        id=str(trip.id),
        code=trip.code,
        title=trip.title,
        subtitle=trip.subtitle,
        destination=trip.destination,
        destinations_detail=trip.destinations_detail or [],
        country=trip.country,
        province=trip.province,
        city=trip.city,
        category=trip.category,
        duration_days=trip.duration_days,
        duration_nights=trip.duration_nights,
        departure_city=trip.departure_city,
        best_season=trip.best_season,
        price_adult=trip.price_adult,
        price_child=trip.price_child,
        price_infant=trip.price_infant,
        single_room_supplement=trip.single_room_supplement,
        price_includes=trip.price_includes or [],
        price_excludes=trip.price_excludes or [],
        summary=trip.summary,
        highlights=trip.highlights or [],
        recommendation_reasons=trip.recommendation_reasons or [],
        detailed_description=trip.detailed_description,
        group_size_min=trip.group_size_min,
        group_size_max=trip.group_size_max,
        departure_dates=trip.departure_dates or [],
        cover_image_url=trip.cover_image_url,
        image_urls=trip.image_urls or [],
        brochure_url=trip.brochure_url,
        is_featured=trip.is_featured,
        status=trip.status,
        created_at=trip.created_at.isoformat() if trip.created_at else "",
        updated_at=trip.updated_at.isoformat() if trip.updated_at else "",
        schedules=[
            ScheduleResponse(
                id=str(s.id),
                trip_id=str(s.trip_id),
                day_number=s.day_number,
                theme=s.theme,
                schedule_type=s.schedule_type,
                time_start=s.time_start,
                time_end=s.time_end,
                location=s.location,
                activity=s.activity,
                description=s.description,
                meal_included=s.meal_included,
                hotel_name=s.hotel_name,
                hotel_stars=s.hotel_stars,
                hotel_description=s.hotel_description,
                transport_type=s.transport_type,
                transport_detail=s.transport_detail,
                tips=s.tips,
                image_urls=s.image_urls or [],
                sort_order=s.sort_order,
            )
            for s in (trip.schedules or [])
        ],
    )


@router.post("", response_model=TripDetailResponse, status_code=201)
async def create_trip(
    data: TripCreate,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Create a new trip with schedules."""
    # Check unique code
    existing = await db.execute(select(Trip).where(Trip.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"行程编号 {data.code} 已存在")

    trip = Trip(
        code=data.code,
        title=data.title,
        subtitle=data.subtitle,
        destination=data.destination,
        destinations_detail=data.destinations_detail,
        country=data.country,
        province=data.province,
        city=data.city,
        category=data.category,
        duration_days=data.duration_days,
        duration_nights=data.duration_nights,
        departure_city=data.departure_city,
        best_season=data.best_season,
        price_adult=data.price_adult,
        price_child=data.price_child,
        price_infant=data.price_infant,
        single_room_supplement=data.single_room_supplement,
        price_includes=data.price_includes,
        price_excludes=data.price_excludes,
        detailed_description=data.detailed_description,
        group_size_min=data.group_size_min,
        group_size_max=data.group_size_max,
        departure_dates=data.departure_dates,
        cover_image_url=data.cover_image_url,
        image_urls=data.image_urls,
        is_featured=data.is_featured,
        created_by=current_user.id,
    )
    db.add(trip)
    await db.flush()

    # Create schedules
    for s in data.schedules:
        schedule = TripSchedule(
            trip_id=trip.id,
            day_number=s.day_number,
            theme=s.theme,
            schedule_type=s.schedule_type,
            time_start=s.time_start,
            time_end=s.time_end,
            location=s.location,
            activity=s.activity,
            description=s.description,
            meal_included=s.meal_included,
            hotel_name=s.hotel_name,
            hotel_stars=s.hotel_stars,
            hotel_description=s.hotel_description,
            transport_type=s.transport_type,
            transport_detail=s.transport_detail,
            tips=s.tips,
            image_urls=s.image_urls,
            sort_order=s.sort_order,
        )
        db.add(schedule)

    await db.flush()

    # Return the created trip
    result = await db.execute(
        select(Trip).where(Trip.id == trip.id)
    )
    trip = result.scalar_one()
    schedules = (await db.execute(
        select(TripSchedule).where(TripSchedule.trip_id == trip.id).order_by(TripSchedule.sort_order)
    )).scalars().all()

    return TripDetailResponse(
        id=str(trip.id),
        code=trip.code,
        title=trip.title,
        subtitle=trip.subtitle,
        destination=trip.destination,
        destinations_detail=trip.destinations_detail or [],
        country=trip.country,
        province=trip.province,
        city=trip.city,
        category=trip.category,
        duration_days=trip.duration_days,
        duration_nights=trip.duration_nights,
        departure_city=trip.departure_city,
        best_season=trip.best_season,
        price_adult=trip.price_adult,
        price_child=trip.price_child,
        price_infant=trip.price_infant,
        single_room_supplement=trip.single_room_supplement,
        price_includes=trip.price_includes or [],
        price_excludes=trip.price_excludes or [],
        summary=trip.summary,
        highlights=trip.highlights or [],
        recommendation_reasons=trip.recommendation_reasons or [],
        detailed_description=trip.detailed_description,
        group_size_min=trip.group_size_min,
        group_size_max=trip.group_size_max,
        departure_dates=trip.departure_dates or [],
        cover_image_url=trip.cover_image_url,
        image_urls=trip.image_urls or [],
        brochure_url=trip.brochure_url,
        is_featured=trip.is_featured,
        status=trip.status,
        created_at=trip.created_at.isoformat() if trip.created_at else "",
        updated_at=trip.updated_at.isoformat() if trip.updated_at else "",
        schedules=[
            ScheduleResponse(
                id=str(s.id),
                trip_id=str(s.trip_id),
                day_number=s.day_number,
                theme=s.theme,
                schedule_type=s.schedule_type,
                time_start=s.time_start,
                time_end=s.time_end,
                location=s.location,
                activity=s.activity,
                description=s.description,
                meal_included=s.meal_included,
                hotel_name=s.hotel_name,
                hotel_stars=s.hotel_stars,
                hotel_description=s.hotel_description,
                transport_type=s.transport_type,
                transport_detail=s.transport_detail,
                tips=s.tips,
                image_urls=s.image_urls or [],
                sort_order=s.sort_order,
            )
            for s in schedules
        ],
    )


@router.put("/{trip_id}", response_model=TripDetailResponse)
async def update_trip(
    trip_id: str,
    data: TripUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Update an existing trip."""
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id).options(selectinload(Trip.schedules))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(trip, field, value)

    await db.flush()

    # Return updated trip (reuse get logic)
    return await get_trip(trip_id, db, current_user)


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(
    trip_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Soft-delete a trip."""
    result = await db.execute(
        select(Trip).where(Trip.id == trip_id).options(selectinload(Trip.schedules))
    )
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail="行程不存在")
    trip.status = "archived"
    await db.flush()
