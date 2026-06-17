"""GRC Platform - Embedding Service.

Generates vector embeddings for compliance documents using:
- Development: OpenRouter embeddings API (baai/bge-m3, 1024-dim)
- Production: NVIDIA Llama Nemotron Embed via Ollama (localhost:11434)

Provides a deterministic mock embedding fallback when ENABLE_MOCK_DATA=true
or when the embedding API is unavailable (e.g., no credits).

Outputs 1024-dimensional vectors for pgvector storage.
"""

import hashlib
import json
import logging
import math
import os
from typing import Optional

import requests
from urllib.parse import urljoin

from config import get_config

logger = logging.getLogger(__name__)
config = get_config()


class EmbeddingService:
    """Service for generating text embeddings.

    Supports three modes:
    - openrouter: Uses OpenRouter API (dev)
    - ollama: Uses local Ollama instance (prod)
    - mock: Deterministic hash-based embeddings for testing/offline use

    When ENABLE_MOCK_DATA is true, uses mock embeddings to avoid API costs.
    """

    def __init__(self) -> None:
        self.provider = config.embedding.provider
        self.model = config.embedding.model
        self.api_key = config.embedding.api_key
        self.base_url = config.embedding.base_url
        self.dimensions = config.embedding.dimensions
        self.use_mock = config.enable_mock_data

    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text string.

        Tries the configured provider first. Falls back to deterministic
        mock embeddings when the API is unavailable or mock mode is enabled.

        Args:
            text: Input text to embed.

        Returns:
            list[float]: 1024-dimensional embedding vector.
        """
        if self.use_mock:
            return self._embed_mock(text)

        if self.provider == "openrouter":
            try:
                return self._embed_openrouter(text)
            except Exception as e:
                logger.warning(
                    f"OpenRouter embedding failed ({e}), "
                    "falling back to mock embedding"
                )
                return self._embed_mock(text)
        elif self.provider == "ollama":
            try:
                return self._embed_ollama(text)
            except Exception as e:
                logger.warning(
                    f"Ollama embedding failed ({e}), "
                    "falling back to mock embedding"
                )
                return self._embed_mock(text)
        else:
            logger.warning(
                f"Unknown embedding provider: {self.provider}, "
                "using mock embedding"
            )
            return self._embed_mock(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of text strings.

        Args:
            texts: List of input texts to embed.

        Returns:
            list[list[float]]: List of 1024-dimensional embedding vectors.
        """
        results: list[list[float]] = []
        for text in texts:
            try:
                vector = self.embed_text(text)
                results.append(vector)
            except Exception as e:
                logger.error(f"Failed to embed text chunk: {e}")
                results.append([0.0] * self.dimensions)
        return results

    def _embed_mock(self, text: str) -> list[float]:
        """Generate a deterministic mock embedding vector from text hash.

        Produces consistent 1024-dimensional vectors using SHA-256 hashing
        and a deterministic pseudo-random generator. Same text always
        produces the same vector, enabling basic similarity comparisons.

        Args:
            text: Input text to embed.

        Returns:
            list[float]: 1024-dimensional mock embedding vector.
        """
        # Create a deterministic seed from text hash
        hash_bytes = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(hash_bytes[:8], "big")
        rng = _SimpleRNG(seed)

        vector = [rng.next_float() * 2.0 - 1.0 for _ in range(self.dimensions)]

        # Normalize to unit length for cosine similarity
        magnitude = math.sqrt(sum(v * v for v in vector))
        if magnitude > 0:
            vector = [v / magnitude for v in vector]

        return vector

    def _embed_openrouter(self, text: str) -> list[float]:
        """Generate embedding via OpenRouter API.

        Uses the OpenRouter embeddings endpoint at:
        {base_url}/embeddings

        Args:
            text: Input text to embed.

        Returns:
            list[float]: Embedding vector.

        Raises:
            RuntimeError: If API call fails.
        """
        if not self.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY not configured. "
                "Set it in .env for embedding generation."
            )

        # base_url already includes /api/v1 (e.g., "https://openrouter.ai/api/v1")
        url = urljoin(self.base_url.rstrip("/") + "/", "embeddings")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": text,
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            embedding = data["data"][0]["embedding"]
            return embedding
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OpenRouter embedding API error: {e}") from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Unexpected response format from OpenRouter: {e}"
            ) from e

    def _embed_ollama(self, text: str) -> list[float]:
        """Generate embedding via local Ollama instance.

        Args:
            text: Input text to embed.

        Returns:
            list[float]: Embedding vector.

        Raises:
            RuntimeError: If Ollama call fails.
        """
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        url = urljoin(ollama_url.rstrip("/") + "/", "api/embeddings")
        payload = {
            "model": self.model,
            "prompt": text,
        }

        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            embedding = data["embedding"]
            return embedding
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama embedding API error: {e}") from e
        except (KeyError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Unexpected response format from Ollama: {e}"
            ) from e

    @staticmethod
    def validate_dimensions(vector: list[float], expected: int = 1024) -> bool:
        """Validate that a vector has the expected number of dimensions.

        Args:
            vector: The embedding vector to validate.
            expected: Expected dimensionality (default 1024).

        Returns:
            bool: True if dimensions match, False otherwise.
        """
        return len(vector) == expected


class _SimpleRNG:
    """Simple deterministic pseudo-random number generator.

    Implements a linear congruential generator (LCG) for creating
    reproducible mock embedding vectors.
    """

    def __init__(self, seed: int) -> None:
        self.state = seed % (2**31 - 1)

    def next_float(self) -> float:
        """Generate the next pseudo-random float in [0, 1).

        Returns:
            float: Next random value.
        """
        self.state = (self.state * 1103515245 + 12345) % (2**31)
        return self.state / (2**31)
