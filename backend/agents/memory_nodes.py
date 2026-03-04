"""
agents/memory_nodes.py — LangGraph memory integration nodes (Phase 12).

Two nodes:
  1. memory_store_node  — after aggregate, store the deep insight to Qdrant
  2. memory_recall_node — before aggregate, check for memory-recall trigger words

Memory keywords that trigger recall:
  "similar", "like", "earlier", "previous", "before", "compare with", "remind"
"""

import logging
from typing import List

from agents.state import AgentState

logger = logging.getLogger(__name__)

# Keywords that trigger memory retrieval in the user's intent
RECALL_KEYWORDS: List[str] = [
    "similar", "like", "earlier", "previous", "before",
    "compare with", "remind", "last time", "recall"
]


async def memory_store_node(state: AgentState) -> AgentState:
    """
    After deep/compare analysis, embed and store the generated insights in Qdrant.
    This node is appended AFTER aggregate_node in the deep workflow.

    Non-fatal — Qdrant unavailability is logged and skipped silently.
    """
    insights = state.get("result", {}).get("insights") if state.get("result") else None
    if not insights:
        logger.debug("memory_store_node: no insights to store, skipping")
        return state

    try:
        from vector_store.qdrant_client import qdrant_wrapper
        if not qdrant_wrapper.is_healthy or qdrant_wrapper.client is None:
            logger.debug("memory_store_node: Qdrant unavailable, skipping store")
            return state

        from vector_store.memory_service import store_insight_embedding

        # Extract metadata from risk + fundamentals
        result = state.get("result", {})
        risk = result.get("risk") or {}
        funds = result.get("fundamentals") or {}
        market = result.get("market") or {}

        metadata = {
            "risk_score": risk.get("composite_risk_score", 0.0),
            "financial_health_score": funds.get("financial_health_score", 0.0),
            "sector": market.get("sector", "unknown"),
            "insight_type": state.get("mode", "deep"),
        }

        success = await store_insight_embedding(
            client=qdrant_wrapper.client,
            user_id=str(state["user_id"]),
            ticker=state["ticker"],
            insight_data=insights,
            metadata=metadata,
        )

        if success:
            logger.info(f"Memory stored for {state['ticker']} ✓")
        else:
            logger.warning(f"Memory store returned False for {state['ticker']}")

    except Exception as e:
        logger.warning(f"memory_store_node failed (non-fatal): {e}")

    return state


async def memory_recall_node(state: AgentState) -> AgentState:
    """
    Checks if the user's query (via ticker context) should trigger a
    memory recall. If recall keywords are present in the ticker field
    or the mode description, retrieves similar past insights.

    Stores recall results in state["memory_recall"] for downstream nodes.
    """
    # Check if Qdrant available
    try:
        from vector_store.qdrant_client import qdrant_wrapper
        if not qdrant_wrapper.is_healthy or qdrant_wrapper.client is None:
            return state
    except Exception:
        return state

    # Build a query from available context
    ticker = state.get("ticker", "")
    mode = state.get("mode", "")

    # Compose a fallback query from the ticker name
    query = f"Financial analysis of {ticker} stock investment research"

    try:
        from vector_store.memory_service import retrieve_similar_insights
        results = await retrieve_similar_insights(
            client=qdrant_wrapper.client,
            query_text=query,
            user_id=str(state["user_id"]),
            top_k=3,
        )

        if results:
            state["memory_recall"] = [r.model_dump() for r in results]
            logger.info(
                f"Memory recall found {len(results)} similar past insights for {ticker}"
            )
        else:
            state["memory_recall"] = []

    except Exception as e:
        logger.warning(f"memory_recall_node failed (non-fatal): {e}")
        state["memory_recall"] = []

    return state
