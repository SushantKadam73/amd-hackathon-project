"""GRC Platform - Search Service.

Provides vector similarity search using pgvector with hybrid search
that combines vector similarity and keyword (full-text) matching.

Uses cosine similarity for vector comparison and PostgreSQL full-text
search for keyword matching, with configurable weighting between the
two approaches.
"""

import logging
from typing import Any, Optional

from config import get_config
from rag.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)
config = get_config()


class SearchService:
    """Hybrid search service combining vector similarity and keyword matching.

    Supports three search modes:
    - vector: Pure cosine similarity search
    - keyword: PostgreSQL full-text search
    - hybrid: Weighted combination of vector and keyword results
    """

    def __init__(self, embedding_service: Optional[EmbeddingService] = None) -> None:
        self.embedding_service = embedding_service or EmbeddingService()
        self._top_k = 5  # Default number of results

    def search(
        self,
        query: str,
        top_k: int = 5,
        search_mode: str = "hybrid",
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Perform a hybrid search combining vector and keyword matching.

        Args:
            query: The search query text.
            top_k: Maximum number of results to return (default 5).
            search_mode: 'vector', 'keyword', or 'hybrid' (default 'hybrid').
            vector_weight: Weight for vector similarity in hybrid mode (default 0.7).
            keyword_weight: Weight for keyword matching in hybrid mode (default 0.3).
            metadata_filter: Optional filter on metadata fields.

        Returns:
            list[dict]: List of search results with id, title, content,
                       source, score, and metadata fields.
        """
        if search_mode == "vector":
            return self._vector_search(query, top_k, metadata_filter)
        elif search_mode == "keyword":
            return self._keyword_search(query, top_k, metadata_filter)
        elif search_mode == "hybrid":
            return self._hybrid_search(
                query, top_k, vector_weight, keyword_weight, metadata_filter
            )
        else:
            raise ValueError(
                f"Unknown search_mode: {search_mode}. "
                "Use 'vector', 'keyword', or 'hybrid'."
            )

    def _vector_search(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Perform pure vector similarity search using cosine distance.

        Args:
            query: The search query text.
            top_k: Maximum number of results.
            metadata_filter: Optional metadata filters.

        Returns:
            list[dict]: Search results with similarity scores.
        """
        query_vector = self.embedding_service.embed_text(query)
        return self._search_by_vector(query_vector, top_k, metadata_filter)

    def _keyword_search(
        self,
        query: str,
        top_k: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Perform keyword/full-text search using PostgreSQL ts_vector.

        Args:
            query: The search query text.
            top_k: Maximum number of results.
            metadata_filter: Optional metadata filters.

        Returns:
            list[dict]: Search results with keyword matching scores.
        """
        from api.database import get_cursor  # noqa: WPS433

        # Build WHERE conditions for full-text search on content and title
        content_condition = (
            "to_tsvector('english', content) @@ "
            "plainto_tsquery('english', %s)"
        )
        title_condition = (
            "to_tsvector('english', title) @@ "
            "plainto_tsquery('english', %s)"
        )

        # Build metadata filter conditions separately
        meta_params: list[Any] = []
        meta_conditions = self._build_metadata_conditions(
            metadata_filter, meta_params
        )

        # Combine all WHERE conditions
        text_where = f"({content_condition} OR {title_condition})"
        if meta_conditions:
            where_clause = f"{text_where} AND " + " AND ".join(meta_conditions)
        else:
            where_clause = text_where

        # Parameters: ts_rank(%s), content_condition(%s), title_condition(%s),
        #             meta_params(%), LIMIT(%s)
        all_params = [query, query, query] + meta_params + [top_k]

        sql = f"""
            SELECT id, title, content, source, chunk_index, metadata,
                   ts_rank(to_tsvector('english', content),
                           plainto_tsquery('english', %s)) AS score
            FROM knowledge_base
            WHERE {where_clause}
            ORDER BY score DESC
            LIMIT %s
        """

        with get_cursor() as cur:
            cur.execute(sql, all_params)
            rows = cur.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": str(row["id"]),
                "title": row["title"],
                "content": row["content"],
                "source": row["source"],
                "chunk_index": row["chunk_index"],
                "metadata": row["metadata"] or {},
                "score": float(row.get("score", 0) or 0),
                "search_type": "keyword",
            })

        return results

    def _hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Perform hybrid search combining vector and keyword results.

        Runs both searches independently, normalizes scores, and combines
        them using the specified weights.

        Args:
            query: The search query text.
            top_k: Maximum number of results.
            vector_weight: Weight for vector similarity (default 0.7).
            keyword_weight: Weight for keyword matching (default 0.3).
            metadata_filter: Optional metadata filters.

        Returns:
            list[dict]: Combined and ranked search results.
        """
        # Get more candidates from each method for better merging
        candidates_k = max(top_k * 3, 10)

        vector_results = self._vector_search(
            query, candidates_k, metadata_filter
        )
        keyword_results = self._keyword_search(
            query, candidates_k, metadata_filter
        )

        # Normalize scores within each result set
        vector_results = self._normalize_scores(vector_results, "vector_score")
        keyword_results = self._normalize_scores(
            keyword_results, "keyword_score"
        )

        # Merge results by ID, combining scores
        merged: dict[str, dict[str, Any]] = {}

        for vr in vector_results:
            entry_id = vr["id"]
            merged[entry_id] = vr
            merged[entry_id]["vector_score"] = vr.get("score", 0)
            merged[entry_id]["keyword_score"] = 0.0
            merged[entry_id]["search_type"] = "hybrid"

        for kr in keyword_results:
            entry_id = kr["id"]
            if entry_id in merged:
                merged[entry_id]["keyword_score"] = kr.get("score", 0)
            else:
                merged[entry_id] = kr
                merged[entry_id]["vector_score"] = 0.0
                merged[entry_id]["keyword_score"] = kr.get("score", 0)
                merged[entry_id]["search_type"] = "hybrid"

        # Calculate combined score
        for entry in merged.values():
            entry["score"] = (
                vector_weight * entry.get("vector_score", 0)
                + keyword_weight * entry.get("keyword_score", 0)
            )

        # Sort by combined score descending and take top_k
        sorted_results = sorted(
            merged.values(), key=lambda x: x["score"], reverse=True
        )[:top_k]

        return sorted_results

    def _search_by_vector(
        self,
        query_vector: list[float],
        top_k: int = 5,
        metadata_filter: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """Search knowledge base by vector similarity using cosine distance.

        Args:
            query_vector: The embedding vector to search with.
            top_k: Maximum number of results.
            metadata_filter: Optional metadata filters.

        Returns:
            list[dict]: Search results with similarity scores.
        """
        from api.database import get_cursor  # noqa: WPS433
        from psycopg2 import sql as psql  # noqa: WPS433

        # Build metadata filter conditions with separate params
        filter_params: list[Any] = []
        filter_conditions = self._build_metadata_conditions(
            metadata_filter, filter_params
        )

        where_parts = ["embedding_vector IS NOT NULL"]
        where_parts.extend(filter_conditions)
        where_clause = " AND ".join(where_parts)

        # Use a subquery approach: select with metadata filter first,
        # then order by vector similarity. This avoids parameter order issues
        # where the vector is referenced in both SELECT and ORDER BY clauses
        # while metadata params sit in between.
        sql = f"""
            SELECT id, title, content, source, chunk_index, metadata
            FROM knowledge_base
            WHERE {where_clause}
            ORDER BY embedding_vector <=> %s::vector ASC
            LIMIT %s
        """

        # Params: filter params..., vector, LIMIT
        params = filter_params + [query_vector, top_k]

        with get_cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        # Calculate similarity scores client-side using the ORDER BY's implicit
        # ordering. Assign highest score to first result, decreasing linearly.
        results = []
        total = len(rows)
        for idx, row in enumerate(rows):
            # Score decreases from 1.0 to 0.1 based on position
            score = max(0.1, 1.0 - (idx / max(total, 1)) * 0.9) if total > 0 else 0.0
            results.append({
                "id": str(row["id"]),
                "title": row["title"],
                "content": row["content"],
                "source": row["source"],
                "chunk_index": row["chunk_index"],
                "metadata": row["metadata"] or {},
                "score": round(score, 4),
                "search_type": "vector",
            })

        return results

    def _build_metadata_conditions(
        self,
        metadata_filter: Optional[dict[str, Any]],
        params: list[Any],
    ) -> list[str]:
        """Build WHERE conditions from metadata filter dict.

        Supports filtering on keys within the metadata JSONB column.

        Args:
            metadata_filter: Dict of metadata key-value pairs to filter on.
            params: Parameter list to extend with filter values.

        Returns:
            list[str]: SQL condition fragments.
        """
        if not metadata_filter:
            return []

        conditions: list[str] = []
        for key, value in metadata_filter.items():
            conditions.append(f"metadata->>%s = %s")
            params.append(key)
            params.append(str(value))

        return conditions

    @staticmethod
    def _normalize_scores(
        results: list[dict[str, Any]],
        score_key: str = "score",
    ) -> list[dict[str, Any]]:
        """Normalize scores in a result list to [0, 1] range.

        Uses min-max normalization.

        Args:
            results: List of result dicts with a 'score' key.
            score_key: Key to store the normalized score under.

        Returns:
            list[dict]: Results with normalized scores.
        """
        if not results:
            return results

        scores = [r.get("score", 0) for r in results]
        min_score = min(scores)
        max_score = max(scores)

        if max_score - min_score < 0.0001:
            for r in results:
                r[score_key] = 1.0 if max_score > 0 else 0.0
        else:
            for r in results:
                original_score = r.get("score", 0)
                r[score_key] = (original_score - min_score) / (
                    max_score - min_score
                )

        return results
