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
        """Build a CapCut draft_content.json structure from script segments.

        Returns a dict that can be serialized to CapCut's draft_content.json format.
        """
        style = cls._get_style(script.platform)

        # Parse segments
        segments_data = []
        if script.script_json and "segments" in script.script_json:
            segments_data = script.script_json["segments"]
        segments = [ScriptSegment(**s) for s in segments_data]

        if not segments:
            raise ValueError("脚本没有分段数据，请先生成脚本")

        # Calculate total duration
        total_duration_s = script.duration_seconds
        total_duration_us = cls._seconds_to_us(total_duration_s)

        track_id_base = str(uuid.uuid4())[:8]

        # ── Build tracks ──
        tracks = []

        # --- Video/Image track ---
        video_clips = []
        image_urls = trip.image_urls if trip and trip.image_urls else []
        img_idx = 0

        for seg in segments:
            duration_us = cls._seconds_to_us(seg.duration_seconds)
            start_us = cls._seconds_to_us(
                sum(s.duration_seconds for s in segments[:segments.index(seg)])
            )

            # Assign image (round-robin through trip images)
            image_ref = ""
            if image_urls:
                image_ref = image_urls[img_idx % len(image_urls)]
                img_idx += 1

            clip = {
                "id": str(uuid.uuid4()),
                "type": "image" if image_ref else "placeholder",
                "file_path": image_ref if image_ref else "",
                "file_name": image_ref.split("/")[-1] if "/" in image_ref else (image_ref or "placeholder"),
                "duration_us": duration_us,
                "start_time_us": start_us,
                "width": style["width"],
                "height": style["height"],
                "transform": {
                    "x": 0.0, "y": 0.0,
                    "scale_x": 1.0, "scale_y": 1.0,
                    "rotation": 0.0,
                },
                "segment_type": seg.segment_type,
            }

            # Add transitions between clips
            if seg.segment_type == "hook":
                clip["transition_in"] = {"type": "fade_in", "duration_us": 500000}
            elif seg.segment_type == "cta":
                clip["transition_out"] = {"type": "fade_out", "duration_us": 500000}

            video_clips.append(clip)

        tracks.append({
            "id": f"video_track_{track_id_base}",
            "type": "video",
            "is_main": True,
            "clips": video_clips,
        })

        # --- Text track ---
        text_clips = []
        for seg in segments:
            duration_us = cls._seconds_to_us(seg.duration_seconds)
            start_us = cls._seconds_to_us(
                sum(s.duration_seconds for s in segments[:segments.index(seg)])
            )

            # Choose text style based on segment type
            if seg.segment_type == "hook":
                font_size = style["hook_font_size"]
                position = {"x": float(style["width"] / 2), "y": float(style["height"] / 2)}
                anim_in = {"type": "scale_in", "duration_us": 300000}
                anim_out = {"type": "fade_out", "duration_us": 300000}
            elif seg.segment_type == "cta":
                font_size = style["cta_font_size"]
                position = {"x": float(style["width"] / 2), "y": float(style["height"] - 120)}
                anim_in = {"type": "slide_up", "duration_us": 300000}
                anim_out = {"type": "fade_out", "duration_us": 200000}
            elif seg.segment_type == "detail":
                font_size = style["body_font_size"]
                position = {"x": float(style["width"] / 2), "y": float(style["height"] - 80)}
                anim_in = {"type": "fade_in", "duration_us": 200000}
                anim_out = {"type": "fade_out", "duration_us": 200000}
            else:  # highlights
                font_size = style["body_font_size"]
                position = {"x": float(style["width"] / 2), "y": float(style["height"] - 100)}
                anim_in = {"type": "fade_in", "duration_us": 300000}
                anim_out = {"type": "fade_out", "duration_us": 300000}

            text_clips.append({
                "id": str(uuid.uuid4()),
                "type": "text",
                "content": seg.text,
                "duration_us": duration_us,
                "start_time_us": start_us,
                "style": {
                    "font_family": style["font_family"],
                    "font_size": font_size,
                    "font_color": style["text_color"],
                    "font_bold": seg.segment_type in ("hook", "cta"),
                    "alignment": "center",
                    "position": position,
                    "background_color": style["bg_color"],
                    "stroke": {
                        "color": style["stroke_color"],
                        "width": style["stroke_width"],
                    },
                    "padding": 16,
                },
                "animation_in": anim_in,
                "animation_out": anim_out,
                "segment_type": seg.segment_type,
            })

        tracks.append({
            "id": f"text_track_{track_id_base}",
            "type": "text",
            "clips": text_clips,
        })

        # --- Audio track (BGM placeholder) ---
        audio_clips = []
        bgm_names = []
        for seg in segments:
            if seg.bgm_suggestion and seg.bgm_suggestion not in bgm_names:
                bgm_names.append(seg.bgm_suggestion)

        audio_clips.append({
            "id": str(uuid.uuid4()),
            "type": "audio",
            "file_path": "",
            "is_bgm": True,
            "bgm_name": bgm_names[0] if bgm_names else "轻快旅行BGM",
            "bgm_artist": "推荐配乐",
            "duration_us": total_duration_us,
            "start_time_us": 0,
            "volume": 0.35,
            "fade_in_us": 500000,
            "fade_out_us": 1000000,
        })

        tracks.append({
            "id": f"audio_track_{track_id_base}",
            "type": "audio",
            "clips": audio_clips,
        })

        # ── Build full draft ──
        draft = {
            "draft_name": script.title or f"{trip.destination if trip else ''}短视频脚本",
            "draft_id": script.capcut_draft_id or str(uuid.uuid4()),
            "draft_version": 5,
            "draft_root_path": "",
            "draft_tracks": tracks,
            "draft_materials": {
                "images": [{"file_path": u} for u in (image_urls or [])],
                "text_styles": [],
                "audios": [],
                "effects": [],
                "bgm_list": [{"name": n, "artist": "推荐"} for n in bgm_names],
            },
            "draft_duration_us": total_duration_us,
            "draft_resolution": {"width": style["width"], "height": style["height"]},
            "draft_fps": style["fps"],
            "draft_create_time": int(datetime.now(timezone.utc).timestamp()),
            "draft_platform": script.platform,
            "draft_notes": (
                f"由欢游HuanYou AI自动生成\n"
                f"行程: {trip.title if trip else script.trip_id}\n"
                f"生成时间: {datetime.now(timezone.utc).isoformat()}\n"
                f"\n使用说明:\n"
                f"1. 将此文件夹复制到: 文档/CapCut/User Data/Projects/com.lveditor.draft/\n"
                f"2. 打开剪映 → 点击「剪辑」→ 在草稿列表中找到此项目\n"
                f"3. 替换占位图片为实际景点照片\n"
                f"4. 在剪映音乐库中选择BGM替换占位配乐\n"
                f"5. 预览并导出视频"
            ),
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
        draft_id = draft["draft_id"]
        draft_name = draft["draft_name"]

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            # Write draft_content.json
            draft_json = json.dumps(draft, ensure_ascii=False, indent=2)
            zf.writestr(f"{draft_name}/draft_content.json", draft_json)

            # Write draft_meta_info.json
            meta = {
                "draft_id": draft_id,
                "draft_name": draft_name,
                "draft_version": 5,
                "create_time": draft["draft_create_time"],
                "platform": script.platform,
                "resolution": f"{draft['draft_resolution']['width']}x{draft['draft_resolution']['height']}",
                "duration_seconds": script.duration_seconds,
                "generated_by": "HuanYou AI",
            }
            zf.writestr(
                f"{draft_name}/draft_meta_info.json",
                json.dumps(meta, ensure_ascii=False, indent=2),
            )

            # Write resources README
            resources_readme = (
                "图片素材文件夹\n"
                "==============\n\n"
                "请将行程相关的景点照片放入此文件夹，文件名与draft_content.json中的file_path对应。\n\n"
                f"行程: {trip.title if trip else '未知'}\n"
                f"目的地: {trip.destination if trip else '未知'}\n\n"
                "建议图片:\n"
            )
            if trip and trip.highlights:
                for h in trip.highlights:
                    resources_readme += f"  - {h}\n"
            resources_readme += (
                "\n没有图片也可以用纯色背景替代，剪映会自动生成占位图。\n"
            )
            zf.writestr(f"{draft_name}/resources/README.txt", resources_readme)

            # Write usage instructions
            instructions = (
                "剪映导入说明\n"
                "============\n\n"
                "1. 将整个文件夹复制到:\n"
                "   Windows: 文档\\CapCut\\User Data\\Projects\\com.lveditor.draft\\\n"
                "   Mac: ~/Movies/CapCut/User Data/Projects/com.lveditor.draft/\n\n"
                "2. 打开剪映桌面版\n\n"
                "3. 点击「开始创作」或查看「草稿」列表\n\n"
                "4. 找到草稿「{draft_name}」并打开\n\n"
                "5. 替换资源文件夹中的占位图片为实际照片\n\n"
                "6. 在剪映音频库中选择合适的BGM替换占位配乐\n\n"
                "7. 调整文字样式和动画效果\n\n"
                "8. 点击「导出」选择分辨率和格式\n\n"
                "常见问题:\n"
                "Q: 打开剪映找不到草稿？\n"
                "A: 确认已复制到正确的目录，重启剪映后再试。\n\n"
                "Q: 文字显示乱码？\n"
                "A: 在剪映中重新选择中文字体即可。\n\n"
                "Q: 没有图片怎么办？\n"
                "A: 剪映会自动使用纯色占位图，您可以手动添加景点照片。\n"
            ).format(draft_name=draft_name)
            zf.writestr(f"{draft_name}/使用说明.txt", instructions)

        zip_bytes = zip_buffer.getvalue()

        # Update script export status
        script.capcut_draft_id = draft_id
        script.export_status = "completed"
        script.exported_at = datetime.now(timezone.utc)
        await db.flush()

        return zip_bytes, draft_id, draft_name
