"""GRC Platform - LLM Model Router.

Selects the appropriate LLM model based on the GRC_ENV environment variable.
In development, uses OpenRouter (meta-llama/llama-3-8b-instruct).
In production, uses Ollama (gemma2:12b).
"""

from typing import Union

from agno.models.openai import OpenAIChat, OpenAILike
from agno.models.openrouter import OpenRouter

from config import get_config

config = get_config()


def get_llm_model() -> Union[OpenRouter, OpenAILike]:
    """Get the appropriate LLM model based on the current environment.

    In development mode, returns an OpenRouter model configured with
    meta-llama/llama-3-8b-instruct. In production mode, returns an
    Ollama-compatible model configured with gemma2:12b via OpenAILike.

    Returns:
        Union[OpenRouter, OpenAILike]: The configured LLM model instance.
    """
    if config.is_development:
        return OpenRouter(
            id="meta-llama/llama-3-8b-instruct",
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )
    else:
        # Ollama exposes an OpenAI-compatible API
        return OpenAILike(
            id="gemma2:12b",
            api_key="ollama",  # Ollama requires a non-empty api_key for openai compat
            base_url=f"{config.llm.base_url}/v1",
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )


def get_llm_model_for_tools() -> Union[OpenRouter, OpenAILike]:
    """Get the LLM model configured specifically for tool-calling workloads.

    Uses a slightly higher max_tokens to accommodate tool responses.

    Returns:
        Union[OpenRouter, OpenAILike]: The configured LLM model instance
            with tool-friendly settings.
    """
    if config.is_development:
        return OpenRouter(
            id="meta-llama/llama-3-8b-instruct",
            api_key=config.llm.api_key,
            base_url=config.llm.base_url,
            temperature=0.5,
            max_tokens=8192,
        )
    else:
        return OpenAILike(
            id="gemma2:12b",
            api_key="ollama",
            base_url=f"{config.llm.base_url}/v1",
            temperature=0.5,
            max_tokens=8192,
        )
