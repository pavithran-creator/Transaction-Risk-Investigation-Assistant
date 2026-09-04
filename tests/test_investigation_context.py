"""
Unit tests for Milestone 2 — Investigation Context Models and Builder.
"""

from datetime import datetime, timezone
import pytest
from src.analytics.investigation_context_builder import build_investigation_context
from src.models.transaction import Transaction, TransactionDataset


def test_investigation_context_empty_dataset():
    """Empty or None dataset returns structured context with INSUFFICIENT_EVIDENCE."""
    ctx = build_investigation_context(None)
    assert ctx.customer_id == "UNKNOWN"
    assert ctx.attention_level == "INSUFFICIENT_EVIDENCE"
    assert ctx.attention_label == "Insufficient Evidence"
    assert ctx.triggered_rules == []
    assert ctx.non_triggered_rules == []
    assert ctx.affected_transactions == []


def test_investigation_context_building():
    """Dataset with odd-hours transaction builds structured context correctly."""
    tx1 = Transaction(
        transaction_id="TXN001",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 1, 10, 0, tzinfo=timezone.utc),
        amount=100.0,
        currency="INR",
        payee="Merchant A",
        description="Day tx",
        channel="UPI",
    )
    tx2 = Transaction(
        transaction_id="TXN_ODD",
        customer_id="CUST001",
        timestamp=datetime(2026, 3, 2, 2, 30, tzinfo=timezone.utc),  # 02:30 AM (R03)
        amount=100.0,
        currency="INR",
        payee="Merchant A",
        description="Late night tx",
        channel="UPI",
    )
    dataset = TransactionDataset(transactions=[tx1, tx2])
    ctx = build_investigation_context(dataset)

    assert ctx.customer_id == "CUST001"
    assert ctx.attention_level == "CONTEXTUAL_REVIEW"
    assert ctx.attention_label == "Contextual Review"
    assert ctx.baseline_summary.transaction_count == 2

    # Check triggered vs non-triggered rules
    triggered_ids = [r.rule_id for r in ctx.triggered_rules]
    non_triggered_ids = [r.rule_id for r in ctx.non_triggered_rules]

    assert triggered_ids == ["R03"]
    assert sorted(non_triggered_ids) == ["R01", "R02", "R04"]

    # Check affected transactions
    assert len(ctx.affected_transactions) == 1
    assert ctx.affected_transactions[0].transaction_id == "TXN_ODD"
    assert ctx.affected_transactions[0].triggered_rules == ["R03"]

    # Safety instruction check
    assert "Do not state that fraud occurred" in ctx.safety_instruction

    # Check that forbidden fraud score fields do NOT exist
    dumped = ctx.model_dump(mode="json")
    for field in ["fraud_score", "fraud_probability", "risk_score"]:
        assert field not in dumped
