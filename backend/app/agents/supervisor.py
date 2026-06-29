"""LangGraph Supervisor Agent — routes user intent to specialized worker agents.

Architecture:
    User Message → Supervisor (intent routing) → Worker Agent → Response

The supervisor pattern uses a central router agent that:
1. Analyzes user input to determine intent
2. Delegates to the appropriate worker agent (TripManager, Recommendation, etc.)
3. Returns structured responses

Worker agents are implemented as async Python functions that call LLM with
specialized tool sets. Full LangGraph tool-calling agents will be enabled
when API keys are configured.
"""

import json
import uuid
from typing import Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from app.agents.state import AgentState
from app.config import get_settings


# ── Intent Detection Prompt ──

INTENT_PROMPT = """你是欢游旅行社的AI主管。根据用户输入，判断用户意图并选择最合适的处理Agent。

用户角色: {role}
用户输入: {input}

可用的Agent:
1. trip_manager - 行程管理：查看行程、创建行程、修改行程、导入行程文件
2. script_writer - 视频脚本生成：为行程生成短视频文案
3. customer_profile - 客户画像：查看和分析客户数据、用户画像
4. recommendation - 智能推荐：根据需求推荐行程、比较方案
5. trip_support - 行程服务：报名咨询、行前准备、行中问题、行后反馈
6. history_agent - 历史查询：查看历史订单、旅行动态
7. general - 通用问答：介绍、帮助、问候等

请返回JSON格式:
{{"agent": "选择的agent名称", "reason": "简短理由", "language": "中文"}}

只返回JSON，不要其他内容。"""


async def detect_intent(state: AgentState, llm) -> dict:
    """Analyze user input to determine which agent should handle it."""
    messages = state.get("messages", [])
    if not messages:
        return {"next_agent": "general"}

    last_message = messages[-1]
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message)

    role = state.get("role", "user")

    # Quick keyword-based routing for common patterns
    agent = _quick_route(user_input, role)
    if agent:
        return {"next_agent": agent}

    # Use LLM for complex intent detection
    try:
        prompt = INTENT_PROMPT.format(role=role, input=user_input[:500])
        response = await llm.ainvoke(prompt)

        # Parse JSON from response
        response_text = response.content if hasattr(response, "content") else str(response)
        # Strip markdown code fences if present
        response_text = response_text.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(response_text)
        agent = result.get("agent", "general")
    except Exception:
        agent = "general"

    return {"next_agent": agent}


def _quick_route(user_input: str, role: str) -> Optional[str]:
    """Fast keyword-based routing to avoid LLM call for obvious intents."""
    text = user_input.lower()

    # Shop owner intents
    if role == "shop_owner":
        if any(kw in text for kw in ["导入", "上传", "读取", "文件"]):
            return "trip_manager"
        if any(kw in text for kw in ["生成脚本", "短视频", "文案", "脚本"]):
            return "script_writer"
        if any(kw in text for kw in ["客户画像", "用户画像", "分析客户", "客户分析"]):
            return "customer_profile"

    # User intents
    if role == "user":
        if any(kw in text for kw in ["推荐", "建议", "适合", "帮我找", "想去"]):
            return "recommendation"
        if any(kw in text for kw in ["报名", "注意事项", "天气", "准备", "集合", "导游",
                                       "紧急", "评价", "投诉", "发票", "合同", "改签"]):
            return "trip_support"
        if any(kw in text for kw in ["历史", "以前的", "过去", "记录", "订单"]):
            return "history_agent"

    # Common intents for both roles
    if any(kw in text for kw in ["行程", "线路", "线路详情", "行程详情"]):
        if role == "shop_owner":
            return "trip_manager"
        return "recommendation"

    if any(kw in text for kw in ["你好", "帮助", "介绍", "功能", "怎么用"]):
        return "general"

    return None


# ── Agent Node Functions ──

async def trip_manager_node(state: AgentState, llm, db_session) -> dict:
    """TripManager Agent: handles trip creation, viewing, file import, summaries."""
    from app.agents.trip_manager import execute as trip_manager_execute
    return await trip_manager_execute(state, llm, db_session)


async def script_writer_node(state: AgentState, llm, db_session) -> dict:
    """ScriptWriter Agent: generates and polishes video scripts."""
    from app.agents.script_writer import execute as script_writer_execute
    return await script_writer_execute(state, llm, db_session)


async def recommendation_node(state: AgentState, llm, db_session) -> dict:
    """Recommendation Agent: matches user needs to trips via RAG."""
    from app.agents.recommendation import execute as recommendation_execute
    return await recommendation_execute(state, llm, db_session)


async def trip_support_node(state: AgentState, llm, db_session) -> dict:
    """TripSupport Agent: pre-trip, in-trip, post-trip service."""
    from app.agents.trip_support import execute as trip_support_execute
    return await trip_support_execute(state, llm, db_session)


async def customer_profile_node(state: AgentState, llm, db_session) -> dict:
    """CustomerProfile Agent: profile analysis and generation."""
    from app.agents.customer_profile import execute as profile_execute
    return await profile_execute(state, llm, db_session)


async def history_node(state: AgentState, llm, db_session) -> dict:
    """History Agent: order history and travel timeline."""
    from app.agents.history_agent import execute as history_execute
    return await history_execute(state, llm, db_session)


async def general_node(state: AgentState, llm, db_session) -> dict:
    """General assistant for greetings, help, and unclassified queries."""
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    user_input = last_message.content if hasattr(last_message, "content") else str(last_message) if last_message else ""

    response = await llm.ainvoke(
        f"你是欢游旅行社的AI助手。请友好地回答用户问题，介绍你能提供的服务。\n"
        f"用户: {user_input}\n"
        f"服务包括: 行程推荐、报名咨询、行前准备、行中支持、行后反馈、视频脚本生成、客户画像分析。"
    )
    return {
        "messages": [response],
        "agent_outputs": {"general": response.content if hasattr(response, "content") else str(response)},
    }


# ── Graph Construction ──

def build_supervisor(llm, checkpointer=None):
    """Build the LangGraph supervisor workflow.

    Args:
        llm: The LLM instance to use for all agents.
        checkpointer: Optional checkpointer for conversation persistence.

    Returns:
        Compiled LangGraph application.
    """
    workflow = StateGraph(AgentState)

    # Add all agent nodes
    workflow.add_node("detect_intent", lambda state: detect_intent(state, llm))
    workflow.add_node("trip_manager", lambda state: trip_manager_node(state, llm, None))
    workflow.add_node("script_writer", lambda state: script_writer_node(state, llm, None))
    workflow.add_node("recommendation", lambda state: recommendation_node(state, llm, None))
    workflow.add_node("trip_support", lambda state: trip_support_node(state, llm, None))
    workflow.add_node("customer_profile", lambda state: customer_profile_node(state, llm, None))
    workflow.add_node("history_agent", lambda state: history_node(state, llm, None))
    workflow.add_node("general", lambda state: general_node(state, llm, None))

    # Entry point: detect intent first
    workflow.set_entry_point("detect_intent")

    # Route from intent detection to the appropriate agent
    workflow.add_conditional_edges(
        "detect_intent",
        lambda state: state.get("next_agent", "general"),
        {
            "trip_manager": "trip_manager",
            "script_writer": "script_writer",
            "recommendation": "recommendation",
            "trip_support": "trip_support",
            "customer_profile": "customer_profile",
            "history_agent": "history_agent",
            "general": "general",
        },
    )

    # All agents terminate after their response
    workflow.add_edge("trip_manager", END)
    workflow.add_edge("script_writer", END)
    workflow.add_edge("recommendation", END)
    workflow.add_edge("trip_support", END)
    workflow.add_edge("customer_profile", END)
    workflow.add_edge("history_agent", END)
    workflow.add_edge("general", END)

    # Compile with checkpointing
    if checkpointer is None:
        checkpointer = SqliteSaver.from_conn_string(":memory:")

    app = workflow.compile(checkpointer=checkpointer)
    return app


# ── Helper: Get Agent Executor ──

async def get_agent_executor():
    """Create an LLM instance and build the agent executor.

    This is called by API routes to get a ready-to-use agent.
    Returns None if no LLM API key is configured.
    """
    settings = get_settings()

    if not settings.DEEPSEEK_API_KEY and not settings.DASHSCOPE_API_KEY:
        return None

    # Use DeepSeek as primary, fall back to Qwen
    if settings.DEEPSEEK_API_KEY:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=0.7,
            max_tokens=2048,
        )
    else:
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(
            model="qwen-max",
            api_key=settings.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            temperature=0.7,
            max_tokens=2048,
        )

    app = build_supervisor(llm)
    return app, llm
