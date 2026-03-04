"""
agents/llm_nodes.py — LangGraph node for LLM integration (Phase 13).

Contains `llm_reasoning_node` which runs AFTER `aggregate_node`
but BEFORE `memory_store_node` to add the LLM narrative directly
into the final AgentResponseData structure.
"""

import logging

from agents.state import AgentState
from llm.llm_service import enhance_narrative

logger = logging.getLogger(__name__)


async def llm_reasoning_node(state: AgentState) -> AgentState:
    """
    Optional LLM Enhancement Layer.
    Takes the structured insights and confidence data prepared by aggregate_node,
    and uses the LLM to rewrite it into a high-quality narrative.

    If LLM fails or is disabled, the deterministic summary remains the default.
    """
    result = state.get("result", {})
    insights = result.get("insights")
    confidence = result.get("confidence")

    if not insights:
        logger.debug("llm_reasoning_node skipped — no insights in state.result")
        return state

    try:
        # Enhance narrative
        llm_response = await enhance_narrative(
            insight_json=insights,
            ticker=state["ticker"],
            mode=state["mode"],
            confidence_data=confidence or {}
        )

        # We append a structured block to the insights dictionary
        # named 'llm_enhancement' that the API layer can pass along.
        state["result"]["insights"]["llm_enhancement"] = llm_response.model_dump()
        logger.info(f"LLM Narrative Enhancement complete for {state['ticker']} (Success={llm_response.llm_used})")
        
    except Exception as e:
        logger.error(f"llm_reasoning_node failed: {e}")
        # Append empty fallback block to keep schema happy
        state["result"]["insights"]["llm_enhancement"] = {
            "enhanced_text": insights.get("plain_language_summary", ""),
            "llm_used": False,
            "provider": "error",
            "tokens_used": 0,
            "estimated_cost": 0.0
        }

    return state
