"""Cross-Encoder reranking module.

Implements Playbook Section 2 & 3:
- Optional cross-encoder reranking.
- Skips gracefully under load or when cross-encoder is not installed.
"""

from typing import Any

from app.rag.schemas import RegChunk


class CrossEncoderReranker:
    """Optional reranker for candidate regulatory passages."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base", enabled: bool = True):
        self.model_name = model_name
        self.enabled = enabled
        self._reranker_model: Any = None

        try:
            from sentence_transformers import CrossEncoder
            self._reranker_model = CrossEncoder(model_name)
        except Exception:
            self._reranker_model = None

    def rerank(
        self,
        query: str,
        candidates: list[tuple[RegChunk, float]],
        top_k: int = 5,
    ) -> list[tuple[RegChunk, float]]:
        """Rerank candidates using cross-encoder scores or return original ranking."""
        if not candidates or not self.enabled or self._reranker_model is None:
            return candidates[:top_k]

        pairs = [[query, chunk.text] for chunk, _ in candidates]
        try:
            scores = self._reranker_model.predict(pairs)
            scored = list(zip([c for c, _ in candidates], [float(s) for s in scores], strict=True))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]
        except Exception:
            return candidates[:top_k]
