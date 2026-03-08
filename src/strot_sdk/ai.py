"""
STROT SDK — AI Module

Provides LLM access via the STROT API proxy.
All LLM calls go through your STROT instance (no direct API keys needed).
"""
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Available model aliases
MODELS = {
    "default": "mistral/mistral-large-latest",
    "fast": "mistral/mistral-small-latest",
    "code": "mistral/codestral-latest",
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "claude-3-sonnet": "anthropic/claude-3-sonnet-20240229",
    "claude-3-opus": "anthropic/claude-3-opus-20240229",
}


class LLM:
    """
    LLM client for STROT SDK.

    All calls go through the STROT API proxy — no direct LLM API keys needed.

    Usage:
        from strot_sdk import llm

        result = llm.complete("Summarize this text: " + text)
        result = llm("What is 2+2?")  # shorthand
        result = llm.classify("Great product!", ["positive", "negative", "neutral"])
    """

    def __init__(self, model: str = "default", temperature: float = 0.1):
        self.model = MODELS.get(model, model)
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        """Lazy-load the StrotClient."""
        if self._client is None:
            from .client import StrotClient
            self._client = StrotClient()
        return self._client

    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """
        Generate a completion from the LLM.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate

        Returns:
            The generated text
        """
        model = MODELS.get(kwargs.pop('model', None), None) or self.model
        temperature = kwargs.pop('temperature', self.temperature)
        client = self._get_client()
        return client.llm_complete(
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    # Aliases — AI code generators often use these names
    generate = complete
    translate = complete
    summarize = complete
    ask = complete

    def __call__(self, prompt: str, **kwargs) -> str:
        """Allow llm('prompt') syntax."""
        return self.complete(prompt, **kwargs)

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """
        Send a chat conversation to the LLM.

        Args:
            messages: List of messages [{"role": "user", "content": "..."}]
            max_tokens: Maximum tokens to generate

        Returns:
            The assistant's response
        """
        model = MODELS.get(kwargs.pop('model', None), None) or self.model
        temperature = kwargs.pop('temperature', self.temperature)
        client = self._get_client()
        return client.llm_chat(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def transform(
        self,
        data: Any,
        instruction: str,
        output_format: str = "json",
        **kwargs
    ) -> Any:
        """
        Transform data using LLM.

        Args:
            data: Input data (will be JSON serialized)
            instruction: What transformation to apply
            output_format: Expected output format ('json', 'text', 'list')

        Returns:
            Transformed data
        """
        client = self._get_client()
        return client.llm_transform(
            data_input=data,
            instruction=instruction,
            output_format=output_format,
        )

    def classify(self, text: str, categories: List[str], **kwargs) -> str:
        """
        Classify text into one of the given categories.

        Args:
            text: Text to classify
            categories: List of possible categories

        Returns:
            The selected category
        """
        client = self._get_client()
        return client.llm_classify(text=text, categories=categories)

    def extract(self, text: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Extract structured data from text according to a schema.

        Args:
            text: Text to extract from
            schema: JSON schema describing expected output

        Returns:
            Extracted data as dictionary
        """
        client = self._get_client()
        return client.llm_extract(text=text, schema=schema)


# Default LLM instance
llm = LLM()
