"""LLM client for generating responses."""

import logging
from typing import List, Optional

from openai import OpenAI

from ..config import OPENAI_API_KEY, OPENAI_MODEL, CHAT_TEMPERATURE, CHAT_MAX_TOKENS

logger = logging.getLogger("orchestrator.llm_client")


class LLMClient:
    """Client for interacting with OpenAI LLM."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
        if self.client:
            logger.info(f"LLM client initialized with model {self.model}")
        else:
            logger.warning("No OpenAI API key provided")
    
    def generate(
        self,
        messages: List[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (optional)
            max_tokens: Max tokens in response (optional)
        
        Returns:
            Generated text response.
        
        Raises:
            RuntimeError: If no client is available.
        """
        if not self.client:
            raise RuntimeError("No LLM client available")
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature or CHAT_TEMPERATURE,
            max_tokens=max_tokens or CHAT_MAX_TOKENS,
        )
        
        return response.choices[0].message.content or ""


# Global instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create the global LLM client."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


def generate_response(
    system_prompt: str,
    user_message: str,
    history: Optional[List[dict]] = None,
) -> str:
    """
    Generate a chat response with optional history.
    
    Args:
        system_prompt: System prompt with context
        user_message: User's message
        history: Optional list of previous messages
    
    Returns:
        Generated response text.
    """
    client = get_llm_client()
    
    messages = [{"role": "system", "content": system_prompt}]
    
    if history:
        messages.extend(history)
    
    messages.append({"role": "user", "content": user_message})
    
    response = client.generate(messages)
    logger.info(f"LLM response generated (temp={CHAT_TEMPERATURE}, max_tokens={CHAT_MAX_TOKENS})")
    
    return response
