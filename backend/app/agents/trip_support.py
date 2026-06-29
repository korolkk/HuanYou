"""
TripSupportAgent — 全流程服务支持.

Covers the full trip lifecycle:
- Pre-trip: booking info, weather, packing, visa, meeting points
- In-trip: weather, attraction guides, food recs, emergency contacts
- Post-trip: feedback, complaints, documents, next trip suggestions
"""

from sqlalchemy import select

from app.agents.state import AgentState
from app.models.order import Order
from app.models.trip import Trip


TRIP_SUPPORT_PROMPT = """你是旅行全程服务专家，覆盖从报名到回团的全流程支持。

你的服务范围：

**报名前 (Pre-Trip)**
- 报名信息确认：价格、团期、余位
- 签证材料清单和要求
- 行前物品准备清单（衣物、药品、证件）
- 当地天气查询和建议
- 集合时间、地点通知
- 合同和保险说明

**行程中 (In-Trip)**
- 每日天气预报和穿衣建议
- 景点历史文化讲解
- 当地美食推荐
- 交通路线指引
- 紧急情况处理（迷路、生病、丢失物品）
- 导游/全陪联系方式

**行程后 (Post-Trip)**
- 满意度评价收集
- 投诉和建议处理
- 发票和合同索取
- 下次出行推荐
- 照片分享和游记鼓励

请根据用户问题的上下文，判断处于哪个阶段并提供相应的帮助。
回复风格：实用、细致、温暖，像一位贴心的旅行管家。"""


async def execute(state: AgentState, llm, db_session) -> dict:
    """Handle trip support queries across all lifecycle stages."""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message) if last_message else ""

    # Detect the support stage and relevant order context
    support_stage = state.get("support_stage", "general")

    # Determine stage from keywords
    pre_trip_kw = ["报名", "签证", "准备", "带什么", "集合", "合同", "保险", "改签", "退团"]
    in_trip_kw = ["天气", "景点", "美食", "迷路", "医院", "急救", "导游电话", "现在在", "到了"]
    post_trip_kw = ["评价", "投诉", "发票", "反馈", "建议", "不满意", "照片", "游记"]

    if any(kw in user_input for kw in pre_trip_kw):
        support_stage = "pre_trip"
    elif any(kw in user_input for kw in in_trip_kw):
        support_stage = "in_trip"
    elif any(kw in user_input for kw in post_trip_kw):
        support_stage = "post_trip"

    # Gather order context if available
    order_context = ""
    if db_session:
        user_id = state.get("user_id")
        active_order_id = state.get("active_trip_id")  # Could be order ID

        if user_id:
            # Find user's most recent orders
            result = await db_session.execute(
                select(Order)
                .where(Order.customer_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(3)
            )
            recent_orders = result.scalars().all()

            if recent_orders:
                order_context = "\n用户最近的订单:\n"
                for o in recent_orders:
                    trip_result = await db_session.execute(
                        select(Trip).where(Trip.id == o.trip_id)
                    )
                    trip = trip_result.scalar_one_or_none()
                    order_context += (
                        f"- 订单{o.order_code}: {trip.title if trip else '未知行程'}, "
                        f"出发日期{o.departure_date}, 状态{o.status}\n"
                    )

    # Build system prompt based on stage
    stage_instructions = {
        "pre_trip": "用户正在准备出行。提供实用信息：证件、物品清单、天气、集合通知。",
        "in_trip": "用户正在旅行中。提供即时帮助：天气、路线、景点讲解、紧急支持。",
        "post_trip": "用户已完成旅行。收集反馈、处理投诉、鼓励分享、推荐下次行程。",
        "general": "判断用户处于哪个阶段，提供对应的旅行服务支持。",
    }

    system_prompt = f"""{TRIP_SUPPORT_PROMPT}

当前阶段：{support_stage}
指导：{stage_instructions.get(support_stage, '')}
{order_context}"""

    response = await llm.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ])

    return {
        "messages": [response],
        "agent_outputs": {"trip_support": response.content if hasattr(response, "content") else str(response)},
        "support_stage": support_stage,
    }
