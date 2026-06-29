"""
CustomerProfileAgent — 客户画像分析专家.

Analyzes customer data to generate comprehensive user profiles:
- Statistical analysis of booking history
- LLM-based preference extraction
- Customer segmentation
- Profile summary generation
"""

from sqlalchemy import select, func

from app.agents.state import AgentState
from app.models.customer import Customer, CustomerProfile
from app.models.order import Order
from app.models.trip import Trip
from app.models.feedback import Feedback


PROFILE_PROMPT = """你是客户画像分析专家。根据客户的历史行为数据，分析客户特征并生成用户画像。

分析维度：
1. **人口特征**: 年龄层、城市、职业推断
2. **旅行偏好**: 目的地偏好、类型偏好（自然/文化/海岛/城市等）
3. **消费能力**: 预算范围、消费频率
4. **行为模式**: 提前报名天数、出行季节、结伴类型
5. **兴趣标签**: 从行程内容推断的兴趣点
6. **特殊需求**: 饮食、住宿、交通等特殊要求

输出格式：
1. 自然语言画像摘要(100-150字)
2. 结构化标签列表"""


async def execute(state: AgentState, llm, db_session) -> dict:
    """Generate or retrieve customer profile analysis."""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message) if last_message else ""

    # Shop owner is querying about a specific customer
    # Try to find which customer they're asking about
    customer_id = None
    customer = None

    if db_session:
        user_id = state.get("user_id")
        role = state.get("role")

        # If shop owner, look for mentioned customer
        if role == "shop_owner":
            # Try to extract phone number from input
            import re
            phone_match = re.search(r'1[3-9]\d{9}', user_input)
            if phone_match:
                result = await db_session.execute(
                    select(Customer).where(Customer.phone == phone_match.group())
                )
                customer = result.scalar_one_or_none()

            if not customer:
                # Try by name
                for name_part in user_input.replace("的画像", "").replace("分析", "").split():
                    if len(name_part) >= 2:
                        result = await db_session.execute(
                            select(Customer).where(Customer.name.ilike(f"%{name_part}%"))
                        )
                        customer = result.scalar_one_or_none()
                        if customer:
                            break

        else:
            # User looking at their own profile
            result = await db_session.execute(
                select(Customer).where(Customer.id == user_id)
            )
            customer = result.scalar_one_or_none()

    if not customer or not db_session:
        response = await llm.ainvoke([
            {"role": "system", "content": PROFILE_PROMPT},
            {"role": "user", "content": "请说明你需要指定一个客户才能分析画像，询问用户想看哪个客户的画像。"},
        ])
        return {
            "messages": [response],
            "agent_outputs": {"customer_profile": response.content if hasattr(response, "content") else str(response)},
        }

    # Gather customer data
    orders_result = await db_session.execute(
        select(Order).where(Order.customer_id == customer.id).order_by(Order.created_at.desc())
    )
    orders = orders_result.scalars().all()

    feedbacks_result = await db_session.execute(
        select(Feedback).where(Feedback.customer_id == customer.id)
    )
    feedbacks = feedbacks_result.scalars().all()

    # Build analysis context
    total_orders = len(orders)
    completed_orders = sum(1 for o in orders if o.status == "completed")
    total_spend = sum(o.total_price or 0 for o in orders)

    destinations = []
    categories = []
    durations = []
    for o in orders:
        trip_result = await db_session.execute(select(Trip).where(Trip.id == o.trip_id))
        trip = trip_result.scalar_one_or_none()
        if trip:
            destinations.append(trip.destination)
            categories.append(trip.category)
            durations.append(trip.duration_days)

    avg_rating = 0
    if feedbacks:
        ratings = [f.rating_overall for f in feedbacks if f.rating_overall]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0

    context = f"""客户: {customer.name or '未知'}
手机: {customer.phone}
角色: {customer.role}

历史数据:
- 总订单数: {total_orders}
- 完成行程: {completed_orders}
- 总消费: ¥{total_spend}
- 目的地: {', '.join(set(destinations)) if destinations else '无'}
- 类型偏好: {', '.join(set(categories)) if categories else '无'}
- 平均天数: {sum(durations)/len(durations) if durations else 0:.0f}天
- 平均评分: {avg_rating:.1f}/5

请分析客户画像，生成100-150字的自然语言摘要和兴趣标签。"""

    response = await llm.ainvoke([
        {"role": "system", "content": PROFILE_PROMPT},
        {"role": "user", "content": context},
    ])

    # Update or create profile in database
    existing_profile = await db_session.execute(
        select(CustomerProfile).where(CustomerProfile.customer_id == customer.id)
    )
    profile = existing_profile.scalar_one_or_none()

    response_text = response.content if hasattr(response, "content") else str(response)

    if not profile:
        profile = CustomerProfile(
            customer_id=customer.id,
            preferred_destinations=list(set(destinations)) if destinations else [],
            preferred_categories=list(set(categories)) if categories else [],
            profile_summary=response_text[:500],
        )
        db_session.add(profile)
    else:
        profile.preferred_destinations = list(set(destinations)) if destinations else profile.preferred_destinations
        profile.preferred_categories = list(set(categories)) if categories else profile.preferred_categories
        profile.profile_summary = response_text[:500]

    return {
        "messages": [response],
        "agent_outputs": {"customer_profile": response_text},
    }
