"""
schemas/agent.py — Pydantic models for LangGraph Orchestration (Phase 9).
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class AgentAnalyzeRequest(BaseModel):
    ticker: str
    mode: str  # enum handled in route/executor: "quick", "deep", "compare", "hidden_risk", "next_analysis"


class AgentResponseData(BaseModel):
    market: Optional[Dict[str, Any]] = None
    forecast: Optional[Dict[str, Any]] = None
    fundamentals: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    comparison: Optional[Dict[str, Any]] = None
    # Live workflow returns one scenario dict; demo fixtures return a list of scenarios.
    scenario: Optional[Dict[str, Any] | list[Dict[str, Any]]] = None
    insights: Optional[Dict[str, Any]] = None
    confidence: Optional[Dict[str, Any]] = None   # Phase 11
    llm_enhanced_memo: Optional[Dict[str, Any]] = None # Phase 13
    recommendations: Optional[Dict[str, Any]] = None  # Phase 15
    memory_recall: Optional[list[Dict[str, Any]]] = None  # Phase 12
    next_step_recommendation: Optional[str] = None


class AgentResponse(BaseModel):
    """
    Structured outcome of the LangGraph state machine execution.
    """
    ticker: str
    mode: str
    summary_type: str
    
    data: AgentResponseData
    
    execution_time_ms: int
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
