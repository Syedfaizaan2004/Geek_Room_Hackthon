"""
agents/workflows.py — LangGraph Topology Definitions (Phase 9 / Phase 15).

Defines the isolated edge graphs for Quick, Deep, Compare, Hidden Risk, and Next Analysis modes.
"""

from langgraph.graph import StateGraph, END
from agents.state import AgentState
from agents.nodes import (
    load_preferences_node,
    market_node,
    forecast_node,
    fundamentals_node,
    risk_node,
    scenario_node,
    comparison_node,
    aggregate_node
)

def build_quick_workflow() -> StateGraph:
    from agents.personalization_nodes import personalization_node

    workflow = StateGraph(AgentState)

    workflow.add_node("load_prefs", load_preferences_node)
    workflow.add_node("market", market_node)
    workflow.add_node("forecast", forecast_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("aggregate", aggregate_node)
    workflow.add_node("personalize", personalization_node)  # Phase 15

    workflow.set_entry_point("load_prefs")
    workflow.add_edge("load_prefs", "market")
    workflow.add_edge("market", "forecast")
    workflow.add_edge("forecast", "risk")
    workflow.add_edge("risk", "aggregate")
    workflow.add_edge("aggregate", "personalize")  # Phase 15
    workflow.add_edge("personalize", END)

    return workflow.compile()


def build_deep_workflow() -> StateGraph:
    from agents.memory_nodes import memory_store_node, memory_recall_node
    from agents.llm_nodes import llm_reasoning_node
    from agents.personalization_nodes import personalization_node

    workflow = StateGraph(AgentState)

    workflow.add_node("load_prefs", load_preferences_node)
    workflow.add_node("memory_recall", memory_recall_node)  # Phase 12
    workflow.add_node("market", market_node)
    workflow.add_node("fundamentals", fundamentals_node)
    workflow.add_node("forecast", forecast_node)
    workflow.add_node("risk", risk_node)
    workflow.add_node("scenario", scenario_node)
    workflow.add_node("compare", comparison_node)
    workflow.add_node("aggregate", aggregate_node)
    workflow.add_node("llm_reasoning", llm_reasoning_node)     # Phase 13
    workflow.add_node("personalize", personalization_node)     # Phase 15
    workflow.add_node("memory_store", memory_store_node)       # Phase 12

    workflow.set_entry_point("load_prefs")

    workflow.add_edge("load_prefs", "memory_recall")
    workflow.add_edge("memory_recall", "market")
    workflow.add_edge("market", "fundamentals")
    workflow.add_edge("fundamentals", "forecast")
    workflow.add_edge("forecast", "risk")
    workflow.add_edge("risk", "scenario")
    workflow.add_edge("scenario", "compare")
    workflow.add_edge("compare", "aggregate")
    workflow.add_edge("aggregate", "llm_reasoning")     # Phase 13: LLM narrative
    workflow.add_edge("llm_reasoning", "personalize")  # Phase 15: recommendations
    workflow.add_edge("personalize", "memory_store")   # Phase 12: store after all enrichment
    workflow.add_edge("memory_store", END)

    return workflow.compile()


def build_compare_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    workflow.add_node("load_prefs", load_preferences_node)
    workflow.add_node("compare", comparison_node)
    workflow.add_node("aggregate", aggregate_node)
    
    workflow.set_entry_point("load_prefs")
    workflow.add_edge("load_prefs", "compare")
    workflow.add_edge("compare", "aggregate")
    workflow.add_edge("aggregate", END)
    
    return workflow.compile()


async def hidden_risk_extraction_node(state: AgentState) -> AgentState:
    """Special isolated node for hidden risk workflow"""
    try:
        from risk.risk_engine import generate_risk_profile
        rp = generate_risk_profile(state["ticker"])
        # We only want to surface the hidden risks
        state["risk"] = {"hidden_risks": [h.model_dump() for h in rp.hidden_risks]}
    except Exception as e:
        state["errors"].append(f"Hidden risk node failed: {e}")
    return state


def build_hidden_risk_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    workflow.add_node("load_prefs", load_preferences_node)
    workflow.add_node("hidden_risk", hidden_risk_extraction_node)
    workflow.add_node("aggregate", aggregate_node)
    
    workflow.set_entry_point("load_prefs")
    workflow.add_edge("load_prefs", "hidden_risk")
    workflow.add_edge("hidden_risk", "aggregate")
    workflow.add_edge("aggregate", END)
    
    return workflow.compile()


async def next_analysis_logic_node(state: AgentState) -> AgentState:
    """
    Deterministic inference of the next logical step strictly based on stats.
    """
    try:
        from analytics.fundamentals_engine import get_fundamental_snapshot
        f = get_fundamental_snapshot(state["ticker"])
        
        from risk.risk_engine import generate_risk_profile
        r = generate_risk_profile(state["ticker"])
        
        # Simple logical tree
        if r.hidden_risks:
            rec = "investigate_hidden_risks"
        elif r.leverage_risk.level == "high":
            rec = "run_rate_hike_stress_test"
        elif f.classification == "strong":
            rec = "run_peer_compare"
        else:
            rec = "run_deep_analysis"
            
        state["next_analysis"] = rec
    except Exception as e:
        state["errors"].append(f"Next analysis logic failed: {e}")
        state["next_analysis"] = "run_deep_analysis"
        
    return state


def build_next_analysis_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    workflow.add_node("logic", next_analysis_logic_node)
    workflow.add_node("aggregate", aggregate_node)
    
    workflow.set_entry_point("logic")
    workflow.add_edge("logic", "aggregate")
    workflow.add_edge("aggregate", END)
    
    return workflow.compile()
