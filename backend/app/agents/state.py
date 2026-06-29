"""LangGraph AgentState definition for the HuanYou multi-agent system."""

from typing import Annotated, Optional, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state across all agents in the LangGraph supervisor.

    This state is passed between agents during execution and is
    checkpointed for conversation persistence.
    """

    # ── Conversation ──
    messages: Annotated[list, add_messages]

    # ── User context ──
    user_id: str
    role: str  # "shop_owner" | "user"
    session_id: str

    # ── Agent routing ──
    next_agent: str  # which agent to invoke next
    agent_outputs: dict  # {"agent_name": output_data}

    # ── Trip context (populated by RAG) ──
    retrieved_trips: list[dict]
    active_trip_id: Optional[str]

    # ── Script generation context ──
    script_state: dict  # {stage, draft, polish_count}

    # ── Recommendation context ──
    extracted_needs: dict  # {destination_preference, budget_range, etc.}
    recommendations: list[dict]

    # ── Support context ──
    support_stage: str  # pre_trip / in_trip / post_trip

    # ── Memory context ──
    user_memories: list[str]
    user_profile: Optional[dict]

    # ── History context ──
    history_orders: list[dict]
