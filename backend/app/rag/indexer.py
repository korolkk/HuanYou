"""RAG document indexer — ingests documents into pgvector."""

import hashlib
from typing import Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk
from app.rag.chunker import ChineseChunker
from app.rag.embedder import Embedder


class RAGIndexer:
    """Ingestion pipeline: chunk → embed → index into pgvector.

    Handles:
    - Chunking documents into semantic segments
    - Generating embeddings via local or cloud models
    - Storing in document_chunks table with metadata
    - Updating PostgreSQL full-text search vectors
    - Deduplication based on content hash
    """

    def __init__(self, embedder: Optional[Embedder] = None, chunker: Optional[ChineseChunker] = None):
        self.embedder = embedder or Embedder()
        self.chunker = chunker or ChineseChunker()

    async def index_document(
        self,
        db: AsyncSession,
        content: str,
        source_file: str,
        source_type: str,
        metadata: Optional[dict] = None,
    ) -> int:
        """Index a single document into the vector store.

        Args:
            db: Database session.
            content: Raw text content.
            source_file: Original filename or identifier.
            source_type: Type of document (trip/schedule/policy/faq/destination).
            metadata: Additional metadata dict (trip_id, destination, etc.)

        Returns:
            Number of chunks indexed.
        """
        # Chunk the content
        chunks = self.chunker.split(content)
        if not chunks:
            return 0

        # Filter out duplicates by hash
        new_chunks = []
        new_hashes = set()

        for i, chunk_text in enumerate(chunks):
            chunk_hash = ChineseChunker.compute_hash(chunk_text)

            # Check if already indexed
            existing = await db.execute(
                select(DocumentChunk).where(
                    DocumentChunk.content_hash == chunk_hash,
                    DocumentChunk.source_file == source_file,
                )
            )
            if existing.scalar_one_or_none():
                continue

            if chunk_hash not in new_hashes:
                new_chunks.append((i, chunk_text, chunk_hash))
                new_hashes.add(chunk_hash)

        if not new_chunks:
            return 0  # All duplicates

        # Batch embed
        texts = [c[1] for c in new_chunks]
        embeddings = await self.embedder.embed_texts(texts)

        # Store in DB
        merged_metadata = {
            "source_file": source_file,
            "source_type": source_type,
            **(metadata or {}),
        }

        for (idx, chunk_text, chunk_hash), embedding in zip(new_chunks, embeddings):
            doc_chunk = DocumentChunk(
                source_file=source_file,
                source_type=source_type,
                chunk_index=idx,
                content=chunk_text,
                content_hash=chunk_hash,
                metadata_=merged_metadata,
                embedding=embedding,
            )
            db.add(doc_chunk)

        # Update full-text search vectors (PostgreSQL handles tsvector generation)
        await db.flush()

        # Update tsvector from content
        from sqlalchemy import text
        await db.execute(
            text(
                "UPDATE document_chunks SET search_vector = "
                "to_tsvector('chinese', content) "
                "WHERE search_vector IS NULL AND source_file = :src"
            ),
            {"src": source_file},
        )

        return len(new_chunks)

    async def index_trip(
        self,
        db: AsyncSession,
        trip_id: str,
        trip_data: dict,
        schedules: list[dict],
        source_file: str = "",
    ) -> int:
        """Index a complete trip (metadata + schedules) into RAG.

        Args:
            db: Database session.
            trip_id: UUID of the trip.
            trip_data: Dict of trip metadata.
            schedules: List of day-by-day schedule dicts.

        Returns:
            Total chunks indexed.
        """
        total_chunks = 0

        metadata = {
            "trip_id": trip_id,
            "destination": trip_data.get("destination", ""),
            "category": trip_data.get("category", ""),
            "duration_days": trip_data.get("duration_days", 0),
            "season": trip_data.get("best_season", ""),
        }

        # 1. Index trip summary/description
        trip_text_parts = []
        for field in ["title", "subtitle", "summary", "detailed_description",
                       "highlights", "recommendation_reasons",
                       "price_includes", "price_excludes"]:
            val = trip_data.get(field)
            if val:
                if isinstance(val, list):
                    trip_text_parts.append("\n".join(val))
                else:
                    trip_text_parts.append(str(val))

        trip_text = "\n\n".join(trip_text_parts)
        if trip_text.strip():
            count = await self.index_document(
                db, trip_text,
                source_file=f"trip:{trip_id}:overview" if not source_file else f"{source_file}:overview",
                source_type="trip",
                metadata=metadata,
            )
            total_chunks += count

        # 2. Index each day's schedule
        for s in schedules:
            schedule_text_parts = []
            for field in ["theme", "schedule_type", "location", "activity",
                           "description", "meal_included", "hotel_name",
                           "transport_detail", "tips"]:
                val = s.get(field)
                if val:
                    schedule_text_parts.append(f"{field}: {val}")

            schedule_text = f"第{s.get('day_number', '?')}天\n" + "\n".join(schedule_text_parts)

            schedule_metadata = {
                **metadata,
                "day_number": s.get("day_number", 0),
            }

            count = await self.index_document(
                db, schedule_text,
                source_file=f"trip:{trip_id}:day{s.get('day_number', '?')}" if not source_file else f"{source_file}:day{s.get('day_number', '?')}",
                source_type="schedule",
                metadata=schedule_metadata,
            )
            total_chunks += count

        return total_chunks

    async def remove_document(
        self,
        db: AsyncSession,
        source_file: str,
    ) -> int:
        """Remove all chunks for a given source file."""
        from sqlalchemy import delete
        result = await db.execute(
            delete(DocumentChunk).where(DocumentChunk.source_file == source_file)
        )
        return result.rowcount
