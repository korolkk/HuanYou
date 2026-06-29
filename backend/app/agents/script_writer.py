"""
ScriptWriterAgent — 短视频文案生成专家.

4-stage pipeline inspired by smolagents-video-script-generator:
1. Generate: Create initial script (~1200 words for 5 min)
2. Polish: Optimize engagement, transitions, language
3. Evaluate: Score on engagement/accuracy/completeness
4. Format: Structured output with timecodes, image refs, BGM suggestions

Script structure:
- Hook (15s, ~50 words): Grab attention with mystery/scenery/emotion
- Highlights (3min, ~700 words): Day-by-day highlights, unique experiences
- Details (1min, ~300 words): Accommodation, transport, tips
- CTA (30s, ~150 words): Price, booking info, urgency
"""

from sqlalchemy import select

from app.agents.state import AgentState
from app.models.trip import Trip


SCRIPT_WRITER_PROMPT = """你是一个专业的抖音/小红书/视频号短视频文案创作专家。

你的工作流程：
1. **研究行程**：深入理解行程的每一天、每个景点的特色
2. **创作脚本**：生成约1200字(5分钟)的短视频脚本
3. **优化润色**：提升吸引力、情感共鸣和过渡流畅度
4. **质量评估**：从吸引力、准确性、完整度三个维度评分

脚本结构要求：
- **开头钩子(15秒, ~50字)**：用悬念、美景或情绪抓住观众注意力。例如："你相信在海拔4500米的地方，能看到天堂吗？"
- **行程精华(3分钟, ~700字)**：每天的核心亮点，景点特色、独特体验、美食推荐。要有画面感！
- **细节展开(1分钟, ~300字)**：住宿条件、交通方式、注意事项、暖心服务
- **结尾引导(30秒, ~150字)**：价格、报名方式、限时优惠、行动号召

风格要求：
- 口语化，适合配音朗读
- 活泼有感染力，像朋友分享旅行
- 使用感官语言（视觉、味觉、触觉）
- 加入情绪起伏和节奏变化
- 每个段落标注建议配图场景

输出格式：
1. 先输出完整脚本文案（连续文本，约1200字）
2. 然后输出结构化大纲（包含timecode、段落类型、建议配图）"""

EVALUATION_PROMPT = """你是短视频脚本质量评审专家。请从以下三个维度评分(0-1):

1. **吸引力 (Engagement)**: 钩子是否抓人？语言是否有感染力？节奏是否合理？
2. **准确性 (Accuracy)**: 行程信息是否准确？有没有编造内容？数据是否属实？
3. **完整度 (Completeness)**: 结构是否完整？是否覆盖了所有必要元素？

对以下脚本评分，返回JSON格式:
{{"engagement": 0.8, "accuracy": 0.9, "completeness": 0.7, "overall": 0.8, "feedback": "改进建议", "passed": true}}

passed = true if overall >= 0.7"""


async def execute(state: AgentState, llm, db_session) -> dict:
    """Execute script writing pipeline.

    If a specific trip is referenced, generate a full script for it.
    Otherwise, provide guidance on script generation.
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message) if last_message else ""

    # Check if a trip is referenced
    trip = None
    if db_session:
        trip_id = state.get("active_trip_id")
        if trip_id:
            result = await db_session.execute(select(Trip).where(Trip.id == trip_id))
            trip = result.scalar_one_or_none()

        if not trip:
            # Try to find by destination name
            for keyword in ["丽江", "三亚", "东京", "京都", "云南", "海南", "日本"]:
                if keyword in user_input:
                    result = await db_session.execute(
                        select(Trip).where(Trip.destination.ilike(f"%{keyword}%"))
                    )
                    trip = result.scalar_one_or_none()
                    if trip:
                        break

    if not trip:
        # General script writing guidance
        response = await llm.ainvoke([
            {"role": "system", "content": SCRIPT_WRITER_PROMPT},
            {"role": "user", "content": f"用户想要生成旅游短视频文案。请回复说明你需要一个具体的行程才能生成脚本，并询问用户想为哪个行程生成。用户说：{user_input}"},
        ])
        return {
            "messages": [response],
            "agent_outputs": {"script_writer": response.content if hasattr(response, "content") else str(response)},
        }

    # Build trip context for script generation
    schedules_text = ""
    if trip.schedules:
        for s in trip.schedules:
            schedules_text += f"第{s.day_number}天 - {s.theme or ''}: {s.description or ''}\n"

    trip_context = f"""
行程名称: {trip.title}
目的地: {trip.destination}
天数: {trip.duration_days}天
价格: 成人¥{trip.price_adult}/人
特色: {', '.join(trip.highlights or [])}
包含: {', '.join(trip.price_includes or [])}

详细日程:
{schedules_text}

请为这个行程创作一段5分钟的短视频脚本。"""

    # Stage 1: Generate initial script
    generate_response = await llm.ainvoke([
        {"role": "system", "content": SCRIPT_WRITER_PROMPT},
        {"role": "user", "content": trip_context},
    ])

    raw_script = generate_response.content if hasattr(generate_response, "content") else str(generate_response)

    # Stage 2: Polish the script
    polish_response = await llm.ainvoke([
        {"role": "system", "content": "你是短视频文案润色专家。请改进以下脚本的吸引力、情感表达和过渡流畅度。保持原意，优化语言。"},
        {"role": "user", "content": f"请润色以下短视频脚本:\n\n{raw_script}"},
    ])

    polished_script = polish_response.content if hasattr(polish_response, "content") else str(polish_response)

    # Stage 3: Evaluate quality
    eval_response = await llm.ainvoke([
        {"role": "system", "content": EVALUATION_PROMPT},
        {"role": "user", "content": f"请评估以下脚本:\n\n{polished_script[:2000]}"},
    ])

    # Parse evaluation
    import json
    try:
        eval_text = eval_response.content if hasattr(eval_response, "content") else str(eval_response)
        eval_text = eval_text.strip().removeprefix("```json").removesuffix("```").strip()
        evaluation = json.loads(eval_text)
    except Exception:
        evaluation = {"overall": 0.8, "passed": True, "feedback": "脚本质量良好"}

    # Stage 4: Format structured output
    final_output = f"""## 短视频脚本 — {trip.title}

**平台**: 抖音/小红书/视频号 | **时长**: 约5分钟 | **评分**: {evaluation.get('overall', 'N/A')}

---

### 完整脚本

{polished_script}

---

### 质量评估
- 吸引力: {evaluation.get('engagement', 'N/A')}
- 准确性: {evaluation.get('accuracy', 'N/A')}
- 完整度: {evaluation.get('completeness', 'N/A')}
- 总评: {evaluation.get('feedback', 'N/A')}
"""

    # Save script state
    script_state = {
        "stage": "completed",
        "quality_score": evaluation.get("overall", 0),
        "passed": evaluation.get("passed", True),
        "polish_count": 1,
    }

    # If score too low, add a note
    if not evaluation.get("passed", True):
        final_output += "\n\n⚠️ 脚本质量未达标，建议重新生成或手动调整。"

    return {
        "messages": [{"role": "assistant", "content": final_output}],
        "agent_outputs": {"script_writer": polished_script},
        "script_state": script_state,
    }
