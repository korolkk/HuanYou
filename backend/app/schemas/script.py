"""Video script schemas — generation, polish, evaluation, CapCut export."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Segment ──

class ScriptSegment(BaseModel):
    """A single segment in the script timeline."""
    timecode_start: str = ""        # "00:00"
    timecode_end: str = ""          # "00:15"
    duration_seconds: int = 15
    segment_type: str = "highlights"  # hook / highlights / detail / cta
    text: str = ""
    image_ref: Optional[str] = None
    image_keyword: Optional[str] = None
    bgm_suggestion: Optional[str] = None


# ── Generate ──

class ScriptGenerateRequest(BaseModel):
    """Request to generate a video script."""
    trip_id: str
    platform: str = Field(default="抖音")
    duration_seconds: int = Field(default=300, ge=60, le=600)
    style: Optional[str] = Field(default="活泼", description="活泼/文艺/专业/感性")
    regenerate: bool = False


# ── Polish ──

class ScriptPolishRequest(BaseModel):
    """Request to polish an existing script."""
    focus_areas: list[str] = Field(
        default=["engagement", "transitions", "sensory_language", "hooks"]
    )
    target_segment_index: Optional[int] = None


# ── Evaluate ──

class ScriptEvaluateResponse(BaseModel):
    """Quality evaluation result."""
    quality_score: float
    engagement_score: float
    accuracy_score: float
    completeness_score: float
    passed: bool
    feedback: str


# ── Export ──

class ScriptExportRequest(BaseModel):
    """Request to export script as CapCut draft."""
    include_images: bool = True
    resolution: str = Field(default="1080p", description="720p / 1080p")


class ScriptExportResponse(BaseModel):
    """CapCut export result."""
    draft_id: str
    draft_name: str
    file_size_bytes: int
    platform_style: dict
    instructions: str


# ── Response ──

class ScriptResponse(BaseModel):
    """Full script detail."""
    id: str
    trip_id: str
    title: Optional[str] = None
    platform: str
    duration_seconds: int
    style: Optional[str] = None
    script_content: str
    segments: list[ScriptSegment] = []
    script_json: Optional[dict] = None
    hook_text: Optional[str] = None
    highlights_text: Optional[str] = None
    detail_text: Optional[str] = None
    cta_text: Optional[str] = None
    image_assignments: Optional[dict] = None
    quality_score: Optional[float] = None
    engagement_score: Optional[float] = None
    accuracy_score: Optional[float] = None
    completeness_score: Optional[float] = None
    generation_version: int = 1
    polish_iterations: int = 0
    status: str = "draft"
    capcut_draft_id: Optional[str] = None
    export_status: str = "none"
    exported_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    class Config:
        from_attributes = True


class ScriptListResponse(BaseModel):
    """Script list item."""
    id: str
    trip_id: str
    title: Optional[str] = None
    platform: str
    duration_seconds: int
    quality_score: Optional[float] = None
    status: str
    export_status: str = "none"
    created_at: str = ""

    class Config:
        from_attributes = True
