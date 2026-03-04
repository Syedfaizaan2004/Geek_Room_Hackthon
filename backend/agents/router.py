"""
agents/router.py — LangGraph Orchestration Router (Phase 9).

Determines which StateGraph to construct and return based on the requested mode.
"""

from langgraph.graph import StateGraph
from agents.workflows import (
    build_quick_workflow,
    build_deep_workflow,
    build_compare_workflow,
    build_hidden_risk_workflow,
    build_next_analysis_workflow
)

def route_request(mode: str) -> StateGraph:
    """
    Return the compiled LangGraph workflow corresponding to the requested analysis mode.
    """
    mode = mode.lower().strip()
    
    if mode == "quick":
        return build_quick_workflow()
    elif mode == "deep":
        return build_deep_workflow()
    elif mode == "compare":
        return build_compare_workflow()
    elif mode == "hidden_risk":
        return build_hidden_risk_workflow()
    elif mode == "next_analysis":
        return build_next_analysis_workflow()
    else:
        raise ValueError(f"Unknown analysis mode: {mode}")
