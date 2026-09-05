"""
Unit tests for src/reports/report_builder.py (Milestone 2).
"""

import pytest
from src.reports.report_builder import build_deterministic_report
from src.models.transaction import Transaction, TransactionDataset


@pytest.fixture
def clean_dataset():
    txs = [
        Transaction(
            transaction_id="TX001",
            customer_id="CUST001",
            timestamp="2026-03-01T10:00:00Z",
            description="Regular grocery",
            amount=500.0,
            channel="UPI",
            payee="Store A"
        ),
        Transaction(
            transaction_id="TX002",
            customer_id="CUST001",
            timestamp="2026-03-01T12:00:00Z",
            description="Lunch payment",
            amount=500.0,
            channel="UPI",
            payee="Store B"
        ),
    ]
    return TransactionDataset(transactions=txs)


@pytest.fixture
def high_amount_dataset():
    txs = [
        Transaction(
            transaction_id="TX001",
            customer_id="CUST001",
            timestamp="2026-03-01T10:00:00Z",
            description="Coffee",
            amount=100.0,
            channel="UPI",
            payee="Cafe"
        ),
        Transaction(
            transaction_id="TX002",
            customer_id="CUST001",
            timestamp="2026-03-01T11:00:00Z",
            description="Tea",
            amount=150.0,
            channel="UPI",
            payee="Cafe"
        ),
        Transaction(
            transaction_id="TX003",
            customer_id="CUST001",
            timestamp="2026-03-02T10:00:00Z",
            description="High transfer",
            amount=250000.0,  # Triggers R01
            channel="NEFT",
            payee="City Hospital"
        ),
    ]
    return TransactionDataset(transactions=txs)


def test_build_report_none_dataset():
    report = build_deterministic_report(None)
    assert report.attention_level == "INSUFFICIENT_EVIDENCE"
    assert report.first_finding == "Insufficient Evidence"
    assert "insufficient for a reliable assessment" in report.assessment
    assert report.valid is False


def test_build_report_no_immediate_concern(clean_dataset):
    report = build_deterministic_report(clean_dataset)
    assert report.customer_id == "CUST001"
    assert report.attention_level == "NO_IMMEDIATE_CONCERN"
    assert report.first_finding == "No Immediate Concern"
    assert "No configured deterministic risk indicator was triggered" in report.assessment
    assert len(report.triggered_rules) == 0
    assert len(report.non_triggered_rules) == 4
    assert report.valid is True
    assert "fraud" not in report.assessment.lower() or "not establish" in report.safety_statement.lower()


def test_build_report_triggered_rule(high_amount_dataset):
    report = build_deterministic_report(high_amount_dataset)
    assert report.customer_id == "CUST001"
    assert report.attention_level in ["CONTEXTUAL_REVIEW", "ATTENTION_RECOMMENDED", "HIGH_ATTENTION"]
    assert report.first_finding == report.attention_label
    assert len(report.triggered_rules) >= 1
    assert any(tr["rule_id"] == "R01" for tr in report.triggered_rules)
    assert len(report.transactions_requiring_review) >= 1
    
    tx_review = report.transactions_requiring_review[0]
    assert tx_review.transaction_id == "TX003"
    assert tx_review.amount == 250000.0
    assert tx_review.payee == "City Hospital"
    assert "TX003" in report.source_transaction_ids
    assert "First priority" in report.investigator_priority
