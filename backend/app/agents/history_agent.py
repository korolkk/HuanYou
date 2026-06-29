"""
HistoryAgent — 历史行程查询和回顾.

Handles:
- Order history lookup
- Travel timeline visualization
- Trip statistics and summaries
- Past trip detail retrieval
"""

from sqlalchemy import select, func

from app.agents.state import AgentState
from app.models.order import Order
from app.models.trip import Trip
from app.models.feedback import Feedback


HISTORY_PROMPT = """你是历史行程查询助手。帮助用户回顾和管理他们的旅行历史。

你的能力：
1. **订单查询**：查看历史订单、当前订单状态
2. **行程回顾**：查看过去行程的详细信息
3. **统计分析**：旅行总天数、消费总额、到访目的地等
4. **评价回顾**：查看提交过的评价和反馈
5. **再次预订**：基于历史行程推荐复购

请以温暖、回忆感的中文回复，唤起用户美好的旅行记忆。"""


async def execute(state: AgentState, llm, db_session) -> dict:
    """Handle history queries - order history and travel timeline."""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message) if last_message else ""

    user_id = state.get("user_id")

    if not db_session or not user_id:
        response = await llm.ainvoke([
            {"role": "system", "content": HISTORY_PROMPT},
            {"role": "user", "content": "请告知用户需要登录才能查看历史行程。"},
        ])
        return {
            "messages": [response],
            "agent_outputs": {"history_agent": response.content if hasattr(response, "content") else str(response)},
        }

    # Gather all orders
    result = await db_session.execute(
        select(Order)
        .where(Order.customer_id == user_id)
        .order_by(Order.departure_date.desc().nullslast())
    )
    orders = result.scalars().all()

    if not orders:
        response = await llm.ainvoke([
            {"role": "system", "content": HISTORY_PROMPT},
            {"role": "user", "content": "用户目前没有任何订单记录。请友好地告诉用户并建议他们浏览推荐行程。"},
        ])
        return {
            "messages": [response],
            "agent_outputs": {},
            "history_orders": [],
        }

    # Build detailed order context
    orders_context = []
    stats = {
        "total_orders": len(orders),
        "completed": 0,
        "upcoming": 0,
        "total_spend": 0,
        "destinations_visited": set(),
        "total_days": 0,
    }

    for o in orders:
        trip_result = await db_session.execute(select(Trip).where(Trip.id == o.trip_id))
        trip = trip_result.scalar_one_or_none()

        trip_title = trip.title if trip else "未知行程"
        destination = trip.destination if trip else "未知"
        status_cn = {
            "inquiry": "咨询中", "reserved": "已预订", "confirmed": "已确认",
            "paid": "已付款", "pre_trip": "准备出发", "in_trip": "旅行中",
            "completed": "已完成", "cancelled": "已取消", "refunded": "已退款",
        }.get(o.status, o.status)

        if o.status in ("completed", "in_trip"):
            stats["destinations_visited"].add(destination)
            if trip:
                stats["total_days"] += trip.duration_days
        if o.status == "completed":
            stats["completed"] += 1
        if o.status in ("reserved", "confirmed", "paid", "pre_trip"):
            stats["upcoming"] += 1
        stats["total_spend"] += o.total_price or 0

        orders_context.append(
            f"- [{status_cn}] {o.order_code}: {trip_title} ({destination}), "
            f"出发: {o.departure_date}, {o.num_adults + o.num_children}人, "
            f"¥{o.total_price or '待定'}"
        )

    # Check if asking for stats
    if any(kw in user_input for kw in ["统计", "总计", "消费", "去了多少", "去了几个"]):
        stats_text = f"""旅行统计:
- 总订单: {stats['total_orders']}个
- 已完成: {stats['completed']}个
- 即将出行: {stats['upcoming']}个
- 总消费: ¥{stats['total_spend']}
- 到访目的地: {len(stats['destinations_visited'])}个 ({', '.join(stats['destinations_visited'])})
- 累计旅行天数: {stats['total_days']}天"""

        response = await llm.ainvoke([
            {"role": "system", "content": HISTORY_PROMPT},
            {"role": "user", "content": f"用户的旅行数据:\n{stats_text}\n\n请生成一段温暖有趣的旅行总结。"},
        ])
    else:
        context = f"用户的历史订单 ({len(orders)}个):\n" + "\n".join(orders_context)
        response = await llm.ainvoke([
            {"role": "system", "content": HISTORY_PROMPT},
            {"role": "user", "content": f"用户查询: {user_input}\n\n{context}\n\n请友好地回复，帮助用户回顾行程。"},
        ])

    return {
        "messages": [response],
        "agent_outputs": {"history_agent": response.content if hasattr(response, "content") else str(response)},
        "history_orders": [
            {
                "order_code": o.order_code,
                "status": o.status,
                "departure_date": str(o.departure_date) if o.departure_date else None,
            }
            for o in orders[:10]
        ],
    }
