"""
schemas/llm.py — Pydantic models for Phase 13 LLM Integration Layer.
"""

from typing import Literal
from pydantic import BaseModel, Field


class LLMResponse(BaseModel):
    """
    Standardised response wrapper for LLM enhancements.
    Tracks whether LLM was successful, which provider was used, and costs.
    """
    enhanced_text: str = Field(..., description="The generated narrative text.")
    llm_used: bool = Field(..., description="True if LLM succeeded, False if fallback was used.")
    provider: str = Field(..., description="e.g. 'groq', 'gemini', or 'fallback'")
    tokens_used: int = Field(default=0, description="Estimated or actual tokens consumed.")
    estimated_cost: float = Field(default=0.0, description="Estimated cost in USD.")


class ChatRequest(BaseModel):
    """Request schema for POST /api/v1/chat"""
    query: str = Field(..., min_length=2, max_length=2000)
    ticker: str | None = Field(default=None, description="Optional context ticker")
    provider: Literal["groq", "gemini"] | None = Field(
        default=None,
        description="Optional LLM provider override for this chat request."
    )
    mode: str | None = Field(default="chat", description="Context mode")
