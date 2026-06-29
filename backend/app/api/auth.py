"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import get_db
from app.models.customer import Customer
from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    UserInfo, UserUpdate, ChangePassword,
)
from app.utils.auth import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user,
)

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if phone already exists
    result = await db.execute(select(Customer).where(Customer.phone == data.phone))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该手机号已注册",
        )

    user = Customer(
        phone=data.phone,
        name=data.name,
        role=data.role,
        email=data.email,
        gender=data.gender,
        birth_date=data.birth_date,
    )
    # Store hashed password in a separate auth table (simplified: store on user)
    # In production, use a dedicated auth table
    user.password_hash = get_password_hash(data.password)

    db.add(user)
    await db.flush()

    # Generate tokens
    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(
            id=str(user.id),
            phone=user.phone,
            name=user.name,
            role=user.role,
            email=user.email,
            gender=user.gender,
        ),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with phone and password."""
    result = await db.execute(select(Customer).where(Customer.phone == data.phone))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
        )

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="手机号或密码错误",
        )

    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )

    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(
            id=str(user.id),
            phone=user.phone,
            name=user.name,
            role=user.role,
            email=user.email,
            gender=user.gender,
        ),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh an access token using a refresh token."""
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新凭证",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(Customer).where(Customer.id == user_id))
    user = result.scalar_one_or_none()

    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已禁用",
        )

    token_data = {"sub": str(user.id), "role": user.role}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserInfo(
            id=str(user.id),
            phone=user.phone,
            name=user.name,
            role=user.role,
            email=user.email,
            gender=user.gender,
        ),
    )


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: Customer = Depends(get_current_user)):
    """Get current user info."""
    return UserInfo(
        id=str(current_user.id),
        phone=current_user.phone,
        name=current_user.name,
        role=current_user.role,
        email=current_user.email,
        gender=current_user.gender,
    )


@router.put("/me", response_model=UserInfo)
async def update_me(
    data: UserUpdate,
    current_user: Customer = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.flush()
    return UserInfo(
        id=str(current_user.id),
        phone=current_user.phone,
        name=current_user.name,
        role=current_user.role,
        email=current_user.email,
        gender=current_user.gender,
    )


@router.post("/change-password")
async def change_password(
    data: ChangePassword,
    current_user: Customer = Depends(get_current_user),
):
    """Change password."""
    if not current_user.password_hash:
        raise HTTPException(status_code=400, detail="未设置密码")
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = get_password_hash(data.new_password)
    return {"message": "密码修改成功"}
