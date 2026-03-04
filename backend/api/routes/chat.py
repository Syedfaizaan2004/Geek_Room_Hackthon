"""
api/routes/chat.py — Conversational Q&A endpoint (Phase 13).

Allows users to ask follow-up questions on their stored research.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Body

from api.routes.auth import get_current_user
from memory.models import User
from schemas.llm import ChatRequest, LLMResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=LLMResponse)
async def chat_with_agent(
    request: ChatRequest = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Ask follow-up questions on a specific ticker or general portfolio context.
    The response strictly adheres to the available deterministic data in Qdrant memory.
    """
    logger.info(
        "Chat request by user=%s | provider=%s | Query: %s...",
        current_user.unique_user_id,
        request.provider or "default",
        request.query[:30],
    )

    # 1. Fetch relevant memory context to ensure deterministic grounding
    memory_context = ""
    session_context = f"Active focus: {request.ticker}" if request.ticker else "No active ticker focus."

    try:
        from vector_store.qdrant_client import qdrant_wrapper
        if qdrant_wrapper.is_healthy and qdrant_wrapper.client:
            from vector_store.memory_service import retrieve_similar_insights
            
            # Use ticker + query for semantic search
            search_str = f"{request.ticker} {request.query}" if request.ticker else request.query
            results = []
            for key in (str(current_user.id), current_user.unique_user_id):
                results = await retrieve_similar_insights(
                    client=qdrant_wrapper.client,
                    query_text=search_str,
                    user_id=key,
                    top_k=3
                )
                if results:
                    break
            
            if results:
                # Compile summaries into context string
                memory_blocks = []
                for idx, res in enumerate(results):
                    memory_blocks.append(f"[{idx+1}] {res.ticker} (Risk={res.risk_score}): {res.summary_excerpt}")
                memory_context = "\n\n".join(memory_blocks)
            else:
                memory_context = "No previous research found."
        else:
            memory_context = "Qdrant memory unavailable. Cannot retrieve past research."
            
    except Exception as e:
        logger.warning(f"Chat memory retrieval failed (non-fatal): {e}")
        memory_context = "Memory lookup error occurred."

    # 2. Invoke LLM Service
    try:
        from llm.llm_service import answer_chat
        llm_response = await answer_chat(
            query=request.query,
            session_context=session_context,
            memory_context=memory_context,
            preferred_provider=request.provider,
        )
        return llm_response
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process chat request.")
