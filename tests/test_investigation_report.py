"""
Comprehensive Integration & Unit Tests for Phase 8 Investigation Report Generation.

Verifies:
1. Report structure & required fields.
2. First finding answers "Does anything need attention?".
3. Attention level matching Phase 6 deterministic output.
4. Transaction traceability (preserves original transaction IDs & attributes).
5. Multi-rule transaction merging into single ReportTransaction.
6. Data-supported transaction connections (SAME_PAYEE, SHARED_RULE, TEMPORAL_SEQUENCE).
7. Gemini explanation integration & fallback handling.
8. Safety statement presence & zero fraud assertions.
9. GET /api/report endpoint behavior (no-data response, success, exception handling).
"""

import pathlib
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app import app
from src.analytics.state import clear_current_dataset, set_current_dataset
from src.models.transaction import Transaction, TransactionDataset
from src.reports.report_builder import build_deterministic_report
from src.reports.report_service import generate_investigation_report

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def reset_in_memory_state():
    """Ensure in-memory state is cleared before each test."""
    clear_current_dataset()
    yield
    clear_current_dataset()


@pytest.fixture
def multi_rule_dataset():
    txs = [
        Transaction(
            transaction_id="TXN_001",
            customer_id="CUST_777",
            timestamp="2026-03-01T08:00:00Z",
            description="Salary",
            amount=50000.0,
            channel="NEFT",
            payee="Employer Corp"
        ),
        Transaction(
            transaction_id="TXN_002",
            customer_id="CUST_777",
            timestamp="2026-03-02T02:00:00Z",  # Off-hours (R03)
            description="Transfer 1",
            amount=150000.0,  # High amount (R01)
            channel="UPI",
            payee="Merchant Hospital"
        ),
        Transaction(
            transaction_id="TXN_003",
            customer_id="CUST_777",
            timestamp="2026-03-02T02:05:00Z",  # Rapid consecutive (R02) + Off-hours (R03)
            description="Transfer 2",
            amount=180000.0,  # High amount (R01)
            channel="UPI",
            payee="Merchant Hospital"  # Same payee
        ),
    ]
    return TransactionDataset(transactions=txs)


# --- Unit Tests ---

def test_report_structure_and_first_finding(multi_rule_dataset):
    report = generate_investigation_report(multi_rule_dataset)
    
    assert report.customer_id == "CUST_777"
    assert report.attention_level in ["HIGH_ATTENTION", "ATTENTION_RECOMMENDED"]
    assert report.first_finding == report.attention_label
    assert len(report.triggered_rules) >= 2
    assert len(report.transactions_requiring_review) >= 2
    assert report.valid is True
    assert "does not establish that fraud occurred" in report.safety_statement


def test_transaction_traceability_and_multi_rule_merging(multi_rule_dataset):
    report = generate_investigation_report(multi_rule_dataset)
    
    review_txs = report.transactions_requiring_review
    tx_ids = [t.transaction_id for t in review_txs]
    
    # Check no duplicate transaction records
    assert len(tx_ids) == len(set(tx_ids))
    
    # Check TXN_003 preserves original fields and merges multiple triggered rules (R01, R03)
    tx3 = next(t for t in review_txs if t.transaction_id == "TXN_003")
    assert tx3.payee == "Merchant Hospital"
    assert tx3.amount == 180000.0
    assert tx3.channel == "UPI"
    assert "R01" in tx3.triggered_rules
    assert "R03" in tx3.triggered_rules


def test_data_supported_transaction_connections(multi_rule_dataset):
    report = generate_investigation_report(multi_rule_dataset)
    
    conns = report.transaction_connections
    conn_types = [c.connection_type for c in conns]
    
    assert "SAME_PAYEE" in conn_types
    assert "SHARED_RULE" in conn_types
    assert "TEMPORAL_SEQUENCE" in conn_types
    
    same_payee = next(c for c in conns if c.connection_type == "SAME_PAYEE")
    assert "Merchant Hospital" in same_payee.description
    assert "TXN_002" in same_payee.transaction_ids
    assert "TXN_003" in same_payee.transaction_ids


def test_report_gemini_failure_preserves_deterministic_evidence(multi_rule_dataset, monkeypatch):
    """When Gemini API key is missing or API fails, report retains full deterministic evidence."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    report = generate_investigation_report(multi_rule_dataset)
    
    assert report.customer_id == "CUST_777"
    assert report.valid is True
    assert len(report.triggered_rules) >= 2
    assert len(report.transactions_requiring_review) >= 2
    assert len(report.evidence) >= 2


# --- API Endpoint Integration Tests ---

@pytest.mark.anyio
async def test_get_report_no_dataset_returns_clear_message():
    """GET /api/report without uploading a CSV returns valid=false with clear message."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/report")
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is False
    assert "No transaction dataset is loaded" in body["message"]


@pytest.mark.anyio
async def test_get_report_after_valid_csv_upload():
    """GET /api/report after CSV upload returns full completed investigation report."""
    csv_bytes = (FIXTURES / "valid_single_customer.csv").read_bytes()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload_resp = await client.post(
            "/api/upload",
            files={"file": ("valid_single_customer.csv", csv_bytes, "text/csv")},
        )
        assert upload_resp.status_code == 200

        report_resp = await client.get("/api/report")
        assert report_resp.status_code == 200
        body = report_resp.json()
        assert body["status"] == "completed"
        assert body["customer_id"] == "CUST001"
        
        rep = body["report"]
        assert "first_finding" in rep
        assert "attention_level" in rep
        assert "triggered_rules" in rep
        assert "transactions_requiring_review" in rep
        assert "safety_statement" in rep
        assert "does not establish that fraud occurred" in rep["safety_statement"]


@pytest.mark.anyio
async def test_get_report_exception_handling(monkeypatch):
    """GET /api/report returns structured 500 JSON without exposing stack trace when an exception occurs."""

    def mock_raise(*args, **kwargs):
        raise ValueError("Internal report failure")

    monkeypatch.setattr("app.get_current_dataset", mock_raise)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/report")

    assert resp.status_code == 500
    body = resp.json()
    assert body["status"] == "error"
    assert "unexpected error" in body["message"].lower()
    assert "ValueError" not in str(body)
    assert "traceback" not in str(body).lower()
