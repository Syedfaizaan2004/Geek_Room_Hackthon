"""
schemas/recommendations.py — Phase 15 Personalization & Smart Recommendations schemas.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class NextAction(BaseModel):
    """A suggested next research step."""
    action_type: str = Field(..., description="e.g. 'stress_test', 'deep_analysis', 'peer_compare'")
    explanation: str = Field(..., description="Human-readable reason for this suggestion")


class SimilarCompany(BaseModel):
    """A Qdrant-based similar company recommendation."""
    ticker: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    reason: str


class WatchlistRecommendation(BaseModel):
    """A recommendation to add a ticker to the watchlist."""
    ticker: str
    reason: str


class BehavioralProfile(BaseModel):
    """Summary of detected user behaviour patterns."""
    dominant_sector: Optional[str] = None
    typical_risk_profile: Optional[str] = None
    analysis_mode_preference: Optional[str] = None
    engagement_pattern: Optional[str] = None


class RecommendationResponse(BaseModel):
    """
    Full personalized recommendation payload returned by
    GET /recommendations/{ticker} and attached to deep-mode agent results.
    """
    ticker: str
    next_actions: List[NextAction] = Field(default_factory=list)
    similar_companies: List[SimilarCompany] = Field(default_factory=list)
    watchlist_recommendations: List[WatchlistRecommendation] = Field(default_factory=list)
    behavioral_profile: Optional[BehavioralProfile] = None
    memory_reminders: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
