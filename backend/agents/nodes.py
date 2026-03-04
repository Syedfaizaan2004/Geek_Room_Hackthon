"""
agents/nodes.py — Modular graph nodes wrapping the Phase 3-8 service engines.

Each node receives the current AgentState, calls the relevant deterministic engine,
and updates the dict with the result before passing it down the graph.
"""

import logging
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

# Import service layers
from memory import crud
from analytics.service import get_market_snapshot
from analytics.forecast_engine import generate_forecast
from analytics.fundamentals_engine import get_fundamental_snapshot
from risk.risk_engine import generate_risk_profile
from risk.scenario_engine import run_sync_scenario_analysis
from comparison.comparison_engine import run_peer_comparison
from agents.state import AgentState

# Note: We need a synchronous or handled-async way to fetch preferences if we are in an async node.
# Langgraph nodes can be async.

logger = logging.getLogger(__name__)


async def load_preferences_node(state: AgentState, db: AsyncSession = None) -> AgentState:
    """Loads user preferences and sets default fallbacks if missing."""
    import asyncio
    
    # In a real LangGraph setup, passing the db session into nodes can be tricky.
    # Often it's attached via a config or closure. We'll assume the db session 
    # is passed as a kwarg from the executor or we generate a new short-lived session.
    # For now, we'll create a new localized session just for this node to keep it pure.
    from db.session import get_db
    from contextlib import asynccontextmanager
    
    prefs_dict = {
        "risk_tolerance": "moderate",
        "time_horizon": "medium_term"
    }
    
    try:
        # Get a db generator
        db_gen = get_db()
        session = await anext(db_gen)
        
        prefs_model = await crud.get_preferences_by_user_id(session, state["user_id"])
        if prefs_model:
            prefs_dict = prefs_model.__dict__
            
        await session.close()
    except Exception as e:
        logger.error(f"Failed to load preferences for {state['user_id']}: {e}")
        state["errors"].append("Failed to load user preferences. Using defaults.")
        
    state["preferences"] = prefs_dict
    return state


async def market_node(state: AgentState) -> AgentState:
    try:
        snap = get_market_snapshot(state["ticker"], period="1y")
        state["market_snapshot"] = snap.model_dump()
    except Exception as e:
        state["errors"].append(f"Market node failed: {e}")
    return state


async def forecast_node(state: AgentState) -> AgentState:
    if not state.get("market_snapshot"):
        state["errors"].append("Forecast node skipped due to missing market snapshot.")
        return state
        
    try:
        ms = state["market_snapshot"]
        th = state.get("preferences", {}).get("time_horizon", "medium_term")
        
        fc = generate_forecast(
            current_price=ms["last_price"],
            volatility_percent=ms["volatility_percent"],
            trend_direction=ms["trend_direction"],
            time_horizon_pref=th
        )
        # Serialize to dict like all other nodes — keeps state consistent
        state["forecast"] = fc.model_dump() if hasattr(fc, "model_dump") else fc
    except Exception as e:
        state["errors"].append(f"Forecast node failed: {e}")
    return state


async def fundamentals_node(state: AgentState) -> AgentState:
    try:
        funds = get_fundamental_snapshot(state["ticker"])
        state["fundamentals"] = funds.model_dump()
    except Exception as e:
        state["errors"].append(f"Fundamentals node failed: {e}")
    return state


async def risk_node(state: AgentState) -> AgentState:
    try:
        rp = generate_risk_profile(state["ticker"])
        state["risk"] = rp.model_dump()
    except Exception as e:
        state["errors"].append(f"Risk node failed: {e}")
    return state


async def scenario_node(state: AgentState) -> AgentState:
    try:
        th = state.get("preferences", {}).get("time_horizon", "medium_term")
        scenario_types = ("recession", "inflation", "rate_hike", "growth_slowdown")
        scenarios = []

        for scenario_type in scenario_types:
            try:
                scen = run_sync_scenario_analysis(
                    state["ticker"],
                    th,
                    scenario_type=scenario_type
                )
                scenarios.append(scen.model_dump() if hasattr(scen, "model_dump") else scen)
            except Exception as e:
                state["errors"].append(f"Scenario '{scenario_type}' failed: {e}")

        if scenarios:
            state["scenario"] = scenarios
        else:
            state["errors"].append("Scenario node failed: no scenarios generated.")
    except Exception as e:
        state["errors"].append(f"Scenario node failed: {e}")
    return state


async def comparison_node(state: AgentState) -> AgentState:
    try:
        comp = run_peer_comparison(state["ticker"])
        state["comparison"] = comp.model_dump()
    except Exception as e:
        state["errors"].append(f"Comparison node failed: {e}")
    return state


async def aggregate_node(state: AgentState) -> AgentState:
    """
    Final node. Gathers all non-null state outputs, runs Phase 10 insight synthesis
    and Phase 11 confidence scoring, then binds everything into the 'result' dict.
    """
    res = {}
    if state.get("market_snapshot"): res["market"] = state["market_snapshot"]
    if state.get("forecast"): res["forecast"] = state["forecast"]
    if state.get("fundamentals"): res["fundamentals"] = state["fundamentals"]
    if state.get("risk"): res["risk"] = state["risk"]
    if state.get("scenario"): res["scenario"] = state["scenario"]
    if state.get("comparison"): res["comparison"] = state["comparison"]
    if state.get("memory_recall"): res["memory_recall"] = state["memory_recall"]
    if state.get("next_analysis"): res["next_step_recommendation"] = state["next_analysis"]

    # Phase 10 — Insight Synthesis
    try:
        has_data = any([
            state.get("market_snapshot"),
            state.get("forecast"),
            state.get("fundamentals"),
            state.get("risk"),
        ])
        if has_data:
            from agents.synthesizer import synthesize_insights
            insight_obj = synthesize_insights(state)
            res["insights"] = insight_obj.model_dump()
    except Exception as e:
        logger.warning(f"Insight synthesis skipped due to error: {e}")

    # Phase 11 — Confidence & Transparency Engine
    try:
        from utils.confidence_engine import generate_confidence_report
        confidence_obj = generate_confidence_report(
            ticker=state["ticker"],
            market=state.get("market_snapshot") or {},
            forecast=state.get("forecast") or {},
            fundamentals=state.get("fundamentals") or {},
            risk=state.get("risk") or {},
            scenario=state.get("scenario") or {},
            comparison=state.get("comparison") or {},
        )
        res["confidence"] = confidence_obj.model_dump()
    except Exception as e:
        logger.warning(f"Confidence engine skipped due to error: {e}")

    state["result"] = res
    return state

