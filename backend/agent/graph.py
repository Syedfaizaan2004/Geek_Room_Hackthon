"""
agent/graph.py — LangGraph StateGraph skeleton.

Phase 0: Defines the graph builder and build_graph() function.
         The graph has NO nodes or edges yet (Phase 3 will add them).

Phase 3 will wire the full pipeline:
    START → fetch_data → analyze → risk → forecast → synthesize → store_memory → END
    with a conditional edge for quick vs deep mode.
"""

import logging
from langgraph.graph import StateGraph, START, END  # type: ignore

from agent.state import AgentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """
    Assemble and compile the LangGraph StateGraph.

    Phase 0: Returns a minimal graph skeleton (no nodes).
             The graph compiles successfully so imports/startup won't fail.

    Phase 3 additions (do NOT add yet):
        builder.add_node("fetch_data",    fetch_data_node)
        builder.add_node("analyze",       analyze_node)
        builder.add_node("risk",          risk_node)
        builder.add_node("forecast",      forecast_node)
        builder.add_node("synthesize",    synthesize_node)
        builder.add_node("store_memory",  store_memory_node)

        builder.add_edge(START, "fetch_data")
        builder.add_edge("fetch_data", "analyze")
        builder.add_conditional_edges(
            "analyze",
            route_by_mode,          # quick → forecast, deep → risk → forecast
            {"quick": "forecast", "deep": "risk"},
        )
        ...
        builder.add_edge("store_memory", END)

    Returns:
        Compiled StateGraph ready for invocation.
    """
    logger.info("Building LangGraph StateGraph (Phase 0 skeleton)")

    builder: StateGraph = StateGraph(AgentState)

    # ── Phase 0: No nodes added yet ──────────────────────────────────────────
    # Nodes and edges will be registered in Phase 3.
    # The graph is intentionally left empty for now.

    # NOTE: langgraph requires at least one node to compile successfully.
    # We add a no-op passthrough node as a placeholder.
    async def _noop(state: AgentState) -> AgentState:
        """Temporary no-op node — removed in Phase 3 when real nodes are added."""
        logger.debug("Passthrough node reached (Phase 0 placeholder)")
        return state

    builder.add_node("passthrough", _noop)
    builder.add_edge(START, "passthrough")
    builder.add_edge("passthrough", END)

    graph = builder.compile()
    logger.info("LangGraph StateGraph compiled successfully")
    return graph


# ---------------------------------------------------------------------------
# Module-level singleton graph instance
# Initialised at startup in main.py lifespan
# ---------------------------------------------------------------------------
financial_graph: StateGraph = build_graph()
