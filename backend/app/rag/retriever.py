"""Hybrid RAG retriever with semantic + keyword search + RRF fusion."""

from typing import Optional
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.rag.embedder import Embedder


class HybridRetriever:
    """Hybrid retrieval pipeline for travel knowledge.

    Combines:
    1. Semantic search (pgvector cosine similarity)
    2. Keyword search (PostgreSQL Chinese full-text search)
    3. RRF (Reciprocal Rank Fusion) to merge results
    4. Metadata filtering for structured constraints
    """

    def __init__(self, embedder: Optional[Embedder] = None):
        self.embedder = embedder or Embedder()
        self.settings = get_settings()
        self.top_k = self.settings.RAG_TOP_K
        self.similarity_threshold = self.settings.RAG_SIMILARITY_THRESHOLD

    async def search(
        self,
        db: AsyncSession,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[dict] = None,
        source_types: Optional[list[str]] = None,
    ) -> list[dict]:
        """Execute hybrid search.

        Args:
            db: Database session.
            query: Natural language search query.
            top_k: Number of results to return (default from settings).
            filters: Metadata filters as key-value pairs.
            source_types: Filter by source_type (trip/schedule/policy/faq).

        Returns:
            List of result dicts with keys: id, content, metadata, score, source_type.
        """
        top_k = top_k or self.top_k

        # Get query embedding
        query_embedding = await self.embedder.embed_text(query)

        # Run semantic and keyword searches in parallel
        semantic_results = await self._semantic_search(
            db, query_embedding, top_k * 4, filters, source_types
        )
        keyword_results = await self._keyword_search(
            db, query, top_k * 4, filters, source_types
        )

        # RRF fusion
        fused = self._rrf_fusion(semantic_results, keyword_results, k=60)

        # Return top_k results
        return fused[:top_k]

    async def _semantic_search(
        self,
        db: AsyncSession,
        query_embedding: list[float],
        top_k: int,
        filters: Optional[dict],
        source_types: Optional[list[str]],
    ) -> list[dict]:
        """pgvector cosine similarity search."""
        # Build the query with optional filters
        filter_clauses = []
        params = {
            "embedding": query_embedding,
            "threshold": self.similarity_threshold,
            "k": top_k,
        }

        if source_types:
            filter_clauses.append("dc.source_type = ANY(:source_types)")
            params["source_types"] = source_types

        if filters:
            for i, (key, val) in enumerate(filters.items()):
                param_name = f"filter_{i}"
                filter_clauses.append(
                    f"dc.metadata ->> '{key}' = :{param_name}"
                )
                params[param_name] = str(val)

        where_extra = " AND " + " AND ".join(filter_clauses) if filter_clauses else ""

        query_sql = text(f"""
            SELECT
                dc.id,
                dc.content,
                dc.metadata,
                dc.source_type,
                dc.source_file,
                1 - (dc.embedding <=> :embedding) AS similarity
            FROM document_chunks dc
            WHERE 1 - (dc.embedding <=> :embedding) > :threshold
                {where_extra}
            ORDER BY dc.embedding <=> :embedding
            LIMIT :k
        """)

        result = await db.execute(query_sql, params)
        rows = result.fetchall()

        return [
            {
                "id": str(row[0]),
                "content": row[1],
                "metadata": row[2],
                "source_type": row[3],
                "source_file": row[4],
                "score": float(row[5]),
            }
            for row in rows
        ]

    async def _keyword_search(
        self,
        db: AsyncSession,
        query: str,
        top_k: int,
        filters: Optional[dict],
        source_types: Optional[list[str]],
    ) -> list[dict]:
        """PostgreSQL Chinese full-text search."""
        filter_clauses = []
        params = {"query": query, "k": top_k}

        if source_types:
            filter_clauses.append("dc.source_type = ANY(:source_types)")
            params["source_types"] = source_types

        if filters:
            for i, (key, val) in enumerate(filters.items()):
                param_name = f"filter_{i}"
                filter_clauses.append(
                    f"dc.metadata ->> '{key}' = :{param_name}"
                )
                params[param_name] = str(val)

        where_extra = " AND " + " AND ".join(filter_clauses) if filter_clauses else ""

        query_sql = text(f"""
            SELECT
                dc.id,
                dc.content,
                dc.metadata,
                dc.source_type,
                dc.source_file,
                ts_rank(dc.search_vector, plainto_tsquery('chinese', :query)) AS rank
            FROM document_chunks dc
            WHERE dc.search_vector @@ plainto_tsquery('chinese', :query)
                {where_extra}
            ORDER BY rank DESC
            LIMIT :k
        """)

        try:
            result = await db.execute(query_sql, params)
            rows = result.fetchall()
        except Exception:
            # Full-text search might fail if no results match; return empty
            return []

        return [
            {
                "id": str(row[0]),
                "content": row[1],
                "metadata": row[2],
                "source_type": row[3],
                "source_file": row[4],
                "score": float(row[5]) if row[5] else 0.0,
            }
            for row in rows
        ]

    def _rrf_fusion(
        self,
        semantic_results: list[dict],
        keyword_results: list[dict],
        k: int = 60,
    ) -> list[dict]:
        """Reciprocal Rank Fusion — combines two ranked lists.

        Formula: RRF(d) = sum_{r in rankings} 1/(k + rank(d, r))

        Args:
            semantic_results: Results from semantic search.
            keyword_results: Results from keyword search.
            k: Constant to prevent high ranks from dominating (default 60).

        Returns:
            Fused and sorted list of results.
        """
        scores = {}
        results_map = {}

        # Score semantic results
        for rank, result in enumerate(semantic_results, start=1):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
            results_map[doc_id] = result

        # Score keyword results
        for rank, result in enumerate(keyword_results, start=1):
            doc_id = result["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank)
            results_map[doc_id] = result

        # Sort by RRF score descending
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        fused = [results_map[doc_id] for doc_id in sorted_ids]

        # Add the RRF score
        for result in fused:
            result["rrf_score"] = scores[result["id"]]

        return fused
