"""
agent/state.py — LangGraph agent state definition.

Phase 0: Minimal TypedDict skeleton.
Phase 3+: Fields will be populated for Quick/Deep analysis workflows.

The AgentState is the shared data structure passed between every
node in the LangGraph StateGraph. All nodes read from and write to it.
"""

from __future__ import annotations

from typing import Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """
    Shared state object for the Financial Research Agent graph.

    Phase 0: Defined but unpopulated — establishes the contract
             for all future graph nodes.

    Fields (to be populated in Phase 3):
        ticker:          Stock/crypto symbol being analysed (e.g. "AAPL")
        mode:            Analysis depth — "quick" | "deep"
        user_id:         Authenticated user ID (from JWT)
        market_data:     Raw market data dict from yfinance
        analysis:        LLM-generated financial analysis text
        risk_assessment: Dict of scenario risk scores
        forecast:        Moving-average / volatility forecast data
        final_report:    Structured final output returned to the user
        messages:        LangChain message history for the LLM
        error:           Error string if any node failed
        metadata:        Arbitrary extra data (latency, tokens_used, etc.)
    """

    # ── Core inputs ──────────────────────────────────────────────────────────
    ticker: str
    mode: str                       # "quick" | "deep"
    user_id: Optional[int]

    # ── Node outputs (populated incrementally as graph runs) ─────────────────
    market_data: Optional[dict[str, Any]]
    analysis: Optional[str]
    risk_assessment: Optional[dict[str, Any]]
    forecast: Optional[dict[str, Any]]
    final_report: Optional[dict[str, Any]]

    # ── LLM conversation history ─────────────────────────────────────────────
    messages: list[Any]

    # ── Error propagation ────────────────────────────────────────────────────
    error: Optional[str]

    # ── Observability ────────────────────────────────────────────────────────
    metadata: dict[str, Any]
