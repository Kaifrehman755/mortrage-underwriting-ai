"""Postgres/pgvector persistence for approved regulatory evidence.

This is the database-backed counterpart to :class:`app.rag.vector_store.VectorStoreManager`.
It implements the playbook's evidence store requirements:

* document chunks live in ``reg_chunk`` with a 384-dimension pgvector embedding;
* keyword search uses the generated ``tsv`` column;
* approval, state isolation, effective dates, and index version are enforced in
  the SQL filters, not only in Python;
* ingestion is idempotent by document SHA-256.

The in-memory store remains for unit tests and synthetic fixtures. Production
retrieval must use this store so a chunk can be traced back to a hashed document
and an active index version.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import and_, func, literal, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.regulatory import RegChunk as RegChunkModel
from app.database.models.regulatory import RegDocument as RegDocumentModel
from app.rag.schemas import RegChunk, RegDocument

EMBEDDING_DIMENSION = 384


class PostgresVectorStore:
    """Persist and retrieve regulatory chunks from PostgreSQL + pgvector."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def is_doc_ingested(self, sha256: str) -> bool:
        """Return whether this exact document hash is already stored."""
        existing = await self.session.scalar(
            select(RegDocumentModel.doc_id).where(RegDocumentModel.sha256 == sha256)
        )
        return existing is not None

    async def upsert_document(self, document: RegDocument) -> UUID:
        """Insert a document once, keyed by its SHA-256.

        Approval metadata is never inferred or updated here. A caller that wants
        to approve a source must use the explicit owner-approval path.
        """
        existing = await self.session.scalar(
            select(RegDocumentModel.doc_id).where(
                RegDocumentModel.sha256 == document.sha256
            )
        )
        if existing is not None:
            return existing

        doc_id = UUID(document.doc_id)
        entity = RegDocumentModel(
            doc_id=doc_id,
            source_name=document.source_name,
            authority=document.authority,
            category=document.category,
            version_or_date=document.version_or_date,
            url=document.url,
            sha256=document.sha256,
            retrieved_at=_parse_datetime(document.retrieved_at) or datetime.now(UTC),
            approved=document.approved,
            approved_by=document.approved_by,
            approved_at=_parse_datetime(document.approved_at),
            review_due=_parse_date(document.review_due),
            terms_snapshot_sha256=document.terms_snapshot_sha256,
            license_scope=document.license_scope,
            scope=document.scope,
            state_code=document.state_code.upper() if document.state_code else None,
            effective_from=_parse_date(document.effective_from),
            effective_to=_parse_date(document.effective_to),
            metadata_json=None,
        )
        self.session.add(entity)
        await self.session.flush()
        return doc_id

    async def upsert_chunks(
        self,
        document: RegDocument,
        chunks: list[RegChunk],
    ) -> int:
        """Idempotently upsert chunks for one document.

        The ``(doc_id, section_ref, index_version)`` natural key makes a repeat
        ingestion update the existing row rather than adding duplicates.
        """
        if not chunks:
            return 0
        if not document.approved:
            raise ValueError(
                "Refusing to persist chunks for an unapproved regulatory document"
            )

        doc_id = UUID(document.doc_id)
        rows: list[dict[str, Any]] = []
        for chunk in chunks:
            if chunk.doc_id != document.doc_id:
                raise ValueError("chunk.doc_id does not match document.doc_id")
            if chunk.approved and not document.approved:
                raise ValueError("an unapproved document cannot have approved chunks")
            if len(chunk.embedding) != EMBEDDING_DIMENSION:
                raise ValueError(
                    f"embedding must have {EMBEDDING_DIMENSION} dimensions, "
                    f"got {len(chunk.embedding)}"
                )
            rows.append(
                {
                    "chunk_id": UUID(chunk.chunk_id),
                    "doc_id": doc_id,
                    "source_name": chunk.source_name,
                    "authority": chunk.authority,
                    "section_ref": chunk.section_ref,
                    "page_ref": chunk.page_ref,
                    "text": chunk.text,
                    "embedding": chunk.embedding,
                    "scope": chunk.scope,
                    "state_code": chunk.state_code.upper()
                    if chunk.state_code
                    else None,
                    "effective_from": _parse_date(chunk.effective_from),
                    "effective_to": _parse_date(chunk.effective_to),
                    "version_or_date": chunk.version_or_date,
                    "approved": chunk.approved,
                    "license_scope": chunk.license_scope,
                    "index_version": chunk.index_version,
                }
            )

        statement = (
            pg_insert(RegChunkModel)
            .values(rows)
            .on_conflict_do_update(
                constraint="uq_reg_chunk_doc_section_version",
                set_={
                    "source_name": pg_insert(RegChunkModel).excluded.source_name,
                    "authority": pg_insert(RegChunkModel).excluded.authority,
                    "page_ref": pg_insert(RegChunkModel).excluded.page_ref,
                    "text": pg_insert(RegChunkModel).excluded.text,
                    "embedding": pg_insert(RegChunkModel).excluded.embedding,
                    "scope": pg_insert(RegChunkModel).excluded.scope,
                    "state_code": pg_insert(RegChunkModel).excluded.state_code,
                    "effective_from": pg_insert(RegChunkModel).excluded.effective_from,
                    "effective_to": pg_insert(RegChunkModel).excluded.effective_to,
                    "version_or_date": pg_insert(RegChunkModel).excluded.version_or_date,
                    "approved": pg_insert(RegChunkModel).excluded.approved,
                    "license_scope": pg_insert(RegChunkModel).excluded.license_scope,
                },
            )
        )
        await self.session.execute(statement)
        await self.session.flush()
        return len(rows)

    async def ingest_document(
        self,
        document: RegDocument,
        chunks: list[RegChunk],
    ) -> int:
        """Persist a document and its chunks in one transaction boundary."""
        await self.upsert_document(document)
        return await self.upsert_chunks(document, chunks)

    async def hybrid_search(
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
        index_version: str | None = None,
    ) -> list[tuple[RegChunk, float]]:
        """Run pgvector + tsvector retrieval and fuse rankings with RRF."""
        if len(query_vector) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"query_vector must have {EMBEDDING_DIMENSION} dimensions, "
                f"got {len(query_vector)}"
            )

        target_date = (
            date.fromisoformat(loan_date[:10]) if loan_date else date.today()
        )
        filters = self._base_filters(
            state_code=state_code,
            target_date=target_date,
            require_approved=require_approved,
            index_version=index_version,
        )

        # Bind the query as a real vector. Without an explicit type asyncpg
        # receives a Python list and the ``<=>`` operator cannot resolve it.
        query_literal = literal(query_vector, type_=Vector(EMBEDDING_DIMENSION))
        distance = RegChunkModel.embedding.cosine_distance(query_literal)
        dense_statement = (
            select(RegChunkModel, distance.label("distance"))
            .join(RegDocumentModel, RegDocumentModel.doc_id == RegChunkModel.doc_id)
            .where(*filters)
            .order_by(distance)
            .limit(dense_candidates)
        )
        dense_rows = (await self.session.execute(dense_statement)).all()

        tsquery = func.plainto_tsquery("english", query_text)
        keyword_rank = func.ts_rank_cd(RegChunkModel.tsv, tsquery)
        keyword_statement = (
            select(RegChunkModel, keyword_rank.label("rank"))
            .join(RegDocumentModel, RegDocumentModel.doc_id == RegChunkModel.doc_id)
            .where(*filters, RegChunkModel.tsv.op("@@")(tsquery))
            .order_by(keyword_rank.desc())
            .limit(keyword_candidates)
        )
        keyword_rows = (await self.session.execute(keyword_statement)).all()

        dense_candidates_list = [
            (row[0], max(0.0, 1.0 - float(row[1]))) for row in dense_rows
        ]
        dense_candidates_list = [
            (chunk, score) for chunk, score in dense_candidates_list if score >= 0.20
        ]
        keyword_candidates_list = [
            (row[0], float(row[1])) for row in keyword_rows if float(row[1]) > 0
        ]

        max_cosine = dense_candidates_list[0][1] if dense_candidates_list else 0.0
        if not keyword_candidates_list and max_cosine < 0.35:
            return []

        rrf_scores: dict[str, float] = {}
        chunk_map: dict[str, RegChunk] = {}

        for rank, (chunk_model, _score) in enumerate(dense_candidates_list):
            chunk = _to_reg_chunk(chunk_model)
            chunk_map[chunk.chunk_id] = chunk
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (
                1.0 / (rrf_k + rank + 1)
            )

        keyword_ids: set[str] = set()
        for rank, (chunk_model, _score) in enumerate(keyword_candidates_list):
            chunk = _to_reg_chunk(chunk_model)
            chunk_map[chunk.chunk_id] = chunk
            keyword_ids.add(chunk.chunk_id)
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (
                1.0 / (rrf_k + rank + 1)
            )

        max_possible_rrf = (1.0 / (rrf_k + 1)) * 2.0
        fused: list[tuple[RegChunk, float]] = []
        for chunk_id, raw_rrf in rrf_scores.items():
            dampener = 1.0 if chunk_id in keyword_ids else 0.60
            score = round(min(1.0, (raw_rrf / max_possible_rrf) * dampener), 4)
            fused.append((chunk_map[chunk_id], score))

        fused.sort(key=lambda item: item[1], reverse=True)
        return fused[:top_k]

    @staticmethod
    def _base_filters(
        *,
        state_code: str | None,
        target_date: date,
        require_approved: bool,
        index_version: str | None,
    ) -> list[Any]:
        filters: list[Any] = [
            or_(
                RegChunkModel.effective_from.is_(None),
                RegChunkModel.effective_from <= target_date,
            ),
            or_(
                RegChunkModel.effective_to.is_(None),
                RegChunkModel.effective_to >= target_date,
            ),
        ]
        if require_approved:
            filters.extend(
                [
                    RegDocumentModel.approved.is_(True),
                    RegChunkModel.approved.is_(True),
                ]
            )
        if state_code:
            state = state_code.upper()
            filters.append(
                or_(
                    RegChunkModel.scope == "national",
                    and_(
                        RegChunkModel.scope == "state",
                        func.upper(RegChunkModel.state_code) == state,
                    ),
                )
            )
        else:
            filters.append(RegChunkModel.scope == "national")
        if index_version:
            filters.append(RegChunkModel.index_version == index_version)
        return filters


def chunk_sha256(text: str) -> str:
    """Hash chunk text for local change detection or test fixtures."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _parse_date(value: str | date | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _parse_datetime(value: str | datetime | None) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    parsed = datetime.fromisoformat(str(value))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _to_reg_chunk(model: RegChunkModel) -> RegChunk:
    return RegChunk(
        chunk_id=str(model.chunk_id),
        doc_id=str(model.doc_id),
        source_name=model.source_name,
        authority=model.authority,
        section_ref=model.section_ref or "unreferenced",
        page_ref=model.page_ref,
        text=model.text,
        embedding=list(model.embedding),
        scope=model.scope,  # type: ignore[arg-type]
        state_code=model.state_code,
        effective_from=str(model.effective_from or date(2000, 1, 1)),
        effective_to=str(model.effective_to or date(2099, 12, 31)),
        version_or_date=model.version_or_date,
        approved=model.approved,
        license_scope=model.license_scope,
        index_version=model.index_version,
    )
