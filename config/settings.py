"""GRC Platform - Environment-Aware Configuration.

Switches between development (OpenRouter) and production (Ollama) settings
based on the GRC_ENV environment variable.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def _bool_env(key: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""
    val = os.getenv(key, str(default)).lower().strip()
    return val in ("true", "1", "yes", "on")


@dataclass
class DatabaseConfig:
    """PostgreSQL + pgvector database configuration."""

    url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://grc_user:grc_pass@localhost:5432/grc_dev",
        )
    )
    pool_min: int = 2
    pool_max: int = 10
    pool_timeout: int = 30


@dataclass
class LLMConfig:
    """Large Language Model configuration.

    In development, uses OpenRouter (meta-llama/llama-3-8b-instruct).
    In production, uses Ollama (gemma2:12b).
    """

    provider: str = "openrouter"  # "openrouter" or "ollama"
    model: str = "meta-llama/llama-3-8b-instruct"
    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    temperature: float = 0.7
    max_tokens: int = 4096

    @classmethod
    def for_development(cls) -> "LLMConfig":
        """Create config for development environment using OpenRouter."""
        return cls(
            provider="openrouter",
            model="meta-llama/llama-3-8b-instruct",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            temperature=0.7,
            max_tokens=4096,
        )

    @classmethod
    def for_production(cls) -> "LLMConfig":
        """Create config for production environment using Ollama."""
        return cls(
            provider="ollama",
            model="gemma2:12b",
            api_key=None,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0.7,
            max_tokens=4096,
        )


@dataclass
class EmbeddingConfig:
    """Embedding model configuration.

    In development, uses OpenRouter embeddings API.
    In production, uses NVIDIA Llama Nemotron Embed via Ollama.
    """

    provider: str = "openrouter"
    model: str = "nvidia/llama-nemotron-embed-vl-1b-v2"
    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    dimensions: int = 1024

    @classmethod
    def for_development(cls) -> "EmbeddingConfig":
        """Create config for development environment using OpenRouter.

        Uses BAAI bge-m3 which produces 1024-dimensional embeddings
        and is available on OpenRouter's free tier.
        """
        return cls(
            provider="openrouter",
            model="baai/bge-m3",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1",
            dimensions=1024,
        )

    @classmethod
    def for_production(cls) -> "EmbeddingConfig":
        """Create config for production environment using Ollama."""
        return cls(
            provider="ollama",
            model="nvidia/llama-nemotron-embed-vl-1b-v2",
            api_key=None,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            dimensions=1024,
        )


@dataclass
class StorageConfig:
    """File storage configuration for evidence artifacts."""

    upload_dir: str = field(
        default_factory=lambda: os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "uploads",
        )
    )
    max_file_size_mb: int = 50
    allowed_extensions: tuple = field(
        default_factory=lambda: (".pdf", ".png", ".jpg", ".jpeg", ".docx")
    )


@dataclass
class Config:
    """Top-level application configuration."""

    env: str = "development"
    debug: bool = True
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    enable_ai_chat: bool = True
    enable_auto_mapping: bool = True
    enable_mock_data: bool = True

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == "production"


# Singleton pattern - hold the loaded config
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the application configuration based on GRC_ENV.

    Returns a Config instance with settings appropriate for the
    current environment. Development uses OpenRouter, production uses Ollama.

    Returns:
        Config: Environment-aware configuration object.
    """
    global _config_instance

    if _config_instance is not None:
        return _config_instance

    env = os.getenv("GRC_ENV", "development").lower().strip()

    if env == "production":
        _config_instance = Config(
            env="production",
            debug=False,
            database=DatabaseConfig(
                url=os.getenv(
                    "DATABASE_URL",
                    "postgresql://grc_user:grc_pass@localhost:5432/grc_prod",
                )
            ),
            llm=LLMConfig.for_production(),
            embedding=EmbeddingConfig.for_production(),
            storage=StorageConfig(),
            enable_ai_chat=_bool_env("ENABLE_AI_CHAT", True),
            enable_auto_mapping=_bool_env("ENABLE_AUTO_MAPPING", True),
            enable_mock_data=_bool_env("ENABLE_MOCK_DATA", False),
        )
    else:
        _config_instance = Config(
            env="development",
            debug=True,
            database=DatabaseConfig(
                url=os.getenv(
                    "DATABASE_URL",
                    "postgresql://grc_user:grc_pass@localhost:5432/grc_dev",
                )
            ),
            llm=LLMConfig.for_development(),
            embedding=EmbeddingConfig.for_development(),
            storage=StorageConfig(),
            enable_ai_chat=_bool_env("ENABLE_AI_CHAT", True),
            enable_auto_mapping=_bool_env("ENABLE_AUTO_MAPPING", True),
            enable_mock_data=_bool_env("ENABLE_MOCK_DATA", True),
        )

    return _config_instance
