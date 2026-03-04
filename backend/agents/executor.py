"""
agents/executor.py — LangGraph Execution Runner (Phase 9 / Phase 16).

Handles instantiating the state, invoking the graph, measuring execution time,
and mapping the output back to the Pydantic AgentResponse schema.
Phase 16: adds result-level caching and demo mode short-circuit.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from agents.state import AgentState
from agents.router import route_request
from schemas.agent import AgentResponse, AgentResponseData
from app.config import settings

logger = logging.getLogger(__name__)


async def execute_agent_workflow(ticker: str, mode: str, user_id: str) -> AgentResponse:
    """
    1. Route to the correct workflow graph
    2. Initialize empty state
    3. Invoke graph
    4. Time and structure the response
    """
    ticker = ticker.upper().strip()
    start_time = time.time()
    from utils.performance_logger import perf_logger

    # Phase 16a: Demo Mode short-circuit (no API calls needed)
    if settings.DEMO_MODE and mode in ("quick", "deep"):
        from demo.fixtures import get_demo_data
        demo = get_demo_data(ticker)
        data_payload = AgentResponseData(**{k: demo.get(k) for k in AgentResponseData.model_fields})
        duration_ms = int((time.time() - start_time) * 1000)
        perf_logger.record_workflow(mode=mode, duration_ms=duration_ms, cache_hit=False)

        # Keep semantic memory usable in demo mode by storing deep insights when possible.
        if mode == "deep" and demo.get("insights"):
            try:
                from vector_store.qdrant_client import qdrant_wrapper
                if qdrant_wrapper.is_healthy and qdrant_wrapper.client:
                    from vector_store.memory_service import store_insight_embedding
                    await store_insight_embedding(
                        client=qdrant_wrapper.client,
                        user_id=str(user_id),
                        ticker=ticker,
                        insight_data=demo.get("insights") or {},
                        metadata={
                            "risk_score": (demo.get("risk") or {}).get("composite_risk_score", 0.0),
                            "financial_health_score": (demo.get("fundamentals") or {}).get("financial_health_score", 0.0),
                            "sector": (demo.get("market") or {}).get("sector", "unknown"),
                            "insight_type": "deep",
                        },
                    )
            except Exception as exc:
                logger.debug("Demo mode memory store skipped: %s", exc)

        logger.info(f"DEMO MODE: returning fixture data for {ticker} in {duration_ms}ms")
        return AgentResponse(
            ticker=ticker, mode=mode,
            summary_type=f"{mode}_demo_report",
            data=data_payload,
            execution_time_ms=duration_ms,
            generated_at=datetime.now(timezone.utc),
        )

    # Phase 16b: Result cache lookup
    from utils.performance import get_cached_result, cache_result
    cached = get_cached_result(ticker, mode, user_id)
    if cached is not None:
        duration_ms = int((time.time() - start_time) * 1000)
        perf_logger.record_workflow(mode=mode, duration_ms=duration_ms, cache_hit=True)
        logger.info(f"Cache HIT for {ticker}:{mode}:{user_id} — skipping graph execution")
        return cached

    # 1. Get compiled graph
    try:
        workflow_app = route_request(mode)
    except Exception as e:
        logger.error(f"Routing failed: {e}")
        raise
        
    # 2. Initialize State
    initial_state = AgentState(
        ticker=ticker,
        mode=mode,
        user_id=user_id,
        preferences=None,
        market_snapshot=None,
        forecast=None,
        fundamentals=None,
        risk=None,
        comparison=None,
        scenario=None,
        next_analysis=None,
        memory_recall=None,   # Phase 12
        recommendations=None, # Phase 15
        errors=[],
        result=None
    )
    
    # 3. Execute Graph
    logger.info(f"Invoking {mode} mode LangGraph for {ticker}")
    final_state = await workflow_app.ainvoke(initial_state)
    logger.info(f"Graph execution complete for {ticker} [Errors: {len(final_state['errors'])}]")
    
    if final_state["errors"]:
        logger.warning(f"Workflow non-fatal errors: {final_state['errors']}")
        # We allow partial failure. The schema makes fields Optional.
        # If the root fetch failed, result dict will just be empty.
        
    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)
    perf_logger.record_workflow(mode=mode, duration_ms=duration_ms, cache_hit=False)
    
    # 4. Map to Schema
    res_dict = final_state.get("result", {})
    if res_dict is None:
        res_dict = {}
        
    data_payload = AgentResponseData(**res_dict)
    
    # Define summary type conceptually
    stype = f"{mode}_research_report"

    response = AgentResponse(
        ticker=ticker,
        mode=mode,
        summary_type=stype,
        data=data_payload,
        execution_time_ms=duration_ms,
        generated_at=datetime.now(timezone.utc)
    )

    # Phase 16: Store in result cache (skip cache if there were errors)
    if not final_state.get("errors"):
        cache_result(ticker, mode, user_id, response)

    return response
