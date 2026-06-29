"""Chinese-optimized text chunker for RAG document processing."""

import hashlib
from typing import Optional

from app.config import get_settings


class ChineseChunker:
    """Chinese-language-optimized text splitter.

    Uses a recursive character splitter with Chinese-specific separators
    to produce semantically coherent chunks for embedding.
    """

    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ):
        settings = get_settings()
        self.chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.RAG_CHUNK_OVERLAP

        # Chinese-specific separators in priority order
        self.separators = [
            "\n\n",    # paragraph breaks
            "\n",      # line breaks
            "。",      # Chinese period
            "！",      # Chinese exclamation
            "？",      # Chinese question mark
            "；",      # Chinese semicolon
            "，",      # Chinese comma
            ".",       # English period
            "!",       # English exclamation
            "?",       # English question
            ";",       # English semicolon
            ",",       # English comma
            " ",       # space (last resort)
        ]

    def split(self, text: str) -> list[str]:
        """Split text into chunks using Chinese-aware separators.

        Args:
            text: Raw text to split.

        Returns:
            List of text chunks.
        """
        return self._recursive_split(text, self.separators)

    def _recursive_split(
        self, text: str, separators: list[str]
    ) -> list[str]:
        """Recursively split text using the given separators."""
        # Try each separator in order
        for i, separator in enumerate(separators):
            if separator == "":
                # Final fallback: split by character
                return self._split_by_chars(text)

            if separator in text:
                parts = text.split(separator)
                chunks = []

                current_chunk = ""
                for part in parts:
                    # Re-add separator except for spaces
                    test_chunk = (
                        current_chunk + separator + part
                        if current_chunk
                        else part
                    )

                    if len(test_chunk) <= self.chunk_size:
                        current_chunk = test_chunk
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())

                        if len(part) > self.chunk_size:
                            # Recurse with next separator
                            sub_chunks = self._recursive_split(
                                part, separators[i + 1 :]
                            )
                            chunks.extend(sub_chunks)
                            current_chunk = ""
                        else:
                            current_chunk = part

                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Add overlap by taking the last `overlap` chars of prev chunk
                if self.chunk_overlap > 0 and len(chunks) > 1:
                    overlapped = []
                    for j, chunk in enumerate(chunks):
                        if j > 0 and len(chunks[j - 1]) > self.chunk_overlap:
                            prefix = chunks[j - 1][-self.chunk_overlap:]
                            overlapped.append(prefix + chunk)
                        else:
                            overlapped.append(chunk)
                    return overlapped

                return chunks

        # If no separator matched, split by chars
        return self._split_by_chars(text)

    def _split_by_chars(self, text: str) -> list[str]:
        """Split text into fixed-size character chunks."""
        chunks = []
        for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
            chunk = text[i : i + self.chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())
        return chunks

    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
