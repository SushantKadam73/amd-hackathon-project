"""Tests for RAG knowledge base search functionality.

These tests verify that the hybrid search works correctly against
the seeded knowledge_base table in PostgreSQL.
"""

import pytest

from rag.search_service import SearchService


# =============================================================================
# Hybrid Search Tests
# =============================================================================

class TestSearchService:
    """Test suite for the SearchService class."""

    def setup_method(self) -> None:
        self.search_service = SearchService()

    def test_vector_search_returns_results(self) -> None:
        """Verify vector search returns relevant compliance information."""
        results = self.search_service.search(
            query="Physical access control requirements for datacenter",
            top_k=3,
            search_mode="vector",
        )
        assert len(results) > 0, "Vector search should return at least one result"
        for r in results:
            assert "id" in r
            assert "title" in r
            assert "content" in r
            assert "score" in r
            assert r["search_type"] == "vector"
            assert 0.0 <= r["score"] <= 1.0

    def test_keyword_search_returns_results(self) -> None:
        """Verify keyword search returns relevant results."""
        results = self.search_service.search(
            query="vulnerability scanning remediation",
            top_k=3,
            search_mode="keyword",
        )
        assert len(results) > 0, "Keyword search should return at least one result"
        for r in results:
            assert "id" in r
            assert "search_type" in r

    def test_hybrid_search_returns_results(self) -> None:
        """Verify hybrid search combines vector and keyword results."""
        results = self.search_service.search(
            query="datacenter compliance evidence collection",
            top_k=5,
            search_mode="hybrid",
        )
        assert len(results) > 0, "Hybrid search should return at least one result"
        for r in results:
            assert r["search_type"] == "hybrid"
            assert 0.0 <= r["score"] <= 1.0

    def test_search_with_metadata_filter(self) -> None:
        """Verify search respects metadata filters."""
        results = self.search_service.search(
            query="requirements",
            top_k=5,
            search_mode="vector",
            metadata_filter={"control_id": "PE-03"},
        )
        assert len(results) > 0
        for r in results:
            assert r["metadata"].get("control_id") == "PE-03", (
                f"Expected control_id PE-03, got {r['metadata'].get('control_id')}"
            )

    def test_search_with_different_top_k(self) -> None:
        """Verify top_k parameter controls result count."""
        results_3 = self.search_service.search(
            query="compliance", top_k=3, search_mode="vector"
        )
        results_10 = self.search_service.search(
            query="compliance", top_k=10, search_mode="vector"
        )
        assert len(results_3) <= 3
        assert len(results_10) <= 10
        assert len(results_10) >= len(results_3)

    def test_search_empty_query_returns_results(self) -> None:
        """Verify that even short queries still return results."""
        results = self.search_service.search(
            query="PE-03", top_k=5, search_mode="hybrid"
        )
        assert len(results) > 0, "Search for 'PE-03' should return results"

    def test_search_by_control_id_returns_relevant(self) -> None:
        """Verify searching for a control returns its documentation.

        Uses keyword search mode since mock embeddings do not capture
        semantic similarity. With a real embedding API (OpenRouter/Ollama),
        vector search would also return semantically relevant results.
        """
        results = self.search_service.search(
            query="AC-02 account management",
            top_k=5,
            search_mode="keyword",
        )
        assert len(results) > 0
        titles = [r["title"] for r in results]
        ac02_titles = [t for t in titles if "AC-02" in t]
        assert len(ac02_titles) > 0, (
            f"Expected AC-02 results, got: {titles[:3]}"
        )


# =============================================================================
# Embedding Service Tests
# =============================================================================

class TestEmbeddingService:
    """Test suite for the EmbeddingService class."""

    def test_embedding_dimensions(self) -> None:
        """Verify embeddings are 1024-dimensional."""
        from rag.embedding_service import EmbeddingService

        svc = EmbeddingService()
        vector = svc.embed_text("Test text for embedding")
        assert len(vector) == 1024, (
            f"Expected 1024 dimensions, got {len(vector)}"
        )

    def test_embedding_deterministic(self) -> None:
        """Verify same text produces same embedding (with mock mode)."""
        from rag.embedding_service import EmbeddingService

        svc = EmbeddingService()
        text = "NIST SP 800-53 physical access control"
        v1 = svc.embed_text(text)
        v2 = svc.embed_text(text)
        assert v1 == v2, "Same text should produce identical embeddings"

    def test_embedding_different_texts_differ(self) -> None:
        """Verify different texts produce different embeddings."""
        from rag.embedding_service import EmbeddingService

        svc = EmbeddingService()
        v1 = svc.embed_text("Account management requirements")
        v2 = svc.embed_text("Incident response procedures")
        assert v1 != v2, "Different texts should produce different embeddings"
