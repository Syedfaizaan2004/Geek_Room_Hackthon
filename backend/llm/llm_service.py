"""
llm/llm_service.py — Orchestrates LLM providers and handles fallbacks (Phase 13).

Provides high-level functions for the agent and API routes to use:
  - enhance_narrative()
  - answer_chat()

Gracefully handles API keys missing or connectivity errors by falling 
back to deterministic data.
"""

import logging
from typing import Dict, Any

from app.config import get_settings
from llm.provider import LLMProvider
from llm.cost_tracker import calculate_cost
from schemas.llm import LLMResponse

logger = logging.getLogger(__name__)
settings = get_settings()

_PROVIDER_INSTANCES: dict[str, LLMProvider | None] = {}
_INIT_ATTEMPTED: set[str] = set()


def _get_provider(provider_override: str | None = None) -> LLMProvider | None:
    """Lazy initialization of the configured LLM provider, optionally overridden per request."""
    provider_name = (provider_override or settings.LLM_PROVIDER).lower()

    if provider_name in _INIT_ATTEMPTED:
        return _PROVIDER_INSTANCES.get(provider_name)

    _INIT_ATTEMPTED.add(provider_name)

    if provider_name == "disabled":
        logger.info("LLM Enhancement is disabled in config.")
        return None

    try:
        if provider_name == "groq":
            from llm.groq_client import GroqProvider
            _PROVIDER_INSTANCES[provider_name] = GroqProvider()
            logger.info("Groq Provider initialized ✓")
        elif provider_name == "gemini":
            from llm.gemini_client import GeminiProvider
            _PROVIDER_INSTANCES[provider_name] = GeminiProvider()
            logger.info("Gemini Provider initialized ✓")
        else:
            logger.warning(f"Unknown LLM_PROVIDER '{provider_name}'. Disabling LLM.")
    except ValueError as e:
        logger.warning(f"LLM Provider initialization skipped: {e}")
    except Exception as e:
        logger.error(f"Failed to initialize LLM Provider: {e}")

    return _PROVIDER_INSTANCES.get(provider_name)


async def enhance_narrative(
    insight_json: Dict[str, Any],
    ticker: str,
    mode: str,
    confidence_data: Dict[str, Any]
) -> LLMResponse:
    """
    Takes the deterministic JSON insight memo and rewrites it into a 
    fluent, professional narrative.

    If LLM is disabled or fails, returns the deterministic plain_language_summary
    as a safe fallback.
    """
    provider = _get_provider()
    
    # Fallback to deterministic
    fallback_text = insight_json.get("plain_language_summary", "No summary generated.")
    fallback_response = LLMResponse(
        enhanced_text=fallback_text,
        llm_used=False,
        provider="fallback"
    )

    if not provider:
        return fallback_response

    try:
        from llm.prompt_templates import MEMO_ENHANCEMENT_SYSTEM, MEMO_ENHANCEMENT_USER

        user_prompt = MEMO_ENHANCEMENT_USER.format(
            ticker=ticker,
            mode=mode,
            executive_summary=insight_json.get("executive_summary", ""),
            strengths="\n".join(insight_json.get("strengths", [])),
            risks="\n".join(insight_json.get("risks", [])),
            bull_thesis="\n".join(insight_json.get("bull_thesis", [])),
            bear_thesis="\n".join(insight_json.get("bear_thesis", [])),
            confidence=str(confidence_data),
            plain_language_summary=fallback_text
        )

        response_text, in_tokens, out_tokens = await provider.generate_response(
            system_prompt=MEMO_ENHANCEMENT_SYSTEM,
            user_prompt=user_prompt,
            temperature=0.2
        )

        provider_name = settings.LLM_PROVIDER.lower()
        cost = calculate_cost(
            provider_model=settings.GROQ_MODEL if provider_name == "groq" else settings.GEMINI_MODEL,
            input_tokens=in_tokens,
            output_tokens=out_tokens
        )
        from utils.performance_logger import perf_logger
        perf_logger.record_llm(tokens_used=in_tokens + out_tokens, cost_usd=cost)

        return LLMResponse(
            enhanced_text=response_text,
            llm_used=True,
            provider=provider_name,
            tokens_used=in_tokens + out_tokens,
            estimated_cost=cost
        )

    except Exception as e:
        logger.error(f"enhance_narrative failed: {e}. Falling back to deterministic.")
        return fallback_response


async def answer_chat(
    query: str,
    session_context: str,
    memory_context: str,
    preferred_provider: str | None = None
) -> LLMResponse:
    """
    Provide conversational answers using current session data and past Qdrant memory.
    """
    provider_name = (preferred_provider or settings.LLM_PROVIDER).lower()
    provider = _get_provider(provider_name)
    
    fallback_response = LLMResponse(
        enhanced_text="I'm sorry, my conversational AI brain is currently offline. I can only provide structured quantitative reports at the moment.",
        llm_used=False,
        provider="fallback"
    )

    if not provider:
        return fallback_response

    try:
        from llm.prompt_templates import CHAT_SYSTEM_PROMPT, CHAT_USER_PROMPT

        user_prompt = CHAT_USER_PROMPT.format(
            session_context=session_context,
            memory_context=memory_context,
            query=query
        )

        response_text, in_tokens, out_tokens = await provider.generate_response(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.3  # Slightly more creative for chat
        )

        cost = calculate_cost(
            provider_model=settings.GROQ_MODEL if provider_name == "groq" else settings.GEMINI_MODEL,
            input_tokens=in_tokens,
            output_tokens=out_tokens
        )
        from utils.performance_logger import perf_logger
        perf_logger.record_llm(tokens_used=in_tokens + out_tokens, cost_usd=cost)

        return LLMResponse(
            enhanced_text=response_text,
            llm_used=True,
            provider=provider_name,
            tokens_used=in_tokens + out_tokens,
            estimated_cost=cost
        )

    except Exception as e:
        logger.error(f"answer_chat failed: {e}")
        return fallback_response
