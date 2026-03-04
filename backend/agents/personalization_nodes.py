"""
agents/personalization_nodes.py — Phase 15 LangGraph personalization node.

Runs after aggregate + llm_reasoning nodes.
Generates a full RecommendationResponse and appends it to state['result'].
"""

import logging
from agents.state import AgentState
from memory.recommendation_engine import build_recommendation_payload
from memory.personalization_service import adapt_insights_to_preferences

logger = logging.getLogger(__name__)


async def personalization_node(state: AgentState) -> AgentState:
    """
    Phase 15 — Personalization & Smart Recommendations node.
    
    1. Adapts synthesized insights based on user risk tolerance.
    2. Builds a full RecommendationResponse (next actions, similar companies,
       watchlist, behavioral profile, memory reminders).
    3. Attaches both to state['result'] for the executor to surface.
    
    Fully deterministic — no LLM calls.
    Non-fatal: if anything fails, the node logs and continues.
    """
    try:
        result = state.get("result", {}) or {}
        preferences = state.get("preferences") or {}
        risk = state.get("risk") or result.get("risk") or {}
        forecast = state.get("forecast") or result.get("forecast") or {}
        fundamentals = state.get("fundamentals") or result.get("fundamentals") or {}
        memory_recall = state.get("memory_recall") or []
        insights = result.get("insights") or {}

        # Feature 1 — Risk-adaptive insight framing
        if insights and preferences:
            adapted = adapt_insights_to_preferences(insights, risk, preferences)
            result["insights"] = adapted

        # Features 2–6 — Full recommendation payload
        recommendations = await build_recommendation_payload(
            ticker=state["ticker"],
            mode=state["mode"],
            user_id=state["user_id"],
            preferences=preferences,
            risk=risk,
            forecast=forecast,
            fundamentals=fundamentals,
            memory_recall=memory_recall,
        )

        result["recommendations"] = recommendations
        state["result"] = result
        state["recommendations"] = recommendations

        logger.info(
            f"Personalization node complete for {state['ticker']} — "
            f"{len(recommendations.get('next_actions', []))} actions, "
            f"{len(recommendations.get('similar_companies', []))} similar companies."
        )

    except Exception as e:
        logger.error(f"personalization_node failed (non-fatal): {e}")
        # Don't re-raise — the rest of the agent must continue working

    return state
