"""
RecommendationAgent — 智能行程推荐.

Handles:
- Understanding user requirements from natural language
- Extracting structured needs (destination, budget, dates, preferences)
- Searching trips via RAG hybrid retrieval
- Filtering by budget and constraints
- Ranking and explaining recommendations
"""

from sqlalchemy import select

from app.agents.state import AgentState
from app.models.trip import Trip
from app.models.customer import Customer, CustomerProfile


RECOMMENDATION_PROMPT = """你是旅游推荐专家。根据用户需求，推荐最匹配的旅游行程。

你的工作流程：
1. **理解需求**：从用户描述中提取：目的地偏好、预算、天数、人数、兴趣爱好
2. **搜索匹配**：从知识库中检索符合条件的行程
3. **智能筛选**：根据预算、时间等约束过滤
4. **对比推荐**：比较候选方案，给出TOP3推荐
5. **解释理由**：用自然语言说明为什么推荐每个行程

推荐原则：
- 尊重用户预算，不超过预算上限
- 考虑季节因素
- 优先推荐与用户历史偏好匹配的行程
- 说明每个推荐的独特优势

请以热情、专业的中文回复，包含清晰的推荐理由。"""


async def execute(state: AgentState, llm, db_session) -> dict:
    """Execute recommendation logic.

    Steps:
    1. Extract structured needs from user input
    2. Search trips via database queries
    3. Rank and explain recommendations
    """
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message) if last_message else ""

    # Step 1: Extract needs using LLM
    extraction_prompt = f"""从用户的旅游需求描述中，提取结构化信息。返回JSON格式。

用户输入: {user_input}

请提取以下字段（如未提及填null）:
{{"destination_preference": "想去的目的地类型或地点",
  "budget_max": 预算上限数字(元),
  "duration_days": 期望天数,
  "group_type": "家庭/情侣/朋友/独自",
  "season": "出行季节",
  "interests": ["兴趣标签列表如: 自然风光, 美食, 徒步, 购物"],
  "category": "国内游/出境游/周边游"}}"""

    extracted_needs = {}
    try:
        import json
        response = await llm.ainvoke(extraction_prompt)
        response_text = response.content if hasattr(response, "content") else str(response)
        response_text = response_text.strip().removeprefix("```json").removesuffix("```").strip()
        extracted_needs = json.loads(response_text)
    except Exception:
        extracted_needs = {"destination_preference": user_input}

    # Step 2: Retrieve user profile (if available)
    user_profile = state.get("user_profile")
    user_id = state.get("user_id")

    if db_session and user_id and not user_profile:
        profile_result = await db_session.execute(
            select(CustomerProfile).where(CustomerProfile.customer_id == user_id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile:
            user_profile = {
                "preferred_destinations": profile.preferred_destinations or [],
                "preferred_categories": profile.preferred_categories or [],
                "budget_range_min": profile.budget_range_min,
                "budget_range_max": profile.budget_range_max,
                "preferred_duration": profile.preferred_duration_days,
                "interests": profile.interest_tags or [],
                "travel_style": profile.travel_style,
            }

    # Step 3: Search trips from database
    candidates = []
    if db_session:
        query = select(Trip).where(Trip.status == "active")

        dest_pref = extracted_needs.get("destination_preference", "")
        if dest_pref:
            # Search by destination
            for keyword in ["海边", "海岛", "三亚", "海滨"]:
                if keyword in dest_pref:
                    query = query.where(Trip.destination.ilike("%三亚%") | Trip.destination.ilike("%海南%"))
                    break
            for keyword in ["山", "自然", "风景"]:
                if keyword in dest_pref:
                    query = query.where(
                        Trip.destination.ilike("%山%") | Trip.destination.ilike("%丽江%")
                    )
                    break

        # Budget filter
        budget_max = extracted_needs.get("budget_max")
        if budget_max:
            query = query.where(Trip.price_adult <= budget_max)

        # Duration filter
        duration = extracted_needs.get("duration_days")
        if duration:
            query = query.where(Trip.duration_days >= duration - 1)
            query = query.where(Trip.duration_days <= duration + 2)

        result = await db_session.execute(query.limit(10))
        candidates = result.scalars().all()

    # Step 4: Build recommendation response
    if candidates:
        trips_context = "\n\n".join(
            f"[{i}] {t.title}\n目的地: {t.destination}\n天数: {t.duration_days}天\n"
            f"价格: ¥{t.price_adult}/人\n特色: {', '.join(t.highlights or [])}\n"
            f"简介: {t.summary or t.detailed_description or ''}"
            for i, t in enumerate(candidates)
        )

        profile_context = ""
        if user_profile:
            profile_context = f"\n用户偏好: 喜欢{user_profile.get('preferred_destinations', [])}，兴趣: {user_profile.get('interests', [])}"

        final_prompt = f"""以下是符合用户需求的行程候选：

{trips_context}
{profile_context}

用户需求: {user_input}

请推荐TOP3最匹配的行程，对每个推荐给出：
1. 匹配度评分(0-100)
2. 推荐理由(基于用户需求和偏好)
3. 与预算的对比
"""

        response = await llm.ainvoke([
            {"role": "system", "content": RECOMMENDATION_PROMPT},
            {"role": "user", "content": final_prompt},
        ])
    else:
        # No candidates found - generate helpful suggestion
        response = await llm.ainvoke([
            {"role": "system", "content": RECOMMENDATION_PROMPT},
            {"role": "user", "content": f"""用户需求: {user_input}

当前知识库中没有完全匹配的行程。请：
1. 友好地告知用户暂时没有完全匹配的行程
2. 根据用户需求给出目的地建议和预算参考
3. 建议用户可以调整哪些条件以获得更好的推荐
4. 推荐用户联系店长咨询定制行程"""},
        ])

    # Save recommendations to state
    recommendations = [
        {
            "trip_id": str(t.id) if hasattr(t, 'id') else "",
            "title": t.title if hasattr(t, 'title') else "",
            "destination": t.destination if hasattr(t, 'destination') else "",
            "price_adult": t.price_adult if hasattr(t, 'price_adult') else None,
        }
        for t in candidates[:3]
    ]

    return {
        "messages": [response],
        "agent_outputs": {"recommendation": response.content if hasattr(response, "content") else str(response)},
        "extracted_needs": extracted_needs,
        "recommendations": recommendations,
    }
