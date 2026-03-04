"""
agents/state.py — LangGraph State definition (Phase 9 / Phase 12 / Phase 15).
"""

from typing import TypedDict, Optional, Dict, Any, List

class AgentState(TypedDict):
    """
    Shared mutable state across all nodes in the LangGraph orchestration.
    """
    ticker: str
    mode: str
    user_id: str
    
    # Input Data
    preferences: Optional[Dict[str, Any]]
    
    # Engine Outputs
    market_snapshot: Optional[Dict[str, Any]]
    forecast: Optional[Dict[str, Any]]
    fundamentals: Optional[Dict[str, Any]]
    risk: Optional[Dict[str, Any]]
    comparison: Optional[Dict[str, Any]]
    scenario: Optional[Dict[str, Any]]
    next_analysis: Optional[str]
    
    # Phase 12 — Memory
    memory_recall: Optional[List[Dict[str, Any]]]   # Past similar insights from Qdrant

    # Phase 15 — Personalization
    recommendations: Optional[Dict[str, Any]]       # Smart recommendation payload

    # Errors/Diagnostics
    errors: List[str]

    # Final generic payload accumulator before conversion to AgentResponseData
    result: Optional[Dict[str, Any]]
