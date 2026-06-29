"""
TripManager Agent — 行程管理专家.

Handles:
- Trip file import and parsing
- Trip CRUD operations
- AI summary generation (highlights, selling points, recommendations)
- Trip search and listing
"""

from sqlalchemy import select

from app.agents.state import AgentState
from app.models.trip import Trip, TripSchedule
from app.rag.parser import DocumentParser
from app.rag.indexer import RAGIndexer


TRIP_MANAGER_PROMPT = """你是行程管理专家，负责旅游行程的导入、管理和概要生成。

你的能力：
1. **行程概要生成**：根据行程详情，生成200字左右的中文概要介绍
2. **特色亮点提炼**：归纳3-5个行程特色
3. **推荐理由**：给出2-3条推荐理由
4. **行程文件解析**：从Excel/PDF/JSON中提取行程信息
5. **行程查询**：按目的地、类型、时间等条件搜索行程

请以专业、热情的中文风格回复。"""


async def execute(state: AgentState, llm, db_session) -> dict:
    """Execute TripManager agent logic.

    Parses user intent within trip management domain and performs
    the appropriate operation (view/create/summarize/import).
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message) if last_message else ""

    # Determine what the user wants to do
    if any(kw in user_input for kw in ["概要", "总结", "摘要", "介绍"]):
        return await _generate_summary(state, llm, db_session, user_input)
    elif any(kw in user_input for kw in ["列表", "所有", "查看行程", "有哪些"]):
        return await _list_trips(state, db_session)
    else:
        # General trip management query
        return await _general_query(state, llm, db_session, user_input)


async def _generate_summary(state: AgentState, llm, db_session, user_input: str) -> dict:
    """Generate AI summary, highlights, and recommendations for a trip."""
    # Try to find the referenced trip
    trip = None
    if db_session:
        # Check if active_trip_id is set
        trip_id = state.get("active_trip_id")
        if trip_id:
            result = await db_session.execute(select(Trip).where(Trip.id == trip_id))
            trip = result.scalar_one_or_none()

        if not trip:
            # Try to find by destination name in user input
            for keyword in ["丽江", "三亚", "东京", "京都", "云南", "海南", "日本"]:
                if keyword in user_input:
                    result = await db_session.execute(
                        select(Trip).where(
                            Trip.destination.ilike(f"%{keyword}%"),
                            Trip.status == "active",
                        )
                    )
                    trip = result.scalar_one_or_none()
                    if trip:
                        break

    if not trip:
        # Generate a sample summary for demonstration
        response = await llm.ainvoke([
            {"role": "system", "content": TRIP_MANAGER_PROMPT},
            {"role": "user", "content": f"请为一个热门旅游目的地写一段200字的概要、3个特色亮点和2条推荐理由。用户说：{user_input}"},
        ])
        return {
            "messages": [response],
            "agent_outputs": {"trip_manager": response.content if hasattr(response, "content") else str(response)},
        }

    # Build context from trip data
    schedules = []
    if trip.schedules:
        schedules = trip.schedules

    context = f"""行程信息：
目的地: {trip.destination}
行程名称: {trip.title}
天数: {trip.duration_days}天
类型: {trip.category}
成人价: {trip.price_adult}元
包含: {', '.join(trip.price_includes or [])}
详细描述: {trip.detailed_description or '无'}

每日行程:
{chr(10).join(f'第{s.day_number}天: {s.theme or ""} - {s.description or ""}' for s in schedules)}
"""

    response = await llm.ainvoke([
        {"role": "system", "content": TRIP_MANAGER_PROMPT},
        {"role": "user", "content": f"请根据以下行程信息，生成：\n1. 200字概要介绍\n2. 3个特色亮点\n3. 2条推荐理由\n\n{context}"},
    ])

    # Save generated content to trip
    if db_session:
        response_text = response.content if hasattr(response, "content") else str(response)
        # Parse response to extract sections (simplified)
        lines = response_text.split("\n")
        highlights = []
        reasons = []
        summary = ""
        current_section = None

        for line in lines:
            line = line.strip()
            if "概要" in line or "介绍" in line:
                current_section = "summary"
            elif "特色" in line or "亮点" in line:
                current_section = "highlights"
            elif "推荐" in line or "理由" in line:
                current_section = "reasons"
            elif line.startswith(("1.", "2.", "3.", "4.", "5.", "-", "•")) and current_section == "highlights":
                highlights.append(line.lstrip("12345.-• "))
            elif line.startswith(("1.", "2.", "3.", "-", "•")) and current_section == "reasons":
                reasons.append(line.lstrip("12345.-• "))
            elif current_section == "summary" and line and not line.startswith("#"):
                summary += line + " "

        if summary.strip():
            trip.summary = summary.strip()
        if highlights:
            trip.highlights = highlights
        if reasons:
            trip.recommendation_reasons = reasons

    return {
        "messages": [response],
        "agent_outputs": {"trip_manager": response.content if hasattr(response, "content") else str(response)},
    }


async def _list_trips(state: AgentState, db_session) -> dict:
    """List available trips."""
    if not db_session:
        return {
            "messages": [{"role": "assistant", "content": "行程查询需要数据库连接。请先配置数据库。"}],
            "agent_outputs": {},
        }

    result = await db_session.execute(
        select(Trip).where(Trip.status == "active").order_by(Trip.is_featured.desc()).limit(10)
    )
    trips = result.scalars().all()

    if not trips:
        return {
            "messages": [{"role": "assistant", "content": "当前没有可用的行程，请联系店长添加行程。"}],
            "agent_outputs": {},
        }

    trip_list = "\n".join(
        f"- **{t.title}** ({t.destination}, {t.duration_days}天, ¥{t.price_adult or '详询'})"
        for t in trips
    )

    response_text = f"当前可报名行程：\n\n{trip_list}\n\n请输入行程名称查看详情，或告诉我你的需求获取推荐。"
    return {
        "messages": [{"role": "assistant", "content": response_text}],
        "agent_outputs": {"trip_manager": response_text},
    }


async def _general_query(state: AgentState, llm, db_session, user_input: str) -> dict:
    """Handle general trip management queries."""
    response = await llm.ainvoke([
        {"role": "system", "content": TRIP_MANAGER_PROMPT},
        {"role": "user", "content": user_input},
    ])
    return {
        "messages": [response],
        "agent_outputs": {"trip_manager": response.content if hasattr(response, "content") else str(response)},
    }
