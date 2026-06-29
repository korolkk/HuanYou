"""FastAPI application entry point for HuanYou (欢游) AI Travel Assistant."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown events."""
    settings = get_settings()
    # Startup
    from app.models.base import engine
    # Verify DB connection (tables created via Alembic migrations)
    yield
    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="旅游AI助手 — 行程管理、智能推荐、短视频文案、客户画像、全流程服务",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from app.api.auth import router as auth_router
    from app.api.shop.trips import router as shop_trips_router
    from app.api.shop.scripts import router as shop_scripts_router
    from app.api.shop.customers import router as shop_customers_router
    from app.api.shop.import_ import router as shop_import_router
    from app.api.user.recommend import router as user_recommend_router
    from app.api.user.support import router as user_support_router
    from app.api.user.orders import router as user_orders_router
    from app.api.user.history import router as user_history_router
    from app.api.agent_chat import router as agent_chat_router

    app.include_router(auth_router, prefix="/api/auth", tags=["认证"])
    app.include_router(shop_trips_router, prefix="/api/shop/trips", tags=["店长-行程管理"])
    app.include_router(shop_scripts_router, prefix="/api/shop/scripts", tags=["店长-脚本管理"])
    app.include_router(shop_customers_router, prefix="/api/shop/customers", tags=["店长-客户管理"])
    app.include_router(shop_import_router, prefix="/api/shop/import", tags=["店长-文件导入"])
    app.include_router(user_recommend_router, prefix="/api/user/recommend", tags=["用户-智能推荐"])
    app.include_router(user_support_router, prefix="/api/user/support", tags=["用户-行程支持"])
    app.include_router(user_orders_router, prefix="/api/user/orders", tags=["用户-订单管理"])
    app.include_router(user_history_router, prefix="/api/user/history", tags=["用户-历史行程"])
    app.include_router(agent_chat_router, prefix="/api/agent", tags=["Agent对话"])

    @app.get("/api/health", tags=["系统"])
    async def health_check():
        return {"status": "healthy", "service": settings.PROJECT_NAME}

    return app


app = create_app()
