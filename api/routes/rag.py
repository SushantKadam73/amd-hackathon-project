"""GRC Platform - RAG Knowledge Base API Routes.

FastAPI endpoints for:
- POST /api/v1/rag/ingest - Ingest documents into the knowledge base
- POST /api/v1/rag/search  - Search the knowledge base using hybrid search
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


# =============================================================================
# Request / Response Schemas
# =============================================================================

class IngestRequest(BaseModel):
    """Request schema for document ingestion."""

    title: str = Field(
        ..., min_length=1, max_length=500,
        description="Document title.",
    )
    content: str = Field(
        ..., min_length=1,
        description="Document text content to ingest.",
    )
    source: str = Field(
        "user_upload",
        description="Source identifier for the document.",
    )
    metadata: Optional[dict[str, Any]] = Field(
        None,
        description="Optional metadata (e.g., control_id, framework, category).",
    )


class IngestResponse(BaseModel):
    """Response schema for document ingestion."""

    document_id: Optional[str] = Field(
        None, description="UUID of the first ingested chunk.",
    )
    title: str = Field(
        ..., description="Document title.",
    )
    chunk_count: int = Field(
        ..., description="Number of chunks the document was split into.",
    )
    message: str = Field(
        ..., description="Status message.",
    )


class SearchRequest(BaseModel):
    """Request schema for knowledge base search."""

    query: str = Field(
        ..., min_length=1, max_length=5000,
        description="Search query text.",
    )
    top_k: int = Field(
        5, ge=1, le=50,
        description="Maximum number of results to return (default 5).",
    )
    search_mode: str = Field(
        "hybrid",
        description="Search mode: 'vector', 'keyword', or 'hybrid' (default).",
    )
    vector_weight: float = Field(
        0.7, ge=0.0, le=1.0,
        description="Weight for vector similarity in hybrid mode (default 0.7).",
    )
    keyword_weight: float = Field(
        0.3, ge=0.0, le=1.0,
        description="Weight for keyword matching in hybrid mode (default 0.3).",
    )
    metadata_filter: Optional[dict[str, Any]] = Field(
        None,
        description="Optional filter on metadata fields (e.g., {'control_id': 'PE-03'}).",
    )


class SearchResultItem(BaseModel):
    """A single search result item."""

    id: str = Field(
        ..., description="UUID of the knowledge entry.",
    )
    title: str = Field(
        ..., description="Entry title.",
    )
    content: str = Field(
        ..., description="Entry text content.",
    )
    source: str = Field(
        ..., description="Source identifier.",
    )
    score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Relevance score (0.0-1.0).",
    )
    search_type: str = Field(
        ..., description="Search type that found this result: 'vector', 'keyword', or 'hybrid'.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Entry metadata.",
    )


class SearchResponse(BaseModel):
    """Response schema for knowledge base search."""

    results: list[SearchResultItem] = Field(
        ..., description="List of search results.",
    )
    total: int = Field(
        ..., description="Total number of results returned.",
    )
    query: str = Field(
        ..., description="The original search query.",
    )
    search_mode: str = Field(
        ..., description="Search mode used.",
    )


class ErrorResponse(BaseModel):
    """Response schema for error conditions."""

    detail: str = Field(
        ..., description="Error description.",
    )


# =============================================================================
# Helper Functions
# =============================================================================

def _create_audit_log(
    action: str,
    entity_type: str,
    entity_id: str,
    user_id: Optional[str] = None,
    new_values: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
) -> None:
    """Create an audit log entry for a RAG action.

    Args:
        action: The action type (RAG_INGEST, RAG_SEARCH).
        entity_type: The entity type.
        entity_id: The entity ID.
        user_id: Optional user ID.
        new_values: Optional additional context.
        ip_address: Optional IP address.
    """
    try:
        from api.database import create_audit_log as db_audit

        db_audit(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user_id,
            new_values=new_values or {},
            ip_address=ip_address,
        )
    except Exception:
        # Audit logging should never break the main flow
        pass


# =============================================================================
# Routes
# =============================================================================

@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Ingest a document into the knowledge base",
    description=(
        "Splits a document into chunks, generates embedding vectors, "
        "and stores them in the pgvector knowledge base. "
        "Ingested content is immediately available for search."
    ),
)
async def ingest_document(
    request: Request,
    body: IngestRequest,
) -> dict[str, Any]:
    """Ingest a document into the RAG knowledge base.

    The document is automatically chunked, embedded, and stored
    in the knowledge_base table for vector similarity search.
    """
    try:
        from rag.knowledge_loader import ingest_document as ingest  # noqa: WPS433

        ip_address = request.client.host if request.client else None

        result = ingest(
            title=body.title,
            content=body.content,
            source=body.source,
            metadata=body.metadata,
            ip_address=ip_address,
        )

        # Log the ingestion
        _create_audit_log(
            action="RAG_INGEST",
            entity_type="knowledge_base",
            entity_id=result.get("document_id") or "unknown",
            new_values={
                "title": body.title,
                "chunk_count": result["chunk_count"],
                "source": body.source,
            },
            ip_address=ip_address,
        )

        return IngestResponse(
            document_id=result.get("document_id"),
            title=result["title"],
            chunk_count=result["chunk_count"],
            message=(
                f"Successfully ingested '{body.title}' "
                f"({result['chunk_count']} chunks created)."
            ),
        )

    except Exception as e:
        logger.error(f"Failed to ingest document '{body.title}': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest document: {str(e)}",
        )


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search the knowledge base",
    description=(
        "Performs hybrid search (vector + keyword) on the compliance "
        "knowledge base. Returns the most relevant document chunks "
        "with similarity scores. Supports filtering by metadata fields "
        "like control_id, framework, or category."
    ),
)
async def search_knowledge_base(
    request: Request,
    body: SearchRequest,
) -> dict[str, Any]:
    """Search the RAG knowledge base for relevant compliance information.

    Uses hybrid search combining vector similarity and keyword matching
    to find the most relevant document chunks.
    """
    try:
        from rag.search_service import SearchService  # noqa: WPS433

        search_service = SearchService()

        results = search_service.search(
            query=body.query,
            top_k=body.top_k,
            search_mode=body.search_mode,
            vector_weight=body.vector_weight,
            keyword_weight=body.keyword_weight,
            metadata_filter=body.metadata_filter,
        )

        # Format results
        result_items = []
        for r in results:
            result_items.append(
                SearchResultItem(
                    id=r["id"],
                    title=r["title"],
                    content=r["content"],
                    source=r["source"],
                    score=r["score"],
                    search_type=r.get("search_type", "hybrid"),
                    metadata=r.get("metadata", {}),
                )
            )

        # Log the search
        ip_address = request.client.host if request.client else None
        _create_audit_log(
            action="RAG_SEARCH",
            entity_type="knowledge_base",
            entity_id="search",
            new_values={
                "query": body.query[:200],
                "result_count": len(result_items),
                "search_mode": body.search_mode,
            },
            ip_address=ip_address,
        )

        return SearchResponse(
            results=result_items,
            total=len(result_items),
            query=body.query,
            search_mode=body.search_mode,
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed for query '{body.query[:50]}...': {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}",
        )
