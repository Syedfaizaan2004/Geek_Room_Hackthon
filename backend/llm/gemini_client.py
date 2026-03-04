"""
llm/gemini_client.py — Gemini LLM Provider (Phase 13).
"""

import logging
from typing import Tuple

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings
from llm.provider import LLMProvider

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiProvider(LLMProvider):
    """
    Implementation for Google Gemini GenAI using LangChain wrapper.
    """

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in environment.")
            
        self.client = ChatGoogleGenerativeAI(
            model=settings.GEMINI_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.2,
        )

    async def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        temperature: float = 0.2
    ) -> Tuple[str, int, int]:
        """
        Generate a response using Gemini via LangChain async invocation.
        """
        try:
            # We explicitly override the baseline temperature on each call.
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = await self.client.ainvoke(
                messages,
                temperature=temperature
            )
            
            # Gemini response wrapper usually contains usage_metadata
            usage = response.response_metadata.get("token_usage", {})
            
            # Pydantic generic fallback if provider specific metadata missing
            input_tokens = usage.get("prompt_tokens", len(system_prompt + user_prompt) // 4)
            output_tokens = usage.get("completion_tokens", len(response.content) // 4)

            return response.content, input_tokens, output_tokens
            
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
