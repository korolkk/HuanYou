"""ScriptGenerationService — unified 4-stage pipeline for video script generation.

Stages: Research → Generate → Polish → Evaluate
All output is persisted to the VideoScript table.
"""

import json
import time
import re
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.trip import Trip
from app.models.video_script import VideoScript
from app.schemas.script import ScriptSegment


# ── Prompts ──

SCRIPT_SYSTEM_PROMPT = """你是专业的短视频文案创作专家，为旅游行程创作短视频脚本。

## 脚本结构
1. **开头钩子(15秒, ~50字)**: 用悬念、美景、情绪或问题抓住注意力
2. **行程精华(占70%时长)**: 每天核心亮点、景点特色、独特体验、美食推荐
3. **细节展开(占20%时长)**: 住宿、交通、注意事项、暖心服务
4. **结尾引导(15秒, ~50字)**: 价格、报名方式、行动号召

## 创作原则
- 口语化、适合配音朗读，像朋友分享旅行
- 使用感官语言（视觉、味觉、触觉、听觉）
- 加入情绪起伏和节奏变化
- 每个段落标注建议配图关键词

## 输出格式（严格JSON）
返回一个JSON对象，包含segments数组：
```json
{
  "title": "脚本标题",
  "segments": [
    {
      "timecode_start": "00:00",
      "timecode_end": "00:15",
      "duration_seconds": 15,
      "segment_type": "hook",
      "text": "脚本文字...",
      "image_keyword": "配图关键词",
      "bgm_suggestion": "BGM风格建议"
    }
  ]
}
```

segment_type 必须是: hook / highlights / detail / cta
highlights 可以拆成多个片段，每个对应一天或一个景点"""


POLISH_SYSTEM_PROMPT = """你是短视频文案润色专家。优化脚本的吸引力和表达质量。

## 润色方向
- engagement: 提升开头钩子、情感共鸣、节奏感
- transitions: 优化段落过渡，使内容更流畅
- sensory_language: 增加感官词汇（视觉、味觉、触觉、听觉）
- hooks: 强化开头吸引力，制造悬念或共鸣

保持原意和结构不变，只优化语言表达。返回完整的segments JSON数组。"""


EVALUATION_PROMPT = """你是短视频质量评审专家。从以下维度评分(每个0-1分):

1. **吸引力(engagement)**: 开头是否抓人？语言是否有感染力？节奏是否合理？
2. **准确性(accuracy)**: 行程信息是否准确？有无编造内容？
3. **完整度(completeness)**: 结构是否完整？是否覆盖所有必要元素？

返回严格JSON:
{"engagement": 0.8, "accuracy": 0.9, "completeness": 0.7, "feedback": "改进建议", "passed": true}
passed = true if 平均分 >= 0.7"""


# ── Service ──

class ScriptGenerationService:
    """Unified script generation pipeline."""

    @staticmethod
    async def _build_llm():
        """Create LLM instance from configured API keys."""
        from app.config import get_settings
        settings = get_settings()

        if settings.DEEPSEEK_API_KEY:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=settings.LLM_MODEL,
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_BASE_URL,
                temperature=0.7,
                max_tokens=4096,
            )
        if settings.DASHSCOPE_API_KEY:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="qwen-max",
                api_key=settings.DASHSCOPE_API_KEY,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                temperature=0.7,
                max_tokens=4096,
            )
        return None

    @staticmethod
    def _format_seconds(seconds: int) -> str:
        """Format seconds to MM:SS."""
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    @staticmethod
    def _parse_llm_json(text: str) -> dict:
        """Extract JSON from LLM response."""
        text = text.strip()
        # Remove markdown code fences
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        # Find JSON object
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group())
        return {}

    @classmethod
    async def generate(
        cls,
        trip_id: str,
        platform: str = "抖音",
        duration_seconds: int = 300,
        style: str = "活泼",
        db: Optional[AsyncSession] = None,
        llm=None,
    ) -> VideoScript:
        """Full 4-stage script generation pipeline.

        Returns the persisted VideoScript with structured segments.
        """
        start_time = time.time()
        if llm is None:
            llm = await cls._build_llm()
        if llm is None:
            raise RuntimeError("未配置AI API Key (DEEPSEEK_API_KEY 或 DASHSCOPE_API_KEY)")

        # ── Stage 1: Research ──
        trip = None
        if db:
            result = await db.execute(
                select(Trip).where(Trip.id == trip_id).options(selectinload(Trip.schedules))
            )
            trip = result.scalar_one_or_none()

        if not trip:
            raise ValueError(f"行程不存在: {trip_id}")

        # Build trip context
        schedules_text = ""
        if trip.schedules:
            for s in trip.schedules:
                schedules_text += (
                    f"第{s.day_number}天 - {s.theme or ''}: {s.description or ''}\n"
                    f"  地点: {s.location or ''} | 住宿: {s.hotel_name or ''}\n"
                )

        trip_context = f"""目的地: {trip.destination}
行程名称: {trip.title}
天数: {trip.duration_days}天
价格: 成人¥{trip.price_adult}/人
特色: {', '.join(trip.highlights or [])}
包含: {', '.join(trip.price_includes or [])}

日程:
{schedules_text}

目标平台: {platform}
目标时长: {duration_seconds}秒 (约{duration_seconds // 60}分钟)
风格: {style}"""

        # ── Stage 2: Generate ──
        generate_prompt = f"""{SCRIPT_SYSTEM_PROMPT}

行程信息:
{trip_context}

请为这个行程创作脚本，时长约{duration_seconds}秒。返回JSON格式。"""

        gen_response = await llm.ainvoke(generate_prompt)
        gen_text = gen_response.content if hasattr(gen_response, "content") else str(gen_response)
        gen_data = cls._parse_llm_json(gen_text)

        # Parse segments
        raw_segments = gen_data.get("segments", [])
        if not raw_segments:
            # Fallback: create simple segments from the raw text
            raw_segments = [{
                "timecode_start": "00:00",
                "timecode_end": cls._format_seconds(duration_seconds),
                "duration_seconds": duration_seconds,
                "segment_type": "highlights",
                "text": gen_text[:500],
                "image_keyword": trip.destination,
            }]

        segments = []
        full_text = ""
        hook_text = ""
        highlights_text = ""
        detail_text = ""
        cta_text = ""

        current_time = 0
        for s in raw_segments:
            seg_dur = min(s.get("duration_seconds", 15), duration_seconds - current_time)
            seg = ScriptSegment(
                timecode_start=cls._format_seconds(current_time),
                timecode_end=cls._format_seconds(current_time + seg_dur),
                duration_seconds=seg_dur,
                segment_type=s.get("segment_type", "highlights"),
                text=s.get("text", ""),
                image_ref=s.get("image_ref"),
                image_keyword=s.get("image_keyword", trip.destination),
                bgm_suggestion=s.get("bgm_suggestion", ""),
            )
            segments.append(seg)
            full_text += seg.text + "\n\n"
            current_time += seg_dur

            if seg.segment_type == "hook":
                hook_text = seg.text
            elif seg.segment_type == "highlights":
                highlights_text += seg.text + "\n"
            elif seg.segment_type == "detail":
                detail_text += seg.text + "\n"
            elif seg.segment_type == "cta":
                cta_text = seg.text

        # ── Stage 3: Polish ──
        polish_json = json.dumps(
            [s.model_dump() for s in segments], ensure_ascii=False, indent=2
        )
        polish_response = await llm.ainvoke([
            {"role": "system", "content": POLISH_SYSTEM_PROMPT},
            {"role": "user", "content": f"请润色以下脚本:\n\n{polish_json}"},
        ])
        polish_text = polish_response.content if hasattr(polish_response, "content") else str(polish_response)
        polish_data = cls._parse_llm_json(polish_text)
        polished_raw = polish_data if isinstance(polish_data, list) else polish_data.get("segments", raw_segments)

        # Update segments with polished text
        for i, seg in enumerate(segments):
            if i < len(polished_raw):
                p = polished_raw[i] if isinstance(polished_raw[i], dict) else {}
                seg.text = p.get("text", seg.text)
                seg.image_keyword = p.get("image_keyword", seg.image_keyword)
                seg.bgm_suggestion = p.get("bgm_suggestion", seg.bgm_suggestion)

        # Rebuild full text
        full_text = "\n\n".join(s.text for s in segments)

        # ── Stage 4: Evaluate ──
        eval_text_for_review = "\n\n".join(
            f"[{s.segment_type}] {s.timecode_start}-{s.timecode_end}: {s.text[:200]}"
            for s in segments
        )
        eval_response = await llm.ainvoke([
            {"role": "system", "content": EVALUATION_PROMPT},
            {"role": "user", "content": f"行程: {trip.title}\n脚本:\n{eval_text_for_review}"},
        ])
        eval_text = eval_response.content if hasattr(eval_response, "content") else str(eval_response)
        eval_data = cls._parse_llm_json(eval_text)

        engagement = eval_data.get("engagement", 0.7)
        accuracy = eval_data.get("accuracy", 0.7)
        completeness = eval_data.get("completeness", 0.7)
        overall = (engagement + accuracy + completeness) / 3
        passed = eval_data.get("passed", overall >= 0.7)
        feedback = eval_data.get("feedback", "")

        # ── Persist to DB ──
        gen_time = int((time.time() - start_time) * 1000)

        if db:
            # Check for existing script (regenerate)
            existing = await db.execute(
                select(VideoScript).where(
                    VideoScript.trip_id == trip_id,
                    VideoScript.platform == platform,
                ).order_by(VideoScript.generation_version.desc()).limit(1)
            )
            script = existing.scalar_one_or_none()

            if script:
                script.generation_version += 1
                script.polish_iterations = 0
            else:
                script = VideoScript(trip_id=trip_id)

            script.title = gen_data.get("title", f"{trip.title}短视频脚本")
            script.platform = platform
            script.duration_seconds = duration_seconds
            script.style = style
            script.script_content = full_text
            script.script_json = {"segments": [s.model_dump() for s in segments]}
            script.hook_text = hook_text
            script.highlights_text = highlights_text
            script.detail_text = detail_text
            script.cta_text = cta_text
            script.quality_score = round(overall, 2)
            script.engagement_score = round(engagement, 2)
            script.accuracy_score = round(accuracy, 2)
            script.completeness_score = round(completeness, 2)
            script.status = "completed" if passed else "needs_revision"
            script.polish_iterations = 1
            script.model_used = getattr(llm, 'model_name', 'llm')
            script.generation_time_ms = gen_time
            db.add(script)
            await db.flush()
            return script

        # No DB: return transient object
        script = VideoScript(
            trip_id=trip_id, title=f"{trip.title}短视频脚本",
            platform=platform, duration_seconds=duration_seconds,
            script_content=full_text,
            script_json={"segments": [s.model_dump() for s in segments]},
            hook_text=hook_text, highlights_text=highlights_text,
            detail_text=detail_text, cta_text=cta_text,
            quality_score=round(overall, 2),
            engagement_score=round(engagement, 2),
            accuracy_score=round(accuracy, 2),
            completeness_score=round(completeness, 2),
            status="completed" if passed else "needs_revision",
            generation_time_ms=gen_time,
        )
        return script

    @classmethod
    async def polish(
        cls,
        script_id: str,
        focus_areas: Optional[list[str]] = None,
        target_segment_index: Optional[int] = None,
        db: Optional[AsyncSession] = None,
        llm=None,
    ) -> VideoScript:
        """Polish an existing script."""
        if llm is None:
            llm = await cls._build_llm()
        if llm is None:
            raise RuntimeError("未配置AI API Key")

        if db is None:
            raise ValueError("DB session required for polish")

        result = await db.execute(select(VideoScript).where(VideoScript.id == script_id))
        script = result.scalar_one_or_none()
        if not script:
            raise ValueError(f"脚本不存在: {script_id}")

        # Load segments
        segments_data = []
        if script.script_json and "segments" in script.script_json:
            segments_data = script.script_json["segments"]
        segments = [ScriptSegment(**s) for s in segments_data]

        # Filter segments if target specified
        polish_segments = segments
        if target_segment_index is not None and 0 <= target_segment_index < len(segments):
            polish_segments = [segments[target_segment_index]]

        focus_str = ", ".join(focus_areas or ["engagement", "transitions", "sensory_language", "hooks"])
        polish_json = json.dumps([s.model_dump() for s in polish_segments], ensure_ascii=False, indent=2)

        response = await llm.ainvoke([
            {"role": "system", "content": POLISH_SYSTEM_PROMPT},
            {"role": "user", "content": f"优化方向: {focus_str}\n\n脚本:\n{polish_json}"},
        ])
        response_text = response.content if hasattr(response, "content") else str(response)
        polished_data = cls._parse_llm_json(response_text)

        # Update segments
        polished_list = polished_data if isinstance(polished_data, list) else polished_data.get("segments", [])
        for i, seg in enumerate(polish_segments):
            if i < len(polished_list):
                p = polished_list[i] if isinstance(polished_list[i], dict) else {}
                seg.text = p.get("text", seg.text)
                seg.image_keyword = p.get("image_keyword", seg.image_keyword)
                seg.bgm_suggestion = p.get("bgm_suggestion", seg.bgm_suggestion)

        # Rebuild full text
        full_text = "\n\n".join(s.text for s in segments)

        script.script_content = full_text
        script.script_json = {"segments": [s.model_dump() for s in segments]}
        script.polish_iterations += 1

        # Rebuild segment text fields
        for s in segments:
            if s.segment_type == "hook":
                script.hook_text = s.text
            elif s.segment_type == "highlights":
                if not script.highlights_text:
                    script.highlights_text = s.text
                else:
                    script.highlights_text += "\n" + s.text
            elif s.segment_type == "detail":
                if not script.detail_text:
                    script.detail_text = s.text
                else:
                    script.detail_text += "\n" + s.text
            elif s.segment_type == "cta":
                script.cta_text = s.text

        await db.flush()
        return script

    @classmethod
    async def evaluate(
        cls,
        script_id: str,
        db: Optional[AsyncSession] = None,
        llm=None,
    ) -> dict:
        """Evaluate script quality."""
        if llm is None:
            llm = await cls._build_llm()
        if llm is None:
            raise RuntimeError("未配置AI API Key")
        if db is None:
            raise ValueError("DB session required")

        result = await db.execute(select(VideoScript).where(VideoScript.id == script_id))
        script = result.scalar_one_or_none()
        if not script:
            raise ValueError(f"脚本不存在: {script_id}")

        # Get trip for context
        trip_result = await db.execute(
            select(Trip).where(Trip.id == script.trip_id)
        )
        trip = trip_result.scalar_one_or_none()

        eval_response = await llm.ainvoke([
            {"role": "system", "content": EVALUATION_PROMPT},
            {"role": "user", "content": f"行程: {trip.title if trip else '未知'}\n脚本:\n{script.script_content[:2000]}"},
        ])
        eval_text = eval_response.content if hasattr(eval_response, "content") else str(eval_response)
        eval_data = cls._parse_llm_json(eval_text)

        engagement = eval_data.get("engagement", script.engagement_score or 0.7)
        accuracy = eval_data.get("accuracy", script.accuracy_score or 0.7)
        completeness = eval_data.get("completeness", script.completeness_score or 0.7)
        overall = (engagement + accuracy + completeness) / 3
        passed = eval_data.get("passed", overall >= 0.7)

        script.engagement_score = round(engagement, 2)
        script.accuracy_score = round(accuracy, 2)
        script.completeness_score = round(completeness, 2)
        script.quality_score = round(overall, 2)
        script.status = "completed" if passed else "needs_revision"

        await db.flush()

        return {
            "quality_score": round(overall, 2),
            "engagement_score": round(engagement, 2),
            "accuracy_score": round(accuracy, 2),
            "completeness_score": round(completeness, 2),
            "passed": passed,
            "feedback": eval_data.get("feedback", ""),
        }
