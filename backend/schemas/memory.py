"""
schemas/memory.py — Pydantic models for Phase 12 Qdrant Semantic Memory.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MemorySimilarResult(BaseModel):
    """A single result returned from a semantic similarity search."""
    ticker: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    summary_excerpt: str
    risk_score: float
    financial_health_score: float
    insight_type: str          # "deep" | "quick"
    stored_at: Optional[datetime] = None


class MemoryRecentResult(BaseModel):
    """A recent stored insight without semantic similarity metadata."""
    ticker: str
    summary_excerpt: str
    risk_score: float
    financial_health_score: float
    insight_type: str
    stored_at: Optional[datetime] = None


class MemorySearchRequest(BaseModel):
    """Request body for POST /memory/search"""
    query: str = Field(..., min_length=3, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class MemorySearchResponse(BaseModel):
    """Response for semantic insight search."""
    query: str
    similar_results: List[MemorySimilarResult]
    total_found: int

    model_config = ConfigDict(from_attributes=True)


class MemoryStoreRequest(BaseModel):
    """Internal schema for upsert operations (not exposed via API)."""
    user_id: str
    ticker: str
    insight_text: str
    risk_score: float = 0.0
    financial_health_score: float = 0.0
    sector: str = "unknown"
    insight_type: str = "deep"


class RiskPatternResult(BaseModel):
    """A ticker returned from risk pattern search."""
    ticker: str
    risk_score: float
    insight_type: str
    stored_at: Optional[datetime] = None
