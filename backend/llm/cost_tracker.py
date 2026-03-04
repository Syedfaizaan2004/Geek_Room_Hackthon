"""
llm/cost_tracker.py — Token estimation and cost tracking for Phase 13.

Provides rough estimates for token usage and cost calculation
when the provider's API doesn't return exact token counts, or
to unify cost tracking across different providers.
"""

import logging

logger = logging.getLogger(__name__)

# Very rough approximation: 1 token ≈ 4 characters
CHARS_PER_TOKEN = 4.0

# Arbitrary fallback pricing (can be configured or fetched live in production)
# Prices per 1M tokens (Input / Output)
PRICING = {
    "groq_llama3_70b": {"input": 0.59, "output": 0.79}, # Llama 3 70b on Groq
    "gemini_flash": {"input": 0.075, "output": 0.30},   # Gemini 1.5 Flash
    "fallback": {"input": 0.0, "output": 0.0},
}


def estimate_tokens(text: str) -> int:
    """Rough heuristic for token count based on string length."""
    if not text:
        return 0
    return int(len(text) / CHARS_PER_TOKEN)


def calculate_cost(provider_model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate estimated cost in USD based on provider and token usage.
    """
    rates = PRICING.get(provider_model)
    
    # Map raw provider names to defaults if specific model string not matching exactly
    if not rates:
        if "groq" in provider_model.lower():
            rates = PRICING["groq_llama3_70b"]
        elif "llama" in provider_model.lower():
            # Groq model IDs are often plain model names (without "groq" prefix).
            rates = PRICING["groq_llama3_70b"]
        elif "gemini" in provider_model.lower():
            rates = PRICING["gemini_flash"]
        else:
            rates = PRICING["fallback"]

    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]

    total = input_cost + output_cost
    # Return rounded to 6 decimals to avoid floating point dust
    return round(total, 6)
