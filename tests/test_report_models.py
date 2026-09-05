"""
Unit tests for src/models/report.py (Milestone 1).
"""

from datetime import datetime, timezone
import pytest
from src.models.report import (
    DEFAULT_REPORT_SAFETY_STATEMENT,
    InvestigationReport,
    ReportEvidence,
    ReportTransaction,
    TransactionConnection,
)


def test_report_transaction_model():
    tx = ReportTransaction(
        transaction_id="TXN001",
        timestamp="2026-06-10T01:45:00Z",
        description="Payment",
        payee="City Hospital",
        amount=250000.0,
        channel="BANK_TRANSFER",
        triggered_rules=["R01", "R03"]
    )
    assert tx.transaction_id == "TXN001"
    assert tx.amount == 250000.0
    assert tx.triggered_rules == ["R01", "R03"]


def test_report_evidence_model():
    ev = ReportEvidence(
        rule_id="R01",
        rule_name="Unusually Large Transfer",
        transaction_id="TXN001",
        description="TXN001 amount INR 250,000 exceeds P95 of 42,000.",
        baseline_comparison={"p95": 42000.0, "amount": 250000.0}
    )
    assert ev.rule_id == "R01"
    assert ev.transaction_id == "TXN001"
    assert ev.baseline_comparison["p95"] == 42000.0


def test_transaction_connection_model():
    conn = TransactionConnection(
        connection_type="SAME_PAYEE",
        description="Transactions TXN001 and TXN002 share payee: City Hospital.",
        transaction_ids=["TXN001", "TXN002"]
    )
    assert conn.connection_type == "SAME_PAYEE"
    assert len(conn.transaction_ids) == 2


def test_investigation_report_instantiation():
    now_str = datetime.now(timezone.utc).isoformat()
    report = InvestigationReport(
        customer_id="CUST001",
        generated_at=now_str,
        attention_level="ATTENTION_RECOMMENDED",
        attention_label="Attention Recommended",
        first_finding="Attention Recommended",
        assessment="Customer exhibited multiple risk rule triggers.",
        triggered_rules=[{"rule_id": "R01", "name": "Unusually Large Transfer"}],
        non_triggered_rules=[{"rule_id": "R02", "name": "Rapid Consecutive Transactions"}],
        transactions_requiring_review=[
            ReportTransaction(
                transaction_id="TXN001",
                timestamp="2026-06-10T01:45:00Z",
                description="Payment",
                payee="City Hospital",
                amount=250000.0,
                channel="BANK_TRANSFER",
                triggered_rules=["R01"]
            )
        ],
        transaction_connections=[
            TransactionConnection(
                connection_type="SAME_PAYEE",
                description="Transaction to City Hospital.",
                transaction_ids=["TXN001"]
            )
        ],
        evidence=[
            ReportEvidence(
                rule_id="R01",
                rule_name="Unusually Large Transfer",
                transaction_id="TXN001",
                description="Exceeds P95"
            )
        ],
        baseline_deviation=["Amount exceeds customer P95 baseline."],
        why_attention="Combines large transfer with new payee.",
        context_reducing_concern="Customer account active for 3 years.",
        investigator_priority="First priority: Review TXN001 and verify purpose of INR 250,000 transfer.",
        suggested_checks=["Verify transaction purpose", "Confirm customer relationship with payee"],
        source_transaction_ids=["TXN001"],
        valid=True
    )

    assert report.customer_id == "CUST001"
    assert report.first_finding == "Attention Recommended"
    assert report.safety_statement == DEFAULT_REPORT_SAFETY_STATEMENT
    assert "does not establish that fraud occurred" in report.safety_statement
    assert report.valid is True

    dumped = report.model_dump()
    assert dumped["customer_id"] == "CUST001"
    assert dumped["attention_level"] == "ATTENTION_RECOMMENDED"
