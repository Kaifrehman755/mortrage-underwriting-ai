"""20-Question Gold Evaluation Set and Invariant Acceptance Tests for RAG Retrieval.

Implements Playbook Section 6, 10, and Prompt P3:
- 20 authoritative regulatory questions mapped to expected section_refs.
- Measures Hit@5 (must exceed 85% / 17 of 20 questions).
- Invariant 3: Empty results returned on out-of-scope query (never a guess).
- Invariant 8: State isolation - UP case never receives MH evidence.
- Idempotency: Re-running ingestion adds no duplicate chunks.
"""

import pytest

from app.rag.chunking import GuidelineChunker
from app.rag.embeddings import EmbeddingService
from app.rag.ingestion import DocumentIngestionPipeline
from app.rag.retriever import GuidelineRetriever
from app.rag.schemas import EvidenceItem, RegDocument
from app.rag.seed_corpus import load_seed_corpus
from app.rag.vector_store import VectorStoreManager


@pytest.fixture(scope="module")
def rag_system():
    """Initialize vector store and ingest authoritative regulatory corpus."""
    v_store = VectorStoreManager()
    chunker = GuidelineChunker()
    emb_service = EmbeddingService()
    pipeline = DocumentIngestionPipeline(vector_store=v_store, chunker=chunker, embedding_service=emb_service)

    total_chunks = load_seed_corpus(pipeline)
    assert total_chunks >= 12

    retriever = GuidelineRetriever(
        vector_store=v_store,
        embedding_service=emb_service,
        default_threshold=0.30,
    )
    return {
        "pipeline": pipeline,
        "store": v_store,
        "retriever": retriever,
        "total_chunks": total_chunks,
    }


# The 20-Question Gold Evaluation Benchmark
GOLD_SET = [
    {
        "id": 1,
        "query": "What disclosures must be included in the Key Fact Statement KFS?",
        "expected_section": "Section 3",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 2,
        "query": "Is penal interest permitted on home loans or only penal charges?",
        "expected_section": "Section 7",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 3,
        "query": "Can penal charges be capitalised into principal loan balance?",
        "expected_section": "Section 7",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 4,
        "query": "What is the mandatory cooling-off look-up period for borrowers?",
        "expected_section": "Section 3",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 5,
        "query": "When is prior registration of a real estate project mandatory under RERA?",
        "expected_section": "Section 3",
        "authority": "Parliament of India",
    },
    {
        "id": 6,
        "query": "What percentage of funds realised must be deposited into separate escrow bank account under RERA?",
        "expected_section": "Section 4",
        "authority": "Parliament of India",
    },
    {
        "id": 7,
        "query": "What documents must be submitted to UP-RERA for project registration in Uttar Pradesh Lucknow?",
        "expected_section": "Rule 4",
        "authority": "UP-RERA",
        "state_code": "UP",
    },
    {
        "id": 8,
        "query": "What is the maximum advance payment allowed before written registered agreement for sale in UP?",
        "expected_section": "Rule 10",
        "authority": "UP-RERA",
        "state_code": "UP",
    },
    {
        "id": 9,
        "query": "How many days notice in writing must be given to borrower under SARFAESI before enforcement?",
        "expected_section": "Section 13",
        "authority": "Parliament of India",
    },
    {
        "id": 10,
        "query": "Is CERSAI registration required before exercising security enforcement rights?",
        "expected_section": "Section 26D",
        "authority": "Parliament of India",
    },
    {
        "id": 11,
        "query": "Within how many days must mortgage charges over property collateral be filed in CERSAI?",
        "expected_section": "Section 26D",
        "authority": "Parliament of India",
    },
    {
        "id": 12,
        "query": "What officially valid documents OVD are acceptable for Customer Due Diligence identity verification?",
        "expected_section": "Section 16",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 13,
        "query": "Within how many days must KYC information be uploaded to CKYCR Central KYC registry?",
        "expected_section": "Section 23",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 14,
        "query": "What is the maximum LTV ratio permitted for individual housing loans up to 30 lakh?",
        "expected_section": "Paragraph 2",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 15,
        "query": "What is the maximum LTV ratio cap for housing loans above 75 lakh?",
        "expected_section": "Paragraph 2",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 16,
        "query": "Can stamp duty and registration charges be included in property cost for LTV calculation?",
        "expected_section": "Paragraph 4",
        "authority": "Reserve Bank of India",
    },
    {
        "id": 17,
        "query": "What valuation standards and methodology must a registered valuer follow for appraisal?",
        "expected_section": "Rule 8",
        "authority": "Insolvency and Bankruptcy Board of India",
    },
    {
        "id": 18,
        "query": "Can an empanelled valuer value a collateral property in which they have a direct or indirect interest?",
        "expected_section": "Rule 8",
        "authority": "Insolvency and Bankruptcy Board of India",
    },
    {
        "id": 19,
        "query": "Must a valuation report disclose material divergence from government circle rates?",
        "expected_section": "Rule 8",
        "authority": "Insolvency and Bankruptcy Board of India",
    },
    {
        "id": 20,
        "query": "Seventy percent separate bank account to cover cost of construction and land cost RERA",
        "expected_section": "Section 4",
        "authority": "Parliament of India",
    },
]


def test_20_question_gold_set_hit_at_5(rag_system):
    """Playbook Section 6 & Prompt P3: Run gold set of 20 questions and assert Hit@5 >= 85%."""
    retriever: GuidelineRetriever = rag_system["retriever"]

    hits = 0
    results_log = []

    for item in GOLD_SET:
        state_code = item.get("state_code", "UP")
        evidence = retriever.retrieve(
            query=item["query"],
            state_code=state_code,
            top_k=5,
            threshold=0.25,
        )

        # Check if expected section appears in top 5 retrieved items
        found_sections = [e.section_or_page for e in evidence]
        is_hit = any(item["expected_section"].lower() in sec.lower() for sec in found_sections)

        if is_hit:
            hits += 1
        results_log.append({
            "id": item["id"],
            "query": item["query"],
            "expected": item["expected_section"],
            "top_retrieved": found_sections[:3],
            "hit": is_hit,
        })

    hit_rate = (hits / len(GOLD_SET)) * 100.0
    print(f"\nGold Set Hit@5: {hits}/{len(GOLD_SET)} ({hit_rate:.1f}%)")
    # Acceptance check: Hit@5 must be at least 85% (17/20)
    assert hits >= 17, f"Hit@5 ({hits}/{len(GOLD_SET)}) fell below 85% acceptance threshold."


def test_empty_result_on_out_of_scope_query(rag_system):
    """Playbook Prompt P3: Out-of-scope query must return empty list, never closest guess."""
    retriever: GuidelineRetriever = rag_system["retriever"]

    nonsense_query = "quantum electrodynamics schrodinger wave function superconductivity boson"
    evidence = retriever.retrieve(
        query=nonsense_query,
        state_code="UP",
        top_k=5,
        threshold=0.35,  # Standard threshold
    )

    assert len(evidence) == 0, "Out-of-scope query must return empty list."


def test_state_isolation_up_never_receives_mh_evidence(rag_system):
    """Invariant 8: State isolation - UP query never receives Maharashtra regulatory evidence."""
    retriever: GuidelineRetriever = rag_system["retriever"]

    # Query matching Maharashtra rules specifically
    evidence_up = retriever.retrieve(
        query="promoters disclosure percentage of completion engineer certificate",
        state_code="UP",  # UP state query
        top_k=5,
        threshold=0.20,
    )

    # Must NOT contain any MH chunks
    for e in evidence_up:
        assert e.state_code != "MH", f"Invariant 8 breach: Received MH chunk in UP case: {e.section_or_page}"


def test_ingestion_idempotency(rag_system):
    """Playbook Prompt P2: Ingesting the same document SHA-256 must not duplicate chunks."""
    pipeline: DocumentIngestionPipeline = rag_system["pipeline"]
    store: VectorStoreManager = rag_system["store"]

    doc_meta = RegDocument(
        source_name="Sample Test Act",
        authority="Test Authority",
        version_or_date="2026-01-01",
        url="http://test.gov.in",
        sha256="sample_test_doc_hash",
    )
    doc_text = """
Section 1. Short Title and Commencement.
This Act may be called the Housing Finance Testing Act, 2026.
It shall come into force at once.

Section 2. Definitions and Scope.
In this Act, unless the context otherwise requires, borrower means any individual applying for credit.
"""

    initial_count = len(store.chunks)
    assert initial_count >= 0

    # First ingestion
    chunks_1 = pipeline.ingest_document_text(doc_meta, doc_text)
    assert len(chunks_1) >= 2
    after_first_count = len(store.chunks)

    # Second ingestion of identical text
    chunks_2 = pipeline.ingest_document_text(doc_meta, doc_text)
    assert len(chunks_2) == len(chunks_1)
    after_second_count = len(store.chunks)

    # Count must NOT change
    assert after_second_count == after_first_count


def test_evidence_item_contract_completeness(rag_system):
    """Playbook Section 1: Every retrieved EvidenceItem carries complete provenance."""
    retriever: GuidelineRetriever = rag_system["retriever"]

    evidence = retriever.retrieve(
        query="Key Fact Statement Annual Percentage Rate APR cooling-off",
        state_code="UP",
        top_k=1,
    )

    assert len(evidence) == 1
    item: EvidenceItem = evidence[0]
    assert item.evidence_id is not None
    assert item.retrieval_ref is not None
    assert item.source_name == "RBI Key Fact Statement Direction 2024"
    assert item.authority == "Reserve Bank of India"
    assert "Section 3" in item.section_or_page
    assert "Annual Percentage Rate" in item.snippet
    assert 0.0 < item.score <= 1.0
    assert item.index_version == "idx_v1_2026_10"
