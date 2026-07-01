"""Shop owner script management API — generate, polish, evaluate, CapCut export."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.models.base import get_db
from app.models.customer import Customer
from app.models.trip import Trip
from app.models.video_script import VideoScript
from app.schemas.script import (
    ScriptGenerateRequest, ScriptPolishRequest, ScriptEvaluateResponse,
    ScriptSegment, ScriptResponse, ScriptListResponse,
    ScriptExportRequest, ScriptExportResponse,
)
from app.utils.auth import get_current_user, get_shop_owner
from app.services.script_service import ScriptGenerationService
from app.services.capcut_service import CapCutExportService

router = APIRouter()


def _script_to_response(s: VideoScript) -> ScriptResponse:
    """Convert VideoScript model to ScriptResponse."""
    segments = []
    if s.script_json and "segments" in s.script_json:
        segments = [ScriptSegment(**seg) for seg in s.script_json["segments"]]
    return ScriptResponse(
        id=str(s.id), trip_id=str(s.trip_id),
        title=s.title, platform=s.platform,
        duration_seconds=s.duration_seconds, style=s.style,
        script_content=s.script_content,
        segments=segments, script_json=s.script_json,
        hook_text=s.hook_text, highlights_text=s.highlights_text,
        detail_text=s.detail_text, cta_text=s.cta_text,
        image_assignments=s.image_assignments,
        quality_score=s.quality_score,
        engagement_score=s.engagement_score,
        accuracy_score=s.accuracy_score,
        completeness_score=s.completeness_score,
        generation_version=s.generation_version,
        polish_iterations=s.polish_iterations,
        status=s.status,
        capcut_draft_id=s.capcut_draft_id,
        export_status=s.export_status,
        exported_at=s.exported_at.isoformat() if s.exported_at else None,
        created_at=s.created_at.isoformat() if s.created_at else "",
        updated_at=s.updated_at.isoformat() if s.updated_at else "",
    )


@router.get("")
async def list_scripts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trip_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """List all video scripts."""
    query = select(VideoScript)
    if trip_id:
        query = query.where(VideoScript.trip_id == trip_id)
    query = query.order_by(VideoScript.updated_at.desc())

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    scripts = result.scalars().all()

    return {
        "items": [
            ScriptListResponse(
                id=str(s.id), trip_id=str(s.trip_id), title=s.title,
                platform=s.platform, duration_seconds=s.duration_seconds,
                quality_score=s.quality_score, status=s.status,
                export_status=s.export_status,
                created_at=s.created_at.isoformat() if s.created_at else "",
            ) for s in scripts
        ],
        "total": total, "page": page, "page_size": page_size,
    }


@router.post("/generate", response_model=ScriptResponse)
async def generate_script(
    data: ScriptGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Generate a video script via 4-stage AI pipeline."""
    # Verify trip
    result = await db.execute(select(Trip).where(Trip.id == data.trip_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="行程不存在")

    try:
        script = await ScriptGenerationService.generate(
            trip_id=data.trip_id,
            platform=data.platform,
            duration_seconds=data.duration_seconds,
            style=data.style or "活泼",
            db=db,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"脚本生成失败: {str(e)}")

    return _script_to_response(script)


@router.get("/{script_id}", response_model=ScriptResponse)
async def get_script(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Get script detail with segments."""
    result = await db.execute(select(VideoScript).where(VideoScript.id == script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")
    return _script_to_response(script)


@router.post("/{script_id}/polish", response_model=ScriptResponse)
async def polish_script(
    script_id: str,
    data: ScriptPolishRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Polish script with AI."""
    try:
        script = await ScriptGenerationService.polish(
            script_id=script_id,
            focus_areas=data.focus_areas,
            target_segment_index=data.target_segment_index,
            db=db,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _script_to_response(script)


@router.post("/{script_id}/evaluate", response_model=ScriptEvaluateResponse)
async def evaluate_script(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Evaluate script quality."""
    try:
        result = await ScriptGenerationService.evaluate(script_id=script_id, db=db)
        return ScriptEvaluateResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=402, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{script_id}/export/capcut")
async def export_capcut(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Export script as CapCut draft ZIP."""
    try:
        zip_bytes, draft_id, draft_name = await CapCutExportService.create_draft_zip(
            script_id=script_id,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

    from urllib.parse import quote
    safe_name = quote(draft_name.replace(" ", "_").replace("/", "_"))
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}_CapCut.zip",
            "X-Draft-Id": draft_id,
        },
    )


@router.get("/{script_id}/export/capcut/status")
async def export_status(
    script_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Check CapCut export status."""
    result = await db.execute(select(VideoScript).where(VideoScript.id == script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")
    return {
        "export_status": script.export_status,
        "capcut_draft_id": script.capcut_draft_id,
        "exported_at": script.exported_at.isoformat() if script.exported_at else None,
    }
