"""All Pydantic schemas."""

from app.schemas.auth import (
    UserRegister, UserLogin, TokenResponse, RefreshTokenRequest,
    UserInfo, UserUpdate, ChangePassword,
)
from app.schemas.trip import (
    TripCreate, TripUpdate, TripListResponse, TripDetailResponse,
    TripSummaryRequest, ScheduleCreate, ScheduleResponse,
)
from app.schemas.script import (
    ScriptGenerateRequest, ScriptPolishRequest, ScriptEvaluateResponse,
    ScriptSegment, ScriptResponse, ScriptListResponse,
    ScriptExportRequest, ScriptExportResponse,
)
from app.schemas.customer import (
    CustomerListResponse, CustomerDetailResponse, CustomerProfileResponse,
    CustomerSegmentResponse, ProfileRefreshRequest,
)
from app.schemas.order import (
    OrderCreate, OrderUpdate, OrderListResponse, OrderDetailResponse,
    FeedbackCreate, FeedbackResponse,
)
from app.schemas.recommendation import (
    RecommendRequest, RecommendResult, RecommendResponse,
    NeedExtraction, SupportQuery, SupportResponse,
)
