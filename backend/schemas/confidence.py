"""
schemas/confidence.py — Pydantic models for Phase 11 Confidence & Transparency Engine.

All fields are deterministic — no LLM, no hallucination.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ContradictionItem(BaseModel):
    """A detected logical inconsistency between two engine outputs."""
    type: str = Field(..., description="Short label e.g. 'growth_margin_conflict'")
    explanation: str = Field(..., description="Plain-language description of the contradiction")


class UncertaintyDetail(BaseModel):
    """Uncertainty classification with driving factors."""
    level: str = Field(..., description="low | moderate | high")
    drivers: List[str] = Field(default_factory=list, description="Root causes of uncertainty")


class ConfidenceResponse(BaseModel):
    """
    Full transparency layer attached to every agent research output.

    - confidence_score: 0–100 composite trust metric
    - confidence_level: low / moderate / high
    - completeness_score: % of expected data that was available
    - contradictions: list of detected logical conflicts
    - uncertainty: uncertainty classification + drivers
    - assumptions: list of modelling assumptions used
    - generated_at: UTC timestamp
    """
    ticker: str

    confidence_score: float = Field(..., ge=0, le=100)
    confidence_level: str  # "low" | "moderate" | "high"

    completeness_score: float = Field(..., ge=0, le=100)

    contradictions: List[ContradictionItem] = Field(default_factory=list)
    uncertainty: UncertaintyDetail

    assumptions: List[str] = Field(default_factory=list)

    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)
