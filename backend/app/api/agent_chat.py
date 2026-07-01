"""
Agent Chat API — Multi-agent conversation endpoint.

Routes user messages through the Supervisor → Worker Agent pipeline.
Each agent has access to LLM, database, and user context.
"""

import json
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.models.base import get_db
from app.models.customer import Customer
from app.models.conversation import Conversation
from app.utils.auth import get_current_user
from app.config import get_settings

router = APIRouter()


async def _build_llm():
    """Create LLM instance from configured API keys."""
    settings = get_settings()

    if settings.DEEPSEEK_API_KEY:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.7,
            max_tokens=2048,
            request_timeout=90,
        )

    if settings.DASHSCOPE_API_KEY:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="qwen-max",
            api_key=settings.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=0.7,
            max_tokens=2048,
            request_timeout=90,
        )

    return None


async def _route_and_execute(
    llm,
    user_input: str,
    role: str,
    user_id: str,
    db: AsyncSession,
) -> dict:
    """Route user intent and execute the appropriate agent handler.

    Returns: {"response": str, "agent": str, "data": dict}
    """
    # ── Quick keyword routing ──
    agent = _quick_route(user_input, role)

    # ── Execute agent ──
    try:
        if agent == "trip_manager":
            return await _handle_trip_manager(llm, user_input, db, role)
        elif agent == "script_writer":
            return await _handle_script_writer(llm, user_input, db)
        elif agent == "customer_profile":
            return await _handle_customer_profile(llm, user_input, db, role, user_id)
        elif agent == "recommendation":
            return await _handle_recommendation(llm, user_input, db, user_id)
        elif agent == "trip_support":
            return await _handle_trip_support(llm, user_input, db, user_id)
        elif agent == "history_agent":
            return await _handle_history(llm, user_input, db, user_id)
        else:
            return await _handle_general(llm, user_input, role)
    except Exception as e:
        # Fallback: direct LLM response
        response = await llm.ainvoke(
            f"用户说：{user_input}\n请友好地回复，告知当前AI服务可用。"
        )
        return {
            "response": response.content if hasattr(response, "content") else str(response),
            "agent": "fallback",
            "data": {},
        }


def _quick_route(user_input: str, role: str) -> str:
    """Fast keyword routing."""
    text = user_input.lower()

    if role == "shop_owner":
        if any(kw in text for kw in ["导入", "上传", "文件", "读取", "解析"]):
            return "trip_manager"
        if any(kw in text for kw in ["脚本", "短视频", "文案", "生成视频"]):
            return "script_writer"
        if any(kw in text for kw in ["画像", "分析客户", "客户分析", "用户画像"]):
            return "customer_profile"

    if role == "user" or role is None:
        if any(kw in text for kw in ["推荐", "建议", "适合", "帮我找", "想去", "有什么"]):
            return "recommendation"
        if any(kw in text for kw in ["报名", "注意", "天气", "准备", "集合", "导游",
                                       "紧急", "投诉", "发票", "合同", "改签", "评价"]):
            return "trip_support"
        if any(kw in text for kw in ["历史", "以前的", "过去的", "订单记录", "足迹"]):
            return "history_agent"

    if any(kw in text for kw in ["行程", "线路"]):
        if role == "shop_owner":
            return "trip_manager"
        return "recommendation"

    if any(kw in text for kw in ["你好", "帮助", "介绍", "功能", "怎么"]):
        return "general"

    return "general"


# ── Agent Handlers ──

async def _handle_trip_manager(llm, user_input: str, db, role: str) -> dict:
    """Handle trip management requests."""
    if role != "shop_owner":
        return {"response": "行程管理功能仅限店长使用。您可以浏览可报名行程。", "agent": "trip_manager", "data": {}}

    # Check if asking to list trips
    if any(kw in user_input for kw in ["列表", "所有", "有哪些", "查看行程"]):
        from sqlalchemy import select
        from app.models.trip import Trip
        result = await db.execute(
            select(Trip).where(Trip.status == "active").order_by(Trip.updated_at.desc()).limit(10)
        )
        trips = result.scalars().all()
        if trips:
            trip_list = "\n".join(
                f"- **{t.title}** ({t.destination}, {t.duration_days}天, ¥{t.price_adult or '详询'}/人)"
                for t in trips
            )
            response_text = f"📋 当前在售行程：\n\n{trip_list}"
        else:
            response_text = "当前没有上架的行程，请先导入行程数据。"
        return {"response": response_text, "agent": "trip_manager", "data": {"trips": [str(t.id) for t in trips] if trips else []}}

    # General trip management
    response = await llm.ainvoke(
        f"你是行程管理专家。用户说：{user_input}\n\n请帮助店长管理行程，包括创建、编辑、查看行程，生成概要介绍等。"
    )
    return {"response": response.content if hasattr(response, "content") else str(response), "agent": "trip_manager", "data": {}}


async def _handle_script_writer(llm, user_input: str, db) -> dict:
    """Handle script generation requests."""
    from sqlalchemy import select
    from app.models.trip import Trip

    # Try to find the referenced trip
    trip = None
    for keyword in ["丽江", "三亚", "东京", "京都", "云南", "海南", "日本"]:
        if keyword in user_input:
            result = await db.execute(
                select(Trip).where(Trip.destination.ilike(f"%{keyword}%"), Trip.status == "active")
            )
            trip = result.scalar_one_or_none()
            if trip:
                break

    if not trip:
        # Get the first featured trip
        result = await db.execute(
            select(Trip).where(Trip.status == "active", Trip.is_featured == True)  # noqa: E712
        )
        trip = result.scalar_one_or_none()

    if not trip:
        return {"response": "请先指定一个行程（如：为丽江行程生成脚本），或先导入行程数据。", "agent": "script_writer", "data": {}}

    # Build trip context
    schedules_text = ""
    if trip.schedules:
        for s in trip.schedules:
            schedules_text += f"第{s.day_number}天 - {s.theme or ''}: {s.description or ''}\n"

    prompt = f"""你是专业的短视频文案专家。为以下旅游行程创作一段5分钟(约1200字)的短视频脚本。

行程: {trip.title}
目的地: {trip.destination}
天数: {trip.duration_days}天
价格: ¥{trip.price_adult}/人
特色: {', '.join(trip.highlights or [])}

日程:
{schedules_text}

脚本结构：
1. 开头钩子(15秒, ~50字)
2. 行程精华(3分钟, ~700字)
3. 细节展开(1分钟, ~300字)
4. 结尾引导(30秒, ~150字)

要求：口语化、有感染力、适合配音朗读、每个段落标注建议配图场景。"""

    response = await llm.ainvoke(prompt)
    script_text = response.content if hasattr(response, "content") else str(response)

    # Save to database
    from app.models.video_script import VideoScript
    script = VideoScript(
        trip_id=trip.id,
        title=f"{trip.title}短视频脚本",
        platform="抖音",
        duration_seconds=300,
        script_content=script_text,
        status="draft",
    )
    db.add(script)

    return {"response": script_text, "agent": "script_writer", "data": {"trip_id": str(trip.id), "script_id": str(script.id)}}


async def _handle_customer_profile(llm, user_input: str, db, role: str, user_id: str) -> dict:
    """Handle customer profile analysis."""
    from sqlalchemy import select
    from app.models.customer import Customer, CustomerProfile
    from app.models.order import Order
    from app.models.trip import Trip

    if role != "shop_owner":
        response = await llm.ainvoke("你是客户画像助手。用户是普通用户，请引导他们查看自己的旅行偏好。")
        return {"response": response.content if hasattr(response, "content") else str(response), "agent": "customer_profile", "data": {}}

    # Try to find customer by phone or name in input
    import re
    customer = None
    phone_match = re.search(r'1[3-9]\d{9}', user_input)
    if phone_match:
        result = await db.execute(select(Customer).where(Customer.phone == phone_match.group()))
        customer = result.scalar_one_or_none()

    if not customer:
        response = await llm.ainvoke(
            f"请告知用户需要指定客户手机号才能分析画像。用户说：{user_input}"
        )
        return {"response": response.content if hasattr(response, "content") else str(response), "agent": "customer_profile", "data": {}}

    # Gather data
    orders = (await db.execute(
        select(Order).where(Order.customer_id == customer.id).order_by(Order.created_at.desc())
    )).scalars().all()

    destinations = []
    total_spend = 0
    for o in orders:
        trip_r = await db.execute(select(Trip).where(Trip.id == o.trip_id))
        t = trip_r.scalar_one_or_none()
        if t:
            destinations.append(t.destination)
        total_spend += o.total_price or 0

    context = f"""客户: {customer.name or customer.phone}
总订单: {len(orders)} | 总消费: ¥{total_spend}
目的地: {', '.join(set(destinations)) if destinations else '无记录'}

请分析客户画像(100-150字)，包括偏好、消费层级、兴趣标签。"""

    response = await llm.ainvoke(context)
    return {"response": response.content if hasattr(response, "content") else str(response), "agent": "customer_profile", "data": {"customer_id": str(customer.id)}}


async def _handle_recommendation(llm, user_input: str, db, user_id: str) -> dict:
    """Handle trip recommendation."""
    from sqlalchemy import select
    from app.models.trip import Trip
    from app.models.customer import CustomerProfile

    # Get user profile
    profile = None
    if user_id:
        result = await db.execute(select(CustomerProfile).where(CustomerProfile.customer_id == user_id))
        profile = result.scalar_one_or_none()

    # Search trips matching the query
    query = select(Trip).where(Trip.status == "active")

    # Simple keyword-based filtering
    keyword_map = {
        "海边": "%三亚%", "海岛": "%三亚%", "三亚": "%三亚%", "海南": "%海南%",
        "丽江": "%丽江%", "云南": "%云南%",
        "日本": "%日本%", "东京": "%日本%",
    }
    for kw, pattern in keyword_map.items():
        if kw in user_input:
            query = query.where(Trip.destination.ilike(pattern))
            break

    # Budget filter
    import re
    budget_match = re.search(r'(\d{3,5})\s*元|预算\s*(\d{3,5})|(\d{3,5})\s*以内', user_input)
    if budget_match:
        budget = int(budget_match.group(1) or budget_match.group(2) or budget_match.group(3) or 5000)
        query = query.where(Trip.price_adult <= budget)

    result = await db.execute(query.limit(6))
    trips = result.scalars().all()

    if trips:
        trips_context = "\n\n".join(
            f"[{i}] {t.title}\n目的地: {t.destination}\n{t.duration_days}天 | ¥{t.price_adult}/人\n"
            f"特色: {', '.join(t.highlights or [])}\n简介: {t.summary or ''}"
            for i, t in enumerate(trips)
        )

        profile_context = ""
        if profile and profile.profile_summary:
            profile_context = f"\n用户偏好: {profile.profile_summary}"

        prompt = f"""你是旅行推荐专家。根据用户需求推荐最匹配的行程。

用户需求: {user_input}
{profile_context}

候选行程:
{trips_context}

请推荐TOP3，说明匹配度和推荐理由。"""

        response = await llm.ainvoke(prompt)
    else:
        response = await llm.ainvoke(
            f"用户需求: {user_input}\n当前没有完全匹配的行程。请友好告知并给出替代建议。"
        )

    return {
        "response": response.content if hasattr(response, "content") else str(response),
        "agent": "recommendation",
        "data": {"trips": [{"id": str(t.id), "title": t.title} for t in trips]},
    }


async def _handle_trip_support(llm, user_input: str, db, user_id: str) -> dict:
    """Handle trip support across lifecycle."""
    from sqlalchemy import select
    from app.models.order import Order
    from app.models.trip import Trip

    # Gather user orders for context
    orders = (await db.execute(
        select(Order).where(Order.customer_id == user_id).order_by(Order.created_at.desc()).limit(5)
    )).scalars().all()

    order_context = ""
    if orders:
        order_context = "\n用户订单:\n"
        for o in orders:
            trip_r = await db.execute(select(Trip).where(Trip.id == o.trip_id))
            t = trip_r.scalar_one_or_none()
            status_cn = {
                "inquiry": "咨询中", "reserved": "已预订", "confirmed": "已确认",
                "paid": "已付款", "pre_trip": "待出发", "in_trip": "旅行中",
                "completed": "已完成", "cancelled": "已取消",
            }.get(o.status, o.status)
            order_context += f"- {o.order_code}: {t.title if t else '未知'} ({status_cn})\n"

    response = await llm.ainvoke(
        f"你是旅行全程服务管家。{order_context}\n用户问：{user_input}\n\n请提供实用的旅行服务支持。如果是报名前，提醒准备事项；行程中，提供即时帮助；行程后，引导评价反馈。"
    )
    return {"response": response.content if hasattr(response, "content") else str(response), "agent": "trip_support", "data": {}}


async def _handle_history(llm, user_input: str, db, user_id: str) -> dict:
    """Handle order history queries."""
    from sqlalchemy import select, func
    from app.models.order import Order
    from app.models.trip import Trip

    orders = (await db.execute(
        select(Order).where(Order.customer_id == user_id).order_by(Order.departure_date.desc().nullslast())
    )).scalars().all()

    if not orders:
        return {"response": "你还没有任何订单记录。去浏览推荐行程，开始你的第一次旅行吧！🧭", "agent": "history_agent", "data": {"orders": []}}

    total_spend = sum(o.total_price or 0 for o in orders)
    destinations = set()
    for o in orders:
        trip_r = await db.execute(select(Trip).where(Trip.id == o.trip_id))
        t = trip_r.scalar_one_or_none()
        if t and o.status == "completed":
            destinations.add(t.destination)

    orders_list = ""
    for o in orders[:10]:
        trip_r = await db.execute(select(Trip).where(Trip.id == o.trip_id))
        t = trip_r.scalar_one_or_none()
        status_cn = {"completed": "✅已完成", "cancelled": "❌已取消", "reserved": "📌已预订", "confirmed": "✔️已确认", "paid": "💰已付款", "pre_trip": "🎒待出发", "in_trip": "🧳旅行中"}.get(o.status, o.status)
        orders_list += f"- {o.order_code}: {t.title if t else '未知'} | {o.departure_date} | {status_cn} | ¥{o.total_price or 0}\n"

    response = await llm.ainvoke(
        f"用户旅行历史：共{len(orders)}个订单，总消费¥{total_spend}，去过{len(destinations)}个目的地({', '.join(destinations)})。\n\n{orders_list}\n\n请温暖地帮用户回顾旅行经历，唤起美好回忆。"
    )
    return {"response": response.content if hasattr(response, "content") else str(response), "agent": "history_agent", "data": {"total_orders": len(orders), "total_spend": total_spend}}


async def _handle_general(llm, user_input: str, role: str) -> dict:
    """Handle general queries."""
    role_text = "店长" if role == "shop_owner" else "游客"
    response = await llm.ainvoke(
        f"你是欢游旅行社的AI助手。当前用户角色：{role_text}。\n"
        f"你能提供的服务：行程推荐、报名咨询、行前准备、行中支持、行后反馈（游客端）；\n"
        f"行程管理、文件导入、脚本生成、客户画像（店长端）。\n\n"
        f"用户说：{user_input}\n请友好地回复。"
    )
    return {"response": response.content if hasattr(response, "content") else str(response), "agent": "general", "data": {}}


# ── API Endpoints ──

@router.post("/chat")
async def agent_chat(
    message: str = Query(..., description="用户输入消息"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Chat with the AI travel agent.

    Routes user intent to specialized agents:
    - trip_manager: Trip CRUD, file import, summaries
    - script_writer: Video script generation (4-stage pipeline)
    - recommendation: Smart trip recommendations via RAG
    - trip_support: Pre/in/post trip lifecycle support
    - customer_profile: Customer behavior analysis
    - history_agent: Order history and travel timeline
    """
    if not session_id:
        session_id = str(uuid.uuid4())

    # Build LLM
    llm = await _build_llm()
    if llm is None:
        return {
            "response": "AI服务尚未配置。请在.env中设置DEEPSEEK_API_KEY或DASHSCOPE_API_KEY后重启服务。\n\n"
                        "获取API Key:\n- DeepSeek: https://platform.deepseek.com\n- 通义千问: https://dashscope.aliyun.com",
            "session_id": session_id,
            "agent": "system",
        }

    # Route and execute
    result = await _route_and_execute(
        llm=llm,
        user_input=message,
        role=current_user.role,
        user_id=str(current_user.id),
        db=db,
    )

    # Save conversation
    conv_user = Conversation(
        customer_id=current_user.id,
        session_id=session_id,
        role="user",
        content=message,
        metadata_={"type": "user_message"},
    )
    db.add(conv_user)

    conv_agent = Conversation(
        customer_id=current_user.id,
        session_id=session_id,
        role="assistant",
        agent_name=result["agent"],
        content=result["response"],
        metadata_={"type": "agent_response", "data": result.get("data", {})},
    )
    db.add(conv_agent)

    return {
        "response": result["response"],
        "session_id": session_id,
        "agent": result["agent"],
    }


@router.post("/chat/stream")
async def agent_chat_stream(
    message: str = Query(..., description="用户输入消息"),
    session_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: Customer = Depends(get_current_user),
):
    """Chat with the AI travel agent (SSE streaming)."""
    if not session_id:
        session_id = str(uuid.uuid4())

    async def event_generator():
        llm = await _build_llm()
        if llm is None:
            yield {"event": "error", "data": "AI服务未配置，请设置API Key"}
            return

        try:
            # For streaming, we bypass the complex routing and use direct LLM
            # The routing adds non-streamable overhead
            result = await _route_and_execute(
                llm=llm, user_input=message, role=current_user.role,
                user_id=str(current_user.id), db=db,
            )
            # Send full response as single chunk (simplified streaming)
            response_text = result["response"]
            chunk_size = 10
            for i in range(0, len(response_text), chunk_size):
                yield {"event": "message", "data": response_text[i:i+chunk_size]}
                import asyncio
                await asyncio.sleep(0.02)
            yield {"event": "done", "data": json.dumps({"session_id": session_id, "agent": result["agent"]})}
        except Exception as e:
            yield {"event": "error", "data": str(e)}

    return EventSourceResponse(event_generator())
