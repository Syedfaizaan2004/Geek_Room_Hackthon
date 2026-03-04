"""
llm/groq_client.py — Groq LLM Provider (Phase 13).
"""

import logging
from typing import Tuple

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import get_settings
from llm.provider import LLMProvider

logger = logging.getLogger(__name__)
settings = get_settings()

DEFAULT_FALLBACK_MODEL = "llama-3.3-70b-versatile"
LEGACY_MODEL_ALIASES = {
    # Groq legacy IDs that now return `model_decommissioned`
    "llama3-70b-8192": DEFAULT_FALLBACK_MODEL,
    "llama3-8b-8192": "llama-3.1-8b-instant",
}


class GroqProvider(LLMProvider):
    """
    Implementation for Groq LLaMA models using LangChain wrapper.
    """

    def __init__(self):
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in environment.")

        configured_model = (settings.GROQ_MODEL or "").strip()
        self.model_name = LEGACY_MODEL_ALIASES.get(configured_model, configured_model or DEFAULT_FALLBACK_MODEL)

        if self.model_name != configured_model:
            logger.warning(
                "Configured GROQ_MODEL '%s' is deprecated; using '%s' instead.",
                configured_model,
                self.model_name,
            )

        self.client = self._build_client(self.model_name)

    def _build_client(self, model_name: str) -> ChatGroq:
        return ChatGroq(
            model_name=model_name,
            groq_api_key=settings.GROQ_API_KEY,
            temperature=0.2,
        )

    async def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        temperature: float = 0.2
    ) -> Tuple[str, int, int]:
        """
        Generate a response using Groq via LangChain async invocation.
        """
        try:
            # We explicitly override the baseline temperature on each call.
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            response = await self.client.ainvoke(messages, temperature=temperature)
            usage = response.response_metadata.get("token_usage", {})
            input_tokens = usage.get("prompt_tokens", len(system_prompt + user_prompt) // 4)
            output_tokens = usage.get("completion_tokens", len(response.content) // 4)
            return response.content, input_tokens, output_tokens

        except Exception as e:
            if "model_decommissioned" in str(e) and self.model_name != DEFAULT_FALLBACK_MODEL:
                logger.warning(
                    "Groq model '%s' is decommissioned; retrying once with '%s'.",
                    self.model_name,
                    DEFAULT_FALLBACK_MODEL,
                )
                self.model_name = DEFAULT_FALLBACK_MODEL
                self.client = self._build_client(self.model_name)
                response = await self.client.ainvoke(messages, temperature=temperature)
                usage = response.response_metadata.get("token_usage", {})
                input_tokens = usage.get("prompt_tokens", len(system_prompt + user_prompt) // 4)
                output_tokens = usage.get("completion_tokens", len(response.content) // 4)
                return response.content, input_tokens, output_tokens

            logger.error(f"Groq API call failed: {e}")
            raise
