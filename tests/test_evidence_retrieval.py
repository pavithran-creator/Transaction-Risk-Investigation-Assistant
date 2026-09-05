"""
Comprehensive Unit & Integration Tests for Phase 9 Grounded Evidence Retrieval.

Tests:
1. Evidence document generation from transaction, baseline, rule, and attention data.
2. LocalEvidenceIndex numpy matrix operations and cosine similarity search.
3. Top-K filtering.
4. Traceability metadata preservation (transaction_ids, rule_ids, customer_id).
5. Safe behavior on empty index.
6. Graceful handling when Gemini embedding API key is missing or fails.
7. No hallucinated content in generated evidence documents.
"""

from unittest.mock import patch
import pytest
from src.ai.evidence_index import LocalEvidenceIndex
from src.ai.evidence_retrieval import EvidenceRetrievalService
from src.analytics.evidence_generator import generate_all_evidence
from src.models.evidence import EvidenceDocument, RetrievedEvidenceItem
from src.models.transaction import Transaction, TransactionDataset


@pytest.fixture
def sample_dataset():
    txs = [
        Transaction(
            transaction_id="TXN_101",
            customer_id="CUST_999",
            timestamp="2026-03-01T10:00:00Z",
            description="Salary credit",
            amount=50000.0,
            channel="NEFT",
            payee="Employer Corp"
        ),
        Transaction(
            transaction_id="TXN_102",
            customer_id="CUST_999",
            timestamp="2026-03-02T02:15:00Z",  # Off-hours (R03) & High amount (R01)
            description="Transfer 1",
            amount=150000.0,
            channel="UPI",
            payee="Merchant Hospital"
        ),
    ]
    return TransactionDataset(transactions=txs)


# --- 1. Evidence Document Creation Tests ---

def test_generate_all_evidence_preserves_traceability(sample_dataset):
    docs = generate_all_evidence(sample_dataset)
    assert len(docs) >= 3  # At least 2 transaction docs + 1 baseline doc + 1 attention doc

    tx_docs = [d for d in docs if d.source_type == "transaction"]
    assert len(tx_docs) == 2

    # Check TXN_101 document content & metadata
    tx101_doc = next(d for d in tx_docs if d.source_id == "TXN_101")
    assert tx101_doc.customer_id == "CUST_999"
    assert tx101_doc.transaction_ids == ["TXN_101"]
    assert "Salary credit" in tx101_doc.content
    assert "Employer Corp" in tx101_doc.content
    assert "50,000.00" in tx101_doc.content


def test_evidence_documents_have_no_hallucinations(sample_dataset):
    docs = generate_all_evidence(sample_dataset)
    for doc in docs:
        # Verify customer_id matches input
        assert doc.customer_id == "CUST_999"
        # Verify no suspicious/fraud terms invented in source evidence
        assert "fraud network" not in doc.content.lower()
        assert "criminal" not in doc.content.lower()


# --- 2. Local Index & Cosine Similarity Tests ---

def test_local_evidence_index_add_and_search():
    index = LocalEvidenceIndex()
    doc1 = EvidenceDocument(
        evidence_id="EVD_1",
        source_type="transaction",
        source_id="TXN_1",
        customer_id="CUST_1",
        transaction_ids=["TXN_1"],
        rule_ids=[],
        title="Doc 1",
        content="First document content",
    )
    doc2 = EvidenceDocument(
        evidence_id="EVD_2",
        source_type="transaction",
        source_id="TXN_2",
        customer_id="CUST_1",
        transaction_ids=["TXN_2"],
        rule_ids=[],
        title="Doc 2",
        content="Second document content",
    )

    # Vector 1 is aligned with query [1.0, 0.0], Vector 2 is orthogonal [0.0, 1.0]
    emb1 = [1.0, 0.0]
    emb2 = [0.0, 1.0]

    added = index.add_documents([doc1, doc2], [emb1, emb2])
    assert added == 2
    assert index.count == 2

    # Query vector close to emb1
    query_emb = [1.0, 0.0]
    results = index.search(query_emb, top_k=2)

    assert len(results) == 2
    assert results[0].evidence_document.evidence_id == "EVD_1"
    assert results[0].similarity == 1.0
    assert "[EVD_1]" in results[0].citation


def test_local_evidence_index_top_k_filtering():
    index = LocalEvidenceIndex()
    docs = [
        EvidenceDocument(
            evidence_id=f"EVD_{i}",
            source_type="transaction",
            source_id=f"TXN_{i}",
            customer_id="CUST_1",
            transaction_ids=[f"TXN_{i}"],
            rule_ids=[],
            title=f"Doc {i}",
            content=f"Content {i}"
        )
        for i in range(10)
    ]
    embs = [[1.0, float(i)] for i in range(10)]

    index.add_documents(docs, embs)
    
    # Request top_k = 3
    results = index.search([1.0, 0.0], top_k=3)
    assert len(results) == 3


def test_empty_index_search():
    index = LocalEvidenceIndex()
    results = index.search([1.0, 0.0], top_k=5)
    assert results == []


# --- 3. Embedding Failure & Service Integration Tests ---

def test_retrieval_service_missing_api_key(sample_dataset, monkeypatch):
    """When GEMINI_API_KEY is not set, service returns clear error without crashing."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    service = EvidenceRetrievalService()
    indexed_count = service.index_dataset(sample_dataset)
    assert indexed_count == 0  # 0 indexed due to missing key

    res = service.search_evidence("high value transfer")
    assert res["retrieved_count"] == 0
    assert "error" in res


@patch("src.ai.evidence_retrieval.get_batch_embeddings")
@patch("src.ai.evidence_retrieval.get_text_embedding")
def test_retrieval_service_mocked_embeddings(mock_get_text_emb, mock_get_batch_embs, sample_dataset):
    """With mocked embeddings, verify full indexing and retrieval flow."""
    # Mock batch embeddings (e.g. 4 documents)
    mock_get_batch_embs.return_value = [
        [0.1, 0.9],
        [0.8, 0.2],
        [0.5, 0.5],
        [0.3, 0.7],
    ]
    mock_get_text_emb.return_value = [0.85, 0.15]  # Similar to doc 2 ([0.8, 0.2])

    service = EvidenceRetrievalService()
    indexed_count = service.index_dataset(sample_dataset)
    assert indexed_count >= 3

    res = service.search_evidence("high value transfer", top_k=2)
    assert res["retrieved_count"] == 2
    assert len(res["results"]) == 2

    top_item = res["results"][0]
    assert "evidence_document" in top_item
    assert "citation" in top_item
    assert "similarity" in top_item
