import logging
from typing import Any, Dict, List
from fastapi import APIRouter, Body
from pydantic import BaseModel

from llm.investment_insights import generate_ai_insights

logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Insights"])

class AIInsightItem(BaseModel):
    question: str
    answer: str

class AIInsightsResponse(BaseModel):
    insights: List[AIInsightItem]
    llm_used: bool
    provider: str

@router.post("/ai-insights", response_model=AIInsightsResponse)
async def api_generate_ai_insights(
    ticker: str = Body(..., embed=True),
    analysis: dict = Body(..., embed=True)
):
    """
    Post analysis data to Gemini and receive structured Q&A insights.
    Falls back to deterministic answers if no LLM is configured.
    """
    result = await generate_ai_insights(ticker, analysis)
    return AIInsightsResponse(**result)
