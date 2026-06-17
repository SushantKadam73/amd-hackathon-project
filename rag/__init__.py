"""GRC Platform - RAG Knowledge Base Package.

Provides Retrieval-Augmented Generation (RAG) capabilities for compliance
knowledge retrieval. Includes embedding generation, knowledge loading,
and vector similarity search with hybrid (vector + keyword) support.
"""

from rag.embedding_service import EmbeddingService
from rag.knowledge_loader import (
    chunk_text,
    get_preloaded_knowledge,
    ingest_document,
    load_preloaded_knowledge,
)
from rag.search_service import SearchService

__all__ = [
    "EmbeddingService",
    "SearchService",
    "chunk_text",
    "get_preloaded_knowledge",
    "ingest_document",
    "load_preloaded_knowledge",
]
