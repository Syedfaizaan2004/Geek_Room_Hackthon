"""
api/routes/agent.py — LangGraph Controller Endpoint (Phase 9).
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.auth import get_current_user
from memory.models import User
from schemas.agent import AgentAnalyzeRequest, AgentResponse
from agents.executor import execute_agent_workflow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analyze", tags=["Agent Orchestration"])

@router.post(
    "",
    response_model=AgentResponse,
    summary="Trigger LangGraph Agent analysis workflow",
    responses={
        400: {"description": "Invalid mode requested"},
        401: {"description": "Missing or invalid token"},
        500: {"description": "Graph execution failed completely"},
    },
)
async def post_analyze(
    request: AgentAnalyzeRequest,
    current_user: Annotated[User, Depends(get_current_user)]
) -> AgentResponse:
    """
    Kicks off a deterministic LangGraph workflow against the target ticker.
    Valid modes:
    - `quick`: Fast basic snapshot + forecast.
    - `deep`: Full fundamental evaluation + risk + scenario testing + peer benchmarking.
    - `compare`: Isolated peer ranking.
    - `hidden_risk`: Focused vulnerability screen.
    - `next_analysis`: AI-guided deterministic next-step suggestion based on stats.
    
    Requires: `Authorization: Bearer <token>`
    """
    valid_modes = ["quick", "deep", "compare", "hidden_risk", "next_analysis"]
    if request.mode not in valid_modes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "Invalid analysis mode",
                "detail": f"Mode must be one of {valid_modes}"
            }
        )
        
    try:
        response = await execute_agent_workflow(
            ticker=request.ticker,
            mode=request.mode,
            user_id=current_user.id
        )
        return response
    except Exception as exc:
        logger.error(f"Agent Orchestrator failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "Agent workflow failed",
                "detail": str(exc),
            },
        ) from exc
