"""CapCutExportService — generates CapCut (剪映) draft JSON and ZIP for one-click import.

CapCut stores projects as folders under:
  文档/CapCut/User Data/Projects/com.lveditor.draft/

Each project folder contains:
  - draft_content.json  (tracks, clips, text, audio, effects)
  - draft_meta_info.json (project metadata)
  - resources/ (media files — we generate placeholders)
"""

import json
import uuid
import zipfile
import io
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.video_script import VideoScript
from app.models.trip import Trip
from app.schemas.script import ScriptSegment


class CapCutExportService:
    """Generate CapCut-compatible draft files from script segments."""

    # ── Platform style presets ──
    PLATFORM_STYLES = {
        "抖音": {
            "width": 1080, "height": 1920, "fps": 30,
            "font_family": "PingFang SC",
            "hook_font_size": 56, "body_font_size": 40, "cta_font_size": 44,
            "text_color": "#FFFFFF",
            "stroke_color": "#000000", "stroke_width": 2,
            "bg_color": "rgba(0,0,0,0.35)",
        },
        "快手": {
            "width": 1080, "height": 1920, "fps": 30,
            "font_family": "PingFang SC",
            "hook_font_size": 56, "body_font_size": 40, "cta_font_size": 44,
            "text_color": "#FFFFFF",
            "stroke_color": "#000000", "stroke_width": 2,
            "bg_color": "rgba(0,0,0,0.35)",
        },
        "视频号": {
            "width": 1920, "height": 1080, "fps": 30,
            "font_family": "PingFang SC",
            "hook_font_size": 48, "body_font_size": 36, "cta_font_size": 40,
            "text_color": "#FFFFFF",
            "stroke_color": "#000000", "stroke_width": 2,
            "bg_color": "rgba(0,0,0,0.3)",
        },
        "小红书": {
            "width": 1080, "height": 1440, "fps": 30,
            "font_family": "PingFang SC",
            "hook_font_size": 48, "body_font_size": 36, "cta_font_size": 40,
            "text_color": "#1a1a1a",
            "stroke_color": "#FFFFFF", "stroke_width": 1,
            "bg_color": "rgba(255,255,255,0.6)",
        },
    }

    @classmethod
    def _seconds_to_us(cls, seconds: int) -> int:
        """Convert seconds to microseconds (CapCut's time unit)."""
        return int(seconds * 1_000_000)

    @classmethod
    def _get_style(cls, platform: str) -> dict:
        """Get platform-specific style preset."""
        return cls.PLATFORM_STYLES.get(platform, cls.PLATFORM_STYLES["抖音"])

    @classmethod
    async def build_draft_json(
        cls,
        script: VideoScript,
        trip: Optional[Trip] = None,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Build a CapCut draft_content.json matching the real CapCut schema.

        Based on reverse-engineered CapCut format from JianyingDraft.PY / capcut-mcp.
        Key elements: id, canvas_config, fps, duration, materials, tracks[segments].
        """
        style = cls._get_style(script.platform)

        # Parse segments
        segments_data = []
        if script.script_json and "segments" in script.script_json:
            segments_data = script.script_json["segments"]
        segments = [ScriptSegment(**s) for s in segments_data]

        if not segments:
            raise ValueError("脚本没有分段数据，请先生成脚本")

        total_duration_us = cls._seconds_to_us(script.duration_seconds)
        draft_id = script.capcut_draft_id or str(uuid.uuid4())

        # ── Materials: define all text assets ──
        texts_materials = []
        audios_materials = []
        text_segments = []
        audio_segments = []

        for i, seg in enumerate(segments):
            start_us = cls._seconds_to_us(sum(s.duration_seconds for s in segments[:i]))
            dur_us = cls._seconds_to_us(seg.duration_seconds)

            # Text material
            mat_id = str(uuid.uuid4())
            texts_materials.append({
                "id": mat_id,
                "type": "text",
                "content": seg.text,
                "font": style["font_family"],
                "size": style["hook_font_size"] if seg.segment_type == "hook" else style["body_font_size"],
                "color": style["text_color"],
                "alignment": 1,  # center
                "bold": seg.segment_type in ("hook", "cta"),
            })

            # Text segment on timeline
            text_segments.append({
                "id": str(uuid.uuid4()),
                "material_id": mat_id,
                "target_timerange": {"start": start_us, "duration": dur_us},
                "source_timerange": {"start": 0, "duration": dur_us},
                "extra_material_refs": [],
                "visible": True,
                "x": 0.0, "y": 0.0,
                "scale": 1.0,
            })

        # ── Audio material (BGM placeholder) ──
        bgm_name = "轻快旅行BGM"
        for seg in segments:
            if seg.bgm_suggestion:
                bgm_name = seg.bgm_suggestion
                break

        audio_mat_id = str(uuid.uuid4())
        audios_materials.append({
            "id": audio_mat_id,
            "type": "audio",
            "name": bgm_name,
            "duration": total_duration_us,
        })
        audio_segments.append({
            "id": str(uuid.uuid4()),
            "material_id": audio_mat_id,
            "target_timerange": {"start": 0, "duration": total_duration_us},
            "source_timerange": {"start": 0, "duration": total_duration_us},
            "extra_material_refs": [],
            "volume": 0.35,
            "visible": True,
            "x": 0.0, "y": 0.0,
            "scale": 1.0,
        })

        # ── Build the real CapCut schema ──
        w, h = style["width"], style["height"]
        draft = {
            "id": draft_id,
            "version": 1,
            "canvas_config": {
                "width": w,
                "height": h,
                "ratio": round(w / h, 4),
            },
            "fps": style["fps"],
            "duration": total_duration_us,
            "materials": {
                "texts": texts_materials,
                "audios": audios_materials,
                "videos": [],
                "images": [],
                "stickers": [],
                "effects": [],
                "transitions": [],
                "speeds": [],
                "animations": [],
                "audio_fades": [],
                "video_effects": [],
                "masks": [],
                "canvases": [],
            },
            "tracks": [
                {
                    "type": "text",
                    "name": "字幕轨道",
                    "render_index": 15000,
                    "mute": False,
                    "segments": text_segments,
                },
                {
                    "type": "audio",
                    "name": "背景音乐",
                    "render_index": 0,
                    "mute": False,
                    "segments": audio_segments,
                },
            ],
        }

        return draft

    @classmethod
    async def create_draft_zip(
        cls,
        script_id: str,
        include_images: bool = True,
        resolution: str = "1080p",
        db: Optional[AsyncSession] = None,
    ) -> tuple[bytes, str, str]:
        """Generate a ZIP file containing the CapCut draft folder structure.

        Returns:
            Tuple of (zip_bytes, draft_id, draft_name)
        """
        if db is None:
            raise ValueError("DB session required")

        # Load script
        result = await db.execute(select(VideoScript).where(VideoScript.id == script_id))
        script = result.scalar_one_or_none()
        if not script:
            raise ValueError(f"脚本不存在: {script_id}")

        # Load trip
        trip_result = await db.execute(select(Trip).where(Trip.id == script.trip_id))
        trip = trip_result.scalar_one_or_none()

        # Build draft JSON
        draft = await cls.build_draft_json(script, trip, db)
        draft_id = draft["id"]
        draft_name = script.title or f"{trip.destination if trip else ''}短视频脚本"
        # Sanitize folder name: remove problematic chars
        safe_folder = draft_name.replace(" ", "_").replace("/", "_").replace("\\", "_")[:50]

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write draft_content.json
            draft_json = json.dumps(draft, ensure_ascii=False, indent=2)
            zf.writestr(f"{safe_folder}/draft_content.json", draft_json)

            # Write minimal draft_meta_info.json
            meta = {
                "id": draft_id,
                "create_time": int(datetime.now(timezone.utc).timestamp()),
            }
            zf.writestr(
                f"{safe_folder}/draft_meta_info.json",
                json.dumps(meta, ensure_ascii=False, indent=2),
            )

            # Write usage instructions
            instructions = (
                "剪映导入说明\n"
                "============\n\n"
                "1. 解压此ZIP文件\n"
                "2. 将整个文件夹复制到剪映草稿目录:\n"
                "   Windows: 文档\\CapCut\\User Data\\Projects\\com.lveditor.draft\\\n"
                "   Mac: ~/Movies/CapCut/User Data/Projects/com.lveditor.draft/\n\n"
                "3. 打开剪映桌面版 → 点击「剪辑」→ 在草稿列表中找到此项目\n"
                "4. 在剪映中为每段文字添加动画效果\n"
                "5. 在剪映音乐库中搜索BGM并添加到音频轨道\n"
                "6. 可选: 添加景点照片到视频轨道\n"
                "7. 预览并导出视频\n\n"
                f"行程: {trip.title if trip else '未知'}\n"
                f"生成时间: {datetime.now(timezone.utc).isoformat()}\n"
                f"由欢游HuanYou AI自动生成\n"
            )
            zf.writestr(f"{safe_folder}/使用说明.txt", instructions)

        zip_bytes = zip_buffer.getvalue()

        # Update script export status
        script.capcut_draft_id = draft_id
        script.export_status = "completed"
        script.exported_at = datetime.now(timezone.utc)
        await db.flush()

        return zip_bytes, draft_id, draft_name
