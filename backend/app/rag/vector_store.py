"""Hybrid vector and keyword search storage manager.

Implements Playbook Section 4 (reg_chunk HNSW & tsvector), Section 15.4 (State isolation),
and Prompt P3 (Reciprocal rank fusion hybrid retrieval).
"""

import math
import re
from datetime import date

import numpy as np

from app.rag.schemas import RegChunk


class VectorStoreManager:
    """Manages regulatory chunks with hybrid vector cosine and tsvector keyword retrieval."""

    def __init__(self):
        self.chunks: dict[str, RegChunk] = {}
        # Document hash registry to ensure idempotent ingestion
        self.ingested_doc_hashes: set[str] = set()

    def upsert_chunks(self, chunks: list[RegChunk], doc_sha256: str | None = None) -> int:
        """Idempotently insert or update regulatory chunks."""
        count = 0
        for c in chunks:
            self.chunks[c.chunk_id] = c
            count += 1
        if doc_sha256:
            self.ingested_doc_hashes.add(doc_sha256)
        return count

    def is_doc_ingested(self, sha256: str) -> bool:
        """Check if document SHA-256 has already been ingested."""
        return sha256 in self.ingested_doc_hashes

    def hybrid_search(
        self,
        query_text: str,
        query_vector: list[float],
        state_code: str | None = None,
        loan_date: str | None = None,
        top_k: int = 5,
        dense_candidates: int = 30,
        keyword_candidates: int = 30,
        rrf_k: int = 60,
        require_approved: bool = True,
    ) -> list[tuple[RegChunk, float]]:
        """Execute hybrid search combining vector cosine ranking and keyword ranking via RRF.

        Enforces:
        - Invariant 8: State isolation (national chunks OR subject's own state_code only).
        - Date validity: effective_from <= loan_date <= effective_to.
        """
        # 1. Filter candidates by approval, state isolation and effective date.
        # The current date is only a fallback for direct callers; compliance runs
        # always pass the loan date explicitly.
        filtered_chunks: list[RegChunk] = []
        target_date = date.fromisoformat(loan_date[:10]) if loan_date else date.today()

        for chunk in self.chunks.values():
            if require_approved and not chunk.approved:
                continue

            # State isolation check
            if chunk.scope == "state":
                if state_code is None or chunk.state_code != state_code.upper():
                    continue

            # Effective date check
            eff_from = date.fromisoformat(chunk.effective_from[:10])
            eff_to = date.fromisoformat(chunk.effective_to[:10])
            if not (eff_from <= target_date <= eff_to):
                continue

            filtered_chunks.append(chunk)

        if not filtered_chunks:
            return []

        # 2. Vector Cosine Ranking (pgvector simulation)
        q_vec = np.array(query_vector)
        q_norm = np.linalg.norm(q_vec)
        if q_norm > 0:
            q_vec = q_vec / q_norm

        vector_scores: list[tuple[RegChunk, float]] = []
        for c in filtered_chunks:
            if not c.embedding:
                continue
            c_vec = np.array(c.embedding)
            c_norm = np.linalg.norm(c_vec)
            if c_norm > 0:
                c_vec = c_vec / c_norm
            cosine_sim = float(np.dot(q_vec, c_vec))
            vector_scores.append((c, cosine_sim))

        vector_scores.sort(key=lambda x: x[1], reverse=True)
        # Only retain vector candidates with meaningful similarity
        top_vector = [item for item in vector_scores[:dense_candidates] if item[1] >= 0.20]

        # 3. Keyword / BM25 / tsvector ranking
        query_terms = set(re.findall(r"\b[a-z0-9_\-\.]{2,}\b", query_text.lower()))
        keyword_scores: list[tuple[RegChunk, float]] = []

        for c in filtered_chunks:
            text_lower = c.text.lower()
            section_lower = c.section_ref.lower()

            # Exact section match bonus (e.g. 'section 4' or 'kfs')
            match_score = 0.0
            for term in query_terms:
                term_count = text_lower.count(term)
                if term_count > 0:
                    match_score += 1.0 + math.log(term_count)
                if term in section_lower:
                    match_score += 3.0  # Section heading match boost

            if match_score > 0:
                keyword_scores.append((c, match_score))

        keyword_scores.sort(key=lambda x: x[1], reverse=True)
        top_keyword = keyword_scores[:keyword_candidates]

        # If zero keyword matches and max vector similarity is weak, abort search (abstain)
        max_cosine = top_vector[0][1] if top_vector else 0.0
        if not top_keyword and max_cosine < 0.35:
            return []

        # 4. Reciprocal Rank Fusion (RRF)
        # RRF_score(d) = sum(1.0 / (rrf_k + rank))
        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, RegChunk] = {}

        for rank, (c, _) in enumerate(top_vector):
            chunk_map[c.chunk_id] = c
            rrf_scores[c.chunk_id] = rrf_scores.get(c.chunk_id, 0.0) + (1.0 / (rrf_k + (rank + 1)))

        for rank, (c, _) in enumerate(top_keyword):
            chunk_map[c.chunk_id] = c
            rrf_scores[c.chunk_id] = rrf_scores.get(c.chunk_id, 0.0) + (1.0 / (rrf_k + (rank + 1)))

        # Normalize RRF scores to 0.0 - 1.0 range
        max_possible_rrf = (1.0 / (rrf_k + 1)) * 2.0
        final_ranked: list[tuple[RegChunk, float]] = []

        kw_chunk_ids = {c.chunk_id for c, _ in top_keyword}
        for chunk_id, raw_rrf in rrf_scores.items():
            # If no keyword overlap at all, dampen score
            dampener = 1.0 if chunk_id in kw_chunk_ids else 0.60
            norm_score = round(min(1.0, (raw_rrf / max_possible_rrf) * dampener), 4)
            final_ranked.append((chunk_map[chunk_id], norm_score))

        final_ranked.sort(key=lambda x: x[1], reverse=True)
        return final_ranked[:top_k]
