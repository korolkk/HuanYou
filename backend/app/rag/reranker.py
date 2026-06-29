"""Reranker module — re-ranks retrieval results using cross-encoder models.

Supports:
- BGE-Reranker-v2-m3 (local, via FlagEmbedding)
- Cross-encoder reranking via sentence-transformers
- LLM-based reranking (when model is not available locally)
"""

from typing import Optional


class Reranker:
    """Re-rank search results for better precision.

    Uses a cross-encoder model to score query-document pairs,
    then re-orders results by relevance score.
    """

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3"):
        self.model_name = model_name
        self._model = None

    async def _load_model(self):
        """Lazy-load the reranker model."""
        if self._model is None:
            try:
                from FlagEmbedding import FlagReranker
                self._model = FlagReranker(
                    self.model_name,
                    use_fp16=True,
                )
            except ImportError:
                # Fallback: use sentence-transformers cross-encoder
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(self.model_name)
        return self._model

    async def rerank(
        self,
        query: str,
        results: list[dict],
        top_k: Optional[int] = None,
    ) -> list[dict]:
        """Re-rank search results by relevance to query.

        Args:
            query: Original search query.
            results: List of result dicts with 'content' key.
            top_k: Number of results to keep after reranking.

        Returns:
            Re-ranked results with updated scores.
        """
        if not results:
            return []

        top_k = top_k or len(results)

        try:
            model = await self._load_model()

            # Prepare query-document pairs
            pairs = [[query, r["content"]] for r in results]

            # Score all pairs
            if hasattr(model, 'compute_score'):
                # FlagReranker
                scores = model.compute_score(pairs, normalize=True)
                if isinstance(scores, float):
                    scores = [scores]
            else:
                # CrossEncoder
                scores = model.predict(pairs)
        except Exception:
            # Fallback: keep original ordering with slight decay
            for i, r in enumerate(results):
                r["rerank_score"] = 1.0 / (1 + i * 0.1)
            return results[:top_k]

        # Attach scores and re-sort
        for result, score in zip(results, scores):
            result["rerank_score"] = float(score)

        results.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        return results[:top_k]

    async def rerank_with_llm(
        self,
        query: str,
        results: list[dict],
        top_k: int = 5,
        llm=None,
    ) -> list[dict]:
        """Alternative: use LLM for reranking (when cross-encoder unavailable).

        This sends a prompt to the LLM asking it to rank results by relevance.
        Useful as a fallback or for small result sets.
        """
        if not results or not llm:
            return results[:top_k]

        # Format results for LLM
        candidates_text = "\n\n".join(
            f"[{i}] {r['content'][:300]}"
            for i, r in enumerate(results)
        )

        prompt = f"""你是一个旅游信息检索专家。请根据用户查询，对以下候选结果进行相关性排序。

用户查询: {query}

候选结果:
{candidates_text}

请输出最相关的 {top_k} 个结果的编号，格式: [编号列表]
例如: [3, 0, 7, 1, 5]

只输出编号列表，不要其他内容。"""

        try:
            response = await llm.ainvoke(prompt)
            # Parse the response to get ranked indices
            import re
            import ast
            match = re.search(r'\[[\d,\s]+\]', str(response))
            if match:
                indices = ast.literal_eval(match.group())
            else:
                indices = list(range(min(top_k, len(results))))

            # Reorder results
            reranked = []
            for idx in indices:
                if 0 <= idx < len(results):
                    results[idx]["rerank_score"] = 1.0 - (indices.index(idx) * 0.1)
                    reranked.append(results[idx])

            # Add any remaining results not in indices
            for i, r in enumerate(results):
                if i not in indices:
                    r["rerank_score"] = 0.0
                    reranked.append(r)

            return reranked[:top_k]
        except Exception:
            return results[:top_k]
