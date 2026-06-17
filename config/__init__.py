"""GRC Platform - Configuration Module.

Provides environment-aware settings that switch between development
(OpenRouter) and production (Ollama) configurations.
"""

from config.settings import (
    get_config,
    DatabaseConfig,
    LLMConfig,
    EmbeddingConfig,
    StorageConfig,
    Config,
)

__all__ = [
    "get_config",
    "DatabaseConfig",
    "LLMConfig",
    "EmbeddingConfig",
    "StorageConfig",
    "Config",
]
