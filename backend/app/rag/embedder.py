"""Embedding model wrapper - supports local and cloud embedding models."""

from typing import Optional

from app.config import get_settings


class Embedder:
    """Embedding model abstraction.

    Supports:
    - Local: BAAI/bge-large-zh-v1.5 (via sentence-transformers)
    - Cloud: DashScope text-embedding-v4
    - Cloud: OpenAI-compatible embedding APIs (via DeepSeek)
    """

    def __init__(self, model_name: Optional[str] = None):
        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self._model = None
        self._model_type = self._detect_model_type()

    def _detect_model_type(self) -> str:
        """Detect whether to use local or cloud embedding."""
        if self.model_name in ("bge-large-zh-v1.5", "bge-base-zh-v1.5", "bge-small-zh-v1.5"):
            return "local"
        if self.model_name == "text-embedding-v4":
            return "dashscope"
        return "openai"  # OpenAI-compatible API

    async def _load_local_model(self):
        """Lazy-load the local sentence-transformers model."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                f"BAAI/{self.model_name}" if "/" not in self.model_name else self.model_name,
                device=self.device,
            )
        return self._model

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (each is list[float]).
        """
        if not texts:
            return []

        if self._model_type == "local":
            model = await self._load_local_model()
            embeddings = model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.tolist()

        elif self._model_type == "dashscope":
            return await self._embed_dashscope(texts)

        else:  # openai-compatible
            return await self._embed_openai(texts)

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        results = await self.embed_texts([text])
        return results[0]

    async def _embed_openai(self, texts: list[str]) -> list[list[float]]:
        """Use OpenAI-compatible embedding API (DeepSeek, etc.)."""
        from openai import AsyncOpenAI
        settings = get_settings()

        client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        response = await client.embeddings.create(
            model="text-embedding-3-small",  # or custom model
            input=texts,
        )
        return [d.embedding for d in response.data]

    async def _embed_dashscope(self, texts: list[str]) -> list[list[float]]:
        """Use DashScope embedding API (text-embedding-v4)."""
        import dashscope
        from http import HTTPStatus
        settings = get_settings()

        # DashScope embedding supports batch, process one by one for batch
        embeddings = []
        for text in texts:
            resp = dashscope.TextEmbedding.call(
                model="text-embedding-v4",
                input=text,
                api_key=settings.DASHSCOPE_API_KEY,
            )
            if resp.status_code == HTTPStatus.OK:
                embeddings.append(resp.output["embeddings"][0]["embedding"])
            else:
                raise RuntimeError(f"DashScope embedding failed: {resp.message}")
        return embeddings
