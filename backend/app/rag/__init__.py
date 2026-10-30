"""RAG package initialization."""

from app.rag.chunking import GuidelineChunker
from app.rag.embeddings import EmbeddingModelUnavailable, EmbeddingService
from app.rag.ingestion import DocumentIngestionPipeline
from app.rag.postgres_store import PostgresVectorStore
from app.rag.raw_store import (
    LocalRawDocumentStore,
    MinioRawDocumentStore,
    RawDocumentStore,
    build_raw_document_store,
)
from app.rag.reranker import CrossEncoderReranker
from app.rag.retriever import GuidelineRetriever
from app.rag.schemas import EvidenceItem, RegChunk, RegDocument, RetrievalQuery
from app.rag.seed_corpus import load_seed_corpus
from app.rag.vector_store import VectorStoreManager

__all__ = [
    "DocumentIngestionPipeline",
    "GuidelineChunker",
    "EmbeddingService",
    "EmbeddingModelUnavailable",
    "VectorStoreManager",
    "PostgresVectorStore",
    "RawDocumentStore",
    "LocalRawDocumentStore",
    "MinioRawDocumentStore",
    "build_raw_document_store",
    "GuidelineRetriever",
    "CrossEncoderReranker",
    "RegDocument",
    "RegChunk",
    "EvidenceItem",
    "RetrievalQuery",
    "load_seed_corpus",
]
