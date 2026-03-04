"""
llm/provider.py — Abstract Base Class for LLM Providers (Phase 13).
"""

from abc import ABC, abstractmethod
from typing import Tuple

class LLMProvider(ABC):
    """
    Abstract interface for LLM integrations (Groq, Gemini).
    Ensures all providers expose a consistent asynchronous generate method.
    """

    @abstractmethod
    async def generate_response(
        self, 
        system_prompt: str, 
        user_prompt: str, 
        temperature: float = 0.2
    ) -> Tuple[str, int, int]:
        """
        Generate a text response from the LLM.

        Args:
            system_prompt: Role and instructions.
            user_prompt: Data and user query.
            temperature: Creativity control (defaults to 0.2 for analytical stability).

        Returns:
            Tuple of:
            - Generated text content (str)
            - Input tokens used (int)
            - Output tokens used (int)
            
        Raises:
            Exception: If API call fails.
        """
        pass
