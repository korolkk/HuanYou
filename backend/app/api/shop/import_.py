"""Shop owner file import API."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.models.base import get_db
from app.models.customer import Customer
from app.utils.auth import get_shop_owner
from app.services.import_service import TripImportService

router = APIRouter()


@router.post("/trip-file")
async def import_trip_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_shop_owner),
):
    """Upload and parse a trip file (Excel .xlsx or .json).

    Returns parsed trip data and imports into the database.
    """
    filename = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ("xlsx", "json"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: .{ext}，请上传 .xlsx 或 .json 文件",
        )

    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > 20:
        raise HTTPException(status_code=400, detail="文件大小不能超过20MB")

    try:
        result = await TripImportService.parse_and_import(
            content=content,
            filename=filename,
            db=db,
            created_by=str(current_user.id),
        )
        return {
            **result,
            "message": f"成功导入行程「{result['trip_title']}」，共{result['schedules_count']}天日程",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/template/trip-import")
async def download_import_template():
    """Download the standard trip import Excel template."""
    try:
        template_bytes = TripImportService.generate_template_bytes()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return StreamingResponse(
        io.BytesIO(template_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=huanyou_trip_import_template.xlsx",
        },
    )
