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

_MODEL_FALLBACKS = ("gemini-2.0-flash", "gemini-1.5-flash")


def _model_candidates() -> list[str]:
    candidates: list[str] = []
    primary = (settings.GEMINI_MODEL or "").strip()
    if primary:
        candidates.append(primary)
    for model in _MODEL_FALLBACKS:
        if model not in candidates:
            candidates.append(model)
    return candidates


class GeminiProvider(LLMProvider):
    """
    Implementation for Google Gemini GenAI using LangChain wrapper.
    """

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set in environment.")

        self._api_key = settings.GEMINI_API_KEY
        self._models = _model_candidates()
        self._active_model = self._models[0]
        self.client = self._build_client(self._active_model)

    def _build_client(self, model_name: str) -> ChatGoogleGenerativeAI:
        return ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self._api_key,
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
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        last_error: Exception | None = None

        for model_name in self._models:
            try:
                if model_name != self._active_model:
                    self.client = self._build_client(model_name)
                    self._active_model = model_name
                    logger.warning("Switched Gemini model fallback to '%s'.", model_name)

                response = await self.client.ainvoke(
                    messages,
                    temperature=temperature
                )

                response_metadata = getattr(response, "response_metadata", {}) or {}
                usage = response_metadata.get("token_usage") or response_metadata.get("usage_metadata") or {}
                text = response.content if isinstance(response.content, str) else str(response.content)

                input_tokens = (
                    usage.get("prompt_tokens")
                    or usage.get("input_tokens")
                    or usage.get("prompt_token_count")
                    or len(system_prompt + user_prompt) // 4
                )
                output_tokens = (
                    usage.get("completion_tokens")
                    or usage.get("output_tokens")
                    or usage.get("candidates_token_count")
                    or len(text) // 4
                )

                return text, int(input_tokens), int(output_tokens)

            except Exception as e:
                last_error = e
                logger.error("Gemini API call failed for model '%s': %s", model_name, e)
                continue

        raise last_error if last_error else RuntimeError("Gemini API call failed.")
