"""Regulatory document ingestion pipeline.

Implements Playbook Section 3b, 4, 14.1, and Prompt P2:
- Idempotent ingestion based on document SHA-256.
- Section-level chunking preserving statutory headings.
- Batch embedding and indexing into VectorStoreManager.
- Built-in corpus loader for official Indian regulatory frameworks.
"""

import hashlib
import logging
from pathlib import Path
from typing import Any

import yaml

from app.rag.chunking import GuidelineChunker
from app.rag.embeddings import EmbeddingService
from app.rag.schemas import RegChunk, RegDocument
from app.rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Orchestrates document fetching, SHA-256 hashing, chunking, embedding, and indexing."""

    def __init__(
        self,
        vector_store: VectorStoreManager | None = None,
        chunker: GuidelineChunker | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        self.vector_store = vector_store or VectorStoreManager()
        self.chunker = chunker or GuidelineChunker()
        self.embedding_service = embedding_service or EmbeddingService()

    def ingest_document_text(
        self,
        doc_metadata: RegDocument,
        raw_text: str,
    ) -> list[RegChunk]:
        """Ingest document text idempotently into the vector store.

        If the document SHA-256 has already been ingested, returns existing chunks without duplication.
        """
        # 1. Compute SHA-256 hash of text
        computed_sha = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        doc_metadata.sha256 = computed_sha

        # 2. Idempotency check
        if self.vector_store.is_doc_ingested(computed_sha):
            logger.info(f"Document '{doc_metadata.source_name}' (SHA {computed_sha[:8]}) already ingested. Skipping.")
            return [c for c in self.vector_store.chunks.values() if c.doc_id == doc_metadata.doc_id]

        # 3. Section chunking
        chunks = self.chunker.chunk_document(doc_metadata, raw_text)
        if not chunks:
            logger.warning(f"No chunks generated for document '{doc_metadata.source_name}'.")
            return []

        # 4. Batch compute embeddings
        texts = [c.text for c in chunks]
        embeddings = self.embedding_service.embed_batch(texts)
        for chunk, emb in zip(chunks, embeddings, strict=True):
            chunk.embedding = emb

        # 5. Upsert into vector store
        self.vector_store.upsert_chunks(chunks, doc_sha256=computed_sha)
        logger.info(f"Ingested {len(chunks)} chunks for '{doc_metadata.source_name}'.")
        return chunks

    def load_sources_registry(self, yaml_path: Path | str) -> list[dict[str, Any]]:
        """Load registered document specifications from sources.yaml."""
        p = Path(yaml_path)
        if not p.exists():
            raise FileNotFoundError(f"Source registry '{yaml_path}' not found.")
        with open(p, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return list(data.get("documents", []))
