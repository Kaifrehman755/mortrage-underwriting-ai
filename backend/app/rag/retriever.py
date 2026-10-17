"""Guideline retriever and EvidenceItem builder.

Implements Playbook Section 1, 3b, 8, and Prompt P3:
- Hybrid retrieval with reciprocal rank fusion.
- Score thresholding: returns empty list rather than closest guess when score < threshold.
- Emits validated EvidenceItem objects with verbatim snippets and source citations.
- Invariant 3: Enables strict rejection of evidence-less compliance flags.
- Invariant 8: State isolation enforced.
"""

import logging
from datetime import UTC, datetime

from app.rag.embeddings import EmbeddingService
from app.rag.reranker import CrossEncoderReranker
from app.rag.schemas import EvidenceItem
from app.rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class GuidelineRetriever:
    """Retrieves authoritative regulatory evidence and constructs EvidenceItem objects."""

    def __init__(
        self,
        vector_store: VectorStoreManager | None = None,
        embedding_service: EmbeddingService | None = None,
        reranker: CrossEncoderReranker | None = None,
        default_threshold: float = 0.35,
    ):
        self.vector_store = vector_store or VectorStoreManager()
        self.embedding_service = embedding_service or EmbeddingService()
        self.reranker = reranker or CrossEncoderReranker(enabled=False)
        self.default_threshold = default_threshold

    def retrieve(
        self,
        query: str,
        state_code: str | None = None,
        loan_date: str | None = None,
        top_k: int = 5,
        threshold: float | None = None,
    ) -> list[EvidenceItem]:
        """Execute hybrid retrieval for regulatory evidence.

        Args:
            query: The natural language regulatory check query or citation.
            state_code: Two-letter state code of subject property (e.g., 'UP').
            loan_date: Reference loan origination date (ISO format).
            top_k: Maximum number of evidence items to return.
            threshold: Minimum score threshold below which empty list is returned.

        Returns:
            List of validated EvidenceItem objects.
        """
        thresh = threshold if threshold is not None else self.default_threshold

        # 1. Embed query
        q_vec = self.embedding_service.embed_text(query)

        # 2. Hybrid search (vector cosine + tsvector keyword + RRF)
        candidates = self.vector_store.hybrid_search(
            query_text=query,
            query_vector=q_vec,
            state_code=state_code,
            loan_date=loan_date,
            top_k=top_k * 2,
        )

        if not candidates:
            return []

        # 3. Optional reranker
        reranked = self.reranker.rerank(query, candidates, top_k=top_k)

        # 4. Strict threshold filter (Playbook Prompt P3)
        # If the best score is below the configured threshold, return empty list
        best_score = reranked[0][1] if reranked else 0.0
        if best_score < thresh:
            logger.info(
                f"Query '{query[:40]}' best score ({best_score:.3f}) below threshold ({thresh}). "
                "Returning empty evidence list (abstain rather than guess)."
            )
            return []

        # 5. Build EvidenceItem objects
        evidence_items: list[EvidenceItem] = []
        for chunk, score in reranked:
            if score < thresh:
                continue

            item = EvidenceItem(
                retrieval_ref=chunk.chunk_id,
                source_name=chunk.source_name,
                authority=chunk.authority,
                version_or_date="2026-10-01",
                section_or_page=chunk.section_ref,
                scope=chunk.scope,
                state_code=chunk.state_code,
                snippet=chunk.text,  # Verbatim quoted text
                score=round(score, 4),
                retrieved_at=datetime.now(UTC).isoformat(),
                index_version=chunk.index_version,
            )
            evidence_items.append(item)

        return evidence_items[:top_k]
